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
  <div class="min-h-screen bg-[#0a0a0f] text-slate-100 font-sans">
    <!-- 独立导航栏 -->
    <header class="fixed top-0 left-0 right-0 z-50 bg-[#0a0a0f]/80 backdrop-blur-xl border-b border-white/5">
      <div class="container mx-auto px-4 md:px-6">
        <div class="flex items-center justify-between h-16 md:h-20">
          <!-- Logo -->
          <router-link to="/blog" class="flex items-center gap-3 group">
            <div class="w-10 h-10 rounded-xl bg-gradient-to-br from-violet-500 to-fuchsia-500 flex items-center justify-center text-white font-bold text-lg shadow-lg shadow-violet-500/25 group-hover:shadow-violet-500/40 transition-shadow">
              L
            </div>
            <div>
              <h1 class="text-lg font-bold text-white group-hover:text-violet-300 transition-colors">LZQ's Tech Blog</h1>
              <p class="text-xs text-slate-500 hidden sm:block">技术沉淀 · 持续进化</p>
            </div>
          </router-link>
          
          <!-- 导航链接 -->
          <nav class="flex items-center gap-2 md:gap-6">
            <router-link 
              to="/blog" 
              class="flex items-center gap-2 text-sm text-slate-400 hover:text-white transition-colors px-3 py-2 rounded-lg hover:bg-white/5"
            >
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 20H5a2 2 0 01-2-2V6a2 2 0 012-2h10a2 2 0 012 2v1m2 13a2 2 0 01-2-2V7m2 13a2 2 0 002-2V9a2 2 0 00-2-2h-2m-4-3H9M7 16h6M7 8h6v4H7V8z"/>
              </svg>
              <span class="hidden sm:inline">全部文章</span>
            </router-link>
            <router-link 
              to="/" 
              class="hidden md:flex items-center gap-2 text-sm text-slate-400 hover:text-white transition-colors px-3 py-2 rounded-lg hover:bg-white/5"
            >
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6"/>
              </svg>
              私人厨房
            </router-link>
            <a 
              href="https://github.com/Eslzzyl" 
              target="_blank"
              class="flex items-center gap-2 text-sm text-slate-400 hover:text-white transition-colors px-3 py-2 rounded-lg hover:bg-white/5"
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
        <header class="relative overflow-hidden bg-[#0a0a0f] text-white px-4 md:px-6 lg:px-8 py-16 md:py-24">
          <!-- 装饰背景 -->
          <div class="absolute inset-0 overflow-hidden">
            <div class="absolute -top-40 -right-40 w-80 h-80 bg-violet-500/15 rounded-full blur-[100px]"></div>
            <div class="absolute -bottom-40 -left-40 w-80 h-80 bg-fuchsia-500/15 rounded-full blur-[100px]"></div>
            <div class="absolute inset-0 bg-[linear-gradient(rgba(255,255,255,0.02)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,0.02)_1px,transparent_1px)] bg-[size:60px_60px]"></div>
          </div>
          
          <div class="relative container mx-auto max-w-4xl">
            <!-- 返回按钮 -->
            <button 
              @click="goBack"
              class="inline-flex items-center gap-2 text-slate-400 hover:text-white mb-8 transition-colors group"
            >
              <svg class="w-5 h-5 group-hover:-translate-x-1 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
              </svg>
              返回博客列表
            </button>
            
            <!-- 标签 -->
            <div class="flex flex-wrap gap-2 mb-4">
              <span
                v-for="tag in post.tags"
                :key="tag.id"
                class="px-3 py-1 rounded-full text-sm font-medium border"
                :style="{ backgroundColor: tag.color + '20', color: tag.color, borderColor: tag.color + '40' }"
              >
                {{ tag.name }}
              </span>
            </div>
            
            <!-- 标题 -->
            <h1 class="text-3xl md:text-5xl font-bold mb-6 leading-tight">{{ post.title }}</h1>
            
            <!-- 摘要 -->
            <p v-if="post.summary" class="text-lg text-slate-400 mb-8 max-w-3xl leading-relaxed">{{ post.summary }}</p>
            
            <!-- 元信息 -->
            <div class="flex flex-wrap items-center gap-6 text-sm text-slate-500">
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
          <div class="bg-[#12121a] rounded-2xl border border-white/5 p-6 md:p-10">
            <div class="prose-content" v-html="parsedContent"></div>
          </div>
          
          <!-- 文章底部 -->
          <div class="mt-12 p-6 bg-gradient-to-r from-violet-500/10 to-fuchsia-500/10 rounded-2xl border border-violet-500/20">
            <div class="flex flex-col md:flex-row items-center justify-between gap-4">
              <div>
                <h3 class="text-lg font-bold text-white mb-1">感谢阅读！</h3>
                <p class="text-slate-400 text-sm">如果这篇文章对你有帮助，欢迎分享给更多人</p>
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
    <footer class="bg-[#08080c] border-t border-white/5">
      <div class="container mx-auto px-4 py-12">
        <div class="grid grid-cols-1 md:grid-cols-3 gap-8 mb-8">
          <!-- 关于 -->
          <div>
            <div class="flex items-center gap-3 mb-4">
              <div class="w-10 h-10 rounded-xl bg-gradient-to-br from-violet-500 to-fuchsia-500 flex items-center justify-center text-white font-bold text-lg">
                L
              </div>
              <div>
                <h3 class="text-lg font-bold text-white">LZQ's Tech Blog</h3>
              </div>
            </div>
            <p class="text-sm text-slate-500 leading-relaxed">
              一个关于技术学习、编程实践和思考沉淀的个人博客。<br>
              记录成长的每一步。
            </p>
          </div>
          
          <!-- 快速链接 -->
          <div>
            <h4 class="text-sm font-semibold text-white uppercase tracking-wider mb-4">快速链接</h4>
            <ul class="space-y-2">
              <li>
                <router-link to="/blog" class="text-sm text-slate-500 hover:text-violet-400 transition-colors">全部文章</router-link>
              </li>
              <li>
                <router-link to="/" class="text-sm text-slate-500 hover:text-violet-400 transition-colors">私人厨房</router-link>
              </li>
              <li>
                <router-link to="/ai-lab" class="text-sm text-slate-500 hover:text-violet-400 transition-colors">AI 实验室</router-link>
              </li>
            </ul>
          </div>
          
          <!-- 联系方式 -->
          <div>
            <h4 class="text-sm font-semibold text-white uppercase tracking-wider mb-4">联系我</h4>
            <div class="flex items-center gap-4">
              <a 
                href="https://github.com/Eslzzyl" 
                target="_blank"
                class="w-10 h-10 rounded-xl bg-white/5 border border-white/10 flex items-center justify-center text-slate-400 hover:text-white hover:bg-white/10 hover:border-white/20 transition-all"
              >
                <svg class="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"/>
                </svg>
              </a>
            </div>
          </div>
        </div>
        
        <!-- 版权信息 -->
        <div class="pt-8 border-t border-white/5 flex flex-col md:flex-row items-center justify-between gap-4 text-sm text-slate-600">
          <p>© 2025 LZQ's Tech Blog. All rights reserved.</p>
          <p class="flex items-center gap-2">
            <span>Built with</span>
            <span class="text-red-500">❤️</span>
            <span>using Vue.js & Tailwind CSS</span>
          </p>
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

.prose-content :deep(.md-p) {
  margin: 1rem 0;
}

.prose-content :deep(.md-link) {
  color: #a78bfa;
  text-decoration: underline;
  text-underline-offset: 2px;
}

.prose-content :deep(.md-link:hover) {
  color: #c4b5fd;
}

.prose-content :deep(.md-img) {
  max-width: 100%;
  border-radius: 0.75rem;
  margin: 1.5rem 0;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.3);
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
  border-left: 4px solid #8b5cf6;
  padding: 1rem 1.5rem;
  margin: 1.5rem 0;
  background: linear-gradient(to right, rgba(139, 92, 246, 0.1), transparent);
  color: #94a3b8;
  font-style: italic;
  border-radius: 0 0.5rem 0.5rem 0;
}

.prose-content :deep(.md-hr) {
  border: none;
  border-top: 2px solid rgba(255,255,255,0.1);
  margin: 2rem 0;
}

.prose-content :deep(.inline-code) {
  background: rgba(139, 92, 246, 0.2);
  padding: 0.2rem 0.4rem;
  border-radius: 0.25rem;
  font-family: 'Fira Code', 'Monaco', monospace;
  font-size: 0.9em;
  color: #c4b5fd;
}

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
}

.prose-content :deep(.code-block code) {
  font-family: 'Fira Code', 'Monaco', monospace;
  font-size: 0.9rem;
  color: #e2e8f0;
  line-height: 1.7;
  white-space: pre-wrap;
  word-break: break-word;
  display: block;
}

.prose-content :deep(strong) {
  color: #f1f5f9;
  font-weight: 600;
}

.prose-content :deep(em) {
  font-style: italic;
}
</style>
