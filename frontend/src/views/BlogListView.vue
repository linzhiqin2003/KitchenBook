<script setup>
import { ref, onMounted, computed } from 'vue'
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
  <div class="min-h-screen bg-gradient-to-b from-slate-50 to-white">
    <!-- 博客头部 Hero Section -->
    <div class="relative overflow-hidden -mx-4 md:-mx-6 lg:-mx-8 -mt-4 md:-mt-6 lg:-mt-8">
      <!-- 背景 -->
      <div class="absolute inset-0 bg-[#0f0a1f]">
        <!-- 渐变光晕 -->
        <div class="absolute top-0 left-1/4 w-[500px] h-[500px] bg-purple-600/30 rounded-full blur-[120px] animate-pulse-slow"></div>
        <div class="absolute bottom-0 right-1/4 w-[400px] h-[400px] bg-blue-600/20 rounded-full blur-[100px] animate-pulse-slow animation-delay-2000"></div>
        <div class="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-indigo-600/10 rounded-full blur-[150px]"></div>
        <!-- 星星点缀 -->
        <div class="absolute inset-0 overflow-hidden">
          <div class="stars"></div>
        </div>
        <!-- 网格 -->
        <div class="absolute inset-0 bg-[linear-gradient(rgba(255,255,255,0.03)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,0.03)_1px,transparent_1px)] bg-[size:50px_50px]"></div>
      </div>
      
      <div class="relative px-4 md:px-6 lg:px-8 py-20 md:py-32">
        <div class="container mx-auto text-center">
          <!-- 状态标签 -->
          <div class="inline-flex items-center gap-2 px-5 py-2.5 rounded-full bg-white/5 backdrop-blur-md border border-white/10 text-sm mb-8 animate-fade-in">
            <span class="relative flex h-2 w-2">
              <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
              <span class="relative inline-flex rounded-full h-2 w-2 bg-green-500"></span>
            </span>
            <span class="text-slate-300">技术分享 · 持续更新中</span>
          </div>
          
          <!-- 标题 -->
          <h1 class="text-5xl md:text-7xl font-bold mb-6 animate-fade-in-up">
            <span class="bg-gradient-to-r from-white via-purple-200 to-blue-200 bg-clip-text text-transparent">
              技术博客
            </span>
          </h1>
          
          <!-- 副标题 -->
          <p class="text-lg md:text-xl text-slate-400 max-w-2xl mx-auto mb-12 leading-relaxed animate-fade-in-up animation-delay-200">
            记录学习历程，分享技术心得<br class="hidden md:block">
            探索编程世界的无限可能
          </p>
          
          <!-- 统计信息 -->
          <div class="flex justify-center gap-6 md:gap-12 animate-fade-in-up animation-delay-400">
            <div class="group">
              <div class="relative">
                <div class="absolute inset-0 bg-gradient-to-r from-purple-500 to-pink-500 rounded-2xl blur-lg opacity-50 group-hover:opacity-75 transition-opacity"></div>
                <div class="relative bg-white/10 backdrop-blur-md rounded-2xl px-6 md:px-8 py-4 md:py-5 border border-white/10">
                  <div class="text-3xl md:text-4xl font-bold text-white mb-1">{{ stats.total_posts }}</div>
                  <div class="text-xs md:text-sm text-slate-400 uppercase tracking-wider">篇文章</div>
                </div>
              </div>
            </div>
            <div class="group">
              <div class="relative">
                <div class="absolute inset-0 bg-gradient-to-r from-blue-500 to-cyan-500 rounded-2xl blur-lg opacity-50 group-hover:opacity-75 transition-opacity"></div>
                <div class="relative bg-white/10 backdrop-blur-md rounded-2xl px-6 md:px-8 py-4 md:py-5 border border-white/10">
                  <div class="text-3xl md:text-4xl font-bold text-white mb-1">{{ stats.total_views }}</div>
                  <div class="text-xs md:text-sm text-slate-400 uppercase tracking-wider">次阅读</div>
                </div>
              </div>
            </div>
            <div class="group">
              <div class="relative">
                <div class="absolute inset-0 bg-gradient-to-r from-emerald-500 to-teal-500 rounded-2xl blur-lg opacity-50 group-hover:opacity-75 transition-opacity"></div>
                <div class="relative bg-white/10 backdrop-blur-md rounded-2xl px-6 md:px-8 py-4 md:py-5 border border-white/10">
                  <div class="text-3xl md:text-4xl font-bold text-white mb-1">{{ stats.total_tags }}</div>
                  <div class="text-xs md:text-sm text-slate-400 uppercase tracking-wider">个标签</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
      
      <!-- 底部波浪 -->
      <div class="absolute bottom-0 left-0 right-0">
        <svg viewBox="0 0 1440 120" fill="none" xmlns="http://www.w3.org/2000/svg" class="w-full h-auto">
          <path d="M0 120L60 110C120 100 240 80 360 70C480 60 600 60 720 65C840 70 960 80 1080 85C1200 90 1320 90 1380 90L1440 90V120H1380C1320 120 1200 120 1080 120C960 120 840 120 720 120C600 120 480 120 360 120C240 120 120 120 60 120H0Z" fill="#f8fafc"/>
        </svg>
      </div>
    </div>
    
    <!-- 搜索和筛选区域 -->
    <div class="container mx-auto px-4 py-8 -mt-4">
      <div class="bg-white rounded-2xl shadow-xl shadow-slate-200/50 border border-slate-100 p-4 md:p-6 mb-10">
        <div class="flex flex-col md:flex-row gap-4 items-center justify-between">
          <!-- 搜索框 -->
          <div class="relative w-full md:w-auto md:flex-1 md:max-w-md">
            <input
              v-model="searchQuery"
              @keyup.enter="handleSearch"
              type="text"
              placeholder="搜索文章标题或内容..."
              class="w-full pl-12 pr-24 py-3.5 bg-slate-50 border-0 rounded-xl focus:outline-none focus:ring-2 focus:ring-purple-500/50 focus:bg-white transition-all text-slate-700 placeholder-slate-400"
            />
            <svg class="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
            <button 
              @click="handleSearch"
              class="absolute right-2 top-1/2 -translate-y-1/2 px-4 py-2 bg-gradient-to-r from-purple-600 to-indigo-600 text-white text-sm font-medium rounded-lg hover:shadow-lg hover:shadow-purple-500/25 transition-all"
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
                  ? 'bg-gradient-to-r from-purple-600 to-indigo-600 text-white shadow-lg shadow-purple-500/25' 
                  : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
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
                  : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
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
      
      <!-- 加载状态 -->
      <div v-if="loading" class="flex flex-col justify-center items-center py-20">
        <div class="relative w-16 h-16">
          <div class="absolute inset-0 border-4 border-purple-200 rounded-full"></div>
          <div class="absolute inset-0 border-4 border-purple-600 rounded-full border-t-transparent animate-spin"></div>
        </div>
        <p class="mt-4 text-slate-500">加载中...</p>
      </div>
      
      <!-- 文章列表 -->
      <div v-else-if="posts.length > 0">
        <!-- 精选文章 -->
        <div v-if="featuredPosts.length > 0 && !selectedTag && !searchQuery" class="mb-14">
          <div class="flex items-center gap-3 mb-8">
            <div class="w-1 h-8 bg-gradient-to-b from-yellow-400 to-orange-500 rounded-full"></div>
            <h2 class="text-2xl font-bold text-slate-800">精选推荐</h2>
          </div>
          <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
            <router-link
              v-for="(post, index) in featuredPosts"
              :key="post.id"
              :to="`/blog/${post.slug}`"
              class="group relative overflow-hidden rounded-2xl aspect-[4/3] cursor-pointer"
              :style="{ animationDelay: `${index * 100}ms` }"
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
                <h3 class="text-xl font-bold text-white mb-2 group-hover:text-purple-200 transition-colors line-clamp-2">
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
              <div class="absolute inset-0 border-2 border-white/0 group-hover:border-white/30 rounded-2xl transition-colors duration-300"></div>
            </router-link>
          </div>
        </div>
        
        <!-- 所有文章 -->
        <div>
          <div v-if="featuredPosts.length > 0 && !selectedTag && !searchQuery" class="flex items-center gap-3 mb-8">
            <div class="w-1 h-8 bg-gradient-to-b from-purple-500 to-indigo-600 rounded-full"></div>
            <h2 class="text-2xl font-bold text-slate-800">最新文章</h2>
          </div>
          
          <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            <router-link
              v-for="(post, index) in (selectedTag || searchQuery ? posts : regularPosts)"
              :key="post.id"
              :to="`/blog/${post.slug}`"
              class="group bg-white rounded-2xl overflow-hidden shadow-sm hover:shadow-2xl hover:shadow-purple-500/10 border border-slate-100 transition-all duration-500 hover:-translate-y-2 animate-fade-in-up"
              :style="{ animationDelay: `${index * 50}ms` }"
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
                      backgroundColor: tag.color + '15', 
                      color: tag.color,
                    }"
                  >
                    {{ tag.name }}
                  </span>
                </div>
                
                <h3 class="text-lg font-bold text-slate-800 mb-2 group-hover:text-purple-600 transition-colors line-clamp-2">
                  {{ post.title }}
                </h3>
                
                <p class="text-sm text-slate-500 line-clamp-2 mb-4 leading-relaxed">
                  {{ post.summary || '暂无摘要' }}
                </p>
                
                <!-- 底部信息 -->
                <div class="flex items-center justify-between pt-4 border-t border-slate-100">
                  <span class="text-sm text-slate-400">{{ formatDate(post.published_at || post.created_at) }}</span>
                  <div class="flex items-center gap-1.5 text-sm text-slate-400">
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
        <div class="inline-flex items-center justify-center w-20 h-20 bg-gradient-to-br from-slate-100 to-slate-200 rounded-full mb-6">
          <svg class="w-10 h-10 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
        </div>
        <h3 class="text-xl font-bold text-slate-700 mb-2">暂无文章</h3>
        <p class="text-slate-500">
          {{ searchQuery ? '没有找到匹配的文章，试试其他关键词？' : '博主还没有发布任何文章，敬请期待！' }}
        </p>
      </div>
    </div>
  </div>
</template>

<style scoped>
.line-clamp-2 {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
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
