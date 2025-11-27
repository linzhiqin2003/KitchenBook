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
    month: 'long',
    day: 'numeric'
  })
}

// 精选文章
const featuredPosts = computed(() => posts.value.filter(p => p.is_featured).slice(0, 3))
const regularPosts = computed(() => posts.value.filter(p => !p.is_featured || featuredPosts.value.length === 0))
</script>

<template>
  <div class="min-h-screen">
    <!-- 博客头部 Hero Section -->
    <div class="relative overflow-hidden bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 text-white -mx-4 md:-mx-6 lg:-mx-8 -mt-4 md:-mt-6 lg:-mt-8 px-4 md:px-6 lg:px-8 py-16 md:py-24">
      <!-- 装饰背景 -->
      <div class="absolute inset-0 overflow-hidden">
        <div class="absolute -top-40 -right-40 w-80 h-80 bg-purple-500/20 rounded-full blur-3xl"></div>
        <div class="absolute -bottom-40 -left-40 w-80 h-80 bg-blue-500/20 rounded-full blur-3xl"></div>
        <div class="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-96 h-96 bg-indigo-500/10 rounded-full blur-3xl"></div>
        <!-- 网格背景 -->
        <div class="absolute inset-0 bg-[linear-gradient(rgba(255,255,255,0.02)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,0.02)_1px,transparent_1px)] bg-[size:60px_60px]"></div>
      </div>
      
      <div class="relative container mx-auto text-center">
        <div class="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-white/10 backdrop-blur-sm border border-white/20 text-sm mb-6">
          <span class="w-2 h-2 bg-green-400 rounded-full animate-pulse"></span>
          <span>技术分享 · 持续更新中</span>
        </div>
        
        <h1 class="text-4xl md:text-6xl font-bold mb-4 bg-gradient-to-r from-white via-purple-200 to-blue-200 bg-clip-text text-transparent">
          技术博客
        </h1>
        <p class="text-lg md:text-xl text-slate-300 max-w-2xl mx-auto mb-8 font-light">
          记录学习历程，分享技术心得，探索编程世界的无限可能
        </p>
        
        <!-- 统计信息 -->
        <div class="flex justify-center gap-8 md:gap-16 text-center">
          <div>
            <div class="text-3xl md:text-4xl font-bold text-white">{{ stats.total_posts }}</div>
            <div class="text-sm text-slate-400">篇文章</div>
          </div>
          <div>
            <div class="text-3xl md:text-4xl font-bold text-white">{{ stats.total_views }}</div>
            <div class="text-sm text-slate-400">次阅读</div>
          </div>
          <div>
            <div class="text-3xl md:text-4xl font-bold text-white">{{ stats.total_tags }}</div>
            <div class="text-sm text-slate-400">个标签</div>
          </div>
        </div>
      </div>
    </div>
    
    <!-- 搜索和筛选区域 -->
    <div class="container mx-auto py-8">
      <div class="flex flex-col md:flex-row gap-4 items-center justify-between mb-8">
        <!-- 搜索框 -->
        <div class="relative w-full md:w-96">
          <input
            v-model="searchQuery"
            @keyup.enter="handleSearch"
            type="text"
            placeholder="搜索文章..."
            class="w-full pl-12 pr-4 py-3 bg-white border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent shadow-sm transition-all"
          />
          <svg class="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
          </svg>
          <button 
            @click="handleSearch"
            class="absolute right-2 top-1/2 -translate-y-1/2 px-3 py-1.5 bg-purple-600 text-white text-sm rounded-lg hover:bg-purple-700 transition-colors"
          >
            搜索
          </button>
        </div>
        
        <!-- 标签筛选 -->
        <div class="flex flex-wrap gap-2 justify-center md:justify-end">
          <button
            @click="filterByTag('')"
            :class="[
              'px-4 py-2 rounded-full text-sm font-medium transition-all',
              !selectedTag ? 'bg-purple-600 text-white shadow-lg shadow-purple-500/30' : 'bg-white text-slate-600 border border-slate-200 hover:border-purple-300'
            ]"
          >
            全部
          </button>
          <button
            v-for="tag in tags"
            :key="tag.id"
            @click="filterByTag(tag.name)"
            :class="[
              'px-4 py-2 rounded-full text-sm font-medium transition-all flex items-center gap-1.5',
              selectedTag === tag.name ? 'text-white shadow-lg' : 'bg-white text-slate-600 border border-slate-200 hover:border-purple-300'
            ]"
            :style="selectedTag === tag.name ? { backgroundColor: tag.color, boxShadow: `0 10px 15px -3px ${tag.color}40` } : {}"
          >
            <span class="w-2 h-2 rounded-full" :style="{ backgroundColor: tag.color }"></span>
            {{ tag.name }}
            <span class="text-xs opacity-70">({{ tag.post_count }})</span>
          </button>
        </div>
      </div>
      
      <!-- 加载状态 -->
      <div v-if="loading" class="flex justify-center items-center py-20">
        <div class="w-12 h-12 border-4 border-purple-200 border-t-purple-600 rounded-full animate-spin"></div>
      </div>
      
      <!-- 文章列表 -->
      <div v-else-if="posts.length > 0">
        <!-- 精选文章 -->
        <div v-if="featuredPosts.length > 0 && !selectedTag && !searchQuery" class="mb-12">
          <h2 class="text-2xl font-bold text-slate-800 mb-6 flex items-center gap-2">
            <span class="text-yellow-500">⭐</span> 精选文章
          </h2>
          <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
            <router-link
              v-for="post in featuredPosts"
              :key="post.id"
              :to="`/blog/${post.slug}`"
              class="group relative overflow-hidden rounded-2xl bg-gradient-to-br from-purple-600 to-indigo-700 p-6 text-white shadow-xl hover:shadow-2xl hover:-translate-y-1 transition-all duration-300"
            >
              <div class="absolute inset-0 bg-black/20 group-hover:bg-black/10 transition-colors"></div>
              <div class="relative">
                <div class="flex gap-2 mb-4">
                  <span
                    v-for="tag in post.tags?.slice(0, 2)"
                    :key="tag.id"
                    class="px-2 py-1 bg-white/20 rounded-full text-xs backdrop-blur-sm"
                  >
                    {{ tag.name }}
                  </span>
                </div>
                <h3 class="text-xl font-bold mb-2 group-hover:underline decoration-2 underline-offset-4">{{ post.title }}</h3>
                <p class="text-sm text-white/80 line-clamp-2 mb-4">{{ post.summary }}</p>
                <div class="flex items-center justify-between text-sm text-white/60">
                  <span>{{ formatDate(post.published_at || post.created_at) }}</span>
                  <span class="flex items-center gap-1">
                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                    </svg>
                    {{ post.view_count }}
                  </span>
                </div>
              </div>
            </router-link>
          </div>
        </div>
        
        <!-- 所有文章 -->
        <div>
          <h2 v-if="featuredPosts.length > 0 && !selectedTag && !searchQuery" class="text-2xl font-bold text-slate-800 mb-6 flex items-center gap-2">
            <span>📚</span> 所有文章
          </h2>
          
          <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            <router-link
              v-for="post in (selectedTag || searchQuery ? posts : regularPosts)"
              :key="post.id"
              :to="`/blog/${post.slug}`"
              class="group bg-white rounded-2xl overflow-hidden shadow-sm hover:shadow-xl border border-slate-100 hover:border-purple-200 transition-all duration-300 hover:-translate-y-1"
            >
              <!-- 封面图 -->
              <div class="aspect-video bg-gradient-to-br from-slate-100 to-slate-200 relative overflow-hidden">
                <img 
                  v-if="post.cover_image"
                  :src="post.cover_image"
                  :alt="post.title"
                  class="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
                />
                <div v-else class="w-full h-full flex items-center justify-center">
                  <span class="text-6xl opacity-30">📝</span>
                </div>
                <!-- 阅读时间 -->
                <div class="absolute top-3 right-3 px-2 py-1 bg-black/50 backdrop-blur-sm rounded-full text-white text-xs">
                  {{ post.reading_time }} 分钟阅读
                </div>
              </div>
              
              <!-- 内容 -->
              <div class="p-5">
                <!-- 标签 -->
                <div class="flex flex-wrap gap-1.5 mb-3">
                  <span
                    v-for="tag in post.tags?.slice(0, 3)"
                    :key="tag.id"
                    class="px-2 py-0.5 rounded-full text-xs font-medium"
                    :style="{ backgroundColor: tag.color + '20', color: tag.color }"
                  >
                    {{ tag.name }}
                  </span>
                </div>
                
                <h3 class="text-lg font-bold text-slate-800 mb-2 group-hover:text-purple-600 transition-colors line-clamp-2">
                  {{ post.title }}
                </h3>
                
                <p class="text-sm text-slate-500 line-clamp-2 mb-4">
                  {{ post.summary }}
                </p>
                
                <!-- 底部信息 -->
                <div class="flex items-center justify-between text-sm text-slate-400">
                  <span>{{ formatDate(post.published_at || post.created_at) }}</span>
                  <div class="flex items-center gap-3">
                    <span class="flex items-center gap-1">
                      <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                      </svg>
                      {{ post.view_count }}
                    </span>
                  </div>
                </div>
              </div>
            </router-link>
          </div>
        </div>
      </div>
      
      <!-- 空状态 -->
      <div v-else class="text-center py-20">
        <div class="text-6xl mb-4">📭</div>
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
</style>

