<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import axios from 'axios'
import API_BASE_URL from '../config/api'
import BookReader from '../components/BookReader.vue'

const route = useRoute()
const router = useRouter()
const recipe = ref(null)
const loading = ref(true)

onMounted(async () => {
  try {
    const id = route.params.id
    // Chef mode: fetches full details including steps/ingredients
        const response = await axios.get(`${API_BASE_URL}/api/recipes/${id}/?mode=chef`)
    recipe.value = response.data
  } catch (error) {
    console.error('Failed to fetch recipe', error)
    alert('无法加载菜谱，请稍后再试。')
    router.push('/')
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <div class="fixed inset-0 z-50 bg-stone-900/95 flex flex-col">
    <div class="absolute top-4 right-4 z-50">
        <button @click="router.push('/')" class="text-white hover:text-emerald-400 transition-colors text-lg flex items-center gap-2">
            <span class="text-2xl">✕</span> 关闭阅读
        </button>
    </div>
    
    <div v-if="loading" class="flex-1 flex items-center justify-center text-white">
        <p class="text-xl animate-pulse">正在打开菜谱...</p>
    </div>
    
    <div v-else-if="recipe" class="flex-1 overflow-hidden">
        <BookReader :recipe="recipe" />
    </div>
  </div>
</template>

