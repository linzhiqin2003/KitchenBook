<script setup>
import { ref, onMounted, computed } from 'vue'
import axios from 'axios'

const orders = ref([])
const loading = ref(true)

const fetchOrders = async () => {
  try {
    const response = await axios.get('http://127.0.0.1:8000/api/orders/')
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
        await axios.patch(`http://127.0.0.1:8000/api/orders/${order.id}/`, { status })
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
  <div class="p-6 max-w-6xl mx-auto">
    <div class="flex justify-between items-center mb-8">
        <div>
            <h1 class="text-3xl font-bold text-stone-800 flex items-center gap-3">
                👨‍🍳 主厨看板
            </h1>
            <p class="text-stone-500 mt-1">实时订单与采购管理</p>
        </div>
        <div class="flex gap-3">
            <router-link to="/chef/inventory" class="bg-amber-100 text-amber-800 px-4 py-2 rounded-lg font-bold hover:bg-amber-200 transition-colors flex items-center gap-2">
                <span>📦</span> 管理库存
            </router-link>
            <button @click="fetchOrders" class="bg-stone-200 hover:bg-stone-300 px-4 py-2 rounded-lg text-stone-700 font-bold transition-colors">
                ↻ 刷新
            </button>
        </div>
    </div>
    
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-8">
        <!-- Orders Column -->
        <div>
            <h2 class="text-2xl font-bold text-emerald-800 mb-4 flex items-center gap-2">
                📜 点餐单
                <span class="text-sm font-normal bg-emerald-100 text-emerald-800 px-2 rounded-full">{{ orders.filter(o => o.status !== 'completed').length }} 待处理</span>
            </h2>
            <div v-if="loading" class="text-stone-500">加载中...</div>
            <div v-else-if="orders.length === 0" class="text-stone-500 italic bg-white p-8 rounded-xl border border-stone-200 text-center">
                暂无订单，喝杯咖啡休息一下吧 ☕️
            </div>
            <div v-else class="space-y-4 max-h-[80vh] overflow-y-auto pr-2">
                <div v-for="order in orders" :key="order.id" class="bg-white p-5 rounded shadow-sm border-l-4 transition-all hover:shadow-md" :class="{
                    'border-yellow-400': order.status === 'pending',
                    'border-blue-400': order.status === 'cooking',
                    'border-green-400': order.status === 'completed',
                    'opacity-60': order.status === 'completed'
                }">
                    <div class="flex justify-between items-start mb-3">
                        <div>
                            <span class="font-bold text-lg text-stone-800">{{ order.customer_name }}</span>
                            <div class="text-stone-400 text-xs mt-1">{{ new Date(order.created_at).toLocaleString() }}</div>
                        </div>
                        <span class="px-2 py-1 rounded text-xs font-bold uppercase tracking-wider" :class="{
                             'bg-yellow-100 text-yellow-800': order.status === 'pending',
                             'bg-blue-100 text-blue-800': order.status === 'cooking',
                             'bg-green-100 text-green-800': order.status === 'completed'
                        }">{{ order.status }}</span>
                    </div>
                    
                    <ul class="mb-4 space-y-2 bg-stone-50 p-3 rounded">
                        <li v-for="item in order.items" :key="item.id" class="text-stone-700 font-medium flex justify-between">
                            <span>{{ item.recipe_title }}</span>
                            <span class="text-stone-500">x{{ item.quantity }}</span>
                        </li>
                    </ul>
                    
                    <div class="flex gap-2 justify-end items-center">
                        <!-- Link to read recipe details for cooking -->
                        <div v-if="order.status === 'cooking'" class="mr-auto flex gap-2">
                            <router-link v-for="item in order.items" :key="item.id" :to="{name: 'recipe-book', params: {id: item.recipe}}" class="text-xs bg-stone-100 px-2 py-1 rounded hover:bg-stone-200 text-stone-600 flex items-center gap-1" target="_blank">
                                📖 {{ item.recipe_title }}
                            </router-link>
                        </div>

                        <button v-if="order.status === 'pending'" @click="updateStatus(order, 'cooking')" class="bg-blue-500 text-white px-4 py-2 rounded text-sm font-bold hover:bg-blue-600 shadow-sm transition-colors">Start Cooking 🔥</button>
                        <button v-if="order.status === 'cooking'" @click="updateStatus(order, 'completed')" class="bg-green-500 text-white px-4 py-2 rounded text-sm font-bold hover:bg-green-600 shadow-sm transition-colors">Complete ✅</button>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- Shopping List Column -->
        <div>
            <h2 class="text-2xl font-bold text-amber-800 mb-4 flex items-center gap-2">
                🛒 采购清单 (缺货食材)
            </h2>
            <div class="bg-amber-50 p-6 rounded-lg shadow-inner border border-amber-200 relative overflow-hidden min-h-[200px]">
                 <div class="absolute top-0 right-0 opacity-10 text-9xl pointer-events-none">🥬</div>
                <div v-if="Object.keys(aggregatedShoppingList).length === 0" class="text-stone-500 italic text-center py-12 relative z-10">
                    <div class="text-4xl mb-2">✨</div>
                    <p>库存充足，无需采购！</p>
                    <p class="text-xs mt-2 text-amber-700/50">(已自动过滤掉库存中有的食材)</p>
                </div>
                <ul v-else class="space-y-3 relative z-10">
                    <li v-for="(amounts, name) in aggregatedShoppingList" :key="name" class="flex justify-between items-baseline border-b border-amber-200/50 pb-2 last:border-0">
                        <span class="font-bold text-stone-800 text-lg flex items-center gap-2">
                            <span class="w-2 h-2 rounded-full bg-red-400"></span>
                            {{ name }}
                        </span>
                        <div class="text-right text-sm">
                            <div v-for="(amt, idx) in amounts" :key="idx" class="text-stone-600 font-mono">{{ amt }}</div>
                        </div>
                    </li>
                </ul>
            </div>
            <div class="mt-4 bg-blue-50 p-4 rounded border border-blue-100 text-sm text-blue-800 flex gap-2">
                <span>💡</span>
                <p>提示：如果在库存管理中将食材标记为 <b>"有货"</b>，它们将不再出现在此清单中。</p>
            </div>
        </div>
    </div>
  </div>
</template>
