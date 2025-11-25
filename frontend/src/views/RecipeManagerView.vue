<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'
import API_BASE_URL from '../config/api'

const recipes = ref([])
const loading = ref(true)

const fetchRecipes = async () => {
  try {
    // Use 'chef' mode to get full details if needed, though list is usually simple
        const response = await axios.get(`${API_BASE_URL}/api/recipes/?mode=chef`)
    recipes.value = response.data
  } catch (error) {
    console.error('Failed to fetch recipes', error)
  } finally {
    loading.value = false
  }
}

const deleteRecipe = async (id) => {
    if(!confirm('确定要删除这道菜吗？')) return
    try {
        await axios.delete(`${API_BASE_URL}/api/recipes/${id}/`)
        recipes.value = recipes.value.filter(r => r.id !== id)
    } catch (error) {
        alert('删除失败')
    }
}

onMounted(fetchRecipes)
</script>

<template>
  <div class="max-w-6xl mx-auto py-8">
    <div class="flex justify-between items-center mb-8">
        <div>
            <h1 class="text-3xl font-bold text-stone-800 font-display">食谱管理</h1>
            <p class="text-stone-500 mt-1">管理您的私房菜单</p>
        </div>
        <router-link to="/chef/recipes/new" class="bg-emerald-600 text-white px-4 py-2 rounded-lg hover:bg-emerald-700 transition-colors flex items-center gap-2 font-bold shadow-sm">
            <span>+</span> 新增菜谱
        </router-link>
    </div>

    <div v-if="loading" class="text-center py-12 text-stone-500">
        加载中...
    </div>

    <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <div v-for="recipe in recipes" :key="recipe.id" class="bg-white rounded-xl border border-stone-200 overflow-hidden shadow-sm hover:shadow-md transition-shadow group">
            <div class="h-48 bg-stone-100 relative">
                <img v-if="recipe.cover_image" :src="recipe.cover_image" class="w-full h-full object-cover" />
                <div v-else class="w-full h-full flex items-center justify-center text-stone-300 text-4xl">🍳</div>
                
                <div class="absolute top-2 right-2 flex gap-2">
                    <span v-if="recipe.is_public" class="bg-green-100 text-green-800 text-xs px-2 py-1 rounded-full font-bold border border-green-200">公开</span>
                    <span v-else class="bg-stone-100 text-stone-600 text-xs px-2 py-1 rounded-full font-bold border border-stone-200">私密</span>
                </div>
            </div>
            <div class="p-4">
                <h3 class="font-bold text-lg text-stone-800 mb-1">{{ recipe.title }}</h3>
                <p class="text-sm text-stone-500 mb-4 line-clamp-1">{{ recipe.description }}</p>
                
                <div class="flex justify-between items-center pt-4 border-t border-stone-100">
                    <span class="text-xs text-stone-400">修改于 {{ new Date().toLocaleDateString() }}</span>
                    <div class="flex gap-2">
                        <!-- We'll implement edit later, just linking for now -->
                         <router-link :to="`/chef/recipes/${recipe.id}/edit`" class="text-stone-500 hover:text-emerald-600 p-1">
                            ✏️
                        </router-link>
                        <button @click="deleteRecipe(recipe.id)" class="text-stone-500 hover:text-red-600 p-1">
                            🗑️
                        </button>
                    </div>
                </div>
            </div>
        </div>
    </div>
  </div>
</template>

