import { ref } from 'vue'
import { getAiLabApiBase } from '../config/aiLab'

/**
 * Composable: lightweight streaming ASR using AudioWorklet + RMS silence detection.
 *
 * Browser Mic → AudioContext(16kHz) → PCM Worklet → accumulate Float32 samples
 *   → silence detected (RMS < threshold for 1.5s) or max duration (15s)
 *   → build WAV → POST /api/interpretation/transcribe-translate-stream/
 *   → NDJSON stream → onFinal callback
 *
 * Advantages over standard VAD mode:
 * - No 600KB+ Silero VAD model download
 * - Instant startup (no ONNX runtime)
 * - RMS-based silence detection is lightweight
 * - Real-time speech activity indicator from RMS energy
 */
export function useStreamingAsr() {
  const API_BASE = getAiLabApiBase()

  // ── Reactive state ──
  const partialText = ref('')
  const speechActive = ref(false)
  const error = ref('')

  // ── Internal state ──
  let audioCtx = null
  let workletNode = null
  let mediaStream = null
  let recording = false
  let onFinalCb = null
  let sourceLang = 'en'
  let targetLang = 'Chinese'

  // Audio accumulation buffer (Float32 samples at 16kHz)
  let accumulatedSamples = []
  let totalSamples = 0

  // Silence detection
  const SILENCE_THRESHOLD = 0.02
  const SILENCE_TIMEOUT_MS = 300
  const MAX_DURATION_MS = 5000
  const MIN_AUDIO_MS = 300
  let lastSpeechTime = 0
  let segmentStartTime = 0
  let silenceTimer = null
  let hasSpeechInSegment = false

  // ── Public API ──

  async function start(lang, onFinal, targetLanguage) {
    if (recording) return
    recording = true
    sourceLang = lang || 'en'
    targetLang = targetLanguage || 'Chinese'
    onFinalCb = onFinal
    error.value = ''
    partialText.value = ''
    speechActive.value = false
    accumulatedSamples = []
    totalSamples = 0
    hasSpeechInSegment = false

    try {
      mediaStream = await navigator.mediaDevices.getUserMedia({
        audio: {
          channelCount: 1,
          sampleRate: 16000,
          echoCancellation: true,
          noiseSuppression: true,
        },
      })

      audioCtx = new AudioContext({ sampleRate: 16000 })
      await audioCtx.audioWorklet.addModule('/worklets/pcm-capture-processor.js')

      const source = audioCtx.createMediaStreamSource(mediaStream)
      workletNode = new AudioWorkletNode(audioCtx, 'pcm-capture-processor', {
        processorOptions: { chunkSize: 8000 }, // 0.5s chunks
      })

      workletNode.port.onmessage = (e) => {
        if (e.data.type === 'pcm') {
          handlePcmChunk(e.data.buffer, e.data.rms)
        }
      }

      source.connect(workletNode)
      workletNode.connect(audioCtx.destination)

      // Start silence detection timer
      lastSpeechTime = Date.now()
      segmentStartTime = Date.now()
      startSilenceTimer()

      console.log('[StreamASR] Started, waiting for speech...')
    } catch (e) {
      recording = false
      if (e.name === 'NotAllowedError' || e.name === 'NotFoundError') {
        error.value = '无法访问麦克风，请检查权限设置'
      } else {
        error.value = `ASR 初始化失败: ${e.message}`
      }
      cleanup()
    }
  }

  function stop() {
    if (!recording) return
    recording = false
    stopSilenceTimer()

    // Flush any remaining audio
    if (hasSpeechInSegment && totalSamples > 0) {
      const samples = mergeSamples()
      const durationMs = (samples.length / 16000) * 1000
      if (durationMs >= MIN_AUDIO_MS) {
        submitAudio(samples)
      }
    }

    cleanup()
  }

  // ── PCM chunk handling ──

  function handlePcmChunk(buffer, rms) {
    if (!recording) return

    // Convert ArrayBuffer back to Int16Array, then to Float32 for accumulation
    const int16 = new Int16Array(buffer)
    const float32 = new Float32Array(int16.length)
    for (let i = 0; i < int16.length; i++) {
      float32[i] = int16[i] / (int16[i] < 0 ? 0x8000 : 0x7FFF)
    }

    accumulatedSamples.push(float32)
    totalSamples += float32.length

    // Update speech activity based on RMS
    if (rms >= SILENCE_THRESHOLD) {
      lastSpeechTime = Date.now()
      speechActive.value = true
      hasSpeechInSegment = true
      partialText.value = '语音识别中...'
    } else {
      // Debounce: only mark inactive after a short delay
      const silenceMs = Date.now() - lastSpeechTime
      if (silenceMs > 300) {
        speechActive.value = false
      }
    }
  }

  // ── Silence detection timer ──

  function startSilenceTimer() {
    stopSilenceTimer()

    silenceTimer = setInterval(() => {
      if (!recording) return

      const now = Date.now()
      const silenceMs = now - lastSpeechTime
      const segmentMs = now - segmentStartTime

      // Silence detected after speech → flush segment
      if (hasSpeechInSegment && silenceMs >= SILENCE_TIMEOUT_MS) {
        console.log('[StreamASR] Silence detected, flushing segment')
        flushSegment()
      }

      // Max duration → force flush
      if (hasSpeechInSegment && segmentMs >= MAX_DURATION_MS) {
        console.log('[StreamASR] Max duration reached, force flushing')
        flushSegment()
      }
    }, 200)
  }

  function stopSilenceTimer() {
    clearInterval(silenceTimer)
    silenceTimer = null
  }

  // ── Flush accumulated audio segment ──

  function flushSegment() {
    if (totalSamples === 0) return

    const samples = mergeSamples()
    const durationMs = (samples.length / 16000) * 1000

    // Reset accumulation for next segment
    accumulatedSamples = []
    totalSamples = 0
    hasSpeechInSegment = false
    segmentStartTime = Date.now()
    lastSpeechTime = Date.now()
    partialText.value = ''
    speechActive.value = false

    if (durationMs < MIN_AUDIO_MS) {
      console.log('[StreamASR] Segment too short, discarding:', durationMs, 'ms')
      return
    }

    submitAudio(samples)
  }

  // ── Merge accumulated Float32 chunks ──

  function mergeSamples() {
    const merged = new Float32Array(totalSamples)
    let offset = 0
    for (const chunk of accumulatedSamples) {
      merged.set(chunk, offset)
      offset += chunk.length
    }
    return merged
  }

  // ── Build WAV and submit to backend ──

  function submitAudio(samples) {
    const blob = float32ToWavBlob(samples, 16000)
    if (blob.size <= 44) return // empty WAV

    console.log('[StreamASR] Submitting', (samples.length / 16000).toFixed(1), 's audio')

    // Call onFinal with a promise-based approach:
    // We submit to the NDJSON stream endpoint, parse events, and call onFinal with the text
    submitToBackend(blob)
  }

  async function submitToBackend(blob) {
    try {
      const formData = new FormData()
      formData.append('file', blob, 'segment.wav')
      formData.append('source_lang', sourceLang)
      formData.append('target_lang', targetLang)

      const res = await fetch(`${API_BASE}/api/interpretation/transcribe-translate-stream/`, {
        method: 'POST',
        body: formData,
      })

      if (!res.ok) {
        const errText = await res.text().catch(() => '')
        let errMsg = `Server error (${res.status})`
        try { errMsg = JSON.parse(errText).text || errMsg } catch {}
        throw new Error(errMsg)
      }

      // Parse NDJSON stream
      const reader = res.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ''
      let transcribedText = ''
      let translatedText = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break
        buffer += decoder.decode(value, { stream: true })

        const lines = buffer.split('\n')
        buffer = lines.pop()

        for (const line of lines) {
          if (!line.trim()) continue
          const event = JSON.parse(line)

          if (event.event === 'transcription') {
            if (!event.text) return // silence — no text
            transcribedText = event.text
          } else if (event.event === 'translation') {
            translatedText = event.text
          } else if (event.event === 'error') {
            throw new Error(event.text)
          }
        }
      }

      // Call onFinal with both original and translated text
      if (transcribedText.trim() && onFinalCb) {
        onFinalCb(transcribedText.trim(), translatedText.trim())
      }
    } catch (e) {
      console.error('[StreamASR] Submit error:', e)
      // Still call onFinal with error info so the UI can show it
      if (onFinalCb) {
        onFinalCb(`[Error: ${e.message}]`, '')
      }
    }
  }

  // ── Float32 → WAV Blob ──

  function float32ToWavBlob(samples, sampleRate) {
    const numChannels = 1
    const bitsPerSample = 16
    const byteRate = sampleRate * numChannels * (bitsPerSample / 8)
    const blockAlign = numChannels * (bitsPerSample / 8)
    const dataSize = samples.length * (bitsPerSample / 8)
    const buffer = new ArrayBuffer(44 + dataSize)
    const view = new DataView(buffer)

    writeString(view, 0, 'RIFF')
    view.setUint32(4, 36 + dataSize, true)
    writeString(view, 8, 'WAVE')
    writeString(view, 12, 'fmt ')
    view.setUint32(16, 16, true)
    view.setUint16(20, 1, true)
    view.setUint16(22, numChannels, true)
    view.setUint32(24, sampleRate, true)
    view.setUint32(28, byteRate, true)
    view.setUint16(32, blockAlign, true)
    view.setUint16(34, bitsPerSample, true)
    writeString(view, 36, 'data')
    view.setUint32(40, dataSize, true)

    let offset = 44
    for (let i = 0; i < samples.length; i++) {
      const s = Math.max(-1, Math.min(1, samples[i]))
      view.setInt16(offset, s < 0 ? s * 0x8000 : s * 0x7FFF, true)
      offset += 2
    }

    return new Blob([buffer], { type: 'audio/wav' })
  }

  function writeString(view, offset, str) {
    for (let i = 0; i < str.length; i++) {
      view.setUint8(offset + i, str.charCodeAt(i))
    }
  }

  // ── Cleanup ──

  function cleanup() {
    stopSilenceTimer()

    if (workletNode) {
      try { workletNode.disconnect() } catch {}
      workletNode = null
    }

    if (audioCtx) {
      try { audioCtx.close() } catch {}
      audioCtx = null
    }

    if (mediaStream) {
      mediaStream.getTracks().forEach(t => t.stop())
      mediaStream = null
    }

    accumulatedSamples = []
    totalSamples = 0
    partialText.value = ''
    speechActive.value = false
  }

  return {
    partialText,
    speechActive,
    error,
    start,
    stop,
  }
}
