<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'
import RecipeCard from '../components/RecipeCard.vue'

const recipes = ref([])

onMounted(async () => {
  try {
    // Public mode: only fetches basic info
    const response = await axios.get('http://127.0.0.1:8000/api/recipes/')
    recipes.value = response.data
  } catch (error) {
    console.error('Failed to fetch recipes', error)
  }
})
</script>

<template>
  <div>
    <div class="mb-12 text-center max-w-2xl mx-auto">
      <div class="inline-block mb-4 p-3 bg-emerald-100 rounded-full text-emerald-800">
          <span class="text-3xl">👨‍🍳</span>
      </div>
      <h2 class="text-4xl font-display font-bold text-emerald-900 mb-4">今日特供菜单</h2>
      <p class="text-stone-600 font-serif text-lg leading-relaxed italic">"这是我为您精心准备的私房菜肴。请随意浏览，挑选您心仪的美味，我将亲自为您烹饪。"</p>
      <div class="w-24 h-1 bg-amber-300 mx-auto mt-6"></div>
    </div>
    
    <div v-if="recipes.length > 0" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8 px-4">
      <RecipeCard 
        v-for="recipe in recipes" 
        :key="recipe.id" 
        :recipe="recipe" 
      />
    </div>
    <div v-else class="text-center py-16 bg-white rounded-xl shadow-sm border border-stone-100 mx-4">
      <p class="text-xl text-stone-500 font-serif">主厨正在构思今日菜单...</p>
    </div>
  </div>
</template>

