<script setup>
import { ref, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '../store/auth'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()

const mode = ref('login') // 'login' | 'register'
const email = ref('')
const password = ref('')
const nickname = ref('')
const error = ref('')
const loading = ref(false)
const success = ref(false)

const handleSubmit = async () => {
  if (!email.value || !password.value) {
    error.value = mode.value === 'login' ? '请输入邮箱和密码' : '请填写所有必填项'
    return
  }

  loading.value = true
  error.value = ''
  success.value = false

  try {
    if (mode.value === 'login') {
      await authStore.login(email.value, password.value)
    } else {
      await authStore.register(email.value, password.value, nickname.value)
    }
    success.value = true
    const redirectPath = route.query.redirect || '/kitchen'
    setTimeout(() => router.push(redirectPath), 400)
  } catch (err) {
    const data = err.response?.data
    if (err.response?.status === 401) {
      error.value = '邮箱或密码错误'
    } else if (data) {
      // Extract first error message from DRF response
      const firstError = typeof data === 'string' ? data
        : data.detail || Object.values(data).flat()[0] || '操作失败'
      error.value = firstError
    } else {
      error.value = '网络错误，请稍后重试'
    }
  } finally {
    loading.value = false
  }
}

// Google Login
const googleClientId = import.meta.env.VITE_GOOGLE_CLIENT_ID || ''

const initGoogleSignIn = () => {
  if (!googleClientId) return

  const script = document.createElement('script')
  script.src = 'https://accounts.google.com/gsi/client'
  script.async = true
  script.defer = true
  script.onload = () => {
    window.google.accounts.id.initialize({
      client_id: googleClientId,
      callback: handleGoogleCallback,
    })
    window.google.accounts.id.renderButton(
      document.getElementById('google-signin-btn'),
      {
        theme: 'filled_black',
        size: 'large',
        width: '100%',
        shape: 'pill',
        text: 'continue_with',
        locale: 'zh_CN',
      }
    )
  }
  document.head.appendChild(script)
}

const handleGoogleCallback = async (response) => {
  loading.value = true
  error.value = ''
  try {
    await authStore.googleLogin(response.credential)
    success.value = true
    const redirectPath = route.query.redirect || '/kitchen'
    setTimeout(() => router.push(redirectPath), 400)
  } catch (err) {
    error.value = err.response?.data?.detail || 'Google 登录失败'
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  initGoogleSignIn()
})
</script>

<template>
  <div class="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 text-white overflow-hidden flex items-center justify-center p-4">
    <!-- Dynamic Background -->
    <div class="fixed inset-0 pointer-events-none overflow-hidden">
      <div class="orb orb-purple"></div>
      <div class="orb orb-cyan"></div>
      <div class="orb orb-orange"></div>
      <div class="absolute inset-0 bg-[linear-gradient(rgba(255,255,255,0.015)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,0.015)_1px,transparent_1px)] bg-[size:60px_60px]"></div>
    </div>

    <div class="w-full max-w-md relative z-10 auth-card-enter">
      <!-- Logo -->
      <div class="text-center mb-8">
        <div class="relative inline-block mb-4">
          <div class="logo-glow"></div>
          <div class="w-20 h-20 rounded-2xl bg-gradient-to-br from-violet-500 via-purple-500 to-fuchsia-500 p-[2px] shadow-2xl shadow-purple-500/25 relative z-10">
            <div class="w-full h-full rounded-[14px] bg-slate-800/90 backdrop-blur-sm flex items-center justify-center">
              <svg class="w-10 h-10 text-white/90" viewBox="0 0 24 24" fill="currentColor">
                <path d="M12 1.5l2 5.5 5.5 2-5.5 2-2 5.5-2-5.5L4.5 9l5.5-2 2-5.5z" fill-opacity="0.92"/>
                <path d="M20 12l.8 2.2 2.2.8-2.2.8-.8 2.2-.8-2.2-2.2-.8 2.2-.8.8-2.2z" fill-opacity="0.5"/>
              </svg>
            </div>
          </div>
        </div>
        <h1 class="text-2xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-white via-white to-white/80">
          LZQ Space
        </h1>
        <p class="text-white/40 text-sm mt-1">{{ mode === 'login' ? '登录以继续' : '创建你的账号' }}</p>
      </div>

      <!-- Auth Card -->
      <div class="glass-card rounded-3xl p-8 border border-white/10">
        <!-- Tab Switch -->
        <div class="flex bg-white/[0.06] rounded-xl p-1 mb-6">
          <button
            @click="mode = 'login'; error = ''"
            :class="mode === 'login' ? 'bg-white/[0.12] text-white shadow-sm' : 'text-white/50 hover:text-white/70'"
            class="flex-1 py-2 rounded-lg text-sm font-medium transition-all duration-200"
          >
            登录
          </button>
          <button
            @click="mode = 'register'; error = ''"
            :class="mode === 'register' ? 'bg-white/[0.12] text-white shadow-sm' : 'text-white/50 hover:text-white/70'"
            class="flex-1 py-2 rounded-lg text-sm font-medium transition-all duration-200"
          >
            注册
          </button>
        </div>

        <form @submit.prevent="handleSubmit" class="space-y-5">
          <!-- Success -->
          <div v-if="success" class="bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 px-4 py-3 rounded-xl text-sm flex items-center gap-2">
            <span class="animate-bounce">&#10003;</span>
            {{ mode === 'login' ? '登录成功，正在跳转...' : '注册成功，正在跳转...' }}
          </div>

          <!-- Error -->
          <div v-if="error" class="bg-red-500/10 border border-red-500/20 text-red-400 px-4 py-3 rounded-xl text-sm flex items-center gap-2">
            <svg class="w-4 h-4 shrink-0" fill="currentColor" viewBox="0 0 20 20">
              <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd"/>
            </svg>
            {{ error }}
          </div>

          <!-- Nickname (register only) -->
          <div v-if="mode === 'register'">
            <label class="block text-sm font-medium text-white/60 mb-2">昵称</label>
            <input
              v-model="nickname"
              type="text"
              placeholder="你的昵称（选填）"
              class="auth-input"
              :disabled="loading"
            />
          </div>

          <!-- Email -->
          <div>
            <label class="block text-sm font-medium text-white/60 mb-2">邮箱</label>
            <input
              v-model="email"
              type="email"
              placeholder="your@email.com"
              class="auth-input"
              :disabled="loading"
              autocomplete="email"
            />
          </div>

          <!-- Password -->
          <div>
            <label class="block text-sm font-medium text-white/60 mb-2">密码</label>
            <input
              v-model="password"
              type="password"
              :placeholder="mode === 'register' ? '至少 6 位' : '请输入密码'"
              class="auth-input"
              :disabled="loading"
              autocomplete="current-password"
              @keyup.enter="handleSubmit"
            />
          </div>

          <!-- Submit Button -->
          <button
            type="submit"
            :disabled="loading"
            class="w-full py-3.5 rounded-xl font-bold transition-all duration-300 flex items-center justify-center gap-2 bg-gradient-to-r from-violet-600 to-purple-600 hover:from-violet-500 hover:to-purple-500 disabled:from-gray-600 disabled:to-gray-600 disabled:cursor-not-allowed shadow-lg shadow-violet-500/25 hover:shadow-violet-500/40"
          >
            <svg v-if="loading" class="w-5 h-5 animate-spin" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"/>
            </svg>
            {{ loading ? '处理中...' : (mode === 'login' ? '登录' : '注册') }}
          </button>
        </form>

        <!-- Divider -->
        <div v-if="googleClientId" class="flex items-center gap-3 my-6">
          <div class="flex-1 h-px bg-white/10"></div>
          <span class="text-xs text-white/30">或</span>
          <div class="flex-1 h-px bg-white/10"></div>
        </div>

        <!-- Google Sign In -->
        <div v-if="googleClientId" id="google-signin-btn" class="flex justify-center"></div>
      </div>

      <!-- Back to Home -->
      <div class="text-center mt-6">
        <router-link to="/" class="text-white/40 hover:text-white/60 text-sm flex items-center justify-center gap-1.5 transition-colors">
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7"/>
          </svg>
          返回首页
        </router-link>
      </div>
    </div>
  </div>
</template>

<style scoped>
/* Glass Card */
.glass-card {
  background: rgba(255, 255, 255, 0.04);
  backdrop-filter: blur(24px);
  -webkit-backdrop-filter: blur(24px);
}

/* Input Style */
.auth-input {
  width: 100%;
  padding: 0.875rem 1rem;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 0.75rem;
  color: white;
  font-size: 0.875rem;
  outline: none;
  transition: all 0.2s;
}

.auth-input::placeholder {
  color: rgba(255, 255, 255, 0.3);
}

.auth-input:focus {
  border-color: rgba(139, 92, 246, 0.5);
  box-shadow: 0 0 0 3px rgba(139, 92, 246, 0.15);
}

.auth-input:disabled {
  opacity: 0.5;
}

/* Logo Glow */
.logo-glow {
  position: absolute;
  inset: -8px;
  border-radius: 1.25rem;
  background: linear-gradient(135deg, #a855f7, #7c3aed, #d946ef);
  opacity: 0.35;
  filter: blur(16px);
  z-index: 0;
  animation: logoBreath 3s ease-in-out infinite;
}

@keyframes logoBreath {
  0%, 100% { opacity: 0.25; transform: scale(1); }
  50% { opacity: 0.5; transform: scale(1.06); }
}

/* Card Enter Animation */
.auth-card-enter {
  animation: cardSlideIn 0.6s ease-out;
}

@keyframes cardSlideIn {
  from {
    opacity: 0;
    transform: translateY(24px) scale(0.97);
  }
  to {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}

/* Floating Orbs */
.orb {
  position: absolute;
  border-radius: 50%;
  filter: blur(80px);
}

.orb-purple {
  width: 400px;
  height: 400px;
  background: rgba(139, 92, 246, 0.12);
  top: -10%;
  left: -10%;
  animation: orbFloat1 20s ease-in-out infinite;
}

.orb-cyan {
  width: 350px;
  height: 350px;
  background: rgba(6, 182, 212, 0.1);
  bottom: -5%;
  right: -10%;
  animation: orbFloat2 25s ease-in-out infinite;
}

.orb-orange {
  width: 300px;
  height: 300px;
  background: rgba(251, 146, 60, 0.08);
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  animation: orbFloat3 18s ease-in-out infinite;
}

@keyframes orbFloat1 {
  0%, 100% { transform: translate(0, 0); }
  33% { transform: translate(60px, 40px); }
  66% { transform: translate(-30px, 60px); }
}

@keyframes orbFloat2 {
  0%, 100% { transform: translate(0, 0); }
  33% { transform: translate(-50px, -30px); }
  66% { transform: translate(40px, -50px); }
}

@keyframes orbFloat3 {
  0%, 100% { transform: translate(-50%, -50%); }
  33% { transform: translate(-40%, -55%); }
  66% { transform: translate(-55%, -45%); }
}
</style>
