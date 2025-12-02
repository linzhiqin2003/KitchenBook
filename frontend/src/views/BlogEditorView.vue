<script setup>
import { ref, onMounted, computed, watch, nextTick, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import axios from 'axios'
import { marked } from 'marked'
import hljs from 'highlight.js'
import API_BASE_URL from '../config/api'
import { auth } from '../store/auth'

const route = useRoute()
const router = useRouter()

const isEditMode = computed(() => !!route.params.id)
const loading = ref(false)
const saving = ref(false)
const allTags = ref([])
const showTagModal = ref(false)
const newTagName = ref('')
const newTagColor = ref('#10b981')

// 预览模式: 'edit' | 'preview' | 'split'
const viewMode = ref('edit')

// 编辑器引用
const editorRef = ref(null)

// 图片上传
const uploadingImage = ref(false)
const imageInputRef = ref(null)

// 表单数据
const form = ref({
  title: '',
  summary: '',
  content: '',
  cover_image: null,
  tag_ids: [],
  is_published: false,
  is_featured: false
})

const coverPreview = ref('')

// ============== 选中文本 AI 助手 ==============
const selectionMenu = ref({
  show: false,
  x: 0,
  y: 0,
  text: '',
  start: 0,
  end: 0
})

const aiPopup = ref({
  show: false,
  x: 0,
  y: 0,
  loading: false,
  content: '',
  action: '',
  selectionStart: 0,
  selectionEnd: 0
})

// 拖拽状态
const isDragging = ref(false)
const dragOffset = ref({ x: 0, y: 0 })

// 开始拖拽
const startDrag = (e) => {
  isDragging.value = true
  dragOffset.value = {
    x: e.clientX - aiPopup.value.x,
    y: e.clientY - aiPopup.value.y
  }
  document.addEventListener('mousemove', onDrag)
  document.addEventListener('mouseup', stopDrag)
}

// 拖拽中
const onDrag = (e) => {
  if (!isDragging.value) return
  aiPopup.value.x = Math.max(0, Math.min(e.clientX - dragOffset.value.x, window.innerWidth - 500))
  aiPopup.value.y = Math.max(0, Math.min(e.clientY - dragOffset.value.y, window.innerHeight - 200))
}

// 停止拖拽
const stopDrag = () => {
  isDragging.value = false
  document.removeEventListener('mousemove', onDrag)
  document.removeEventListener('mouseup', stopDrag)
}

// 提问输入框
const askModal = ref({
  show: false,
  question: '',
  x: 0,
  y: 0,
  selectedText: '',
  selectionStart: 0,
  selectionEnd: 0
})
const askInputRef = ref(null)

// AI 操作选项
const aiActions = [
  { id: 'continue', label: '续写', icon: '✨', desc: '继续写作' },
  { id: 'polish', label: '润色', icon: '💎', desc: '优化文字' },
  { id: 'expand', label: '扩展', icon: '📝', desc: '丰富内容' },
  { id: 'summarize', label: '摘要', icon: '📋', desc: '生成摘要' },
  { id: 'code_explain', label: '解释', icon: '💻', desc: '解释代码' },
  { id: 'ask', label: '提问', icon: '❓', desc: '询问 AI' },
]

// 获取所有标签
const fetchTags = async () => {
  try {
    const response = await axios.get(`${API_BASE_URL}/api/blog/tags/`)
    allTags.value = response.data
  } catch (error) {
    console.error('Failed to fetch tags', error)
  }
}

// 获取文章详情（编辑模式）
const fetchPost = async () => {
  if (!isEditMode.value) return
  
  try {
    loading.value = true
    const response = await axios.get(`${API_BASE_URL}/api/blog/posts/${route.params.id}/?mode=chef`, {
      headers: { Authorization: `Bearer ${auth.token}` }
    })
    const post = response.data
    form.value = {
      title: post.title,
      summary: post.summary,
      content: post.content,
      cover_image: null,
      tag_ids: post.tags?.map(t => t.id) || [],
      is_published: post.is_published,
      is_featured: post.is_featured
    }
    if (post.cover_image) {
      coverPreview.value = post.cover_image
    }
  } catch (error) {
    console.error('Failed to fetch post', error)
    alert('加载文章失败')
  } finally {
    loading.value = false
  }
}

// 监听文本选中
const handleSelectionChange = () => {
  const textarea = editorRef.value
  if (!textarea) return
  
  const start = textarea.selectionStart
  const end = textarea.selectionEnd
  
  if (start !== end && document.activeElement === textarea) {
    const selectedText = form.value.content.substring(start, end)
    
    if (selectedText.trim().length > 0) {
      // 计算选中文本的位置
      const rect = textarea.getBoundingClientRect()
      
      // 获取光标大致位置（简化计算）
      const textBeforeSelection = form.value.content.substring(0, start)
      const lines = textBeforeSelection.split('\n')
      const lineHeight = 24 // 估算行高
      const charWidth = 8 // 估算字符宽度
      
      const currentLine = lines.length - 1
      const currentCol = lines[lines.length - 1].length
      
      // 计算菜单位置
      const menuX = rect.left + Math.min(currentCol * charWidth, rect.width - 200) + 16
      const menuY = rect.top + Math.min(currentLine * lineHeight, textarea.scrollTop + 100) + 40
      
      selectionMenu.value = {
        show: true,
        x: Math.max(menuX, rect.left + 20),
        y: Math.min(menuY, rect.bottom - 60),
        text: selectedText,
        start,
        end
      }
    } else {
      selectionMenu.value.show = false
    }
  } else {
    // 延迟隐藏，避免点击菜单时立即消失
    setTimeout(() => {
      if (!aiPopup.value.show) {
        selectionMenu.value.show = false
      }
    }, 200)
  }
}

// 处理鼠标抬起事件
const handleMouseUp = (e) => {
  // 如果点击的是菜单或弹窗，不处理
  if (e.target.closest('.ai-selection-menu') || e.target.closest('.ai-result-popup')) {
    return
  }
  
  setTimeout(() => {
    handleSelectionChange()
  }, 10)
}

// 处理键盘选择
const handleKeyUp = (e) => {
  if (e.shiftKey && ['ArrowLeft', 'ArrowRight', 'ArrowUp', 'ArrowDown', 'Home', 'End'].includes(e.key)) {
    handleSelectionChange()
  }
}

// 点击其他地方关闭菜单
const handleClickOutside = (e) => {
  if (!e.target.closest('.ai-selection-menu') && 
      !e.target.closest('.ai-result-popup') &&
      !e.target.closest('.ai-ask-modal') &&
      !e.target.closest('textarea')) {
    selectionMenu.value.show = false
    if (!aiPopup.value.loading) {
      aiPopup.value.show = false
    }
    askModal.value.show = false
  }
}

onMounted(() => {
  fetchTags()
  fetchPost()
  document.addEventListener('click', handleClickOutside)
})

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
})

// AI 操作
const handleAiAction = async (action) => {
  const { text, start, end, x, y } = selectionMenu.value
  
  // 隐藏选择菜单
  selectionMenu.value.show = false
  
  // 如果是提问，显示自定义输入框
  if (action === 'ask') {
    askModal.value = {
      show: true,
      question: '',
      x: Math.min(x, window.innerWidth - 380),
      y: Math.min(y + 10, window.innerHeight - 250),
      selectedText: text,
      selectionStart: start,
      selectionEnd: end
    }
    // 聚焦输入框
    nextTick(() => {
      askInputRef.value?.focus()
    })
    return
  }
  
  aiPopup.value = {
    show: true,
    x: Math.min(x, window.innerWidth - 420),
    y: Math.min(y + 10, window.innerHeight - 300),
    loading: true,
    content: '',
    action,
    selectionStart: start,
    selectionEnd: end
  }
  
  await callAiStream(action, '', text)
}

// 流式调用 AI
const callAiStream = async (action, customMessage = '', selectedText = '') => {
  try {
    const response = await fetch(`${API_BASE_URL}/api/blog/ai-assist/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        action,
        content: selectedText || form.value.content.slice(-500),
        context: form.value.content.slice(0, 2000),
        message: customMessage
      })
    })
    
    if (!response.ok) {
      throw new Error('请求失败')
    }
    
    const reader = response.body.getReader()
    const decoder = new TextDecoder()
    
    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      
      const chunk = decoder.decode(value)
      const lines = chunk.split('\n')
      
      for (const line of lines) {
        if (line.startsWith('data: ')) {
          try {
            const data = JSON.parse(line.slice(6))
            
            if (data.type === 'content') {
              aiPopup.value.content += data.content
            } else if (data.type === 'done') {
              aiPopup.value.loading = false
            } else if (data.type === 'error') {
              aiPopup.value.content = `❌ 错误：${data.content}`
              aiPopup.value.loading = false
            }
          } catch (e) {
            // 忽略解析错误
          }
        }
      }
    }
    
    aiPopup.value.loading = false
    
  } catch (error) {
    console.error('AI assist failed', error)
    aiPopup.value.content = `❌ 请求失败：${error.message}`
    aiPopup.value.loading = false
  }
}

// AI 结果操作
const applyAiResult = (mode) => {
  const { content, selectionStart, selectionEnd, action } = aiPopup.value
  if (!content) return
  
  const textarea = editorRef.value
  
  if (mode === 'replace') {
    // 替换选中内容
    const text = form.value.content
    form.value.content = text.substring(0, selectionStart) + content + text.substring(selectionEnd)
  } else if (mode === 'insert') {
    // 在选中内容后插入
    const text = form.value.content
    form.value.content = text.substring(0, selectionEnd) + '\n\n' + content + text.substring(selectionEnd)
  } else if (mode === 'copy') {
    navigator.clipboard.writeText(content)
    return // 不关闭弹窗
  } else if (mode === 'summary') {
    form.value.summary = content
  }
  
  closeAiPopup()
  
  // 聚焦回编辑器
  nextTick(() => {
    textarea?.focus()
  })
}

const closeAiPopup = () => {
  aiPopup.value.show = false
  aiPopup.value.content = ''
  aiPopup.value.loading = false
}

// 提交提问
const submitAskQuestion = async () => {
  const { question, selectedText, selectionStart, selectionEnd, x, y } = askModal.value
  
  if (!question.trim()) return
  
  // 关闭提问输入框
  askModal.value.show = false
  
  // 显示 AI 响应弹窗
  aiPopup.value = {
    show: true,
    x: Math.min(x, window.innerWidth - 420),
    y: Math.min(y, window.innerHeight - 300),
    loading: true,
    content: '',
    action: 'ask',
    selectionStart,
    selectionEnd
  }
  
  // 调用 AI
  await callAiStream('chat', question, selectedText)
}

// 关闭提问输入框
const closeAskModal = () => {
  askModal.value.show = false
  askModal.value.question = ''
}

// 处理封面图上传
const handleCoverUpload = (event) => {
  const file = event.target.files[0]
  if (file) {
    form.value.cover_image = file
    coverPreview.value = URL.createObjectURL(file)
  }
}

// 移除封面图
const removeCover = () => {
  form.value.cover_image = null
  coverPreview.value = ''
}

// 切换标签
const toggleTag = (tagId) => {
  const index = form.value.tag_ids.indexOf(tagId)
  if (index > -1) {
    form.value.tag_ids.splice(index, 1)
  } else {
    form.value.tag_ids.push(tagId)
  }
}

// 创建标签
const createTag = async () => {
  if (!newTagName.value.trim()) return
  
  try {
    const response = await axios.post(`${API_BASE_URL}/api/blog/tags/`, {
      name: newTagName.value.trim(),
      color: newTagColor.value
    })
    allTags.value.push(response.data)
    form.value.tag_ids.push(response.data.id)
    newTagName.value = ''
    showTagModal.value = false
  } catch (error) {
    console.error('Failed to create tag', error)
    alert('创建标签失败')
  }
}

// 预设颜色
const presetColors = [
  '#ef4444', '#f97316', '#eab308', '#22c55e', '#10b981',
  '#14b8a6', '#06b6d4', '#3b82f6', '#6366f1', '#8b5cf6',
  '#a855f7', '#d946ef', '#ec4899', '#f43f5e'
]

// ============== 工具栏操作 ==============
const toolbarActions = {
  heading1: () => wrapText('# ', ''),
  heading2: () => wrapText('## ', ''),
  heading3: () => wrapText('### ', ''),
  bold: () => wrapText('**', '**'),
  italic: () => wrapText('*', '*'),
  code: () => wrapText('`', '`'),
  codeBlock: () => wrapText('```\n', '\n```'),
  link: () => wrapText('[', '](url)'),
  quote: () => wrapText('> ', ''),
  list: () => wrapText('- ', ''),
  hr: () => insertAtCursor('\n---\n')
}

const wrapText = (before, after) => {
  const textarea = editorRef.value
  if (!textarea) return
  
  const start = textarea.selectionStart
  const end = textarea.selectionEnd
  const text = form.value.content
  const selected = text.substring(start, end)
  
  form.value.content = text.substring(0, start) + before + selected + after + text.substring(end)
  
  nextTick(() => {
    textarea.focus()
    if (selected) {
      textarea.setSelectionRange(start + before.length, start + before.length + selected.length)
    } else {
      textarea.setSelectionRange(start + before.length, start + before.length)
    }
  })
}

const insertAtCursor = (text) => {
  const textarea = editorRef.value
  if (!textarea) return
  
  const start = textarea.selectionStart
  form.value.content = form.value.content.substring(0, start) + text + form.value.content.substring(start)
  
  nextTick(() => {
    textarea.focus()
    textarea.setSelectionRange(start + text.length, start + text.length)
  })
}

// 触发图片上传
const triggerImageUpload = () => {
  imageInputRef.value?.click()
}

// 处理图片上传
const handleImageUpload = async (event) => {
  const file = event.target.files[0]
  if (!file) return
  
  if (!file.type.startsWith('image/')) {
    alert('请选择图片文件')
    return
  }
  
  if (file.size > 5 * 1024 * 1024) {
    alert('图片大小不能超过 5MB')
    return
  }
  
  try {
    uploadingImage.value = true
    
    const formData = new FormData()
    formData.append('image', file)
    
    const response = await axios.post(`${API_BASE_URL}/api/blog/posts/upload-image/`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
    
    if (response.data.url) {
      insertAtCursor(`\n![${file.name}](${response.data.url})\n`)
    }
  } catch (error) {
    console.error('Failed to upload image', error)
    alert('图片上传失败：' + (error.response?.data?.error || '未知错误'))
  } finally {
    uploadingImage.value = false
    event.target.value = ''
  }
}

// 保存文章
const savePost = async (publish = false) => {
  if (!form.value.title.trim()) {
    alert('请填写文章标题')
    return
  }
  if (!form.value.content.trim()) {
    alert('请填写文章内容')
    return
  }
  
  try {
    saving.value = true
    
    const formData = new FormData()
    formData.append('title', form.value.title)
    formData.append('summary', form.value.summary)
    formData.append('content', form.value.content)
    formData.append('is_published', publish || form.value.is_published)
    formData.append('is_featured', form.value.is_featured)
    
    form.value.tag_ids.forEach(id => {
      formData.append('tag_ids', id)
    })
    
    if (form.value.cover_image instanceof File) {
      formData.append('cover_image', form.value.cover_image)
    }
    
    const config = {
      headers: {
        Authorization: `Bearer ${auth.token}`,
        'Content-Type': 'multipart/form-data'
      }
    }
    
    if (isEditMode.value) {
      await axios.patch(`${API_BASE_URL}/api/blog/posts/${route.params.id}/`, formData, config)
    } else {
      await axios.post(`${API_BASE_URL}/api/blog/posts/`, formData, config)
    }
    
    router.push('/chef/blog')
  } catch (error) {
    console.error('Failed to save post', error)
    alert('保存失败：' + (error.response?.data?.detail || '未知错误'))
  } finally {
    saving.value = false
  }
}

// 配置 marked - 编辑器预览用
const editorRenderer = new marked.Renderer()

editorRenderer.heading = (text, level) => {
  const sizes = {
    1: 'text-2xl font-bold mt-8 mb-4 pb-2 border-b border-slate-200',
    2: 'text-xl font-bold mt-6 mb-3',
    3: 'text-lg font-bold mt-5 mb-2',
    4: 'text-base font-bold mt-4 mb-2',
    5: 'text-sm font-bold mt-3 mb-1',
    6: 'text-xs font-bold mt-3 mb-1 uppercase tracking-wide text-slate-500'
  }
  return `<h${level} class="${sizes[level] || ''}">${text}</h${level}>`
}

editorRenderer.code = (code, lang) => {
  let highlighted = code
  if (lang && hljs.getLanguage(lang)) {
    try {
      highlighted = hljs.highlight(code, { language: lang }).value
    } catch (e) {
      highlighted = hljs.highlightAuto(code).value
    }
  } else {
    highlighted = hljs.highlightAuto(code).value
  }
  return `<pre class="bg-slate-800 text-slate-200 p-4 rounded-lg my-4 overflow-x-auto text-sm" data-lang="${lang || 'text'}"><code class="hljs">${highlighted}</code></pre>`
}

editorRenderer.codespan = (code) => {
  return `<code class="bg-slate-100 px-1.5 py-0.5 rounded text-purple-600 text-sm font-mono">${code}</code>`
}

editorRenderer.link = (href, title, text) => {
  return `<a href="${href}" class="text-purple-600 underline hover:text-purple-800" target="_blank" rel="noopener">${text}</a>`
}

editorRenderer.image = (href, title, text) => {
  return `<img src="${href}" alt="${text}" class="max-w-full rounded-lg my-4 shadow-md" loading="lazy" />`
}

editorRenderer.blockquote = (quote) => {
  return `<blockquote class="border-l-4 border-purple-400 pl-4 my-4 text-slate-600 italic">${quote}</blockquote>`
}

editorRenderer.list = (body, ordered) => {
  const tag = ordered ? 'ol' : 'ul'
  const cls = ordered ? 'list-decimal' : 'list-disc'
  return `<${tag} class="${cls} ml-6 my-3 space-y-1">${body}</${tag}>`
}

editorRenderer.listitem = (text) => {
  return `<li>${text}</li>`
}

editorRenderer.paragraph = (text) => {
  return `<p class="my-3 leading-relaxed">${text}</p>`
}

editorRenderer.hr = () => {
  return '<hr class="my-6 border-t-2 border-slate-200" />'
}

editorRenderer.table = (header, body) => {
  return `<div class="overflow-x-auto my-4"><table class="min-w-full border-collapse border border-slate-200"><thead class="bg-slate-50">${header}</thead><tbody>${body}</tbody></table></div>`
}

editorRenderer.tablerow = (content) => {
  return `<tr class="border-b border-slate-200">${content}</tr>`
}

editorRenderer.tablecell = (content, flags) => {
  const tag = flags.header ? 'th' : 'td'
  const align = flags.align ? ` class="text-${flags.align}"` : ''
  return `<${tag} class="px-4 py-2 border border-slate-200"${align}>${content}</${tag}>`
}

// Markdown 预览解析
const parseMarkdown = (markdown) => {
  if (!markdown) return '<p class="text-slate-400 italic">开始输入内容，右侧实时预览...</p>'
  
  return marked.parse(markdown, { 
    renderer: editorRenderer,
    breaks: true,
    gfm: true,
    headerIds: false
  })
}

const renderedContent = computed(() => parseMarkdown(form.value.content))

// AI Markdown 渲染 (简化版，用于浮窗)
const renderAiMarkdown = (text) => {
  if (!text) return ''
  
  const aiRenderer = new marked.Renderer()
  
  aiRenderer.code = (code, lang) => {
    let highlighted = code
    if (lang && hljs.getLanguage(lang)) {
      try {
        highlighted = hljs.highlight(code, { language: lang }).value
      } catch (e) {
        highlighted = hljs.highlightAuto(code).value
      }
    } else {
      highlighted = hljs.highlightAuto(code).value
    }
    return `<pre class="bg-slate-800 text-slate-200 p-3 rounded-lg my-2 overflow-x-auto text-xs"><code class="hljs">${highlighted}</code></pre>`
  }
  
  aiRenderer.codespan = (code) => {
    return `<code class="bg-purple-100 px-1 py-0.5 rounded text-purple-700 text-xs font-mono">${code}</code>`
  }
  
  aiRenderer.paragraph = (text) => {
    return `<p class="my-2">${text}</p>`
  }
  
  aiRenderer.heading = (text, level) => {
    const sizes = { 1: 'text-lg', 2: 'text-base', 3: 'text-sm', 4: 'text-sm', 5: 'text-xs', 6: 'text-xs' }
    return `<h${level} class="${sizes[level]} font-bold my-2">${text}</h${level}>`
  }
  
  aiRenderer.list = (body, ordered) => {
    const tag = ordered ? 'ol' : 'ul'
    const cls = ordered ? 'list-decimal' : 'list-disc'
    return `<${tag} class="${cls} ml-4 my-2 text-sm">${body}</${tag}>`
  }
  
  return marked.parse(text, { 
    renderer: aiRenderer,
    breaks: true,
    gfm: true,
    headerIds: false
  })
}

// 获取操作标签
const getActionLabel = (action) => {
  const found = aiActions.find(a => a.id === action)
  return found ? `${found.icon} ${found.label}` : action
}
</script>

<template>
  <div class="max-w-7xl mx-auto relative">
    <!-- 顶部工具栏 -->
    <div class="flex items-center justify-between mb-4">
      <div class="flex items-center gap-4">
        <button
          @click="router.push('/chef/blog')"
          class="flex items-center gap-2 text-slate-600 hover:text-slate-800 transition-colors"
        >
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
          </svg>
          返回
        </button>
        <h1 class="text-xl font-bold text-slate-800">
          {{ isEditMode ? '编辑文章' : '写新文章' }}
        </h1>
      </div>
      
      <div class="flex items-center gap-3">
        <!-- 预览模式切换 -->
        <div class="flex items-center bg-slate-100 rounded-lg p-0.5">
          <button
            v-for="mode in [
              { value: 'edit', icon: '📝', label: '编辑' },
              { value: 'split', icon: '📐', label: '分屏' },
              { value: 'preview', icon: '👁️', label: '预览' }
            ]"
            :key="mode.value"
            @click="viewMode = mode.value"
            :class="[
              'px-3 py-1.5 text-xs rounded-md transition-all',
              viewMode === mode.value
                ? 'bg-white text-purple-700 shadow-sm'
                : 'text-slate-600 hover:text-slate-800'
            ]"
          >
            {{ mode.icon }} {{ mode.label }}
          </button>
        </div>
        
        <button
          @click="savePost(false)"
          :disabled="saving"
          class="px-4 py-2 bg-slate-200 text-slate-700 rounded-lg text-sm font-medium hover:bg-slate-300 transition-colors disabled:opacity-50"
        >
          {{ saving ? '保存中...' : '保存草稿' }}
        </button>
        
        <button
          @click="savePost(true)"
          :disabled="saving"
          class="px-5 py-2 bg-purple-600 text-white rounded-lg text-sm font-medium hover:bg-purple-700 transition-colors shadow-lg shadow-purple-500/30 disabled:opacity-50"
        >
          {{ saving ? '发布中...' : (form.is_published ? '更新发布' : '立即发布') }}
        </button>
      </div>
    </div>
    
    <!-- 加载状态 -->
    <div v-if="loading" class="flex justify-center items-center py-20">
      <div class="w-12 h-12 border-4 border-purple-200 border-t-purple-600 rounded-full animate-spin"></div>
    </div>
    
    <!-- 编辑区域 -->
    <div v-else class="flex gap-4">
      <!-- 主编辑区 -->
      <div class="flex-1 min-w-0 space-y-3">
        <!-- 标题 -->
        <input
          v-model="form.title"
          type="text"
          placeholder="输入文章标题..."
          class="w-full px-4 py-3 text-xl font-bold border-0 border-b-2 border-slate-200 focus:border-purple-500 focus:outline-none bg-transparent placeholder-slate-300"
        />
        
        <!-- 摘要 -->
        <textarea
          v-model="form.summary"
          placeholder="简短描述文章内容（可选，用于列表展示）..."
          rows="2"
          class="w-full px-4 py-2 border border-slate-200 rounded-xl focus:ring-2 focus:ring-purple-500 focus:border-transparent resize-none text-slate-600 text-sm"
        ></textarea>
        
        <!-- 编辑器/预览区域 -->
        <div class="bg-white rounded-2xl border border-slate-200 overflow-hidden">
          <!-- 工具栏 -->
          <div v-if="viewMode !== 'preview'" class="bg-slate-50 px-3 py-2 border-b border-slate-200 flex flex-wrap items-center gap-1">
            <div class="flex items-center gap-0.5 mr-2">
              <button @click="toolbarActions.heading1" class="toolbar-btn" title="一级标题">H1</button>
              <button @click="toolbarActions.heading2" class="toolbar-btn" title="二级标题">H2</button>
              <button @click="toolbarActions.heading3" class="toolbar-btn" title="三级标题">H3</button>
            </div>
            
            <div class="w-px h-6 bg-slate-300 mr-2"></div>
            
            <button @click="toolbarActions.bold" class="toolbar-btn" title="粗体"><span class="font-bold">B</span></button>
            <button @click="toolbarActions.italic" class="toolbar-btn" title="斜体"><span class="italic">I</span></button>
            <button @click="toolbarActions.code" class="toolbar-btn font-mono text-xs" title="行内代码">&lt;/&gt;</button>
            <button @click="toolbarActions.codeBlock" class="toolbar-btn" title="代码块">
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4"/>
              </svg>
            </button>
            
            <div class="w-px h-6 bg-slate-300 mx-1"></div>
            
            <button @click="toolbarActions.link" class="toolbar-btn" title="链接">
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1"/>
              </svg>
            </button>
            <button @click="triggerImageUpload" :disabled="uploadingImage" class="toolbar-btn" title="插入图片">
              <svg v-if="!uploadingImage" class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"/>
              </svg>
              <div v-else class="w-4 h-4 border-2 border-slate-400 border-t-transparent rounded-full animate-spin"></div>
            </button>
            <input ref="imageInputRef" type="file" accept="image/*" class="hidden" @change="handleImageUpload" />
            
            <div class="w-px h-6 bg-slate-300 mx-1"></div>
            
            <button @click="toolbarActions.quote" class="toolbar-btn" title="引用">❝</button>
            <button @click="toolbarActions.list" class="toolbar-btn" title="列表">☰</button>
            <button @click="toolbarActions.hr" class="toolbar-btn" title="分割线">―</button>
            
            <!-- AI 提示 -->
            <div class="flex-grow"></div>
            <div class="text-xs text-slate-400 flex items-center gap-1">
              <span class="text-purple-500">✨</span>
              <span>选中文字后可使用 AI 助手</span>
            </div>
          </div>
          
          <!-- 编辑器内容区 -->
          <div class="flex" :class="viewMode === 'split' ? 'divide-x divide-slate-200' : ''">
            <div v-if="viewMode !== 'preview'" :class="viewMode === 'split' ? 'w-1/2' : 'w-full'" class="relative">
              <textarea
                ref="editorRef"
                v-model="form.content"
                @mouseup="handleMouseUp"
                @keyup="handleKeyUp"
                placeholder="在这里写下你的技术分享...

支持 Markdown 语法，选中文字后可呼出 AI 助手 ✨"
                class="w-full p-4 focus:outline-none resize-none font-mono text-sm leading-relaxed"
                :class="viewMode === 'split' ? 'h-[500px]' : 'h-[550px]'"
              ></textarea>
            </div>
            
            <div 
              v-if="viewMode !== 'edit'" 
              :class="viewMode === 'split' ? 'w-1/2' : 'w-full'"
              class="overflow-auto bg-white"
              :style="viewMode === 'split' ? 'height: 500px' : 'min-height: 550px'"
            >
              <div class="p-6 prose-preview" v-html="renderedContent"></div>
            </div>
          </div>
        </div>
      </div>
      
      <!-- 右侧设置面板 -->
      <div class="w-64 flex-shrink-0 space-y-4">
        <!-- 封面图 -->
        <div class="bg-white rounded-2xl border border-slate-200 p-4">
          <h3 class="font-bold text-slate-800 mb-3 flex items-center gap-2 text-sm">
            <span>🖼️</span> 封面图片
          </h3>
          
          <div v-if="coverPreview" class="relative mb-3">
            <img :src="coverPreview" class="w-full aspect-video object-cover rounded-lg" />
            <button
              @click="removeCover"
              class="absolute top-2 right-2 w-7 h-7 bg-red-500 text-white rounded-full flex items-center justify-center hover:bg-red-600 transition-colors text-sm"
            >
              ×
            </button>
          </div>
          
          <label class="block">
            <div class="border-2 border-dashed border-slate-200 rounded-xl p-4 text-center cursor-pointer hover:border-purple-400 hover:bg-purple-50 transition-all">
              <span class="text-2xl block mb-1">📷</span>
              <span class="text-xs text-slate-500">点击上传</span>
            </div>
            <input type="file" accept="image/*" class="hidden" @change="handleCoverUpload" />
          </label>
        </div>
        
        <!-- 标签 -->
        <div class="bg-white rounded-2xl border border-slate-200 p-4">
          <h3 class="font-bold text-slate-800 mb-3 flex items-center justify-between text-sm">
            <span class="flex items-center gap-2"><span>🏷️</span> 标签</span>
            <button @click="showTagModal = true" class="text-xs text-purple-600 hover:text-purple-800">+ 新建</button>
          </h3>
          
          <div class="flex flex-wrap gap-1.5">
            <button
              v-for="tag in allTags"
              :key="tag.id"
              @click="toggleTag(tag.id)"
              :class="[
                'px-2.5 py-1 rounded-full text-xs font-medium transition-all border',
                form.tag_ids.includes(tag.id)
                  ? 'text-white border-transparent'
                  : 'bg-white border-slate-200 hover:border-purple-300'
              ]"
              :style="form.tag_ids.includes(tag.id) ? { backgroundColor: tag.color } : { color: tag.color }"
            >
              {{ tag.name }}
            </button>
            
            <div v-if="allTags.length === 0" class="text-xs text-slate-400 py-2">暂无标签</div>
          </div>
        </div>
        
        <!-- 发布设置 -->
        <div class="bg-white rounded-2xl border border-slate-200 p-4">
          <h3 class="font-bold text-slate-800 mb-3 flex items-center gap-2 text-sm">
            <span>⚙️</span> 发布设置
          </h3>
          
          <div class="space-y-2">
            <label class="flex items-center gap-2 cursor-pointer p-1.5 rounded-lg hover:bg-slate-50">
              <input v-model="form.is_featured" type="checkbox" class="w-4 h-4 rounded border-slate-300 text-purple-600 focus:ring-purple-500" />
              <span class="font-medium text-slate-700 text-sm">⭐ 设为精选</span>
            </label>
            
            <label class="flex items-center gap-2 cursor-pointer p-1.5 rounded-lg hover:bg-slate-50">
              <input v-model="form.is_published" type="checkbox" class="w-4 h-4 rounded border-slate-300 text-purple-600 focus:ring-purple-500" />
              <span class="font-medium text-slate-700 text-sm">📢 公开发布</span>
            </label>
          </div>
        </div>
        
        <!-- AI 提示卡片 -->
        <div class="bg-gradient-to-br from-purple-50 to-indigo-50 rounded-2xl border border-purple-100 p-4">
          <h3 class="font-bold text-purple-800 mb-2 flex items-center gap-2 text-sm">
            <span>✨</span> AI 写作助手
          </h3>
          <p class="text-xs text-purple-600 leading-relaxed">
            选中文字后，会弹出 AI 菜单，可快速：
          </p>
          <div class="mt-2 flex flex-wrap gap-1">
            <span class="text-xs bg-white px-2 py-0.5 rounded-full text-purple-700">续写</span>
            <span class="text-xs bg-white px-2 py-0.5 rounded-full text-purple-700">润色</span>
            <span class="text-xs bg-white px-2 py-0.5 rounded-full text-purple-700">扩展</span>
            <span class="text-xs bg-white px-2 py-0.5 rounded-full text-purple-700">摘要</span>
          </div>
        </div>
        
        <!-- Markdown 速查 -->
        <div class="bg-slate-50 rounded-2xl border border-slate-200 p-4">
          <h3 class="font-bold text-slate-700 mb-2 flex items-center gap-2 text-sm">
            <span>⌨️</span> Markdown 速查
          </h3>
          <div class="text-xs text-slate-500 space-y-1 font-mono">
            <div># 标题 ## 二级</div>
            <div>**粗体** *斜体*</div>
            <div>`代码` ```代码块```</div>
            <div>[链接](url) ![图](url)</div>
            <div>- 列表 > 引用</div>
          </div>
        </div>
      </div>
    </div>
    
    <!-- 选中文字后的 AI 菜单 (Notion/iOS 风格) -->
    <Teleport to="body">
      <Transition name="menu-pop">
        <div
          v-if="selectionMenu.show"
          class="ai-selection-menu fixed z-50"
          :style="{ left: selectionMenu.x + 'px', top: selectionMenu.y + 'px' }"
        >
          <div class="bg-slate-900 rounded-xl shadow-2xl p-1 flex items-center gap-0.5 backdrop-blur-xl">
            <button
              v-for="action in aiActions"
              :key="action.id"
              @click="handleAiAction(action.id)"
              class="flex items-center gap-1.5 px-3 py-2 text-white/90 hover:bg-white/10 rounded-lg transition-all text-sm whitespace-nowrap group"
              :title="action.desc"
            >
              <span class="text-base">{{ action.icon }}</span>
              <span class="hidden sm:inline text-xs font-medium">{{ action.label }}</span>
            </button>
          </div>
          <!-- 小三角 -->
          <div class="absolute -top-2 left-6 w-4 h-4 bg-slate-900 transform rotate-45"></div>
        </div>
      </Transition>
    </Teleport>
    
    <!-- 简约提问输入框 -->
    <Teleport to="body">
      <Transition name="popup-scale">
        <div
          v-if="askModal.show"
          class="ai-ask-modal fixed z-50"
          :style="{ left: askModal.x + 'px', top: askModal.y + 'px' }"
        >
          <div class="bg-white/95 backdrop-blur-xl rounded-2xl shadow-xl border border-slate-200/50 w-72 overflow-hidden">
            <!-- 简洁输入框 -->
            <div class="p-3">
              <div class="relative">
                <textarea
                  ref="askInputRef"
                  v-model="askModal.question"
                  @keydown.enter.exact.prevent="submitAskQuestion"
                  @keydown.escape="closeAskModal"
                  placeholder="问点什么..."
                  rows="2"
                  class="w-full px-3 py-2 bg-slate-50 border-0 rounded-xl text-sm resize-none focus:ring-2 focus:ring-purple-500/50 focus:bg-white placeholder-slate-400 transition-all"
                ></textarea>
              </div>
              
              <!-- 选中内容提示 + 操作 -->
              <div class="flex items-center justify-between mt-2">
                <div v-if="askModal.selectedText" class="text-xs text-slate-400 truncate max-w-[140px]" :title="askModal.selectedText">
                  📝 {{ askModal.selectedText.slice(0, 20) }}{{ askModal.selectedText.length > 20 ? '...' : '' }}
                </div>
                <div v-else></div>
                
                <div class="flex items-center gap-1">
                  <button
                    @click="closeAskModal"
                    class="p-1.5 text-slate-400 hover:text-slate-600 hover:bg-slate-100 rounded-lg transition-all"
                    title="取消 (Esc)"
                  >
                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  </button>
                  <button
                    @click="submitAskQuestion"
                    :disabled="!askModal.question.trim()"
                    class="p-1.5 text-purple-600 hover:text-purple-700 hover:bg-purple-50 rounded-lg transition-all disabled:opacity-30 disabled:cursor-not-allowed"
                    title="发送 (Enter)"
                  >
                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
                    </svg>
                  </button>
                </div>
              </div>
            </div>
          </div>
          <!-- 小三角指示器 -->
          <div class="absolute -top-1.5 left-8 w-3 h-3 bg-white border-l border-t border-slate-200/50 transform rotate-45"></div>
        </div>
      </Transition>
    </Teleport>
    
    <!-- AI 结果浮窗 (简约可伸缩设计) -->
    <Teleport to="body">
      <Transition name="popup-scale">
        <div
          v-if="aiPopup.show"
          class="ai-result-popup fixed z-50"
          :style="{ left: aiPopup.x + 'px', top: aiPopup.y + 'px' }"
        >
          <div class="bg-white/95 backdrop-blur-xl rounded-2xl shadow-2xl border border-slate-200/60 overflow-hidden resize flex flex-col" style="width: 480px; min-width: 320px; min-height: 200px; max-width: min(700px, 90vw); max-height: 70vh;">
            <!-- 简约头部 (可拖拽) -->
            <div 
              @mousedown="startDrag"
              class="flex items-center justify-between px-4 py-2.5 border-b border-slate-100 bg-slate-50/80 cursor-move select-none flex-shrink-0"
            >
              <div class="flex items-center gap-2">
                <span class="text-purple-600">{{ aiActions.find(a => a.id === aiPopup.action)?.icon || '✨' }}</span>
                <span class="font-medium text-sm text-slate-700">{{ getActionLabel(aiPopup.action) }}</span>
                <span v-if="aiPopup.loading" class="flex items-center gap-1 ml-2">
                  <span class="w-1.5 h-1.5 bg-purple-500 rounded-full animate-bounce"></span>
                  <span class="w-1.5 h-1.5 bg-purple-500 rounded-full animate-bounce" style="animation-delay: 0.15s"></span>
                  <span class="w-1.5 h-1.5 bg-purple-500 rounded-full animate-bounce" style="animation-delay: 0.3s"></span>
                </span>
              </div>
              <button
                @click="closeAiPopup"
                class="p-1 text-slate-400 hover:text-slate-600 hover:bg-slate-200 rounded-lg transition-all"
              >
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
            
            <!-- 内容区域 (可滚动，flex-grow 自适应) -->
            <div class="p-4 overflow-auto flex-grow min-h-0">
              <div 
                v-if="aiPopup.content"
                class="text-sm text-slate-700 leading-relaxed ai-content prose prose-sm max-w-none"
                v-html="renderAiMarkdown(aiPopup.content)"
              ></div>
              <div v-else-if="aiPopup.loading" class="flex items-center gap-2 text-sm text-slate-400">
                <svg class="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
                  <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                  <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"></path>
                </svg>
                AI 正在生成...
              </div>
            </div>
            
            <!-- 底部操作栏 (固定不收缩) -->
            <div v-if="aiPopup.content && !aiPopup.loading" class="flex items-center justify-between px-4 py-2.5 border-t border-slate-100 bg-slate-50/50 flex-shrink-0">
              <button
                @click="applyAiResult('copy')"
                class="flex items-center gap-1.5 px-2.5 py-1.5 text-xs text-slate-500 hover:text-slate-700 hover:bg-slate-100 rounded-lg transition-all"
              >
                <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                </svg>
                复制
              </button>
              <div class="flex items-center gap-2">
                <button
                  @click="closeAiPopup"
                  class="px-3 py-1.5 text-xs text-slate-500 hover:text-slate-700 hover:bg-slate-100 rounded-lg transition-all"
                >
                  关闭
                </button>
                <button
                  v-if="aiPopup.action === 'summarize'"
                  @click="applyAiResult('summary')"
                  class="px-3 py-1.5 text-xs bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-all"
                >
                  填入摘要
                </button>
                <button
                  v-else-if="aiPopup.action === 'polish' || aiPopup.action === 'code_explain'"
                  @click="applyAiResult('replace')"
                  class="px-3 py-1.5 text-xs bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-all"
                >
                  替换原文
                </button>
                <button
                  v-else
                  @click="applyAiResult('insert')"
                  class="px-3 py-1.5 text-xs bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-all"
                >
                  插入文章
                </button>
              </div>
            </div>
            
            <!-- 右下角拖拽提示 -->
            <div class="absolute bottom-1 right-1 text-slate-300 pointer-events-none">
              <svg class="w-3 h-3" viewBox="0 0 24 24" fill="currentColor">
                <path d="M22 22H20V20H22V22ZM22 18H20V16H22V18ZM18 22H16V20H18V22ZM22 14H20V12H22V14ZM18 18H16V16H18V18ZM14 22H12V20H14V22Z"/>
              </svg>
            </div>
          </div>
        </div>
      </Transition>
    </Teleport>
    
    
    <!-- 新建标签弹窗 -->
    <Teleport to="body">
      <Transition name="modal">
        <div v-if="showTagModal" class="fixed inset-0 z-50 flex items-center justify-center p-4">
          <div class="absolute inset-0 bg-black/50" @click="showTagModal = false"></div>
          <div class="relative bg-white rounded-2xl p-6 w-full max-w-md shadow-2xl">
            <h3 class="text-xl font-bold text-slate-800 mb-4">新建标签</h3>
            
            <div class="space-y-4">
              <div>
                <label class="block text-sm font-medium text-slate-700 mb-1">标签名称</label>
                <input
                  v-model="newTagName"
                  type="text"
                  placeholder="如：Vue.js、Python、DevOps..."
                  class="w-full px-4 py-2 border border-slate-200 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                />
              </div>
              
              <div>
                <label class="block text-sm font-medium text-slate-700 mb-2">标签颜色</label>
                <div class="flex flex-wrap gap-2 mb-3">
                  <button
                    v-for="color in presetColors"
                    :key="color"
                    @click="newTagColor = color"
                    :class="[
                      'w-7 h-7 rounded-full transition-transform',
                      newTagColor === color ? 'ring-2 ring-offset-2 ring-slate-400 scale-110' : 'hover:scale-110'
                    ]"
                    :style="{ backgroundColor: color }"
                  ></button>
                </div>
                <div class="flex items-center gap-2">
                  <input v-model="newTagColor" type="color" class="w-10 h-10 rounded cursor-pointer" />
                  <input v-model="newTagColor" type="text" class="flex-1 px-3 py-2 border border-slate-200 rounded-lg text-sm font-mono" />
                </div>
              </div>
              
              <div class="p-3 bg-slate-50 rounded-lg">
                <span class="text-sm text-slate-500 mr-2">预览：</span>
                <span class="px-3 py-1 rounded-full text-white text-sm font-medium" :style="{ backgroundColor: newTagColor }">
                  {{ newTagName || '标签名称' }}
                </span>
              </div>
            </div>
            
            <div class="flex justify-end gap-3 mt-6">
              <button @click="showTagModal = false" class="px-4 py-2 text-slate-600 hover:text-slate-800">取消</button>
              <button
                @click="createTag"
                :disabled="!newTagName.trim()"
                class="px-6 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                创建
              </button>
            </div>
          </div>
        </div>
      </Transition>
    </Teleport>
  </div>
</template>

<style scoped>
.toolbar-btn {
  @apply w-8 h-8 flex items-center justify-center rounded text-slate-600 hover:bg-slate-200 hover:text-slate-800 transition-colors text-sm;
}

.prose-preview {
  font-size: 1rem;
  line-height: 1.75;
  color: #374151;
}

/* AI 内容样式 */
.ai-content {
  line-height: 1.6;
}

.ai-content :deep(pre) {
  margin: 0.5rem 0;
}

.ai-content :deep(code) {
  font-size: 0.75rem;
}

/* 菜单弹出动画 */
.menu-pop-enter-active {
  animation: menuPop 0.2s cubic-bezier(0.34, 1.56, 0.64, 1);
}

.menu-pop-leave-active {
  animation: menuPop 0.15s ease-in reverse;
}

@keyframes menuPop {
  from {
    opacity: 0;
    transform: scale(0.9) translateY(8px);
  }
  to {
    opacity: 1;
    transform: scale(1) translateY(0);
  }
}

/* 浮窗缩放动画 */
.popup-scale-enter-active {
  animation: popupScale 0.25s cubic-bezier(0.34, 1.56, 0.64, 1);
}

.popup-scale-leave-active {
  animation: popupScale 0.15s ease-in reverse;
}

@keyframes popupScale {
  from {
    opacity: 0;
    transform: scale(0.95);
  }
  to {
    opacity: 1;
    transform: scale(1);
  }
}

/* 弹窗动画 */
.modal-enter-active,
.modal-leave-active {
  transition: all 0.3s ease;
}

.modal-enter-from,
.modal-leave-to {
  opacity: 0;
}

.modal-enter-from .relative,
.modal-leave-to .relative {
  transform: scale(0.95);
}
</style>
