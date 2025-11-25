<script setup>
import { computed, ref, watch } from 'vue'
import { RouterView, useRoute } from 'vue-router'
import CartSidebar from './components/CartSidebar.vue'
import { cart } from './store/cart'

const route = useRoute()
const isChefMode = computed(() => route.path.startsWith('/chef'))

// 移动端菜单状态
const mobileMenuOpen = ref(false)

// 路由变化时关闭移动菜单
watch(() => route.path, () => {
  mobileMenuOpen.value = false
})
</script>

<template>
  <div class="min-h-screen bg-[#fcfaf5] text-stone-800 font-serif bg-texture">
    <header class="bg-emerald-800 text-white p-3 md:p-4 shadow-lg sticky top-0 z-30 border-b-4 border-amber-200/50">
      <div class="container mx-auto flex justify-between items-center">
        <router-link to="/" class="text-lg md:text-2xl font-bold flex items-center gap-2 md:gap-3 font-display tracking-wide hover:text-amber-100 transition-colors">
          <span class="text-2xl md:text-3xl">🍳</span> 
          <span class="hidden xs:inline">LZQ的私人厨房</span>
          <span class="xs:hidden">私人厨房</span>
        </router-link>
        
        <!-- 桌面端导航 - 客人模式 -->
        <nav v-if="!isChefMode" class="hidden md:flex items-center gap-6 text-sm font-medium">
           <router-link to="/" class="hover:text-emerald-200 transition-colors flex items-center gap-1">
             <span>🍽️</span> 首页
           </router-link>
           <router-link to="/my-orders" class="hover:text-emerald-200 transition-colors flex items-center gap-1">
             <span>🧾</span> 我的订单
           </router-link>
           <button @click="cart.isOpen = true" class="relative bg-emerald-900/50 px-3 py-1.5 rounded-full hover:bg-emerald-900 transition-colors border border-emerald-600 cursor-pointer">
              <span class="flex items-center gap-1">🛒 点餐单</span>
              <span v-if="cart.items.length > 0" class="absolute -top-1.5 -right-1.5 bg-amber-500 text-white text-[10px] font-bold rounded-full w-5 h-5 flex items-center justify-center shadow-sm border-2 border-emerald-800">
                  {{ cart.items.length }}
              </span>
           </button>
        </nav>

        <!-- 桌面端导航 - 主厨模式 -->
        <nav v-if="isChefMode" class="hidden md:flex items-center gap-6 text-sm font-medium">
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

        <!-- 移动端操作按钮 -->
        <div class="flex md:hidden items-center gap-2">
          <!-- 购物车按钮 (客人模式) -->
          <button v-if="!isChefMode" @click="cart.isOpen = true" class="relative bg-emerald-900/50 p-2 rounded-full hover:bg-emerald-900 transition-colors border border-emerald-600 cursor-pointer">
            <span class="text-lg">🛒</span>
            <span v-if="cart.items.length > 0" class="absolute -top-1 -right-1 bg-amber-500 text-white text-[10px] font-bold rounded-full w-4 h-4 flex items-center justify-center shadow-sm border border-emerald-800">
                {{ cart.items.length }}
            </span>
          </button>
          
          <!-- 汉堡菜单按钮 -->
          <button @click="mobileMenuOpen = !mobileMenuOpen" class="p-2 hover:bg-emerald-700 rounded-lg transition-colors">
            <svg v-if="!mobileMenuOpen" class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16"/>
            </svg>
            <svg v-else class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
            </svg>
          </button>
        </div>
      </div>

      <!-- 移动端下拉菜单 -->
      <Transition name="mobile-menu">
        <div v-if="mobileMenuOpen" class="md:hidden mt-3 pt-3 border-t border-emerald-700/50">
          <!-- 客人模式菜单 -->
          <nav v-if="!isChefMode" class="flex flex-col gap-2">
            <router-link to="/" class="hover:bg-emerald-700 px-3 py-2 rounded-lg transition-colors flex items-center gap-2">
              <span>🍽️</span> 首页
            </router-link>
            <router-link to="/my-orders" class="hover:bg-emerald-700 px-3 py-2 rounded-lg transition-colors flex items-center gap-2">
              <span>🧾</span> 我的订单
            </router-link>
            <button @click="cart.isOpen = true; mobileMenuOpen = false" class="hover:bg-emerald-700 px-3 py-2 rounded-lg transition-colors flex items-center gap-2 text-left w-full">
              <span>🛒</span> 点餐单
              <span v-if="cart.items.length > 0" class="bg-amber-500 text-white text-xs font-bold rounded-full px-2 py-0.5 ml-auto">
                {{ cart.items.length }}
              </span>
            </button>
          </nav>
          
          <!-- 主厨模式菜单 -->
          <nav v-else class="flex flex-col gap-2">
            <router-link to="/chef" class="hover:bg-emerald-700 px-3 py-2 rounded-lg transition-colors flex items-center gap-2">
              <span>👨‍🍳</span> 控制台
            </router-link>
            <router-link to="/chef/orders" class="hover:bg-emerald-700 px-3 py-2 rounded-lg transition-colors flex items-center gap-2">
              <span>🛎️</span> 订单
            </router-link>
            <router-link to="/chef/inventory" class="hover:bg-emerald-700 px-3 py-2 rounded-lg transition-colors flex items-center gap-2">
              <span>📦</span> 库存
            </router-link>
            <router-link to="/chef/recipes" class="hover:bg-emerald-700 px-3 py-2 rounded-lg transition-colors flex items-center gap-2">
              <span>📝</span> 食谱
            </router-link>
            <a href="/" class="bg-emerald-900/50 px-3 py-2 rounded-lg hover:bg-emerald-900 transition-colors border border-emerald-600 flex items-center gap-2 mt-2">
              <span>👋</span> 退出后台
            </a>
          </nav>
        </div>
      </Transition>
    </header>

    <main class="container mx-auto p-4 md:p-6 lg:p-8">
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

/* 移动端菜单动画 */
.mobile-menu-enter-active,
.mobile-menu-leave-active {
  transition: all 0.2s ease;
}
.mobile-menu-enter-from,
.mobile-menu-leave-to {
  opacity: 0;
  transform: translateY(-10px);
}

/* 自定义断点 - 很小的屏幕 */
@media (min-width: 360px) {
  .xs\:inline { display: inline; }
  .xs\:hidden { display: none; }
}
</style>
