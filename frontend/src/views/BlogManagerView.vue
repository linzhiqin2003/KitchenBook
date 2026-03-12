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
const isDarkTheme = ref(localStorage.getItem('blog_theme') !== 'light')
const studioBasePath = '/blog/studio'

// 筛选
const filterStatus = ref('all') // all, published, draft
const filterTag = ref('')
const searchQuery = ref('')

const toggleTheme = () => {
  isDarkTheme.value = !isDarkTheme.value
  localStorage.setItem('blog_theme', isDarkTheme.value ? 'dark' : 'light')
}

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

const publishedCount = computed(() => posts.value.filter(p => p.is_published).length)
const draftCount = computed(() => posts.value.filter(p => !p.is_published).length)

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
  <div :class="[
    'min-h-screen transition-colors duration-500',
    isDarkTheme ? 'bg-[#0a0a0f] text-slate-100' : 'bg-gradient-to-br from-slate-50 via-white to-violet-50 text-slate-800'
  ]">
    <div class="relative overflow-hidden">
      <div class="absolute inset-0 bg-[radial-gradient(circle_at_top_left,rgba(139,92,246,0.22),transparent_35%),radial-gradient(circle_at_top_right,rgba(236,72,153,0.18),transparent_30%)]"></div>
      <div class="absolute inset-0 opacity-40" :class="isDarkTheme ? 'bg-[linear-gradient(rgba(255,255,255,0.03)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,0.03)_1px,transparent_1px)]' : 'bg-[linear-gradient(rgba(139,92,246,0.04)_1px,transparent_1px),linear-gradient(90deg,rgba(139,92,246,0.04)_1px,transparent_1px)]'" style="background-size: 40px 40px;"></div>
      <div class="relative max-w-7xl mx-auto px-4 md:px-6 py-8 md:py-10">
        <div class="flex flex-col gap-6 md:flex-row md:items-start md:justify-between">
          <div class="space-y-4">
            <div class="flex items-center gap-3 text-sm">
              <router-link
                to="/blog"
                :class="[
                  'inline-flex items-center gap-2 rounded-full px-3 py-1.5 transition-colors',
                  isDarkTheme ? 'bg-white/5 text-slate-300 hover:bg-white/10 hover:text-white' : 'bg-white/70 text-slate-600 hover:text-violet-700 hover:bg-white'
                ]"
              >
                <span>←</span>
                返回博客首页
              </router-link>
              <span :class="isDarkTheme ? 'text-slate-500' : 'text-slate-400'">/</span>
              <span :class="isDarkTheme ? 'text-violet-300' : 'text-violet-600'" class="font-medium">Studio</span>
            </div>
            <div>
              <p :class="isDarkTheme ? 'text-violet-300/80' : 'text-violet-600'" class="text-xs uppercase tracking-[0.35em] mb-3">Blog Studio</p>
              <h1 :class="isDarkTheme ? 'text-white' : 'text-slate-900'" class="text-4xl md:text-5xl font-bold tracking-tight">博客写作台</h1>
              <p :class="isDarkTheme ? 'text-slate-400' : 'text-slate-500'" class="mt-3 max-w-2xl text-sm md:text-base">
                写作区已经从 Kitchen 后台剥离。这里专注文章草稿、发布和标签管理，视觉语言与 Blog 前台保持一致。
              </p>
            </div>
          </div>

          <div class="flex items-center gap-3">
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
            <router-link
              :to="`${studioBasePath}/new`"
              class="inline-flex items-center gap-2 px-5 py-3 rounded-full bg-gradient-to-r from-violet-600 to-fuchsia-600 text-white font-medium shadow-lg shadow-violet-500/30 hover:shadow-violet-500/40 transition-all"
            >
              <span>✍️</span>
              写新文章
            </router-link>
          </div>
        </div>

        <div class="mt-8 grid grid-cols-2 lg:grid-cols-4 gap-4">
          <div :class="isDarkTheme ? 'bg-white/5 border-white/10' : 'bg-white/80 border-white'" class="rounded-3xl border backdrop-blur-xl p-5">
            <div class="text-3xl font-bold text-violet-400">{{ posts.length }}</div>
            <div :class="isDarkTheme ? 'text-slate-400' : 'text-slate-500'" class="text-sm mt-1">总文章数</div>
          </div>
          <div :class="isDarkTheme ? 'bg-white/5 border-white/10' : 'bg-white/80 border-white'" class="rounded-3xl border backdrop-blur-xl p-5">
            <div class="text-3xl font-bold text-emerald-400">{{ publishedCount }}</div>
            <div :class="isDarkTheme ? 'text-slate-400' : 'text-slate-500'" class="text-sm mt-1">已发布</div>
          </div>
          <div :class="isDarkTheme ? 'bg-white/5 border-white/10' : 'bg-white/80 border-white'" class="rounded-3xl border backdrop-blur-xl p-5">
            <div class="text-3xl font-bold text-amber-400">{{ draftCount }}</div>
            <div :class="isDarkTheme ? 'text-slate-400' : 'text-slate-500'" class="text-sm mt-1">草稿</div>
          </div>
          <div :class="isDarkTheme ? 'bg-white/5 border-white/10' : 'bg-white/80 border-white'" class="rounded-3xl border backdrop-blur-xl p-5">
            <div class="text-3xl font-bold text-sky-400">{{ stats.total_views }}</div>
            <div :class="isDarkTheme ? 'text-slate-400' : 'text-slate-500'" class="text-sm mt-1">总阅读量</div>
          </div>
        </div>
      </div>
    </div>

    <div class="max-w-7xl mx-auto px-4 md:px-6 pb-12">
      <div :class="isDarkTheme ? 'bg-white/5 border-white/10' : 'bg-white/90 border-white'" class="rounded-3xl p-4 border backdrop-blur-xl shadow-sm mb-6">
      <div class="flex flex-col md:flex-row gap-4">
        <!-- 搜索 -->
        <div class="relative flex-1">
          <svg :class="isDarkTheme ? 'text-slate-500' : 'text-slate-400'" class="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
          </svg>
          <input
            v-model="searchQuery"
            type="text"
            placeholder="搜索文章标题..."
            :class="[
              'w-full pl-10 pr-4 py-2.5 rounded-2xl focus:ring-2 focus:ring-violet-500 focus:border-transparent transition-colors',
              isDarkTheme ? 'bg-[#13131b] border border-white/10 text-white placeholder:text-slate-500' : 'bg-white border border-slate-200 text-slate-800'
            ]"
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
              'px-4 py-2 rounded-full text-sm font-medium transition-all',
              filterStatus === status.value
                ? 'bg-violet-500 text-white'
                : (isDarkTheme ? 'bg-white/5 text-slate-300 hover:bg-white/10' : 'bg-slate-100 text-slate-600 hover:bg-slate-200')
            ]"
          >
            {{ status.icon }} {{ status.label }}
          </button>
        </div>
        
        <!-- 标签筛选 -->
        <select
          v-model="filterTag"
          :class="[
            'px-4 py-2.5 rounded-2xl focus:ring-2 focus:ring-violet-500 focus:border-transparent',
            isDarkTheme ? 'bg-[#13131b] border border-white/10 text-slate-200' : 'bg-white border border-slate-200 text-slate-700'
          ]"
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
        :class="isDarkTheme ? 'bg-white/5 border-white/10 hover:bg-white/[0.07]' : 'bg-white border-slate-100 hover:shadow-md'"
        class="rounded-3xl border shadow-sm transition-all overflow-hidden backdrop-blur-xl"
      >
        <div class="flex flex-col md:flex-row">
          <!-- 封面图 -->
          <div :class="isDarkTheme ? 'bg-[#151520]' : 'bg-slate-100'" class="md:w-48 h-32 md:h-auto flex-shrink-0">
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
                <h3 :class="isDarkTheme ? 'text-white hover:text-violet-300' : 'text-slate-800 hover:text-purple-600'" class="text-lg font-bold mb-1 cursor-pointer transition-colors" @click="router.push(`${studioBasePath}/${post.id}/edit`)">
                  {{ post.title }}
                </h3>
                
                <!-- 摘要 -->
                <p :class="isDarkTheme ? 'text-slate-400' : 'text-slate-500'" class="text-sm line-clamp-1 mb-2">{{ post.summary || '暂无摘要' }}</p>
                
                <!-- 元信息 -->
                <div :class="isDarkTheme ? 'text-slate-500' : 'text-slate-400'" class="flex flex-wrap items-center gap-4 text-xs">
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
                  :to="`${studioBasePath}/${post.id}/edit`"
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
    <div v-else :class="isDarkTheme ? 'bg-white/5 border-white/10' : 'bg-white border-slate-100'" class="text-center py-20 rounded-3xl border">
      <div class="text-6xl mb-4">📭</div>
      <h3 :class="isDarkTheme ? 'text-white' : 'text-slate-700'" class="text-xl font-bold mb-2">
        {{ searchQuery || filterTag || filterStatus !== 'all' ? '没有找到匹配的文章' : '还没有任何文章' }}
      </h3>
      <p :class="isDarkTheme ? 'text-slate-400' : 'text-slate-500'" class="mb-6">
        {{ searchQuery || filterTag || filterStatus !== 'all' ? '试试调整筛选条件' : '点击上方按钮开始写你的第一篇技术博客吧！' }}
      </p>
      <router-link 
        v-if="!searchQuery && !filterTag && filterStatus === 'all'"
        :to="`${studioBasePath}/new`"
        class="inline-flex items-center gap-2 px-6 py-3 bg-purple-600 text-white rounded-xl font-medium hover:bg-purple-700 transition-colors"
      >
        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
        </svg>
        写新文章
      </router-link>
    </div>
    
    <!-- 标签管理 -->
    <div :class="isDarkTheme ? 'bg-white/5 border-white/10' : 'bg-white border-slate-100'" class="mt-8 rounded-3xl p-6 border shadow-sm backdrop-blur-xl">
      <h2 :class="isDarkTheme ? 'text-white' : 'text-slate-800'" class="text-xl font-bold mb-4 flex items-center gap-2">
        <span>🏷️</span> 标签管理
      </h2>
      
      <div v-if="tags.length > 0" class="flex flex-wrap gap-3">
        <div
          v-for="tag in tags"
          :key="tag.id"
          :class="isDarkTheme ? 'bg-white/5' : 'bg-slate-50'" class="flex items-center gap-2 px-3 py-2 rounded-2xl group"
        >
          <span
            class="w-3 h-3 rounded-full"
            :style="{ backgroundColor: tag.color }"
          ></span>
          <span :class="isDarkTheme ? 'text-slate-200' : 'text-slate-700'" class="font-medium">{{ tag.name }}</span>
          <span :class="isDarkTheme ? 'text-slate-500' : 'text-slate-400'" class="text-xs">({{ tag.post_count }} 篇)</span>
          <button
            @click="deleteTag(tag)"
            class="opacity-0 group-hover:opacity-100 text-red-500 hover:text-red-700 transition-opacity ml-1"
          >
            ×
          </button>
        </div>
      </div>
      
      <p :class="isDarkTheme ? 'text-slate-500' : 'text-slate-400'" class="text-sm">
        暂无标签，在编辑文章时可以创建新标签
      </p>
    </div>
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


