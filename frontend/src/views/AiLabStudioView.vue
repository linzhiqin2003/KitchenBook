<script setup>
import { ref, nextTick, onUnmounted, computed } from 'vue'
import { useRoute } from 'vue-router'
import LanguageSelector from '../components/ailab/LanguageSelector.vue'
import BackgroundOrbs from '../components/ailab/BackgroundOrbs.vue'
import EmojiGenerator from '../components/ailab/EmojiGenerator.vue'
import { getAiLabApiBase } from '../config/aiLab'

const API_BASE = getAiLabApiBase()
const route = useRoute()

// View toggle
const currentView = ref(route.query.view === 'emoji' ? 'emoji' : 'interpretation')

// Language
const sourceLang = ref('en')
const targetLang = ref('Chinese')

// State
const errorMsg = ref('')
const inflight = ref(0)
const isRecording = ref(false)
const recordingTime = ref(0)

let timerInterval = null
let recordingStartTime = null
let segmentSeq = 0

// VAD
let vadInstance = null
let currentParagraphId = null

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
      })
      continue
    }
    if (!map.has(pid)) {
      const group = { paragraphId: pid, entries: [], original: '', translated: '', timestamp: '', pending: false }
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

  // Initialize VAD — it manages microphone access internally
  try {
    const { MicVAD } = await import('@ricky0123/vad-web')
    vadInstance = await MicVAD.new({
      baseAssetPath: '/vad/',
      onnxWASMBasePath: 'https://cdn.jsdelivr.net/npm/onnxruntime-web@1.24.1/dist/',
      positiveSpeechThreshold: 0.5,
      negativeSpeechThreshold: 0.35,
      redemptionMs: 500,
      minSpeechMs: 250,
      submitUserSpeechOnPause: true,
      onSpeechStart: () => {
        console.log('[VAD] Speech started')
      },
      onSpeechEnd: (audio) => {
        console.log('[VAD] Speech ended, audio length:', audio.length)
        const blob = float32ToWavBlob(audio)
        if (blob.size <= 44) return // empty WAV (header only)

        if (!currentParagraphId) {
          currentParagraphId = `para-${Date.now()}`
        }
        const seq = segmentSeq++
        submitSegment(blob, seq, currentParagraphId)
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

  if (vadInstance) {
    vadInstance.destroy()
    vadInstance = null
  }

  currentParagraphId = null
}

function toggleRecording() {
  if (isRecording.value) {
    stopRecording()
  } else {
    startRecording()
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

// ── Submit a segment ──
async function submitSegment(blob, seq, paragraphId) {
  const placeholderId = `seg-${Date.now()}-${seq}`
  const entry = {
    id: placeholderId,
    seq,
    paragraphId,
    original: '',
    translated: '',
    timestamp: new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit', second: '2-digit' }),
    pending: true,
  }
  transcriptionHistory.value.unshift(entry)
  inflight.value++

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
    .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
    .replace(/^## (.+)$/gm, '<h3 class="text-[15px] font-semibold text-white/90 mt-4 mb-2 first:mt-0">$1</h3>')
    .replace(/^- \[ \] (.+)$/gm, '<div class="flex items-start gap-2 ml-2 mb-1"><span class="text-white/30 mt-0.5">☐</span><span class="text-[13px] text-white/70">$1</span></div>')
    .replace(/^- (.+)$/gm, '<div class="flex items-start gap-2 ml-2 mb-1"><span class="text-white/40 mt-0.5">•</span><span class="text-[13px] text-white/70">$1</span></div>')
    .replace(/\n{2,}/g, '<div class="h-2"></div>')
    .replace(/\n/g, '<br>')
    .replace(/\*\*(.+?)\*\*/g, '<strong class="text-white/90">$1</strong>')
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
}

function copyAll() {
  const resolved = paragraphs.value.filter(g => !g.pending)
  const text = resolved
    .map(g => `[${g.timestamp}]\n原文: ${g.original}\n译文: ${g.translated}`)
    .join('\n\n')
  navigator.clipboard.writeText(text)
}

function downloadText() {
  const resolved = paragraphs.value.filter(g => !g.pending)
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

const totalEntries = computed(() => paragraphs.value.filter(g => !g.pending).length)
const canGenerateMinutes = computed(() => {
  return paragraphs.value.filter(g => !g.pending && !g.original.startsWith('[Error')).length >= 3
})

onUnmounted(() => {
  if (isRecording.value) stopRecording()
})
</script>

<template>
  <div class="h-screen bg-black text-white selection:bg-ios-blue/30 selection:text-white pb-safe overflow-hidden relative font-ailab flex flex-col">
    <BackgroundOrbs />

    <!-- Header -->
    <header class="relative z-50 flex-none h-16 backdrop-blur-xl bg-black/30 border-b border-white/5">
      <div class="max-w-[1240px] mx-auto px-4 h-full flex items-center justify-between">
        <!-- Left -->
        <div class="flex items-center gap-3 w-[200px]">
          <router-link
            to="/ai-lab"
            class="w-8 h-8 rounded-full bg-white/10 hover:bg-white/20 text-white/70 hover:text-white flex items-center justify-center transition-colors"
            title="返回 AI Lab"
          >
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 19l-7-7m0 0l7-7m-7 7h18"/>
            </svg>
          </router-link>
          <span class="text-[15px] font-semibold tracking-tight text-white/90 font-display">Studio</span>
        </div>

        <!-- Center: Segmented Control -->
        <div class="flex-1 flex justify-center">
          <div class="bg-white/10 backdrop-blur-md p-1 rounded-full flex relative">
            <div
              class="absolute top-1 bottom-1 rounded-full bg-white/20 shadow-sm transition-all duration-300 ease-[cubic-bezier(0.4,0,0.2,1)]"
              :class="currentView === 'interpretation' ? 'left-1 w-[100px]' : 'left-[108px] w-[110px]'"
            ></div>
            <button
              @click="currentView = 'interpretation'"
              class="relative z-10 px-4 py-1.5 rounded-full text-[13px] font-medium transition-colors duration-200"
              :class="currentView === 'interpretation' ? 'text-white' : 'text-white/60 hover:text-white/80'"
            >
              🎙️ 转录翻译
            </button>
            <button
              @click="currentView = 'emoji'"
              class="relative z-10 px-4 py-1.5 rounded-full text-[13px] font-medium transition-colors duration-200"
              :class="currentView === 'emoji' ? 'text-white' : 'text-white/60 hover:text-white/80'"
            >
              🎭 表情包生成
            </button>
          </div>
        </div>

        <!-- Right: Provider badge -->
        <div class="flex items-center justify-end gap-2 w-[200px]">
          <span class="px-2 py-0.5 rounded-md bg-white/5 border border-white/5 text-[11px] font-medium text-white/40 uppercase tracking-wider">
            {{ currentView === 'interpretation' ? 'Groq + Cerebras' : 'Emoji-v1' }}
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
          <div class="flex-none flex items-end gap-4">
            <div class="flex items-center gap-3 flex-1">
              <div class="w-40">
                <LanguageSelector v-model="sourceLang" label="From" :disabled="isRecording || inflight > 0" />
              </div>
              <div class="pt-5 text-white/20">
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14 5l7 7m0 0l-7 7m7-7H3"/></svg>
              </div>
              <div class="w-40">
                <LanguageSelector v-model="targetLang" label="To" :disabled="isRecording || inflight > 0" :is-target="true" />
              </div>
            </div>
            <!-- Action buttons -->
            <div class="flex items-center gap-2">
              <button
                v-if="canGenerateMinutes"
                @click="generateMeetingMinutes"
                :disabled="generatingMinutes"
                class="px-3 py-2 rounded-xl bg-gradient-to-r from-purple-500/20 to-blue-500/20 hover:from-purple-500/30 hover:to-blue-500/30 border border-purple-500/20 hover:border-purple-500/30 text-[12px] text-purple-300 hover:text-purple-200 transition-all disabled:opacity-50"
              >
                <span v-if="generatingMinutes" class="flex items-center gap-1.5">
                  <span class="w-3 h-3 border-2 border-purple-400 border-t-transparent rounded-full animate-spin"></span>
                  生成中...
                </span>
                <span v-else>会议纪要</span>
              </button>
              <button
                v-if="transcriptionHistory.length"
                @click="copyAll"
                class="px-3 py-2 rounded-xl bg-white/5 hover:bg-white/10 border border-white/10 text-[12px] text-white/60 hover:text-white transition-colors"
              >复制全部</button>
              <button
                v-if="transcriptionHistory.length"
                @click="downloadText"
                class="px-3 py-2 rounded-xl bg-white/5 hover:bg-white/10 border border-white/10 text-[12px] text-white/60 hover:text-white transition-colors"
              >下载</button>
              <button
                v-if="transcriptionHistory.length"
                @click="clearHistory"
                class="px-3 py-2 rounded-xl bg-white/5 hover:bg-red-500/10 border border-white/10 text-[12px] text-white/40 hover:text-red-400 transition-colors"
              >清空</button>
            </div>
          </div>

          <!-- Input area: Record + Upload + Status -->
          <div class="flex-none ios-glass rounded-[20px] p-5 ring-1 ring-white/10">
            <div class="flex items-center justify-center gap-4">
              <!-- Recording timer -->
              <div v-if="isRecording" class="text-2xl font-light tabular-nums tracking-tighter text-white/80 font-display w-20 text-center">
                {{ formatTime(recordingTime) }}
              </div>

              <!-- Record button with attached upload icon -->
              <div class="relative">
                <button
                  @click="toggleRecording"
                  class="relative w-16 h-16 rounded-full flex items-center justify-center transition-all duration-300 group"
                  :class="isRecording
                    ? 'bg-ios-red shadow-lg shadow-ios-red/30'
                    : 'bg-white/10 hover:bg-white/15 border border-white/20 hover:border-white/30'"
                >
                  <!-- Pulse ring when recording -->
                  <div v-if="isRecording" class="absolute inset-0 rounded-full bg-ios-red/40 animate-ping"></div>
                  <!-- Mic / Stop icon -->
                  <svg v-if="!isRecording" class="w-7 h-7 text-white/80 group-hover:text-white transition-colors" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M12 1a3 3 0 00-3 3v8a3 3 0 006 0V4a3 3 0 00-3-3z"/>
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M19 10v2a7 7 0 01-14 0v-2"/>
                    <line x1="12" y1="19" x2="12" y2="23" stroke-width="1.5" stroke-linecap="round"/>
                    <line x1="8" y1="23" x2="16" y2="23" stroke-width="1.5" stroke-linecap="round"/>
                  </svg>
                  <svg v-else class="w-6 h-6 text-white relative z-10" fill="currentColor" viewBox="0 0 24 24">
                    <rect x="6" y="6" width="12" height="12" rx="2"/>
                  </svg>
                </button>

                <!-- Upload file: small icon at bottom-right of record button -->
                <input type="file" ref="fileInput" accept="audio/*,video/*" class="hidden" @change="handleFileSelect">
                <button
                  v-if="!isRecording"
                  @click="triggerFileSelect"
                  class="absolute -bottom-1 -right-1 w-7 h-7 rounded-full bg-white/10 hover:bg-white/20 border border-white/15 hover:border-white/30 flex items-center justify-center transition-all group/upload"
                  title="上传音频文件"
                >
                  <svg class="w-3.5 h-3.5 text-white/50 group-hover/upload:text-white/80 transition-colors" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15.172 7l-6.586 6.586a2 2 0 102.828 2.828l6.414-6.586a4 4 0 00-5.656-5.656l-6.415 6.585a6 6 0 108.486 8.486L20.5 13"/>
                  </svg>
                </button>
              </div>

              <!-- Inflight indicator -->
              <div v-if="inflight > 0" class="flex items-center gap-3 pl-2">
                <div class="w-5 h-5 border-2 border-ios-blue border-t-transparent rounded-full animate-spin"></div>
                <span class="text-[13px] text-ios-blue font-medium">
                  处理中 ({{ inflight }})
                </span>
              </div>
            </div>

            <!-- Error -->
            <div v-if="errorMsg" class="mt-3 text-center text-[12px] text-red-400">
              {{ errorMsg }}
            </div>
          </div>

          <!-- Results: two-column transcript by paragraphs -->
          <div ref="historyContainer" class="flex-1 overflow-y-auto custom-scrollbar min-h-0 space-y-3">
            <!-- Meeting minutes card -->
            <div
              v-if="showMinutes"
              class="rounded-2xl p-[1px] bg-gradient-to-br from-purple-500/40 via-blue-500/30 to-cyan-500/20"
            >
              <div class="bg-black/80 backdrop-blur-xl rounded-2xl p-5">
                <div class="flex items-center justify-between mb-4">
                  <div class="flex items-center gap-2">
                    <span class="text-[13px] font-semibold text-purple-300">会议纪要</span>
                    <div v-if="generatingMinutes" class="w-3 h-3 border-2 border-purple-400 border-t-transparent rounded-full animate-spin"></div>
                  </div>
                  <button
                    @click="closeMinutes"
                    class="w-6 h-6 rounded-full bg-white/5 hover:bg-white/10 flex items-center justify-center text-white/40 hover:text-white/70 transition-colors"
                  >
                    <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
                    </svg>
                  </button>
                </div>
                <div
                  v-if="meetingMinutes"
                  class="text-[13px] leading-relaxed text-white/70"
                  v-html="renderMinutesMarkdown(meetingMinutes)"
                ></div>
                <div v-else-if="generatingMinutes" class="text-[13px] text-white/30">
                  正在生成会议纪要...
                </div>
              </div>
            </div>

            <!-- Empty state -->
            <div v-if="!transcriptionHistory.length && inflight === 0 && !showMinutes" class="h-full flex items-center justify-center">
              <div class="text-center space-y-3 opacity-40">
                <div class="text-4xl">🎙️</div>
                <p class="text-[14px] text-white/60">录音或上传音频文件，自动转录并翻译</p>
                <p class="text-[11px] text-white/30">语音自动检测，停顿时自动切分 · Powered by Silero VAD + Groq + Cerebras</p>
              </div>
            </div>

            <!-- Two-column transcript table (paragraph groups) -->
            <div v-if="transcriptionHistory.length" class="ios-glass rounded-2xl ring-1 ring-white/10 overflow-hidden">
              <!-- Column headers -->
              <div class="grid grid-cols-2 gap-4 px-5 pt-3 pb-2 border-b border-white/5 sticky top-0 bg-black/60 backdrop-blur-md z-10">
                <span class="text-[10px] font-bold uppercase tracking-wider text-white/30">Original</span>
                <span class="text-[10px] font-bold uppercase tracking-wider text-ios-blue/60">Translation</span>
              </div>

              <!-- Rows: one per paragraph -->
              <div class="px-3 py-1">
                <div
                  v-for="group in paragraphs"
                  :key="group.paragraphId"
                  @mouseenter="hoveredId = group.paragraphId"
                  @mouseleave="hoveredId = null"
                  class="grid grid-cols-2 gap-4 py-2.5 px-2 rounded-lg transition-colors duration-100 cursor-default"
                  :class="hoveredId === group.paragraphId ? 'bg-white/[0.04]' : ''"
                >
                  <!-- Original (left) -->
                  <div>
                    <div v-if="group.pending === true && !group.original" class="flex items-center gap-2">
                      <span class="w-3 h-3 border-2 border-ios-blue border-t-transparent rounded-full animate-spin"></span>
                      <span class="text-[13px] text-white/30">转录中...</span>
                    </div>
                    <p v-else class="text-[14px] leading-relaxed text-white/80">
                      {{ group.original }}
                      <span v-if="group.pending" class="inline-flex items-center ml-1 align-middle">
                        <span class="w-2.5 h-2.5 border-[1.5px] border-ios-blue/50 border-t-transparent rounded-full animate-spin"></span>
                      </span>
                    </p>
                  </div>

                  <!-- Translation (right) -->
                  <div>
                    <div v-if="group.pending === true && !group.translated" class="text-[13px] text-white/[0.06]">&mdash;</div>
                    <div v-else-if="group.pending === 'translating' && !group.translated" class="flex items-center gap-2">
                      <span class="w-3 h-3 border-2 border-ios-blue/50 border-t-transparent rounded-full animate-spin"></span>
                      <span class="text-[13px] text-white/30">翻译中...</span>
                    </div>
                    <p v-else class="text-[14px] leading-relaxed text-white/90">
                      {{ group.translated }}
                      <span v-if="group.pending && group.translated" class="inline-flex items-center ml-1 align-middle">
                        <span class="w-2.5 h-2.5 border-[1.5px] border-ios-blue/50 border-t-transparent rounded-full animate-spin"></span>
                      </span>
                    </p>
                  </div>
                </div>
              </div>

              <!-- Stats footer -->
              <div class="px-5 py-2 border-t border-white/5 text-center">
                <span class="text-[11px] text-white/20">{{ totalEntries }} 段记录</span>
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
  </div>
</template>
