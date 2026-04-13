<script setup>
import { computed, ref, watch } from 'vue'
import { RouterView, useRoute, useRouter } from 'vue-router'
import CartSidebar from './components/CartSidebar.vue'
import AiChatWidget from './components/AiChatWidget.vue'
import { cart } from './store/cart'
import { auth } from './store/auth'
import { useAuthStore } from './store/auth'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

// 个人首页独立布局
const isPortfolioHome = computed(() => route.path === '/')
// 统一登录页独立布局
const isAuthPage = computed(() => route.path === '/login')
// 更新为新的 /kitchen 路径结构
const isChefMode = computed(() => route.path.startsWith('/kitchen/chef'))
const isLoginPage = computed(() => route.path === '/kitchen/chef/login')
const isAiLabPage = computed(() => route.path.startsWith('/ai-lab'))
// 博客页面独立布局 (/blog)
const isBlogPage = computed(() => route.path === '/blog' || route.path.startsWith('/blog/'))
// QuestionGen 刷题页面独立布局 (/questiongen)
const isQuestionGenPage = computed(() => route.path === '/questiongen')
// Games 页面独立布局 (/games)
const isGamesPage = computed(() => route.path === '/games' || route.path.startsWith('/games/'))
// Tarot 页面独立布局 (/tarot)
const isTarotPage = computed(() => route.path.startsWith('/tarot'))
// Kitchen 首页模式 - 排除chef和ai-lab
const isKitchenPage = computed(() => route.path.startsWith('/kitchen') && !isChefMode.value && !isAiLabPage.value)

// 移动端菜单状态
const mobileMenuOpen = ref(false)

// 路由变化时关闭移动菜单
watch(() => route.path, () => {
  mobileMenuOpen.value = false
})

// 登出（厨师模式退出）
const handleLogout = () => {
  auth.logout()
  authStore.chefLogout()
  router.push('/kitchen/chef/login')
}

// 全站登出
const handleFullLogout = () => {
  authStore.logout()
  router.push('/login')
}
</script>

<template>
  <!-- 个人网站首页独立模式 -->
  <div v-if="isPortfolioHome" class="min-h-screen">
    <RouterView />
  </div>

  <!-- 统一登录页独立模式 -->
  <div v-else-if="isAuthPage" class="min-h-screen">
    <RouterView />
  </div>

  <!-- AI Lab 全屏模式 -->
  <div v-else-if="isAiLabPage" class="min-h-screen">
    <RouterView />
  </div>
  
  <!-- 博客独立页面模式 -->
  <div v-else-if="isBlogPage" class="min-h-screen">
    <RouterView />
  </div>
  
  <!-- QuestionGen 刷题独立页面模式 -->
  <div v-else-if="isQuestionGenPage" class="min-h-screen">
    <RouterView />
  </div>

  <!-- Games 独立页面模式 -->
  <div v-else-if="isGamesPage" class="min-h-screen">
    <RouterView />
  </div>

  <!-- Tarot 独立页面模式 -->
  <div v-else-if="isTarotPage" class="min-h-screen">
    <RouterView />
  </div>
  
  <!-- 普通页面模式 -->
  <div v-else class="min-h-screen bg-[#fcfaf5] text-stone-800 font-serif bg-texture flex flex-col">
    <header v-if="!isLoginPage" class="bg-emerald-800 text-white p-3 md:p-4 shadow-lg sticky top-0 z-30 border-b-4 border-amber-200/50">
      <div class="container mx-auto flex justify-between items-center">
        <router-link to="/kitchen" class="text-lg md:text-2xl font-bold flex items-center gap-2 md:gap-3 font-display tracking-wide hover:text-amber-100 transition-colors">
          <span class="text-2xl md:text-3xl">🍳</span> 
          <span class="hidden xs:inline">LZQ的私人厨房</span>
          <span class="xs:hidden">私人厨房</span>
        </router-link>
        
        <!-- 桌面端导航 - 客人模式 -->
        <nav v-if="!isChefMode" class="hidden md:flex items-center gap-6 text-sm font-medium">
           <router-link to="/kitchen" class="hover:text-emerald-200 transition-colors flex items-center gap-1">
             <span>🍽️</span> 首页
           </router-link>
           <router-link to="/kitchen/my-orders" class="hover:text-emerald-200 transition-colors flex items-center gap-1">
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
           <router-link to="/kitchen/chef" class="hover:text-emerald-200 transition-colors flex items-center gap-1">
             <span>👨‍🍳</span> 控制台
           </router-link>
           <router-link to="/kitchen/chef/orders" class="hover:text-emerald-200 transition-colors flex items-center gap-1">
             <span>🛎️</span> 订单
           </router-link>
           <router-link to="/kitchen/chef/inventory" class="hover:text-emerald-200 transition-colors flex items-center gap-1">
             <span>📦</span> 库存
           </router-link>
           <router-link to="/kitchen/chef/recipes" class="hover:text-emerald-200 transition-colors flex items-center gap-1">
             <span>📖</span> 食谱
           </router-link>
           <router-link to="/blog/studio" class="hover:text-emerald-200 transition-colors flex items-center gap-1">
             <span>✍️</span> 博客
           </router-link>
           <button @click="handleLogout" class="bg-red-900/50 px-3 py-1.5 rounded-full hover:bg-red-900 transition-colors border border-red-600 flex items-center gap-1 cursor-pointer">
              <span>🚪</span> 退出登录
           </button>
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
            <router-link to="/kitchen" class="hover:bg-emerald-700 px-3 py-2 rounded-lg transition-colors flex items-center gap-2">
              <span>🍽️</span> 首页
            </router-link>
            <router-link to="/kitchen/my-orders" class="hover:bg-emerald-700 px-3 py-2 rounded-lg transition-colors flex items-center gap-2">
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
            <router-link to="/kitchen/chef" class="hover:bg-emerald-700 px-3 py-2 rounded-lg transition-colors flex items-center gap-2">
              <span>👨‍🍳</span> 控制台
            </router-link>
            <router-link to="/kitchen/chef/orders" class="hover:bg-emerald-700 px-3 py-2 rounded-lg transition-colors flex items-center gap-2">
              <span>🛎️</span> 订单
            </router-link>
            <router-link to="/kitchen/chef/inventory" class="hover:bg-emerald-700 px-3 py-2 rounded-lg transition-colors flex items-center gap-2">
              <span>📦</span> 库存
            </router-link>
            <router-link to="/kitchen/chef/recipes" class="hover:bg-emerald-700 px-3 py-2 rounded-lg transition-colors flex items-center gap-2">
              <span>📖</span> 食谱
            </router-link>
            <router-link to="/blog/studio" class="hover:bg-emerald-700 px-3 py-2 rounded-lg transition-colors flex items-center gap-2">
              <span>✍️</span> 博客
            </router-link>
            <button @click="handleLogout" class="bg-red-900/50 px-3 py-2 rounded-lg hover:bg-red-900 transition-colors border border-red-600 flex items-center gap-2 mt-2 w-full cursor-pointer">
              <span>🚪</span> 退出登录
            </button>
          </nav>
        </div>
      </Transition>
    </header>

    <main :class="[isLoginPage ? '' : 'container mx-auto p-4 md:p-6 lg:p-8', 'flex-grow']">
      <RouterView />
    </main>
    
    <!-- Footer 占位空间 - 防止内容被固定底栏遮挡 -->
    <div v-if="!isChefMode && !isLoginPage" class="h-24 md:h-20"></div>
    
    <!-- 底部 Footer - 固定悬浮在底部，仅在客人模式显示 -->
    <footer v-if="!isChefMode && !isLoginPage" class="fixed bottom-0 left-0 right-0 z-20 border-t border-stone-200/60 bg-gradient-to-b from-stone-50/95 to-stone-100/95 backdrop-blur-sm shadow-[0_-4px_20px_rgba(0,0,0,0.08)]">
      <div class="container mx-auto px-4 py-3 md:py-4">
        <div class="flex flex-col md:flex-row items-center justify-between gap-2 md:gap-4 text-sm text-stone-500">
          <!-- 左侧：版权 -->
          <div class="flex items-center gap-2">
            <span>🍳</span>
            <span>© 2026 LZQ的私人厨房</span>
          </div>
          
          <!-- 中间：链接 -->
          <div class="flex flex-col sm:flex-row items-center gap-1 sm:gap-2 text-stone-400">
            <div class="flex items-center gap-1">
              <span>也逛逛</span>
              <router-link to="/blog" class="text-stone-600 hover:text-purple-600 transition-colors font-medium underline underline-offset-2 decoration-stone-300 hover:decoration-purple-400">
                我的技术博客
              </router-link>
              <span>？</span>
            </div>
            <div class="flex items-center gap-1">
              <span>或者体验</span>
              <router-link to="/kitchen/ai-lab" class="text-stone-600 hover:text-pink-600 transition-colors font-medium underline underline-offset-2 decoration-stone-300 hover:decoration-pink-400">
                更强大的AI开源模型
              </router-link>
              <span>？</span>
            </div>
          </div>
          
          <!-- 右侧：签名 -->
          <div class="flex items-center gap-1.5 text-stone-400">
            <span>Made with</span>
            <span class="text-red-400">❤️</span>
            <span>&</span>
            <span>☕</span>
          </div>
        </div>
      </div>
    </footer>
    
    <CartSidebar v-if="!isChefMode" />
    
    <!-- AI 聊天助手 - 仅在客人模式显示 -->
    <AiChatWidget v-if="!isChefMode && !isLoginPage" />
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
