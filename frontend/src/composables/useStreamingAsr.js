import { ref, shallowRef } from 'vue'
import { getAiLabWsBaseUrl } from '../config/aiLab'

/**
 * Composable: streaming ASR via WebSocket to Qwen3-ASR GPU server.
 *
 * Browser Mic → AudioContext(16kHz) → PCM Worklet → Int16 chunks
 *   → wss://.../ws/asr/transcribe → partial / final JSON
 *
 * Silence detection: RMS < threshold for silenceTimeout → auto finish
 * Max duration: continuous speech > maxDuration → forced finish
 *
 * After each final, if still recording, reconnects WS for next utterance.
 */
export function useStreamingAsr() {
  // ── Reactive state ──
  const partialText = ref('')
  const speechActive = ref(false)
  const error = ref('')

  // ── Internal refs (non-reactive) ──
  let ws = null
  let audioCtx = null
  let workletNode = null
  let mediaStream = null
  let recording = false
  let onFinalCb = null
  let language = 'en'

  // Silence detection
  const SILENCE_THRESHOLD = 0.01
  const SILENCE_TIMEOUT_MS = 1500
  const MAX_DURATION_MS = 15000
  let lastSpeechTime = 0
  let sessionStartTime = 0
  let silenceTimer = null
  let durationTimer = null

  // ── Public API ──

  async function start(lang, onFinal) {
    if (recording) return
    recording = true
    language = lang || 'en'
    onFinalCb = onFinal
    error.value = ''
    partialText.value = ''
    speechActive.value = false

    try {
      // Get microphone
      mediaStream = await navigator.mediaDevices.getUserMedia({
        audio: {
          channelCount: 1,
          sampleRate: 16000,
          echoCancellation: true,
          noiseSuppression: true,
        },
      })

      // AudioContext at 16 kHz
      audioCtx = new AudioContext({ sampleRate: 16000 })
      await audioCtx.audioWorklet.addModule('/worklets/pcm-capture-processor.js')

      const source = audioCtx.createMediaStreamSource(mediaStream)
      workletNode = new AudioWorkletNode(audioCtx, 'pcm-capture-processor', {
        processorOptions: { chunkSize: 8000 }, // 0.5s
      })

      workletNode.port.onmessage = (e) => {
        if (e.data.type === 'pcm') {
          handlePcmChunk(e.data.buffer, e.data.rms)
        }
      }

      source.connect(workletNode)
      workletNode.connect(audioCtx.destination) // needed to keep processing alive

      // Connect first WS session
      connectWs()
    } catch (e) {
      recording = false
      if (e.name === 'NotAllowedError' || e.name === 'NotFoundError') {
        error.value = '无法访问麦克风，请检查权限设置'
      } else {
        error.value = `流式 ASR 初始化失败: ${e.message}`
      }
      cleanup()
    }
  }

  function stop() {
    if (!recording) return
    recording = false
    // Send finish if WS is open
    sendFinish()
    // Don't cleanup immediately — wait for final response
    // Set a timeout to force cleanup if final never arrives
    setTimeout(() => {
      cleanup()
    }, 3000)
  }

  // ── WebSocket management ──

  function connectWs() {
    if (!recording) return

    const base = getAiLabWsBaseUrl()
    const url = `${base}/ws/asr/transcribe`

    partialText.value = ''
    speechActive.value = false

    ws = new WebSocket(url)
    ws.binaryType = 'arraybuffer'

    ws.onopen = () => {
      // Send config
      ws.send(JSON.stringify({ type: 'config', language }))
    }

    ws.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data)
        handleWsMessage(msg)
      } catch {
        // Ignore non-JSON messages
      }
    }

    ws.onerror = (e) => {
      console.error('[StreamingASR] WS error:', e)
      error.value = 'WebSocket 连接错误'
    }

    ws.onclose = (e) => {
      console.log('[StreamingASR] WS closed:', e.code, e.reason)
      ws = null
    }
  }

  function handleWsMessage(msg) {
    if (msg.type === 'ready') {
      console.log('[StreamingASR] Server ready')
      // Reset timers for new session
      lastSpeechTime = Date.now()
      sessionStartTime = Date.now()
      startTimers()
    } else if (msg.type === 'partial') {
      partialText.value = msg.text || ''
      if (msg.text) {
        speechActive.value = true
      }
    } else if (msg.type === 'final') {
      const finalText = msg.text || ''
      partialText.value = ''
      speechActive.value = false
      stopTimers()

      if (finalText.trim() && onFinalCb) {
        onFinalCb(finalText.trim())
      }

      // Reconnect for next utterance if still recording
      if (recording) {
        setTimeout(() => connectWs(), 100)
      }
    } else if (msg.type === 'error') {
      console.error('[StreamingASR] Server error:', msg.message)
      error.value = msg.message || 'ASR 服务错误'
    }
  }

  // ── PCM chunk handling ──

  function handlePcmChunk(buffer, rms) {
    // Update speech activity based on RMS
    if (rms >= SILENCE_THRESHOLD) {
      lastSpeechTime = Date.now()
      speechActive.value = true
    }

    // Send binary PCM to WS if connected
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(buffer)
    }
  }

  // ── Silence & duration timers ──

  function startTimers() {
    stopTimers()

    // Check silence every 200ms
    silenceTimer = setInterval(() => {
      if (!recording || !ws) return
      const silenceMs = Date.now() - lastSpeechTime
      if (silenceMs >= SILENCE_TIMEOUT_MS && partialText.value) {
        console.log('[StreamingASR] Silence detected, finishing')
        sendFinish()
      }
    }, 200)

    // Check max duration every 1s
    durationTimer = setInterval(() => {
      if (!recording || !ws) return
      const elapsed = Date.now() - sessionStartTime
      if (elapsed >= MAX_DURATION_MS) {
        console.log('[StreamingASR] Max duration reached, finishing')
        sendFinish()
      }
    }, 1000)
  }

  function stopTimers() {
    clearInterval(silenceTimer)
    silenceTimer = null
    clearInterval(durationTimer)
    durationTimer = null
  }

  // ── Send finish command ──

  function sendFinish() {
    stopTimers()
    if (ws && ws.readyState === WebSocket.OPEN) {
      try {
        ws.send(JSON.stringify({ type: 'finish' }))
      } catch {
        // WS might be closing
      }
    }
  }

  // ── Cleanup ──

  function cleanup() {
    stopTimers()

    if (ws) {
      try { ws.close() } catch {}
      ws = null
    }

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
