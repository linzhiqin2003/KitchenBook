<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'
import API_BASE_URL from '../config/api'
import MenuBook from '../components/MenuBook.vue'
import RecipeCard from '../components/RecipeCard.vue'

const recipes = ref([])
const viewMode = ref('grid') // 默认使用网格(卡片)模式

onMounted(async () => {
  try {
    const response = await axios.get(`${API_BASE_URL}/api/recipes/`)
    recipes.value = response.data
  } catch (error) {
    console.error('Failed to fetch recipes', error)
  }
})
</script>

<template>
  <div class="min-h-[calc(100vh-4rem)] flex flex-col">
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
    </div>

    <!-- Content Area -->
    <div v-if="recipes.length > 0" class="flex-1 w-full container mx-auto px-2 md:px-4 pb-8 md:pb-12">
      
      <Transition name="mode-switch" mode="out-in">
        <!-- Grid View (Default) -->
        <div v-if="viewMode === 'grid'" key="grid" class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 md:gap-8">
          <RecipeCard 
            v-for="recipe in recipes" 
            :key="recipe.id" 
            :recipe="recipe"
          />
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
</style>

