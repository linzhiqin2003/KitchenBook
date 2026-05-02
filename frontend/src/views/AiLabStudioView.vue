<script setup>
import { ref, nextTick, onUnmounted, computed } from 'vue'
import { useRoute } from 'vue-router'
import LanguageSelector from '../components/ailab/LanguageSelector.vue'
import EmojiGenerator from '../components/ailab/EmojiGenerator.vue'
import { getAiLabApiBase } from '../config/aiLab'
import { useStreamingAsr } from '../composables/useStreamingAsr'
import { useTingwuAsr } from '../composables/useTingwuAsr'

const API_BASE = getAiLabApiBase()
const route = useRoute()

// View toggle
const currentView = ref(route.query.view === 'emoji' ? 'emoji' : 'interpretation')

// Language
const sourceLang = ref('en')
const targetLang = ref('Chinese')

// ASR mode: 'standard' (VAD) only — streaming disabled
const asrMode = ref('standard')

// Provider: 'standard' (VAD + REST) or 'tingwu' (WebSocket real-time)
const asrProvider = ref('standard')

// State
const errorMsg = ref('')
const inflight = ref(0)
const isRecording = ref(false)
const asrModel = ref('')  // 当前使用的 ASR 模型名称
const recordingTime = ref(0)

// Streaming ASR composable
const {
  partialText: streamingPartialText,
  speechActive: streamingSpeechActive,
  error: streamingError,
  start: startStreamingAsr,
  stop: stopStreamingAsr,
} = useStreamingAsr()

// Tingwu composable
const {
  connected: tingwuConnected,
  error: tingwuError,
  start: startTingwu,
  stop: stopTingwu,
} = useTingwuAsr()

let timerInterval = null
let recordingStartTime = null
let segmentSeq = 0

// VAD
let vadInstance = null
let currentParagraphId = null

// Slow pipeline: accumulate audio for high-quality overwrite
let accumulatedAudio = []       // Float32Array segments
let accumulatedDuration = 0     // seconds
let accumulatedEntryIds = []    // entry IDs to overwrite
let slowPipelineTimer = null
const SLOW_FLUSH_DELAY_MS = 1000 // flush after 1s silence

// Audio visualization
const vizCanvas = ref(null)
let vizAudioCtx = null
let vizAnalyser = null
let vizStream = null
let vizAnimId = null

async function startVisualization() {
  try {
    vizStream = await navigator.mediaDevices.getUserMedia({ audio: true })
    vizAudioCtx = new AudioContext()
    const source = vizAudioCtx.createMediaStreamSource(vizStream)
    vizAnalyser = vizAudioCtx.createAnalyser()
    vizAnalyser.fftSize = 128
    vizAnalyser.smoothingTimeConstant = 0.8
    source.connect(vizAnalyser)
    drawVisualization()
  } catch (e) {
    console.warn('[Viz] init failed:', e)
  }
}

function drawVisualization() {
  const canvas = vizCanvas.value
  if (!vizAnalyser || !canvas) return
  const ctx = canvas.getContext('2d')
  const dpr = window.devicePixelRatio || 1

  // Size canvas to container
  const rect = canvas.parentElement.getBoundingClientRect()
  canvas.width = rect.width * dpr
  canvas.height = rect.height * dpr
  ctx.scale(dpr, dpr)
  const W = rect.width
  const H = rect.height

  const bufLen = vizAnalyser.frequencyBinCount
  const dataArray = new Uint8Array(bufLen)

  function draw() {
    vizAnimId = requestAnimationFrame(draw)
    vizAnalyser.getByteFrequencyData(dataArray)
    ctx.clearRect(0, 0, W, H)

    // Draw mirrored bars from center
    const centerX = W / 2
    const barCount = Math.min(bufLen, 48)
    const barW = 3
    const gap = 2
    const totalW = barCount * (barW + gap)

    for (let i = 0; i < barCount; i++) {
      const val = dataArray[i] / 255
      const barH = Math.max(2, val * H * 0.7)
      const x = centerX + i * (barW + gap)
      const xMirror = centerX - (i + 1) * (barW + gap)
      const y = (H - barH) / 2

      // Gradient from blue to purple based on frequency
      const alpha = 0.15 + val * 0.35
      const hue = 220 + i * 1.5
      ctx.fillStyle = `hsla(${hue}, 80%, 65%, ${alpha})`
      ctx.beginPath()
      ctx.roundRect(x, y, barW, barH, 1.5)
      ctx.fill()
      ctx.beginPath()
      ctx.roundRect(xMirror, y, barW, barH, 1.5)
      ctx.fill()
    }
  }
  draw()
}

function stopVisualization() {
  if (vizAnimId) { cancelAnimationFrame(vizAnimId); vizAnimId = null }
  if (vizStream) { vizStream.getTracks().forEach(t => t.stop()); vizStream = null }
  if (vizAudioCtx) { vizAudioCtx.close(); vizAudioCtx = null }
  vizAnalyser = null
}

// File input
const fileInput = ref(null)

// History — items: { id, seq, paragraphId, original, translated, timestamp, pending }
const transcriptionHistory = ref([])
const historyContainer = ref(null)

// Meeting minutes state
const meetingMinutes = ref('')
const generatingMinutes = ref(false)
const showMinutes = ref(false)

// Two-column layout: hover highlight
const hoveredId = ref(null)

const SENTENCE_END_RE = /[.。!！?？]\s*$/

// ── Float32Array → WAV Blob ──
function float32ToWavBlob(samples, sampleRate = 16000) {
  const numChannels = 1
  const bitsPerSample = 16
  const byteRate = sampleRate * numChannels * (bitsPerSample / 8)
  const blockAlign = numChannels * (bitsPerSample / 8)
  const dataSize = samples.length * (bitsPerSample / 8)
  const buffer = new ArrayBuffer(44 + dataSize)
  const view = new DataView(buffer)

  // RIFF header
  writeString(view, 0, 'RIFF')
  view.setUint32(4, 36 + dataSize, true)
  writeString(view, 8, 'WAVE')

  // fmt chunk
  writeString(view, 12, 'fmt ')
  view.setUint32(16, 16, true)           // chunk size
  view.setUint16(20, 1, true)            // PCM
  view.setUint16(22, numChannels, true)
  view.setUint32(24, sampleRate, true)
  view.setUint32(28, byteRate, true)
  view.setUint16(32, blockAlign, true)
  view.setUint16(34, bitsPerSample, true)

  // data chunk
  writeString(view, 36, 'data')
  view.setUint32(40, dataSize, true)

  // PCM samples: float32 → int16
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

// ── Paragraphs computed ──
const paragraphs = computed(() => {
  // Group entries by paragraphId, maintain chronological order (oldest first)
  const groups = []
  const map = new Map()

  // transcriptionHistory is newest-first (unshift), so reverse for chronological
  const chronological = [...transcriptionHistory.value].reverse()

  for (const entry of chronological) {
    const pid = entry.paragraphId
    if (!pid) {
      // standalone entry (e.g., file upload without paragraphId grouping)
      groups.push({
        paragraphId: entry.id,
        entries: [entry],
        original: entry.original,
        translated: entry.translated,
        timestamp: entry.timestamp,
        pending: entry.pending,
        isFinal: entry.isFinal ?? !entry.pending,
      })
      continue
    }
    if (!map.has(pid)) {
      const group = { paragraphId: pid, entries: [], original: '', translated: '', timestamp: '', pending: false, isFinal: false }
      map.set(pid, group)
      groups.push(group)
    }
    map.get(pid).entries.push(entry)
  }

  // Build concatenated text for each group
  for (const g of groups) {
    if (g.entries.length === 0) continue
    g.entries.sort((a, b) => a.seq - b.seq)
    g.original = g.entries.map(e => e.original).filter(Boolean).join(' ')
    g.translated = g.entries.map(e => e.translated).filter(Boolean).join(' ')
    g.timestamp = g.entries[0].timestamp
    // pending if any entry is still pending
    const pendingEntry = g.entries.find(e => e.pending)
    g.pending = pendingEntry ? pendingEntry.pending : false
    // final if all non-empty entries are final
    g.isFinal = g.entries.filter(e => e.original).every(e => e.isFinal)
  }

  return groups
})

// ── Recording with VAD ──
async function startRecording() {
  segmentSeq = 0
  currentParagraphId = null
  isRecording.value = true
  recordingTime.value = 0
  recordingStartTime = Date.now()
  errorMsg.value = ''

  // Timer display
  timerInterval = setInterval(() => {
    recordingTime.value = Math.floor((Date.now() - recordingStartTime) / 1000)
  }, 200)

  // Start audio visualization
  await nextTick()
  startVisualization()

  // Initialize VAD — it manages microphone access internally
  try {
    const { MicVAD } = await import('@ricky0123/vad-web')
    vadInstance = await MicVAD.new({
      baseAssetPath: '/vad/',
      onnxWASMBasePath: 'https://cdn.jsdelivr.net/npm/onnxruntime-web@1.24.1/dist/',
      // Fast pipeline: more sensitive VAD for quicker segments
      positiveSpeechThreshold: 0.3,
      negativeSpeechThreshold: 0.55,
      redemptionMs: 100,
      minSpeechMs: 60,
      submitUserSpeechOnPause: true,
      onSpeechStart: () => {
        console.log('[VAD] Speech started')
      },
      onSpeechEnd: (audio) => {
        // RMS energy check: skip near-silent segments to prevent ASR hallucination
        let sumSq = 0
        for (let i = 0; i < audio.length; i++) sumSq += audio[i] * audio[i]
        const rms = Math.sqrt(sumSq / audio.length)
        if (rms < 0.01) {
          console.log('[VAD] Skipped silent segment, RMS:', rms.toFixed(4))
          return
        }
        console.log('[VAD] Speech ended, audio length:', audio.length, 'RMS:', rms.toFixed(4))
        const blob = float32ToWavBlob(audio)
        if (blob.size <= 44) return // empty WAV (header only)

        if (!currentParagraphId) {
          currentParagraphId = `para-${Date.now()}`
        }
        const seq = segmentSeq++

        // Fast pipeline: quick transcription (translation comes but we'll overwrite)
        submitSegment(blob, seq, currentParagraphId)

        // Slow pipeline: accumulate audio for high-quality overwrite
        accumulatedAudio.push(audio)
        accumulatedDuration += audio.length / 16000
        scheduleSlowPipeline()
      },
    })
  } catch (e) {
    console.error('VAD init failed:', e)
    if (e.name === 'NotAllowedError' || e.name === 'NotFoundError') {
      errorMsg.value = '无法访问麦克风，请检查权限设置'
    } else {
      errorMsg.value = `语音检测模型加载失败: ${e.message}`
    }
    stopRecording()
  }
}

function stopRecording() {
  isRecording.value = false
  clearInterval(timerInterval)
  timerInterval = null
  stopVisualization()

  if (vadInstance) {
    vadInstance.destroy()
    vadInstance = null
  }

  // Flush any remaining accumulated audio through slow pipeline
  if (accumulatedAudio.length > 0) {
    flushSlowPipeline()
  }
  clearTimeout(slowPipelineTimer)
  slowPipelineTimer = null

  currentParagraphId = null
}

// ── Slow pipeline: accumulate → combined transcription + translation ──
function scheduleSlowPipeline() {
  clearTimeout(slowPipelineTimer)

  // Flush after a real pause (silence timeout only, no duration limit)
  slowPipelineTimer = setTimeout(() => {
    flushSlowPipeline()
  }, SLOW_FLUSH_DELAY_MS)
}

async function flushSlowPipeline() {
  clearTimeout(slowPipelineTimer)
  slowPipelineTimer = null

  if (accumulatedAudio.length === 0) return

  // Snapshot and reset
  const audioChunks = accumulatedAudio
  const entryIds = [...accumulatedEntryIds]
  const pid = currentParagraphId
  accumulatedAudio = []
  accumulatedDuration = 0
  accumulatedEntryIds = []

  // Merge all Float32 audio
  let totalLen = 0
  for (const chunk of audioChunks) totalLen += chunk.length
  const merged = new Float32Array(totalLen)
  let offset = 0
  for (const chunk of audioChunks) {
    merged.set(chunk, offset)
    offset += chunk.length
  }

  const blob = float32ToWavBlob(merged)
  if (blob.size <= 44 || entryIds.length === 0) return

  const t0 = performance.now()
  console.log(`[SlowPipe] submit: ${(totalLen / 16000).toFixed(1)}s audio, overwriting ${entryIds.length} entries`)

  try {
    const formData = new FormData()
    formData.append('file', blob, 'combined.wav')
    formData.append('source_lang', sourceLang.value)
    formData.append('target_lang', targetLang.value)

    const res = await fetch(`${API_BASE}/api/interpretation/transcribe-translate-stream/`, {
      method: 'POST',
      body: formData,
    })

    if (!res.ok) return

    // Parse NDJSON for transcription + translation
    const reader = res.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''
    let betterOriginal = ''
    let betterTranslation = ''

    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split('\n')
      buffer = lines.pop()
      for (const line of lines) {
        if (!line.trim()) continue
        const event = JSON.parse(line)
        if (event.event === 'transcription' && event.text) {
          betterOriginal = event.text
          if (event.asr_model) asrModel.value = event.asr_model
        } else if (event.event === 'translation' && event.text) {
          betterTranslation = event.text
        }
      }
    }

    if (!betterOriginal) return

    // Overwrite: first entry gets combined result, rest get cleared
    for (let i = 0; i < entryIds.length; i++) {
      const idx = transcriptionHistory.value.findIndex(h => h.id === entryIds[i])
      if (idx === -1) continue
      if (i === 0) {
        transcriptionHistory.value[idx].original = betterOriginal
        transcriptionHistory.value[idx].translated = betterTranslation
        transcriptionHistory.value[idx].pending = false
        transcriptionHistory.value[idx].isFinal = true
      } else {
        transcriptionHistory.value[idx].original = ''
        transcriptionHistory.value[idx].translated = ''
        transcriptionHistory.value[idx].pending = false
        transcriptionHistory.value[idx].isFinal = true
      }
    }

    // Sentence boundary → new paragraph
    if (SENTENCE_END_RE.test(betterOriginal.trim())) {
      currentParagraphId = null
    }

    console.log(`[SlowPipe] done in ${((performance.now() - t0) / 1000).toFixed(2)}s`)
  } catch (e) {
    console.warn('[SlowPipe] failed:', e)
  }
}

function toggleRecording() {
  if (isRecording.value) {
    if (asrProvider.value === 'tingwu') {
      stopTingwuRecording()
    } else if (asrMode.value === 'streaming') {
      stopStreamingRecording()
    } else {
      stopRecording()
    }
  } else {
    if (asrProvider.value === 'tingwu') {
      startTingwuRecording()
    } else if (asrMode.value === 'streaming') {
      startStreamingRecording()
    } else {
      startRecording()
    }
  }
}

// ── Tingwu mode recording ──
let tingwuParagraphId = null
let tingwuSegSeq = 0
// Tingwu sends partial transcription (is_final=false) then final + translation
// We keep a "current" entry that gets updated incrementally
let tingwuCurrentEntryId = null

async function startTingwuRecording() {
  isRecording.value = true
  recordingTime.value = 0
  recordingStartTime = Date.now()
  errorMsg.value = ''
  tingwuParagraphId = `para-${Date.now()}`
  tingwuSegSeq = 0
  tingwuCurrentEntryId = null
  asrModel.value = 'Tingwu'

  // Timer display
  timerInterval = setInterval(() => {
    recordingTime.value = Math.floor((Date.now() - recordingStartTime) / 1000)
  }, 200)

  // Start visualization
  await nextTick()
  startVisualization()

  try {
    await startTingwu(sourceLang.value, targetLang.value, {
      onTranscription: handleTingwuTranscription,
      onTranslation: handleTingwuTranslation,
      onSpeechStart: () => { console.log('[Tingwu] Speech started') },
      onError: (msg) => { errorMsg.value = msg },
    })
  } catch (e) {
    console.error('[Tingwu] Start failed:', e)
    errorMsg.value = `听悟启动失败: ${e.message}`
    stopTingwuRecording()
  }
}

function stopTingwuRecording() {
  isRecording.value = false
  clearInterval(timerInterval)
  timerInterval = null
  stopVisualization()
  stopTingwu()
  tingwuParagraphId = null
  tingwuCurrentEntryId = null
}

function handleTingwuTranscription({ text, is_final }) {
  if (!text || !text.trim()) return

  if (!is_final) {
    // Intermediate result: update or create current entry
    if (tingwuCurrentEntryId) {
      const idx = transcriptionHistory.value.findIndex(h => h.id === tingwuCurrentEntryId)
      if (idx !== -1) {
        transcriptionHistory.value[idx].original = text
        return
      }
    }
    // Create new entry for partial
    const entryId = `tw-${Date.now()}-${tingwuSegSeq}`
    tingwuCurrentEntryId = entryId
    transcriptionHistory.value.unshift({
      id: entryId,
      seq: tingwuSegSeq,
      paragraphId: tingwuParagraphId,
      original: text,
      translated: '',
      timestamp: new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit', second: '2-digit' }),
      pending: 'translating',
      isFinal: false,
    })
    nextTick(() => {
      if (historyContainer.value) {
        historyContainer.value.scrollTop = historyContainer.value.scrollHeight
      }
    })
  } else {
    // Final result: update current entry or create new one
    if (tingwuCurrentEntryId) {
      const idx = transcriptionHistory.value.findIndex(h => h.id === tingwuCurrentEntryId)
      if (idx !== -1) {
        transcriptionHistory.value[idx].original = text
        transcriptionHistory.value[idx].isFinal = true
        // Translation will come via separate event; keep pending
      }
    } else {
      // No partial existed — create fresh entry
      const entryId = `tw-${Date.now()}-${tingwuSegSeq}`
      tingwuCurrentEntryId = entryId
      transcriptionHistory.value.unshift({
        id: entryId,
        seq: tingwuSegSeq,
        paragraphId: tingwuParagraphId,
        original: text,
        translated: '',
        timestamp: new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit', second: '2-digit' }),
        pending: 'translating',
        isFinal: true,
      })
      nextTick(() => {
        if (historyContainer.value) {
          historyContainer.value.scrollTop = historyContainer.value.scrollHeight
        }
      })
    }

    // Prepare for next sentence
    tingwuSegSeq++
    // Sentence boundary → new paragraph
    if (SENTENCE_END_RE.test(text.trim())) {
      tingwuParagraphId = `para-${Date.now()}`
    }
    tingwuCurrentEntryId = null
  }
}

function handleTingwuTranslation({ original, translated, target_lang }) {
  if (!translated) return

  // Find the most recent entry that matches and needs translation
  // Strategy: find entry whose original text best matches
  const candidates = transcriptionHistory.value.filter(
    h => h.pending && h.paragraphId && h.paragraphId.startsWith('para-')
  )

  // Try exact match first
  let idx = transcriptionHistory.value.findIndex(
    h => h.pending && h.original === original
  )

  // Fallback: most recent pending entry
  if (idx === -1) {
    idx = transcriptionHistory.value.findIndex(h => h.pending)
  }

  if (idx !== -1) {
    transcriptionHistory.value[idx].translated = translated
    transcriptionHistory.value[idx].pending = false
  }
}

// ── Streaming mode recording ──
let streamingParagraphId = null
let streamingSegSeq = 0

async function startStreamingRecording() {
  isRecording.value = true
  recordingTime.value = 0
  recordingStartTime = Date.now()
  errorMsg.value = ''
  streamingParagraphId = `para-${Date.now()}`
  streamingSegSeq = 0

  // Timer display
  timerInterval = setInterval(() => {
    recordingTime.value = Math.floor((Date.now() - recordingStartTime) / 1000)
  }, 200)

  await startStreamingAsr(sourceLang.value, (finalText, translatedText) => {
    handleStreamingFinal(finalText, translatedText)
  }, targetLang.value)

  // Check for composable-level errors
  if (streamingError.value) {
    errorMsg.value = streamingError.value
    stopStreamingRecording()
  }
}

function stopStreamingRecording() {
  isRecording.value = false
  clearInterval(timerInterval)
  timerInterval = null
  stopStreamingAsr()
  streamingParagraphId = null
}

async function handleStreamingFinal(text, translatedText) {
  if (!text.trim()) return

  const seq = streamingSegSeq++
  const entryId = `stream-${Date.now()}-${seq}`
  const pid = streamingParagraphId || `para-${Date.now()}`

  const isError = text.startsWith('[Error')
  const entry = {
    id: entryId,
    seq,
    paragraphId: pid,
    original: text,
    translated: translatedText || '',
    timestamp: new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit', second: '2-digit' }),
    pending: isError ? false : (!translatedText ? 'translating' : false),
  }
  transcriptionHistory.value.unshift(entry)

  await nextTick()
  if (historyContainer.value) {
    historyContainer.value.scrollTop = historyContainer.value.scrollHeight
  }

  // Sentence boundary → new paragraph for next segment
  if (!isError && SENTENCE_END_RE.test(text.trim())) {
    streamingParagraphId = `para-${Date.now()}`
  }

  if (isError) return

  // Per-segment translation already provided by composable → trigger paragraph refinement
  if (translatedText) {
    // (refinement handled by slow pipeline in standard mode)
    return
  }

  // Fallback: composable didn't return translation, fetch it
  inflight.value++
  try {
    const res = await fetch(`${API_BASE}/api/interpretation/translate/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text, source_lang: sourceLang.value, target_lang: targetLang.value }),
    })
    if (!res.ok) throw new Error(`Server error (${res.status})`)
    const data = await res.json()
    const idx = transcriptionHistory.value.findIndex(h => h.id === entryId)
    if (idx !== -1) {
      transcriptionHistory.value[idx].translated = data.translated || ''
      transcriptionHistory.value[idx].pending = false
      // (refinement handled by slow pipeline in standard mode)
    }
  } catch (e) {
    const idx = transcriptionHistory.value.findIndex(h => h.id === entryId)
    if (idx !== -1) {
      transcriptionHistory.value[idx].pending = false
    }
  } finally {
    inflight.value--
  }
}

// ── Stream NDJSON from backend and update history progressively ──
async function processNDJSONStream(res, entryId) {
  const reader = res.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''

  while (true) {
    const { done, value } = await reader.read()
    if (done) break
    buffer += decoder.decode(value, { stream: true })

    const lines = buffer.split('\n')
    buffer = lines.pop()

    for (const line of lines) {
      if (!line.trim()) continue
      const event = JSON.parse(line)
      const idx = transcriptionHistory.value.findIndex(h => h.id === entryId)
      if (idx === -1) continue

      if (event.event === 'transcription') {
        if (event.asr_model) asrModel.value = event.asr_model
        if (!event.text) {
          // Empty transcription (silence) — remove placeholder
          transcriptionHistory.value.splice(idx, 1)
          return
        }
        transcriptionHistory.value[idx].original = event.text
        transcriptionHistory.value[idx].pending = 'translating'

        // Sentence boundary: close current paragraph so next speech starts a new one
        if (SENTENCE_END_RE.test(event.text.trim())) {
          currentParagraphId = null
        }
      } else if (event.event === 'translation') {
        transcriptionHistory.value[idx].translated = event.text
        transcriptionHistory.value[idx].pending = false
      } else if (event.event === 'done') {
        transcriptionHistory.value[idx].pending = false
      } else if (event.event === 'error') {
        transcriptionHistory.value[idx].original = `[Error: ${event.text}]`
        transcriptionHistory.value[idx].pending = false
      }
    }
  }
}

// ── Submit a segment (fast pipeline) ──
async function submitSegment(blob, seq, paragraphId) {
  const t0 = performance.now()
  const audioDur = ((blob.size - 44) / 2 / 16000).toFixed(2)
  const placeholderId = `seg-${Date.now()}-${seq}`
  console.log(`[FastPipe] #${seq} submit: ${audioDur}s audio`)
  const entry = {
    id: placeholderId,
    seq,
    paragraphId,
    original: '',
    translated: '',
    timestamp: new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit', second: '2-digit' }),
    pending: true,
    isFinal: false,
  }
  transcriptionHistory.value.unshift(entry)
  inflight.value++

  // Track for slow pipeline overwrite
  accumulatedEntryIds.push(placeholderId)

  await nextTick()
  if (historyContainer.value) {
    historyContainer.value.scrollTop = historyContainer.value.scrollHeight
  }

  try {
    const formData = new FormData()
    formData.append('file', blob, 'segment.wav')
    formData.append('source_lang', sourceLang.value)
    formData.append('target_lang', targetLang.value)

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

    await processNDJSONStream(res, placeholderId)
    console.log(`[FastPipe] #${seq} done in ${((performance.now() - t0) / 1000).toFixed(2)}s`)
  } catch (e) {
    const idx = transcriptionHistory.value.findIndex(h => h.id === placeholderId)
    if (idx !== -1) {
      transcriptionHistory.value[idx] = {
        ...entry,
        original: `[Error: ${e.message}]`,
        translated: '',
        pending: false,
      }
    }
  } finally {
    inflight.value--
  }
}

// ── File upload (one-shot) ──
function triggerFileSelect() {
  fileInput.value?.click()
}

async function handleFileSelect(event) {
  const file = event.target.files?.[0]
  if (!file) return
  errorMsg.value = ''
  event.target.value = ''

  const fileParagraphId = `file-para-${Date.now()}`
  const entry = {
    id: `file-${Date.now()}`,
    seq: -1,
    paragraphId: fileParagraphId,
    original: '',
    translated: '',
    timestamp: new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit', second: '2-digit' }),
    pending: true,
  }
  transcriptionHistory.value.unshift(entry)
  inflight.value++

  try {
    const formData = new FormData()
    formData.append('file', file, file.name)
    formData.append('source_lang', sourceLang.value)
    formData.append('target_lang', targetLang.value)

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

    await processNDJSONStream(res, entry.id)
  } catch (e) {
    const idx = transcriptionHistory.value.findIndex(h => h.id === entry.id)
    if (idx !== -1) {
      transcriptionHistory.value[idx] = { ...entry, original: `[Error: ${e.message}]`, translated: '', pending: false }
    }
  } finally {
    inflight.value--
  }
}

// ── Meeting minutes ──
async function generateMeetingMinutes() {
  const resolved = paragraphs.value.filter(g => !g.pending && !g.original.startsWith('[Error'))
  if (resolved.length < 3) return

  generatingMinutes.value = true
  meetingMinutes.value = ''
  showMinutes.value = true

  try {
    const entries = resolved.map(g => ({
      original: g.original,
      translated: g.translated,
    }))

    const res = await fetch(`${API_BASE}/api/interpretation/meeting-minutes/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ entries }),
    })

    if (!res.ok) {
      throw new Error(`Server error (${res.status})`)
    }

    const reader = res.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''

    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      buffer += decoder.decode(value, { stream: true })

      const lines = buffer.split('\n')
      buffer = lines.pop()

      for (const line of lines) {
        if (!line.trim()) continue
        const event = JSON.parse(line)
        if (event.event === 'chunk') {
          meetingMinutes.value += event.text
        } else if (event.event === 'error') {
          meetingMinutes.value += `\n\n[Error: ${event.text}]`
        }
      }
    }
  } catch (e) {
    meetingMinutes.value += `\n\n[Error: ${e.message}]`
  } finally {
    generatingMinutes.value = false
  }
}

function closeMinutes() {
  showMinutes.value = false
}

// ── Simple markdown renderer for meeting minutes ──
function renderMinutesMarkdown(text) {
  return text
    // Strip <think>...</think> blocks (DeepSeek reasoning output)
    .replace(/<think>[\s\S]*?<\/think>/g, '')
    .replace(/<think>[\s\S]*/g, '') // unclosed <think> during streaming
    .trim()
    .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
    .replace(/^### (.+)$/gm, '<h4 class="text-[14px] font-semibold mt-3 mb-1.5" style="color: var(--theme-700);">$1</h4>')
    .replace(/^## (.+)$/gm, '<h3 class="text-[15px] font-semibold mt-4 mb-2 first:mt-0" style="color: var(--theme-700);">$1</h3>')
    .replace(/^- \[ \] (.+)$/gm, '<div class="flex items-start gap-2 ml-2 mb-1"><span style="color: var(--theme-300);" class="mt-0.5">☐</span><span class="text-[13px]" style="color: var(--theme-600);">$1</span></div>')
    .replace(/^- (.+)$/gm, '<div class="flex items-start gap-2 ml-2 mb-1"><span style="color: var(--theme-400);" class="mt-0.5">•</span><span class="text-[13px]" style="color: var(--theme-600);">$1</span></div>')
    .replace(/\n{2,}/g, '<div class="h-2"></div>')
    .replace(/\n/g, '<br>')
    .replace(/\*\*(.+?)\*\*/g, '<strong style="color: var(--theme-700);">$1</strong>')
}

// ── Utilities ──
function formatTime(seconds) {
  const mins = Math.floor(seconds / 60)
  const secs = seconds % 60
  return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
}

function clearHistory() {
  transcriptionHistory.value = []
  meetingMinutes.value = ''
  showMinutes.value = false
  currentParagraphId = null
  accumulatedAudio = []
  accumulatedDuration = 0
  accumulatedEntryIds = []
}

function copyAll() {
  const resolved = paragraphs.value.filter(g => !g.pending && (g.original || g.translated))
  const text = resolved
    .map(g => `[${g.timestamp}]\n原文: ${g.original}\n译文: ${g.translated}`)
    .join('\n\n')
  navigator.clipboard.writeText(text)
}

function downloadText() {
  const resolved = paragraphs.value.filter(g => !g.pending && (g.original || g.translated))
  const text = resolved
    .map(g => `[${g.timestamp}]\n原文: ${g.original}\n译文: ${g.translated}`)
    .join('\n\n')
  const blob = new Blob([text], { type: 'text/plain;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `translation_${new Date().toISOString().slice(0, 10)}.txt`
  a.click()
  URL.revokeObjectURL(url)
}

const totalEntries = computed(() => paragraphs.value.filter(g => !g.pending && (g.original || g.translated)).length)
const canGenerateMinutes = computed(() => {
  return paragraphs.value.filter(g => !g.pending && !g.original.startsWith('[Error')).length >= 3
})

onUnmounted(() => {
  if (isRecording.value) {
    if (asrProvider.value === 'tingwu') {
      stopTingwuRecording()
    } else if (asrMode.value === 'streaming') {
      stopStreamingRecording()
    } else {
      stopRecording()
    }
  }
})
</script>

<template>
  <div class="h-screen pb-safe overflow-hidden relative flex flex-col" style="background: var(--theme-50, #f8f8f6); color: var(--theme-700, #2d2d28); font-family: var(--ai-font-body);">

    <!-- Header -->
    <header class="relative z-50 flex-none h-12 flex items-center" style="border-bottom: 1px solid var(--theme-200, #e4e4df);">
      <div class="max-w-[1240px] mx-auto px-4 w-full flex items-center justify-between">
        <div class="flex items-center gap-3">
          <router-link
            to="/ai-lab"
            class="w-7 h-7 rounded-md flex items-center justify-center transition-colors"
            style="color: var(--theme-400);"
            title="返回 AI Lab"
          >
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="1.5">
              <path stroke-linecap="round" stroke-linejoin="round" d="M10.5 19.5L3 12m0 0l7.5-7.5M3 12h18"/>
            </svg>
          </router-link>
          <span class="text-[13px] font-semibold tracking-tight hidden sm:inline" style="color: var(--theme-700);">Studio</span>
        </div>

        <div class="flex-1 flex justify-center px-2">
          <div class="p-0.5 rounded-lg flex relative" style="background: var(--theme-200);">
            <div
              class="absolute top-0.5 bottom-0.5 rounded-md shadow-sm transition-all duration-300 ease-[cubic-bezier(0.4,0,0.2,1)]"
              style="background: #fff;"
              :class="currentView === 'interpretation' ? 'left-0.5 w-[76px]' : 'left-[82px] w-[76px]'"
            ></div>
            <button
              @click="currentView = 'interpretation'"
              class="relative z-10 px-3 py-1 rounded-md text-[12px] font-medium transition-colors duration-200 focus:outline-none"
              :style="currentView === 'interpretation' ? 'color: var(--theme-700);' : 'color: var(--theme-400);'"
            >转录翻译</button>
            <button
              @click="currentView = 'emoji'"
              class="relative z-10 px-3 py-1 rounded-md text-[12px] font-medium transition-colors duration-200 focus:outline-none"
              :style="currentView === 'emoji' ? 'color: var(--theme-700);' : 'color: var(--theme-400);'"
            >表情包</button>
          </div>
        </div>

        <div class="flex items-center justify-end gap-2">
          <span class="hidden md:inline px-2 py-0.5 rounded-md text-[10px] font-medium uppercase tracking-wider" style="border: 1px solid var(--theme-200); color: var(--theme-400);">
            {{ currentView === 'interpretation'
              ? (asrProvider === 'tingwu' ? 'Tingwu ASR+Trans' : (asrModel || 'Qwen3-ASR') + ' + Cerebras')
              : 'Emoji-v1' }}
          </span>
        </div>
      </div>
    </header>

    <!-- Main -->
    <main class="relative z-10 flex-1 overflow-hidden">
      <div class="max-w-[1240px] mx-auto px-4 py-6 h-full">

        <!-- Interpretation View -->
        <div v-show="currentView === 'interpretation'" class="h-full flex flex-col gap-5">

          <!-- Top bar: Language + Actions -->
          <div class="flex-none flex flex-col sm:flex-row sm:items-end gap-3 sm:gap-4">
            <div class="flex items-center gap-2 sm:gap-3 flex-1 overflow-x-auto pb-1 sm:pb-0 -mx-1 px-1 sm:mx-0 sm:px-0">
              <div class="w-32 sm:w-40 shrink-0">
                <LanguageSelector v-model="sourceLang" label="From" :disabled="isRecording || inflight > 0" />
              </div>
              <div class="pt-5 shrink-0" style="color: var(--theme-300);">
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="1.5"><path stroke-linecap="round" stroke-linejoin="round" d="M13.5 4.5L21 12m0 0l-7.5 7.5M21 12H3"/></svg>
              </div>
              <div class="w-32 sm:w-40 shrink-0">
                <LanguageSelector v-model="targetLang" label="To" :disabled="isRecording || inflight > 0" :is-target="true" />
              </div>
              <div class="pt-5 sm:ml-2 shrink-0">
                <div class="p-0.5 rounded-lg flex text-[11px]" style="background: var(--theme-200);">
                  <button
                    @click="asrProvider = 'standard'"
                    :disabled="isRecording"
                    class="px-2.5 py-1 rounded-md transition-all focus:outline-none"
                    :style="asrProvider === 'standard'
                      ? 'background: #fff; color: var(--theme-700); box-shadow: 0 1px 2px rgba(0,0,0,0.05);'
                      : 'color: var(--theme-400);'"
                  >Standard</button>
                  <button
                    @click="asrProvider = 'tingwu'"
                    :disabled="isRecording"
                    class="px-2.5 py-1 rounded-md transition-all focus:outline-none"
                    :style="asrProvider === 'tingwu'
                      ? 'background: #fff; color: var(--theme-700); box-shadow: 0 1px 2px rgba(0,0,0,0.05);'
                      : 'color: var(--theme-400);'"
                  >Tingwu</button>
                </div>
              </div>
            </div>
            <div class="flex items-center gap-1.5 shrink-0">
              <button
                v-if="canGenerateMinutes"
                @click="generateMeetingMinutes"
                :disabled="generatingMinutes"
                class="px-3 py-1.5 rounded-lg text-[12px] transition-all disabled:opacity-50"
                style="background: var(--ai-accent-soft); color: var(--ai-accent); border: 1px solid var(--theme-200);"
              >
                <span v-if="generatingMinutes" class="flex items-center gap-1.5">
                  <span class="w-3 h-3 border-2 border-t-transparent rounded-full animate-spin" style="border-color: var(--ai-accent); border-top-color: transparent;"></span>
                  生成中...
                </span>
                <span v-else>会议纪要</span>
              </button>
              <button
                v-if="transcriptionHistory.length"
                @click="copyAll"
                class="px-3 py-1.5 rounded-lg text-[12px] transition-colors"
                style="border: 1px solid var(--theme-200); color: var(--theme-500);"
              >复制</button>
              <button
                v-if="transcriptionHistory.length"
                @click="downloadText"
                class="px-3 py-1.5 rounded-lg text-[12px] transition-colors"
                style="border: 1px solid var(--theme-200); color: var(--theme-500);"
              >下载</button>
              <button
                v-if="transcriptionHistory.length"
                @click="clearHistory"
                class="px-3 py-1.5 rounded-lg text-[12px] transition-colors hover:text-red-500"
                style="border: 1px solid var(--theme-200); color: var(--theme-400);"
              >清空</button>
            </div>
          </div>

          <!-- Input area: Record + Upload + Status -->
          <div class="flex-none rounded-xl p-4 relative overflow-hidden" style="background: var(--theme-100); border: 1px solid var(--theme-200);">
            <canvas v-show="isRecording" ref="vizCanvas" class="absolute inset-0 w-full h-full pointer-events-none"></canvas>
            <div class="relative flex items-center justify-center gap-4">
              <div v-if="isRecording" class="text-xl font-light tabular-nums tracking-tighter w-16 text-center" style="color: var(--theme-500);">
                {{ formatTime(recordingTime) }}
              </div>

              <div class="relative">
                <button
                  @click="toggleRecording"
                  class="relative w-14 h-14 rounded-full flex items-center justify-center transition-all duration-300 group"
                  :style="isRecording
                    ? 'background: #e53e3e; box-shadow: 0 4px 12px rgba(229,62,62,0.25);'
                    : 'background: var(--theme-200); color: var(--theme-500);'"
                >
                  <div v-if="isRecording" class="absolute inset-0 rounded-full animate-ping" style="background: rgba(229,62,62,0.3);"></div>
                  <svg v-if="!isRecording" class="w-6 h-6 transition-colors" style="color: var(--theme-500);" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="1.5">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M12 18.75a6 6 0 006-6v-1.5m-6 7.5a6 6 0 01-6-6v-1.5m6 7.5v3.75m-3.75 0h7.5M12 15.75a3 3 0 01-3-3V4.5a3 3 0 116 0v8.25a3 3 0 01-3 3z"/>
                  </svg>
                  <svg v-else class="w-5 h-5 text-white relative z-10" fill="currentColor" viewBox="0 0 24 24">
                    <rect x="7" y="7" width="10" height="10" rx="2"/>
                  </svg>
                </button>

                <input type="file" ref="fileInput" accept="audio/*,video/*" class="hidden" @change="handleFileSelect">
                <button
                  v-if="!isRecording"
                  @click="triggerFileSelect"
                  class="absolute -bottom-1 -right-1 w-6 h-6 rounded-full flex items-center justify-center transition-all group/upload"
                  style="background: var(--theme-200); border: 1px solid var(--theme-300); color: var(--theme-400);"
                  title="上传音频文件"
                >
                  <svg class="w-3 h-3 transition-colors" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M15.172 7l-6.586 6.586a2 2 0 102.828 2.828l6.414-6.586a4 4 0 00-5.656-5.656l-6.415 6.585a6 6 0 108.486 8.486L20.5 13"/>
                  </svg>
                </button>
              </div>

              <div v-if="inflight > 0 && !isRecording" class="flex items-center gap-2 pl-2">
                <div class="w-4 h-4 border-2 rounded-full animate-spin" style="border-color: var(--ai-accent); border-top-color: transparent;"></div>
                <span class="text-[12px] font-medium" style="color: var(--ai-accent);">
                  处理中 ({{ inflight }})
                </span>
              </div>
            </div>

            <div v-if="errorMsg" class="mt-2 text-center text-[12px] text-red-500">
              {{ errorMsg }}
            </div>
          </div>

          <!-- Results: two-column transcript by paragraphs -->
          <div ref="historyContainer" class="flex-1 overflow-y-auto custom-scrollbar min-h-0 space-y-3">

            <div v-if="!transcriptionHistory.length && inflight === 0 && !showMinutes" class="h-full flex items-center justify-center">
              <div class="text-center space-y-1.5 px-4">
                <p class="text-[13px]" style="color: var(--theme-400);">录音或上传音频文件，自动转录并翻译</p>
                <p class="text-[11px]" style="color: var(--theme-300);">
                  {{ asrProvider === 'tingwu'
                    ? 'Powered by 通义听悟'
                    : 'Powered by Silero VAD + Qwen3-ASR + Cerebras' }}
                </p>
              </div>
            </div>

            <div v-if="transcriptionHistory.length" class="rounded-xl overflow-hidden" style="border: 1px solid var(--theme-200);">
              <!-- Desktop header: two columns -->
              <div class="hidden sm:grid grid-cols-2 gap-4 px-5 pt-3 pb-2 sticky top-0 z-10" style="border-bottom: 1px solid var(--theme-200); background: var(--theme-100);">
                <span class="text-[10px] font-semibold uppercase tracking-wider" style="color: var(--theme-400);">Original</span>
                <span class="text-[10px] font-semibold uppercase tracking-wider" style="color: var(--ai-accent);">Translation</span>
              </div>
              <!-- Mobile header: stacked labels -->
              <div class="sm:hidden flex gap-3 px-4 pt-3 pb-2 sticky top-0 z-10" style="border-bottom: 1px solid var(--theme-200); background: var(--theme-100);">
                <span class="text-[10px] font-semibold uppercase tracking-wider" style="color: var(--theme-400);">原文</span>
                <span class="text-[10px] font-semibold uppercase tracking-wider" style="color: var(--ai-accent);">译文</span>
              </div>

              <!-- Desktop: two columns -->
              <div class="hidden sm:grid grid-cols-2 gap-4 px-5 py-3" style="background: #fff;">
                <p class="text-[14px] leading-relaxed">
                  <template v-for="group in paragraphs" :key="'o-' + group.paragraphId">
                    <span
                      @mouseenter="hoveredId = group.paragraphId"
                      @mouseleave="hoveredId = null"
                      class="transition-colors duration-200 rounded px-0.5 -mx-0.5"
                      :class="hoveredId === group.paragraphId ? 'bg-amber-100/60' : ''"
                      :style="group.isFinal ? 'color: var(--theme-700);' : 'color: var(--theme-300);'"
                    >{{ group.original }}</span>{{ ' ' }}
                  </template>
                  <span v-if="paragraphs.length && paragraphs[paragraphs.length - 1].pending" class="inline-flex items-center ml-1 align-middle">
                    <span class="w-2.5 h-2.5 border-[1.5px] rounded-full animate-spin" style="border-color: var(--ai-accent); border-top-color: transparent;"></span>
                  </span>
                </p>

                <p class="text-[14px] leading-relaxed">
                  <template v-for="group in paragraphs" :key="'t-' + group.paragraphId">
                    <span
                      @mouseenter="hoveredId = group.paragraphId"
                      @mouseleave="hoveredId = null"
                      class="transition-colors duration-200 rounded px-0.5 -mx-0.5"
                      :class="hoveredId === group.paragraphId ? 'bg-amber-100/60' : ''"
                      :style="group.isFinal ? 'color: var(--theme-700);' : 'color: var(--theme-300);'"
                    >{{ group.translated }}</span>{{ ' ' }}
                  </template>
                  <span v-if="paragraphs.length && paragraphs[paragraphs.length - 1].pending && paragraphs[paragraphs.length - 1].translated" class="inline-flex items-center ml-1 align-middle">
                    <span class="w-2.5 h-2.5 border-[1.5px] rounded-full animate-spin" style="border-color: var(--ai-accent); border-top-color: transparent;"></span>
                  </span>
                </p>
              </div>

              <!-- Mobile: stacked paragraphs -->
              <div class="sm:hidden px-4 py-3 space-y-4" style="background: #fff;">
                <template v-for="group in paragraphs" :key="'m-' + group.paragraphId">
                  <div class="space-y-1.5">
                    <p class="text-[13px] leading-relaxed" :style="group.isFinal ? 'color: var(--theme-700);' : 'color: var(--theme-300);'">
                      {{ group.original }}
                    </p>
                    <p class="text-[13px] leading-relaxed" :style="group.isFinal ? 'color: var(--ai-accent);' : 'color: var(--theme-300);'">
                      {{ group.translated }}
                    </p>
                  </div>
                </template>
                <div v-if="paragraphs.length && paragraphs[paragraphs.length - 1].pending" class="flex items-center gap-2 py-1">
                  <span class="w-2.5 h-2.5 border-[1.5px] rounded-full animate-spin" style="border-color: var(--ai-accent); border-top-color: transparent;"></span>
                  <span class="text-[12px]" style="color: var(--theme-400);">处理中...</span>
                </div>
              </div>

              <div class="px-4 sm:px-5 py-2 text-center" style="border-top: 1px solid var(--theme-200);">
                <span class="text-[11px]" style="color: var(--theme-400);">{{ totalEntries }} 段记录</span>
              </div>
            </div>
          </div>
        </div>

        <!-- Emoji Generator View -->
        <div v-show="currentView === 'emoji'" class="min-h-[calc(100vh-120px)]">
          <EmojiGenerator />
        </div>

      </div>
    </main>

    <!-- Meeting Minutes Modal -->
    <Teleport to="body">
      <Transition name="modal">
        <div v-if="showMinutes" class="fixed inset-0 z-50 flex items-center justify-center p-4" @click.self="closeMinutes">
          <div class="absolute inset-0 bg-black/20 backdrop-blur-[2px]"></div>
          <div class="relative w-full max-w-2xl max-h-[80vh] flex flex-col rounded-xl overflow-hidden" style="background: #fff; border: 1px solid var(--theme-200); box-shadow: 0 8px 32px rgba(0,0,0,0.08);">
            <div class="flex items-center justify-between px-6 py-3 shrink-0" style="border-bottom: 1px solid var(--theme-200);">
              <div class="flex items-center gap-2">
                <span class="text-[14px] font-semibold" style="color: var(--theme-700);">会议纪要</span>
                <div v-if="generatingMinutes" class="w-3 h-3 border-2 rounded-full animate-spin" style="border-color: var(--ai-accent); border-top-color: transparent;"></div>
              </div>
              <button @click="closeMinutes" class="w-7 h-7 rounded-md flex items-center justify-center transition-colors cursor-pointer" style="color: var(--theme-400);">
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="1.5">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12"/>
                </svg>
              </button>
            </div>
            <div class="flex-1 overflow-y-auto px-6 py-4 custom-scrollbar">
              <div v-if="meetingMinutes" class="text-[13px] leading-relaxed" style="color: var(--theme-600);" v-html="renderMinutesMarkdown(meetingMinutes)"></div>
              <div v-else-if="generatingMinutes" class="flex items-center gap-2 text-[13px] py-8 justify-center" style="color: var(--theme-400);">
                <span class="w-4 h-4 border-2 rounded-full animate-spin" style="border-color: var(--ai-accent); border-top-color: transparent;"></span>
                正在生成会议纪要...
              </div>
            </div>
            <div v-if="meetingMinutes && !generatingMinutes" class="px-6 py-3 shrink-0 flex justify-end gap-2" style="border-top: 1px solid var(--theme-200);">
              <button @click="navigator.clipboard.writeText(meetingMinutes); closeMinutes()" class="px-4 py-1.5 rounded-lg text-[12px] transition-colors" style="border: 1px solid var(--theme-200); color: var(--theme-500);">复制纪要</button>
              <button @click="closeMinutes" class="px-4 py-1.5 rounded-lg text-[12px] transition-colors" style="background: var(--theme-700); color: var(--theme-50);">关闭</button>
            </div>
          </div>
        </div>
      </Transition>
    </Teleport>
  </div>
</template>

<style scoped>
/* Shimmer effect for fast pipeline preliminary text */
.shimmer-text {
  background: linear-gradient(
    90deg,
    transparent 0%,
    rgba(0, 0, 0, 0.08) 50%,
    transparent 100%
  );
  background-size: 200% 100%;
  -webkit-background-clip: text;
  background-clip: text;
  animation: shimmer 2s linear infinite;
}

@keyframes shimmer {
  0% { background-position: 200% center; }
  100% { background-position: -200% center; }
}

.modal-enter-active,
.modal-leave-active {
  transition: opacity 0.2s ease;
}
.modal-enter-active .relative,
.modal-leave-active .relative {
  transition: transform 0.2s ease, opacity 0.2s ease;
}
.modal-enter-from,
.modal-leave-to {
  opacity: 0;
}
.modal-enter-from .relative {
  transform: scale(0.95) translateY(10px);
  opacity: 0;
}
.modal-leave-to .relative {
  transform: scale(0.95) translateY(10px);
  opacity: 0;
}
</style>
