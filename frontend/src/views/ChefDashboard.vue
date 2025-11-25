<script setup>
import { ref, onMounted, computed } from 'vue'
import axios from 'axios'
import API_BASE_URL from '../config/api'

const orders = ref([])
const loading = ref(true)

const fetchOrders = async () => {
  try {
    const response = await axios.get(`${API_BASE_URL}/api/orders/`)
    orders.value = response.data
  } catch (error) {
    console.error('Fetch orders failed', error)
  } finally {
    loading.value = false
  }
}

onMounted(fetchOrders)

const updateStatus = async (order, status) => {
    try {
        await axios.patch(`${API_BASE_URL}/api/orders/${order.id}/`, { status })
        order.status = status
        // Refetch to update stock usage implications if we implemented that
        // For now, just UI update
    } catch (e) {
        alert('Update failed')
    }
}

const aggregatedShoppingList = computed(() => {
    const groups = {}
    const pendingOrders = orders.value.filter(o => o.status === 'pending')
    
    pendingOrders.forEach(order => {
        order.items.forEach(item => {
            // Check if recipe_details exists (it should with new serializer)
            if (item.recipe_details && item.recipe_details.ingredients) {
                item.recipe_details.ingredients.forEach(ing => {
                    // Skip if we already have it in stock
                    if (ing.in_stock) return

                    if (!groups[ing.ingredient_name]) groups[ing.ingredient_name] = []
                    // Rough display: "200g (x1)"
                    groups[ing.ingredient_name].push(`${ing.quantity} (x${item.quantity})`)
                })
            }
        })
    })
    return groups
})
</script>

<template>
  <div class="p-2 md:p-6 max-w-6xl mx-auto">
    <div class="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 mb-6 md:mb-8">
        <div>
            <h1 class="text-xl md:text-3xl font-bold text-stone-800 flex items-center gap-2 md:gap-3">
                👨‍🍳 主厨看板
            </h1>
            <p class="text-stone-500 mt-1 text-sm md:text-base">实时订单与采购管理</p>
        </div>
        <div class="flex gap-2 md:gap-3 w-full sm:w-auto">
            <router-link to="/chef/inventory" class="flex-1 sm:flex-none bg-amber-100 text-amber-800 px-3 md:px-4 py-2 rounded-lg font-bold hover:bg-amber-200 transition-colors flex items-center justify-center gap-1 md:gap-2 text-sm md:text-base">
                <span>📦</span> <span class="hidden xs:inline">管理</span>库存
            </router-link>
            <button @click="fetchOrders" class="bg-stone-200 hover:bg-stone-300 px-3 md:px-4 py-2 rounded-lg text-stone-700 font-bold transition-colors text-sm md:text-base">
                ↻ 刷新
            </button>
        </div>
    </div>
    
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-4 md:gap-8">
        <!-- Orders Column -->
        <div>
            <h2 class="text-lg md:text-2xl font-bold text-emerald-800 mb-3 md:mb-4 flex items-center gap-2 flex-wrap">
                📜 点餐单
                <span class="text-xs md:text-sm font-normal bg-emerald-100 text-emerald-800 px-2 rounded-full">{{ orders.filter(o => o.status !== 'completed').length }} 待处理</span>
            </h2>
            <div v-if="loading" class="text-stone-500">加载中...</div>
            <div v-else-if="orders.length === 0" class="text-stone-500 italic bg-white p-8 rounded-xl border border-stone-200 text-center">
                暂无订单，喝杯咖啡休息一下吧 ☕️
            </div>
            <div v-else class="space-y-3 md:space-y-4 max-h-[60vh] md:max-h-[80vh] overflow-y-auto pr-1 md:pr-2">
                <div v-for="order in orders" :key="order.id" class="bg-white p-3 md:p-5 rounded shadow-sm border-l-4 transition-all hover:shadow-md" :class="{
                    'border-yellow-400': order.status === 'pending',
                    'border-blue-400': order.status === 'cooking',
                    'border-green-400': order.status === 'completed',
                    'opacity-60': order.status === 'completed'
                }">
                    <div class="flex justify-between items-start mb-2 md:mb-3">
                        <div class="min-w-0 flex-1">
                            <span class="font-bold text-base md:text-lg text-stone-800 truncate block">{{ order.customer_name }}</span>
                            <div class="text-stone-400 text-[10px] md:text-xs mt-1">{{ new Date(order.created_at).toLocaleString() }}</div>
                        </div>
                        <span class="px-2 py-1 rounded text-[10px] md:text-xs font-bold uppercase tracking-wider flex-shrink-0 ml-2" :class="{
                             'bg-yellow-100 text-yellow-800': order.status === 'pending',
                             'bg-blue-100 text-blue-800': order.status === 'cooking',
                             'bg-green-100 text-green-800': order.status === 'completed'
                        }">{{ order.status }}</span>
                    </div>
                    
                    <ul class="mb-3 md:mb-4 space-y-1.5 md:space-y-2 bg-stone-50 p-2 md:p-3 rounded">
                        <li v-for="item in order.items" :key="item.id" class="text-stone-700 font-medium flex justify-between text-sm md:text-base">
                            <span class="truncate">{{ item.recipe_title }}</span>
                            <span class="text-stone-500 flex-shrink-0 ml-2">x{{ item.quantity }}</span>
                        </li>
                    </ul>
                    
                    <div class="flex flex-col sm:flex-row gap-2 justify-end items-stretch sm:items-center">
                        <!-- Link to read recipe details for cooking -->
                        <div v-if="order.status === 'cooking'" class="sm:mr-auto flex flex-wrap gap-1 md:gap-2">
                            <router-link v-for="item in order.items" :key="item.id" :to="{name: 'recipe-book', params: {id: item.recipe}}" class="text-[10px] md:text-xs bg-stone-100 px-2 py-1 rounded hover:bg-stone-200 text-stone-600 flex items-center gap-1" target="_blank">
                                📖 <span class="truncate max-w-[80px] md:max-w-none">{{ item.recipe_title }}</span>
                            </router-link>
                        </div>

                        <button v-if="order.status === 'pending'" @click="updateStatus(order, 'cooking')" class="bg-blue-500 text-white px-3 md:px-4 py-2 rounded text-xs md:text-sm font-bold hover:bg-blue-600 shadow-sm transition-colors w-full sm:w-auto">开始制作 🔥</button>
                        <button v-if="order.status === 'cooking'" @click="updateStatus(order, 'completed')" class="bg-green-500 text-white px-3 md:px-4 py-2 rounded text-xs md:text-sm font-bold hover:bg-green-600 shadow-sm transition-colors w-full sm:w-auto">完成 ✅</button>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- Shopping List Column -->
        <div>
            <h2 class="text-lg md:text-2xl font-bold text-amber-800 mb-3 md:mb-4 flex items-center gap-2">
                🛒 采购清单
            </h2>
            <div class="bg-amber-50 p-4 md:p-6 rounded-lg shadow-inner border border-amber-200 relative overflow-hidden min-h-[150px] md:min-h-[200px]">
                 <div class="absolute top-0 right-0 opacity-10 text-6xl md:text-9xl pointer-events-none">🥬</div>
                <div v-if="Object.keys(aggregatedShoppingList).length === 0" class="text-stone-500 italic text-center py-8 md:py-12 relative z-10">
                    <div class="text-3xl md:text-4xl mb-2">✨</div>
                    <p class="text-sm md:text-base">库存充足，无需采购！</p>
                    <p class="text-[10px] md:text-xs mt-2 text-amber-700/50">(已自动过滤掉库存中有的食材)</p>
                </div>
                <ul v-else class="space-y-2 md:space-y-3 relative z-10">
                    <li v-for="(amounts, name) in aggregatedShoppingList" :key="name" class="flex justify-between items-baseline border-b border-amber-200/50 pb-2 last:border-0">
                        <span class="font-bold text-stone-800 text-sm md:text-lg flex items-center gap-1.5 md:gap-2">
                            <span class="w-1.5 md:w-2 h-1.5 md:h-2 rounded-full bg-red-400"></span>
                            {{ name }}
                        </span>
                        <div class="text-right text-xs md:text-sm">
                            <div v-for="(amt, idx) in amounts" :key="idx" class="text-stone-600 font-mono">{{ amt }}</div>
                        </div>
                    </li>
                </ul>
            </div>
            <div class="mt-3 md:mt-4 bg-blue-50 p-3 md:p-4 rounded border border-blue-100 text-xs md:text-sm text-blue-800 flex gap-2">
                <span>💡</span>
                <p>提示：在库存管理中将食材标记为 <b>"有货"</b>，它们将不再出现在此清单中。</p>
            </div>
        </div>
    </div>
  </div>
</template>
