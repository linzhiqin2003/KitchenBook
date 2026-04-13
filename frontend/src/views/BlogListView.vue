<script setup>
import { ref, onMounted, computed, onUnmounted, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'
import API_BASE_URL from '../config/api'

const router = useRouter()
const posts = ref([])
const tags = ref([])
const categories = ref([])
const stats = ref({ total_posts: 0, total_views: 0, total_tags: 0 })
const loading = ref(true)
const selectedCategory = ref('')
const searchQuery = ref('')
const viewMode = ref(localStorage.getItem('blog_view_mode') || 'card')

const setViewMode = (mode) => {
  viewMode.value = mode
  localStorage.setItem('blog_view_mode', mode)
  setupScrollAnimation()
}

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
    
    if (selectedCategory.value) {
      params.append('category', selectedCategory.value)
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

// 获取分类列表
const fetchCategories = async () => {
  try {
    const response = await axios.get(`${API_BASE_URL}/api/blog/categories/`)
    categories.value = response.data
  } catch (error) {
    console.error('Failed to fetch categories', error)
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
  fetchCategories()
  fetchStats()
})

// 打开/关闭文件夹
const openCategory = (slug) => {
  selectedCategory.value = slug
  fetchPosts()
}

const closeCategory = () => {
  selectedCategory.value = ''
  fetchPosts()
}

// 搜索后也要重建动画
const handleSearchAndAnimate = () => {
  handleSearch()
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

// 精选文章（仅在未打开文件夹时显示）
const featuredPosts = computed(() => posts.value.filter(p => p.is_featured).slice(0, 3))
const regularPosts = computed(() => posts.value.filter(p => !p.is_featured || featuredPosts.value.length === 0))

// 当前打开的文件夹信息
const currentCategory = computed(() => categories.value.find(c => c.slug === selectedCategory.value))

// 未归类文章
const uncategorizedPosts = computed(() => posts.value.filter(p => !p.category))
</script>

<template>
  <div :class="[
    'min-h-screen font-sans transition-colors duration-500',
    isDarkTheme ? 'bg-[#0a0a0f] text-slate-100' : 'bg-[#faf8f0] text-slate-800'
  ]">
    <!-- 独立导航栏 -->
    <header :class="[
      'fixed top-0 left-0 right-0 z-50 backdrop-blur-xl border-b transition-colors duration-500',
      isDarkTheme ? 'bg-[#0a0a0f]/80 border-white/5' : 'bg-[#faf8f0]/90 border-amber-200/30'
    ]">
      <div class="container mx-auto px-4 md:px-6">
        <div class="flex items-center justify-between h-16 md:h-20">
          <!-- Left: Back Button + Logo -->
          <div class="flex items-center gap-3">
            <!-- 返回主页 -->
            <router-link 
              to="/" 
              :class="[
                'w-9 h-9 rounded-lg flex items-center justify-center transition-all group',
                isDarkTheme ? 'bg-white/10 hover:bg-white/20 text-slate-400 hover:text-white' : 'bg-gray-100 hover:bg-gray-200 text-gray-500 hover:text-violet-600'
              ]"
              title="返回首页"
            >
              <svg class="w-4 h-4 group-hover:-translate-x-0.5 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 19l-7-7m0 0l7-7m-7 7h18"/>
              </svg>
            </router-link>
            
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
          </div>
          
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
              to="/ai-lab" 
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
        <div v-else class="absolute inset-0 bg-gradient-to-br from-[#f5f0e0] via-[#faf8f0] to-[#f0ebe0]">
          <!-- 渐变光晕 -->
          <div class="absolute top-0 left-1/4 w-[500px] h-[500px] bg-violet-300/30 rounded-full blur-[120px]"></div>
          <div class="absolute bottom-0 right-1/4 w-[400px] h-[400px] bg-fuchsia-300/20 rounded-full blur-[100px]"></div>
          <div class="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-blue-200/20 rounded-full blur-[150px]"></div>
          <!-- 网格 -->
          <div class="absolute inset-0 bg-[linear-gradient(rgba(139,92,246,0.05)_1px,transparent_1px),linear-gradient(90deg,rgba(139,92,246,0.05)_1px,transparent_1px)] bg-[size:60px_60px]"></div>
        </div>
        
        <div class="relative px-4 md:px-6 lg:px-8 py-20 md:py-32">
          <div class="container mx-auto text-center">
            <!-- 副品牌 -->
            <div :class="['text-sm tracking-[0.3em] uppercase mb-8 animate-fade-in', isDarkTheme ? 'text-slate-500' : 'text-amber-700/60']">
              Code · Think · Share
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
      

      <!-- 内容区域 -->
      <div :class="['min-h-[50vh] transition-colors duration-500', isDarkTheme ? 'bg-[#0f0f15]' : 'bg-[#f7f4ea]']">
        <div class="container mx-auto px-4 py-12">
          <!-- 加载状态 -->
          <div v-if="loading" class="flex flex-col justify-center items-center py-20">
            <div class="relative w-16 h-16">
              <div :class="['absolute inset-0 border-4 rounded-full', isDarkTheme ? 'border-violet-500/20' : 'border-violet-300']"></div>
              <div class="absolute inset-0 border-4 border-violet-500 rounded-full border-t-transparent animate-spin"></div>
            </div>
            <p :class="['mt-4', isDarkTheme ? 'text-slate-500' : 'text-slate-600']">加载中...</p>
          </div>

          <template v-else>
            <!-- ======== 文件夹视图（未打开任何文件夹） ======== -->
            <div v-if="!selectedCategory && !searchQuery">
              <!-- 搜索栏 -->
              <div class="scroll-reveal mb-10 max-w-lg mx-auto">
                <div class="relative">
                  <input
                    v-model="searchQuery"
                    @keyup.enter="handleSearch"
                    type="text"
                    placeholder="搜索文章..."
                    :class="[
                      'w-full pl-11 pr-4 py-3 border rounded-xl focus:outline-none focus:ring-2 focus:ring-violet-500/50 transition-all text-sm',
                      isDarkTheme
                        ? 'bg-white/5 border-white/10 text-white placeholder-slate-500'
                        : 'bg-[#faf7ef] border-amber-200/40 text-slate-800 placeholder-slate-400 shadow-sm'
                    ]"
                  />
                  <svg class="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                  </svg>
                </div>
              </div>

              <!-- 文件夹网格 -->
              <div class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-5 md:gap-6">
                <button
                  v-for="cat in categories"
                  :key="cat.id"
                  @click="openCategory(cat.slug)"
                  :class="[
                    'group flex flex-col items-center gap-3 p-6 rounded-2xl transition-all duration-300 cursor-pointer',
                    isDarkTheme
                      ? 'bg-white/[0.03] hover:bg-white/[0.08] border border-white/5 hover:border-white/15'
                      : 'bg-[#faf7ef] hover:bg-amber-50 border border-amber-200/40 hover:border-amber-300 shadow-sm hover:shadow-lg'
                  ]"
                >
                  <div class="w-16 h-16 rounded-2xl flex items-center justify-center text-3xl transition-all duration-300 group-hover:scale-110 group-hover:-translate-y-1"
                    :style="{ background: `linear-gradient(135deg, ${cat.color}15, ${cat.color}30)` }">
                    {{ cat.icon }}
                  </div>
                  <span :class="[
                    'text-sm font-medium text-center leading-tight transition-colors',
                    isDarkTheme ? 'text-slate-300 group-hover:text-white' : 'text-slate-700 group-hover:text-violet-700'
                  ]">
                    {{ cat.name }}
                  </span>
                  <span :class="[
                    'text-xs px-2.5 py-0.5 rounded-full',
                    isDarkTheme ? 'bg-white/5 text-slate-500' : 'bg-slate-100 text-slate-500'
                  ]">
                    {{ cat.post_count }} 篇
                  </span>
                </button>
              </div>

              <!-- 精选文章 -->
              <div v-if="featuredPosts.length > 0" class="mt-14">
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
                    <div class="absolute inset-0 bg-gradient-to-br transition-transform duration-500 group-hover:scale-110" :class="post.cover_image ? '' : getDefaultCover(index)">
                      <img v-if="post.cover_image" :src="post.cover_image" :alt="post.title" class="w-full h-full object-cover" />
                    </div>
                    <div class="absolute inset-0 bg-gradient-to-t from-black/80 via-black/40 to-transparent"></div>
                    <div class="absolute inset-0 p-6 flex flex-col justify-end">
                      <h3 class="text-xl font-bold text-white mb-2 group-hover:text-violet-200 transition-colors line-clamp-2">{{ post.title }}</h3>
                      <div class="flex items-center justify-between text-sm text-white/60">
                        <span>{{ formatDate(post.published_at || post.created_at) }}</span>
                        <span class="flex items-center gap-1">
                          <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20"><path d="M10 12a2 2 0 100-4 2 2 0 000 4z"/><path fill-rule="evenodd" d="M.458 10C1.732 5.943 5.522 3 10 3s8.268 2.943 9.542 7c-1.274 4.057-5.064 7-9.542 7S1.732 14.057.458 10zM14 10a4 4 0 11-8 0 4 4 0 018 0z" clip-rule="evenodd"/></svg>
                          {{ post.view_count }}
                        </span>
                      </div>
                    </div>
                    <div class="absolute inset-0 border-2 border-white/0 group-hover:border-violet-400/50 rounded-2xl transition-colors duration-300"></div>
                  </router-link>
                </div>
              </div>
            </div>

            <!-- ======== 打开了文件夹 / 搜索结果 ======== -->
            <div v-else>
              <!-- 面包屑 + 视图切换 -->
              <div class="scroll-reveal flex items-center justify-between mb-8">
                <div class="flex items-center gap-3">
                  <button @click="closeCategory(); searchQuery = ''"
                    :class="['w-9 h-9 rounded-lg flex items-center justify-center transition-all group', isDarkTheme ? 'bg-white/10 hover:bg-white/20 text-slate-400 hover:text-white' : 'bg-slate-200 hover:bg-slate-300 text-slate-500 hover:text-slate-700']">
                    <svg class="w-4 h-4 group-hover:-translate-x-0.5 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 19l-7-7m0 0l7-7m-7 7h18"/></svg>
                  </button>
                  <div class="w-1 h-8 bg-gradient-to-b from-violet-400 to-indigo-500 rounded-full"></div>
                  <h2 :class="['text-2xl font-bold', isDarkTheme ? 'text-white' : 'text-slate-800']">
                    {{ searchQuery ? `搜索: "${searchQuery}"` : currentCategory?.name || '' }}
                  </h2>
                  <span :class="['text-sm', isDarkTheme ? 'text-slate-500' : 'text-slate-400']">{{ posts.length }} 篇</span>
                </div>
                <div :class="['flex rounded-lg overflow-hidden border', isDarkTheme ? 'border-white/10' : 'border-slate-200']">
                  <button @click="setViewMode('card')" :class="['px-3 py-2 transition-colors', viewMode === 'card' ? 'bg-violet-600 text-white' : isDarkTheme ? 'bg-white/5 text-slate-400 hover:text-white' : 'bg-[#faf7ef] text-slate-500 hover:text-slate-700']" title="卡片视图">
                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2V6zm10 0a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V6zM4 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2v-2zm10 0a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z"/></svg>
                  </button>
                  <button @click="setViewMode('list')" :class="['px-3 py-2 transition-colors', viewMode === 'list' ? 'bg-violet-600 text-white' : isDarkTheme ? 'bg-white/5 text-slate-400 hover:text-white' : 'bg-[#faf7ef] text-slate-500 hover:text-slate-700']" title="列表视图">
                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16"/></svg>
                  </button>
                </div>
              </div>

              <div v-if="posts.length > 0">
                <!-- 卡片视图 -->
                <div v-if="viewMode === 'card'" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                  <router-link v-for="(post, index) in posts" :key="post.id" :to="`/blog/${post.slug}`"
                    :class="['scroll-reveal group rounded-2xl overflow-hidden border transition-all duration-500 hover:-translate-y-2 hover:shadow-2xl', isDarkTheme ? 'bg-[#16161f] border-white/5 hover:border-violet-500/30 hover:shadow-violet-500/10' : 'bg-[#faf7ef] border-amber-200/40 hover:border-amber-300 hover:shadow-amber-200/50 shadow-md']"
                    :style="{ transitionDelay: `${index * 80}ms` }">
                    <div class="aspect-[16/10] relative overflow-hidden">
                      <div v-if="!post.cover_image" class="absolute inset-0 bg-gradient-to-br opacity-90" :class="getDefaultCover(index)">
                        <div class="absolute inset-0 flex items-center justify-center">
                          <svg class="w-16 h-16 text-white/30" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/></svg>
                        </div>
                      </div>
                      <img v-else :src="post.cover_image" :alt="post.title" class="w-full h-full object-cover group-hover:scale-105 transition-transform duration-700" />
                      <div class="absolute top-4 right-4 px-3 py-1.5 bg-black/60 backdrop-blur-md rounded-full text-white text-xs font-medium">{{ post.reading_time }} min</div>
                    </div>
                    <div class="p-5">
                      <h3 :class="['text-lg font-bold mb-2 transition-colors line-clamp-2', isDarkTheme ? 'text-white group-hover:text-violet-300' : 'text-slate-800 group-hover:text-violet-600']">{{ post.title }}</h3>
                      <p :class="['text-sm line-clamp-2 mb-4 leading-relaxed', isDarkTheme ? 'text-slate-500' : 'text-slate-600']">{{ post.summary || '暂无摘要' }}</p>
                      <div :class="['flex items-center justify-between pt-4 border-t', isDarkTheme ? 'border-white/5' : 'border-slate-100']">
                        <span :class="['text-sm', 'text-slate-500']">{{ formatDate(post.published_at || post.created_at) }}</span>
                        <div class="flex items-center gap-1.5 text-sm text-slate-500">
                          <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20"><path d="M10 12a2 2 0 100-4 2 2 0 000 4z"/><path fill-rule="evenodd" d="M.458 10C1.732 5.943 5.522 3 10 3s8.268 2.943 9.542 7c-1.274 4.057-5.064 7-9.542 7S1.732 14.057.458 10zM14 10a4 4 0 11-8 0 4 4 0 018 0z" clip-rule="evenodd"/></svg>
                          {{ post.view_count }}
                        </div>
                      </div>
                    </div>
                  </router-link>
                </div>

                <!-- 列表视图 -->
                <div v-else class="flex flex-col gap-3">
                  <router-link v-for="(post, index) in posts" :key="post.id" :to="`/blog/${post.slug}`"
                    :class="['scroll-reveal group flex items-center gap-5 p-4 rounded-xl border transition-all duration-300 hover:shadow-lg', isDarkTheme ? 'bg-[#16161f] border-white/5 hover:border-violet-500/30 hover:bg-[#1a1a25]' : 'bg-[#faf7ef] border-amber-200/40 hover:border-amber-300 shadow-sm']"
                    :style="{ transitionDelay: `${index * 50}ms` }">
                    <div :class="['text-2xl font-bold w-8 text-center shrink-0', isDarkTheme ? 'text-white/10' : 'text-slate-200']">{{ String(index + 1).padStart(2, '0') }}</div>
                    <div class="flex-1 min-w-0">
                      <h3 :class="['font-bold transition-colors truncate', isDarkTheme ? 'text-slate-200 group-hover:text-violet-300' : 'text-slate-800 group-hover:text-violet-600']">{{ post.title }}</h3>
                      <p :class="['text-sm truncate mt-1', isDarkTheme ? 'text-slate-500' : 'text-slate-500']">{{ post.summary || '暂无摘要' }}</p>
                    </div>
                    <div class="hidden sm:flex items-center gap-4 shrink-0 text-sm text-slate-500">
                      <span>{{ post.reading_time }} min</span>
                      <span class="flex items-center gap-1">
                        <svg class="w-3.5 h-3.5" fill="currentColor" viewBox="0 0 20 20"><path d="M10 12a2 2 0 100-4 2 2 0 000 4z"/><path fill-rule="evenodd" d="M.458 10C1.732 5.943 5.522 3 10 3s8.268 2.943 9.542 7c-1.274 4.057-5.064 7-9.542 7S1.732 14.057.458 10zM14 10a4 4 0 11-8 0 4 4 0 018 0z" clip-rule="evenodd"/></svg>
                        {{ post.view_count }}
                      </span>
                      <span>{{ formatDate(post.published_at || post.created_at) }}</span>
                    </div>
                    <svg :class="['w-4 h-4 shrink-0 transition-transform group-hover:translate-x-1', isDarkTheme ? 'text-slate-600' : 'text-slate-400']" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"/></svg>
                  </router-link>
                </div>
              </div>

              <!-- 空状态 -->
              <div v-else class="text-center py-20">
                <h3 :class="['text-xl font-bold mb-2', isDarkTheme ? 'text-white' : 'text-slate-700']">暂无文章</h3>
                <p :class="isDarkTheme ? 'text-slate-500' : 'text-slate-500'">{{ searchQuery ? '没有找到匹配的文章' : '这个分类还没有文章' }}</p>
              </div>
            </div>
          </template>
        </div>
      </div>
    </main>
    
    <!-- 独立页脚 -->
    <footer :class="[
      'border-t transition-colors duration-500',
      isDarkTheme ? 'bg-[#08080c] border-white/5' : 'bg-[#f0ebe0] border-amber-200/30'
    ]">
      <div class="container mx-auto px-4 py-8">
        <div :class="['flex flex-col md:flex-row items-center justify-between gap-4 text-sm', isDarkTheme ? 'text-slate-500' : 'text-slate-500']">
          <!-- 左侧：品牌 -->
          <div class="flex items-center gap-3">
            <div class="w-8 h-8 rounded-lg bg-gradient-to-br from-violet-500 to-fuchsia-500 flex items-center justify-center text-white font-bold text-sm">
              L
            </div>
            <span :class="isDarkTheme ? 'text-slate-400' : 'text-slate-600'">© 2026 LZQ's Tech Blog</span>
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
