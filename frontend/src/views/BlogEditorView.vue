<script setup>
import { ref, onMounted, computed, nextTick } from 'vue'
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
const isDarkTheme = ref(localStorage.getItem('blog_theme') !== 'light')
const studioBasePath = '/blog/studio'

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

const toggleTheme = () => {
  isDarkTheme.value = !isDarkTheme.value
  localStorage.setItem('blog_theme', isDarkTheme.value ? 'dark' : 'light')
}

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
    
    router.push(studioBasePath)
  } catch (error) {
    console.error('Failed to save post', error)
    alert('保存失败：' + (error.response?.data?.detail || '未知错误'))
  } finally {
    saving.value = false
  }
}

// 配置 marked - 使用简单配置
marked.setOptions({
  breaks: true,
  gfm: true
})

// 允许的 HTML 标签白名单
const allowedTags = ['a', 'b', 'i', 'strong', 'em', 'u', 'strike', 's', 'del', 'ins', 'mark', 
  'small', 'big', 'sup', 'sub', 'br', 'hr', 'p', 'div', 'span', 'ul', 'ol', 'li', 
  'table', 'thead', 'tbody', 'tr', 'th', 'td', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
  'blockquote', 'pre', 'code', 'img', 'video', 'audio', 'source', 'iframe', 'figure', 
  'figcaption', 'details', 'summary', 'abbr', 'cite', 'q', 'dfn', 'kbd', 'samp', 'var']


// 简单的代码高亮函数
const highlightCode = (code, lang) => {
  if (lang && hljs.getLanguage(lang)) {
    try {
      return hljs.highlight(code, { language: lang }).value
    } catch (e) {
      return hljs.highlightAuto(code).value
    }
  }
  return hljs.highlightAuto(code).value
}

// Markdown 预览解析 - 使用后处理方式添加样式
const parseMarkdown = (markdown) => {
  if (!markdown) return '<p class="text-slate-400 italic">开始输入内容，右侧实时预览...</p>'
  
  // 预处理：转义未知的 HTML 标签（在代码块外）
  // 使用正则匹配非标准 HTML 标签并转义
  let processedMarkdown = markdown.replace(/<([a-zA-Z][a-zA-Z0-9]*)(?:\s[^>]*)?>(?![\s\S]*?<\/\1>)/g, (match, tagName) => {
    if (allowedTags.includes(tagName.toLowerCase())) {
      return match
    }
    return match.replace(/</g, '&lt;').replace(/>/g, '&gt;')
  })
  
  let html = marked.parse(processedMarkdown)
  
  // 后处理：添加样式类
  html = html.replace(/<h1>/g, '<h1 class="text-2xl font-bold mt-8 mb-4 pb-2 border-b border-slate-200">')
  html = html.replace(/<h2>/g, '<h2 class="text-xl font-bold mt-6 mb-3">')
  html = html.replace(/<h3>/g, '<h3 class="text-lg font-bold mt-5 mb-2">')
  html = html.replace(/<h4>/g, '<h4 class="text-base font-bold mt-4 mb-2">')
  html = html.replace(/<h5>/g, '<h5 class="text-sm font-bold mt-3 mb-1">')
  html = html.replace(/<h6>/g, '<h6 class="text-xs font-bold mt-3 mb-1 uppercase tracking-wide text-slate-500">')
  html = html.replace(/<p>/g, '<p class="my-3 leading-relaxed">')
  html = html.replace(/<ul>/g, '<ul class="list-disc ml-6 my-3 space-y-1">')
  html = html.replace(/<ol>/g, '<ol class="list-decimal ml-6 my-3 space-y-1">')
  html = html.replace(/<blockquote>/g, '<blockquote class="border-l-4 border-purple-400 pl-4 my-4 text-slate-600 italic">')
  html = html.replace(/<a /g, '<a class="text-purple-600 underline hover:text-purple-800" target="_blank" rel="noopener" ')
  html = html.replace(/<img /g, '<img class="max-w-full rounded-lg my-4 shadow-md" loading="lazy" ')
  html = html.replace(/<hr>/g, '<hr class="my-6 border-t-2 border-slate-200">')
  html = html.replace(/<table>/g, '<table class="min-w-full border-collapse border border-slate-200 my-4">')
  html = html.replace(/<th>/g, '<th class="px-4 py-2 border border-slate-200 bg-slate-50">')
  html = html.replace(/<td>/g, '<td class="px-4 py-2 border border-slate-200">')
  
  // 代码块高亮
  html = html.replace(/<pre><code class="language-(\w+)">([\s\S]*?)<\/code><\/pre>/g, (match, lang, code) => {
    const decoded = code.replace(/&lt;/g, '<').replace(/&gt;/g, '>').replace(/&amp;/g, '&')
    const highlighted = highlightCode(decoded, lang)
    return `<pre class="bg-slate-800 text-slate-200 p-4 rounded-lg my-4 overflow-x-auto text-sm" data-lang="${lang}"><code class="hljs">${highlighted}</code></pre>`
  })
  
  // 无语言代码块
  html = html.replace(/<pre><code>([\s\S]*?)<\/code><\/pre>/g, (match, code) => {
    const decoded = code.replace(/&lt;/g, '<').replace(/&gt;/g, '>').replace(/&amp;/g, '&')
    const highlighted = highlightCode(decoded, '')
    return `<pre class="bg-slate-800 text-slate-200 p-4 rounded-lg my-4 overflow-x-auto text-sm"><code class="hljs">${highlighted}</code></pre>`
  })
  
  // 行内代码
  html = html.replace(/<code>/g, '<code class="bg-slate-100 px-1.5 py-0.5 rounded text-purple-600 text-sm font-mono">')
  
  return html
}

const renderedContent = computed(() => parseMarkdown(form.value.content))
const toolbarButtonClass = computed(() => isDarkTheme.value ? 'toolbar-btn toolbar-btn-dark' : 'toolbar-btn')
</script>

<template>
  <div :class="[
    'min-h-screen transition-colors duration-500',
    isDarkTheme ? 'bg-[#0a0a0f] text-slate-100' : 'bg-gradient-to-br from-slate-50 via-white to-violet-50 text-slate-800'
  ]">
    <div class="relative overflow-hidden">
      <div class="absolute inset-0 bg-[radial-gradient(circle_at_top_left,rgba(139,92,246,0.22),transparent_35%),radial-gradient(circle_at_top_right,rgba(236,72,153,0.18),transparent_30%)]"></div>
      <div class="absolute inset-0 opacity-40" :class="isDarkTheme ? 'bg-[linear-gradient(rgba(255,255,255,0.03)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,0.03)_1px,transparent_1px)]' : 'bg-[linear-gradient(rgba(139,92,246,0.04)_1px,transparent_1px),linear-gradient(90deg,rgba(139,92,246,0.04)_1px,transparent_1px)]'" style="background-size: 40px 40px;"></div>
      <div class="relative max-w-7xl mx-auto px-4 md:px-6 py-8 md:py-10">
    <!-- 顶部工具栏 -->
    <div class="flex flex-col gap-6 md:flex-row md:items-start md:justify-between mb-6">
      <div class="space-y-4">
        <div class="flex items-center gap-3 text-sm">
          <button 
            @click="router.push(studioBasePath)"
            :class="[
              'inline-flex items-center gap-2 rounded-full px-3 py-1.5 transition-colors',
              isDarkTheme ? 'bg-white/5 text-slate-300 hover:bg-white/10 hover:text-white' : 'bg-white/70 text-slate-600 hover:text-violet-700 hover:bg-white'
            ]"
          >
            <span>←</span>
            返回写作台
          </button>
          <router-link
            to="/blog"
            :class="[
              'inline-flex items-center gap-2 rounded-full px-3 py-1.5 transition-colors',
              isDarkTheme ? 'bg-white/5 text-slate-300 hover:bg-white/10 hover:text-white' : 'bg-white/70 text-slate-600 hover:text-violet-700 hover:bg-white'
            ]"
          >
            浏览前台
          </router-link>
        </div>
        <div class="flex items-center gap-4">
          <div class="w-14 h-14 rounded-2xl bg-gradient-to-br from-violet-500 to-fuchsia-500 shadow-lg shadow-violet-500/30 flex items-center justify-center text-2xl">
            ✍️
          </div>
          <div>
            <p :class="isDarkTheme ? 'text-violet-300/80' : 'text-violet-600'" class="text-xs uppercase tracking-[0.35em] mb-2">Writing Deck</p>
            <h1 :class="isDarkTheme ? 'text-white' : 'text-slate-900'" class="text-3xl md:text-4xl font-bold tracking-tight">
              {{ isEditMode ? '编辑文章' : '写新文章' }}
            </h1>
            <p :class="isDarkTheme ? 'text-slate-400' : 'text-slate-500'" class="mt-2 text-sm">
              在独立的 Blog 写作区内完成标题、摘要、封面、标签与 Markdown 正文编辑。
            </p>
          </div>
        </div>
      </div>
      
      <div class="flex flex-wrap items-center gap-3">
        <button
          @click="toggleTheme"
          :class="[
            'w-11 h-11 rounded-full border transition-colors flex items-center justify-center',
            isDarkTheme ? 'border-white/10 bg-white/5 text-slate-300 hover:bg-white/10 hover:text-white' : 'border-slate-200 bg-white/80 text-slate-600 hover:text-violet-700'
          ]"
          :title="isDarkTheme ? '切换亮色模式' : '切换暗色模式'"
        >
          <span>{{ isDarkTheme ? '☀️' : '🌙' }}</span>
        </button>
        <div :class="isDarkTheme ? 'bg-white/5 border-white/10' : 'bg-white/80 border-white'" class="flex items-center rounded-full border p-1 backdrop-blur-xl">
        <button
            v-for="mode in [
              { value: 'edit', icon: '📝', label: '编辑' },
              { value: 'split', icon: '📐', label: '分屏' },
              { value: 'preview', icon: '👁️', label: '预览' }
            ]"
            :key="mode.value"
            @click="viewMode = mode.value"
          :class="[
              'px-3 py-2 text-xs rounded-full transition-all',
              viewMode === mode.value
                ? 'bg-white text-purple-700 shadow-sm'
                : (isDarkTheme ? 'text-slate-300 hover:text-white' : 'text-slate-600 hover:text-slate-800')
            ]"
          >
            {{ mode.icon }} {{ mode.label }}
        </button>
        </div>
        
        <button
          @click="savePost(false)"
          :disabled="saving"
          :class="[
            'px-4 py-2.5 rounded-full text-sm font-medium transition-colors disabled:opacity-50',
            isDarkTheme ? 'bg-white/10 text-slate-100 hover:bg-white/15 border border-white/10' : 'bg-slate-200 text-slate-700 hover:bg-slate-300'
          ]"
        >
          {{ saving ? '保存中...' : '保存草稿' }}
        </button>
        
        <button
          @click="savePost(true)"
          :disabled="saving"
          class="px-5 py-2.5 bg-gradient-to-r from-violet-600 to-fuchsia-600 text-white rounded-full text-sm font-medium transition-colors shadow-lg shadow-purple-500/30 disabled:opacity-50"
        >
          {{ saving ? '发布中...' : (form.is_published ? '更新发布' : '立即发布') }}
        </button>
      </div>
    </div>
      </div>
    </div>

  <div class="max-w-7xl mx-auto px-4 md:px-6 pb-12 relative">
    <div class="flex items-center justify-between mb-4">
      <div class="flex items-center gap-4">
        <button 
          @click="router.push(studioBasePath)"
          :class="isDarkTheme ? 'text-slate-400 hover:text-white' : 'text-slate-600 hover:text-slate-800'"
          class="flex items-center gap-2 transition-colors"
        >
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
          </svg>
          返回
        </button>
      </div>
    </div>
    
    <!-- 加载状态 -->
    <div v-if="loading" class="flex justify-center items-center py-20">
      <div class="w-12 h-12 border-4 border-purple-200 border-t-purple-600 rounded-full animate-spin"></div>
    </div>
    
    <!-- 编辑区域 -->
    <div v-else class="flex flex-col xl:flex-row gap-4">
      <!-- 主编辑区 -->
      <div class="flex-1 min-w-0 space-y-3">
        <!-- 标题 -->
        <input
          v-model="form.title"
          type="text"
          placeholder="输入文章标题..."
          :class="[
            'w-full px-5 py-4 text-xl font-bold rounded-3xl focus:outline-none placeholder-slate-400 transition-colors',
            isDarkTheme ? 'bg-white/5 border border-white/10 text-white' : 'bg-white/80 border border-white text-slate-900'
          ]"
        />
        
        <!-- 摘要 -->
        <textarea
          v-model="form.summary"
          placeholder="简短描述文章内容（可选，用于列表展示）..."
          rows="2"
          :class="[
            'w-full px-5 py-3 rounded-3xl focus:ring-2 focus:ring-purple-500 focus:border-transparent resize-none text-sm transition-colors',
            isDarkTheme ? 'bg-white/5 border border-white/10 text-slate-200 placeholder:text-slate-500' : 'bg-white/80 border border-white text-slate-600'
          ]"
        ></textarea>
        
        <!-- 编辑器/预览区域 -->
        <div :class="isDarkTheme ? 'bg-white/5 border-white/10' : 'bg-white border-slate-200'" class="rounded-3xl border overflow-hidden backdrop-blur-xl shadow-sm">
          <!-- 工具栏 -->
          <div v-if="viewMode !== 'preview'" :class="isDarkTheme ? 'bg-black/20 border-white/10' : 'bg-slate-50 border-slate-200'" class="px-3 py-2 border-b flex flex-wrap items-center gap-1">
            <div class="flex items-center gap-0.5 mr-2">
              <button @click="toolbarActions.heading1" :class="toolbarButtonClass" title="一级标题">H1</button>
              <button @click="toolbarActions.heading2" :class="toolbarButtonClass" title="二级标题">H2</button>
              <button @click="toolbarActions.heading3" :class="toolbarButtonClass" title="三级标题">H3</button>
            </div>
            
            <div class="w-px h-6 bg-slate-300 mr-2"></div>
            
            <button @click="toolbarActions.bold" :class="toolbarButtonClass" title="粗体"><span class="font-bold">B</span></button>
            <button @click="toolbarActions.italic" :class="toolbarButtonClass" title="斜体"><span class="italic">I</span></button>
            <button @click="toolbarActions.code" :class="toolbarButtonClass" title="行内代码"><span class="font-mono text-xs">&lt;/&gt;</span></button>
            <button @click="toolbarActions.codeBlock" :class="toolbarButtonClass" title="代码块">
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4"/>
              </svg>
            </button>
            
            <div class="w-px h-6 bg-slate-300 mx-1"></div>
            
            <button @click="toolbarActions.link" :class="toolbarButtonClass" title="链接">
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1"/>
              </svg>
            </button>
            <button @click="triggerImageUpload" :disabled="uploadingImage" :class="toolbarButtonClass" title="插入图片">
              <svg v-if="!uploadingImage" class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"/>
              </svg>
              <div v-else class="w-4 h-4 border-2 border-slate-400 border-t-transparent rounded-full animate-spin"></div>
            </button>
            <input ref="imageInputRef" type="file" accept="image/*" class="hidden" @change="handleImageUpload" />
            
            <div class="w-px h-6 bg-slate-300 mx-1"></div>
            
            <button @click="toolbarActions.quote" :class="toolbarButtonClass" title="引用">❝</button>
            <button @click="toolbarActions.list" :class="toolbarButtonClass" title="列表">☰</button>
            <button @click="toolbarActions.hr" :class="toolbarButtonClass" title="分割线">―</button>
            
          </div>
          
          <!-- 编辑器内容区 -->
          <div class="flex" :class="viewMode === 'split' ? 'divide-x divide-slate-200' : ''">
            <div v-if="viewMode !== 'preview'" :class="viewMode === 'split' ? 'w-1/2' : 'w-full'" class="relative">
            <textarea
                ref="editorRef"
              v-model="form.content"
              placeholder="在这里写下你的技术分享...

支持 Markdown 语法"
                :class="[
                  'w-full p-4 focus:outline-none resize-none font-mono text-sm leading-relaxed transition-colors',
                  viewMode === 'split' ? 'h-[500px]' : 'h-[550px]',
                  isDarkTheme ? 'bg-transparent text-slate-100 placeholder:text-slate-500' : 'bg-transparent text-slate-800 placeholder:text-slate-400'
                ]"
            ></textarea>
          </div>
          
            <div 
              v-if="viewMode !== 'edit'" 
              :class="[
                viewMode === 'split' ? 'w-1/2' : 'w-full',
                isDarkTheme ? 'bg-[#f8fafc]' : 'bg-white'
              ]"
              class="overflow-auto"
              :style="viewMode === 'split' ? 'height: 500px' : 'min-height: 550px'"
            >
              <div class="p-6 prose-preview" v-html="renderedContent"></div>
            </div>
          </div>
        </div>
      </div>
      
      <!-- 右侧设置面板 -->
      <div class="xl:w-72 flex-shrink-0 space-y-4">
        <!-- 封面图 -->
        <div :class="isDarkTheme ? 'bg-white/5 border-white/10' : 'bg-white/90 border-white'" class="rounded-3xl border p-4 backdrop-blur-xl">
          <h3 :class="isDarkTheme ? 'text-slate-100' : 'text-slate-800'" class="font-bold mb-3 flex items-center gap-2 text-sm">
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
            <div :class="isDarkTheme ? 'border-white/10 hover:border-violet-400 hover:bg-white/5' : 'border-slate-200 hover:border-purple-400 hover:bg-purple-50'" class="border-2 border-dashed rounded-2xl p-4 text-center cursor-pointer transition-all">
              <span class="text-2xl block mb-1">📷</span>
              <span :class="isDarkTheme ? 'text-slate-400' : 'text-slate-500'" class="text-xs">点击上传</span>
            </div>
            <input type="file" accept="image/*" class="hidden" @change="handleCoverUpload" />
          </label>
        </div>
        
        <!-- 标签 -->
        <div :class="isDarkTheme ? 'bg-white/5 border-white/10' : 'bg-white/90 border-white'" class="rounded-3xl border p-4 backdrop-blur-xl">
          <h3 :class="isDarkTheme ? 'text-slate-100' : 'text-slate-800'" class="font-bold mb-3 flex items-center justify-between text-sm">
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
                  : (isDarkTheme ? 'bg-white/5 border-white/10 hover:border-violet-300' : 'bg-white border-slate-200 hover:border-purple-300')
              ]"
              :style="form.tag_ids.includes(tag.id) ? { backgroundColor: tag.color } : { color: tag.color }"
            >
              {{ tag.name }}
            </button>
            
            <div v-if="allTags.length === 0" :class="isDarkTheme ? 'text-slate-500' : 'text-slate-400'" class="text-xs py-2">暂无标签</div>
          </div>
        </div>
        
        <!-- 发布设置 -->
        <div :class="isDarkTheme ? 'bg-white/5 border-white/10' : 'bg-white/90 border-white'" class="rounded-3xl border p-4 backdrop-blur-xl">
          <h3 :class="isDarkTheme ? 'text-slate-100' : 'text-slate-800'" class="font-bold mb-3 flex items-center gap-2 text-sm">
            <span>⚙️</span> 发布设置
          </h3>
          
          <div class="space-y-2">
            <label :class="isDarkTheme ? 'hover:bg-white/5' : 'hover:bg-slate-50'" class="flex items-center gap-2 cursor-pointer p-1.5 rounded-lg">
              <input v-model="form.is_featured" type="checkbox" class="w-4 h-4 rounded border-slate-300 text-purple-600 focus:ring-purple-500" />
              <span :class="isDarkTheme ? 'text-slate-200' : 'text-slate-700'" class="font-medium text-sm">⭐ 设为精选</span>
            </label>
            
            <label :class="isDarkTheme ? 'hover:bg-white/5' : 'hover:bg-slate-50'" class="flex items-center gap-2 cursor-pointer p-1.5 rounded-lg">
              <input v-model="form.is_published" type="checkbox" class="w-4 h-4 rounded border-slate-300 text-purple-600 focus:ring-purple-500" />
              <span :class="isDarkTheme ? 'text-slate-200' : 'text-slate-700'" class="font-medium text-sm">📢 公开发布</span>
            </label>
          </div>
        </div>
        
        <!-- Markdown 速查 -->
        <div :class="isDarkTheme ? 'bg-white/5 border-white/10' : 'bg-slate-50 border-slate-200'" class="rounded-3xl border p-4 backdrop-blur-xl">
          <h3 :class="isDarkTheme ? 'text-slate-100' : 'text-slate-700'" class="font-bold mb-2 flex items-center gap-2 text-sm">
            <span>⌨️</span> Markdown 速查
          </h3>
          <div :class="isDarkTheme ? 'text-slate-400' : 'text-slate-500'" class="text-xs space-y-1 font-mono">
            <div># 标题 ## 二级</div>
            <div>**粗体** *斜体*</div>
            <div>`代码` ```代码块```</div>
            <div>[链接](url) ![图](url)</div>
            <div>- 列表 > 引用</div>
          </div>
        </div>
      </div>
    </div>
  </div>
    
    <!-- 新建标签弹窗 -->
    <Teleport to="body">
      <Transition name="modal">
        <div v-if="showTagModal" class="fixed inset-0 z-50 flex items-center justify-center p-4">
          <div class="absolute inset-0 bg-black/50" @click="showTagModal = false"></div>
          <div class="relative bg-white rounded-3xl p-6 w-full max-w-md shadow-2xl">
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

.toolbar-btn-dark {
  @apply text-slate-300 hover:bg-white/10 hover:text-white;
}

.prose-preview {
  font-size: 1rem;
  line-height: 1.75;
  color: #374151;
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
