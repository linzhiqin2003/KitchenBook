<script setup>
import { ref, onMounted, computed } from 'vue'
import axios from 'axios'
import API_BASE_URL from '../config/api'
import MenuBook from '../components/MenuBook.vue'
import RecipeCard from '../components/RecipeCard.vue'

const recipes = ref([])
const viewMode = ref('grid') // 默认使用网格(卡片)模式
const selectedCategory = ref('全部') // 当前选中的分类

onMounted(async () => {
  try {
    const response = await axios.get(`${API_BASE_URL}/api/recipes/`)
    recipes.value = response.data
  } catch (error) {
    console.error('Failed to fetch recipes', error)
  }
})

// 提取所有分类（去重）
const categories = computed(() => {
  const cats = recipes.value.map(r => r.category || '家常菜')
  return ['全部', ...new Set(cats)]
})

// 根据分类筛选菜品
const filteredRecipes = computed(() => {
  if (selectedCategory.value === '全部') {
    return recipes.value
  }
  return recipes.value.filter(r => (r.category || '家常菜') === selectedCategory.value)
})

// 分类对应的 emoji 图标
const categoryIcons = {
  '全部': '🍽️',
  '烧烤': '🔥',
  '小炒': '🥘',
  '水煮': '🍲',
  '奶茶': '🥤',
  '甜点': '🍰',
  '硬菜': '🥩',
  '凉菜': '🥗',
  '汤品': '🍜',
  '主食': '🍚',
  '海鲜': '🦐',
  '素菜': '🥬',
  '麻辣烫': '🌶️',
  '小吃': '🥟',
  '家常菜': '🏠'
}

const getCategoryIcon = (cat) => categoryIcons[cat] || '🍴'
</script>

<template>
  <div class="min-h-[calc(100vh-4rem)] flex flex-col">
    <!-- 返回主页悬浮按钮 -->
    <router-link 
      to="/" 
      class="fixed top-4 left-4 z-50 w-10 h-10 rounded-full bg-white/90 backdrop-blur-sm shadow-lg border border-gray-200 flex items-center justify-center text-gray-600 hover:text-emerald-600 hover:border-emerald-300 hover:shadow-xl transition-all group"
      title="返回首页"
    >
      <svg class="w-5 h-5 group-hover:-translate-x-0.5 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 19l-7-7m0 0l7-7m-7 7h18"/>
      </svg>
    </router-link>

    <!-- View Switcher & Title -->
    <div class="container mx-auto px-2 md:px-4 py-4 md:py-6" v-if="recipes.length > 0">
      <!-- 标题行：标题和开关在同一行 -->
      <div class="flex justify-between items-center">
        <h2 class="text-xl md:text-2xl font-display font-bold text-emerald-900">今日菜单</h2>
        
        <!-- Toggle Switch -->
        <div class="flex items-center gap-2 md:gap-3 bg-white px-3 md:px-4 py-1.5 md:py-2 rounded-full shadow-sm border border-stone-100">
          <span class="text-xs md:text-sm font-bold text-stone-600 font-serif">阅读模式</span>
          <button 
            @click="viewMode = viewMode === 'grid' ? 'book' : 'grid'"
            class="w-10 md:w-12 h-5 md:h-6 rounded-full relative transition-colors duration-300 focus:outline-none shadow-inner cursor-pointer"
            :class="viewMode === 'book' ? 'bg-emerald-500' : 'bg-stone-300'"
            aria-label="切换视图模式"
          >
            <div 
              class="w-4 md:w-5 h-4 md:h-5 bg-white rounded-full absolute top-0.5 left-0.5 shadow-sm transition-transform duration-300"
              :class="viewMode === 'book' ? 'translate-x-5 md:translate-x-6' : 'translate-x-0'"
            ></div>
          </button>
        </div>
      </div>
      <!-- 副标题 -->
      <p class="text-xs md:text-sm text-stone-500 mt-1 font-serif">精选当季食材，用心烹饪每一道佳肴</p>
      
      <!-- 分类筛选栏 - 只在卡片模式显示 -->
      <div v-if="viewMode === 'grid' && categories.length > 2" class="mt-4 md:mt-6">
        <div class="flex gap-2 overflow-x-auto pb-2 scrollbar-hide -mx-2 px-2">
          <button
            v-for="cat in categories"
            :key="cat"
            @click="selectedCategory = cat"
            class="flex-shrink-0 px-3 md:px-4 py-1.5 md:py-2 rounded-full text-xs md:text-sm font-bold transition-all duration-300 flex items-center gap-1.5 whitespace-nowrap"
            :class="selectedCategory === cat 
              ? 'bg-emerald-700 text-white shadow-md scale-105' 
              : 'bg-white text-stone-600 border border-stone-200 hover:border-emerald-300 hover:text-emerald-700'"
          >
            <span class="text-sm md:text-base">{{ getCategoryIcon(cat) }}</span>
            <span>{{ cat }}</span>
            <span 
              v-if="cat !== '全部'" 
              class="ml-0.5 px-1.5 py-0.5 rounded-full text-[10px] md:text-xs"
              :class="selectedCategory === cat ? 'bg-white/20' : 'bg-stone-100'"
            >
              {{ recipes.filter(r => (r.category || '家常菜') === cat).length }}
            </span>
          </button>
        </div>
      </div>
    </div>

    <!-- Content Area -->
    <div v-if="recipes.length > 0" class="flex-1 w-full container mx-auto px-2 md:px-4 pb-8 md:pb-12">
      
      <Transition name="mode-switch" mode="out-in">
        <!-- Grid View (Default) -->
        <div v-if="viewMode === 'grid'" key="grid">
          <!-- 筛选结果提示 -->
          <div v-if="selectedCategory !== '全部'" class="mb-4 flex items-center justify-between">
            <p class="text-sm text-stone-500">
              <span class="text-emerald-700 font-bold">{{ selectedCategory }}</span> 
              分类下共 <span class="font-bold">{{ filteredRecipes.length }}</span> 道菜
            </p>
            <button 
              @click="selectedCategory = '全部'" 
              class="text-xs text-emerald-600 hover:text-emerald-800 underline"
            >
              查看全部
            </button>
          </div>
          
          <TransitionGroup 
            name="card-list" 
            tag="div" 
            class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 md:gap-8"
          >
            <RecipeCard 
              v-for="recipe in filteredRecipes" 
              :key="recipe.id" 
              :recipe="recipe"
            />
          </TransitionGroup>
          
          <!-- 空状态 -->
          <div v-if="filteredRecipes.length === 0" class="text-center py-12">
            <span class="text-4xl block mb-3">🍳</span>
            <p class="text-stone-500">该分类下暂无菜品</p>
          </div>
        </div>

        <!-- Book View -->
        <div v-else key="book" class="flex flex-col items-center">
          <MenuBook :recipes="recipes" />
          <div class="text-center pb-4 md:pb-8 text-stone-400 text-xs md:text-sm font-serif animate-pulse mt-2 md:mt-4">
            Tip: 滑动或点击角落来翻阅菜单
          </div>
        </div>
      </Transition>

    </div>
    
    <!-- Empty State -->
    <div v-else class="flex-1 flex items-center justify-center">
      <div class="text-center py-16 bg-white rounded-xl shadow-sm border border-stone-100 mx-4 p-8">
        <p class="text-xl text-stone-500 font-serif">主厨正在构思今日菜单...</p>
      </div>
    </div>
  </div>
</template>

<style scoped>
/* 隐藏滚动条但保持滚动功能 */
.scrollbar-hide {
  -ms-overflow-style: none;
  scrollbar-width: none;
}
.scrollbar-hide::-webkit-scrollbar {
  display: none;
}

/* Transition Styles */
.mode-switch-enter-active,
.mode-switch-leave-active {
  transition: all 0.3s ease;
}

.mode-switch-enter-from,
.mode-switch-leave-to {
  opacity: 0;
  transform: translateY(10px);
}

.mode-switch-enter-to,
.mode-switch-leave-from {
  opacity: 1;
  transform: translateY(0);
}

/* 卡片列表过渡动画 */
.card-list-enter-active {
  transition: all 0.4s ease;
}
.card-list-leave-active {
  transition: all 0.3s ease;
  position: absolute;
}
.card-list-enter-from {
  opacity: 0;
  transform: translateY(20px) scale(0.9);
}
.card-list-leave-to {
  opacity: 0;
  transform: scale(0.9);
}
.card-list-move {
  transition: transform 0.4s ease;
}
</style>
