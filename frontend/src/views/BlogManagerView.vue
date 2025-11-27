<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'
import API_BASE_URL from '../config/api'
import { auth } from '../store/auth'

const router = useRouter()
const posts = ref([])
const tags = ref([])
const loading = ref(true)
const stats = ref({ total_posts: 0, total_views: 0, total_tags: 0 })

// 筛选
const filterStatus = ref('all') // all, published, draft
const filterTag = ref('')
const searchQuery = ref('')

// 获取文章列表
const fetchPosts = async () => {
  try {
    loading.value = true
    const response = await axios.get(`${API_BASE_URL}/api/blog/posts/?mode=chef`, {
      headers: { Authorization: `Bearer ${auth.token}` }
    })
    posts.value = response.data
  } catch (error) {
    console.error('Failed to fetch posts', error)
  } finally {
    loading.value = false
  }
}

// 获取标签
const fetchTags = async () => {
  try {
    const response = await axios.get(`${API_BASE_URL}/api/blog/tags/`)
    tags.value = response.data
  } catch (error) {
    console.error('Failed to fetch tags', error)
  }
}

// 获取统计
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

// 筛选后的文章列表
const filteredPosts = computed(() => {
  let result = posts.value
  
  // 状态筛选
  if (filterStatus.value === 'published') {
    result = result.filter(p => p.is_published)
  } else if (filterStatus.value === 'draft') {
    result = result.filter(p => !p.is_published)
  }
  
  // 标签筛选
  if (filterTag.value) {
    result = result.filter(p => p.tags?.some(t => t.name === filterTag.value))
  }
  
  // 搜索
  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase()
    result = result.filter(p => 
      p.title.toLowerCase().includes(query) ||
      p.summary?.toLowerCase().includes(query)
    )
  }
  
  return result
})

// 格式化日期
const formatDate = (dateStr) => {
  if (!dateStr) return '-'
  const date = new Date(dateStr)
  return date.toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

// 删除文章
const deletePost = async (post) => {
  if (!confirm(`确定要删除文章「${post.title}」吗？此操作不可恢复。`)) return
  
  try {
    await axios.delete(`${API_BASE_URL}/api/blog/posts/${post.id}/`, {
      headers: { Authorization: `Bearer ${auth.token}` }
    })
    posts.value = posts.value.filter(p => p.id !== post.id)
  } catch (error) {
    console.error('Failed to delete post', error)
    alert('删除失败')
  }
}

// 切换发布状态
const togglePublish = async (post) => {
  try {
    await axios.patch(`${API_BASE_URL}/api/blog/posts/${post.id}/`, {
      is_published: !post.is_published
    }, {
      headers: { Authorization: `Bearer ${auth.token}` }
    })
    post.is_published = !post.is_published
  } catch (error) {
    console.error('Failed to toggle publish', error)
    alert('操作失败')
  }
}

// 切换精选状态
const toggleFeatured = async (post) => {
  try {
    await axios.patch(`${API_BASE_URL}/api/blog/posts/${post.id}/`, {
      is_featured: !post.is_featured
    }, {
      headers: { Authorization: `Bearer ${auth.token}` }
    })
    post.is_featured = !post.is_featured
  } catch (error) {
    console.error('Failed to toggle featured', error)
    alert('操作失败')
  }
}

// 删除标签
const deleteTag = async (tag) => {
  if (!confirm(`确定要删除标签「${tag.name}」吗？`)) return
  
  try {
    await axios.delete(`${API_BASE_URL}/api/blog/tags/${tag.id}/`, {
      headers: { Authorization: `Bearer ${auth.token}` }
    })
    tags.value = tags.value.filter(t => t.id !== tag.id)
  } catch (error) {
    console.error('Failed to delete tag', error)
    alert('删除失败')
  }
}
</script>

<template>
  <div class="max-w-7xl mx-auto">
    <!-- 页面标题 -->
    <div class="flex flex-col md:flex-row md:items-center md:justify-between gap-4 mb-8">
      <div>
        <h1 class="text-3xl font-bold text-slate-800 flex items-center gap-3">
          <span class="text-4xl">📝</span> 博客管理
        </h1>
        <p class="text-slate-500 mt-1">管理你的技术博客文章</p>
      </div>
      
      <router-link 
        to="/chef/blog/new"
        class="inline-flex items-center gap-2 px-6 py-3 bg-purple-600 text-white rounded-xl font-medium hover:bg-purple-700 transition-colors shadow-lg shadow-purple-500/30"
      >
        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
        </svg>
        写新文章
      </router-link>
    </div>
    
    <!-- 统计卡片 -->
    <div class="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
      <div class="bg-white rounded-2xl p-5 border border-slate-100 shadow-sm">
        <div class="text-3xl font-bold text-purple-600">{{ posts.length }}</div>
        <div class="text-sm text-slate-500 mt-1">总文章数</div>
      </div>
      <div class="bg-white rounded-2xl p-5 border border-slate-100 shadow-sm">
        <div class="text-3xl font-bold text-green-600">{{ posts.filter(p => p.is_published).length }}</div>
        <div class="text-sm text-slate-500 mt-1">已发布</div>
      </div>
      <div class="bg-white rounded-2xl p-5 border border-slate-100 shadow-sm">
        <div class="text-3xl font-bold text-amber-600">{{ posts.filter(p => !p.is_published).length }}</div>
        <div class="text-sm text-slate-500 mt-1">草稿</div>
      </div>
      <div class="bg-white rounded-2xl p-5 border border-slate-100 shadow-sm">
        <div class="text-3xl font-bold text-blue-600">{{ stats.total_views }}</div>
        <div class="text-sm text-slate-500 mt-1">总阅读量</div>
      </div>
    </div>
    
    <!-- 筛选工具栏 -->
    <div class="bg-white rounded-2xl p-4 border border-slate-100 shadow-sm mb-6">
      <div class="flex flex-col md:flex-row gap-4">
        <!-- 搜索 -->
        <div class="relative flex-1">
          <svg class="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
          </svg>
          <input
            v-model="searchQuery"
            type="text"
            placeholder="搜索文章标题..."
            class="w-full pl-10 pr-4 py-2 border border-slate-200 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
          />
        </div>
        
        <!-- 状态筛选 -->
        <div class="flex gap-2">
          <button
            v-for="status in [
              { value: 'all', label: '全部', icon: '📋' },
              { value: 'published', label: '已发布', icon: '✅' },
              { value: 'draft', label: '草稿', icon: '📝' }
            ]"
            :key="status.value"
            @click="filterStatus = status.value"
            :class="[
              'px-4 py-2 rounded-lg text-sm font-medium transition-all',
              filterStatus === status.value
                ? 'bg-purple-100 text-purple-700'
                : 'bg-slate-50 text-slate-600 hover:bg-slate-100'
            ]"
          >
            {{ status.icon }} {{ status.label }}
          </button>
        </div>
        
        <!-- 标签筛选 -->
        <select
          v-model="filterTag"
          class="px-4 py-2 border border-slate-200 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
        >
          <option value="">所有标签</option>
          <option v-for="tag in tags" :key="tag.id" :value="tag.name">
            {{ tag.name }}
          </option>
        </select>
      </div>
    </div>
    
    <!-- 加载状态 -->
    <div v-if="loading" class="flex justify-center items-center py-20">
      <div class="w-12 h-12 border-4 border-purple-200 border-t-purple-600 rounded-full animate-spin"></div>
    </div>
    
    <!-- 文章列表 -->
    <div v-else-if="filteredPosts.length > 0" class="space-y-4">
      <div
        v-for="post in filteredPosts"
        :key="post.id"
        class="bg-white rounded-2xl border border-slate-100 shadow-sm hover:shadow-md transition-shadow overflow-hidden"
      >
        <div class="flex flex-col md:flex-row">
          <!-- 封面图 -->
          <div class="md:w-48 h-32 md:h-auto bg-slate-100 flex-shrink-0">
            <img
              v-if="post.cover_image"
              :src="post.cover_image"
              :alt="post.title"
              class="w-full h-full object-cover"
            />
            <div v-else class="w-full h-full flex items-center justify-center text-4xl opacity-30">
              📄
            </div>
          </div>
          
          <!-- 内容 -->
          <div class="flex-1 p-4 md:p-5">
            <div class="flex flex-col md:flex-row md:items-start md:justify-between gap-3">
              <div class="flex-1">
                <!-- 状态标签 -->
                <div class="flex flex-wrap items-center gap-2 mb-2">
                  <span
                    :class="[
                      'px-2 py-0.5 rounded-full text-xs font-medium',
                      post.is_published
                        ? 'bg-green-100 text-green-700'
                        : 'bg-amber-100 text-amber-700'
                    ]"
                  >
                    {{ post.is_published ? '已发布' : '草稿' }}
                  </span>
                  <span v-if="post.is_featured" class="px-2 py-0.5 bg-yellow-100 text-yellow-700 rounded-full text-xs font-medium">
                    ⭐ 精选
                  </span>
                  <span
                    v-for="tag in post.tags?.slice(0, 3)"
                    :key="tag.id"
                    class="px-2 py-0.5 rounded-full text-xs"
                    :style="{ backgroundColor: tag.color + '20', color: tag.color }"
                  >
                    {{ tag.name }}
                  </span>
                </div>
                
                <!-- 标题 -->
                <h3 class="text-lg font-bold text-slate-800 mb-1 hover:text-purple-600 cursor-pointer" @click="router.push(`/chef/blog/${post.id}/edit`)">
                  {{ post.title }}
                </h3>
                
                <!-- 摘要 -->
                <p class="text-sm text-slate-500 line-clamp-1 mb-2">{{ post.summary || '暂无摘要' }}</p>
                
                <!-- 元信息 -->
                <div class="flex flex-wrap items-center gap-4 text-xs text-slate-400">
                  <span class="flex items-center gap-1">
                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                    </svg>
                    {{ formatDate(post.created_at) }}
                  </span>
                  <span class="flex items-center gap-1">
                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                    </svg>
                    {{ post.view_count }} 次阅读
                  </span>
                  <span class="flex items-center gap-1">
                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    {{ post.reading_time }} 分钟
                  </span>
                </div>
              </div>
              
              <!-- 操作按钮 -->
              <div class="flex items-center gap-2 mt-2 md:mt-0">
                <button
                  @click="toggleFeatured(post)"
                  :class="[
                    'p-2 rounded-lg transition-colors',
                    post.is_featured ? 'bg-yellow-100 text-yellow-600' : 'bg-slate-100 text-slate-400 hover:text-yellow-600'
                  ]"
                  title="切换精选"
                >
                  ⭐
                </button>
                <button
                  @click="togglePublish(post)"
                  :class="[
                    'p-2 rounded-lg transition-colors',
                    post.is_published ? 'bg-green-100 text-green-600' : 'bg-slate-100 text-slate-400 hover:text-green-600'
                  ]"
                  :title="post.is_published ? '取消发布' : '发布'"
                >
                  {{ post.is_published ? '📢' : '📝' }}
                </button>
                <router-link
                  :to="`/chef/blog/${post.id}/edit`"
                  class="p-2 bg-purple-100 text-purple-600 rounded-lg hover:bg-purple-200 transition-colors"
                  title="编辑"
                >
                  ✏️
                </router-link>
                <router-link
                  v-if="post.is_published"
                  :to="`/blog/${post.slug}`"
                  target="_blank"
                  class="p-2 bg-blue-100 text-blue-600 rounded-lg hover:bg-blue-200 transition-colors"
                  title="查看"
                >
                  👁️
                </router-link>
                <button
                  @click="deletePost(post)"
                  class="p-2 bg-red-100 text-red-600 rounded-lg hover:bg-red-200 transition-colors"
                  title="删除"
                >
                  🗑️
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
    
    <!-- 空状态 -->
    <div v-else class="text-center py-20 bg-white rounded-2xl border border-slate-100">
      <div class="text-6xl mb-4">📭</div>
      <h3 class="text-xl font-bold text-slate-700 mb-2">
        {{ searchQuery || filterTag || filterStatus !== 'all' ? '没有找到匹配的文章' : '还没有任何文章' }}
      </h3>
      <p class="text-slate-500 mb-6">
        {{ searchQuery || filterTag || filterStatus !== 'all' ? '试试调整筛选条件' : '点击上方按钮开始写你的第一篇技术博客吧！' }}
      </p>
      <router-link 
        v-if="!searchQuery && !filterTag && filterStatus === 'all'"
        to="/chef/blog/new"
        class="inline-flex items-center gap-2 px-6 py-3 bg-purple-600 text-white rounded-xl font-medium hover:bg-purple-700 transition-colors"
      >
        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
        </svg>
        写新文章
      </router-link>
    </div>
    
    <!-- 标签管理 -->
    <div class="mt-8 bg-white rounded-2xl p-6 border border-slate-100 shadow-sm">
      <h2 class="text-xl font-bold text-slate-800 mb-4 flex items-center gap-2">
        <span>🏷️</span> 标签管理
      </h2>
      
      <div v-if="tags.length > 0" class="flex flex-wrap gap-3">
        <div
          v-for="tag in tags"
          :key="tag.id"
          class="flex items-center gap-2 px-3 py-2 bg-slate-50 rounded-lg group"
        >
          <span
            class="w-3 h-3 rounded-full"
            :style="{ backgroundColor: tag.color }"
          ></span>
          <span class="font-medium text-slate-700">{{ tag.name }}</span>
          <span class="text-xs text-slate-400">({{ tag.post_count }} 篇)</span>
          <button
            @click="deleteTag(tag)"
            class="opacity-0 group-hover:opacity-100 text-red-500 hover:text-red-700 transition-opacity ml-1"
          >
            ×
          </button>
        </div>
      </div>
      
      <p v-else class="text-slate-400 text-sm">
        暂无标签，在编辑文章时可以创建新标签
      </p>
    </div>
  </div>
</template>

<style scoped>
.line-clamp-1 {
  display: -webkit-box;
  -webkit-line-clamp: 1;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
</style>

