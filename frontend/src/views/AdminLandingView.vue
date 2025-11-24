<script setup>
import { ref, onMounted } from 'vue'

const currentTime = ref(new Date().toLocaleTimeString())
const currentDate = ref(new Date().toLocaleDateString())

onMounted(() => {
    setInterval(() => {
        currentTime.value = new Date().toLocaleTimeString()
    }, 1000)
})
</script>

<template>
  <div class="max-w-6xl mx-auto py-8">
    <!-- Header Section -->
    <div class="mb-10 flex flex-col md:flex-row md:items-end justify-between gap-4 border-b border-emerald-100 pb-6">
        <div>
            <h1 class="text-4xl font-display font-bold text-emerald-900 flex items-center gap-3">
                <span class="bg-emerald-100 p-2 rounded-lg text-3xl">👨‍🍳</span>
                厨房管理中心
            </h1>
            <p class="text-stone-500 mt-2 font-serif">主厨，准备好开始今天的烹饪了吗？</p>
        </div>
        <div class="text-right">
            <div class="text-3xl font-mono font-bold text-emerald-700">{{ currentTime }}</div>
            <div class="text-stone-400 text-sm">{{ currentDate }}</div>
        </div>
    </div>

    <!-- Main Dashboard Grid -->
    <div class="grid grid-cols-1 md:grid-cols-3 gap-8">
      
      <!-- Live Service Card -->
      <router-link to="/chef/orders" class="group relative overflow-hidden bg-white rounded-2xl shadow-sm border border-stone-100 hover:shadow-xl transition-all duration-300 hover:-translate-y-1">
        <div class="absolute top-0 right-0 p-4 opacity-10 group-hover:opacity-20 transition-opacity">
            <span class="text-9xl">🛎️</span>
        </div>
        <div class="p-8 relative z-10">
            <div class="w-14 h-14 bg-blue-50 text-blue-600 rounded-xl flex items-center justify-center text-2xl mb-6 shadow-sm group-hover:bg-blue-600 group-hover:text-white transition-colors duration-300">
                🔥
            </div>
            <h2 class="text-xl font-bold text-stone-800 mb-3 font-display">订单看板</h2>
            <p class="text-stone-500 mb-8 leading-relaxed h-12 text-sm">
                处理实时订单，管理烹饪流程。
            </p>
            <div class="flex items-center text-blue-600 font-bold group-hover:translate-x-2 transition-transform">
                进入厨房 <span class="ml-2">→</span>
            </div>
        </div>
        <div class="h-1.5 bg-blue-500 w-0 group-hover:w-full transition-all duration-500 absolute bottom-0 left-0"></div>
      </router-link>

      <!-- Inventory Management Card -->
      <router-link to="/chef/inventory" class="group relative overflow-hidden bg-white rounded-2xl shadow-sm border border-stone-100 hover:shadow-xl transition-all duration-300 hover:-translate-y-1">
        <div class="absolute top-0 right-0 p-4 opacity-10 group-hover:opacity-20 transition-opacity">
            <span class="text-9xl">📦</span>
        </div>
        <div class="p-8 relative z-10">
            <div class="w-14 h-14 bg-purple-50 text-purple-600 rounded-xl flex items-center justify-center text-2xl mb-6 shadow-sm group-hover:bg-purple-600 group-hover:text-white transition-colors duration-300">
                🍎
            </div>
            <h2 class="text-xl font-bold text-stone-800 mb-3 font-display">库存管理</h2>
            <p class="text-stone-500 mb-8 leading-relaxed h-12 text-sm">
                管理食材库存，自动更新采购清单。
            </p>
            <div class="flex items-center text-purple-600 font-bold group-hover:translate-x-2 transition-transform">
                管理库存 <span class="ml-2">→</span>
            </div>
        </div>
        <div class="h-1.5 bg-purple-500 w-0 group-hover:w-full transition-all duration-500 absolute bottom-0 left-0"></div>
      </router-link>

      <!-- Recipe Management Card -->
      <router-link to="/chef/recipes" class="group relative overflow-hidden bg-white rounded-2xl shadow-sm border border-stone-100 hover:shadow-xl transition-all duration-300 hover:-translate-y-1">
        <div class="absolute top-0 right-0 p-4 opacity-10 group-hover:opacity-20 transition-opacity">
            <span class="text-9xl">📝</span>
        </div>
        <div class="p-8 relative z-10">
            <div class="w-14 h-14 bg-amber-50 text-amber-600 rounded-xl flex items-center justify-center text-2xl mb-6 shadow-sm group-hover:bg-amber-600 group-hover:text-white transition-colors duration-300">
                🥬
            </div>
            <h2 class="text-xl font-bold text-stone-800 mb-3 font-display">食谱数据库</h2>
            <p class="text-stone-500 mb-8 leading-relaxed h-12 text-sm">
                录入新菜品，编辑私密配方。
            </p>
            <div class="flex items-center text-amber-600 font-bold group-hover:translate-x-2 transition-transform">
                管理菜单 <span class="ml-2">→</span>
            </div>
        </div>
        <div class="h-1.5 bg-amber-500 w-0 group-hover:w-full transition-all duration-500 absolute bottom-0 left-0"></div>
      </router-link>
      
    </div>

    <!-- Quick Stats / Info Row -->
    <div class="mt-8 grid grid-cols-1 md:grid-cols-3 gap-4">
        <div class="bg-emerald-50/50 rounded-xl p-6 border border-emerald-100/50 flex items-center gap-4">
            <div class="bg-white p-3 rounded-full shadow-sm text-emerald-600">📊</div>
            <div>
                <h4 class="font-bold text-emerald-900">今日概况</h4>
                <p class="text-xs text-emerald-700">准备好迎接客人了吗？</p>
            </div>
        </div>
        <div class="bg-emerald-50/50 rounded-xl p-6 border border-emerald-100/50 flex items-center gap-4">
             <div class="bg-white p-3 rounded-full shadow-sm text-emerald-600">💡</div>
             <div>
                <h4 class="font-bold text-emerald-900">小贴士</h4>
                <p class="text-xs text-emerald-700">及时更新库存状态</p>
            </div>
        </div>
        <router-link to="/" class="bg-white rounded-xl p-6 border border-stone-200 flex items-center gap-4 hover:border-emerald-300 transition-colors group">
             <div class="bg-stone-100 p-3 rounded-full shadow-sm text-stone-600 group-hover:bg-emerald-100 group-hover:text-emerald-600 transition-colors">🏠</div>
             <div>
                <h4 class="font-bold text-stone-800">返回前台</h4>
                <p class="text-xs text-stone-500">查看菜单预览</p>
            </div>
        </router-link>
    </div>
  </div>
</template>
