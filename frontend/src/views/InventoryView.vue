<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'
import API_BASE_URL from '../config/api'

const ingredients = ref([])
const loading = ref(true)
const newIngredientName = ref('')

const fetchIngredients = async () => {
    try {
        const response = await axios.get(`${API_BASE_URL}/api/ingredients/`)
        ingredients.value = response.data
    } catch (e) {
        console.error(e)
    } finally {
        loading.value = false
    }
}

const toggleStock = async (ingredient) => {
    const originalQuantity = ingredient.quantity
    const originalInStock = ingredient.in_stock
    
    // Toggle logic: if in_stock, set quantity to 0; if out of stock, set to a default value
    const newQuantity = ingredient.in_stock ? 0 : 100
    
    // Optimistic update for UI
    ingredient.quantity = newQuantity
    ingredient.in_stock = newQuantity > 0
    
    try {
        await axios.patch(`${API_BASE_URL}/api/ingredients/${ingredient.id}/`, {
            quantity: newQuantity
        })
    } catch (e) {
        // Revert on failure
        ingredient.quantity = originalQuantity
        ingredient.in_stock = originalInStock
        alert('更新失败')
    }
}

const addIngredient = async () => {
    if (!newIngredientName.value.trim()) return
    try {
        const response = await axios.post(`${API_BASE_URL}/api/ingredients/`, {
            name: newIngredientName.value,
            quantity: 100,  // Default stock quantity
            unit: 'g'       // Default unit
        })
        ingredients.value.push(response.data)
        newIngredientName.value = ''
    } catch (e) {
        alert('添加失败')
    }
}

const deleteIngredient = async (id) => {
    if (!confirm('确定删除该食材？')) return
    try {
        await axios.delete(`${API_BASE_URL}/api/ingredients/${id}/`)
        ingredients.value = ingredients.value.filter(i => i.id !== id)
    } catch (e) {
        alert('删除失败')
    }
}

onMounted(fetchIngredients)
</script>

<template>
  <div class="max-w-4xl mx-auto py-8 px-4">
    <div class="flex justify-between items-center mb-8">
        <div>
            <h1 class="text-3xl font-bold text-stone-800 font-display">库存管理</h1>
            <p class="text-stone-500 mt-1">管理厨房食材与库存状态</p>
        </div>
    </div>

    <!-- Add New -->
    <div class="bg-white p-4 rounded-xl shadow-sm border border-stone-200 mb-8 flex gap-4">
        <input 
            v-model="newIngredientName" 
            @keyup.enter="addIngredient"
            class="flex-1 border border-stone-300 rounded-lg px-4 py-2 focus:ring-2 focus:ring-emerald-500 focus:outline-none"
            placeholder="输入新食材名称，例如：黑胡椒..." 
        />
        <button @click="addIngredient" class="bg-emerald-600 text-white px-6 py-2 rounded-lg font-bold hover:bg-emerald-700 transition-colors">
            + 添加
        </button>
    </div>

    <div v-if="loading" class="text-center py-12 text-stone-500">加载中...</div>

    <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        <div 
            v-for="ing in ingredients" 
            :key="ing.id" 
            class="bg-white p-4 rounded-xl border transition-all flex justify-between items-center group"
            :class="ing.in_stock ? 'border-stone-200 shadow-sm' : 'border-red-200 bg-red-50/30'"
        >
            <div class="flex items-center gap-3">
                <button 
                    @click="toggleStock(ing)"
                    class="w-6 h-6 rounded border flex items-center justify-center transition-colors"
                    :class="ing.in_stock ? 'bg-emerald-500 border-emerald-600 text-white' : 'bg-white border-stone-300 text-transparent'"
                >
                    ✓
                </button>
                <span class="font-bold text-lg" :class="ing.in_stock ? 'text-stone-700' : 'text-red-400 line-through'">{{ ing.name }}</span>
            </div>
            
            <button @click="deleteIngredient(ing.id)" class="text-stone-300 hover:text-red-500 opacity-0 group-hover:opacity-100 transition-all">
                🗑️
            </button>
        </div>
    </div>
  </div>
</template>


