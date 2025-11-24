<script setup>
import { ref, onMounted, computed } from 'vue'
import axios from 'axios'

const ingredients = ref([])
const loading = ref(true)
const newItemName = ref('')
const filter = ref('all') // 'all', 'in_stock', 'out_of_stock'

const fetchIngredients = async () => {
    try {
        const response = await axios.get('http://127.0.0.1:8000/api/ingredients/')
        ingredients.value = response.data.sort((a, b) => a.name.localeCompare(b.name))
    } catch (e) {
        console.error(e)
    } finally {
        loading.value = false
    }
}

const toggleStock = async (ingredient) => {
    const originalState = ingredient.in_stock
    ingredient.in_stock = !ingredient.in_stock // Optimistic update
    
    try {
        await axios.patch(`http://127.0.0.1:8000/api/ingredients/${ingredient.id}/`, {
            in_stock: ingredient.in_stock
        })
    } catch (e) {
        ingredient.in_stock = originalState // Revert
        alert('更新失败')
    }
}

const addIngredient = async () => {
    if (!newItemName.value.trim()) return
    
    try {
        const response = await axios.post('http://127.0.0.1:8000/api/ingredients/', {
            name: newItemName.value,
            in_stock: true
        })
        ingredients.value.unshift(response.data)
        newItemName.value = ''
    } catch (e) {
        alert('添加失败')
    }
}

const deleteIngredient = async (id) => {
    if (!confirm('确定要删除这个食材吗？如果有菜谱使用了它，可能会受到影响。')) return
    
    try {
        await axios.delete(`http://127.0.0.1:8000/api/ingredients/${id}/`)
        ingredients.value = ingredients.value.filter(i => i.id !== id)
    } catch (e) {
        alert('删除失败')
    }
}

const filteredIngredients = computed(() => {
    if (filter.value === 'in_stock') return ingredients.value.filter(i => i.in_stock)
    if (filter.value === 'out_of_stock') return ingredients.value.filter(i => !i.in_stock)
    return ingredients.value
})

onMounted(fetchIngredients)
</script>

<template>
  <div class="max-w-4xl mx-auto py-8 px-4">
    <div class="flex flex-col md:flex-row justify-between items-end mb-8 gap-4">
        <div>
            <h1 class="text-3xl font-bold text-stone-800 font-display">食材库存管理</h1>
            <p class="text-stone-500 mt-1">管理冰箱里的存货，缺货的食材会自动标记在菜单上</p>
        </div>
        
        <!-- Quick Add -->
        <div class="flex w-full md:w-auto gap-2">
            <input 
                v-model="newItemName" 
                @keyup.enter="addIngredient"
                type="text" 
                placeholder="输入新食材名称..." 
                class="border border-stone-300 rounded-lg px-4 py-2 focus:ring-2 focus:ring-emerald-500 outline-none flex-1 md:w-64"
            />
            <button 
                @click="addIngredient" 
                :disabled="!newItemName.trim()"
                class="bg-emerald-600 text-white px-4 py-2 rounded-lg hover:bg-emerald-700 disabled:opacity-50 disabled:cursor-not-allowed font-bold whitespace-nowrap">
                + 添加
            </button>
        </div>
    </div>

    <!-- Filters -->
    <div class="flex gap-2 mb-6 overflow-x-auto pb-2">
        <button 
            @click="filter = 'all'"
            class="px-4 py-1.5 rounded-full text-sm font-bold transition-colors whitespace-nowrap"
            :class="filter === 'all' ? 'bg-stone-800 text-white' : 'bg-stone-100 text-stone-600 hover:bg-stone-200'">
            全部 ({{ ingredients.length }})
        </button>
        <button 
            @click="filter = 'in_stock'"
            class="px-4 py-1.5 rounded-full text-sm font-bold transition-colors whitespace-nowrap"
            :class="filter === 'in_stock' ? 'bg-emerald-600 text-white' : 'bg-emerald-50 text-emerald-700 hover:bg-emerald-100'">
            ✅ 充足 ({{ ingredients.filter(i => i.in_stock).length }})
        </button>
        <button 
            @click="filter = 'out_of_stock'"
            class="px-4 py-1.5 rounded-full text-sm font-bold transition-colors whitespace-nowrap"
            :class="filter === 'out_of_stock' ? 'bg-red-600 text-white' : 'bg-red-50 text-red-700 hover:bg-red-100'">
            ⚠️ 缺货 ({{ ingredients.filter(i => !i.in_stock).length }})
        </button>
    </div>

    <!-- List -->
    <div v-if="loading" class="text-center py-12 text-stone-500">
        加载中...
    </div>

    <div v-else class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4">
        <div 
            v-for="item in filteredIngredients" 
            :key="item.id"
            class="bg-white border rounded-xl p-4 flex justify-between items-center group transition-all duration-300"
            :class="item.in_stock ? 'border-stone-200 shadow-sm' : 'border-red-200 bg-red-50/30'"
        >
            <div class="flex items-center gap-3">
                <div 
                    class="w-3 h-3 rounded-full"
                    :class="item.in_stock ? 'bg-emerald-500' : 'bg-red-500'"
                ></div>
                <span class="font-bold text-stone-700" :class="{ 'line-through text-stone-400': !item.in_stock }">
                    {{ item.name }}
                </span>
            </div>
            
            <div class="flex items-center gap-2">
                <button 
                    @click="toggleStock(item)"
                    class="text-xs font-bold px-3 py-1 rounded border transition-colors"
                    :class="item.in_stock 
                        ? 'border-stone-200 text-stone-500 hover:border-red-300 hover:text-red-600 hover:bg-red-50' 
                        : 'border-emerald-200 text-emerald-600 bg-white hover:bg-emerald-50'"
                >
                    {{ item.in_stock ? '标为缺货' : '补货' }}
                </button>
                <button @click="deleteIngredient(item.id)" class="text-stone-300 hover:text-red-500 px-2 opacity-0 group-hover:opacity-100 transition-opacity">
                    ×
                </button>
            </div>
        </div>
    </div>
  </div>
</template>

