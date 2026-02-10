<script setup>
import { ref, nextTick, onUnmounted, computed } from 'vue'
import { useRoute } from 'vue-router'
import LanguageSelector from '../components/ailab/LanguageSelector.vue'
import BackgroundOrbs from '../components/ailab/BackgroundOrbs.vue'
import EmojiGenerator from '../components/ailab/EmojiGenerator.vue'
import { getAiLabApiBase } from '../config/aiLab'

const API_BASE = getAiLabApiBase()
const route = useRoute()

const SEGMENT_SECONDS = 3 // auto-split interval

// View toggle
const currentView = ref(route.query.view === 'emoji' ? 'emoji' : 'interpretation')

// Language
const sourceLang = ref('en')
const targetLang = ref('Chinese')

// State
const errorMsg = ref('')
const inflight = ref(0) // number of segments being processed
const isRecording = ref(false)
const recordingTime = ref(0)

let mediaStream = null
let mediaRecorder = null
let recordedChunks = []
let timerInterval = null
let segmentInterval = null
let recordingStartTime = null
let segmentSeq = 0 // monotonic ordering

// File input
const fileInput = ref(null)

// History — items can be pending (placeholder) or resolved
// { id, seq, original, translated, timestamp, pending }
const transcriptionHistory = ref([])
const historyContainer = ref(null)

// ── Recording with auto-segmentation ──
async function startRecording() {
  try {
    mediaStream = await navigator.mediaDevices.getUserMedia({ audio: true })
    segmentSeq = 0
    isRecording.value = true
    recordingTime.value = 0
    recordingStartTime = Date.now()
    errorMsg.value = ''

    // Timer display
    timerInterval = setInterval(() => {
      recordingTime.value = Math.floor((Date.now() - recordingStartTime) / 1000)
    }, 200)

    startNewSegment()

    // Auto-split every N seconds
    segmentInterval = setInterval(() => {
      rotateSegment()
    }, SEGMENT_SECONDS * 1000)
  } catch (e) {
    errorMsg.value = '无法访问麦克风，请检查权限设置'
  }
}

function startNewSegment() {
  recordedChunks = []
  mediaRecorder = new MediaRecorder(mediaStream, { mimeType: 'audio/webm;codecs=opus' })
  mediaRecorder.ondataavailable = (e) => {
    if (e.data.size > 0) recordedChunks.push(e.data)
  }
  mediaRecorder.start()
}

function rotateSegment() {
  if (!mediaRecorder || mediaRecorder.state === 'inactive') return
  // Capture current chunks callback before stopping
  const chunks = recordedChunks
  const seq = segmentSeq++

  mediaRecorder.onstop = () => {
    const blob = new Blob(chunks, { type: 'audio/webm' })
    if (blob.size > 0) {
      submitSegment(blob, seq)
    }
  }
  mediaRecorder.stop()

  // Immediately start next segment on the same stream
  if (isRecording.value && mediaStream) {
    startNewSegment()
  }
}

function stopRecording() {
  isRecording.value = false
  clearInterval(timerInterval)
  clearInterval(segmentInterval)
  timerInterval = null
  segmentInterval = null

  // Flush final segment
  if (mediaRecorder && mediaRecorder.state !== 'inactive') {
    const chunks = recordedChunks
    const seq = segmentSeq++
    mediaRecorder.onstop = () => {
      const blob = new Blob(chunks, { type: 'audio/webm' })
      if (blob.size > 0) {
        submitSegment(blob, seq)
      }
    }
    mediaRecorder.stop()
  }

  if (mediaStream) {
    mediaStream.getTracks().forEach(t => t.stop())
    mediaStream = null
  }
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
    buffer = lines.pop() // keep incomplete trailing line

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

// ── Submit a segment (fire-and-forget, updates history in place) ──
async function submitSegment(blob, seq) {
  const placeholderId = `seg-${Date.now()}-${seq}`
  const entry = {
    id: placeholderId,
    seq,
    original: '',
    translated: '',
    timestamp: new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit', second: '2-digit' }),
    pending: true,
  }
  transcriptionHistory.value.unshift(entry)
  inflight.value++

  await nextTick()
  if (historyContainer.value) {
    historyContainer.value.scrollTop = 0
  }

  try {
    const formData = new FormData()
    formData.append('file', blob, 'segment.webm')
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

  const entry = {
    id: `file-${Date.now()}`,
    seq: -1,
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

// ── Utilities ──
function formatTime(seconds) {
  const mins = Math.floor(seconds / 60)
  const secs = seconds % 60
  return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
}

function clearHistory() {
  transcriptionHistory.value = []
}

function copyAll() {
  const resolved = transcriptionHistory.value.filter(i => !i.pending)
  const text = resolved
    .map(item => `[${item.timestamp}]\n原文: ${item.original}\n译文: ${item.translated}`)
    .join('\n\n')
  navigator.clipboard.writeText(text)
}

function downloadText() {
  const resolved = transcriptionHistory.value.filter(i => !i.pending)
  const text = resolved
    .map(item => `[${item.timestamp}]\n原文: ${item.original}\n译文: ${item.translated}`)
    .join('\n\n')
  const blob = new Blob([text], { type: 'text/plain;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `translation_${new Date().toISOString().slice(0, 10)}.txt`
  a.click()
  URL.revokeObjectURL(url)
}

const totalEntries = computed(() => transcriptionHistory.value.filter(i => !i.pending).length)

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
            <div class="flex items-center justify-center gap-6">
              <!-- Recording timer -->
              <div v-if="isRecording" class="text-2xl font-light tabular-nums tracking-tighter text-white/80 font-display w-20 text-center">
                {{ formatTime(recordingTime) }}
              </div>

              <!-- Record button -->
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

              <!-- Divider -->
              <div class="w-px h-10 bg-white/10"></div>

              <!-- Upload button -->
              <input type="file" ref="fileInput" accept="audio/*,video/*" class="hidden" @change="handleFileSelect">
              <button
                @click="triggerFileSelect"
                :disabled="isRecording"
                class="flex items-center gap-2 px-5 py-3 rounded-2xl bg-white/5 hover:bg-white/10 border border-white/10 hover:border-white/20 transition-all disabled:opacity-40"
              >
                <svg class="w-5 h-5 text-white/60" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12"/>
                </svg>
                <span class="text-[13px] text-white/70 font-medium">上传文件</span>
              </button>

              <!-- Inflight indicator -->
              <div v-if="inflight > 0" class="flex items-center gap-3 pl-4">
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

          <!-- Results: scrollable history -->
          <div ref="historyContainer" class="flex-1 overflow-y-auto custom-scrollbar space-y-3 min-h-0">
            <div v-if="!transcriptionHistory.length && inflight === 0" class="h-full flex items-center justify-center">
              <div class="text-center space-y-3 opacity-40">
                <div class="text-4xl">🎙️</div>
                <p class="text-[14px] text-white/60">录音或上传音频文件，自动转录并翻译</p>
                <p class="text-[11px] text-white/30">Powered by Groq Whisper + Cerebras Qwen3-32B</p>
              </div>
            </div>

            <div
              v-for="item in transcriptionHistory"
              :key="item.id"
              class="ios-glass rounded-2xl p-5 ring-1 transition-all"
              :class="item.pending === true ? 'ring-ios-blue/20 animate-pulse' : item.pending === 'translating' ? 'ring-ios-blue/10' : 'ring-white/5 hover:ring-white/10'"
            >
              <!-- Fully pending: transcribing -->
              <div v-if="item.pending === true" class="flex items-center gap-3">
                <div class="w-4 h-4 border-2 border-ios-blue border-t-transparent rounded-full animate-spin"></div>
                <span class="text-[13px] text-white/40">转录中...</span>
                <span class="text-[11px] text-white/20 ml-auto">{{ item.timestamp }}</span>
              </div>
              <!-- Partial: transcription done, translating -->
              <template v-else-if="item.pending === 'translating'">
                <div class="flex items-start justify-between mb-3">
                  <span class="text-[11px] text-white/30 font-medium">{{ item.timestamp }}</span>
                </div>
                <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <div class="text-[10px] font-bold uppercase tracking-wider text-white/30 mb-1.5">Original</div>
                    <p class="text-[14px] leading-relaxed text-white/80">{{ item.original }}</p>
                  </div>
                  <div>
                    <div class="text-[10px] font-bold uppercase tracking-wider text-ios-blue/60 mb-1.5">Translation</div>
                    <div class="flex items-center gap-2">
                      <div class="w-3 h-3 border-2 border-ios-blue/50 border-t-transparent rounded-full animate-spin"></div>
                      <span class="text-[13px] text-white/30">翻译中...</span>
                    </div>
                  </div>
                </div>
              </template>
              <!-- Resolved result -->
              <template v-else>
                <div class="flex items-start justify-between mb-3">
                  <span class="text-[11px] text-white/30 font-medium">{{ item.timestamp }}</span>
                </div>
                <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <div class="text-[10px] font-bold uppercase tracking-wider text-white/30 mb-1.5">Original</div>
                    <p class="text-[14px] leading-relaxed text-white/80">{{ item.original }}</p>
                  </div>
                  <div>
                    <div class="text-[10px] font-bold uppercase tracking-wider text-ios-blue/60 mb-1.5">Translation</div>
                    <p class="text-[14px] leading-relaxed text-white/90">{{ item.translated }}</p>
                  </div>
                </div>
              </template>
            </div>
          </div>

          <!-- Bottom stats -->
          <div v-if="transcriptionHistory.length" class="flex-none text-center py-2">
            <span class="text-[11px] text-white/20">{{ totalEntries }} 条记录</span>
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
