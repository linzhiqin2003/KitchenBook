<script setup>
import { ref, onMounted, computed, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import axios from 'axios'
import { marked } from 'marked'
import hljs from 'highlight.js'
import API_BASE_URL from '../config/api'

const route = useRoute()
const router = useRouter()
const post = ref(null)
const loading = ref(true)
const error = ref(null)

// 读取博客列表页的主题设置
const isDarkTheme = ref(localStorage.getItem('blog_theme') !== 'light')

// 配置 marked
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

// 代码高亮函数
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

// Markdown 解析函数 - 使用后处理方式添加样式类
const parseMarkdown = (markdown) => {
  if (!markdown) return ''
  
  // 预处理：转义未知的 HTML 标签
  let processedMarkdown = markdown.replace(/<([a-zA-Z][a-zA-Z0-9]*)(?:\s[^>]*)?>(?![\s\S]*?<\/\1>)/g, (match, tagName) => {
    if (allowedTags.includes(tagName.toLowerCase())) {
      return match
    }
    return match.replace(/</g, '&lt;').replace(/>/g, '&gt;')
  })
  
  let html = marked.parse(processedMarkdown)
  
  // 后处理：添加样式类
  html = html.replace(/<h1([^>]*)>/g, '<h1$1 class="md-h1">')
  html = html.replace(/<h2([^>]*)>/g, '<h2$1 class="md-h2">')
  html = html.replace(/<h3([^>]*)>/g, '<h3$1 class="md-h3">')
  html = html.replace(/<h4([^>]*)>/g, '<h4$1 class="md-h4">')
  html = html.replace(/<h5([^>]*)>/g, '<h5$1 class="md-h5">')
  html = html.replace(/<h6([^>]*)>/g, '<h6$1 class="md-h6">')
  html = html.replace(/<p>/g, '<p class="md-p">')
  html = html.replace(/<ul>/g, '<ul class="md-ul">')
  html = html.replace(/<ol>/g, '<ol class="md-ol">')
  html = html.replace(/<li>/g, '<li class="md-li">')
  html = html.replace(/<blockquote>/g, '<blockquote class="md-quote">')
  html = html.replace(/<a /g, '<a class="md-link" target="_blank" rel="noopener noreferrer" ')
  html = html.replace(/<img /g, '<img class="md-img" loading="lazy" ')
  html = html.replace(/<hr>/g, '<hr class="md-hr">')
  html = html.replace(/<table>/g, '<div class="md-table-wrapper"><table class="md-table">')
  html = html.replace(/<\/table>/g, '</table></div>')
  
  // 代码块高亮
  html = html.replace(/<pre><code class="language-(\w+)">([\s\S]*?)<\/code><\/pre>/g, (match, lang, code) => {
    const decoded = code.replace(/&lt;/g, '<').replace(/&gt;/g, '>').replace(/&amp;/g, '&')
    const highlighted = highlightCode(decoded, lang)
    return `<pre class="code-block" data-lang="${lang}"><code class="hljs language-${lang}">${highlighted}</code></pre>`
  })
  
  // 无语言代码块
  html = html.replace(/<pre><code>([\s\S]*?)<\/code><\/pre>/g, (match, code) => {
    const decoded = code.replace(/&lt;/g, '<').replace(/&gt;/g, '>').replace(/&amp;/g, '&')
    const highlighted = highlightCode(decoded, '')
    return `<pre class="code-block"><code class="hljs">${highlighted}</code></pre>`
  })
  
  // 行内代码
  html = html.replace(/<code>/g, '<code class="inline-code">')
  
  return html
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
  <div :class="['min-h-screen font-sans transition-colors duration-500', isDarkTheme ? 'bg-[#0a0a0f] text-slate-100' : 'bg-[#faf8f0] text-slate-800 paper-texture']">
    <!-- 独立导航栏 -->
    <header :class="['fixed top-0 left-0 right-0 z-50 backdrop-blur-xl border-b transition-colors duration-500', isDarkTheme ? 'bg-[#0a0a0f]/80 border-white/5' : 'bg-[#faf8f0]/90 border-amber-200/30']">
      <div class="container mx-auto px-4 md:px-6">
        <div class="flex items-center justify-between h-16 md:h-20">
          <!-- Logo -->
          <router-link to="/blog" class="flex items-center gap-3 group">
            <div :class="['w-10 h-10 rounded-xl flex items-center justify-center transition-shadow', isDarkTheme ? 'bg-white/10 group-hover:bg-white/15' : 'bg-slate-100 group-hover:bg-slate-200']">
              <svg class="w-5 h-5" :class="isDarkTheme ? 'text-violet-400' : 'text-violet-600'" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <polyline points="16 18 22 12 16 6" /><polyline points="8 6 2 12 8 18" />
              </svg>
            </div>
            <div>
              <h1 :class="['text-lg font-bold transition-colors', isDarkTheme ? 'text-white group-hover:text-violet-300' : 'text-slate-800 group-hover:text-violet-600']">LZQ's Tech Blog</h1>
              <p class="text-xs text-slate-500 hidden sm:block">技术沉淀 · 持续进化</p>
            </div>
          </router-link>
          
          <!-- 导航链接 -->
          <nav class="flex items-center gap-2 md:gap-6">
            <router-link 
              to="/blog" 
              :class="['flex items-center gap-2 text-sm transition-colors px-3 py-2 rounded-lg', isDarkTheme ? 'text-slate-400 hover:text-white hover:bg-white/5' : 'text-slate-600 hover:text-violet-600 hover:bg-violet-50']"
            >
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 20H5a2 2 0 01-2-2V6a2 2 0 012-2h10a2 2 0 012 2v1m2 13a2 2 0 01-2-2V7m2 13a2 2 0 002-2V9a2 2 0 00-2-2h-2m-4-3H9M7 16h6M7 8h6v4H7V8z"/>
              </svg>
              <span class="hidden sm:inline">全部文章</span>
            </router-link>
            <router-link 
              to="/kitchen" 
              class="hidden md:flex items-center gap-2 text-sm text-slate-400 hover:text-white transition-colors px-3 py-2 rounded-lg hover:bg-white/5"
            >
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6"/>
              </svg>
              私人厨房
            </router-link>
            <a 
              href="https://github.com/linzhiqin2003" 
              target="_blank"
              :class="['flex items-center gap-2 text-sm transition-colors px-3 py-2 rounded-lg', isDarkTheme ? 'text-slate-400 hover:text-white hover:bg-white/5' : 'text-slate-600 hover:text-violet-600 hover:bg-violet-50']"
            >
              <svg class="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                <path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"/>
              </svg>
              <span class="hidden sm:inline">GitHub</span>
            </a>
          </nav>
        </div>
      </div>
    </header>
    
    <!-- 主内容区域 -->
    <main class="pt-16 md:pt-20">
      <!-- 加载状态 -->
      <div v-if="loading" class="flex justify-center items-center py-40">
        <div class="relative w-16 h-16">
          <div class="absolute inset-0 border-4 border-violet-500/20 rounded-full"></div>
          <div class="absolute inset-0 border-4 border-violet-500 rounded-full border-t-transparent animate-spin"></div>
        </div>
      </div>
      
      <!-- 错误状态 -->
      <div v-else-if="error" class="text-center py-20">
        <div class="text-6xl mb-4">😢</div>
        <h2 class="text-2xl font-bold text-white mb-2">{{ error }}</h2>
        <button @click="goBack" class="mt-4 px-6 py-3 bg-gradient-to-r from-violet-600 to-fuchsia-600 text-white rounded-xl hover:shadow-lg hover:shadow-violet-500/25 transition-all">
          返回博客列表
        </button>
      </div>
      
      <!-- 文章内容 -->
      <article v-else-if="post" class="pb-16">
        <!-- 文章头部 -->
        <header :class="['relative overflow-hidden px-4 md:px-6 lg:px-8 py-16 md:py-24', isDarkTheme ? 'bg-[#0a0a0f] text-white' : 'bg-[#f5f0e0] text-slate-800']">
          <!-- 装饰背景 -->
          <div v-if="isDarkTheme" class="absolute inset-0 overflow-hidden">
            <div class="absolute -top-40 -right-40 w-80 h-80 bg-violet-500/15 rounded-full blur-[100px]"></div>
            <div class="absolute -bottom-40 -left-40 w-80 h-80 bg-fuchsia-500/15 rounded-full blur-[100px]"></div>
            <div class="absolute inset-0 bg-[linear-gradient(rgba(255,255,255,0.02)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,0.02)_1px,transparent_1px)] bg-[size:60px_60px]"></div>
          </div>
          
          <div class="relative container mx-auto max-w-4xl">
            <!-- 返回按钮 -->
            <button 
              @click="goBack"
              :class="['inline-flex items-center gap-2 mb-8 transition-colors group', isDarkTheme ? 'text-slate-400 hover:text-white' : 'text-slate-500 hover:text-slate-800']"
            >
              <svg class="w-5 h-5 group-hover:-translate-x-1 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
              </svg>
              返回博客列表
            </button>
            
            <!-- 标签 -->
            <div class="flex flex-wrap items-center gap-3 mb-5">
              <span
                v-for="(tag, i) in post.tags"
                :key="tag.id"
                :class="['text-sm font-medium tracking-wide uppercase', isDarkTheme ? 'text-violet-400' : 'text-amber-700']"
              >
                <span v-if="i > 0" :class="['mx-2', isDarkTheme ? 'text-slate-600' : 'text-amber-300']">/</span>{{ tag.name }}
              </span>
            </div>
            
            <!-- 标题 -->
            <h1 class="text-3xl md:text-5xl font-bold mb-6 leading-tight">{{ post.title }}</h1>
            
            <!-- 摘要 -->
            <p v-if="post.summary" :class="['text-lg mb-8 max-w-3xl leading-relaxed', isDarkTheme ? 'text-slate-400' : 'text-slate-600']">{{ post.summary }}</p>
            
            <!-- 元信息 -->
            <div :class="['flex flex-wrap items-center gap-6 text-sm', isDarkTheme ? 'text-slate-500' : 'text-slate-500']">
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
            class="w-full rounded-2xl shadow-2xl shadow-black/50 border border-white/10"
          />
        </div>
        
        <!-- 文章正文 -->
        <div class="container mx-auto max-w-4xl px-4 mt-12">
          <div :class="['rounded-2xl border p-6 md:p-10', isDarkTheme ? 'bg-[#12121a] border-white/5' : 'bg-[#faf7ef] border-amber-200/30 shadow-sm']">
            <div :class="['prose-content', isDarkTheme ? '' : 'prose-light']" v-html="parsedContent"></div>
          </div>
          
          <!-- 文章底部 -->
          <div :class="['mt-12 p-6 rounded-2xl border', isDarkTheme ? 'bg-gradient-to-r from-violet-500/10 to-fuchsia-500/10 border-violet-500/20' : 'bg-amber-50 border-amber-200/50']">
            <div class="flex flex-col md:flex-row items-center justify-between gap-4">
              <div>
                <h3 :class="['text-lg font-bold mb-1', isDarkTheme ? 'text-white' : 'text-slate-800']">感谢阅读！</h3>
                <p :class="['text-sm', isDarkTheme ? 'text-slate-400' : 'text-slate-600']">如果这篇文章对你有帮助，欢迎分享给更多人</p>
              </div>
              <button 
                @click="goBack"
                class="px-6 py-3 bg-gradient-to-r from-violet-600 to-fuchsia-600 text-white rounded-xl hover:shadow-lg hover:shadow-violet-500/25 transition-all"
              >
                查看更多文章
              </button>
            </div>
          </div>
        </div>
      </article>
    </main>
    
    <!-- 独立页脚 -->
    <footer :class="['border-t', isDarkTheme ? 'bg-[#08080c] border-white/5' : 'bg-[#f0ebe0] border-amber-200/30']">
      <div class="container mx-auto px-4 py-8">
        <div class="flex flex-col md:flex-row items-center justify-between gap-4 text-sm text-slate-500">
          <!-- 左侧：品牌 -->
          <div class="flex items-center gap-3">
            <div :class="['w-8 h-8 rounded-lg flex items-center justify-center', isDarkTheme ? 'bg-white/10' : 'bg-slate-100']">
              <svg class="w-4 h-4" :class="isDarkTheme ? 'text-violet-400' : 'text-violet-600'" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <polyline points="16 18 22 12 16 6" /><polyline points="8 6 2 12 8 18" />
              </svg>
            </div>
            <span class="text-slate-400">© 2026 LZQ's Tech Blog</span>
          </div>
          
          <!-- 右侧：GitHub + 技术栈 -->
          <div class="flex items-center gap-4">
            <a 
              href="https://github.com/linzhiqin2003" 
              target="_blank"
              class="flex items-center gap-2 text-slate-500 hover:text-violet-400 transition-colors"
            >
              <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 24 24">
                <path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"/>
              </svg>
              <span class="hidden sm:inline">GitHub</span>
            </a>
            <span class="text-slate-700">·</span>
            <span class="flex items-center gap-1.5">
              Built with <span class="text-red-500">❤️</span>
            </span>
          </div>
        </div>
      </div>
    </footer>
  </div>
</template>

<style scoped>
/* Markdown 内容样式 - 暗色主题 */
.prose-content {
  font-size: 1.125rem;
  line-height: 1.8;
  color: #cbd5e1;
}

/* 标题 h1-h6 */
.prose-content :deep(.md-h1) {
  font-size: 2rem;
  font-weight: 700;
  color: #f1f5f9;
  margin: 2rem 0 1rem;
  padding-bottom: 0.5rem;
  border-bottom: 2px solid rgba(255,255,255,0.1);
}

.prose-content :deep(.md-h2) {
  font-size: 1.5rem;
  font-weight: 700;
  color: #e2e8f0;
  margin: 1.75rem 0 0.75rem;
}

.prose-content :deep(.md-h3) {
  font-size: 1.25rem;
  font-weight: 600;
  color: #cbd5e1;
  margin: 1.5rem 0 0.5rem;
}

.prose-content :deep(.md-h4) {
  font-size: 1.125rem;
  font-weight: 600;
  color: #a5b4c8;
  margin: 1.25rem 0 0.5rem;
}

.prose-content :deep(.md-h5) {
  font-size: 1rem;
  font-weight: 600;
  color: #94a3b8;
  margin: 1rem 0 0.5rem;
}

.prose-content :deep(.md-h6) {
  font-size: 0.875rem;
  font-weight: 600;
  color: #64748b;
  margin: 1rem 0 0.5rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.prose-content :deep(.md-p) {
  margin: 1rem 0;
}

.prose-content :deep(.md-link) {
  color: #a78bfa;
  text-decoration: underline;
  text-underline-offset: 2px;
  transition: color 0.2s;
}

.prose-content :deep(.md-link:hover) {
  color: #c4b5fd;
}

/* 图片和 figure */
.prose-content :deep(.md-img) {
  max-width: 100%;
  border-radius: 0.75rem;
  margin: 1.5rem 0;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.3);
}

.prose-content :deep(.md-figure) {
  margin: 1.5rem 0;
  text-align: center;
}

.prose-content :deep(.md-figure figcaption) {
  margin-top: 0.5rem;
  font-size: 0.875rem;
  color: #64748b;
  font-style: italic;
}

/* 列表 */
.prose-content :deep(.md-ul),
.prose-content :deep(.md-ol) {
  margin: 1rem 0;
  padding-left: 1.5rem;
}

.prose-content :deep(.md-li) {
  margin: 0.5rem 0;
}

.prose-content :deep(.md-ul) {
  list-style-type: disc;
}

.prose-content :deep(.md-ol) {
  list-style-type: decimal;
}

/* 嵌套列表 */
.prose-content :deep(.md-ul .md-ul),
.prose-content :deep(.md-ol .md-ol),
.prose-content :deep(.md-ul .md-ol),
.prose-content :deep(.md-ol .md-ul) {
  margin: 0.25rem 0;
}

/* 引用 */
.prose-content :deep(.md-quote) {
  border-left: 4px solid #8b5cf6;
  padding: 1rem 1.5rem;
  margin: 1.5rem 0;
  background: linear-gradient(to right, rgba(139, 92, 246, 0.1), transparent);
  color: #94a3b8;
  font-style: italic;
  border-radius: 0 0.5rem 0.5rem 0;
}

.prose-content :deep(.md-quote p) {
  margin: 0.5rem 0;
}

.prose-content :deep(.md-quote p:first-child) {
  margin-top: 0;
}

.prose-content :deep(.md-quote p:last-child) {
  margin-bottom: 0;
}

/* 水平线 */
.prose-content :deep(.md-hr) {
  border: none;
  border-top: 2px solid rgba(255,255,255,0.1);
  margin: 2rem 0;
}

/* 行内代码 */
.prose-content :deep(.inline-code) {
  background: rgba(139, 92, 246, 0.2);
  padding: 0.2rem 0.4rem;
  border-radius: 0.25rem;
  font-family: 'Fira Code', 'Monaco', 'Consolas', monospace;
  font-size: 0.9em;
  color: #c4b5fd;
}

/* 代码块 */
.prose-content :deep(.code-block) {
  background: #0d0d12;
  border-radius: 0.75rem;
  padding: 1.25rem;
  margin: 1.5rem 0;
  overflow-x: auto;
  position: relative;
  border: 1px solid rgba(255,255,255,0.05);
}

.prose-content :deep(.code-block)::before {
  content: attr(data-lang);
  position: absolute;
  top: 0.5rem;
  right: 0.75rem;
  font-size: 0.75rem;
  color: #4b5563;
  text-transform: uppercase;
  font-weight: 500;
}

.prose-content :deep(.code-block code) {
  font-family: 'Fira Code', 'Monaco', 'Consolas', monospace;
  font-size: 0.9rem;
  color: #e2e8f0;
  line-height: 1.7;
  white-space: pre;
  display: block;
}

/* highlight.js 语法高亮样式 - 暗色主题 */
.prose-content :deep(.hljs-comment),
.prose-content :deep(.hljs-quote) {
  color: #6b7280;
  font-style: italic;
}

.prose-content :deep(.hljs-keyword),
.prose-content :deep(.hljs-selector-tag),
.prose-content :deep(.hljs-type) {
  color: #c792ea;
}

.prose-content :deep(.hljs-string),
.prose-content :deep(.hljs-template-variable),
.prose-content :deep(.hljs-addition) {
  color: #c3e88d;
}

.prose-content :deep(.hljs-number),
.prose-content :deep(.hljs-literal),
.prose-content :deep(.hljs-variable),
.prose-content :deep(.hljs-template-tag) {
  color: #f78c6c;
}

.prose-content :deep(.hljs-function),
.prose-content :deep(.hljs-title) {
  color: #82aaff;
}

.prose-content :deep(.hljs-attribute),
.prose-content :deep(.hljs-symbol),
.prose-content :deep(.hljs-bullet) {
  color: #ffcb6b;
}

.prose-content :deep(.hljs-built_in),
.prose-content :deep(.hljs-class .hljs-title) {
  color: #89ddff;
}

.prose-content :deep(.hljs-deletion) {
  color: #ff5370;
}

.prose-content :deep(.hljs-meta) {
  color: #f78c6c;
}

.prose-content :deep(.hljs-emphasis) {
  font-style: italic;
}

.prose-content :deep(.hljs-strong) {
  font-weight: bold;
}

/* 粗体和斜体 */
.prose-content :deep(strong) {
  color: #f1f5f9;
  font-weight: 600;
}

.prose-content :deep(em) {
  font-style: italic;
}

/* 表格 */
.prose-content :deep(.md-table-wrapper) {
  overflow-x: auto;
  margin: 1.5rem 0;
  border-radius: 0.5rem;
}

.prose-content :deep(.md-table) {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.95rem;
}

.prose-content :deep(.md-table th),
.prose-content :deep(.md-table td) {
  padding: 0.75rem 1rem;
  border: 1px solid rgba(255,255,255,0.1);
  text-align: left;
}

.prose-content :deep(.md-table th) {
  background: rgba(139, 92, 246, 0.1);
  color: #e2e8f0;
  font-weight: 600;
}

.prose-content :deep(.md-table tr:hover) {
  background: rgba(255,255,255,0.02);
}

/* 删除线 */
.prose-content :deep(del) {
  color: #64748b;
  text-decoration: line-through;
}

/* 任务列表 */
.prose-content :deep(.task-list-item) {
  list-style: none;
  margin-left: -1.5rem;
  padding-left: 1.5rem;
}

.prose-content :deep(.task-list-item input) {
  margin-right: 0.5rem;
}

/* ====== 亮色模式覆盖 ====== */
.prose-light :deep(.md-h1),
.prose-light :deep(.md-h2),
.prose-light :deep(.md-h3),
.prose-light :deep(.md-h4) {
  color: #1e293b;
}

.prose-light :deep(.md-p) {
  color: #334155;
}

.prose-light :deep(.md-li) {
  color: #334155;
}

.prose-light :deep(.md-quote) {
  border-left-color: #d97706;
  background: #fef3c7;
  color: #92400e;
}

.prose-light :deep(.md-link) {
  color: #6d28d9;
  text-decoration: underline;
  text-underline-offset: 3px;
  text-decoration-color: #6d28d920;
}

.prose-light :deep(.md-link:hover) {
  color: #5b21b6;
  text-decoration-color: #5b21b6;
}

.prose-light :deep(strong) {
  color: #1e293b;
}

.prose-light :deep(em) {
  color: #334155;
}

.prose-light :deep(.inline-code) {
  background: rgba(139, 92, 246, 0.12);
  color: #5b21b6;
  padding: 0.2rem 0.45rem;
  font-weight: 500;
}

.prose-light :deep(.code-block) {
  background: #1e1e2e;
  border: 1px solid #e2e8f0;
}

.prose-light :deep(.md-table th) {
  background: #f5f0e0;
  color: #1e293b;
}

.prose-light :deep(.md-table td) {
  border-color: #e2e8f0;
  color: #334155;
}

.prose-light :deep(.md-table tr:hover) {
  background: #faf8f0;
}

.prose-light :deep(.md-hr) {
  border-color: #e2e8f0;
}

.prose-light :deep(del) {
  color: #94a3b8;
}

/* 纸质纹理 */
.paper-texture {
  background-image:
    url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='200' height='200'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.65' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='200' height='200' filter='url(%23n)' opacity='0.06'/%3E%3C/svg%3E");
  background-color: #faf8f0;
}
</style>
