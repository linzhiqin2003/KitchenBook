<script setup>
import { ref, onMounted, computed, onUnmounted, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'
import API_BASE_URL from '../config/api'

const router = useRouter()
const posts = ref([])
const tags = ref([])
const stats = ref({ total_posts: 0, total_views: 0, total_tags: 0 })
const loading = ref(true)
const selectedTag = ref('')
const searchQuery = ref('')

// 主题切换 (dark / light)
const isDarkTheme = ref(localStorage.getItem('blog_theme') !== 'light')

const toggleTheme = () => {
  isDarkTheme.value = !isDarkTheme.value
  localStorage.setItem('blog_theme', isDarkTheme.value ? 'dark' : 'light')
  
  // 主题切换后，确保所有已在视口内的 scroll-reveal 元素保持可见
  nextTick(() => {
    document.querySelectorAll('.scroll-reveal').forEach(el => {
      el.classList.add('revealed')
    })
  })
}

// 滚动动画观察器
let observer = null
const setupScrollAnimation = () => {
  nextTick(() => {
    observer = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          entry.target.classList.add('revealed')
          observer.unobserve(entry.target)
        }
      })
    }, {
      threshold: 0.1,
      rootMargin: '0px 0px -50px 0px'
    })
    
    document.querySelectorAll('.scroll-reveal').forEach(el => {
      observer.observe(el)
    })
  })
}

onUnmounted(() => {
  if (observer) {
    observer.disconnect()
  }
})

// 默认封面渐变色
const defaultCovers = [
  'from-violet-500 via-purple-500 to-fuchsia-500',
  'from-cyan-500 via-blue-500 to-indigo-500',
  'from-emerald-500 via-teal-500 to-cyan-500',
  'from-orange-500 via-amber-500 to-yellow-500',
  'from-rose-500 via-pink-500 to-purple-500',
  'from-slate-600 via-slate-700 to-slate-800',
]

const getDefaultCover = (index) => defaultCovers[index % defaultCovers.length]

// 获取博客文章
const fetchPosts = async () => {
  try {
    loading.value = true
    let url = `${API_BASE_URL}/api/blog/posts/`
    const params = new URLSearchParams()
    
    if (selectedTag.value) {
      params.append('tag', selectedTag.value)
    }
    if (searchQuery.value) {
      params.append('search', searchQuery.value)
    }
    
    if (params.toString()) {
      url += `?${params.toString()}`
    }
    
    const response = await axios.get(url)
    posts.value = response.data
  } catch (error) {
    console.error('Failed to fetch posts', error)
  } finally {
    loading.value = false
    // 数据加载完成后设置滚动动画
    setupScrollAnimation()
  }
}

// 获取标签列表
const fetchTags = async () => {
  try {
    const response = await axios.get(`${API_BASE_URL}/api/blog/tags/`)
    tags.value = response.data
  } catch (error) {
    console.error('Failed to fetch tags', error)
  }
}

// 获取统计信息
const fetchStats = async () => {
  try {
    const response = await axios.get(`${API_BASE_URL}/api/blog/posts/stats/`)
    stats.value = response.data
  } catch (error) {
    console.error('Failed to fetch stats', error)
  }
}

onMounted(() => {
  fetchPosts()
  fetchTags()
  fetchStats()
})

// 筛选标签
const filterByTag = (tagName) => {
  selectedTag.value = selectedTag.value === tagName ? '' : tagName
  fetchPosts()
}

// 搜索
const handleSearch = () => {
  fetchPosts()
}

// 格式化日期
const formatDate = (dateStr) => {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  return date.toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: 'short',
    day: 'numeric'
  })
}

// 精选文章
const featuredPosts = computed(() => posts.value.filter(p => p.is_featured).slice(0, 3))
const regularPosts = computed(() => posts.value.filter(p => !p.is_featured || featuredPosts.value.length === 0))
</script>

<template>
  <div :class="[
    'min-h-screen font-sans transition-colors duration-500',
    isDarkTheme ? 'bg-[#0a0a0f] text-slate-100' : 'bg-gradient-to-br from-slate-50 via-white to-violet-50 text-slate-800'
  ]">
    <!-- 独立导航栏 -->
    <header :class="[
      'fixed top-0 left-0 right-0 z-50 backdrop-blur-xl border-b transition-colors duration-500',
      isDarkTheme ? 'bg-[#0a0a0f]/80 border-white/5' : 'bg-white/80 border-slate-200/50'
    ]">
      <div class="container mx-auto px-4 md:px-6">
        <div class="flex items-center justify-between h-16 md:h-20">
          <!-- Logo -->
          <router-link to="/blog" class="flex items-center gap-3 group">
            <div class="w-10 h-10 rounded-xl bg-gradient-to-br from-violet-500 to-fuchsia-500 flex items-center justify-center text-white font-bold text-lg shadow-lg shadow-violet-500/25 group-hover:shadow-violet-500/40 transition-shadow">
              L
            </div>
            <div>
              <h1 :class="['text-lg font-bold transition-colors', isDarkTheme ? 'text-white group-hover:text-violet-300' : 'text-slate-800 group-hover:text-violet-600']">LZQ's Tech Blog</h1>
              <p :class="['text-xs hidden sm:block', isDarkTheme ? 'text-slate-500' : 'text-slate-500']">技术沉淀 · 持续进化</p>
            </div>
          </router-link>
          
          <!-- 导航链接 -->
          <nav class="flex items-center gap-2 md:gap-4">
            <!-- 主题切换按钮 -->
            <button 
              @click="toggleTheme"
              :class="[
                'flex items-center justify-center w-9 h-9 rounded-lg transition-all',
                isDarkTheme ? 'text-slate-400 hover:text-white hover:bg-white/10' : 'text-slate-500 hover:text-slate-800 hover:bg-slate-100'
              ]"
              :title="isDarkTheme ? '切换为亮色模式' : '切换为暗色模式'"
            >
              <!-- 太阳图标 (亮色) -->
              <svg v-if="isDarkTheme" class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z" />
              </svg>
              <!-- 月亮图标 (暗色) -->
              <svg v-else class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z" />
              </svg>
            </button>
            
            <router-link 
              to="/kitchen" 
              :class="[
                'hidden md:flex items-center gap-2 text-sm transition-colors px-3 py-2 rounded-lg',
                isDarkTheme ? 'text-slate-400 hover:text-white hover:bg-white/5' : 'text-slate-600 hover:text-violet-600 hover:bg-violet-50'
              ]"
            >
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6"/>
              </svg>
              私人厨房
            </router-link>
            <router-link 
              to="/kitchen/ai-lab" 
              :class="[
                'flex items-center gap-2 text-sm transition-colors px-3 py-2 rounded-lg',
                isDarkTheme ? 'text-slate-400 hover:text-white hover:bg-white/5' : 'text-slate-600 hover:text-violet-600 hover:bg-violet-50'
              ]"
            >
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"/>
              </svg>
              <span class="hidden sm:inline">AI 实验室</span>
              <span class="sm:hidden">AI</span>
            </router-link>
            <a 
              href="https://github.com/linzhiqin2003" 
              target="_blank"
              :class="[
                'flex items-center gap-2 text-sm transition-colors px-3 py-2 rounded-lg',
                isDarkTheme ? 'text-slate-400 hover:text-white hover:bg-white/5' : 'text-slate-600 hover:text-violet-600 hover:bg-violet-50'
              ]"
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
      <!-- 博客头部 Hero Section -->
      <div class="relative overflow-hidden">
        <!-- 暗色背景 -->
        <div v-if="isDarkTheme" class="absolute inset-0 bg-[#0a0a0f]">
          <!-- 渐变光晕 -->
          <div class="absolute top-0 left-1/4 w-[500px] h-[500px] bg-violet-600/20 rounded-full blur-[120px] animate-pulse-slow"></div>
          <div class="absolute bottom-0 right-1/4 w-[400px] h-[400px] bg-fuchsia-600/15 rounded-full blur-[100px] animate-pulse-slow animation-delay-2000"></div>
          <div class="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-indigo-600/10 rounded-full blur-[150px]"></div>
          <!-- 星星点缀 -->
          <div class="absolute inset-0 overflow-hidden">
            <div class="stars"></div>
          </div>
          <!-- 网格 -->
          <div class="absolute inset-0 bg-[linear-gradient(rgba(255,255,255,0.02)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,0.02)_1px,transparent_1px)] bg-[size:60px_60px]"></div>
        </div>
        <!-- 亮色背景 -->
        <div v-else class="absolute inset-0 bg-gradient-to-br from-violet-50 via-white to-fuchsia-50">
          <!-- 渐变光晕 -->
          <div class="absolute top-0 left-1/4 w-[500px] h-[500px] bg-violet-300/30 rounded-full blur-[120px]"></div>
          <div class="absolute bottom-0 right-1/4 w-[400px] h-[400px] bg-fuchsia-300/20 rounded-full blur-[100px]"></div>
          <div class="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-blue-200/20 rounded-full blur-[150px]"></div>
          <!-- 网格 -->
          <div class="absolute inset-0 bg-[linear-gradient(rgba(139,92,246,0.05)_1px,transparent_1px),linear-gradient(90deg,rgba(139,92,246,0.05)_1px,transparent_1px)] bg-[size:60px_60px]"></div>
        </div>
        
        <div class="relative px-4 md:px-6 lg:px-8 py-20 md:py-32">
          <div class="container mx-auto text-center">
            <!-- 状态标签 -->
            <div :class="[
              'inline-flex items-center gap-2 px-5 py-2.5 rounded-full backdrop-blur-md border text-sm mb-8 animate-fade-in',
              isDarkTheme ? 'bg-white/5 border-white/10' : 'bg-white/60 border-violet-200/50 shadow-lg shadow-violet-500/5'
            ]">
              <span class="relative flex h-2 w-2">
                <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                <span class="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
              </span>
              <span :class="isDarkTheme ? 'text-slate-300' : 'text-slate-600'">技术分享 · 持续更新中</span>
            </div>
            
            <!-- 标题 -->
            <h1 class="text-5xl md:text-7xl font-black mb-6 animate-fade-in-up tracking-tight">
              <span :class="[
                'bg-clip-text text-transparent',
                isDarkTheme ? 'bg-gradient-to-r from-white via-violet-200 to-fuchsia-200' : 'bg-gradient-to-r from-violet-600 via-purple-600 to-fuchsia-600'
              ]">
                技术博客
              </span>
            </h1>
            
            <!-- 副标题 -->
            <p :class="[
              'text-lg md:text-xl max-w-2xl mx-auto mb-12 leading-relaxed animate-fade-in-up animation-delay-200',
              isDarkTheme ? 'text-slate-400' : 'text-slate-600'
            ]">
              记录学习历程，分享技术心得<br class="hidden md:block">
              探索编程世界的无限可能
            </p>
            
            <!-- 统计信息 -->
            <div class="flex justify-center gap-6 md:gap-12 animate-fade-in-up animation-delay-400">
              <div class="group">
                <div class="relative">
                  <div class="absolute inset-0 bg-gradient-to-r from-violet-500 to-fuchsia-500 rounded-2xl blur-lg opacity-40 group-hover:opacity-60 transition-opacity"></div>
                  <div :class="[
                    'relative backdrop-blur-md rounded-2xl px-6 md:px-8 py-4 md:py-5 border',
                    isDarkTheme ? 'bg-white/5 border-white/10' : 'bg-white/80 border-violet-200/50 shadow-xl'
                  ]">
                    <div :class="['text-3xl md:text-4xl font-bold mb-1', isDarkTheme ? 'text-white' : 'text-violet-600']">{{ stats.total_posts }}</div>
                    <div :class="['text-xs md:text-sm uppercase tracking-wider', isDarkTheme ? 'text-slate-400' : 'text-slate-500']">篇文章</div>
                  </div>
                </div>
              </div>
              <div class="group">
                <div class="relative">
                  <div class="absolute inset-0 bg-gradient-to-r from-cyan-500 to-blue-500 rounded-2xl blur-lg opacity-40 group-hover:opacity-60 transition-opacity"></div>
                  <div :class="[
                    'relative backdrop-blur-md rounded-2xl px-6 md:px-8 py-4 md:py-5 border',
                    isDarkTheme ? 'bg-white/5 border-white/10' : 'bg-white/80 border-cyan-200/50 shadow-xl'
                  ]">
                    <div :class="['text-3xl md:text-4xl font-bold mb-1', isDarkTheme ? 'text-white' : 'text-cyan-600']">{{ stats.total_views }}</div>
                    <div :class="['text-xs md:text-sm uppercase tracking-wider', isDarkTheme ? 'text-slate-400' : 'text-slate-500']">次阅读</div>
                  </div>
                </div>
              </div>
              <div class="group">
                <div class="relative">
                  <div class="absolute inset-0 bg-gradient-to-r from-emerald-500 to-teal-500 rounded-2xl blur-lg opacity-40 group-hover:opacity-60 transition-opacity"></div>
                  <div :class="[
                    'relative backdrop-blur-md rounded-2xl px-6 md:px-8 py-4 md:py-5 border',
                    isDarkTheme ? 'bg-white/5 border-white/10' : 'bg-white/80 border-emerald-200/50 shadow-xl'
                  ]">
                    <div :class="['text-3xl md:text-4xl font-bold mb-1', isDarkTheme ? 'text-white' : 'text-emerald-600']">{{ stats.total_tags }}</div>
                    <div :class="['text-xs md:text-sm uppercase tracking-wider', isDarkTheme ? 'text-slate-400' : 'text-slate-500']">个标签</div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
      
      <!-- 搜索和筛选区域 -->
      <div :class="[
        'border-y transition-colors duration-500',
        isDarkTheme ? 'bg-[#12121a] border-white/5' : 'bg-white border-slate-200'
      ]">
        <div class="container mx-auto px-4 py-6">
          <div class="scroll-reveal flex flex-col md:flex-row gap-4 items-center justify-between">
            <!-- 搜索框 -->
            <div class="relative w-full md:w-auto md:flex-1 md:max-w-md">
              <input
                v-model="searchQuery"
                @keyup.enter="handleSearch"
                type="text"
                placeholder="搜索文章标题或内容..."
                :class="[
                  'w-full pl-12 pr-24 py-3.5 border rounded-xl focus:outline-none focus:ring-2 focus:ring-violet-500/50 focus:border-violet-500/50 transition-all',
                  isDarkTheme 
                    ? 'bg-white/5 border-white/10 text-white placeholder-slate-500' 
                    : 'bg-white border-slate-200 text-slate-800 placeholder-slate-400 shadow-lg'
                ]"
              />
              <svg class="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
              <button 
                @click="handleSearch"
                class="absolute right-2 top-1/2 -translate-y-1/2 px-4 py-2 bg-gradient-to-r from-violet-600 to-fuchsia-600 text-white text-sm font-medium rounded-lg hover:shadow-lg hover:shadow-violet-500/25 transition-all"
              >
                搜索
              </button>
            </div>
            
            <!-- 标签筛选 -->
            <div class="flex flex-wrap gap-2 justify-center md:justify-end">
              <button
                @click="filterByTag('')"
                :class="[
                  'px-4 py-2 rounded-xl text-sm font-medium transition-all duration-300',
                  !selectedTag 
                    ? 'bg-gradient-to-r from-violet-600 to-fuchsia-600 text-white shadow-lg shadow-violet-500/25' 
                    : isDarkTheme 
                      ? 'bg-white/5 text-slate-400 hover:bg-white/10 hover:text-white border border-white/10'
                      : 'bg-white text-slate-600 hover:bg-violet-50 hover:text-violet-600 border border-slate-200 shadow-sm'
                ]"
              >
                全部文章
              </button>
              <button
                v-for="tag in tags"
                :key="tag.id"
                @click="filterByTag(tag.name)"
                :class="[
                  'px-4 py-2 rounded-xl text-sm font-medium transition-all duration-300 flex items-center gap-2',
                  selectedTag === tag.name 
                    ? 'text-white shadow-lg' 
                    : isDarkTheme 
                      ? 'bg-white/5 text-slate-400 hover:bg-white/10 hover:text-white border border-white/10'
                      : 'bg-white text-slate-600 hover:bg-slate-50 border border-slate-200 shadow-sm'
                ]"
                :style="selectedTag === tag.name ? { 
                  background: `linear-gradient(135deg, ${tag.color}, ${tag.color}dd)`,
                  boxShadow: `0 10px 25px -5px ${tag.color}50`
                } : {}"
              >
                <span 
                  class="w-2 h-2 rounded-full" 
                  :style="{ backgroundColor: tag.color }"
                ></span>
                {{ tag.name }}
              </button>
            </div>
          </div>
        </div>
      </div>
      
      <!-- 文章列表区域 -->
      <div :class="['min-h-[50vh] transition-colors duration-500', isDarkTheme ? 'bg-[#0f0f15]' : 'bg-slate-50']">
        <div class="container mx-auto px-4 py-12">
          <!-- 加载状态 -->
          <div v-if="loading" class="flex flex-col justify-center items-center py-20">
            <div class="relative w-16 h-16">
              <div :class="['absolute inset-0 border-4 rounded-full', isDarkTheme ? 'border-violet-500/20' : 'border-violet-300']"></div>
              <div class="absolute inset-0 border-4 border-violet-500 rounded-full border-t-transparent animate-spin"></div>
            </div>
            <p :class="['mt-4', isDarkTheme ? 'text-slate-500' : 'text-slate-600']">加载中...</p>
          </div>
          
          <!-- 文章列表 -->
          <div v-else-if="posts.length > 0">
            <!-- 精选文章 -->
            <div v-if="featuredPosts.length > 0 && !selectedTag && !searchQuery" class="mb-14">
              <div class="scroll-reveal flex items-center gap-3 mb-8">
                <div class="w-1 h-8 bg-gradient-to-b from-amber-400 to-orange-500 rounded-full"></div>
                <h2 :class="['text-2xl font-bold', isDarkTheme ? 'text-white' : 'text-slate-800']">精选推荐</h2>
              </div>
              <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
                <router-link
                  v-for="(post, index) in featuredPosts"
                  :key="post.id"
                  :to="`/blog/${post.slug}`"
                  class="scroll-reveal group relative overflow-hidden rounded-2xl aspect-[4/3] cursor-pointer"
                  :style="{ transitionDelay: `${index * 100}ms` }"
                >
                  <!-- 背景 -->
                  <div 
                    class="absolute inset-0 bg-gradient-to-br transition-transform duration-500 group-hover:scale-110"
                    :class="post.cover_image ? '' : getDefaultCover(index)"
                  >
                    <img 
                      v-if="post.cover_image"
                      :src="post.cover_image"
                      :alt="post.title"
                      class="w-full h-full object-cover"
                    />
                  </div>
                  <!-- 遮罩 -->
                  <div class="absolute inset-0 bg-gradient-to-t from-black/80 via-black/40 to-transparent"></div>
                  <!-- 内容 -->
                  <div class="absolute inset-0 p-6 flex flex-col justify-end">
                    <div class="flex gap-2 mb-3">
                      <span
                        v-for="tag in post.tags?.slice(0, 2)"
                        :key="tag.id"
                        class="px-2.5 py-1 bg-white/20 backdrop-blur-sm rounded-full text-xs text-white/90"
                      >
                        {{ tag.name }}
                      </span>
                    </div>
                    <h3 class="text-xl font-bold text-white mb-2 group-hover:text-violet-200 transition-colors line-clamp-2">
                      {{ post.title }}
                    </h3>
                    <div class="flex items-center justify-between text-sm text-white/60">
                      <span>{{ formatDate(post.published_at || post.created_at) }}</span>
                      <span class="flex items-center gap-1">
                        <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                          <path d="M10 12a2 2 0 100-4 2 2 0 000 4z"/>
                          <path fill-rule="evenodd" d="M.458 10C1.732 5.943 5.522 3 10 3s8.268 2.943 9.542 7c-1.274 4.057-5.064 7-9.542 7S1.732 14.057.458 10zM14 10a4 4 0 11-8 0 4 4 0 018 0z" clip-rule="evenodd"/>
                        </svg>
                        {{ post.view_count }}
                      </span>
                    </div>
                  </div>
                  <!-- 悬停边框 -->
                  <div class="absolute inset-0 border-2 border-white/0 group-hover:border-violet-400/50 rounded-2xl transition-colors duration-300"></div>
                </router-link>
              </div>
            </div>
            
            <!-- 所有文章 -->
            <div>
              <div v-if="featuredPosts.length > 0 && !selectedTag && !searchQuery" class="scroll-reveal flex items-center gap-3 mb-8">
                <div class="w-1 h-8 bg-gradient-to-b from-violet-500 to-fuchsia-600 rounded-full"></div>
                <h2 :class="['text-2xl font-bold', isDarkTheme ? 'text-white' : 'text-slate-800']">最新文章</h2>
              </div>
              
              <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                <router-link
                  v-for="(post, index) in (selectedTag || searchQuery ? posts : regularPosts)"
                  :key="post.id"
                  :to="`/blog/${post.slug}`"
                  :class="[
                    'scroll-reveal group rounded-2xl overflow-hidden border transition-all duration-500 hover:-translate-y-2 hover:shadow-2xl',
                    isDarkTheme 
                      ? 'bg-[#16161f] border-white/5 hover:border-violet-500/30 hover:shadow-violet-500/10' 
                      : 'bg-white border-slate-200/50 hover:border-violet-300 hover:shadow-violet-200/50 shadow-lg'
                  ]"
                  :style="{ transitionDelay: `${index * 80}ms` }"
                >
                  <!-- 封面图 -->
                  <div class="aspect-[16/10] relative overflow-hidden">
                    <div 
                      v-if="!post.cover_image"
                      class="absolute inset-0 bg-gradient-to-br opacity-90"
                      :class="getDefaultCover(index)"
                    >
                      <div class="absolute inset-0 flex items-center justify-center">
                        <svg class="w-16 h-16 text-white/30" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                        </svg>
                      </div>
                    </div>
                    <img 
                      v-else
                      :src="post.cover_image"
                      :alt="post.title"
                      class="w-full h-full object-cover group-hover:scale-105 transition-transform duration-700"
                    />
                    <!-- 阅读时间 -->
                    <div class="absolute top-4 right-4 px-3 py-1.5 bg-black/60 backdrop-blur-md rounded-full text-white text-xs font-medium">
                      {{ post.reading_time }} min
                    </div>
                  </div>
                  
                  <!-- 内容 -->
                  <div class="p-5">
                    <!-- 标签 -->
                    <div class="flex flex-wrap gap-2 mb-3">
                      <span
                        v-for="tag in post.tags?.slice(0, 3)"
                        :key="tag.id"
                        class="px-2.5 py-1 rounded-lg text-xs font-medium transition-colors"
                        :style="{ 
                          backgroundColor: tag.color + '20', 
                          color: tag.color,
                        }"
                      >
                        {{ tag.name }}
                      </span>
                    </div>
                    
                    <h3 :class="['text-lg font-bold mb-2 transition-colors line-clamp-2', isDarkTheme ? 'text-white group-hover:text-violet-300' : 'text-slate-800 group-hover:text-violet-600']">
                      {{ post.title }}
                    </h3>
                    
                    <p :class="['text-sm line-clamp-2 mb-4 leading-relaxed', isDarkTheme ? 'text-slate-500' : 'text-slate-600']">
                      {{ post.summary || '暂无摘要' }}
                    </p>
                    
                    <!-- 底部信息 -->
                    <div :class="['flex items-center justify-between pt-4 border-t', isDarkTheme ? 'border-white/5' : 'border-slate-100']">
                      <span :class="['text-sm', isDarkTheme ? 'text-slate-500' : 'text-slate-500']">{{ formatDate(post.published_at || post.created_at) }}</span>
                      <div class="flex items-center gap-1.5 text-sm text-slate-500">
                        <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                          <path d="M10 12a2 2 0 100-4 2 2 0 000 4z"/>
                          <path fill-rule="evenodd" d="M.458 10C1.732 5.943 5.522 3 10 3s8.268 2.943 9.542 7c-1.274 4.057-5.064 7-9.542 7S1.732 14.057.458 10zM14 10a4 4 0 11-8 0 4 4 0 018 0z" clip-rule="evenodd"/>
                        </svg>
                        {{ post.view_count }}
                      </div>
                    </div>
                  </div>
                </router-link>
              </div>
            </div>
          </div>
          
          <!-- 空状态 -->
          <div v-else class="text-center py-20">
            <div :class="[
              'inline-flex items-center justify-center w-20 h-20 rounded-full mb-6 border',
              isDarkTheme ? 'bg-gradient-to-br from-slate-800 to-slate-900 border-white/10' : 'bg-gradient-to-br from-slate-100 to-slate-200 border-slate-300'
            ]">
              <svg :class="['w-10 h-10', isDarkTheme ? 'text-slate-600' : 'text-slate-400']" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
            </div>
            <h3 :class="['text-xl font-bold mb-2', isDarkTheme ? 'text-white' : 'text-slate-700']">暂无文章</h3>
            <p :class="isDarkTheme ? 'text-slate-500' : 'text-slate-500'">
              {{ searchQuery ? '没有找到匹配的文章，试试其他关键词？' : '博主还没有发布任何文章，敬请期待！' }}
            </p>
          </div>
        </div>
      </div>
    </main>
    
    <!-- 独立页脚 -->
    <footer :class="[
      'border-t transition-colors duration-500',
      isDarkTheme ? 'bg-[#08080c] border-white/5' : 'bg-slate-50 border-slate-200'
    ]">
      <div class="container mx-auto px-4 py-8">
        <div :class="['flex flex-col md:flex-row items-center justify-between gap-4 text-sm', isDarkTheme ? 'text-slate-500' : 'text-slate-500']">
          <!-- 左侧：品牌 -->
          <div class="flex items-center gap-3">
            <div class="w-8 h-8 rounded-lg bg-gradient-to-br from-violet-500 to-fuchsia-500 flex items-center justify-center text-white font-bold text-sm">
              L
            </div>
            <span :class="isDarkTheme ? 'text-slate-400' : 'text-slate-600'">© 2025 LZQ's Tech Blog</span>
          </div>
          
          <!-- 右侧：GitHub + 技术栈 -->
          <div class="flex items-center gap-4">
            <a 
              href="https://github.com/linzhiqin2003" 
              target="_blank"
              :class="['flex items-center gap-2 transition-colors', isDarkTheme ? 'text-slate-500 hover:text-violet-400' : 'text-slate-500 hover:text-violet-600']"
            >
              <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 24 24">
                <path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"/>
              </svg>
              <span class="hidden sm:inline">GitHub</span>
            </a>
            <span :class="isDarkTheme ? 'text-slate-700' : 'text-slate-300'">·</span>
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
.line-clamp-2 {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

/* 滚动浮现动画 */
.scroll-reveal {
  opacity: 0;
  transform: translateY(40px) scale(0.95);
  transition: all 0.7s cubic-bezier(0.16, 1, 0.3, 1);
}

.scroll-reveal.revealed {
  opacity: 1;
  transform: translateY(0) scale(1);
}

/* 动画 */
@keyframes fade-in {
  from { opacity: 0; }
  to { opacity: 1; }
}

@keyframes fade-in-up {
  from { 
    opacity: 0; 
    transform: translateY(20px);
  }
  to { 
    opacity: 1; 
    transform: translateY(0);
  }
}

@keyframes pulse-slow {
  0%, 100% { opacity: 0.3; transform: scale(1); }
  50% { opacity: 0.5; transform: scale(1.05); }
}

.animate-fade-in {
  animation: fade-in 0.6s ease-out forwards;
}

.animate-fade-in-up {
  animation: fade-in-up 0.6s ease-out forwards;
}

.animate-pulse-slow {
  animation: pulse-slow 8s ease-in-out infinite;
}

.animation-delay-200 {
  animation-delay: 200ms;
}

.animation-delay-400 {
  animation-delay: 400ms;
}

.animation-delay-2000 {
  animation-delay: 2000ms;
}

/* 星星背景 */
.stars {
  position: absolute;
  width: 100%;
  height: 100%;
  background-image: 
    radial-gradient(2px 2px at 20px 30px, white, transparent),
    radial-gradient(2px 2px at 40px 70px, rgba(255,255,255,0.8), transparent),
    radial-gradient(1px 1px at 90px 40px, white, transparent),
    radial-gradient(2px 2px at 160px 120px, rgba(255,255,255,0.6), transparent),
    radial-gradient(1px 1px at 230px 80px, white, transparent),
    radial-gradient(2px 2px at 300px 150px, rgba(255,255,255,0.7), transparent),
    radial-gradient(1px 1px at 370px 50px, white, transparent),
    radial-gradient(2px 2px at 450px 180px, rgba(255,255,255,0.5), transparent),
    radial-gradient(1px 1px at 520px 100px, white, transparent),
    radial-gradient(2px 2px at 600px 60px, rgba(255,255,255,0.8), transparent);
  background-size: 650px 200px;
  animation: twinkle 5s ease-in-out infinite;
}

@keyframes twinkle {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}
</style>
