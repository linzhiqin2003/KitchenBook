<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
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
      const firstError = typeof data === 'string'
        ? data
        : data.detail || Object.values(data).flat()[0] || '操作失败'
      error.value = firstError
    } else {
      error.value = '网络错误，请稍后重试'
    }
  } finally {
    loading.value = false
  }
}

// Live time only — single quiet detail in the bottom of the brand pane
const time = ref('')
const updateClock = () => {
  const now = new Date()
  time.value = String(now.getHours()).padStart(2, '0') + ':' + String(now.getMinutes()).padStart(2, '0')
}
let clockTimer = null

// Google
const googleClientId = import.meta.env.VITE_GOOGLE_CLIENT_ID || ''
const initGoogleSignIn = () => {
  if (!googleClientId) return
  const script = document.createElement('script')
  script.src = 'https://accounts.google.com/gsi/client'
  script.async = true
  script.defer = true
  script.onload = () => {
    if (!window.google) return
    window.google.accounts.id.initialize({
      client_id: googleClientId,
      callback: handleGoogleCallback,
    })
    window.google.accounts.id.renderButton(
      document.getElementById('google-signin-btn'),
      { theme: 'filled_black', size: 'large', width: 320, shape: 'rectangular', text: 'continue_with', locale: 'zh_CN' }
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
  updateClock()
  clockTimer = setInterval(updateClock, 30_000)
  initGoogleSignIn()
})
onUnmounted(() => { if (clockTimer) clearInterval(clockTimer) })
</script>

<template>
  <div class="home-shell auth-stage min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 text-white overflow-hidden relative">
    <!-- Background — orbs only. Quieter than before. -->
    <div class="fixed inset-0 pointer-events-none overflow-hidden">
      <div class="orb orb-purple"></div>
      <div class="orb orb-cyan"></div>
      <div class="absolute inset-x-0 top-0 h-32 bg-gradient-to-b from-slate-900/50 to-transparent"></div>
      <div class="absolute inset-x-0 bottom-0 h-32 bg-gradient-to-t from-slate-900/60 to-transparent"></div>
    </div>

    <main class="auth-grid">
      <!-- LEFT brand pane (desktop only) -->
      <section class="auth-brand">
        <div class="auth-brand__top">
          <div class="auth-brand__monogram">
            <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linejoin="round">
              <path d="M12 3l2 5 5 2-5 2-2 5-2-5-5-2 5-2z"/>
            </svg>
          </div>
          <span class="auth-brand__id" data-mono>LZQ.SPACE</span>
        </div>

        <div class="auth-brand__hero">
          <h2 class="auth-brand__title">
            一个人的<br />
            <span class="auth-brand__titleAccent">工作室。</span>
          </h2>
          <p class="auth-brand__tagline">
            收纳习题、菜谱、随笔、占卜与日常账本。
          </p>
        </div>

        <div class="auth-brand__bottom">
          <div class="auth-brand__clock">
            <span class="auth-brand__clockTime" data-mono>{{ time }}</span>
            <span class="auth-brand__clockSub" data-mono>BRISTOL · LOCAL</span>
          </div>
        </div>
      </section>

      <!-- RIGHT form pane -->
      <section class="auth-form-col">
        <div class="auth-form-card">
          <div class="auth-form-head">
            <div class="auth-form-head__icon">
              <div class="logo-glow"></div>
              <div class="auth-form-head__iconInner">
                <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linejoin="round">
                  <path d="M12 3l2 5 5 2-5 2-2 5-2-5-5-2 5-2z"/>
                </svg>
              </div>
            </div>
            <div class="auth-form-head__copy">
              <h1 class="auth-form-head__title">{{ mode === 'login' ? '欢迎回来' : '新建账号' }}</h1>
              <p class="auth-form-head__sub">{{ mode === 'login' ? '登录进入工作室' : '完成注册即可开始使用' }}</p>
            </div>
          </div>

          <div class="auth-tabs grid grid-cols-2">
            <span class="auth-tabs__indicator" :class="{ 'is-register': mode === 'register' }"></span>
            <button
              type="button"
              @click="mode = 'login'; error = ''"
              :class="mode === 'login' ? 'text-white' : 'text-white/45 hover:text-white/70'"
              class="auth-tabs__btn"
            >登录</button>
            <button
              type="button"
              @click="mode = 'register'; error = ''"
              :class="mode === 'register' ? 'text-white' : 'text-white/45 hover:text-white/70'"
              class="auth-tabs__btn"
            >注册</button>
          </div>

          <form @submit.prevent="handleSubmit" class="space-y-4">
            <transition name="auth-fade">
              <div v-if="success" class="auth-notice auth-notice--ok">
                <svg width="14" height="14" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M5 10.5l3.5 3.5L15 7"/></svg>
                <span>{{ mode === 'login' ? '登录成功，正在跳转…' : '注册成功，正在跳转…' }}</span>
              </div>
            </transition>
            <transition name="auth-fade">
              <div v-if="error" class="auth-notice auth-notice--err">
                <svg width="14" height="14" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><circle cx="10" cy="10" r="7.5"/><path d="M10 6.5v4M10 13.5h.01"/></svg>
                <span>{{ error }}</span>
              </div>
            </transition>

            <div v-if="mode === 'register'" class="auth-field">
              <label class="auth-label">昵称</label>
              <input v-model="nickname" type="text" placeholder="你的昵称（选填）" class="auth-input" :disabled="loading" />
            </div>

            <div class="auth-field">
              <label class="auth-label">邮箱</label>
              <div class="auth-input-wrap">
                <svg class="auth-input__icon" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">
                  <rect x="3" y="5" width="18" height="14" rx="2"/>
                  <path d="M3 7l9 6 9-6"/>
                </svg>
                <input v-model="email" type="email" placeholder="you@example.com" class="auth-input auth-input--with-icon" :disabled="loading" autocomplete="email" />
              </div>
            </div>

            <div class="auth-field">
              <label class="auth-label">密码</label>
              <div class="auth-input-wrap">
                <svg class="auth-input__icon" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">
                  <rect x="4" y="11" width="16" height="10" rx="2"/>
                  <path d="M8 11V7a4 4 0 1 1 8 0v4"/>
                </svg>
                <input
                  v-model="password"
                  type="password"
                  :placeholder="mode === 'register' ? '至少 6 位' : '请输入密码'"
                  class="auth-input auth-input--with-icon"
                  :disabled="loading"
                  :autocomplete="mode === 'register' ? 'new-password' : 'current-password'"
                  @keyup.enter="handleSubmit"
                />
              </div>
            </div>

            <button type="submit" :disabled="loading" class="auth-submit">
              <svg v-if="loading" class="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
                <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-opacity="0.25" stroke-width="3"/>
                <path d="M22 12a10 10 0 0 0-10-10" stroke="currentColor" stroke-width="3" stroke-linecap="round"/>
              </svg>
              <span>{{ loading ? '处理中…' : (mode === 'login' ? '登录' : '注册') }}</span>
              <svg v-if="!loading" class="auth-submit__arrow w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12h14M13 6l6 6-6 6"/></svg>
            </button>
          </form>

          <div v-if="googleClientId" class="auth-divider">
            <span class="auth-divider__line"></span>
            <span class="auth-divider__label">或</span>
            <span class="auth-divider__line"></span>
          </div>
          <div v-if="googleClientId" id="google-signin-btn" class="auth-google"></div>
        </div>

        <router-link to="/" class="auth-back">
          <svg class="auth-back__arrow w-3.5 h-3.5" fill="none" stroke="currentColor" stroke-width="1.6" viewBox="0 0 24 24" stroke-linecap="round" stroke-linejoin="round">
            <path d="M15 18l-6-6 6-6"/>
          </svg>
          <span>返回首页</span>
        </router-link>
      </section>
    </main>
  </div>
</template>

<style scoped>
/* ────────── Typography ────────── */
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
[data-mono] {
  font-family: 'Geist Mono', ui-monospace, SFMono-Regular, Menlo, monospace;
  font-feature-settings: 'tnum', 'zero';
  letter-spacing: 0.04em;
}

.auth-stage { display: flex; flex-direction: column; }

/* ────────── Grid ────────── */
.auth-grid {
  flex: 1;
  display: grid;
  grid-template-columns: 1fr;
  align-items: stretch;
  position: relative;
  z-index: 5;
  min-height: 100vh;
}
@media (min-width: 980px) {
  .auth-grid {
    grid-template-columns: 1.05fr 1fr;
    max-width: 1180px;
    margin: 0 auto;
    padding: 0 clamp(24px, 4vw, 48px);
  }
}

/* ────────── Left brand pane ────────── */
.auth-brand {
  display: none;
  flex-direction: column;
  padding: 56px 56px 36px 0;
  position: relative;
}
@media (min-width: 980px) { .auth-brand { display: flex; } }

.auth-brand__top {
  display: flex;
  align-items: center;
  gap: 14px;
  margin-bottom: auto;
}
.auth-brand__monogram {
  width: 40px;
  height: 40px;
  border-radius: 12px;
  background: linear-gradient(135deg, rgba(168, 85, 247, 0.95), rgba(124, 58, 237, 0.95));
  border: 1px solid rgba(255, 255, 255, 0.12);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  color: white;
  flex-shrink: 0;
  box-shadow: 0 8px 24px -8px rgba(168, 85, 247, 0.5);
}
.auth-brand__id {
  font-size: 11px;
  letter-spacing: 0.18em;
  color: rgba(255, 255, 255, 0.65);
}

.auth-brand__hero {
  margin-top: clamp(48px, 8vh, 120px);
  margin-bottom: auto;
}
.auth-brand__title {
  font-size: clamp(2.5rem, 1.6rem + 2.4vw, 4rem);
  font-weight: 500;
  line-height: 1.05;
  margin: 0;
  color: rgba(255, 255, 255, 0.94);
}
.auth-brand__titleAccent {
  background: linear-gradient(135deg, #c4b5fd 0%, #a855f7 50%, #ec4899 100%);
  background-clip: text;
  -webkit-background-clip: text;
  color: transparent;
}
.auth-brand__tagline {
  margin-top: 22px;
  font-size: 15px;
  line-height: 1.65;
  color: rgba(255, 255, 255, 0.45);
  max-width: 36ch;
}

.auth-brand__bottom {
  margin-top: auto;
  padding-top: 32px;
}
.auth-brand__clock {
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.auth-brand__clockTime {
  font-size: 26px;
  font-weight: 300;
  color: rgba(255, 255, 255, 0.85);
  letter-spacing: -0.01em;
  font-variant-numeric: tabular-nums;
  line-height: 1;
}
.auth-brand__clockSub {
  font-size: 9.5px;
  letter-spacing: 0.18em;
  color: rgba(255, 255, 255, 0.32);
}

/* ────────── Right form pane ────────── */
.auth-form-col {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: clamp(40px, 8vw, 80px) clamp(20px, 5vw, 32px);
  gap: 16px;
}

.auth-form-card {
  position: relative;
  width: 100%;
  max-width: 400px;
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.05) 0%, rgba(255, 255, 255, 0.02) 100%);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 22px;
  padding: 28px;
  backdrop-filter: blur(28px) saturate(1.4);
  -webkit-backdrop-filter: blur(28px) saturate(1.4);
  box-shadow:
    0 1px 0 rgba(255, 255, 255, 0.06) inset,
    0 24px 60px -20px rgba(0, 0, 0, 0.5);
  animation: cardSlideIn 0.55s cubic-bezier(0.22, 0.61, 0.36, 1) backwards;
}
@keyframes cardSlideIn {
  from { opacity: 0; transform: translateY(12px) scale(0.99); }
  to { opacity: 1; transform: translateY(0) scale(1); }
}

.auth-form-head {
  display: flex;
  align-items: center;
  gap: 14px;
  padding-bottom: 22px;
  margin-bottom: 22px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
}
.auth-form-head__icon {
  position: relative;
  width: 40px;
  height: 40px;
  border-radius: 12px;
  background: linear-gradient(135deg, rgba(124, 58, 237, 0.95) 0%, rgba(168, 85, 247, 0.95) 100%);
  border: 1px solid rgba(255, 255, 255, 0.12);
  flex-shrink: 0;
}
.auth-form-head__iconInner {
  position: absolute;
  inset: 1px;
  border-radius: 11px;
  background: rgba(15, 23, 42, 0.55);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  color: white;
  z-index: 2;
}
.auth-form-head__copy { display: flex; flex-direction: column; gap: 2px; }
.auth-form-head__title {
  font-size: 19px;
  font-weight: 500;
  margin: 0;
  color: rgba(255, 255, 255, 0.96);
  font-variation-settings: 'opsz' 36;
}
.auth-form-head__sub {
  font-size: 12px;
  margin: 0;
  color: rgba(255, 255, 255, 0.45);
}

/* Tabs */
.auth-tabs {
  position: relative;
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.05);
  border-radius: 10px;
  padding: 4px;
  margin-bottom: 22px;
  gap: 0;
}
.auth-tabs__indicator {
  position: absolute;
  top: 4px;
  bottom: 4px;
  left: 4px;
  width: calc(50% - 4px);
  border-radius: 7px;
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.13), rgba(255, 255, 255, 0.06));
  box-shadow:
    0 1px 0 rgba(255, 255, 255, 0.1) inset,
    0 4px 12px -4px rgba(0, 0, 0, 0.3);
  transition: transform 0.32s cubic-bezier(0.65, 0, 0.35, 1);
  pointer-events: none;
  z-index: 0;
}
.auth-tabs__indicator.is-register { transform: translateX(100%); }
.auth-tabs__btn {
  position: relative;
  z-index: 1;
  background: transparent;
  border: none;
  padding: 7px;
  font-size: 13px;
  font-weight: 500;
  letter-spacing: 0.02em;
  cursor: pointer;
  border-radius: 7px;
  transition: color 0.2s ease;
}

/* Notices */
.auth-notice {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 9px 12px;
  border-radius: 10px;
  font-size: 12.5px;
  font-weight: 500;
}
.auth-notice--ok {
  background: rgba(16, 185, 129, 0.08);
  border: 1px solid rgba(16, 185, 129, 0.2);
  color: rgba(110, 231, 183, 0.95);
}
.auth-notice--err {
  background: rgba(239, 68, 68, 0.08);
  border: 1px solid rgba(239, 68, 68, 0.22);
  color: rgba(252, 165, 165, 0.95);
}
.auth-fade-enter-active,
.auth-fade-leave-active { transition: opacity 0.22s ease, transform 0.22s ease; }
.auth-fade-enter-from,
.auth-fade-leave-to { opacity: 0; transform: translateY(-4px); }

/* Field */
.auth-field { display: flex; flex-direction: column; gap: 7px; }
.auth-label {
  font-size: 10.5px;
  letter-spacing: 0.13em;
  color: rgba(255, 255, 255, 0.45);
  font-family: 'Geist Mono', ui-monospace, monospace;
  text-transform: uppercase;
  font-weight: 500;
}

.auth-input-wrap { position: relative; }
.auth-input__icon {
  position: absolute;
  left: 13px;
  top: 50%;
  transform: translateY(-50%);
  color: rgba(255, 255, 255, 0.35);
  pointer-events: none;
  transition: color 0.18s ease;
}
.auth-input-wrap:focus-within .auth-input__icon { color: rgba(196, 181, 253, 0.85); }

.auth-input {
  width: 100%;
  padding: 11px 14px;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.07);
  border-radius: 10px;
  color: white;
  font-size: 14px;
  outline: none;
  transition: border-color 0.18s ease, background 0.18s ease, box-shadow 0.18s ease;
}
.auth-input--with-icon { padding-left: 38px; }
.auth-input::placeholder { color: rgba(255, 255, 255, 0.28); }
.auth-input:hover:not(:focus):not(:disabled) {
  border-color: rgba(255, 255, 255, 0.12);
  background: rgba(255, 255, 255, 0.045);
}
.auth-input:focus {
  border-color: rgba(167, 139, 250, 0.55);
  background: rgba(255, 255, 255, 0.05);
  box-shadow: 0 0 0 3px rgba(139, 92, 246, 0.13);
}
.auth-input:disabled { opacity: 0.5; cursor: not-allowed; }

/* Submit */
.auth-submit {
  width: 100%;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  padding: 12px 18px;
  font-size: 14px;
  font-weight: 600;
  color: white;
  background: linear-gradient(135deg, #7c3aed 0%, #9333ea 50%, #a855f7 100%);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 11px;
  cursor: pointer;
  margin-top: 6px;
  box-shadow:
    0 1px 0 rgba(255, 255, 255, 0.16) inset,
    0 8px 24px -8px rgba(139, 92, 246, 0.5);
  transition: transform 0.18s ease, box-shadow 0.18s ease, filter 0.18s ease;
}
.auth-submit:hover:not(:disabled) {
  filter: brightness(1.06);
  box-shadow:
    0 1px 0 rgba(255, 255, 255, 0.18) inset,
    0 10px 30px -8px rgba(139, 92, 246, 0.6);
}
.auth-submit:hover:not(:disabled) .auth-submit__arrow { transform: translateX(3px); }
.auth-submit:active:not(:disabled) { transform: translateY(0.5px); }
.auth-submit:disabled {
  cursor: not-allowed;
  background: linear-gradient(135deg, #4b5563 0%, #6b7280 100%);
  box-shadow: none;
  opacity: 0.6;
}
.auth-submit__arrow { transition: transform 0.18s ease; }

/* Divider */
.auth-divider {
  display: flex;
  align-items: center;
  gap: 12px;
  margin: 22px 0 14px;
}
.auth-divider__line {
  flex: 1; height: 1px;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.1), transparent);
}
.auth-divider__label {
  font-size: 11px;
  color: rgba(255, 255, 255, 0.32);
}

.auth-google { display: flex; justify-content: center; }
.auth-google :deep(iframe) {
  border-radius: 12px !important;
  filter: brightness(0.92) saturate(0.95);
}

/* Back link */
.auth-back {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 10px;
  color: rgba(255, 255, 255, 0.4);
  font-size: 12.5px;
  text-decoration: none;
  transition: color 0.18s ease;
}
.auth-back:hover { color: rgba(255, 255, 255, 0.7); }
.auth-back:hover .auth-back__arrow { transform: translateX(-3px); }
.auth-back__arrow { transition: transform 0.18s ease; }

/* Logo glow on the form-card icon */
.logo-glow {
  position: absolute;
  inset: -4px;
  border-radius: 14px;
  background: radial-gradient(circle, rgba(168, 85, 247, 0.5), rgba(124, 58, 237, 0.18) 50%, transparent 70%);
  filter: blur(14px);
  z-index: 0;
  animation: logoBreath 5.5s ease-in-out infinite;
  pointer-events: none;
}
@keyframes logoBreath {
  0%, 100% { opacity: 0.18; transform: scale(0.96); }
  50%      { opacity: 0.32; transform: scale(1.04); }
}

/* Background orbs — toned down further */
.orb {
  position: absolute;
  border-radius: 50%;
  filter: blur(110px);
}
.orb-purple {
  width: 460px; height: 460px;
  background: rgba(139, 92, 246, 0.13);
  top: -10%; left: -8%;
  animation: orbFloat1 28s ease-in-out infinite;
}
.orb-cyan {
  width: 360px; height: 360px;
  background: rgba(6, 182, 212, 0.07);
  bottom: -6%; right: -8%;
  animation: orbFloat2 32s ease-in-out infinite;
}
@keyframes orbFloat1 {
  0%, 100% { transform: translate(0, 0); }
  50% { transform: translate(40px, 30px); }
}
@keyframes orbFloat2 {
  0%, 100% { transform: translate(0, 0); }
  50% { transform: translate(-40px, -25px); }
}

@media (prefers-reduced-motion: reduce) {
  .orb, .logo-glow, .auth-form-card { animation: none !important; }
}
</style>
