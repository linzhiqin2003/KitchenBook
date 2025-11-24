<script setup>
import { cart } from '../store/cart'

const totalPrice = 0 // We don't have prices, just menu selection
</script>

<template>
  <div v-if="cart.isOpen" class="fixed inset-0 z-40 flex justify-end">
    <!-- Backdrop -->
    <div class="absolute inset-0 bg-black/30" @click="cart.isOpen = false"></div>
    
    <!-- Sidebar -->
    <div class="relative w-full max-w-md bg-white shadow-2xl h-full flex flex-col animate-slide-in">
        <div class="p-4 border-b flex justify-between items-center bg-emerald-50">
            <h2 class="text-xl font-bold text-emerald-900">您的菜单</h2>
            <button @click="cart.isOpen = false" class="text-stone-500 hover:text-stone-800">✕</button>
        </div>
        
        <div class="flex-1 overflow-y-auto p-4">
            <div v-if="cart.items.length === 0" class="text-center text-stone-500 mt-10">
                <span class="text-4xl block mb-2">🍽️</span>
                还没点菜呢
            </div>
            <div v-else class="space-y-4">
                <div v-for="item in cart.items" :key="item.recipe.id" class="flex gap-4 items-center border-b pb-4">
                    <img v-if="item.recipe.cover_image" :src="item.recipe.cover_image" class="w-16 h-16 object-cover rounded" />
                    <div v-else class="w-16 h-16 bg-stone-200 rounded flex items-center justify-center">🍳</div>
                    
                    <div class="flex-1">
                        <h4 class="font-bold text-stone-800">{{ item.recipe.title }}</h4>
                        <div class="flex items-center gap-2 mt-1">
                             <button @click="item.quantity > 1 ? item.quantity-- : cart.removeItem(item.recipe.id)" class="w-6 h-6 bg-stone-100 rounded text-stone-600">-</button>
                             <span>{{ item.quantity }}</span>
                             <button @click="item.quantity++" class="w-6 h-6 bg-stone-100 rounded text-stone-600">+</button>
                        </div>
                    </div>
                    <button @click="cart.removeItem(item.recipe.id)" class="text-red-400 hover:text-red-600">删除</button>
                </div>
            </div>
        </div>
        
        <div class="p-4 border-t bg-stone-50">
            <div class="mb-4">
                <label class="block text-sm font-bold text-stone-700 mb-1">您的称呼</label>
                <input v-model="cart.customerName" type="text" placeholder="例如：张先生 / 2号桌" class="w-full border rounded p-2 text-stone-800 focus:outline-none focus:ring-2 focus:ring-emerald-500" />
            </div>
            <button 
                @click="cart.submitOrder" 
                :disabled="cart.items.length === 0"
                class="w-full bg-emerald-700 text-white py-3 rounded-lg font-bold hover:bg-emerald-800 disabled:bg-stone-300 disabled:cursor-not-allowed transition-colors shadow-md">
                🍽️ 提交点餐单
            </button>
        </div>
    </div>
  </div>
</template>

<style scoped>
.animate-slide-in {
    animation: slideIn 0.3s ease-out;
}
@keyframes slideIn {
    from { transform: translateX(100%); }
    to { transform: translateX(0); }
}
</style>

