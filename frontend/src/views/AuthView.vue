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
  <div class="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 text-white overflow-hidden flex items-center justify-center p-4 home-shell">
    <!-- Dynamic Background -->
    <div class="fixed inset-0 pointer-events-none overflow-hidden">
      <div class="orb orb-purple"></div>
      <div class="orb orb-cyan"></div>
      <div class="orb orb-orange"></div>
      <div class="absolute inset-0 bg-[linear-gradient(rgba(255,255,255,0.015)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,0.015)_1px,transparent_1px)] bg-[size:60px_60px]"></div>
    </div>

    <div class="w-full max-w-[400px] relative z-10 auth-card-enter">
      <!-- Header: refined logo + title cluster -->
      <div class="text-center mb-7">
        <div class="relative inline-block mb-5">
          <div class="logo-glow"></div>
          <div class="w-14 h-14 rounded-2xl bg-gradient-to-br from-violet-500 via-purple-500 to-fuchsia-500 p-[1.5px] shadow-lg shadow-purple-500/20 relative z-10">
            <div class="w-full h-full rounded-[14px] bg-slate-800/95 backdrop-blur-sm flex items-center justify-center">
              <svg class="w-6 h-6 text-white/90" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linejoin="round">
                <path d="M12 3l2 5 5 2-5 2-2 5-2-5-5-2 5-2z"/>
                <path d="M19 14l.7 1.8 1.8.7-1.8.7-.7 1.8-.7-1.8-1.8-.7 1.8-.7z" fill="currentColor" fill-opacity="0.6" stroke="none"/>
              </svg>
            </div>
          </div>
        </div>
        <h1 class="text-3xl font-medium bg-clip-text text-transparent bg-gradient-to-b from-white to-white/70 tracking-tight">
          LZQ Space
        </h1>
        <p class="text-white/45 text-sm mt-2.5 tracking-wide">
          {{ mode === 'login' ? '登录以继续' : '创建你的账号' }}
        </p>
      </div>

      <!-- Auth Card -->
      <div class="glass-card rounded-[22px] p-7 border border-white/[0.08] relative">
        <!-- Subtle inner top highlight — gives the glass a hand-lit edge -->
        <div class="absolute inset-x-7 top-0 h-px bg-gradient-to-r from-transparent via-white/15 to-transparent pointer-events-none"></div>

        <!-- Tab Switch — sliding indicator -->
        <div class="auth-tabs relative grid grid-cols-2 bg-white/[0.045] rounded-[10px] p-1 mb-7 border border-white/[0.04]">
          <span class="auth-tabs__indicator" :class="{ 'is-register': mode === 'register' }"></span>
          <button
            type="button"
            @click="mode = 'login'; error = ''"
            :class="mode === 'login' ? 'text-white' : 'text-white/45 hover:text-white/70'"
            class="relative z-10 py-1.5 rounded-[7px] text-[13px] font-medium tracking-wide transition-colors duration-200"
          >
            登录
          </button>
          <button
            type="button"
            @click="mode = 'register'; error = ''"
            :class="mode === 'register' ? 'text-white' : 'text-white/45 hover:text-white/70'"
            class="relative z-10 py-1.5 rounded-[7px] text-[13px] font-medium tracking-wide transition-colors duration-200"
          >
            注册
          </button>
        </div>

        <form @submit.prevent="handleSubmit" class="space-y-4">
          <!-- Success -->
          <transition name="auth-fade">
            <div v-if="success" class="bg-emerald-500/[0.08] border border-emerald-500/20 text-emerald-300 px-3.5 py-2.5 rounded-xl text-[13px] flex items-center gap-2">
              <svg class="w-3.5 h-3.5 shrink-0" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M5 10.5l3.5 3.5L15 7"/>
              </svg>
              <span>{{ mode === 'login' ? '登录成功，正在跳转…' : '注册成功，正在跳转…' }}</span>
            </div>
          </transition>

          <!-- Error -->
          <transition name="auth-fade">
            <div v-if="error" class="bg-red-500/[0.08] border border-red-500/20 text-red-300 px-3.5 py-2.5 rounded-xl text-[13px] flex items-center gap-2">
              <svg class="w-3.5 h-3.5 shrink-0" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">
                <circle cx="10" cy="10" r="7.5"/>
                <path d="M10 6.5v4M10 13.5h.01"/>
              </svg>
              <span>{{ error }}</span>
            </div>
          </transition>

          <!-- Nickname (register only) -->
          <div v-if="mode === 'register'" class="auth-field">
            <label class="auth-label">昵称</label>
            <input
              v-model="nickname"
              type="text"
              placeholder="你的昵称（选填）"
              class="auth-input"
              :disabled="loading"
            />
          </div>

          <!-- Email -->
          <div class="auth-field">
            <label class="auth-label">邮箱</label>
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
          <div class="auth-field">
            <label class="auth-label">密码</label>
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
            class="auth-submit"
          >
            <svg v-if="loading" class="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
              <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-opacity="0.25" stroke-width="3"/>
              <path d="M22 12a10 10 0 0 0-10-10" stroke="currentColor" stroke-width="3" stroke-linecap="round"/>
            </svg>
            <span>{{ loading ? '处理中…' : (mode === 'login' ? '登录' : '注册') }}</span>
            <svg v-if="!loading" class="auth-submit__arrow w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
              <path d="M5 12h14M13 6l6 6-6 6"/>
            </svg>
          </button>
        </form>

        <!-- Divider -->
        <div v-if="googleClientId" class="flex items-center gap-3 my-5">
          <div class="flex-1 h-px bg-gradient-to-r from-transparent to-white/10"></div>
          <span class="text-[10px] tracking-[0.18em] uppercase text-white/30 font-medium">或继续使用</span>
          <div class="flex-1 h-px bg-gradient-to-l from-transparent to-white/10"></div>
        </div>

        <!-- Google Sign In -->
        <div v-if="googleClientId" id="google-signin-btn" class="flex justify-center auth-google"></div>
      </div>

      <!-- Back to Home -->
      <div class="text-center mt-5">
        <router-link to="/" class="auth-back text-white/35 hover:text-white/65 text-[13px] inline-flex items-center justify-center gap-1.5 transition-colors">
          <svg class="auth-back__arrow w-3.5 h-3.5" fill="none" stroke="currentColor" stroke-width="1.6" viewBox="0 0 24 24" stroke-linecap="round" stroke-linejoin="round">
            <path d="M15 18l-6-6 6-6"/>
          </svg>
          <span>返回首页</span>
        </router-link>
      </div>
    </div>
  </div>
</template>

<style scoped>
/* ========== Typography overrides — refined font stack on the dark layout ========== */
.home-shell {
  font-family: 'Geist', ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, 'Helvetica Neue', sans-serif;
  font-feature-settings: 'cv11', 'ss01';
  letter-spacing: -0.005em;
}
.home-shell h1, .home-shell h2 {
  font-family: 'Bricolage Grotesque', 'Geist', ui-sans-serif, system-ui, sans-serif;
  letter-spacing: -0.022em;
  font-variation-settings: 'opsz' 60;
}
.home-shell .auth-input {
  font-family: 'Geist', ui-sans-serif, system-ui, sans-serif;
  letter-spacing: -0.003em;
}

/* Glass Card — slightly more refined edge + subtle inner glow */
.glass-card {
  background: linear-gradient(
    180deg,
    rgba(255, 255, 255, 0.045) 0%,
    rgba(255, 255, 255, 0.025) 100%
  );
  backdrop-filter: blur(28px) saturate(1.4);
  -webkit-backdrop-filter: blur(28px) saturate(1.4);
  box-shadow:
    0 1px 0 rgba(255, 255, 255, 0.04) inset,
    0 24px 60px -20px rgba(0, 0, 0, 0.5);
}

/* Field group — tighter label/input pairing */
.auth-field { display: flex; flex-direction: column; gap: 6px; }
.auth-label {
  font-size: 11px;
  letter-spacing: 0.08em;
  color: rgba(255, 255, 255, 0.5);
  font-family: 'Geist Mono', ui-monospace, monospace;
  text-transform: uppercase;
  font-weight: 500;
}

/* Refined Input */
.auth-input {
  width: 100%;
  padding: 11px 14px;
  background: rgba(255, 255, 255, 0.035);
  border: 1px solid rgba(255, 255, 255, 0.07);
  border-radius: 10px;
  color: white;
  font-size: 14px;
  outline: none;
  transition: border-color 0.18s ease, background 0.18s ease, box-shadow 0.18s ease;
}
.auth-input::placeholder { color: rgba(255, 255, 255, 0.28); }
.auth-input:hover:not(:focus):not(:disabled) {
  border-color: rgba(255, 255, 255, 0.12);
  background: rgba(255, 255, 255, 0.05);
}
.auth-input:focus {
  border-color: rgba(167, 139, 250, 0.55);
  background: rgba(255, 255, 255, 0.05);
  box-shadow: 0 0 0 3px rgba(139, 92, 246, 0.14);
}
.auth-input:disabled { opacity: 0.5; cursor: not-allowed; }

/* Sliding tab indicator — refined active state without per-button bg flicker */
.auth-tabs__indicator {
  position: absolute;
  top: 4px;
  bottom: 4px;
  left: 4px;
  width: calc(50% - 4px);
  border-radius: 7px;
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.14), rgba(255, 255, 255, 0.07));
  box-shadow:
    0 1px 0 rgba(255, 255, 255, 0.1) inset,
    0 4px 12px -4px rgba(0, 0, 0, 0.3);
  transition: transform 0.32s cubic-bezier(0.65, 0, 0.35, 1);
  pointer-events: none;
  z-index: 0;
}
.auth-tabs__indicator.is-register { transform: translateX(100%); }

/* Submit button — same brand gradient, refined geometry + arrow micro-motion */
.auth-submit {
  width: 100%;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  padding: 12px 18px;
  font-size: 14px;
  font-weight: 600;
  letter-spacing: 0.005em;
  color: white;
  background: linear-gradient(135deg, #7c3aed 0%, #9333ea 50%, #a855f7 100%);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 11px;
  cursor: pointer;
  margin-top: 8px;
  box-shadow:
    0 1px 0 rgba(255, 255, 255, 0.15) inset,
    0 8px 24px -8px rgba(139, 92, 246, 0.5),
    0 2px 6px -2px rgba(124, 58, 237, 0.4);
  transition: transform 0.18s ease, box-shadow 0.18s ease, filter 0.18s ease;
}
.auth-submit:hover:not(:disabled) {
  filter: brightness(1.06);
  box-shadow:
    0 1px 0 rgba(255, 255, 255, 0.18) inset,
    0 10px 30px -8px rgba(139, 92, 246, 0.6),
    0 2px 6px -2px rgba(124, 58, 237, 0.5);
}
.auth-submit:hover:not(:disabled) .auth-submit__arrow { transform: translateX(3px); }
.auth-submit:active:not(:disabled) { transform: translateY(0.5px); }
.auth-submit:disabled {
  cursor: not-allowed;
  background: linear-gradient(135deg, #4b5563 0%, #6b7280 100%);
  box-shadow: none;
  opacity: 0.65;
}
.auth-submit__arrow { transition: transform 0.18s ease; }

/* Google iframe button — match the card's radius and tone down its harshness */
.auth-google :deep(iframe) {
  border-radius: 12px !important;
  filter: brightness(0.96);
}

/* Back link — subtle arrow shimmy on hover */
.auth-back {
  letter-spacing: 0.02em;
  padding: 4px 8px;
  border-radius: 6px;
}
.auth-back:hover .auth-back__arrow { transform: translateX(-3px); }
.auth-back__arrow { transition: transform 0.18s ease; }

/* Logo glow — slower and softer */
.logo-glow {
  position: absolute;
  inset: -10px;
  border-radius: 1.25rem;
  background: radial-gradient(circle, rgba(168, 85, 247, 0.5), rgba(124, 58, 237, 0.2) 50%, transparent 70%);
  filter: blur(18px);
  z-index: 0;
  animation: logoBreath 5.5s ease-in-out infinite;
}

@keyframes logoBreath {
  0%, 100% { opacity: 0.18; transform: scale(0.96); }
  50%      { opacity: 0.34; transform: scale(1.04); }
}

/* Notice transitions */
.auth-fade-enter-active,
.auth-fade-leave-active { transition: opacity 0.2s ease, transform 0.2s ease; }
.auth-fade-enter-from,
.auth-fade-leave-to { opacity: 0; transform: translateY(-4px); }

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
