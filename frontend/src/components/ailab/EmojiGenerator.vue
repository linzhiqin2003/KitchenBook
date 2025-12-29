<script setup>
import { ref, computed, onMounted } from 'vue'
import { getAiLabApiBase } from '../../config/aiLab'

// Configuration
const API_BASE = getAiLabApiBase()

// State
const imageUrl = ref('')
const imagePreview = ref(null)
const selectedTemplate = ref('mengwa_kaixin')
const templates = ref([])
const categories = ref({})
const activeCategory = ref('萌娃')

const categoryList = computed(() => {
  return Object.keys(categories.value)
})

const currentCategoryTemplates = computed(() => {
  return categories.value[activeCategory.value] || []
})
const isLoading = ref(false)
const isUploading = ref(false)  // Track file upload status
const currentStep = ref('idle') // idle, uploading, detecting, creating, polling, completed, error
const taskId = ref(null)
const progress = ref(0)
const resultVideoUrl = ref(null)
const errorMessage = ref(null)
const detectionResult = ref(null)
const fileInputRef = ref(null)  // Reference to hidden file input

// Poll configuration
const POLL_INTERVAL = 3000 // 3 seconds
let pollTimer = null

// Computed
const canGenerate = computed(() => {
  return imageUrl.value.trim() !== '' && !isLoading.value
})

const statusText = computed(() => {
  switch (currentStep.value) {
    case 'uploading': return '正在上传图片...'
    case 'detecting': return '正在检测人脸...'
    case 'creating': return '正在创建生成任务...'
    case 'polling': return '正在生成表情包视频...'
    case 'completed': return '生成完成！'
    case 'error': return '生成失败'
    default: return '准备就绪'
  }
})

// Load templates
async function loadTemplates() {
  try {
    const response = await fetch(`${API_BASE}/api/emoji/templates/`)
    const data = await response.json()
    templates.value = data.templates
    categories.value = data.categories
  } catch (error) {
    console.error('Failed to load templates:', error)
  }
}

// Generate emoji
async function generateEmoji() {
  if (!canGenerate.value) return
  
  isLoading.value = true
  errorMessage.value = null
  resultVideoUrl.value = null
  progress.value = 0
  
  try {
    // Step 1: Detect face
    currentStep.value = 'detecting'
    progress.value = 10
    
    const detectResponse = await fetch(`${API_BASE}/api/emoji/detect-face/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ image_url: imageUrl.value })
    })
    const detectData = await detectResponse.json()
    
    if (!detectData.success) {
      throw new Error(detectData.error_message || '人脸检测失败')
    }
    
    detectionResult.value = detectData
    progress.value = 30
    
    // Step 2: Create video task
    currentStep.value = 'creating'
    
    const createResponse = await fetch(`${API_BASE}/api/emoji/create-task/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        image_url: imageUrl.value,
        face_bbox: detectData.bbox_face,
        ext_bbox: detectData.ext_bbox_face,
        driven_id: selectedTemplate.value
      })
    })
    const createData = await createResponse.json()
    
    if (!createData.success) {
      throw new Error(createData.error_message || '创建任务失败')
    }
    
    taskId.value = createData.task_id
    progress.value = 40
    
    // Step 3: Poll for completion
    currentStep.value = 'polling'
    startPolling()
    
  } catch (error) {
    console.error('Generation error:', error)
    currentStep.value = 'error'
    errorMessage.value = error.message
    isLoading.value = false
  }
}

// Polling
function startPolling() {
  pollTimer = setInterval(async () => {
    try {
      const response = await fetch(`${API_BASE}/api/emoji/task-status/${taskId.value}/`)
      const data = await response.json()
      
      // Update progress
      if (data.task_status === 'PENDING') {
        progress.value = Math.min(progress.value + 5, 60)
      } else if (data.task_status === 'RUNNING') {
        progress.value = Math.min(progress.value + 8, 90)
      }
      
      if (data.task_status === 'SUCCEEDED') {
        stopPolling()
        progress.value = 100
        currentStep.value = 'completed'
        resultVideoUrl.value = data.video_url
        isLoading.value = false
      } else if (data.task_status === 'FAILED' || data.task_status === 'CANCELED') {
        stopPolling()
        currentStep.value = 'error'
        errorMessage.value = data.error_message || '视频生成失败'
        isLoading.value = false
      }
    } catch (error) {
      console.error('Polling error:', error)
      stopPolling()
      currentStep.value = 'error'
      errorMessage.value = '查询任务状态失败'
      isLoading.value = false
    }
  }, POLL_INTERVAL)
}

function stopPolling() {
  if (pollTimer) {
    clearInterval(pollTimer)
    pollTimer = null
  }
}

// Reset
function resetGenerator() {
  stopPolling()
  currentStep.value = 'idle'
  progress.value = 0
  taskId.value = null
  resultVideoUrl.value = null
  errorMessage.value = null
  detectionResult.value = null
  isLoading.value = false
}

// Download video
async function downloadVideo() {
  if (!resultVideoUrl.value) return
  
  const filename = `emoji_${selectedTemplate.value}_${Date.now()}.mp4`
  
  try {
    // Try to fetch the video as a blob directly
    const response = await fetch(resultVideoUrl.value, {
      mode: 'cors',
      credentials: 'omit'
    })
    
    if (!response.ok) {
      throw new Error('Direct fetch failed, using proxy')
    }
    
    const blob = await response.blob()
    
    // Create download link
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = filename
    a.style.display = 'none'
    document.body.appendChild(a)
    a.click()
    
    // Cleanup
    setTimeout(() => {
      document.body.removeChild(a)
      URL.revokeObjectURL(url)
    }, 100)
    
  } catch (error) {
    console.warn('Direct download failed, using backend proxy:', error)
    
    // Fallback: Use backend proxy to download the video
    // This solves CORS issues and ensures proper .mp4 filename
    const proxyUrl = `${API_BASE}/api/emoji/download-video/?url=${encodeURIComponent(resultVideoUrl.value)}&filename=${encodeURIComponent(filename)}`
    
    const a = document.createElement('a')
    a.href = proxyUrl
    a.download = filename
    a.style.display = 'none'
    document.body.appendChild(a)
    a.click()
    
    setTimeout(() => {
      document.body.removeChild(a)
    }, 100)
  }
}

// Preview image URL
function onImageUrlChange() {
  if (imageUrl.value.match(/^https?:\/\/.+\.(jpg|jpeg|png|bmp|webp)/i)) {
    imagePreview.value = imageUrl.value
  } else {
    imagePreview.value = null
  }
}

// Trigger file input click
function triggerFileSelect() {
  if (fileInputRef.value) {
    fileInputRef.value.click()
  }
}

// Handle file selection
async function handleFileSelect(event) {
  const file = event.target.files?.[0]
  if (!file) return
  
  // Validate file type
  const validTypes = ['image/jpeg', 'image/png', 'image/webp', 'image/bmp']
  if (!validTypes.includes(file.type)) {
    errorMessage.value = '请选择有效的图片文件 (JPG, PNG, WebP, BMP)'
    return
  }
  
  // Validate file size (max 10MB)
  if (file.size > 10 * 1024 * 1024) {
    errorMessage.value = '文件太大，最大支持 10MB'
    return
  }
  
  // Show local preview immediately
  const localPreviewUrl = URL.createObjectURL(file)
  imagePreview.value = localPreviewUrl
  
  // Upload to server
  await uploadFile(file)
  
  // Clean up the local preview URL after upload
  URL.revokeObjectURL(localPreviewUrl)
}

// Upload file to server and get accessible URL
async function uploadFile(file) {
  isUploading.value = true
  errorMessage.value = null
  currentStep.value = 'uploading'
  
  try {
    const formData = new FormData()
    formData.append('file', file)
    
    const response = await fetch(`${API_BASE}/api/emoji/upload-image/`, {
      method: 'POST',
      body: formData,
    })
    
    const data = await response.json()
    
    if (data.success) {
      // Use image_url (oss://) for API calls, preview_url for display
      imageUrl.value = data.image_url
      imagePreview.value = data.preview_url || data.image_url
      console.log('Image uploaded:', data.image_url)
      console.log('Preview URL:', data.preview_url)
    } else {
      throw new Error(data.error || '上传失败')
    }
  } catch (error) {
    console.error('Upload error:', error)
    errorMessage.value = `上传失败: ${error.message}`
    imagePreview.value = null
  } finally {
    isUploading.value = false
    currentStep.value = 'idle'
  }
}

// Handle drag and drop
function handleDrop(event) {
  event.preventDefault()
  const file = event.dataTransfer?.files?.[0]
  if (file && file.type.startsWith('image/')) {
    // Create a fake event to reuse handleFileSelect logic
    handleFileSelect({ target: { files: [file] } })
  }
}

function handleDragOver(event) {
  event.preventDefault()
}

function getTemplateIcon(template) {
  const name = template.name;
  const desc = template.desc || '';
  
  // Mapping based on new templates
  if (name.includes('开心')) return '😄';
  if (name.includes('瞪眼') || desc.includes('我滴妈呀')) return '😳';
  if (name.includes('感动') || desc.includes('OK')) return '🥹';
  if (name.includes('认真') || desc.includes('想')) return '🤔';
  if (name.includes('激动') || desc.includes('god')) return '🤩';
  if (name.includes('困惑') || desc.includes('sir')) return '😵‍💫';
  if (name.includes('困')) return '😪';
  if (name.includes('狡黠') || name.includes('调皮')) return '😜';
  if (name.includes('抓狂')) return '😫';
  if (name.includes('无奈')) return '🤷';
  if (name.includes('微笑') || name.includes('呵呵')) return '🙂';
  if (name.includes('感激') || name.includes('拜托')) return '🙏';
  if (name.includes('仰望') || desc.includes('针不搓')) return '🙄';
  if (name.includes('得意') || desc.includes('夸我')) return '😎';
  if (name.includes('期待') || desc.includes('加油')) return '🥰';
  if (name.includes('懒惰') || desc.includes('下课')) return '😴';
  if (name.includes('嫌弃') || desc.includes('就这')) return '😒';
  if (name.includes('累')) return '😮‍💨';
  
  return '😐'; // Default
}

onMounted(() => {
  loadTemplates()
})
</script>

<template>
  <div class="h-full">
    <div class="grid grid-cols-1 lg:grid-cols-12 gap-6 h-full">
      
      <!-- Left Column: Inputs & Settings -->
      <section class="lg:col-span-5 flex flex-col gap-4 h-full overflow-hidden">
        
        <!-- Image Input Card -->
        <div class="ios-glass p-5 rounded-[28px] shrink-0 shadow-lg ring-1 ring-white/10">
          <div class="flex items-center justify-between mb-3">
            <h2 class="text-[14px] font-semibold text-white/90 flex items-center gap-2">
              <span class="p-1 rounded-md bg-orange-500/20 text-orange-400 text-xs">📷</span> 
              Source Portrait
            </h2>
            <div class="text-[11px] font-medium text-white/30 bg-white/5 py-1 px-2.5 rounded-full border border-white/5">
              JPG / PNG / WEBP
            </div>
          </div>
          
          <div class="flex flex-col gap-3">
             <!-- Drop Zone & Preview -->
             <div 
               class="relative w-full h-52 bg-black/40 rounded-xl overflow-hidden border-2 border-dashed border-white/10 group cursor-pointer transition-all duration-300 hover:border-ios-blue/30 hover:bg-black/50"
               @click="triggerFileSelect"
               @drop="handleDrop"
               @dragover="handleDragOver"
             >
                <transition name="fade" mode="out-in">
                  <img v-if="imagePreview" :src="imagePreview" class="w-full h-full object-cover transition-transform duration-700 group-hover:scale-105" alt="Source" />
                  
                  <div v-else class="w-full h-full flex flex-col items-center justify-center text-white/30 hover:text-white/50 transition-colors gap-2">
                    <svg class="w-10 h-10 stroke-1" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                      <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4" stroke-width="1.5" stroke-linecap="round"/>
                      <polyline points="17 8 12 3 7 8" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
                      <line x1="12" y1="3" x2="12" y2="15" stroke-width="1.5" stroke-linecap="round"/>
                    </svg>
                    <span class="text-xs">Drag & Drop or Click to Upload</span>
                  </div>
                </transition>
                
                <!-- Loading Overlay -->
                <div v-if="isUploading" class="absolute inset-0 bg-black/60 flex flex-col items-center justify-center z-10 backdrop-blur-sm">
                   <div class="w-6 h-6 border-2 border-ios-blue border-t-transparent rounded-full animate-spin mb-2"></div>
                   <span class="text-[10px] text-white/60 font-medium">UPLOADING...</span>
                </div>
             </div>

             <!-- URL Input (Compact) -->
             <div class="relative group">
               <input
                 v-model="imageUrl"
                 @input="onImageUrlChange"
                 type="url"
                 placeholder="Or paste image URL..."
                 :disabled="isLoading || isUploading"
                 class="w-full pl-8 pr-3 py-2.5 rounded-xl bg-white/5 border border-white/10 text-[12px] text-white placeholder-white/20 focus:outline-none focus:bg-white/10 focus:border-ios-blue/50 transition-all font-mono"
               />
               <span class="absolute left-2.5 top-1/2 -translate-y-1/2 text-white/20 text-xs">🔗</span>
             </div>
          </div>
            
          <!-- Hidden file input -->
          <input 
            ref="fileInputRef"
            type="file" 
            accept="image/jpeg,image/png,image/webp,image/bmp"
            @change="handleFileSelect"
            class="hidden"
          />
        </div>

        <!-- Template Selector -->
        <!-- Template Selector -->
        <div class="ios-glass p-6 rounded-[32px] flex-1 min-h-[400px] flex flex-col shadow-xl ring-1 ring-white/10">
          <div class="flex items-center justify-between mb-5">
            <h2 class="text-[15px] font-semibold text-white/90 flex items-center gap-2">
              <span class="p-1.5 rounded-lg bg-pink-500/20 text-pink-400">🎭</span>
              Choose Expression
            </h2>
            
            <!-- Category Tabs -->
            <div class="flex bg-black/20 p-1 rounded-xl">
              <button 
                v-for="cat in categoryList" 
                :key="cat"
                @click="activeCategory = cat"
                class="px-3 py-1.5 rounded-lg text-[11px] font-medium transition-all duration-200"
                :class="activeCategory === cat ? 'bg-white/10 text-white shadow-sm' : 'text-white/40 hover:text-white/60'"
              >
                {{ cat }}
              </button>
            </div>
          </div>
          
          <div class="flex-1 overflow-y-auto pr-1 custom-scrollbar">
            <div class="grid grid-cols-4 gap-2.5">
              <button
                v-for="template in currentCategoryTemplates"
                :key="template.id"
                @click="selectedTemplate = template.id"
                :disabled="isLoading"
                class="group relative aspect-[0.9] rounded-2xl border transition-all duration-200 flex flex-col items-center justify-center gap-1.5 overflow-hidden p-1.5"
                :class="selectedTemplate === template.id 
                  ? 'bg-ios-blue/20 border-ios-blue/50 ring-2 ring-ios-blue/20' 
                  : 'bg-white/5 border-white/5 hover:bg-white/10 hover:border-white/20'"
              >
                <div class="text-3xl transform group-hover:scale-110 transition-transform duration-300 filter drop-shadow-lg">
                  {{ getTemplateIcon(template) }}
                </div>
                
                <div class="flex flex-col items-center w-full gap-0.5">
                  <span class="text-[11px] font-bold text-center px-1 truncate w-full" 
                    :class="selectedTemplate === template.id ? 'text-white' : 'text-white/70'">
                    {{ template.name.split('·')[1] || template.name }}
                  </span>
                  <span v-if="template.desc" class="text-[9px] text-center px-1 truncate w-full scale-90"
                    :class="selectedTemplate === template.id ? 'text-blue-200/80' : 'text-white/30'">
                    {{ template.desc }}
                  </span>
                </div>
                
                <!-- Active Indicator -->
                <div v-if="selectedTemplate === template.id" class="absolute top-1.5 right-1.5 w-1.5 h-1.5 rounded-full bg-ios-blue shadow-[0_0_8px_rgba(10,132,255,0.8)]"></div>
              </button>
            </div>
            
            <!-- Empty state for category -->
            <div v-if="currentCategoryTemplates.length === 0" class="h-40 flex flex-col items-center justify-center text-white/20">
              <span class="text-2xl mb-2">📂</span>
              <span class="text-xs">该分类暂无模版</span>
            </div>
          </div>
        </div>
      </section>

      <!-- Right Column: Action & Result -->
      <section class="lg:col-span-7 flex flex-col h-full">
        <!-- Result/Status Card -->
        <div class="ios-glass flex-1 p-8 rounded-[32px] flex flex-col items-center justify-center relative overflow-hidden shadow-2xl ring-1 ring-white/10 group">
          
          <!-- Background Ambient Glow -->
          <div class="absolute inset-0 bg-gradient-to-br from-indigo-500/5 via-transparent to-pink-500/5 pointer-events-none"></div>

          <!-- STATE: IDLE or LOADING -->
          <div v-if="!resultVideoUrl" class="w-full max-w-sm flex flex-col items-center gap-10 relative z-10 transition-all duration-500">
            <!-- Progress Circle -->
            <div class="relative w-56 h-56 flex items-center justify-center">
              <!-- Track -->
              <svg class="absolute w-full h-full transform -rotate-90">
                <circle cx="112" cy="112" r="100" class="fill-none stroke-white/5" stroke-width="8" />
                <circle 
                  cx="112" cy="112" r="100" 
                  class="fill-none transition-all duration-1000 ease-out" 
                  :class="currentStep === 'error' ? 'stroke-red-500' : 'stroke-transparent'"
                  :stroke="currentStep !== 'error' ? 'url(#gradient)' : ''"
                  stroke-width="8" stroke-linecap="round"
                  :stroke-dasharray="628" 
                  :stroke-dashoffset="628 - (628 * progress / 100)" 
                />
                
                <defs>
                  <linearGradient id="gradient" x1="0%" y1="0%" x2="100%" y2="0%">
                    <stop offset="0%" stop-color="#8B5CF6" />
                    <stop offset="100%" stop-color="#EC4899" />
                  </linearGradient>
                </defs>
              </svg>
              
              <div class="text-center space-y-1">
                <div class="text-5xl font-bold tabular-nums tracking-tighter text-transparent bg-clip-text bg-gradient-to-br from-white to-white/50">
                  {{ progress }}<span class="text-2xl align-top">%</span>
                </div>
                <div class="text-[13px] font-medium text-white/40 uppercase tracking-widest animate-pulse">{{ statusText }}</div>
              </div>
            </div>

            <!-- Generate Button -->
            <button
              @click="currentStep === 'idle' || currentStep === 'error' ? generateEmoji() : null"
              :disabled="!canGenerate && currentStep === 'idle'"
              class="w-full py-4 rounded-2xl relative overflow-hidden group/btn transition-all duration-300"
              :class="canGenerate || currentStep !== 'idle'
                ? 'bg-white text-black shadow-lg shadow-white/10 hover:shadow-white/20 hover:scale-[1.02] active:scale-[0.98]' 
                : 'bg-white/10 text-white/20 cursor-not-allowed'"
            >
              <div class="absolute inset-0 bg-gradient-to-r from-transparent via-black/5 to-transparent -translate-x-full group-hover/btn:translate-x-full transition-transform duration-1000"></div>
              <span class="relative text-[16px] font-semibold flex items-center justify-center gap-2">
                 <span v-if="currentStep === 'idle'">✨ Generate Video</span>
                 <span v-else-if="currentStep === 'error'">🔄 Try Again</span>
                 <span v-else>Processing...</span>
              </span>
            </button>

            <!-- Error Message Toast -->
            <div v-if="errorMessage" class="bg-red-500/10 border border-red-500/20 text-red-200 px-4 py-3 rounded-xl text-[13px] text-center w-full animate-fade-in-up">
              {{ errorMessage }}
            </div>
          </div>

          <!-- STATE: COMPLETED -->
          <div v-else class="w-full h-full flex flex-col animate-fade-in">
             <div class="flex-1 relative rounded-2xl overflow-hidden bg-black/50 border border-white/10 shadow-2xl group/video">
                <video 
                  :src="resultVideoUrl" 
                  autoplay loop muted playsinline 
                  class="w-full h-full object-contain"
                ></video>
                
                <!-- Overlay Actions -->
                <div class="absolute inset-0 bg-black/60 opacity-0 group-hover/video:opacity-100 transition-opacity duration-300 flex items-center justify-center gap-4 backdrop-blur-sm">
                   <button @click="downloadVideo" class="p-4 rounded-full bg-white/10 hover:bg-white/20 backdrop-blur-md border border-white/20 text-white transition-transform hover:scale-110 active:scale-95">
                      <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"></path></svg>
                   </button>
                   <button @click="window.open(resultVideoUrl)" class="p-4 rounded-full bg-white/10 hover:bg-white/20 backdrop-blur-md border border-white/20 text-white transition-transform hover:scale-110 active:scale-95">
                      <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"></path></svg>
                   </button>
                </div>
             </div>

             <!-- Bottom Actions -->
             <div class="h-20 flex items-center justify-between px-2 mt-4">
                <div class="flex flex-col">
                   <span class="text-[14px] font-semibold text-white">Generation Success</span>
                   <span class="text-[12px] text-white/40">Expires in 24 hours</span>
                </div>
                <button 
                  @click="resetGenerator" 
                  class="px-6 py-2.5 rounded-full bg-white/5 hover:bg-white/10 border border-white/10 text-[13px] font-medium transition-colors"
                >
                  Create New
                </button>
             </div>
          </div>

        </div>
      </section>
      
    </div>
  </div>
</template>
