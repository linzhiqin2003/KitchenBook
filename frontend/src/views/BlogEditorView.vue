<script setup>
import { ref, onMounted, computed, watch, nextTick, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import axios from 'axios'
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

// ============== AI 助手浮窗 ==============
const aiPanelOpen = ref(false)
const aiLoading = ref(false)
const aiMessage = ref('')
const aiResponse = ref('')
const aiChatHistory = ref([]) // 对话历史
const aiPanelRef = ref(null)
const aiResponseRef = ref(null)

// 快捷操作
const aiActions = [
  { id: 'continue', label: '✨ 续写', icon: '✨' },
  { id: 'polish', label: '💎 润色', icon: '💎' },
  { id: 'expand', label: '📝 扩展', icon: '📝' },
  { id: 'summarize', label: '📋 摘要', icon: '📋' },
  { id: 'code_explain', label: '💻 解释代码', icon: '💻' },
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

onMounted(() => {
  fetchTags()
  fetchPost()
})

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

const insertAtEnd = (text) => {
  form.value.content += text
  nextTick(() => {
    if (editorRef.value) {
      editorRef.value.scrollTop = editorRef.value.scrollHeight
    }
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
  
  // 验证文件类型
  if (!file.type.startsWith('image/')) {
    alert('请选择图片文件')
    return
  }
  
  // 验证文件大小 (5MB)
  if (file.size > 5 * 1024 * 1024) {
    alert('图片大小不能超过 5MB')
    return
  }
  
  try {
    uploadingImage.value = true
    
    const formData = new FormData()
    formData.append('image', file)
    
    const response = await axios.post(`${API_BASE_URL}/api/blog/posts/upload-image/`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
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

// ============== AI 助手功能 ==============

// 获取选中的文本或上下文
const getSelectedContent = () => {
  const textarea = editorRef.value
  if (!textarea) return ''
  
  const start = textarea.selectionStart
  const end = textarea.selectionEnd
  
  if (start !== end) {
    return form.value.content.substring(start, end)
  }
  
  // 没有选中时返回最后 500 字符
  return form.value.content.slice(-500)
}

// 流式调用 AI
const callAiStream = async (action, customMessage = '') => {
  const content = getSelectedContent()
  
  if (action !== 'chat' && !content.trim()) {
    // 添加系统消息
    aiChatHistory.value.push({
      role: 'assistant',
      content: '请先在编辑器中输入一些内容，或选中要处理的文本。'
    })
    return
  }
  
  // 添加用户消息到历史
  const userMessage = customMessage || `[${aiActions.find(a => a.id === action)?.label || action}]`
  aiChatHistory.value.push({
    role: 'user',
    content: userMessage,
    action: action
  })
  
  // 添加占位的 AI 响应
  const aiMsgIndex = aiChatHistory.value.length
  aiChatHistory.value.push({
    role: 'assistant',
    content: '',
    loading: true
  })
  
  try {
    aiLoading.value = true
    
    const response = await fetch(`${API_BASE_URL}/api/blog/ai-assist/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        action,
        content: action !== 'chat' ? content : '',
        context: form.value.content.slice(0, 2000),
        message: customMessage
      })
    })
    
    if (!response.ok) {
      throw new Error('请求失败')
    }
    
    const reader = response.body.getReader()
    const decoder = new TextDecoder()
    let fullContent = ''
    
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
              fullContent += data.content
              // 更新 AI 响应
              aiChatHistory.value[aiMsgIndex] = {
                role: 'assistant',
                content: fullContent,
                loading: false,
                action: data.action
              }
              // 滚动到底部
              scrollToBottom()
            } else if (data.type === 'done') {
              aiChatHistory.value[aiMsgIndex].action = data.action
            } else if (data.type === 'error') {
              aiChatHistory.value[aiMsgIndex] = {
                role: 'assistant',
                content: `❌ 错误：${data.content}`,
                error: true
              }
            }
          } catch (e) {
            // 忽略解析错误
          }
        }
      }
    }
    
  } catch (error) {
    console.error('AI assist failed', error)
    aiChatHistory.value[aiMsgIndex] = {
      role: 'assistant',
      content: `❌ 请求失败：${error.message}`,
      error: true
    }
  } finally {
    aiLoading.value = false
  }
}

// 发送自由对话
const sendAiMessage = () => {
  if (!aiMessage.value.trim() || aiLoading.value) return
  
  const message = aiMessage.value.trim()
  aiMessage.value = ''
  callAiStream('chat', message)
}

// 快捷操作
const callQuickAction = (action) => {
  callAiStream(action)
}

// 复制 AI 响应
const copyAiResponse = (content) => {
  navigator.clipboard.writeText(content)
  // 简单的提示效果
}

// 插入 AI 响应到编辑器
const insertAiResponse = (content) => {
  insertAtEnd('\n\n' + content)
}

// 滚动到底部
const scrollToBottom = () => {
  nextTick(() => {
    if (aiResponseRef.value) {
      aiResponseRef.value.scrollTop = aiResponseRef.value.scrollHeight
    }
  })
}

// 清空对话
const clearChat = () => {
  aiChatHistory.value = []
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

// 简单的 Markdown 预览
const parseMarkdown = (markdown) => {
  if (!markdown) return '<p class="text-slate-400 italic">开始输入内容，右侧实时预览...</p>'
  
  let html = markdown
  
  // 图片
  html = html.replace(/!\[([^\]]*)\]\(([^)]+)\)/g, '<img src="$2" alt="$1" class="max-w-full rounded-lg my-4" />')
  
  // 代码块
  html = html.replace(/```(\w+)?\n([\s\S]*?)```/g, (match, lang, code) => {
    return `<pre class="bg-slate-800 text-slate-200 p-4 rounded-lg my-4 overflow-x-auto text-sm"><code>${code.trim().replace(/</g, '&lt;').replace(/>/g, '&gt;')}</code></pre>`
  })
  
  // 行内代码
  html = html.replace(/`([^`]+)`/g, '<code class="bg-slate-100 px-1.5 py-0.5 rounded text-purple-600 text-sm">$1</code>')
  
  // 标题
  html = html.replace(/^### (.+)$/gm, '<h3 class="text-lg font-bold mt-6 mb-2">$1</h3>')
  html = html.replace(/^## (.+)$/gm, '<h2 class="text-xl font-bold mt-8 mb-3">$1</h2>')
  html = html.replace(/^# (.+)$/gm, '<h1 class="text-2xl font-bold mt-8 mb-4 pb-2 border-b">$1</h1>')
  
  // 粗体和斜体
  html = html.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
  html = html.replace(/\*(.+?)\*/g, '<em>$1</em>')
  
  // 链接
  html = html.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" class="text-purple-600 underline" target="_blank">$1</a>')
  
  // 列表
  html = html.replace(/^\s*[-*]\s+(.+)$/gm, '<li class="ml-4">$1</li>')
  
  // 引用
  html = html.replace(/^>\s*(.+)$/gm, '<blockquote class="border-l-4 border-purple-400 pl-4 my-4 text-slate-600 italic">$1</blockquote>')
  
  // 分割线
  html = html.replace(/^---$/gm, '<hr class="my-6 border-t-2 border-slate-200" />')
  
  // 段落
  html = html.split('\n\n').map(block => {
    if (!block.trim()) return ''
    if (block.match(/^<[a-z]/i)) return block
    return `<p class="my-3">${block.replace(/\n/g, '<br>')}</p>`
  }).join('')
  
  return html
}

const renderedContent = computed(() => parseMarkdown(form.value.content))

// 简化的 Markdown 渲染（用于 AI 响应）
const renderAiMarkdown = (text) => {
  if (!text) return ''
  let html = text
  
  // 代码块
  html = html.replace(/```(\w+)?\n([\s\S]*?)```/g, (match, lang, code) => {
    return `<pre class="bg-slate-800 text-slate-200 p-3 rounded-lg my-2 overflow-x-auto text-xs"><code>${code.trim().replace(/</g, '&lt;').replace(/>/g, '&gt;')}</code></pre>`
  })
  
  // 行内代码
  html = html.replace(/`([^`]+)`/g, '<code class="bg-slate-200 px-1 py-0.5 rounded text-purple-700 text-xs">$1</code>')
  
  // 粗体
  html = html.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
  
  // 链接
  html = html.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" class="text-purple-600 underline" target="_blank">$1</a>')
  
  // 换行
  html = html.replace(/\n/g, '<br>')
  
  return html
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
        
        <!-- 保存按钮 -->
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
            
            <!-- AI 助手按钮 -->
            <div class="flex-grow"></div>
            <button
              @click="aiPanelOpen = !aiPanelOpen"
              :class="[
                'flex items-center gap-2 px-3 py-1.5 rounded-lg text-sm font-medium transition-all',
                aiPanelOpen 
                  ? 'bg-purple-600 text-white shadow-lg shadow-purple-500/30' 
                  : 'bg-purple-100 text-purple-700 hover:bg-purple-200'
              ]"
            >
              <span>🤖</span>
              <span>AI 助手</span>
              <span v-if="aiLoading" class="w-3 h-3 border-2 border-current border-t-transparent rounded-full animate-spin"></span>
            </button>
          </div>
          
          <!-- 编辑器内容区 -->
          <div class="flex" :class="viewMode === 'split' ? 'divide-x divide-slate-200' : ''">
            <div v-if="viewMode !== 'preview'" :class="viewMode === 'split' ? 'w-1/2' : 'w-full'">
              <textarea
                ref="editorRef"
                v-model="form.content"
                placeholder="在这里写下你的技术分享...

支持 Markdown 语法，可使用工具栏快速插入格式"
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
        
        <!-- Markdown 速查 -->
        <div class="bg-gradient-to-br from-slate-50 to-slate-100 rounded-2xl border border-slate-200 p-4">
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
    
    <!-- AI 助手浮窗 -->
    <Transition name="slide-panel">
      <div 
        v-if="aiPanelOpen"
        ref="aiPanelRef"
        class="fixed right-0 top-0 h-full w-96 bg-white shadow-2xl border-l border-slate-200 z-40 flex flex-col"
      >
        <!-- 头部 -->
        <div class="flex items-center justify-between px-4 py-3 border-b border-slate-200 bg-gradient-to-r from-purple-600 to-indigo-600">
          <div class="flex items-center gap-2 text-white">
            <span class="text-xl">🤖</span>
            <span class="font-bold">AI 写作助手</span>
          </div>
          <div class="flex items-center gap-2">
            <button
              @click="clearChat"
              class="p-1.5 text-white/70 hover:text-white hover:bg-white/10 rounded-lg transition-colors"
              title="清空对话"
            >
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
              </svg>
            </button>
            <button
              @click="aiPanelOpen = false"
              class="p-1.5 text-white/70 hover:text-white hover:bg-white/10 rounded-lg transition-colors"
            >
              <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>
        
        <!-- 快捷操作 -->
        <div class="px-4 py-3 border-b border-slate-100 bg-slate-50">
          <div class="text-xs text-slate-500 mb-2">快捷操作（基于选中文本或文章末尾）</div>
          <div class="flex flex-wrap gap-2">
            <button
              v-for="action in aiActions"
              :key="action.id"
              @click="callQuickAction(action.id)"
              :disabled="aiLoading"
              class="px-3 py-1.5 text-xs rounded-full bg-white border border-slate-200 text-slate-700 hover:border-purple-300 hover:bg-purple-50 hover:text-purple-700 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {{ action.label }}
            </button>
          </div>
        </div>
        
        <!-- 对话区域 -->
        <div 
          ref="aiResponseRef"
          class="flex-1 overflow-auto p-4 space-y-4"
        >
          <!-- 欢迎消息 -->
          <div v-if="aiChatHistory.length === 0" class="text-center py-8">
            <div class="text-4xl mb-3">🤖</div>
            <h3 class="font-bold text-slate-700 mb-2">AI 写作助手</h3>
            <p class="text-sm text-slate-500 mb-4">我可以帮你续写、润色、扩展文章内容</p>
            <p class="text-xs text-slate-400">在编辑器中选中文本，然后使用快捷操作<br/>或直接在下方输入你的问题</p>
          </div>
          
          <!-- 对话历史 -->
          <div
            v-for="(msg, index) in aiChatHistory"
            :key="index"
            :class="[
              'flex',
              msg.role === 'user' ? 'justify-end' : 'justify-start'
            ]"
          >
            <div
              :class="[
                'max-w-[85%] rounded-2xl px-4 py-2.5 text-sm',
                msg.role === 'user' 
                  ? 'bg-purple-600 text-white rounded-br-md' 
                  : msg.error 
                    ? 'bg-red-50 text-red-700 border border-red-200 rounded-bl-md'
                    : 'bg-slate-100 text-slate-700 rounded-bl-md'
              ]"
            >
              <!-- 用户消息 -->
              <div v-if="msg.role === 'user'">{{ msg.content }}</div>
              
              <!-- AI 消息 -->
              <div v-else>
                <!-- 加载动画 -->
                <div v-if="msg.loading" class="flex items-center gap-2">
                  <div class="flex gap-1">
                    <div class="w-2 h-2 bg-purple-500 rounded-full animate-bounce" style="animation-delay: 0ms"></div>
                    <div class="w-2 h-2 bg-purple-500 rounded-full animate-bounce" style="animation-delay: 150ms"></div>
                    <div class="w-2 h-2 bg-purple-500 rounded-full animate-bounce" style="animation-delay: 300ms"></div>
                  </div>
                  <span class="text-slate-500 text-xs">思考中...</span>
                </div>
                
                <!-- 内容 -->
                <div v-else>
                  <div class="ai-content prose-sm" v-html="renderAiMarkdown(msg.content)"></div>
                  
                  <!-- 操作按钮 -->
                  <div v-if="msg.content && !msg.error" class="flex items-center gap-2 mt-3 pt-2 border-t border-slate-200">
                    <button
                      @click="copyAiResponse(msg.content)"
                      class="text-xs text-slate-500 hover:text-slate-700 flex items-center gap-1"
                    >
                      📋 复制
                    </button>
                    <button
                      @click="insertAiResponse(msg.content)"
                      class="text-xs text-purple-600 hover:text-purple-800 flex items-center gap-1"
                    >
                      ✓ 插入文章
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
        
        <!-- 输入区域 -->
        <div class="p-4 border-t border-slate-200 bg-white">
          <div class="flex gap-2">
            <input
              v-model="aiMessage"
              @keyup.enter="sendAiMessage"
              type="text"
              placeholder="输入问题，或使用快捷操作..."
              :disabled="aiLoading"
              class="flex-1 px-4 py-2.5 border border-slate-200 rounded-xl text-sm focus:ring-2 focus:ring-purple-500 focus:border-transparent disabled:bg-slate-50"
            />
            <button
              @click="sendAiMessage"
              :disabled="!aiMessage.trim() || aiLoading"
              class="px-4 py-2.5 bg-purple-600 text-white rounded-xl hover:bg-purple-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
              </svg>
            </button>
          </div>
          <p class="text-xs text-slate-400 mt-2 text-center">
            按 Enter 发送 · 选中文本后使用快捷操作效果更佳
          </p>
        </div>
      </div>
    </Transition>
    
    <!-- 背景遮罩（移动端） -->
    <Transition name="fade">
      <div 
        v-if="aiPanelOpen"
        class="fixed inset-0 bg-black/20 z-30 lg:hidden"
        @click="aiPanelOpen = false"
      ></div>
    </Transition>
    
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

/* AI 响应内容样式 */
.ai-content {
  line-height: 1.6;
}

.ai-content :deep(pre) {
  margin: 0.5rem 0;
}

.ai-content :deep(code) {
  font-size: 0.75rem;
}

/* 面板滑入动画 */
.slide-panel-enter-active {
  transition: transform 0.3s cubic-bezier(0.16, 1, 0.3, 1);
}

.slide-panel-leave-active {
  transition: transform 0.25s cubic-bezier(0.4, 0, 1, 1);
}

.slide-panel-enter-from,
.slide-panel-leave-to {
  transform: translateX(100%);
}

/* 淡入淡出 */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
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

/* 加载动画 */
@keyframes bounce {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-4px); }
}
</style>
