<script setup>
import { ref, onMounted, onUnmounted, computed, watch, reactive } from 'vue'
import RecordButton from '../components/ailab/RecordButton.vue'
import TranscriptionPanel from '../components/ailab/TranscriptionPanel.vue'
import LanguageSelector from '../components/ailab/LanguageSelector.vue'
import AudioVisualizer from '../components/ailab/AudioVisualizer.vue'
import BackgroundOrbs from '../components/ailab/BackgroundOrbs.vue'
import EmojiGenerator from '../components/ailab/EmojiGenerator.vue'
import { getAiLabApiBase, getAiLabWsBaseUrl } from '../config/aiLab'

const API_BASE = getAiLabApiBase()

// Current view
const currentView = ref('interpretation') // 'interpretation' or 'emoji'

// State
const isRecording = ref(false)
const isConnected = ref(false)
const connectionStatus = ref('disconnected')
const sourceLang = ref('en')
const targetLang = ref('Chinese')

// Two-tier mode selection
const inputType = ref('realtime') // 'realtime' or 'file'
const functionType = ref('simultaneous') // 'transcription', 'translation', 'simultaneous'

// Computed interpretationMode for backward compatibility
const interpretationMode = computed(() => {
  if (inputType.value === 'file') {
    // File mode only supports transcription and translation (not simultaneous)
    const fn = functionType.value === 'simultaneous' ? 'translation' : functionType.value
    return fn === 'transcription' ? 'file_asr' : 'file_translation'
  }
  return functionType.value
})

// Auto-switch to translation when going to file mode while in simultaneous mode
watch(inputType, (newType) => {
  if (newType === 'file' && functionType.value === 'simultaneous') {
    functionType.value = 'translation'
  }
}, { flush: 'sync' })

const translationEnabled = ref(true)
const recordingTime = ref(0)
const speechStatus = ref('idle')
const asrProvider = ref('dashscope') // 'dashscope' or 'groq' (high-speed mode)



// TTS Settings
const ttsEnabled = ref(false)
const ttsVoice = ref('Cherry')
const isPlayingAudio = ref(false)
const audioQueue = ref([])  // Queue for audio URLs to play
const ttsVoices = ref([])   // Available TTS voices from API
const showVoiceSelector = ref(false)  // Toggle for voice selector dropdown

// Transcription and translation results
const currentTranscription = ref('')
const transcriptionHistory = ref([])

// File ASR Logic
const fileASRInput = ref(null)
const fileASRState = reactive({
  status: 'idle', // idle, uploading, processing, success, error
  fileName: '',
  progress: 0,
  error: ''
})

function triggerASRFileSelect() {
  if (fileASRInput.value) fileASRInput.value.click()
}

async function handleASRFileSelect(event) {
  const file = event.target.files?.[0]
  if (!file) return
  
  fileASRState.status = 'uploading'
  fileASRState.fileName = file.name
  fileASRState.error = ''
  
  // Clear previous results
  transcriptionHistory.value = []
  currentTranscription.value = ''
  
  try {
    const formData = new FormData()
    formData.append('file', file)
    
    const apiBase = API_BASE
    
    // Choose API endpoint based on mode
    const endpoint = interpretationMode.value === 'file_translation' 
      ? 'submit-file-translation' 
      : 'submit-file-asr'
    
    const res = await fetch(`${apiBase}/api/interpretation/${endpoint}/`, {
      method: 'POST',
      body: formData
    })
    
    const contentType = res.headers.get('content-type')
    let data
    if (contentType && contentType.includes('application/json')) {
         data = await res.json()
    } else {
         const text = await res.text()
         console.error('Invalid response:', text.substring(0, 200))
         throw new Error(`Server returned non-JSON (${res.status})`)
    }
    
    if (data.success) {
      fileASRState.status = 'processing'
      pollASRResult(data.task_id, data.task_type)
    } else {
      throw new Error(data.error_message || 'Upload failed')
    }
  } catch (e) {
    fileASRState.status = 'error'
    fileASRState.error = e.message
  }
}

function pollASRResult(taskId, taskType = 'transcription') {
  const apiBase = API_BASE
  const poll = async () => {
    // Stop polling if error or switched away from file modes
    if (fileASRState.status === 'error' || 
        (interpretationMode.value !== 'file_asr' && interpretationMode.value !== 'file_translation')) return
    
    try {
        const res = await fetch(`${apiBase}/api/interpretation/get-asr-result/?task_id=${taskId}`)
        
        const contentType = res.headers.get('content-type')
        let data
        if (contentType && contentType.includes('application/json')) {
             data = await res.json()
        } else {
             const text = await res.text()
             console.error('Invalid poll response:', text.substring(0, 200))
             throw new Error(`Invalid response (${res.status})`)
        }
        
        if (data.success) {
            if (data.status === 'SUCCEEDED') {
                fileASRState.status = 'success'
                // Populate History with result
                if (data.full_text) {
                    const isTranslation = data.task_type === 'translation' || taskType === 'translation'
                    transcriptionHistory.value.push({
                        id: Date.now(),
                        original: data.full_text,
                        translated: null,
                        isFileASR: !isTranslation,
                        isFileTranslation: isTranslation,
                        isFinal: true,
                        timestamp: new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
                    })
                }
            } else if (data.status === 'FAILED') {
                fileASRState.status = 'error'
                const errorMsg = data.error_message || 'Task failed'
                const errorMap = {
                    'FILE_DOWNLOAD_FAILED': '文件云端处理失败，请检查文件是否损坏',
                    'INVALID_AUDIO': '音频格式无法识别',
                    'TASK_TIMEOUT': '处理超时'
                }
                fileASRState.error = errorMap[errorMsg] || `处理失败: ${errorMsg}`
            } else {
                // Still running
                setTimeout(poll, 2000)
            }
        } else {
             throw new Error(data.error_message)
        }
    } catch(e) {
        fileASRState.status = 'error'
        fileASRState.error = e.message
    }
  }
  poll()
}
const isTranslating = ref(false)  // Track if waiting for translation
const pendingTranscription = ref('')  // Store final transcription while waiting for translation

// Audio
const audioContext = ref(null)
const mediaStream = ref(null)
const analyserNode = ref(null)
const ttsAudioElement = ref(null)  // HTML Audio element for TTS playback

// WebSocket
const ws = ref(null)
const wsUrl = computed(() => `${getAiLabWsBaseUrl()}/ws/asr/`)

// Watch mode change to update flags (Moved here to ensure dependencies are initialized)
watch(interpretationMode, (newMode) => {
  console.log('Switching mode:', newMode)
  switch (newMode) {
    case 'transcription':
      translationEnabled.value = false
      ttsEnabled.value = false
      stopTTSPlayback()
      break
    case 'translation':
      translationEnabled.value = true
      ttsEnabled.value = false
      stopTTSPlayback()
      break
    case 'simultaneous':
      translationEnabled.value = true
      ttsEnabled.value = true
      break
    case 'file_asr':
    case 'file_translation':
      translationEnabled.value = false
      ttsEnabled.value = false
      stopTTSPlayback()
      // Reset file state when switching to file modes
      fileASRState.status = 'idle'
      fileASRState.fileName = ''
      fileASRState.error = ''
      break
  }
  
  // Send update to backend immediately
  sendWSMessage('config', { 
    translation_enabled: translationEnabled.value,
    tts_enabled: ttsEnabled.value 
  })
}, { immediate: true })

// Timer
let recordingInterval = null
let recordingStartTime = null
let reconnectTimer = null
let allowReconnect = true

// WebSocket handlers
function connectWebSocket() {
  connectionStatus.value = 'connecting'
  
  if (ws.value && ws.value.readyState === WebSocket.CONNECTING) {
    return
  }
  
  ws.value = new WebSocket(wsUrl.value)
  
  ws.value.onopen = () => {
    console.log('WebSocket connected')
    isConnected.value = true
    connectionStatus.value = 'connected'
  }
  
  ws.value.onclose = (event) => {
    console.log('WebSocket closed:', event.code)
    isConnected.value = false
    connectionStatus.value = 'disconnected'
    
    if (isRecording.value) {
      stopRecording()
    }
    
    scheduleReconnect()
  }
  
  ws.value.onerror = (error) => {
    console.error('WebSocket error:', error)
    connectionStatus.value = 'error'
  }
  
  ws.value.onmessage = (event) => {
    try {
      handleWSMessage(JSON.parse(event.data))
    } catch (error) {
      console.error('Invalid WebSocket message:', error)
    }
  }
}

function scheduleReconnect() {
  if (!allowReconnect || reconnectTimer) {
    return
  }
  
  reconnectTimer = setTimeout(() => {
    reconnectTimer = null
    connectWebSocket()
  }, 3000)
}

function handleWSMessage(message) {
  const { type, text, translated, original, is_final, audio_url } = message
  
  switch (type) {
    case 'connected':
    case 'started':
      console.log('Service:', message.message)
      break
      
    case 'transcription':
      if (is_final) {
        // Don't clear currentTranscription immediately!
        // Instead, store it as pending and mark as translating
        if (translationEnabled.value && text && text.trim()) {
          pendingTranscription.value = text
          isTranslating.value = true
          // Keep showing the text in currentTranscription until translation arrives
          currentTranscription.value = text
        } else if (!translationEnabled.value && text && text.trim()) {
          // If translation is disabled (transcription-only mode), add to history with null translated
          addToHistory(text, null)
          currentTranscription.value = ''
          isTranslating.value = false
        } else {
          currentTranscription.value = ''
          isTranslating.value = false
        }
      } else {
        // Intermediate result - just show it
        currentTranscription.value = text
        isTranslating.value = false
      }
      break
      
    case 'translation':
      // Translation arrived - NOW we can clear the current transcription
      currentTranscription.value = ''
      pendingTranscription.value = ''
      isTranslating.value = false
      addToHistory(original, translated)
      // Queue audio for playback if TTS is enabled
      console.log('[TTS] Translation received:', { audio_url, ttsEnabled: ttsEnabled.value })
      if (audio_url && ttsEnabled.value) {
        console.log('[TTS] Queueing audio:', audio_url.substring(0, 80))
        queueAudio(audio_url)
      }
      break
      
    case 'speech_start':
      speechStatus.value = 'speaking'
      break
      
    case 'speech_stop':
      speechStatus.value = 'silent'
      break
      
    case 'error':
      console.error('Server error:', message.message)
      break
  }
}

// TTS Audio Queue Management
function queueAudio(url) {
  audioQueue.value.push(url)
  if (!isPlayingAudio.value) {
    playNextAudio()
  }
}

function playNextAudio() {
  if (audioQueue.value.length === 0) {
    isPlayingAudio.value = false
    return
  }
  
  isPlayingAudio.value = true
  const url = audioQueue.value.shift()
  
  if (!ttsAudioElement.value) {
    ttsAudioElement.value = new Audio()
    ttsAudioElement.value.onended = () => {
      playNextAudio()
    }
    ttsAudioElement.value.onerror = (e) => {
      console.error('Audio playback error:', e)
      playNextAudio()  // Move to next audio on error
    }
  }
  
  ttsAudioElement.value.src = url
  ttsAudioElement.value.play().catch(err => {
    console.error('Failed to play audio:', err)
    playNextAudio()
  })
}

function stopTTSPlayback() {
  audioQueue.value = []
  isPlayingAudio.value = false
  if (ttsAudioElement.value) {
    ttsAudioElement.value.pause()
    ttsAudioElement.value.src = ''
  }
}

function toggleTTS() {
  ttsEnabled.value = !ttsEnabled.value
  // Update backend config
  sendWSMessage('config', { tts_enabled: ttsEnabled.value, tts_voice: ttsVoice.value })
  
  if (!ttsEnabled.value) {
    stopTTSPlayback()
  }
}

function sendWSMessage(type, data = {}) {
  if (ws.value && ws.value.readyState === WebSocket.OPEN) {
    ws.value.send(JSON.stringify({ type, ...data }))
  }
}

async function startRecording() {
  try {
    mediaStream.value = await navigator.mediaDevices.getUserMedia({
      audio: {
        channelCount: 1,
        sampleRate: 16000,
        echoCancellation: true,
        noiseSuppression: true,
      }
    })
    
    audioContext.value = new (window.AudioContext || window.webkitAudioContext)({
      sampleRate: 16000
    })
    
    const source = audioContext.value.createMediaStreamSource(mediaStream.value)
    
    analyserNode.value = audioContext.value.createAnalyser()
    analyserNode.value.fftSize = 256
    source.connect(analyserNode.value)
    
    const bufferSize = 4096
    const scriptProcessor = audioContext.value.createScriptProcessor(bufferSize, 1, 1)
    
    scriptProcessor.onaudioprocess = (e) => {
      if (!isRecording.value) return
      
      const inputData = e.inputBuffer.getChannelData(0)
      const pcmData = floatTo16BitPCM(inputData)
      const base64Audio = arrayBufferToBase64(pcmData.buffer)
      
      sendWSMessage('audio', { audio: base64Audio })
    }
    
    source.connect(scriptProcessor)
    scriptProcessor.connect(audioContext.value.destination)
    
    sendWSMessage('start', {
      source_lang: sourceLang.value,
      target_lang: targetLang.value,
      translation_enabled: translationEnabled.value,
      tts_enabled: ttsEnabled.value,
      tts_voice: ttsVoice.value,
      provider: asrProvider.value,  // 'dashscope' or 'groq'
    })
    
    isRecording.value = true
    recordingStartTime = Date.now()
    startTimer()
    
  } catch (error) {
    console.error('Failed to start recording:', error)
    alert('无法访问麦克风，请检查权限设置')
  }
}

async function stopRecording() {
  isRecording.value = false
  speechStatus.value = 'idle'
  stopTimer()
  stopTTSPlayback()  // Stop any playing audio
  
  if (mediaStream.value) {
    mediaStream.value.getTracks().forEach(track => track.stop())
    mediaStream.value = null
  }
  
  if (audioContext.value) {
    await audioContext.value.close()
    audioContext.value = null
  }
  
  sendWSMessage('stop')
}

function toggleRecording() {
  if (isRecording.value) {
    stopRecording()
  } else {
    startRecording()
  }
}

function startTimer() {
  recordingInterval = setInterval(() => {
    recordingTime.value = Math.floor((Date.now() - recordingStartTime) / 1000)
  }, 1000)
}

function stopTimer() {
  if (recordingInterval) {
    clearInterval(recordingInterval)
    recordingInterval = null
  }
}

function formatTime(seconds) {
  const mins = Math.floor(seconds / 60)
  const secs = seconds % 60
  return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
}

function addToHistory(original, translated) {
  transcriptionHistory.value.push({
    id: Date.now(),
    original,
    translated,
    timestamp: new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
  })
}

function clearHistory() {
  transcriptionHistory.value = []
}

function copyAll() {
  const text = transcriptionHistory.value
    .map(item => `[${item.timestamp}]\n原文: ${item.original}\n译文: ${item.translated}`)
    .join('\n\n')
  
  navigator.clipboard.writeText(text)
}

function downloadText() {
  const text = transcriptionHistory.value
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

function floatTo16BitPCM(float32Array) {
  const int16Array = new Int16Array(float32Array.length)
  for (let i = 0; i < float32Array.length; i++) {
    const s = Math.max(-1, Math.min(1, float32Array[i]))
    int16Array[i] = s < 0 ? s * 0x8000 : s * 0x7FFF
  }
  return int16Array
}

function arrayBufferToBase64(buffer) {
  const bytes = new Uint8Array(buffer)
  let binary = ''
  for (let i = 0; i < bytes.byteLength; i++) {
    binary += String.fromCharCode(bytes[i])
  }
  return btoa(binary)
}

const totalChars = computed(() => {
  return transcriptionHistory.value.reduce(
    (sum, item) => sum + (item.translated?.length || 0),
    0
  )
})

// Switch view handler - stop recording if switching away from interpretation
watch(currentView, (newView) => {
  if (newView !== 'interpretation' && isRecording.value) {
    stopRecording()
  }
})

// Load available TTS voices from API
async function loadTTSVoices() {
  try {
    const response = await fetch(`${API_BASE}/api/interpretation/tts-voices/`)
    if (response.ok) {
      const data = await response.json()
      ttsVoices.value = data.voices || []
      console.log('Loaded TTS voices:', ttsVoices.value.length)
    }
  } catch (error) {
    console.error('Failed to load TTS voices:', error)
    // Fallback to default voices
    ttsVoices.value = [
      { id: 'Cherry', emoji: '🌸', description: '芊悦 - 阳光积极的女声', gender: 'female' },
      { id: 'Ethan', emoji: '☀️', description: '晨煦 - 阳光温暖的男声', gender: 'male' },
      { id: 'Jennifer', emoji: '🎬', description: '詹妮弗 - 电影质感美语女声', gender: 'female' },
      { id: 'Ryan', emoji: '🎭', description: '甜茶 - 节奏感强的男声', gender: 'male' },
    ]
  }
}

// Select a voice
function selectVoice(voiceId) {
  ttsVoice.value = voiceId
  showVoiceSelector.value = false
  // Update backend if TTS is enabled
  if (ttsEnabled.value) {
    sendWSMessage('config', { tts_voice: voiceId })
  }
}

// Get current voice info
const currentVoiceInfo = computed(() => {
  const voice = ttsVoices.value.find(v => v.id === ttsVoice.value)
  return voice || { id: ttsVoice.value, emoji: '🔊', description: ttsVoice.value }
})

onMounted(() => {
  connectWebSocket()
  loadTTSVoices()
})

onUnmounted(() => {
  allowReconnect = false
  if (reconnectTimer) {
    clearTimeout(reconnectTimer)
    reconnectTimer = null
  }
  if (ws.value) {
    ws.value.close()
  }
  stopRecording()
})
</script>

<template>

  <div class="h-screen bg-black text-white selection:bg-ios-blue/30 selection:text-white pb-safe overflow-hidden relative font-ailab flex flex-col">
    <!-- Global Animated Background -->
    <BackgroundOrbs />

    <!-- Unified Global Header -->
    <header class="relative z-50 flex-none h-16 transition-all duration-300 backdrop-blur-xl bg-black/30 border-b border-white/5">
      <div class="max-w-[1240px] mx-auto px-4 h-full flex items-center justify-between">
        
        <!-- Left: Status & Identity -->
        <div class="flex items-center gap-3 w-[200px]">
          <router-link
            to="/kitchen/ai-lab"
            class="w-8 h-8 rounded-full bg-white/10 hover:bg-white/20 text-white/70 hover:text-white flex items-center justify-center transition-colors"
            title="返回 AI Lab"
          >
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 19l-7-7m0 0l7-7m-7 7h18"/>
            </svg>
          </router-link>
          <!-- Connection Status Dot -->
          <div class="relative flex h-3 w-3">
             <span v-if="isConnected" class="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
             <span class="relative inline-flex rounded-full h-3 w-3 transition-colors duration-500" :class="isConnected ? 'bg-green-500' : 'bg-red-500'"></span>
          </div>
          <span class="text-[15px] font-semibold tracking-tight text-white/90 font-display">SimulTrans</span>
        </div>

        <!-- Center: iOS Segmented Control -->
        <div class="flex-1 flex justify-center">
          <div class="bg-white/10 backdrop-blur-md p-1 rounded-full flex relative">
            <!-- Gliding Background -->
            <div 
              class="absolute top-1 bottom-1 rounded-full bg-white/20 shadow-sm transition-all duration-300 ease-[cubic-bezier(0.4,0,0.2,1)]"
              :class="currentView === 'interpretation' ? 'left-1 w-[100px]' : 'left-[108px] w-[110px]'"
            ></div>
            
            <button
              @click="currentView = 'interpretation'"
              class="relative z-10 px-4 py-1.5 rounded-full text-[13px] font-medium transition-colors duration-200"
              :class="currentView === 'interpretation' ? 'text-white' : 'text-white/60 hover:text-white/80'"
            >
              🎙️ 同声传译
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

        <!-- Right: Model Info -->
        <div class="flex items-center justify-end gap-3 w-[200px]">
           <span class="px-2 py-0.5 rounded-md bg-white/5 border border-white/5 text-[11px] font-medium text-white/40 uppercase tracking-wider">
             {{ currentView === 'interpretation' ? 'Qwen-Realtime' : 'Emoji-v1' }}
           </span>
        </div>
      </div>
    </header>

    <!-- Main Content Area -->
    <main class="relative z-10 flex-1 overflow-hidden">
      <div class="max-w-[1240px] mx-auto px-4 py-6 h-full">
        
        <!-- Interpretation View -->
          <div v-show="currentView === 'interpretation'" class="grid grid-cols-1 lg:grid-cols-12 gap-6 h-full">
            
            <!-- Left: Control Center -->
            <section class="lg:col-span-4 h-full overflow-hidden">
              <!-- Single scrollable card -->
              <div class="ios-glass h-full p-5 rounded-[24px] flex flex-col shadow-2xl ring-1 ring-white/10 overflow-y-auto custom-scrollbar">
                
                <!-- Timer Section (compact) -->
                <div v-if="interpretationMode !== 'file_asr' && interpretationMode !== 'file_translation'" class="flex flex-col items-center py-3 border-b border-white/5">
                  <span class="text-[10px] font-bold text-white/40 uppercase tracking-[0.15em] mb-1">Session Time</span>
                  <div class="text-4xl font-light tabular-nums tracking-tighter text-white/90 font-display">
                    {{ formatTime(recordingTime) }}
                  </div>
                </div>

                <!-- Recording Button Section -->
                <div v-if="interpretationMode !== 'file_asr' && interpretationMode !== 'file_translation'" class="flex flex-col items-center py-4 border-b border-white/5">
                  <div class="relative group">
                    <div class="absolute inset-0 bg-ios-red/30 rounded-full blur-2xl group-hover:blur-3xl transition-all duration-500 opacity-0 group-hover:opacity-100" :class="{ 'opacity-100 animate-pulse-slow': isRecording }"></div>
                    <RecordButton 
                      :is-recording="isRecording"
                      :disabled="!isConnected"
                      @click="toggleRecording"
                    />
                  </div>
                  
                  <!-- Status Text -->
                  <div class="h-5 flex items-center justify-center mt-3">
                     <span 
                       class="px-3 py-0.5 rounded-full text-[11px] font-medium transition-all duration-300 border"
                       :class="speechStatus === 'speaking' 
                         ? 'bg-green-500/10 border-green-500/20 text-green-400' 
                         : (isRecording ? 'bg-white/5 border-white/10 text-white/60' : 'bg-transparent border-transparent text-white/30')"
                     >
                       {{ speechStatus === 'speaking' ? 'Detected Speech' : (isRecording ? 'Listening...' : 'Ready') }}
                     </span>
                  </div>
                  
                  <!-- Visualizer -->
                  <div class="w-full h-10 flex items-end justify-center mt-2 opacity-60 mix-blend-screen">
                     <AudioVisualizer 
                        :is-active="isRecording"
                        :analyser="analyserNode"
                      />
                  </div>
                </div>

                <!-- File Upload UI (Visible in File ASR/Translation Mode) -->
                <div v-if="interpretationMode === 'file_asr' || interpretationMode === 'file_translation'" class="flex flex-col items-center py-6 border-b border-white/5">
                     <input type="file" ref="fileASRInput" accept="audio/*,video/*" class="hidden" @change="handleASRFileSelect">
                     
                     <div 
                        @click="triggerASRFileSelect"
                        class="w-full aspect-square max-w-[180px] rounded-[24px] border-2 border-dashed border-white/10 bg-white/5 flex flex-col items-center justify-center gap-3 cursor-pointer hover:bg-white/10 hover:border-ios-blue/30 transition-all group relative overflow-hidden"
                     >
                        <!-- Loading Overlay -->
                        <div v-if="fileASRState.status === 'uploading' || fileASRState.status === 'processing'" class="absolute inset-0 bg-black/60 backdrop-blur-sm flex flex-col items-center justify-center z-20">
                            <div class="w-8 h-8 border-2 border-ios-blue border-t-transparent rounded-full animate-spin mb-2"></div>
                            <span class="text-[10px] font-medium tracking-wider uppercase opacity-80">{{ fileASRState.status === 'uploading' ? 'Uploading...' : 'Processing...' }}</span>
                        </div>

                        <div class="w-12 h-12 rounded-full bg-white/5 flex items-center justify-center">
                            <span class="text-2xl text-white/60">{{ interpretationMode === 'file_translation' ? '🌐' : '📂' }}</span>
                        </div>
                        <div class="text-center space-y-0.5">
                            <div class="text-xs font-medium text-white/90">
                              {{ interpretationMode === 'file_translation' ? '上传音频翻译' : '上传音频转译' }}
                            </div>
                            <div class="text-[9px] text-white/40">
                              {{ interpretationMode === 'file_translation' ? '翻译为英文 (Groq)' : '转写为原语言 (Groq)' }}
                            </div>
                        </div>
                     </div>
                     
                     <!-- Status / Filename -->
                     <div v-if="fileASRState.fileName" class="mt-4 flex flex-col items-center gap-1">
                        <div class="flex items-center gap-2 px-3 py-1.5 rounded-full bg-white/5 border border-white/10">
                           <span class="text-sm">🎵</span>
                           <span class="text-[10px] font-medium text-white/80 max-w-[120px] truncate">{{ fileASRState.fileName }}</span>
                        </div>
                        <span v-if="fileASRState.status === 'success'" class="text-green-400 text-[9px] font-bold uppercase tracking-wider">Completed</span>
                        <span v-else-if="fileASRState.status === 'error'" class="text-red-400 text-[9px] font-bold uppercase tracking-wider">Error</span>
                     </div>
                     
                     <div v-if="fileASRState.error" class="mt-3 text-[10px] text-red-400 px-3 text-center max-w-[220px]">
                        {{ fileASRState.error }}
                     </div>
                </div>

                <!-- Settings Section -->
                <div class="flex-1 pt-4 space-y-4">
                  <!-- Languages -->
                  <div class="flex items-center gap-3">
                    <div class="flex-1">
                       <LanguageSelector v-model="sourceLang" label="From" :disabled="isRecording" />
                    </div>
                    <div class="pt-5 text-white/20">
                      <svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor"><path d="M17 11l-5-5-5 5M17 13l-5 5-5-5" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>
                    </div>
                    <div class="flex-1">
                       <LanguageSelector v-model="targetLang" label="To" :disabled="isRecording" :is-target="true" />
                    </div>
                  </div>
                  
                  <!-- Mode Selection & Voice -->
                  <div class="space-y-4 pt-2">
                    <!-- Input Type Selector -->
                    <div>
                      <div class="flex items-center justify-between mb-2">
                        <label class="text-[11px] font-medium text-white/40 uppercase tracking-wider">输入方式</label>
                        <span v-if="isPlayingAudio" class="text-[10px] text-ios-blue animate-pulse font-medium">Playing Audio...</span>
                      </div>
                      
                      <div class="flex gap-2 p-1 bg-black/20 rounded-xl border border-white/5">
                        <button 
                          @click="inputType = 'realtime'"
                          class="flex-1 flex items-center justify-center gap-2 py-2.5 rounded-lg transition-all duration-200"
                          :class="inputType === 'realtime' ? 'bg-white/10 text-white shadow-sm ring-1 ring-white/10' : 'text-white/40 hover:bg-white/5 hover:text-white/60'"
                          :disabled="isRecording"
                        >
                          <span class="text-lg">🎙️</span>
                          <span class="text-[12px] font-medium">实时录音</span>
                        </button>
                        <button 
                          @click="inputType = 'file'"
                          class="flex-1 flex items-center justify-center gap-2 py-2.5 rounded-lg transition-all duration-200"
                          :class="inputType === 'file' ? 'bg-white/10 text-white shadow-sm ring-1 ring-white/10' : 'text-white/40 hover:bg-white/5 hover:text-white/60'"
                          :disabled="isRecording"
                        >
                          <span class="text-lg">📁</span>
                          <span class="text-[12px] font-medium">文件上传</span>
                        </button>
                      </div>
                    </div>
                    
                    <!-- Function Selector -->
                    <div>
                      <label class="text-[11px] font-medium text-white/40 uppercase tracking-wider mb-2 block">功能选择</label>
                      
                      <!-- Realtime Mode: 3 buttons -->
                      <div v-show="inputType === 'realtime'" class="grid grid-cols-3 gap-2 p-1 bg-black/20 rounded-xl border border-white/5">
                        <button 
                          @click="functionType = 'transcription'"
                          class="relative flex flex-col items-center justify-center py-3 rounded-lg transition-all duration-200"
                          :class="functionType === 'transcription' ? 'bg-gradient-to-b from-blue-500/20 to-blue-500/5 text-white shadow-sm ring-1 ring-blue-500/30' : 'text-white/40 hover:bg-white/5 hover:text-white/60'"
                          :disabled="isRecording"
                        >
                          <span class="text-xl mb-1">📝</span>
                          <span class="text-[11px] font-medium">转译</span>
                          <span class="text-[9px] text-white/40 mt-0.5">仅语音识别</span>
                        </button>
                        
                        <button 
                          @click="functionType = 'translation'"
                          class="relative flex flex-col items-center justify-center py-3 rounded-lg transition-all duration-200"
                          :class="functionType === 'translation' ? 'bg-gradient-to-b from-green-500/20 to-green-500/5 text-white shadow-sm ring-1 ring-green-500/30' : 'text-white/40 hover:bg-white/5 hover:text-white/60'"
                          :disabled="isRecording"
                        >
                          <span class="text-xl mb-1">🌐</span>
                          <span class="text-[11px] font-medium">翻译</span>
                          <span class="text-[9px] text-white/40 mt-0.5">识别 + 翻译</span>
                        </button>
                        
                        <button 
                          @click="functionType = 'simultaneous'"
                          class="relative flex flex-col items-center justify-center py-3 rounded-lg transition-all duration-200"
                          :class="functionType === 'simultaneous' ? 'bg-gradient-to-b from-purple-500/20 to-purple-500/5 text-white shadow-sm ring-1 ring-purple-500/30' : 'text-white/40 hover:bg-white/5 hover:text-white/60'"
                          :disabled="isRecording"
                        >
                          <span class="text-xl mb-1">🎧</span>
                          <span class="text-[11px] font-medium">同传</span>
                          <span class="text-[9px] text-white/40 mt-0.5">识别+翻译+语音</span>
                        </button>
                      </div>
                      
                      <!-- File Mode: 2 buttons only -->
                      <div v-show="inputType === 'file'" class="grid grid-cols-2 gap-2 p-1 bg-black/20 rounded-xl border border-white/5">
                        <button 
                          @click="functionType = 'transcription'"
                          class="relative flex flex-col items-center justify-center py-3 rounded-lg transition-all duration-200"
                          :class="functionType === 'transcription' ? 'bg-gradient-to-b from-blue-500/20 to-blue-500/5 text-white shadow-sm ring-1 ring-blue-500/30' : 'text-white/40 hover:bg-white/5 hover:text-white/60'"
                        >
                          <span class="text-xl mb-1">📝</span>
                          <span class="text-[11px] font-medium">转译</span>
                          <span class="text-[9px] text-white/40 mt-0.5">仅语音识别</span>
                        </button>
                        
                        <button 
                          @click="functionType = 'translation'"
                          class="relative flex flex-col items-center justify-center py-3 rounded-lg transition-all duration-200"
                          :class="functionType === 'translation' || functionType === 'simultaneous' ? 'bg-gradient-to-b from-green-500/20 to-green-500/5 text-white shadow-sm ring-1 ring-green-500/30' : 'text-white/40 hover:bg-white/5 hover:text-white/60'"
                        >
                          <span class="text-xl mb-1">🌐</span>
                          <span class="text-[11px] font-medium">翻译</span>
                          <span class="text-[9px] text-white/40 mt-0.5">识别 + 翻译</span>
                        </button>
                      </div>
                    </div>
                    
                    <!-- High-Speed Mode Toggle (Groq) - only for realtime translation -->
                    <div v-show="inputType === 'realtime' && functionType === 'translation'" class="flex items-center justify-between p-3 bg-gradient-to-r from-orange-500/10 to-yellow-500/10 rounded-xl border border-orange-500/20">
                      <div class="flex items-center gap-2">
                        <span class="text-lg">⚡</span>
                        <div>
                          <span class="text-[12px] font-medium text-white/90">高速模式</span>
                          <span class="text-[10px] text-white/50 block">Groq Whisper + GPT</span>
                        </div>
                      </div>
                      <button 
                        @click="asrProvider = asrProvider === 'groq' ? 'dashscope' : 'groq'"
                        class="relative w-12 h-6 rounded-full transition-colors duration-200"
                        :class="asrProvider === 'groq' ? 'bg-orange-500' : 'bg-white/20'"
                        :disabled="isRecording"
                      >
                        <span 
                          class="absolute top-0.5 w-5 h-5 bg-white rounded-full shadow-lg transition-transform duration-200"
                          :class="asrProvider === 'groq' ? 'left-[26px]' : 'left-0.5'"
                        ></span>
                      </button>
                    </div>
                    
                    <!-- Voice Selector - only for realtime simultaneous -->
                    <div v-show="inputType === 'realtime' && functionType === 'simultaneous'" class="space-y-2">
                      <label class="text-[11px] font-medium text-white/40 uppercase tracking-wider pl-1">AI Voice</label>
                      
                      <!-- Horizontal Scrollable Voice Badges -->
                      <div class="flex gap-2 overflow-x-auto pb-2 no-scrollbar">
                        <button
                          v-for="voice in ttsVoices"
                          :key="voice.id"
                          @click="selectVoice(voice.id)"
                          class="flex-shrink-0 flex items-center gap-2 px-3 py-2 rounded-full border transition-all duration-200"
                          :class="voice.id === ttsVoice 
                            ? 'bg-ios-blue/20 border-ios-blue/50 text-white shadow-lg shadow-ios-blue/20' 
                            : 'bg-white/5 border-white/10 text-white/70 hover:bg-white/10 hover:border-white/20'"
                          :disabled="isRecording"
                        >
                          <span class="text-lg">{{ voice.emoji }}</span>
                          <span class="text-[12px] font-medium whitespace-nowrap">{{ voice.id }}</span>
                        </button>
                      </div>
                      
                      <!-- Current Voice Description -->
                      <div class="flex items-center gap-2 px-2 py-1.5 rounded-lg bg-white/5 border border-white/5">
                        <span class="text-lg">{{ currentVoiceInfo.emoji }}</span>
                        <span class="text-[11px] text-white/50 truncate">{{ currentVoiceInfo.description }}</span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </section>

            <!-- Right: Transcript Flow -->
            <section class="lg:col-span-8 h-full overflow-hidden">
              <TranscriptionPanel
                :current-transcription="currentTranscription"
                :history="transcriptionHistory"
                :total-chars="totalChars"
                :is-translating="isTranslating"
                @clear="clearHistory"
                @copy="copyAll"
                @download="downloadText"
              />
            </section>
          </div>

          <!-- Emoji Generator View -->
          <div v-show="currentView === 'emoji'" class="min-h-[calc(100vh-120px)]">
            <EmojiGenerator />
          </div>

      </div>
    </main>
  </div>
</template>
