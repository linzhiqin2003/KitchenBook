<script setup>
import { ref, onMounted, computed, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import axios from 'axios'
import API_BASE_URL from '../config/api'

const route = useRoute()
const router = useRouter()
const post = ref(null)
const loading = ref(true)
const error = ref(null)

// 简单的 Markdown 解析器
const parseMarkdown = (markdown) => {
  if (!markdown) return ''
  
  let html = markdown
  
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
  html = html.replace(/^### (.+)$/gm, '<h3 class="md-h3">$1</h3>')
  html = html.replace(/^## (.+)$/gm, '<h2 class="md-h2">$1</h2>')
  html = html.replace(/^# (.+)$/gm, '<h1 class="md-h1">$1</h1>')
  
  // 粗体和斜体
  html = html.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
  html = html.replace(/\*(.+?)\*/g, '<em>$1</em>')
  
  // 链接
  html = html.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" class="md-link" target="_blank" rel="noopener">$1</a>')
  
  // 图片
  html = html.replace(/!\[([^\]]*)\]\(([^)]+)\)/g, '<img src="$2" alt="$1" class="md-img" loading="lazy" />')
  
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
    if (block.match(/^<(h[1-6]|ul|ol|pre|blockquote|hr)/) || block.includes('__CODE_BLOCK_')) {
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
  
  return html
}

// HTML 转义
const escapeHtml = (text) => {
  const div = document.createElement('div')
  div.textContent = text
  return div.innerHTML
}

// 获取文章详情
const fetchPost = async () => {
  try {
    loading.value = true
    error.value = null
    const slug = route.params.slug
    
    // 通过 slug 直接获取文章
    const response = await axios.get(`${API_BASE_URL}/api/blog/posts/by-slug/${slug}/`)
    post.value = response.data
  } catch (err) {
    console.error('Failed to fetch post', err)
    if (err.response?.status === 404) {
      error.value = '文章不存在'
    } else {
      error.value = '加载失败'
    }
  } finally {
    loading.value = false
  }
}

onMounted(fetchPost)
watch(() => route.params.slug, fetchPost)

// 格式化日期
const formatDate = (dateStr) => {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  return date.toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: 'long',
    day: 'numeric'
  })
}

// 返回博客列表
const goBack = () => {
  router.push('/blog')
}

// 解析后的内容
const parsedContent = computed(() => parseMarkdown(post.value?.content))
</script>

<template>
  <div class="min-h-screen">
    <!-- 加载状态 -->
    <div v-if="loading" class="flex justify-center items-center py-40">
      <div class="w-16 h-16 border-4 border-purple-200 border-t-purple-600 rounded-full animate-spin"></div>
    </div>
    
    <!-- 错误状态 -->
    <div v-else-if="error" class="text-center py-20">
      <div class="text-6xl mb-4">😢</div>
      <h2 class="text-2xl font-bold text-slate-700 mb-2">{{ error }}</h2>
      <button @click="goBack" class="mt-4 px-6 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors">
        返回博客列表
      </button>
    </div>
    
    <!-- 文章内容 -->
    <article v-else-if="post" class="pb-16">
      <!-- 文章头部 -->
      <header class="relative overflow-hidden bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 text-white -mx-4 md:-mx-6 lg:-mx-8 -mt-4 md:-mt-6 lg:-mt-8 px-4 md:px-6 lg:px-8 py-16 md:py-24">
        <!-- 装饰背景 -->
        <div class="absolute inset-0 overflow-hidden">
          <div class="absolute -top-40 -right-40 w-80 h-80 bg-purple-500/20 rounded-full blur-3xl"></div>
          <div class="absolute -bottom-40 -left-40 w-80 h-80 bg-blue-500/20 rounded-full blur-3xl"></div>
          <div class="absolute inset-0 bg-[linear-gradient(rgba(255,255,255,0.02)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,0.02)_1px,transparent_1px)] bg-[size:60px_60px]"></div>
        </div>
        
        <div class="relative container mx-auto max-w-4xl">
          <!-- 返回按钮 -->
          <button 
            @click="goBack"
            class="inline-flex items-center gap-2 text-slate-300 hover:text-white mb-8 transition-colors"
          >
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
            </svg>
            返回博客列表
          </button>
          
          <!-- 标签 -->
          <div class="flex flex-wrap gap-2 mb-4">
            <span
              v-for="tag in post.tags"
              :key="tag.id"
              class="px-3 py-1 rounded-full text-sm font-medium"
              :style="{ backgroundColor: tag.color + '30', color: 'white', borderColor: tag.color }"
            >
              {{ tag.name }}
            </span>
          </div>
          
          <!-- 标题 -->
          <h1 class="text-3xl md:text-5xl font-bold mb-6 leading-tight">{{ post.title }}</h1>
          
          <!-- 摘要 -->
          <p v-if="post.summary" class="text-lg text-slate-300 mb-8 max-w-3xl">{{ post.summary }}</p>
          
          <!-- 元信息 -->
          <div class="flex flex-wrap items-center gap-6 text-sm text-slate-400">
            <div class="flex items-center gap-2">
              <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
              </svg>
              {{ formatDate(post.published_at || post.created_at) }}
            </div>
            <div class="flex items-center gap-2">
              <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              {{ post.reading_time }} 分钟阅读
            </div>
            <div class="flex items-center gap-2">
              <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
              </svg>
              {{ post.view_count }} 次阅读
            </div>
          </div>
        </div>
      </header>
      
      <!-- 封面图 -->
      <div v-if="post.cover_image" class="container mx-auto max-w-4xl -mt-8 relative z-10 px-4">
        <img 
          :src="post.cover_image" 
          :alt="post.title"
          class="w-full rounded-2xl shadow-2xl"
        />
      </div>
      
      <!-- 文章正文 -->
      <div class="container mx-auto max-w-4xl px-4 mt-12">
        <div class="bg-white rounded-2xl shadow-sm border border-slate-100 p-6 md:p-10">
          <div class="prose-content" v-html="parsedContent"></div>
        </div>
        
        <!-- 文章底部 -->
        <div class="mt-12 p-6 bg-gradient-to-r from-purple-50 to-indigo-50 rounded-2xl border border-purple-100">
          <div class="flex flex-col md:flex-row items-center justify-between gap-4">
            <div>
              <h3 class="text-lg font-bold text-slate-800 mb-1">感谢阅读！</h3>
              <p class="text-slate-600 text-sm">如果这篇文章对你有帮助，欢迎分享给更多人</p>
            </div>
            <button 
              @click="goBack"
              class="px-6 py-3 bg-purple-600 text-white rounded-xl hover:bg-purple-700 transition-colors shadow-lg shadow-purple-500/30"
            >
              查看更多文章
            </button>
          </div>
        </div>
      </div>
    </article>
  </div>
</template>

<style scoped>
/* Markdown 内容样式 */
.prose-content {
  font-size: 1.125rem;
  line-height: 1.8;
  color: #374151;
}

.prose-content :deep(.md-h1) {
  font-size: 2rem;
  font-weight: 700;
  color: #111827;
  margin: 2rem 0 1rem;
  padding-bottom: 0.5rem;
  border-bottom: 2px solid #e5e7eb;
}

.prose-content :deep(.md-h2) {
  font-size: 1.5rem;
  font-weight: 700;
  color: #1f2937;
  margin: 1.75rem 0 0.75rem;
}

.prose-content :deep(.md-h3) {
  font-size: 1.25rem;
  font-weight: 600;
  color: #374151;
  margin: 1.5rem 0 0.5rem;
}

.prose-content :deep(.md-p) {
  margin: 1rem 0;
}

.prose-content :deep(.md-link) {
  color: #7c3aed;
  text-decoration: underline;
  text-underline-offset: 2px;
}

.prose-content :deep(.md-link:hover) {
  color: #5b21b6;
}

.prose-content :deep(.md-img) {
  max-width: 100%;
  border-radius: 0.75rem;
  margin: 1.5rem 0;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
}

.prose-content :deep(.md-ul),
.prose-content :deep(.md-ol) {
  margin: 1rem 0;
  padding-left: 1.5rem;
}

.prose-content :deep(.md-li),
.prose-content :deep(.md-oli) {
  margin: 0.5rem 0;
}

.prose-content :deep(.md-ul) {
  list-style-type: disc;
}

.prose-content :deep(.md-ol) {
  list-style-type: decimal;
}

.prose-content :deep(.md-quote) {
  border-left: 4px solid #a78bfa;
  padding: 1rem 1.5rem;
  margin: 1.5rem 0;
  background: linear-gradient(to right, #f5f3ff, transparent);
  color: #4b5563;
  font-style: italic;
  border-radius: 0 0.5rem 0.5rem 0;
}

.prose-content :deep(.md-hr) {
  border: none;
  border-top: 2px solid #e5e7eb;
  margin: 2rem 0;
}

.prose-content :deep(.inline-code) {
  background: #f3f4f6;
  padding: 0.2rem 0.4rem;
  border-radius: 0.25rem;
  font-family: 'Fira Code', 'Monaco', monospace;
  font-size: 0.9em;
  color: #7c3aed;
}

.prose-content :deep(.code-block) {
  background: #1e1e2e;
  border-radius: 0.75rem;
  padding: 1.25rem;
  margin: 1.5rem 0;
  overflow-x: auto;
  position: relative;
}

.prose-content :deep(.code-block)::before {
  content: attr(data-lang);
  position: absolute;
  top: 0.5rem;
  right: 0.75rem;
  font-size: 0.75rem;
  color: #6b7280;
  text-transform: uppercase;
}

.prose-content :deep(.code-block code) {
  font-family: 'Fira Code', 'Monaco', monospace;
  font-size: 0.9rem;
  color: #e5e7eb;
  line-height: 1.7;
  white-space: pre-wrap;
  word-break: break-word;
  display: block;
}

.prose-content :deep(strong) {
  color: #111827;
  font-weight: 600;
}

.prose-content :deep(em) {
  font-style: italic;
}
</style>

