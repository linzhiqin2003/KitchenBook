<script setup>
import { ref, nextTick, onMounted } from 'vue'
import API_BASE_URL from '../config/api'

// 聊天状态
const isLoading = ref(false)
const inputMessage = ref('')
const messages = ref([])
const messagesContainer = ref(null)

// 图片上传状态
const selectedImage = ref(null)
const imagePreview = ref(null)
const isOcrProcessing = ref(false)
const ocrResult = ref(null)
const fileInputRef = ref(null)

// 语音录制状态
const isRecording = ref(false)
const isTranscribing = ref(false)
const recordingDuration = ref(0)
let mediaRecorder = null
let audioChunks = []
let recordingTimer = null

// 当前流式状态
const currentReasoning = ref('')
const currentContent = ref('')
const isReasoningPhase = ref(false)
const isContentPhase = ref(false)
const reasoningCollapsed = ref({}) // 按消息索引存储折叠状态

// 用于取消请求
let abortController = null
let currentReader = null
let currentAiMessageIndex = null

// 统计信息
const stats = ref({
  reasoningLength: 0,
  contentLength: 0,
  startTime: null,
  endTime: null
})

// HTML 转义
const escapeHtml = (text) => {
  const div = document.createElement('div')
  div.textContent = text
  return div.innerHTML
}

// Markdown 解析器（支持 LaTeX 数学公式）
const parseMarkdown = (markdown) => {
  if (!markdown) return ''
  
  let html = markdown
  
  // 先保存 LaTeX 数学公式块，防止被其他规则处理
  const mathBlocks = []
  // 块级公式 \[ ... \] 或 $$ ... $$
  html = html.replace(/\\\[([\s\S]*?)\\\]/g, (match, formula) => {
    const placeholder = `__MATH_BLOCK_${mathBlocks.length}__`
    mathBlocks.push({ type: 'block', formula: formula.trim() })
    return placeholder
  })
  html = html.replace(/\$\$([\s\S]*?)\$\$/g, (match, formula) => {
    const placeholder = `__MATH_BLOCK_${mathBlocks.length}__`
    mathBlocks.push({ type: 'block', formula: formula.trim() })
    return placeholder
  })
  // 行内公式 \( ... \) 或 $ ... $
  html = html.replace(/\\\(([\s\S]*?)\\\)/g, (match, formula) => {
    const placeholder = `__MATH_INLINE_${mathBlocks.length}__`
    mathBlocks.push({ type: 'inline', formula: formula.trim() })
    return placeholder
  })
  html = html.replace(/\$([^\$\n]+?)\$/g, (match, formula) => {
    const placeholder = `__MATH_INLINE_${mathBlocks.length}__`
    mathBlocks.push({ type: 'inline', formula: formula.trim() })
    return placeholder
  })
  
  // 先保存代码块，防止被其他规则处理
  const codeBlocks = []
  html = html.replace(/```(\w+)?\n?([\s\S]*?)```/g, (match, lang, code) => {
    const placeholder = `__CODE_BLOCK_${codeBlocks.length}__`
    codeBlocks.push({
      lang: lang || 'text',
      code: code.trim()
    })
    return placeholder
  })
  
  // 行内代码 - 也先保存
  const inlineCodes = []
  html = html.replace(/`([^`]+)`/g, (match, code) => {
    const placeholder = `__INLINE_CODE_${inlineCodes.length}__`
    inlineCodes.push(code)
    return placeholder
  })
  
  // 标题
  html = html.replace(/^#### (.+)$/gm, '<h4 class="md-h4">$1</h4>')
  html = html.replace(/^### (.+)$/gm, '<h3 class="md-h3">$1</h3>')
  html = html.replace(/^## (.+)$/gm, '<h2 class="md-h2">$1</h2>')
  html = html.replace(/^# (.+)$/gm, '<h1 class="md-h1">$1</h1>')
  
  // 粗体和斜体
  html = html.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
  html = html.replace(/\*(.+?)\*/g, '<em>$1</em>')
  
  // 链接
  html = html.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" class="md-link" target="_blank" rel="noopener">$1</a>')
  
  // 无序列表
  html = html.replace(/^\s*[-*]\s+(.+)$/gm, '<li class="md-li">$1</li>')
  html = html.replace(/(<li class="md-li">.*<\/li>\n?)+/g, '<ul class="md-ul">$&</ul>')
  
  // 有序列表
  html = html.replace(/^\s*\d+\.\s+(.+)$/gm, '<li class="md-oli">$1</li>')
  html = html.replace(/(<li class="md-oli">.*<\/li>\n?)+/g, '<ol class="md-ol">$&</ol>')
  
  // 引用块
  html = html.replace(/^>\s*(.+)$/gm, '<blockquote class="md-quote">$1</blockquote>')
  
  // 水平线
  html = html.replace(/^---$/gm, '<hr class="md-hr" />')
  
  // 段落 (连续的非空行)
  html = html.split('\n\n').map(block => {
    if (block.match(/^<(h[1-6]|ul|ol|pre|blockquote|hr)/) || 
        block.includes('__CODE_BLOCK_') || 
        block.includes('__MATH_BLOCK_')) {
      return block
    }
    if (block.trim() && !block.match(/^<[a-z]/i)) {
      return `<p class="md-p">${block.replace(/\n/g, '<br>')}</p>`
    }
    return block
  }).join('\n')
  
  // 恢复代码块
  codeBlocks.forEach((block, i) => {
    const escapedCode = escapeHtml(block.code)
    html = html.replace(
      `__CODE_BLOCK_${i}__`,
      `<pre class="code-block" data-lang="${block.lang}"><code>${escapedCode}</code></pre>`
    )
  })
  
  // 恢复行内代码
  inlineCodes.forEach((code, i) => {
    html = html.replace(
      `__INLINE_CODE_${i}__`,
      `<code class="inline-code">${escapeHtml(code)}</code>`
    )
  })
  
  // 恢复数学公式
  mathBlocks.forEach((block, i) => {
    if (block.type === 'block') {
      html = html.replace(
        `__MATH_BLOCK_${i}__`,
        `<div class="math-block">\\[${escapeHtml(block.formula)}\\]</div>`
      )
    } else {
      html = html.replace(
        `__MATH_INLINE_${i}__`,
        `<span class="math-inline">\\(${escapeHtml(block.formula)}\\)</span>`
      )
    }
  })
  
  return html
}

// 渲染数学公式
const renderMath = async () => {
  await nextTick()
  if (window.MathJax) {
    window.MathJax.typesetPromise?.()
  }
}

// 初始欢迎消息
const welcomeMessage = {
  role: 'assistant',
  content: '你好！我是 **DeepSeek Reasoner** 🧠\n\n我是一个强大的思考模型，擅长复杂推理和深度分析。你可以问我：\n\n- 数学推理和证明\n- 代码分析和算法设计\n- 逻辑推理和问题解决\n- 深度分析和创意写作\n\n我的思考过程会完整展示给你，让你看到 AI 是如何一步步推理的。',
  reasoning: null,
  type: 'text'
}

onMounted(() => {
  // 加载 MathJax
  if (!window.MathJax) {
    window.MathJax = {
      tex: {
        inlineMath: [['\\(', '\\)']],
        displayMath: [['\\[', '\\]']],
      },
      svg: {
        fontCache: 'global'
      },
      startup: {
        ready: () => {
          window.MathJax.startup.defaultReady()
        }
      }
    }
    const script = document.createElement('script')
    script.src = 'https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-svg.js'
    script.async = true
    document.head.appendChild(script)
  }
  
  const saved = localStorage.getItem('ai_lab_messages')
  if (saved) {
    try {
      messages.value = JSON.parse(saved)
    } catch (e) {
      messages.value = [welcomeMessage]
    }
  } else {
    messages.value = [welcomeMessage]
  }
  
  // 初始渲染数学公式
  setTimeout(renderMath, 500)
})

const saveMessages = () => {
  const toSave = messages.value.slice(-20) // 保存最近20条
  localStorage.setItem('ai_lab_messages', JSON.stringify(toSave))
}

const scrollToBottom = async () => {
  await nextTick()
  if (messagesContainer.value) {
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
  }
}

// 切换思维链折叠状态
const toggleReasoning = (index) => {
  reasoningCollapsed.value[index] = !reasoningCollapsed.value[index]
}

// 停止生成
const stopGeneration = async () => {
  if (abortController) {
    abortController.abort()
  }
  if (currentReader) {
    try {
      await currentReader.cancel()
    } catch (e) {
      // 忽略取消错误
    }
  }
  
  // 标记当前消息为已停止
  if (currentAiMessageIndex !== null && messages.value[currentAiMessageIndex]) {
    const msg = messages.value[currentAiMessageIndex]
    msg.isStreaming = false
    msg.stopped = true
    // 如果有内容，添加停止标记
    if (msg.content) {
      msg.content += '\n\n*[已停止生成]*'
    } else if (msg.reasoning) {
      msg.content = '*[已停止生成]*'
    }
    // 更新统计
    msg.stats = {
      ...stats.value,
      endTime: Date.now(),
      reasoningLength: currentReasoning.value.length,
      contentLength: currentContent.value.length
    }
    saveMessages()
  }
  
  // 重置状态
  isLoading.value = false
  isReasoningPhase.value = false
  isContentPhase.value = false
  abortController = null
  currentReader = null
  currentAiMessageIndex = null
}

// 发送消息
const sendMessage = async () => {
  const text = inputMessage.value.trim()
  if (!text || isLoading.value) return
  
  messages.value.push({ role: 'user', content: text, type: 'text' })
  inputMessage.value = ''
  isLoading.value = true
  currentReasoning.value = ''
  currentContent.value = ''
  isReasoningPhase.value = false
  isContentPhase.value = false
  stats.value = { reasoningLength: 0, contentLength: 0, startTime: Date.now(), endTime: null }
  scrollToBottom()
  
  // 构建 API 消息（不包含 reasoning 和停止标记）
  const apiMessages = messages.value
    .filter(m => m.type === 'text' && (m.role === 'user' || m.role === 'assistant'))
    .map(m => ({ 
      role: m.role, 
      // 移除停止标记
      content: m.content?.replace(/\n\n\*\[已停止生成\]\*$/, '') || ''
    }))
    .filter(m => m.content) // 过滤掉空内容
  
  // 添加一个空的 AI 消息用于流式填充
  const aiMessageIndex = messages.value.length
  currentAiMessageIndex = aiMessageIndex
  messages.value.push({
    role: 'assistant',
    content: '',
    reasoning: '',
    type: 'text',
    isStreaming: true
  })
  
  // 创建 AbortController
  abortController = new AbortController()
  
  try {
    const response = await fetch(`${API_BASE_URL}/api/ai/speciale/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ messages: apiMessages }),
      signal: abortController.signal
    })
    
    if (!response.ok) {
      const error = await response.json()
      throw new Error(error.error || '请求失败')
    }
    
    const reader = response.body.getReader()
    currentReader = reader // 保存引用以便取消
    const decoder = new TextDecoder()
    let buffer = '' // 用于存储跨 chunk 的不完整数据
    
    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      
      // 检查是否已被取消
      if (!isLoading.value) break
      
      // 将新数据追加到 buffer
      buffer += decoder.decode(value, { stream: true })
      
      // 按行分割，处理完整的行
      const lines = buffer.split('\n')
      // 最后一行可能不完整，保留到下次处理
      buffer = lines.pop() || ''
      
      for (const line of lines) {
        // 跳过心跳和空行
        if (!line || line.startsWith(':')) continue
        
        if (line.startsWith('data: ')) {
          const data = line.slice(6).trim()
          if (data === '[DONE]') break
          if (!data) continue
          
          try {
            const parsed = JSON.parse(data)
            
            switch (parsed.type) {
              case 'status':
                // 状态更新
                break
                
              case 'reasoning_start':
                isReasoningPhase.value = true
                break
                
              case 'reasoning':
                currentReasoning.value += parsed.content
                messages.value[aiMessageIndex].reasoning = currentReasoning.value
                scrollToBottom()
                break
                
              case 'reasoning_end':
                isReasoningPhase.value = false
                break
                
              case 'content_start':
                isContentPhase.value = true
                break
                
              case 'content':
                currentContent.value += parsed.content
                messages.value[aiMessageIndex].content = currentContent.value
                scrollToBottom()
                renderMath()
                break
                
              case 'done':
                stats.value.reasoningLength = parsed.reasoning_length
                stats.value.contentLength = parsed.content_length
                stats.value.endTime = Date.now()
                break
                
              case 'error':
                throw new Error(parsed.error)
            }
          } catch (e) {
            if (!(e instanceof SyntaxError)) {
              throw e
            }
            // JSON 不完整，跳过这行
          }
        }
      }
    }
    
    messages.value[aiMessageIndex].isStreaming = false
    messages.value[aiMessageIndex].stats = { ...stats.value }
    saveMessages()
    renderMath()
    
  } catch (error) {
    // 如果是用户取消，不显示错误
    if (error.name === 'AbortError') {
      // 已在 stopGeneration 中处理
      return
    }
    messages.value[aiMessageIndex].content = `抱歉，我遇到了一点问题 😅\n\n${error.message}\n\n请稍后再试~`
    messages.value[aiMessageIndex].reasoning = ''
    messages.value[aiMessageIndex].isStreaming = false
  } finally {
    isLoading.value = false
    isReasoningPhase.value = false
    isContentPhase.value = false
    abortController = null
    currentReader = null
    currentAiMessageIndex = null
    scrollToBottom()
  }
}

const clearChat = () => {
  messages.value = [welcomeMessage]
  localStorage.removeItem('ai_lab_messages')
  reasoningCollapsed.value = {}
}

const handleKeydown = (e) => {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault()
    sendMessage()
  }
}

// 示例问题
const exampleQuestions = [
  { text: '证明根号2是无理数', icon: '📐' },
  { text: '用动态规划解决背包问题', icon: '💻' },
  { text: '分析量子纠缠的本质', icon: '⚛️' },
  { text: '写一首关于AI的诗', icon: '✨' }
]

const askExample = (text) => {
  inputMessage.value = text
  sendMessage()
}

// ===== 图片上传和 OCR 功能 =====

const triggerFileInput = () => {
  fileInputRef.value?.click()
}

const handleFileSelect = (event) => {
  const file = event.target.files?.[0]
  if (!file) return
  
  // 验证文件类型
  if (!file.type.startsWith('image/')) {
    alert('请选择图片文件')
    return
  }
  
  // 验证文件大小 (最大 10MB)
  if (file.size > 10 * 1024 * 1024) {
    alert('图片大小不能超过 10MB')
    return
  }
  
  selectedImage.value = file
  
  // 生成预览
  const reader = new FileReader()
  reader.onload = (e) => {
    imagePreview.value = e.target.result
  }
  reader.readAsDataURL(file)
  
  // 清空 OCR 结果
  ocrResult.value = null
}

const removeImage = () => {
  selectedImage.value = null
  imagePreview.value = null
  ocrResult.value = null
  if (fileInputRef.value) {
    fileInputRef.value.value = ''
  }
}

const processOCR = async () => {
  if (!selectedImage.value || isOcrProcessing.value) return
  
  isOcrProcessing.value = true
  ocrResult.value = null
  
  try {
    const formData = new FormData()
    formData.append('image', selectedImage.value)
    
    const response = await fetch(`${API_BASE_URL}/api/ai/ocr/`, {
      method: 'POST',
      body: formData
    })
    
    const data = await response.json()
    
    if (!response.ok) {
      throw new Error(data.error || 'OCR 识别失败')
    }
    
    ocrResult.value = data.markdown
    // 自动填充到输入框
    inputMessage.value = `请解答以下题目：\n\n${data.markdown}`
    
  } catch (error) {
    alert(`OCR 识别失败: ${error.message}`)
  } finally {
    isOcrProcessing.value = false
  }
}

// 发送带图片的消息
const sendWithImage = async () => {
  if (!ocrResult.value && !inputMessage.value.trim()) return
  
  // 如果有图片但还没 OCR，先进行 OCR
  if (selectedImage.value && !ocrResult.value) {
    await processOCR()
    if (!ocrResult.value) return // OCR 失败
  }
  
  // 发送消息
  await sendMessage()
  
  // 清除图片状态
  removeImage()
}

// 处理粘贴图片
const handlePaste = (event) => {
  const items = event.clipboardData?.items
  if (!items) return
  
  for (const item of items) {
    if (item.type.startsWith('image/')) {
      event.preventDefault()
      const file = item.getAsFile()
      if (file) {
        selectedImage.value = file
        const reader = new FileReader()
        reader.onload = (e) => {
          imagePreview.value = e.target.result
        }
        reader.readAsDataURL(file)
        ocrResult.value = null
      }
      break
    }
  }
}

// ===== 语音录制功能 =====

// 格式化录音时长
const formatDuration = (seconds) => {
  const mins = Math.floor(seconds / 60)
  const secs = seconds % 60
  return `${mins}:${secs.toString().padStart(2, '0')}`
}

// 开始/停止录音
const toggleRecording = async () => {
  if (isRecording.value) {
    stopRecording()
  } else {
    await startRecording()
  }
}

// 开始录音
const startRecording = async () => {
  try {
    // 检查浏览器是否支持 MediaDevices API
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
      // 检查是否是因为非 HTTPS
      if (location.protocol === 'http:' && location.hostname !== 'localhost' && location.hostname !== '127.0.0.1') {
        alert('语音输入需要 HTTPS 安全连接。请使用 HTTPS 访问本站，或在本地开发环境中使用。')
      } else {
        alert('您的浏览器不支持语音录制功能，请使用最新版本的 Chrome、Firefox 或 Safari。')
      }
      return
    }
    
    const stream = await navigator.mediaDevices.getUserMedia({ 
      audio: {
        channelCount: 1,
        sampleRate: 16000
      }
    })
    
    // 使用 webm 格式（浏览器兼容性最好）
    const mimeType = MediaRecorder.isTypeSupported('audio/webm;codecs=opus') 
      ? 'audio/webm;codecs=opus' 
      : 'audio/webm'
    
    mediaRecorder = new MediaRecorder(stream, { mimeType })
    audioChunks = []
    recordingDuration.value = 0
    
    mediaRecorder.ondataavailable = (event) => {
      if (event.data.size > 0) {
        audioChunks.push(event.data)
      }
    }
    
    mediaRecorder.onstop = async () => {
      // 停止所有音轨
      stream.getTracks().forEach(track => track.stop())
      
      // 创建音频 Blob
      const audioBlob = new Blob(audioChunks, { type: mimeType })
      
      // 保存录音时长（在清零前）
      const duration = recordingDuration.value
      
      // 发送到后端转录（传递录音时长）
      await transcribeAudio(audioBlob, duration)
    }
    
    // 每秒更新录音时长
    recordingTimer = setInterval(() => {
      recordingDuration.value++
      // 最长录音 60 秒
      if (recordingDuration.value >= 60) {
        stopRecording()
      }
    }, 1000)
    
    mediaRecorder.start(1000) // 每秒收集一次数据
    isRecording.value = true
    
  } catch (error) {
    console.error('录音失败:', error)
    if (error.name === 'NotAllowedError') {
      alert('请允许麦克风访问权限')
    } else if (error.name === 'NotFoundError') {
      alert('未找到麦克风设备')
    } else {
      alert('录音初始化失败: ' + error.message)
    }
  }
}

// 停止录音
const stopRecording = () => {
  if (mediaRecorder && mediaRecorder.state !== 'inactive') {
    mediaRecorder.stop()
  }
  if (recordingTimer) {
    clearInterval(recordingTimer)
    recordingTimer = null
  }
  isRecording.value = false
}

// 发送音频到后端转录
const transcribeAudio = async (audioBlob, duration = 0) => {
  isTranscribing.value = true
  
  try {
    const formData = new FormData()
    formData.append('audio', audioBlob, 'recording.webm')
    formData.append('duration', duration.toString())
    
    const response = await fetch(`${API_BASE_URL}/api/ai/transcribe/`, {
      method: 'POST',
      body: formData
    })
    
    const data = await response.json()
    
    if (!response.ok) {
      throw new Error(data.error || '转录失败')
    }
    
    // 将转录文本填充到输入框
    if (data.text) {
      inputMessage.value = (inputMessage.value ? inputMessage.value + ' ' : '') + data.text
    }
    
  } catch (error) {
    console.error('转录失败:', error)
    alert('语音转录失败: ' + error.message)
  } finally {
    isTranscribing.value = false
    recordingDuration.value = 0
  }
}
</script>

<template>
  <div class="h-dvh w-full fixed inset-0 bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 text-white flex flex-col overflow-hidden">
    <!-- 动态背景 -->
    <div class="fixed inset-0 pointer-events-none overflow-hidden">
      <div class="absolute top-[-20%] left-[-10%] w-[500px] h-[500px] bg-indigo-500/10 rounded-full blur-[120px] animate-pulse-slow"></div>
      <div class="absolute bottom-[-20%] right-[-10%] w-[400px] h-[400px] bg-purple-500/10 rounded-full blur-[100px] animate-pulse-slow animation-delay-2000"></div>
      <div class="absolute inset-0 bg-[linear-gradient(rgba(255,255,255,0.01)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,0.01)_1px,transparent_1px)] bg-[size:40px_40px]"></div>
    </div>

    <!-- 顶部导航栏 - 毛玻璃效果 -->
    <header class="shrink-0 relative z-10 h-14 sm:h-16 bg-white/5 backdrop-blur-xl border-b border-white/10 flex items-center px-4 sm:px-6 gap-3 sm:gap-4 safe-area-top">
      <router-link 
        to="/" 
        class="group w-9 h-9 sm:w-10 sm:h-10 rounded-xl bg-white/10 hover:bg-white/20 backdrop-blur-sm flex items-center justify-center transition-all duration-300 border border-white/10 hover:border-white/20 hover:scale-105"
        title="返回主页"
      >
        <svg class="w-5 h-5 text-white/70 group-hover:text-white transition-colors" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 19l-7-7m0 0l7-7m-7 7h18"/>
        </svg>
      </router-link>
      
      <div class="flex items-center gap-3 flex-1 min-w-0">
        <div class="relative">
          <div class="w-10 h-10 sm:w-11 sm:h-11 rounded-xl bg-gradient-to-br from-indigo-500 via-purple-500 to-pink-500 flex items-center justify-center shadow-lg shadow-purple-500/25">
            <span class="text-xl sm:text-2xl">🧠</span>
          </div>
          <!-- 在线状态指示器 -->
          <div class="absolute -bottom-0.5 -right-0.5 w-3 h-3 rounded-full bg-emerald-500 border-2 border-slate-900"></div>
        </div>
        <div class="min-w-0">
          <h1 class="text-base sm:text-lg font-bold text-white leading-tight truncate">DeepSeek Reasoner</h1>
          <p class="text-xs text-white/40 hidden xs:block">思考模型 · 可见推理链</p>
        </div>
      </div>
      
      <button 
        @click="clearChat" 
        class="h-9 sm:h-10 px-3 sm:px-4 text-xs font-medium text-white/70 hover:text-white bg-white/10 hover:bg-white/20 backdrop-blur-sm rounded-xl transition-all duration-300 flex items-center gap-2 cursor-pointer border border-white/10 hover:border-white/20 hover:scale-105"
      >
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/>
        </svg>
        <span class="hidden sm:inline">清空对话</span>
      </button>
    </header>
    
    <!-- 消息区域 -->
    <div 
      ref="messagesContainer" 
      class="flex-1 relative z-10 overflow-y-auto px-4 py-6"
    >
      <div class="max-w-3xl mx-auto space-y-6">
        <TransitionGroup name="message">
          <template v-for="(msg, index) in messages" :key="index">
            <!-- 用户消息 -->
            <div v-if="msg.role === 'user'" class="flex justify-end w-full">
              <div class="max-w-[85%] md:max-w-[75%] min-w-[100px]">
                <div class="bg-gradient-to-br from-indigo-500 to-purple-600 text-white rounded-2xl rounded-br-md px-4 py-3 shadow-lg shadow-indigo-500/20">
                  <div class="whitespace-pre-wrap text-sm leading-relaxed break-words">{{ msg.content }}</div>
                </div>
              </div>
            </div>
            
            <!-- AI 消息 -->
            <div v-else-if="msg.role === 'assistant'" class="flex justify-start w-full">
              <div class="max-w-[95%] md:max-w-[85%] min-w-[200px] space-y-3">
                <!-- 思维链展示 -->
                <div v-if="msg.reasoning" class="rounded-2xl overflow-hidden border border-amber-500/30 bg-amber-500/5 backdrop-blur-sm">
                  <button 
                    @click="toggleReasoning(index)"
                    class="w-full text-left cursor-pointer flex items-center gap-3 px-4 py-3 hover:bg-amber-500/10 transition-colors"
                  >
                    <div class="w-8 h-8 rounded-xl bg-gradient-to-br from-amber-400 to-orange-500 flex items-center justify-center shrink-0 shadow-lg shadow-amber-500/20">
                      <span class="text-sm">💭</span>
                    </div>
                    <span class="text-sm font-semibold text-amber-300">思维链</span>
                    <span class="text-xs text-amber-400/70 ml-auto flex items-center gap-2">
                      <span v-if="msg.isStreaming && isReasoningPhase" class="flex items-center gap-1.5 text-amber-300">
                        <svg class="w-3.5 h-3.5 animate-spin" fill="none" viewBox="0 0 24 24">
                          <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                          <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                        </svg>
                        思考中...
                      </span>
                      <span v-else>{{ msg.reasoning.length }} 字</span>
                      <svg 
                        class="w-4 h-4 transition-transform duration-300 text-amber-400" 
                        :class="{ 'rotate-180': !reasoningCollapsed[index] }"
                        fill="none" stroke="currentColor" viewBox="0 0 24 24"
                      >
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"/>
                      </svg>
                    </span>
                  </button>
                  <Transition name="collapse">
                    <div 
                      v-if="!reasoningCollapsed[index]"
                      class="px-4 py-3 max-h-64 overflow-y-auto custom-scrollbar border-t border-amber-500/20"
                    >
                      <div class="text-amber-100/70 leading-relaxed whitespace-pre-wrap font-mono text-xs">{{ msg.reasoning }}</div>
                    </div>
                  </Transition>
                </div>
                
                <!-- 主要内容 -->
                <div 
                  v-if="msg.content || (!isReasoningPhase && msg.isStreaming && !msg.reasoning)"
                  class="bg-white/5 backdrop-blur-sm rounded-2xl rounded-bl-md px-5 py-4 border border-white/10 shadow-xl"
                >
                  <div 
                    v-if="msg.content" 
                    class="markdown-content text-sm leading-relaxed"
                    v-html="parseMarkdown(msg.content)"
                  ></div>
                  
                  <!-- 加载中状态 -->
                  <div v-else-if="msg.isStreaming && !msg.reasoning" class="flex items-center gap-3 text-white/50 py-1">
                    <div class="flex items-center gap-1.5">
                      <span class="w-2 h-2 bg-indigo-400 rounded-full animate-bounce" style="animation-delay: 0ms"></span>
                      <span class="w-2 h-2 bg-purple-400 rounded-full animate-bounce" style="animation-delay: 150ms"></span>
                      <span class="w-2 h-2 bg-pink-400 rounded-full animate-bounce" style="animation-delay: 300ms"></span>
                    </div>
                    <span class="text-xs">正在连接...</span>
                  </div>
                </div>
                
                <!-- 统计信息 -->
                <div v-if="msg.stats && msg.stats.endTime" class="flex items-center gap-4 px-1 text-xs text-white/30">
                  <span class="flex items-center gap-1.5">
                    <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"/>
                    </svg>
                    {{ ((msg.stats.endTime - msg.stats.startTime) / 1000).toFixed(1) }}s
                  </span>
                  <span>💭 思考 {{ msg.stats.reasoningLength }} 字</span>
                  <span>📝 回答 {{ msg.stats.contentLength }} 字</span>
                </div>
              </div>
            </div>
          </template>
        </TransitionGroup>
        
        <!-- 空状态提示 -->
        <div v-if="messages.length <= 1" class="text-center py-12">
          <div class="text-white/30 mb-8 text-sm">试试这些问题：</div>
          <div class="flex flex-wrap justify-center gap-3">
            <button
              v-for="q in exampleQuestions"
              :key="q.text"
              @click="askExample(q.text)"
              :disabled="isLoading"
              class="group px-4 py-3 bg-white/5 hover:bg-white/10 border border-white/10 hover:border-white/20 rounded-2xl text-sm text-white/70 hover:text-white transition-all duration-300 disabled:opacity-50 cursor-pointer flex items-center gap-2.5 backdrop-blur-sm hover:scale-105"
            >
              <span class="text-lg group-hover:scale-110 transition-transform">{{ q.icon }}</span>
              <span>{{ q.text }}</span>
            </button>
          </div>
        </div>
      </div>
    </div>
    
    <!-- 输入区域 - 底部毛玻璃 -->
    <div class="shrink-0 relative z-10 bg-white/5 backdrop-blur-xl border-t border-white/10 px-3 sm:px-4 py-3 safe-area-bottom">
      <div class="max-w-3xl mx-auto">
        <!-- 图片预览区域 -->
        <Transition name="fade">
          <div v-if="imagePreview" class="mb-3 p-3 bg-white/5 rounded-2xl border border-white/10">
            <div class="flex items-start gap-3">
              <div class="relative shrink-0">
                <img 
                  :src="imagePreview" 
                  alt="预览" 
                  class="w-20 h-20 object-cover rounded-xl border border-white/20"
                />
                <button
                  @click="removeImage"
                  class="absolute -top-2 -right-2 w-6 h-6 bg-red-500 hover:bg-red-400 text-white rounded-full flex items-center justify-center shadow-lg cursor-pointer transition-colors"
                >
                  <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
                  </svg>
                </button>
              </div>
              <div class="flex-1 min-w-0">
                <div class="text-sm text-white/60 mb-2 truncate">{{ selectedImage?.name }}</div>
                <div v-if="ocrResult" class="text-xs text-emerald-400 flex items-center gap-1.5 mb-2">
                  <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/>
                  </svg>
                  已识别，内容已填充
                </div>
                <button
                  v-if="!ocrResult"
                  @click="processOCR"
                  :disabled="isOcrProcessing"
                  class="px-3 py-1.5 text-xs bg-indigo-500 hover:bg-indigo-400 text-white rounded-lg disabled:bg-white/10 disabled:text-white/30 transition-colors cursor-pointer flex items-center gap-1.5"
                >
                  <svg v-if="isOcrProcessing" class="w-3.5 h-3.5 animate-spin" fill="none" viewBox="0 0 24 24">
                    <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                    <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  <svg v-else class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/>
                  </svg>
                  {{ isOcrProcessing ? '识别中...' : '识别图片' }}
                </button>
              </div>
            </div>
          </div>
        </Transition>
        
        <!-- 隐藏的文件输入 -->
        <input
          ref="fileInputRef"
          type="file"
          accept="image/*"
          class="hidden"
          @change="handleFileSelect"
        />
        
        <!-- 输入框容器 -->
        <div class="bg-white/10 backdrop-blur-sm rounded-2xl border border-white/10 focus-within:border-indigo-500/50 focus-within:ring-2 focus-within:ring-indigo-500/20 transition-all">
          <div class="flex items-center gap-2 p-2 sm:p-2.5">
            <!-- 上传图片按钮 -->
            <button
              @click="triggerFileInput"
              :disabled="isLoading || isOcrProcessing || isRecording"
              class="w-9 h-9 sm:w-10 sm:h-10 bg-white/10 hover:bg-white/20 text-white/50 hover:text-white rounded-xl disabled:opacity-30 disabled:cursor-not-allowed transition-all shrink-0 cursor-pointer flex items-center justify-center"
              title="上传图片"
            >
              <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"/>
              </svg>
            </button>
            
            <!-- 语音输入按钮 -->
            <button
              @click="toggleRecording"
              :disabled="isLoading || isOcrProcessing || isTranscribing"
              :class="[
                'w-9 h-9 sm:w-10 sm:h-10 rounded-xl transition-all shrink-0 cursor-pointer flex items-center justify-center',
                isRecording 
                  ? 'bg-red-500 hover:bg-red-400 text-white animate-pulse' 
                  : 'bg-white/10 hover:bg-white/20 text-white/50 hover:text-white',
                (isLoading || isOcrProcessing || isTranscribing) && 'opacity-30 cursor-not-allowed'
              ]"
              :title="isRecording ? '停止录音' : '语音输入'"
            >
              <svg v-if="isTranscribing" class="w-5 h-5 animate-spin" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"></path>
              </svg>
              <svg v-else-if="isRecording" class="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                <rect x="6" y="6" width="12" height="12" rx="2"/>
              </svg>
              <svg v-else class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z"/>
              </svg>
            </button>
            
            <!-- 录音时长显示 -->
            <span v-if="isRecording" class="text-xs text-red-400 font-mono min-w-[40px]">
              {{ formatDuration(recordingDuration) }}
            </span>
            
            <textarea
              v-model="inputMessage"
              @keydown="handleKeydown"
              @paste="handlePaste"
              :disabled="isLoading || isRecording"
              :placeholder="isRecording ? '录音中...' : '输入你的问题...'"
              rows="1"
              class="flex-1 resize-none bg-transparent border-0 text-sm text-white placeholder-white/30 focus:outline-none focus:ring-0 max-h-32 min-h-[28px] py-2"
              style="field-sizing: content;"
            ></textarea>
            
            <!-- 发送按钮 / 停止按钮 -->
            <button
              v-if="!isLoading"
              @click="selectedImage ? sendWithImage() : sendMessage()"
              :disabled="(!inputMessage.trim() && !ocrResult) || isOcrProcessing || isRecording || isTranscribing"
              class="w-9 h-9 sm:w-10 sm:h-10 bg-gradient-to-r from-indigo-500 to-purple-500 hover:from-indigo-400 hover:to-purple-400 text-white rounded-xl disabled:from-white/10 disabled:to-white/10 disabled:text-white/30 disabled:cursor-not-allowed transition-all shrink-0 cursor-pointer flex items-center justify-center shadow-lg shadow-indigo-500/25 hover:shadow-indigo-500/40 hover:scale-105"
            >
              <svg v-if="!isOcrProcessing && !isTranscribing" class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8"/>
              </svg>
              <svg v-else class="w-5 h-5 animate-spin" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"></path>
              </svg>
            </button>
            
            <!-- 停止生成按钮 -->
            <button
              v-else
              @click="stopGeneration"
              class="w-9 h-9 sm:w-10 sm:h-10 bg-gradient-to-r from-red-500 to-pink-500 hover:from-red-400 hover:to-pink-400 text-white rounded-xl transition-all shrink-0 cursor-pointer flex items-center justify-center shadow-lg shadow-red-500/25 hover:scale-105"
              title="停止生成"
            >
              <svg class="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                <rect x="6" y="6" width="12" height="12" rx="2"/>
              </svg>
            </button>
          </div>
        </div>
        
        <!-- 底部提示 -->
        <div class="text-center mt-2 text-[10px] sm:text-xs text-white/20">
          DeepSeek Reasoner · 图片OCR · 语音输入
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
/* 动态视口高度兼容 */
.h-dvh {
  height: 100vh;
  height: 100dvh;
}

/* 安全区域适配 (iPhone 等刘海屏设备) */
.safe-area-top {
  padding-top: env(safe-area-inset-top);
}
.safe-area-bottom {
  padding-bottom: env(safe-area-inset-bottom);
}

/* 消息动画 */
.message-enter-active { animation: message-in 0.3s ease-out; }
@keyframes message-in {
  0% { opacity: 0; transform: translateY(10px); }
  100% { opacity: 1; transform: translateY(0); }
}

/* 动态背景动画 */
@keyframes pulse-slow {
  0%, 100% { 
    opacity: 0.1; 
    transform: scale(1); 
  }
  50% { 
    opacity: 0.15; 
    transform: scale(1.05); 
  }
}

.animate-pulse-slow {
  animation: pulse-slow 8s ease-in-out infinite;
}

.animation-delay-2000 {
  animation-delay: 2s;
}

/* 折叠动画 */
.collapse-enter-active,
.collapse-leave-active {
  transition: all 0.3s ease;
  overflow: hidden;
}
.collapse-enter-from,
.collapse-leave-to {
  opacity: 0;
  max-height: 0;
}

/* 淡入淡出动画 */
.fade-enter-active,
.fade-leave-active {
  transition: all 0.2s ease;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
  transform: translateY(-10px);
}

/* 自定义滚动条 */
.custom-scrollbar::-webkit-scrollbar { width: 6px; }
.custom-scrollbar::-webkit-scrollbar-track { background: transparent; }
.custom-scrollbar::-webkit-scrollbar-thumb { 
  background: rgba(200, 180, 140, 0.4); 
  border-radius: 3px; 
}
.custom-scrollbar::-webkit-scrollbar-thumb:hover { 
  background: rgba(200, 180, 140, 0.6); 
}

/* 消息区域滚动条 */
.overflow-y-auto::-webkit-scrollbar { width: 8px; }
.overflow-y-auto::-webkit-scrollbar-track { background: transparent; }
.overflow-y-auto::-webkit-scrollbar-thumb { 
  background: rgba(150, 150, 170, 0.3); 
  border-radius: 4px; 
}
.overflow-y-auto::-webkit-scrollbar-thumb:hover { 
  background: rgba(150, 150, 170, 0.5); 
}

/* Markdown 内容样式 */
.markdown-content {
  color: #374151;
}

.markdown-content :deep(.md-h1) {
  font-size: 1.5rem;
  font-weight: 700;
  color: #111827;
  margin: 1.25rem 0 0.75rem;
  padding-bottom: 0.5rem;
  border-bottom: 1px solid #e5e7eb;
}

.markdown-content :deep(.md-h2) {
  font-size: 1.25rem;
  font-weight: 600;
  color: #1f2937;
  margin: 1rem 0 0.5rem;
}

.markdown-content :deep(.md-h3) {
  font-size: 1.1rem;
  font-weight: 600;
  color: #374151;
  margin: 0.75rem 0 0.5rem;
}

.markdown-content :deep(.md-h4) {
  font-size: 1rem;
  font-weight: 600;
  color: #4b5563;
  margin: 0.5rem 0 0.25rem;
}

.markdown-content :deep(.md-p) {
  margin: 0.5rem 0;
  line-height: 1.7;
}

.markdown-content :deep(.md-ul),
.markdown-content :deep(.md-ol) {
  margin: 0.5rem 0;
  padding-left: 1.5rem;
}

.markdown-content :deep(.md-li),
.markdown-content :deep(.md-oli) {
  margin: 0.25rem 0;
  line-height: 1.6;
}

.markdown-content :deep(.md-ul) {
  list-style-type: disc;
}

.markdown-content :deep(.md-ol) {
  list-style-type: decimal;
}

.markdown-content :deep(.md-quote) {
  border-left: 3px solid #6366f1;
  padding-left: 1rem;
  margin: 0.75rem 0;
  color: #6b7280;
  font-style: italic;
}

.markdown-content :deep(.md-link) {
  color: #4f46e5;
  text-decoration: underline;
  text-underline-offset: 2px;
}

.markdown-content :deep(.md-link:hover) {
  color: #6366f1;
}

.markdown-content :deep(.md-hr) {
  border: none;
  border-top: 1px solid #e5e7eb;
  margin: 1rem 0;
}

.markdown-content :deep(.code-block) {
  background: #1e293b;
  border: 1px solid #334155;
  border-radius: 0.5rem;
  padding: 1rem;
  margin: 0.75rem 0;
  overflow-x: auto;
  font-family: 'JetBrains Mono', 'Fira Code', 'Consolas', monospace;
  font-size: 0.8rem;
  line-height: 1.5;
}

.markdown-content :deep(.code-block code) {
  color: #e2e8f0;
}

.markdown-content :deep(.inline-code) {
  background: #f1f5f9;
  color: #6366f1;
  padding: 0.1rem 0.35rem;
  border-radius: 0.25rem;
  font-family: 'JetBrains Mono', 'Fira Code', 'Consolas', monospace;
  font-size: 0.85em;
  border: 1px solid #e2e8f0;
}

.markdown-content :deep(strong) {
  color: #111827;
  font-weight: 600;
}

.markdown-content :deep(em) {
  color: #4b5563;
  font-style: italic;
}

/* 数学公式样式 */
.markdown-content :deep(.math-block) {
  margin: 0.75rem 0;
  padding: 1rem;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 0.5rem;
  overflow-x: auto;
  text-align: center;
}

/* MathJax 样式覆盖 - 行内公式 */
.markdown-content :deep(.math-inline) {
  display: inline !important;
  padding: 0 0.1rem;
  white-space: nowrap;
}

.markdown-content :deep(.math-inline mjx-container),
.markdown-content :deep(.math-inline mjx-container[jax="SVG"]),
.markdown-content :deep(.math-inline mjx-container[jax="CHTML"]) {
  display: inline !important;
  margin: 0 !important;
  padding: 0 !important;
  vertical-align: baseline !important;
}

.markdown-content :deep(.math-inline mjx-container svg) {
  display: inline !important;
  vertical-align: middle;
}

/* MathJax 样式覆盖 - 块级公式 */
.markdown-content :deep(.math-block) {
  display: block;
  margin: 0.75rem 0;
  padding: 1rem;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 0.5rem;
  overflow-x: auto;
  text-align: center;
}

.markdown-content :deep(.math-block mjx-container) {
  display: block !important;
  margin: 0 auto;
}

/* MathJax 通用样式 */
.markdown-content :deep(mjx-container) {
  color: #1f2937 !important;
}
</style>
