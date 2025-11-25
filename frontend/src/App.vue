<script setup>
import { computed } from 'vue'
import { RouterView, useRoute } from 'vue-router'
import CartSidebar from './components/CartSidebar.vue'
import { cart } from './store/cart'

const route = useRoute()
const isChefMode = computed(() => route.path.startsWith('/chef'))
</script>

<template>
  <div class="min-h-screen bg-[#fcfaf5] text-stone-800 font-serif bg-texture">
    <header class="bg-emerald-800 text-white p-4 shadow-lg sticky top-0 z-30 border-b-4 border-amber-200/50">
      <div class="container mx-auto flex justify-between items-center">
        <router-link to="/" class="text-2xl font-bold flex items-center gap-3 font-display tracking-wide hover:text-amber-100 transition-colors">
          <span class="text-3xl">🍳</span> 
          <span>LZQ的私人厨房</span>
        </router-link>
        
        <nav v-if="!isChefMode" class="flex items-center gap-6 text-sm font-medium">
           <router-link to="/" class="hover:text-emerald-200 transition-colors flex items-center gap-1">
             <span>🍽️</span> 首页
           </router-link>
           <router-link to="/my-orders" class="hover:text-emerald-200 transition-colors flex items-center gap-1">
             <span>🧾</span> 我的订单
           </router-link>
           <!-- Simple Cart Toggle -->
           <button @click="cart.isOpen = true" class="relative bg-emerald-900/50 px-3 py-1.5 rounded-full hover:bg-emerald-900 transition-colors border border-emerald-600 cursor-pointer">
              <span class="flex items-center gap-1">🛒 点餐单</span>
              <span v-if="cart.items.length > 0" class="absolute -top-1.5 -right-1.5 bg-amber-500 text-white text-[10px] font-bold rounded-full w-5 h-5 flex items-center justify-center shadow-sm border-2 border-emerald-800">
                  {{ cart.items.length }}
              </span>
           </button>
        </nav>

        <nav v-else class="flex items-center gap-6 text-sm font-medium">
           <router-link to="/chef" class="hover:text-emerald-200 transition-colors flex items-center gap-1">
             <span>👨‍🍳</span> 控制台
           </router-link>
           <router-link to="/chef/orders" class="hover:text-emerald-200 transition-colors flex items-center gap-1">
             <span>🛎️</span> 订单
           </router-link>
           <router-link to="/chef/inventory" class="hover:text-emerald-200 transition-colors flex items-center gap-1">
             <span>📦</span> 库存
           </router-link>
           <router-link to="/chef/recipes" class="hover:text-emerald-200 transition-colors flex items-center gap-1">
             <span>📝</span> 食谱
           </router-link>
           <a href="/" class="bg-emerald-900/50 px-3 py-1.5 rounded-full hover:bg-emerald-900 transition-colors border border-emerald-600 flex items-center gap-1">
              <span>👋</span> 退出后台
           </a>
        </nav>
      </div>
    </header>

    <main class="container mx-auto p-6 md:p-8">
      <RouterView />
    </main>
    
    <CartSidebar v-if="!isChefMode" />
  </div>
</template>

<style>
.font-serif {
  font-family: 'Noto Serif SC', serif;
}
.font-display {
  font-family: 'Playfair Display', serif;
}
.bg-texture {
  background-image: radial-gradient(#e5e7eb 1px, transparent 1px);
  background-size: 20px 20px;
}
</style>
