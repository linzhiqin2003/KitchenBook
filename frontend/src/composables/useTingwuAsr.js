/**
 * Tingwu Real-time ASR + Translation Composable
 *
 * Connects to backend WebSocket (provider='tingwu') which internally manages
 * the Tingwu real-time task and NLS meeting connection.
 *
 * Flow:
 *   Browser mic → AudioWorklet (16kHz PCM Int16) → WebSocket binary frames
 *   WebSocket JSON events ← transcription / translation / speech_start / error
 */

import { ref } from 'vue'
import { getAiLabWsBaseUrl } from '../config/aiLab'

export function useTingwuAsr() {
  const connected = ref(false)
  const error = ref('')

  let ws = null
  let audioCtx = null
  let workletNode = null
  let micStream = null
  let _onTranscription = null
  let _onTranslation = null

  /**
   * Start Tingwu real-time session.
   *
   * @param {string} sourceLang - Source language code (e.g. 'en', 'zh')
   * @param {string} targetLang - Target language name (e.g. 'Chinese', 'English')
   * @param {object} callbacks
   *   - onTranscription({ text, is_final })
   *   - onTranslation({ original, translated, target_lang })
   *   - onSpeechStart()
   *   - onError(msg)
   *   - onStarted(config)
   */
  async function start(sourceLang, targetLang, callbacks = {}) {
    error.value = ''
    _onTranscription = callbacks.onTranscription || null
    _onTranslation = callbacks.onTranslation || null

    // 1. Open WebSocket to backend
    const wsUrl = `${getAiLabWsBaseUrl()}/ws/interpretation/`
    console.log('[Tingwu] Connecting to', wsUrl)

    return new Promise((resolve, reject) => {
      ws = new WebSocket(wsUrl)

      ws.onopen = () => {
        console.log('[Tingwu] WebSocket connected, sending start')
        // Send start with tingwu provider
        ws.send(JSON.stringify({
          type: 'start',
          provider: 'tingwu',
          source_lang: sourceLang,
          target_lang: targetLang,
          translation_enabled: true,
        }))
      }

      ws.onmessage = async (event) => {
        try {
          const data = JSON.parse(event.data)
          handleMessage(data, callbacks)

          // Resolve promise once started
          if (data.type === 'started') {
            connected.value = true
            // Start mic capture after backend is ready
            await startMicCapture()
            resolve()
          } else if (data.type === 'error' && !connected.value) {
            error.value = data.message
            reject(new Error(data.message))
          }
        } catch (e) {
          console.error('[Tingwu] message parse error:', e)
        }
      }

      ws.onerror = (e) => {
        console.error('[Tingwu] WebSocket error:', e)
        error.value = 'WebSocket 连接失败'
        if (!connected.value) reject(new Error('WebSocket error'))
      }

      ws.onclose = (e) => {
        console.log('[Tingwu] WebSocket closed:', e.code, e.reason)
        connected.value = false
        cleanupMic()
      }
    })
  }

  function handleMessage(data, callbacks) {
    switch (data.type) {
      case 'transcription':
        if (callbacks.onTranscription) {
          callbacks.onTranscription({
            text: data.text,
            is_final: data.is_final,
          })
        }
        break

      case 'translation':
        if (callbacks.onTranslation) {
          callbacks.onTranslation({
            original: data.original,
            translated: data.translated,
            target_lang: data.target_lang,
          })
        }
        break

      case 'speech_start':
        if (callbacks.onSpeechStart) callbacks.onSpeechStart()
        break

      case 'speech_stop':
        if (callbacks.onSpeechStop) callbacks.onSpeechStop()
        break

      case 'started':
        console.log('[Tingwu] Services started:', data.config)
        if (callbacks.onStarted) callbacks.onStarted(data.config)
        break

      case 'stopped':
        console.log('[Tingwu] Services stopped')
        break

      case 'error':
        console.error('[Tingwu] Server error:', data.message)
        error.value = data.message
        if (callbacks.onError) callbacks.onError(data.message)
        break

      case 'connected':
      case 'pong':
        break

      default:
        console.log('[Tingwu] Unknown message:', data.type)
    }
  }

  /**
   * Start microphone capture and send PCM frames over WebSocket.
   */
  async function startMicCapture() {
    try {
      micStream = await navigator.mediaDevices.getUserMedia({
        audio: {
          sampleRate: 16000,
          channelCount: 1,
          echoCancellation: true,
          noiseSuppression: true,
        },
      })

      audioCtx = new AudioContext({ sampleRate: 16000 })
      await audioCtx.audioWorklet.addModule('/worklets/pcm-capture-processor.js')

      const source = audioCtx.createMediaStreamSource(micStream)
      workletNode = new AudioWorkletNode(audioCtx, 'pcm-capture-processor', {
        processorOptions: {
          chunkSize: 3200, // 200ms @ 16kHz — good for real-time streaming
        },
      })

      workletNode.port.onmessage = (event) => {
        if (event.data.type === 'pcm' && ws && ws.readyState === WebSocket.OPEN) {
          // Send raw PCM bytes as binary frame
          ws.send(new Uint8Array(event.data.buffer))
        }
      }

      source.connect(workletNode)
      workletNode.connect(audioCtx.destination) // needed to keep worklet alive
      console.log('[Tingwu] Mic capture started')
    } catch (e) {
      console.error('[Tingwu] Mic capture failed:', e)
      error.value = `麦克风访问失败: ${e.message}`
      throw e
    }
  }

  function cleanupMic() {
    if (workletNode) {
      workletNode.disconnect()
      workletNode = null
    }
    if (audioCtx) {
      audioCtx.close()
      audioCtx = null
    }
    if (micStream) {
      micStream.getTracks().forEach((t) => t.stop())
      micStream = null
    }
  }

  /**
   * Stop the Tingwu session.
   */
  function stop() {
    cleanupMic()

    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({ type: 'stop' }))
      ws.close()
    }
    ws = null
    connected.value = false
  }

  return {
    connected,
    error,
    start,
    stop,
  }
}
