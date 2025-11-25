<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'
import API_BASE_URL from '../config/api'
import { cart } from '../store/cart'

const myOrders = ref([])
const loading = ref(true)
const errorMessage = ref('')

const fetchMyOrders = async () => {
    if (cart.myOrderIds.length === 0) {
        loading.value = false
        return
    }
    
    loading.value = true
    errorMessage.value = ''
    
    try {
        // Fetch orders one by one and track which ones are valid
        const validOrderIds = []
        const orderPromises = cart.myOrderIds.map(async id => {
            try {
                const response = await axios.get(`${API_BASE_URL}/api/orders/${id}/`)
                validOrderIds.push(id)
                return response.data
            } catch (e) {
                // Order doesn't exist anymore (404)
                console.warn(`Order ${id} not found, removing from local storage`)
                return null
            }
        })
        
        const results = await Promise.all(orderPromises)
        
        // Update localStorage to only keep valid order IDs
        cart.myOrderIds = validOrderIds
        localStorage.setItem('kitchen_book_orders', JSON.stringify(validOrderIds))
        
        // Filter out nulls and sort by creation date
        myOrders.value = results
            .filter(r => r !== null)
            .sort((a, b) => new Date(b.created_at) - new Date(a.created_at))
            
    } catch (e) {
        console.error(e)
        errorMessage.value = '加载订单时出错，请稍后重试'
    } finally {
        loading.value = false
    }
}

const clearInvalidOrders = () => {
    cart.myOrderIds = []
    localStorage.removeItem('kitchen_book_orders')
    myOrders.value = []
    alert('已清除失效订单记录')
}

onMounted(fetchMyOrders)
</script>

<template>
  <div class="max-w-4xl mx-auto">
    <div class="mb-6 md:mb-8 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
        <div>
            <h2 class="text-2xl md:text-3xl font-bold text-emerald-900 mb-1 md:mb-2">我的订单</h2>
            <p class="text-stone-600 text-sm md:text-base">追踪您的美食制作进度</p>
        </div>
        <div class="flex gap-2 md:gap-3">
            <button @click="fetchMyOrders" class="text-emerald-600 hover:text-emerald-800 font-bold text-xs md:text-sm flex items-center gap-1">
                <span>↻</span> 刷新
            </button>
            <button v-if="cart.myOrderIds.length > 0" @click="clearInvalidOrders" class="text-stone-400 hover:text-red-600 text-[10px] md:text-xs flex items-center gap-1">
                🗑️ 清除
            </button>
        </div>
    </div>

    <div v-if="errorMessage" class="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700">
        {{ errorMessage }}
    </div>

    <div v-if="loading" class="py-12 text-center text-stone-500">
        <div class="animate-pulse">加载中...</div>
    </div>

    <div v-else-if="myOrders.length === 0" class="py-12 text-center bg-white rounded-xl shadow-sm border border-stone-100">
        <span class="text-4xl block mb-4">🍽️</span>
        <p class="text-lg text-stone-600 mb-4">您还没有点过餐哦</p>
        <router-link to="/" class="inline-block bg-emerald-600 text-white px-6 py-2 rounded-full hover:bg-emerald-700 transition-colors">
            去点餐
        </router-link>
    </div>

    <div v-else class="space-y-4 md:space-y-6">
        <div v-for="order in myOrders" :key="order.id" class="bg-white rounded-xl shadow-sm border border-stone-100 overflow-hidden">
            <!-- Header -->
            <div class="p-3 md:p-4 bg-stone-50 border-b border-stone-100 flex flex-col sm:flex-row justify-between items-start sm:items-center gap-2">
                <div class="text-stone-500 text-xs md:text-sm">
                    订单 #{{ order.id }} · {{ new Date(order.created_at).toLocaleString() }}
                </div>
                <div class="px-2 md:px-3 py-1 rounded-full text-[10px] md:text-xs font-bold uppercase tracking-wider flex items-center gap-1 md:gap-2"
                    :class="{
                        'bg-yellow-100 text-yellow-800': order.status === 'pending',
                        'bg-blue-100 text-blue-800': order.status === 'cooking',
                        'bg-green-100 text-green-800': order.status === 'completed'
                    }">
                    <span v-if="order.status === 'pending'" class="animate-pulse">●</span>
                    <span v-else-if="order.status === 'cooking'" class="animate-spin">◐</span>
                    <span v-else>●</span>
                    
                    <span v-if="order.status === 'pending'">等待接单</span>
                    <span v-else-if="order.status === 'cooking'">烹饪中...</span>
                    <span v-else>已出餐</span>
                </div>
            </div>
            
            <!-- Items -->
            <div class="p-3 md:p-4">
                <ul class="space-y-2 md:space-y-3">
                    <li v-for="item in order.items" :key="item.id" class="flex justify-between items-center">
                        <div class="flex items-center gap-2 md:gap-3 min-w-0">
                            <div class="w-10 h-10 md:w-12 md:h-12 bg-stone-100 rounded overflow-hidden flex-shrink-0">
                                <img v-if="item.recipe_details && item.recipe_details.cover_image" :src="item.recipe_details.cover_image" class="w-full h-full object-cover" />
                                <div v-else class="w-full h-full flex items-center justify-center text-base md:text-lg">🥘</div>
                            </div>
                            <span class="font-bold text-stone-800 text-sm md:text-base truncate">{{ item.recipe_title }}</span>
                        </div>
                        <span class="font-mono text-stone-500 text-sm md:text-base flex-shrink-0 ml-2">x{{ item.quantity }}</span>
                    </li>
                </ul>
            </div>
            
            <!-- Footer -->
            <div v-if="order.status === 'completed'" class="p-2 md:p-3 bg-green-50/50 text-center text-green-800 text-xs md:text-sm font-bold border-t border-green-100">
                ✨ 美味已送达，祝您用餐愉快！
            </div>
             <div v-else-if="order.status === 'cooking'" class="p-2 md:p-3 bg-blue-50/50 text-center text-blue-800 text-xs md:text-sm font-bold border-t border-blue-100">
                🔥 厨房正在热火朝天地为您制作...
            </div>
        </div>
    </div>
  </div>
</template>
