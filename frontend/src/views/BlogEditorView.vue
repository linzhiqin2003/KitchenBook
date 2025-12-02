<script setup>
import { ref, onMounted, computed, watch, nextTick } from 'vue'
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
const previewMode = ref(false)

// AI 助手相关
const aiEnabled = ref(false)
const aiLoading = ref(false)
const aiPanel = ref(false)
const selectedText = ref('')

// 编辑器引用
const editorRef = ref(null)

// 图片上传
const uploadingImage = ref(false)

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

// 删除封面图
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

// 创建新标签
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

// ============== 编辑器工具栏功能 ==============

// 插入文本到光标位置
const insertText = (before, after = '', placeholder = '') => {
  const textarea = editorRef.value
  if (!textarea) return
  
  const start = textarea.selectionStart
  const end = textarea.selectionEnd
  const text = form.value.content
  const selectedText = text.substring(start, end) || placeholder
  
  const newText = text.substring(0, start) + before + selectedText + after + text.substring(end)
  form.value.content = newText
  
  // 设置光标位置
  nextTick(() => {
    textarea.focus()
    const newPos = start + before.length + selectedText.length
    textarea.setSelectionRange(newPos, newPos)
  })
}

// 工具栏按钮
const toolbarActions = {
  bold: () => insertText('**', '**', '粗体文字'),
  italic: () => insertText('*', '*', '斜体文字'),
  heading1: () => insertText('# ', '\n', '一级标题'),
  heading2: () => insertText('## ', '\n', '二级标题'),
  heading3: () => insertText('### ', '\n', '三级标题'),
  quote: () => insertText('> ', '\n', '引用内容'),
  code: () => insertText('`', '`', 'code'),
  codeBlock: () => insertText('```\n', '\n```', '代码内容'),
  link: () => insertText('[', '](url)', '链接文字'),
  list: () => insertText('- ', '\n', '列表项'),
  orderedList: () => insertText('1. ', '\n', '列表项'),
  hr: () => insertText('\n---\n', '', ''),
}

// 上传内容图片
const imageInputRef = ref(null)

const triggerImageUpload = () => {
  imageInputRef.value?.click()
}

const handleImageUpload = async (event) => {
  const file = event.target.files[0]
  if (!file) return
  
  // 验证文件
  const allowedTypes = ['image/jpeg', 'image/png', 'image/gif', 'image/webp']
  if (!allowedTypes.includes(file.type)) {
    alert('不支持的图片格式，请使用 JPG/PNG/GIF/WebP')
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
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
    
    if (response.data.success) {
      // 插入图片 Markdown
      insertText(`\n![image](${response.data.url})\n`, '', '')
    }
  } catch (error) {
    console.error('Failed to upload image', error)
    alert('图片上传失败：' + (error.response?.data?.error || '未知错误'))
  } finally {
    uploadingImage.value = false
    event.target.value = '' // 清空 input
  }
}

// ============== AI 辅助功能 ==============

const aiActions = [
  { id: 'continue', label: '✨ 续写', desc: '继续写作' },
  { id: 'polish', label: '💎 润色', desc: '优化文字' },
  { id: 'expand', label: '📝 扩展', desc: '丰富内容' },
  { id: 'summarize', label: '📋 摘要', desc: '生成摘要' },
  { id: 'code_explain', label: '💻 解释代码', desc: '添加注释' },
]

const callAiAssist = async (action) => {
  const textarea = editorRef.value
  let content = ''
  
  // 获取选中文本或全部内容
  if (textarea) {
    const start = textarea.selectionStart
    const end = textarea.selectionEnd
    if (start !== end) {
      content = form.value.content.substring(start, end)
    } else {
      // 没有选中时，使用最后 500 字符作为上下文
      content = form.value.content.slice(-500)
    }
  }
  
  if (!content.trim()) {
    alert('请先输入一些内容')
    return
  }
  
  try {
    aiLoading.value = true
    
    const response = await axios.post(`${API_BASE_URL}/api/blog/ai-assist/`, {
      action,
      content,
      context: form.value.title ? `标题：${form.value.title}` : ''
    })
    
    if (response.data.success) {
      const aiContent = response.data.content
      
      if (action === 'summarize') {
        // 摘要直接填入摘要框
        form.value.summary = aiContent
        alert('摘要已生成并填入摘要框')
      } else if (action === 'polish' || action === 'code_explain') {
        // 润色/解释替换选中内容
        if (textarea) {
          const start = textarea.selectionStart
          const end = textarea.selectionEnd
          if (start !== end) {
            const text = form.value.content
            form.value.content = text.substring(0, start) + aiContent + text.substring(end)
          } else {
            form.value.content = aiContent
          }
        }
      } else {
        // 续写/扩展追加到末尾
        form.value.content += '\n\n' + aiContent
      }
    }
  } catch (error) {
    console.error('AI assist failed', error)
    alert('AI 助手出错：' + (error.response?.data?.error || '未知错误'))
  } finally {
    aiLoading.value = false
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

// 简单的 Markdown 预览
const parseMarkdown = (markdown) => {
  if (!markdown) return '<p class="text-slate-400 italic">开始输入内容...</p>'
  
  let html = markdown
  
  // 图片
  html = html.replace(/!\[([^\]]*)\]\(([^)]+)\)/g, '<img src="$2" alt="$1" class="max-w-full rounded-lg my-4" />')
  
  // 代码块
  html = html.replace(/```(\w+)?\n([\s\S]*?)```/g, (match, lang, code) => {
    return `<pre class="bg-slate-800 text-slate-200 p-4 rounded-lg my-4 overflow-x-auto"><code>${code.trim().replace(/</g, '&lt;').replace(/>/g, '&gt;')}</code></pre>`
  })
  
  // 行内代码
  html = html.replace(/`([^`]+)`/g, '<code class="bg-slate-100 px-1.5 py-0.5 rounded text-purple-600">$1</code>')
  
  // 标题
  html = html.replace(/^### (.+)$/gm, '<h3 class="text-lg font-semibold mt-4 mb-2">$1</h3>')
  html = html.replace(/^## (.+)$/gm, '<h2 class="text-xl font-bold mt-6 mb-3">$1</h2>')
  html = html.replace(/^# (.+)$/gm, '<h1 class="text-2xl font-bold mt-8 mb-4 pb-2 border-b">$1</h1>')
  
  // 粗体和斜体
  html = html.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
  html = html.replace(/\*(.+?)\*/g, '<em>$1</em>')
  
  // 链接
  html = html.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" class="text-purple-600 underline" target="_blank">$1</a>')
  
  // 列表
  html = html.replace(/^\s*[-*]\s+(.+)$/gm, '<li class="ml-4">• $1</li>')
  
  // 引用
  html = html.replace(/^>\s*(.+)$/gm, '<blockquote class="border-l-4 border-purple-400 pl-4 my-4 text-slate-600 italic">$1</blockquote>')
  
  // 水平线
  html = html.replace(/^---$/gm, '<hr class="my-6 border-slate-200" />')
  
  // 段落
  html = html.split('\n\n').map(block => {
    if (!block.trim()) return ''
    if (block.match(/^<[a-z]/i)) return block
    return `<p class="my-3">${block.replace(/\n/g, '<br>')}</p>`
  }).join('')
  
  return html
}

const renderedContent = computed(() => parseMarkdown(form.value.content))

// 预设颜色
const presetColors = [
  '#ef4444', '#f97316', '#eab308', '#22c55e', '#10b981',
  '#14b8a6', '#06b6d4', '#3b82f6', '#6366f1', '#8b5cf6',
  '#a855f7', '#d946ef', '#ec4899', '#f43f5e'
]
</script>

<template>
  <div class="max-w-6xl mx-auto">
    <!-- 顶部工具栏 -->
    <div class="flex items-center justify-between mb-6">
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
        <h1 class="text-2xl font-bold text-slate-800">
          {{ isEditMode ? '编辑文章' : '写新文章' }}
        </h1>
      </div>
      
      <div class="flex items-center gap-3">
        <!-- 预览切换 -->
        <button
          @click="previewMode = !previewMode"
          :class="[
            'px-4 py-2 rounded-lg text-sm font-medium transition-all',
            previewMode 
              ? 'bg-purple-100 text-purple-700' 
              : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
          ]"
        >
          {{ previewMode ? '📝 编辑' : '👁️ 预览' }}
        </button>
        
        <!-- 保存草稿 -->
        <button
          @click="savePost(false)"
          :disabled="saving"
          class="px-4 py-2 bg-slate-200 text-slate-700 rounded-lg text-sm font-medium hover:bg-slate-300 transition-colors disabled:opacity-50"
        >
          {{ saving ? '保存中...' : '保存草稿' }}
        </button>
        
        <!-- 发布 -->
        <button
          @click="savePost(true)"
          :disabled="saving"
          class="px-6 py-2 bg-purple-600 text-white rounded-lg text-sm font-medium hover:bg-purple-700 transition-colors shadow-lg shadow-purple-500/30 disabled:opacity-50"
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
    <div v-else class="grid grid-cols-1 lg:grid-cols-3 gap-6">
      <!-- 主编辑区 -->
      <div class="lg:col-span-2 space-y-4">
        <!-- 标题 -->
        <input
          v-model="form.title"
          type="text"
          placeholder="输入文章标题..."
          class="w-full px-4 py-3 text-2xl font-bold border-0 border-b-2 border-slate-200 focus:border-purple-500 focus:outline-none bg-transparent placeholder-slate-300"
        />
        
        <!-- 摘要 -->
        <textarea
          v-model="form.summary"
          placeholder="简短描述文章内容（可选，用于列表展示）..."
          rows="2"
          class="w-full px-4 py-3 border border-slate-200 rounded-xl focus:ring-2 focus:ring-purple-500 focus:border-transparent resize-none text-slate-600"
        ></textarea>
        
        <!-- 内容编辑/预览 -->
        <div class="bg-white rounded-2xl border border-slate-200 overflow-hidden min-h-[500px]">
          <!-- 工具栏 -->
          <div v-if="!previewMode" class="bg-slate-50 px-3 py-2 border-b border-slate-200 flex flex-wrap items-center gap-1">
            <!-- 格式化按钮 -->
            <div class="flex items-center gap-0.5 mr-2">
              <button @click="toolbarActions.heading1" class="toolbar-btn" title="一级标题">H1</button>
              <button @click="toolbarActions.heading2" class="toolbar-btn" title="二级标题">H2</button>
              <button @click="toolbarActions.heading3" class="toolbar-btn" title="三级标题">H3</button>
            </div>
            
            <div class="w-px h-6 bg-slate-300 mr-2"></div>
            
            <button @click="toolbarActions.bold" class="toolbar-btn" title="粗体 (Ctrl+B)">
              <span class="font-bold">B</span>
            </button>
            <button @click="toolbarActions.italic" class="toolbar-btn" title="斜体 (Ctrl+I)">
              <span class="italic">I</span>
            </button>
            <button @click="toolbarActions.code" class="toolbar-btn font-mono" title="行内代码">&lt;/&gt;</button>
            <button @click="toolbarActions.codeBlock" class="toolbar-btn" title="代码块">
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4"/>
              </svg>
            </button>
            
            <div class="w-px h-6 bg-slate-300 mx-2"></div>
            
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
            
            <div class="w-px h-6 bg-slate-300 mx-2"></div>
            
            <button @click="toolbarActions.quote" class="toolbar-btn" title="引用">
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z"/>
              </svg>
            </button>
            <button @click="toolbarActions.list" class="toolbar-btn" title="无序列表">
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16"/>
              </svg>
            </button>
            <button @click="toolbarActions.hr" class="toolbar-btn" title="分割线">─</button>
            
            <!-- AI 助手开关 -->
            <div class="flex-grow"></div>
            <label class="flex items-center gap-2 cursor-pointer px-3 py-1.5 rounded-lg transition-colors" :class="aiEnabled ? 'bg-purple-100' : 'hover:bg-slate-100'">
              <span class="text-sm" :class="aiEnabled ? 'text-purple-700' : 'text-slate-500'">🤖 AI 助手</span>
              <div 
                class="relative w-10 h-5 rounded-full transition-colors"
                :class="aiEnabled ? 'bg-purple-500' : 'bg-slate-300'"
                @click="aiEnabled = !aiEnabled"
              >
                <div 
                  class="absolute top-0.5 w-4 h-4 bg-white rounded-full shadow transition-transform"
                  :class="aiEnabled ? 'translate-x-5' : 'translate-x-0.5'"
                ></div>
              </div>
            </label>
          </div>
          
          <!-- AI 助手面板 -->
          <div v-if="aiEnabled && !previewMode" class="bg-gradient-to-r from-purple-50 to-indigo-50 px-3 py-2 border-b border-purple-100 flex items-center gap-2 flex-wrap">
            <span class="text-xs text-purple-600 font-medium mr-2">AI 辅助：</span>
            <button
              v-for="action in aiActions"
              :key="action.id"
              @click="callAiAssist(action.id)"
              :disabled="aiLoading"
              class="px-3 py-1 text-xs rounded-full bg-white border border-purple-200 text-purple-700 hover:bg-purple-100 hover:border-purple-300 transition-all disabled:opacity-50 disabled:cursor-wait"
              :title="action.desc"
            >
              {{ action.label }}
            </button>
            <div v-if="aiLoading" class="flex items-center gap-2 ml-2 text-xs text-purple-600">
              <div class="w-3 h-3 border-2 border-purple-500 border-t-transparent rounded-full animate-spin"></div>
              AI 思考中...
            </div>
            <span class="text-xs text-purple-400 ml-auto">选中文字后点击按钮，或自动使用最近内容</span>
          </div>
          
          <!-- 编辑模式 -->
          <div v-if="!previewMode" class="h-full">
            <textarea
              ref="editorRef"
              v-model="form.content"
              placeholder="在这里写下你的技术分享...

支持 Markdown 语法：
# 一级标题
## 二级标题
**粗体** *斜体*
- 列表项
> 引用
`行内代码`
```python
代码块
```
![图片](url)
[链接](url)
"
              class="w-full h-[450px] p-4 focus:outline-none resize-none font-mono text-sm leading-relaxed"
            ></textarea>
          </div>
          
          <!-- 预览模式 -->
          <div v-else class="p-6 min-h-[500px]">
            <div class="prose-preview" v-html="renderedContent"></div>
          </div>
        </div>
      </div>
      
      <!-- 右侧设置面板 -->
      <div class="space-y-4">
        <!-- 封面图 -->
        <div class="bg-white rounded-2xl border border-slate-200 p-4">
          <h3 class="font-bold text-slate-800 mb-3 flex items-center gap-2">
            <span>🖼️</span> 封面图片
          </h3>
          
          <div v-if="coverPreview" class="relative mb-3">
            <img :src="coverPreview" class="w-full aspect-video object-cover rounded-lg" />
            <button
              @click="removeCover"
              class="absolute top-2 right-2 w-8 h-8 bg-red-500 text-white rounded-full flex items-center justify-center hover:bg-red-600 transition-colors"
            >
              ×
            </button>
          </div>
          
          <label class="block">
            <div class="border-2 border-dashed border-slate-200 rounded-xl p-6 text-center cursor-pointer hover:border-purple-400 hover:bg-purple-50 transition-all">
              <span class="text-3xl block mb-2">📷</span>
              <span class="text-sm text-slate-500">点击上传封面图片</span>
            </div>
            <input type="file" accept="image/*" class="hidden" @change="handleCoverUpload" />
          </label>
        </div>
        
        <!-- 标签 -->
        <div class="bg-white rounded-2xl border border-slate-200 p-4">
          <h3 class="font-bold text-slate-800 mb-3 flex items-center justify-between">
            <span class="flex items-center gap-2">
              <span>🏷️</span> 标签
            </span>
            <button
              @click="showTagModal = true"
              class="text-sm text-purple-600 hover:text-purple-800"
            >
              + 新建
            </button>
          </h3>
          
          <div class="flex flex-wrap gap-2">
            <button
              v-for="tag in allTags"
              :key="tag.id"
              @click="toggleTag(tag.id)"
              :class="[
                'px-3 py-1.5 rounded-full text-sm font-medium transition-all border-2',
                form.tag_ids.includes(tag.id)
                  ? 'text-white border-transparent'
                  : 'bg-white border-slate-200 hover:border-purple-300'
              ]"
              :style="form.tag_ids.includes(tag.id) ? { backgroundColor: tag.color } : { color: tag.color }"
            >
              {{ tag.name }}
            </button>
            
            <div v-if="allTags.length === 0" class="text-sm text-slate-400 py-2">
              暂无标签，点击上方新建
            </div>
          </div>
        </div>
        
        <!-- 发布设置 -->
        <div class="bg-white rounded-2xl border border-slate-200 p-4">
          <h3 class="font-bold text-slate-800 mb-3 flex items-center gap-2">
            <span>⚙️</span> 发布设置
          </h3>
          
          <div class="space-y-3">
            <label class="flex items-center gap-3 cursor-pointer p-2 rounded-lg hover:bg-slate-50">
              <input
                v-model="form.is_featured"
                type="checkbox"
                class="w-5 h-5 rounded border-slate-300 text-purple-600 focus:ring-purple-500"
              />
              <div>
                <div class="font-medium text-slate-700">⭐ 设为精选</div>
                <div class="text-xs text-slate-400">在博客首页优先展示</div>
              </div>
            </label>
            
            <label class="flex items-center gap-3 cursor-pointer p-2 rounded-lg hover:bg-slate-50">
              <input
                v-model="form.is_published"
                type="checkbox"
                class="w-5 h-5 rounded border-slate-300 text-purple-600 focus:ring-purple-500"
              />
              <div>
                <div class="font-medium text-slate-700">📢 公开发布</div>
                <div class="text-xs text-slate-400">取消勾选则保存为草稿</div>
              </div>
            </label>
          </div>
        </div>
        
        <!-- 写作提示 -->
        <div class="bg-gradient-to-br from-purple-50 to-indigo-50 rounded-2xl border border-purple-100 p-4">
          <h3 class="font-bold text-purple-800 mb-2 flex items-center gap-2">
            <span>💡</span> 写作提示
          </h3>
          <ul class="text-sm text-purple-700 space-y-1.5">
            <li>• 标题要简洁明了，吸引读者</li>
            <li>• 摘要用 1-2 句话概括核心内容</li>
            <li>• 善用代码块展示代码示例</li>
            <li>• 可插入图片丰富文章内容</li>
            <li v-if="aiEnabled" class="text-purple-600 font-medium">• 🤖 AI 已开启，选中文字可获得辅助</li>
          </ul>
        </div>
      </div>
    </div>
    
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
                      'w-8 h-8 rounded-full transition-transform',
                      newTagColor === color ? 'ring-2 ring-offset-2 ring-slate-400 scale-110' : 'hover:scale-110'
                    ]"
                    :style="{ backgroundColor: color }"
                  ></button>
                </div>
                <div class="flex items-center gap-2">
                  <input
                    v-model="newTagColor"
                    type="color"
                    class="w-10 h-10 rounded cursor-pointer"
                  />
                  <input
                    v-model="newTagColor"
                    type="text"
                    class="flex-1 px-3 py-2 border border-slate-200 rounded-lg text-sm font-mono"
                  />
                </div>
              </div>
              
              <!-- 预览 -->
              <div class="p-3 bg-slate-50 rounded-lg">
                <span class="text-sm text-slate-500 mr-2">预览：</span>
                <span
                  class="px-3 py-1 rounded-full text-white text-sm font-medium"
                  :style="{ backgroundColor: newTagColor }"
                >
                  {{ newTagName || '标签名称' }}
                </span>
              </div>
            </div>
            
            <div class="flex justify-end gap-3 mt-6">
              <button
                @click="showTagModal = false"
                class="px-4 py-2 text-slate-600 hover:text-slate-800"
              >
                取消
              </button>
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
