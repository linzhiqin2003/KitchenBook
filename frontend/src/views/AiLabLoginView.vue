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
            auth.login(response.data.token)
            success.value = true
            
            const redirectPath = route.query.redirect || '/ai-lab'
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
  <div class="min-h-screen bg-black flex items-center justify-center p-4 relative overflow-hidden">
    <!-- Background Effects -->
    <div class="absolute inset-0 overflow-hidden pointer-events-none">
      <!-- Gradient orbs -->
      <div class="absolute top-1/4 left-1/4 w-96 h-96 bg-blue-500/10 rounded-full blur-3xl"></div>
      <div class="absolute bottom-1/4 right-1/4 w-80 h-80 bg-purple-500/10 rounded-full blur-3xl"></div>
      <!-- Grid pattern -->
      <div class="absolute inset-0 bg-[linear-gradient(rgba(255,255,255,0.02)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,0.02)_1px,transparent_1px)] bg-[size:50px_50px]"></div>
    </div>
    
    <div class="w-full max-w-md relative z-10">
      <!-- Logo -->
      <div class="text-center mb-8">
        <div class="inline-flex items-center justify-center w-20 h-20 bg-gradient-to-br from-blue-500/20 to-purple-500/20 rounded-2xl border border-white/10 mb-4 backdrop-blur-xl">
          <span class="text-4xl">🤖</span>
        </div>
        <h1 class="text-2xl font-bold text-white">AI Lab</h1>
        <p class="text-white/40 text-sm mt-1">登录以访问 AI 实验室</p>
      </div>
      
      <!-- Login Card -->
      <div class="ios-glass rounded-2xl p-8 border border-white/10">
        <form @submit.prevent="handleLogin" class="space-y-6">
          <!-- Success Message -->
          <div v-if="success" class="bg-green-500/10 border border-green-500/20 text-green-400 px-4 py-3 rounded-xl text-sm flex items-center gap-2">
            <span class="animate-bounce">✅</span>
            登录成功，正在跳转...
          </div>
          
          <!-- Error Message -->
          <div v-if="error" class="bg-red-500/10 border border-red-500/20 text-red-400 px-4 py-3 rounded-xl text-sm flex items-center gap-2">
            <span>⚠️</span>
            {{ error }}
          </div>
          
          <!-- Username -->
          <div>
            <label class="block text-sm font-medium text-white/60 mb-2">用户名</label>
            <div class="relative">
              <span class="absolute left-4 top-1/2 -translate-y-1/2 text-white/30">👤</span>
              <input 
                v-model="username"
                type="text" 
                placeholder="请输入用户名"
                class="w-full pl-12 pr-4 py-3.5 bg-white/5 border border-white/10 rounded-xl text-white placeholder-white/30 focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-transparent transition-all"
                :disabled="loading"
              />
            </div>
          </div>
          
          <!-- Password -->
          <div>
            <label class="block text-sm font-medium text-white/60 mb-2">密码</label>
            <div class="relative">
              <span class="absolute left-4 top-1/2 -translate-y-1/2 text-white/30">🔒</span>
              <input 
                v-model="password"
                type="password" 
                placeholder="请输入密码"
                class="w-full pl-12 pr-4 py-3.5 bg-white/5 border border-white/10 rounded-xl text-white placeholder-white/30 focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-transparent transition-all"
                :disabled="loading"
                @keyup.enter="handleLogin"
              />
            </div>
          </div>
          
          <!-- Login Button -->
          <button 
            type="submit"
            :disabled="loading"
            class="w-full bg-gradient-to-r from-blue-600 to-purple-600 text-white py-3.5 rounded-xl font-bold hover:from-blue-500 hover:to-purple-500 disabled:from-gray-600 disabled:to-gray-600 disabled:cursor-not-allowed transition-all shadow-lg shadow-blue-500/25 flex items-center justify-center gap-2"
          >
            <span v-if="loading" class="animate-spin">⏳</span>
            <span v-else>🚀</span>
            {{ loading ? '登录中...' : '进入 AI Lab' }}
          </button>
        </form>
        
        <!-- Footer -->
        <div class="mt-6 pt-6 border-t border-white/5 text-center">
          <p class="text-xs text-white/30">
            🔐 仅限授权用户访问
          </p>
        </div>
      </div>
      
      <!-- Back Link -->
      <div class="text-center mt-6">
        <router-link to="/" class="text-white/40 hover:text-white/60 text-sm flex items-center justify-center gap-1 transition-colors">
          <span>←</span> 返回首页
        </router-link>
      </div>
    </div>
  </div>
</template>

<style scoped>
.ios-glass {
  background: rgba(28, 28, 30, 0.8);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
}
</style>
