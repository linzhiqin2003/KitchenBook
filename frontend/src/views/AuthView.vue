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

// Live time + date in the brand panel
const time = ref('')
const dateLabel = ref('')
const updateClock = () => {
  const now = new Date()
  time.value = String(now.getHours()).padStart(2, '0') + ':' + String(now.getMinutes()).padStart(2, '0')
  dateLabel.value = now.toLocaleDateString('en-US', {
    weekday: 'short', month: 'short', day: 'numeric', year: 'numeric',
  }).toUpperCase()
}
let clockTimer = null

// Spaces — quiet preview of what lives behind the door
const spaces = [
  { mono: 'KB', label: 'Kitchen' },
  { mono: 'QG', label: 'Practice' },
  { mono: 'AI', label: 'AI Lab' },
  { mono: 'TR', label: 'Tarot' },
  { mono: 'GM', label: 'Games' },
  { mono: 'BL', label: 'Blog' },
]

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
    <!-- ─── Background layers ────────────────────────────────────────── -->
    <div class="fixed inset-0 pointer-events-none overflow-hidden">
      <div class="orb orb-purple"></div>
      <div class="orb orb-cyan"></div>
      <div class="orb orb-orange"></div>
      <!-- Grid overlay -->
      <div class="absolute inset-0 bg-[linear-gradient(rgba(255,255,255,0.012)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,0.012)_1px,transparent_1px)] bg-[size:64px_64px]"></div>
      <!-- Constellation lines (decorative SVG) -->
      <svg class="absolute inset-0 w-full h-full opacity-[0.18]" preserveAspectRatio="none" viewBox="0 0 1200 800" fill="none">
        <defs>
          <linearGradient id="ln" x1="0" y1="0" x2="1" y2="1">
            <stop offset="0" stop-color="#a855f7" stop-opacity="0.4"/>
            <stop offset="1" stop-color="#22d3ee" stop-opacity="0.05"/>
          </linearGradient>
        </defs>
        <g stroke="url(#ln)" stroke-width="1">
          <line x1="80" y1="120" x2="320" y2="220"/>
          <line x1="320" y1="220" x2="180" y2="430"/>
          <line x1="180" y1="430" x2="420" y2="540"/>
          <line x1="420" y1="540" x2="640" y2="380"/>
          <line x1="640" y1="380" x2="800" y2="600"/>
          <line x1="800" y1="600" x2="980" y2="490"/>
          <line x1="980" y1="490" x2="1080" y2="220"/>
          <line x1="1080" y1="220" x2="880" y2="80"/>
        </g>
        <g fill="white">
          <circle cx="80" cy="120" r="1.4" opacity="0.6"/>
          <circle cx="320" cy="220" r="1.6" opacity="0.7"/>
          <circle cx="180" cy="430" r="1.2" opacity="0.5"/>
          <circle cx="420" cy="540" r="1.8" opacity="0.8"/>
          <circle cx="640" cy="380" r="1.3" opacity="0.6"/>
          <circle cx="800" cy="600" r="1.5" opacity="0.7"/>
          <circle cx="980" cy="490" r="1.4" opacity="0.6"/>
          <circle cx="1080" cy="220" r="1.7" opacity="0.7"/>
          <circle cx="880" cy="80" r="1.3" opacity="0.6"/>
        </g>
      </svg>
      <!-- Vignettes -->
      <div class="absolute inset-x-0 top-0 h-32 bg-gradient-to-b from-slate-900/60 to-transparent"></div>
      <div class="absolute inset-x-0 bottom-0 h-32 bg-gradient-to-t from-slate-900/60 to-transparent"></div>
    </div>

    <!-- ─── Top status bar ───────────────────────────────────────────── -->
    <header class="auth-topbar">
      <div class="auth-topbar__left">
        <span class="auth-status">
          <span class="auth-status__dot"></span>
          <span class="auth-status__txt">SYSTEM ONLINE</span>
        </span>
      </div>
      <div class="auth-topbar__right">
        <span class="auth-meta-chip">v 0.4 · STABLE</span>
        <span class="auth-meta-chip auth-meta-chip--quiet">{{ dateLabel }}</span>
      </div>
    </header>

    <!-- ─── Main grid ────────────────────────────────────────────────── -->
    <main class="auth-grid">
      <!-- LEFT: brand essay (hidden on small screens) -->
      <section class="auth-brand">
        <div class="auth-brand__head">
          <div class="auth-brand__monogram">
            <div class="logo-glow logo-glow--brand"></div>
            <svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linejoin="round">
              <path d="M12 3l2 5 5 2-5 2-2 5-2-5-5-2 5-2z"/>
              <path d="M19 14l.7 1.8 1.8.7-1.8.7-.7 1.8-.7-1.8-1.8-.7 1.8-.7z" fill="currentColor" fill-opacity="0.6" stroke="none"/>
            </svg>
          </div>
          <div class="auth-brand__id" data-mono>LZQ.SPACE</div>
        </div>

        <div class="auth-brand__hero">
          <p class="auth-brand__eyebrow" data-mono>WELCOME BACK,</p>
          <h2 class="auth-brand__title">
            一个人的<br />
            <span class="auth-brand__titleAccent">工作室。</span>
          </h2>
          <p class="auth-brand__tagline">
            收纳习题、菜谱、随笔、占卜与日常账本。
          </p>
        </div>

        <div class="auth-brand__spaces">
          <div class="auth-brand__sectionLabel" data-mono>
            <span class="auth-brand__bullet"></span>
            <span>6 SPACES INSIDE</span>
          </div>
          <div class="auth-brand__chips">
            <span v-for="s in spaces" :key="s.mono" class="auth-chip">
              <span class="auth-chip__mono" data-mono>{{ s.mono }}</span>
              <span class="auth-chip__label">{{ s.label }}</span>
            </span>
          </div>
        </div>

        <div class="auth-brand__foot">
          <div class="auth-brand__clock">
            <span class="auth-brand__clockTime" data-mono>{{ time }}</span>
            <span class="auth-brand__clockSub" data-mono>LOCAL TIME</span>
          </div>
          <div class="auth-brand__signature" data-mono>
            <span>BRISTOL</span>
            <span class="auth-brand__signatureDot"></span>
            <span>EST. 2024</span>
          </div>
        </div>
      </section>

      <!-- RIGHT: form -->
      <section class="auth-form-col">
        <div class="auth-form-stack">
          <!-- ghost cards behind for depth -->
          <span class="auth-form-ghost auth-form-ghost--back"></span>
          <span class="auth-form-ghost auth-form-ghost--mid"></span>

          <div class="auth-form-card">
            <!-- Header -->
            <div class="auth-form-head">
              <div class="auth-form-head__icon">
                <div class="logo-glow"></div>
                <div class="auth-form-head__iconInner">
                  <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linejoin="round">
                    <path d="M12 3l2 5 5 2-5 2-2 5-2-5-5-2 5-2z"/>
                    <path d="M19 14l.7 1.8 1.8.7-1.8.7-.7 1.8-.7-1.8-1.8-.7 1.8-.7z" fill="currentColor" fill-opacity="0.6" stroke="none"/>
                  </svg>
                </div>
              </div>
              <div class="auth-form-head__copy">
                <h1 class="auth-form-head__title">{{ mode === 'login' ? '欢迎回来' : '新建账号' }}</h1>
                <p class="auth-form-head__sub">{{ mode === 'login' ? '登录进入工作室' : '完成注册即可开始使用' }}</p>
              </div>
            </div>

            <!-- Tab Switch — sliding indicator -->
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
              <span class="auth-divider__label" data-mono>OR · 第三方登录</span>
              <span class="auth-divider__line"></span>
            </div>
            <div v-if="googleClientId" id="google-signin-btn" class="auth-google"></div>

            <p class="auth-fineprint">
              {{ mode === 'login' ? '尚未注册？' : '已有账号？' }}
              <button type="button" class="auth-fineprint__link" @click="mode = mode === 'login' ? 'register' : 'login'; error = ''">
                {{ mode === 'login' ? '创建一个新账号' : '直接登录' }}
                <span class="auth-fineprint__arrow">↗</span>
              </button>
            </p>
          </div>

          <router-link to="/" class="auth-back">
            <svg class="auth-back__arrow w-3.5 h-3.5" fill="none" stroke="currentColor" stroke-width="1.6" viewBox="0 0 24 24" stroke-linecap="round" stroke-linejoin="round">
              <path d="M15 18l-6-6 6-6"/>
            </svg>
            <span>返回首页</span>
            <span class="auth-back__shortcut" data-mono>⌘ ←</span>
          </router-link>
        </div>
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

.auth-stage {
  display: flex;
  flex-direction: column;
}

/* ────────── Top status bar ────────── */
.auth-topbar {
  position: relative;
  z-index: 10;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 18px clamp(16px, 4vw, 32px);
  border-bottom: 1px solid rgba(255, 255, 255, 0.04);
  font-size: 11px;
}
.auth-status {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 4px 10px 4px 8px;
  background: rgba(16, 185, 129, 0.07);
  border: 1px solid rgba(16, 185, 129, 0.18);
  border-radius: 999px;
  font-family: 'Geist Mono', ui-monospace, monospace;
  font-size: 10px;
  letter-spacing: 0.14em;
  color: rgba(110, 231, 183, 0.95);
}
.auth-status__dot {
  width: 6px; height: 6px; border-radius: 50%;
  background: #10b981;
  box-shadow: 0 0 8px rgba(16, 185, 129, 0.6);
  animation: statusPulse 2s ease-in-out infinite;
}
@keyframes statusPulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

.auth-topbar__right {
  display: inline-flex;
  align-items: center;
  gap: 8px;
}
.auth-meta-chip {
  padding: 4px 10px;
  background: rgba(255, 255, 255, 0.035);
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 6px;
  font-family: 'Geist Mono', ui-monospace, monospace;
  font-size: 10px;
  letter-spacing: 0.12em;
  color: rgba(255, 255, 255, 0.55);
}
.auth-meta-chip--quiet {
  background: transparent;
  border-color: transparent;
  color: rgba(255, 255, 255, 0.35);
}
@media (max-width: 480px) {
  .auth-meta-chip--quiet { display: none; }
}

/* ────────── Grid ────────── */
.auth-grid {
  flex: 1;
  display: grid;
  grid-template-columns: 1fr;
  gap: 0;
  align-items: stretch;
  position: relative;
  z-index: 5;
}
@media (min-width: 980px) {
  .auth-grid {
    grid-template-columns: 1.1fr 1fr;
    max-width: 1200px;
    margin: 0 auto;
    padding: 0 clamp(16px, 4vw, 32px);
  }
}

/* ────────── Left brand pane ────────── */
.auth-brand {
  display: none; /* hidden on small screens */
  flex-direction: column;
  padding: 56px 48px 36px 8px;
  position: relative;
}
@media (min-width: 980px) {
  .auth-brand { display: flex; }
}

.auth-brand__head {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 64px;
}
.auth-brand__monogram {
  position: relative;
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
}
.auth-brand__id {
  font-size: 11px;
  letter-spacing: 0.18em;
  color: rgba(255, 255, 255, 0.75);
}

.auth-brand__hero { margin-bottom: 56px; }
.auth-brand__eyebrow {
  font-size: 10px;
  letter-spacing: 0.2em;
  color: rgba(255, 255, 255, 0.4);
  margin-bottom: 14px;
}
.auth-brand__title {
  font-size: clamp(2.5rem, 1.8rem + 2vw, 3.5rem);
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
  margin-top: 18px;
  font-size: 15px;
  line-height: 1.65;
  color: rgba(255, 255, 255, 0.45);
  max-width: 38ch;
}

.auth-brand__spaces { margin-bottom: auto; }
.auth-brand__sectionLabel {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  font-size: 10px;
  letter-spacing: 0.18em;
  color: rgba(255, 255, 255, 0.45);
  margin-bottom: 14px;
}
.auth-brand__bullet {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: rgba(168, 85, 247, 0.65);
  box-shadow: 0 0 6px rgba(168, 85, 247, 0.4);
}
.auth-brand__chips {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 8px;
  max-width: 360px;
}
.auth-chip {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 9px;
  transition: background 0.2s ease, border-color 0.2s ease;
}
.auth-chip:hover {
  background: rgba(255, 255, 255, 0.05);
  border-color: rgba(255, 255, 255, 0.1);
}
.auth-chip__mono {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 20px;
  height: 18px;
  padding: 0 5px;
  font-size: 9.5px;
  font-weight: 500;
  letter-spacing: 0.06em;
  color: rgba(196, 181, 253, 0.95);
  background: rgba(168, 85, 247, 0.13);
  border: 1px solid rgba(168, 85, 247, 0.22);
  border-radius: 4px;
}
.auth-chip__label {
  font-size: 12px;
  font-weight: 500;
  color: rgba(255, 255, 255, 0.7);
}

.auth-brand__foot {
  margin-top: 56px;
  display: flex;
  align-items: end;
  justify-content: space-between;
  gap: 16px;
  padding-top: 24px;
  border-top: 1px solid rgba(255, 255, 255, 0.05);
}
.auth-brand__clock { display: flex; flex-direction: column; gap: 2px; }
.auth-brand__clockTime {
  font-size: 28px;
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
.auth-brand__signature {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  font-size: 10px;
  letter-spacing: 0.16em;
  color: rgba(255, 255, 255, 0.4);
}
.auth-brand__signatureDot {
  width: 4px; height: 4px; border-radius: 50%;
  background: rgba(255, 255, 255, 0.3);
}

/* ────────── Right form pane ────────── */
.auth-form-col {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: clamp(24px, 6vw, 56px) clamp(16px, 5vw, 32px);
}

.auth-form-stack {
  width: 100%;
  max-width: 420px;
  position: relative;
}

/* Ghost cards behind for depth */
.auth-form-ghost {
  position: absolute;
  inset: 0;
  border-radius: 22px;
  pointer-events: none;
}
.auth-form-ghost--back {
  background: rgba(255, 255, 255, 0.018);
  border: 1px solid rgba(255, 255, 255, 0.04);
  transform: rotate(-1.4deg) translate(-6px, 8px) scale(0.98);
}
.auth-form-ghost--mid {
  background: rgba(255, 255, 255, 0.025);
  border: 1px solid rgba(255, 255, 255, 0.05);
  transform: rotate(0.8deg) translate(8px, 4px) scale(0.99);
}

.auth-form-card {
  position: relative;
  z-index: 2;
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.05) 0%, rgba(255, 255, 255, 0.025) 100%);
  border: 1px solid rgba(255, 255, 255, 0.09);
  border-radius: 22px;
  padding: 28px;
  backdrop-filter: blur(28px) saturate(1.4);
  -webkit-backdrop-filter: blur(28px) saturate(1.4);
  box-shadow:
    0 1px 0 rgba(255, 255, 255, 0.06) inset,
    0 24px 60px -20px rgba(0, 0, 0, 0.5),
    0 8px 24px -8px rgba(124, 58, 237, 0.15);
  animation: cardSlideIn 0.55s cubic-bezier(0.22, 0.61, 0.36, 1) backwards;
}
@keyframes cardSlideIn {
  from { opacity: 0; transform: translateY(16px) scale(0.985); }
  to { opacity: 1; transform: translateY(0) scale(1); }
}
.auth-form-card::before {
  content: "";
  position: absolute;
  inset: 0;
  border-radius: 22px;
  padding: 1px;
  background: linear-gradient(135deg, rgba(168, 85, 247, 0.25) 0%, transparent 50%, rgba(34, 211, 238, 0.12) 100%);
  -webkit-mask: linear-gradient(#000 0 0) content-box, linear-gradient(#000 0 0);
  -webkit-mask-composite: xor;
  mask-composite: exclude;
  pointer-events: none;
  opacity: 0.6;
}

/* Form header */
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
  width: 44px;
  height: 44px;
  border-radius: 13px;
  background: linear-gradient(135deg, rgba(124, 58, 237, 0.95) 0%, rgba(168, 85, 247, 0.95) 100%);
  border: 1px solid rgba(255, 255, 255, 0.12);
  flex-shrink: 0;
}
.auth-form-head__iconInner {
  position: absolute;
  inset: 1px;
  border-radius: 12px;
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

/* Tabs with sliding indicator */
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
  transition: transform 0.35s cubic-bezier(0.65, 0, 0.35, 1);
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
  letter-spacing: 0.005em;
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

/* Field group */
.auth-field { display: flex; flex-direction: column; gap: 7px; }
.auth-label {
  font-size: 10.5px;
  letter-spacing: 0.13em;
  color: rgba(255, 255, 255, 0.45);
  font-family: 'Geist Mono', ui-monospace, monospace;
  text-transform: uppercase;
  font-weight: 500;
}

/* Input with leading icon */
.auth-input-wrap {
  position: relative;
}
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
  letter-spacing: 0.005em;
  color: white;
  background: linear-gradient(135deg, #7c3aed 0%, #9333ea 50%, #a855f7 100%);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 11px;
  cursor: pointer;
  margin-top: 6px;
  position: relative;
  overflow: hidden;
  box-shadow:
    0 1px 0 rgba(255, 255, 255, 0.16) inset,
    0 8px 24px -8px rgba(139, 92, 246, 0.5),
    0 2px 6px -2px rgba(124, 58, 237, 0.4);
  transition: transform 0.18s ease, box-shadow 0.18s ease, filter 0.18s ease;
}
.auth-submit::after {
  /* Subtle moving sheen on hover */
  content: "";
  position: absolute;
  inset: 0;
  background: linear-gradient(120deg, transparent 30%, rgba(255, 255, 255, 0.18) 50%, transparent 70%);
  transform: translateX(-100%);
  transition: transform 0.6s cubic-bezier(0.4, 0, 0.2, 1);
  pointer-events: none;
}
.auth-submit:hover:not(:disabled) {
  filter: brightness(1.06);
  box-shadow:
    0 1px 0 rgba(255, 255, 255, 0.18) inset,
    0 10px 30px -8px rgba(139, 92, 246, 0.6),
    0 2px 6px -2px rgba(124, 58, 237, 0.5);
}
.auth-submit:hover:not(:disabled)::after { transform: translateX(100%); }
.auth-submit:hover:not(:disabled) .auth-submit__arrow { transform: translateX(3px); }
.auth-submit:active:not(:disabled) { transform: translateY(0.5px); }
.auth-submit:disabled {
  cursor: not-allowed;
  background: linear-gradient(135deg, #4b5563 0%, #6b7280 100%);
  box-shadow: none;
  opacity: 0.6;
}
.auth-submit__arrow { transition: transform 0.18s ease; position: relative; z-index: 1; }
.auth-submit > * { position: relative; z-index: 1; }

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
  font-size: 9.5px;
  letter-spacing: 0.18em;
  color: rgba(255, 255, 255, 0.32);
}

/* Google button */
.auth-google { display: flex; justify-content: center; }
.auth-google :deep(iframe) {
  border-radius: 12px !important;
  filter: brightness(0.92) saturate(0.95);
}

/* Fineprint switch */
.auth-fineprint {
  margin-top: 20px;
  text-align: center;
  font-size: 12.5px;
  color: rgba(255, 255, 255, 0.4);
}
.auth-fineprint__link {
  background: transparent;
  border: none;
  color: rgba(196, 181, 253, 0.95);
  font-weight: 500;
  cursor: pointer;
  padding: 0 4px;
  transition: color 0.18s ease;
}
.auth-fineprint__link:hover { color: rgba(221, 214, 254, 1); }
.auth-fineprint__arrow {
  display: inline-block;
  transition: transform 0.18s ease;
}
.auth-fineprint__link:hover .auth-fineprint__arrow { transform: translate(2px, -2px); }

/* Back link */
.auth-back {
  margin-top: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 8px 12px;
  color: rgba(255, 255, 255, 0.4);
  font-size: 13px;
  text-decoration: none;
  transition: color 0.18s ease;
}
.auth-back:hover { color: rgba(255, 255, 255, 0.75); }
.auth-back:hover .auth-back__arrow { transform: translateX(-3px); }
.auth-back__arrow { transition: transform 0.18s ease; }
.auth-back__shortcut {
  margin-left: auto;
  font-size: 9.5px;
  padding: 2px 6px;
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 4px;
  color: rgba(255, 255, 255, 0.4);
  letter-spacing: 0.04em;
}

/* Logo glow */
.logo-glow {
  position: absolute;
  inset: -6px;
  border-radius: 18px;
  background: radial-gradient(circle, rgba(168, 85, 247, 0.5), rgba(124, 58, 237, 0.18) 50%, transparent 70%);
  filter: blur(16px);
  z-index: 0;
  animation: logoBreath 5.5s ease-in-out infinite;
  pointer-events: none;
}
.logo-glow--brand {
  inset: -4px;
  border-radius: 14px;
  background: radial-gradient(circle, rgba(168, 85, 247, 0.55), rgba(124, 58, 237, 0.22) 50%, transparent 70%);
}
@keyframes logoBreath {
  0%, 100% { opacity: 0.18; transform: scale(0.96); }
  50%      { opacity: 0.34; transform: scale(1.04); }
}

/* ────────── Background orbs (refined opacity for richer scene) ────────── */
.orb {
  position: absolute;
  border-radius: 50%;
  filter: blur(90px);
}
.orb-purple {
  width: 480px; height: 480px;
  background: rgba(139, 92, 246, 0.16);
  top: -12%; left: -10%;
  animation: orbFloat1 22s ease-in-out infinite;
}
.orb-cyan {
  width: 380px; height: 380px;
  background: rgba(6, 182, 212, 0.10);
  bottom: -8%; right: -10%;
  animation: orbFloat2 26s ease-in-out infinite;
}
.orb-orange {
  width: 320px; height: 320px;
  background: rgba(236, 72, 153, 0.07);
  top: 35%; left: 50%;
  transform: translate(-50%, -50%);
  animation: orbFloat3 19s ease-in-out infinite;
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

@media (prefers-reduced-motion: reduce) {
  .orb, .auth-status__dot, .logo-glow, .auth-form-card { animation: none !important; }
}
</style>
