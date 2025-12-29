<script setup>
import { ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import axios from 'axios'
import API_BASE_URL from '../config/api'
import { auth } from '../store/auth'

const router = useRouter()
const route = useRoute()

const username = ref('')
const password = ref('')
const error = ref('')
const loading = ref(false)
const success = ref(false)

const handleLogin = async () => {
    if (!username.value || !password.value) {
        error.value = '请输入用户名和密码'
        return
    }
    
    loading.value = true
    error.value = ''
    success.value = false
    
    try {
        const response = await axios.post(`${API_BASE_URL}/api/chef/login/`, {
            username: username.value,
            password: password.value
        })
        
        if (response.data.success) {
            // 更新 auth store（这会同时更新 localStorage）
            auth.login(response.data.token)
            
            // 显示成功提示
            success.value = true
            
            // 获取重定向目标，默认跳转到 chef 后台
            const redirectPath = route.query.redirect || '/kitchen/chef'
            
            // 稍微延迟后跳转，让用户看到成功提示
            setTimeout(() => {
                router.push(redirectPath)
            }, 500)
        }
    } catch (err) {
        if (err.response?.status === 401) {
            error.value = '用户名或密码错误'
        } else {
            error.value = '登录失败，请稍后重试'
        }
    } finally {
        loading.value = false
    }
}
</script>

<template>
  <div class="min-h-screen bg-gradient-to-br from-stone-100 via-emerald-50 to-stone-100 flex items-center justify-center p-4">
    <!-- 背景装饰 -->
    <div class="absolute inset-0 overflow-hidden pointer-events-none">
      <div class="absolute top-20 left-10 text-8xl opacity-10 rotate-12">🍳</div>
      <div class="absolute bottom-20 right-10 text-8xl opacity-10 -rotate-12">👨‍🍳</div>
      <div class="absolute top-1/2 left-1/4 text-6xl opacity-5">🥬</div>
      <div class="absolute top-1/3 right-1/4 text-6xl opacity-5">🍖</div>
    </div>
    
    <div class="w-full max-w-md relative">
      <!-- Logo -->
      <div class="text-center mb-8">
        <div class="inline-flex items-center justify-center w-20 h-20 bg-white rounded-full shadow-lg mb-4">
          <span class="text-4xl">👨‍🍳</span>
        </div>
        <h1 class="text-2xl font-bold text-stone-800">主厨后台</h1>
        <p class="text-stone-500 text-sm mt-1">登录以管理您的厨房</p>
      </div>
      
      <!-- 登录卡片 -->
      <div class="bg-white rounded-2xl shadow-xl p-8 border border-stone-100">
        <form @submit.prevent="handleLogin" class="space-y-6">
          <!-- 成功提示 -->
          <div v-if="success" class="bg-emerald-50 border border-emerald-200 text-emerald-700 px-4 py-3 rounded-lg text-sm flex items-center gap-2">
            <span class="animate-bounce">✅</span>
            登录成功，正在跳转...
          </div>
          
          <!-- 错误提示 -->
          <div v-if="error" class="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg text-sm flex items-center gap-2">
            <span>⚠️</span>
            {{ error }}
          </div>
          
          <!-- 用户名 -->
          <div>
            <label class="block text-sm font-medium text-stone-700 mb-2">用户名</label>
            <div class="relative">
              <span class="absolute left-3 top-1/2 -translate-y-1/2 text-stone-400">👤</span>
              <input 
                v-model="username"
                type="text" 
                placeholder="请输入用户名"
                class="w-full pl-10 pr-4 py-3 border border-stone-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent transition-all"
                :disabled="loading"
              />
            </div>
          </div>
          
          <!-- 密码 -->
          <div>
            <label class="block text-sm font-medium text-stone-700 mb-2">密码</label>
            <div class="relative">
              <span class="absolute left-3 top-1/2 -translate-y-1/2 text-stone-400">🔒</span>
              <input 
                v-model="password"
                type="password" 
                placeholder="请输入密码"
                class="w-full pl-10 pr-4 py-3 border border-stone-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent transition-all"
                :disabled="loading"
                @keyup.enter="handleLogin"
              />
            </div>
          </div>
          
          <!-- 登录按钮 -->
          <button 
            type="submit"
            :disabled="loading"
            class="w-full bg-gradient-to-r from-emerald-600 to-emerald-500 text-white py-3.5 rounded-xl font-bold hover:from-emerald-500 hover:to-emerald-400 disabled:from-stone-300 disabled:to-stone-300 disabled:cursor-not-allowed transition-all shadow-lg shadow-emerald-500/25 flex items-center justify-center gap-2"
          >
            <span v-if="loading" class="animate-spin">⏳</span>
            <span v-else>🚀</span>
            {{ loading ? '登录中...' : '进入后台' }}
          </button>
        </form>
        
        <!-- 提示 -->
        <div class="mt-6 pt-6 border-t border-stone-100 text-center">
          <p class="text-xs text-stone-400">
            🔐 仅限授权人员访问
          </p>
        </div>
      </div>
      
      <!-- 返回首页 -->
      <div class="text-center mt-6">
        <router-link to="/kitchen" class="text-stone-500 hover:text-emerald-600 text-sm flex items-center justify-center gap-1 transition-colors">
          <span>←</span> 返回餐厅首页
        </router-link>
      </div>
    </div>
  </div>
</template>

