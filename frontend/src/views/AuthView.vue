<script setup>
import { ref, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '../store/auth'
import QgThemeToggle from '../components/QgThemeToggle.vue'

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
    const redirectPath = route.query.redirect || '/'
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

const setMode = (next) => {
  if (mode.value === next) return
  mode.value = next
  error.value = ''
}

// Google one-tap / button — kept functional but visually tamed
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
      { theme: 'outline', size: 'large', width: 320, shape: 'rectangular', text: 'continue_with', locale: 'zh_CN' }
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
    const redirectPath = route.query.redirect || '/'
    setTimeout(() => router.push(redirectPath), 400)
  } catch (err) {
    error.value = err.response?.data?.detail || 'Google 登录失败'
  } finally {
    loading.value = false
  }
}

onMounted(() => initGoogleSignIn())

// Mini "table of contents" — what's behind the door
const spaces = [
  { label: 'Practice',  hint: '题库 / 选择 · 填空 · 论述' },
  { label: 'Kitchen',   hint: '菜谱 / 点单 / 后厨' },
  { label: 'Blog',      hint: '技术随笔 + 知识图谱' },
  { label: 'AI Lab',    hint: '对话 / 翻译 / 表情包' },
  { label: 'Tarot',     hint: '塔罗占卜' },
  { label: 'Receipts',  hint: '私人记账' },
]
</script>

<template>
  <div data-qg-surface class="auth">
    <!-- Top utility bar -->
    <header class="auth__top">
      <router-link to="/" class="auth__back" title="返回首页">
        <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><path d="M15 18l-6-6 6-6"/></svg>
        <span>返回</span>
      </router-link>
      <QgThemeToggle />
    </header>

    <!-- Two-column layout — editorial left, form right. Mobile collapses to single column. -->
    <main class="auth__grid">
      <!-- LEFT: brand essay -->
      <section class="auth__brand">
        <div class="auth__eyebrow" data-mono>Personal · Established 2024</div>
        <h1 class="auth__wordmark">LZQ Space</h1>
        <p class="auth__tagline">
          一个人的工作室。<br />
          收纳习题、菜谱、随笔、占卜与日常账本。
        </p>

        <div class="auth__index" aria-label="目录">
          <div class="auth__indexHead" data-mono>Inside</div>
          <ul class="auth__indexList">
            <li v-for="s in spaces" :key="s.label" class="auth__indexRow">
              <span class="auth__indexName">{{ s.label }}</span>
              <span class="auth__indexHint">{{ s.hint }}</span>
            </li>
          </ul>
        </div>

        <footer class="auth__brandFoot" data-mono>
          <span>www.lzqqq.org</span>
          <span class="auth__brandDot">·</span>
          <span>v 0.4</span>
        </footer>
      </section>

      <!-- RIGHT: form -->
      <section class="auth__form">
        <div class="auth__formInner">
          <div class="auth__tabs" role="tablist" aria-label="登录或注册">
            <button
              role="tab"
              :aria-selected="mode === 'login'"
              class="auth__tab"
              @click="setMode('login')"
            >登录</button>
            <button
              role="tab"
              :aria-selected="mode === 'register'"
              class="auth__tab"
              @click="setMode('register')"
            >注册</button>
          </div>

          <h2 class="auth__formTitle">
            {{ mode === 'login' ? '继续。' : '入门。' }}
          </h2>
          <p class="auth__formSub">
            {{ mode === 'login' ? '用邮箱或 Google 账号登录。' : '创建账号开始使用。' }}
          </p>

          <form @submit.prevent="handleSubmit" class="auth__fields" novalidate>
            <transition name="auth-fade">
              <div v-if="success" class="auth__notice" data-tone="success">
                <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12.5l4 4L19 7"/></svg>
                <span>{{ mode === 'login' ? '登录成功，正在跳转…' : '注册成功，正在跳转…' }}</span>
              </div>
            </transition>
            <transition name="auth-fade">
              <div v-if="error" class="auth__notice" data-tone="danger">
                <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"><path d="M12 8v4M12 16h.01"/><circle cx="12" cy="12" r="9"/></svg>
                <span>{{ error }}</span>
              </div>
            </transition>

            <div v-if="mode === 'register'" class="auth__field">
              <label class="auth__label" for="auth-nickname">昵称</label>
              <input
                id="auth-nickname"
                v-model="nickname"
                type="text"
                class="auth__input"
                placeholder="可选"
                :disabled="loading"
              />
            </div>

            <div class="auth__field">
              <label class="auth__label" for="auth-email">邮箱</label>
              <input
                id="auth-email"
                v-model="email"
                type="email"
                class="auth__input"
                placeholder="you@example.com"
                :disabled="loading"
                autocomplete="email"
              />
            </div>

            <div class="auth__field">
              <label class="auth__label" for="auth-password">密码</label>
              <input
                id="auth-password"
                v-model="password"
                type="password"
                class="auth__input"
                :placeholder="mode === 'register' ? '至少 6 位' : '请输入密码'"
                :disabled="loading"
                :autocomplete="mode === 'register' ? 'new-password' : 'current-password'"
                @keyup.enter="handleSubmit"
              />
            </div>

            <button
              type="submit"
              class="auth__submit"
              :disabled="loading"
            >
              <svg v-if="loading" class="auth__spinner" viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">
                <path d="M12 2a10 10 0 1 1-7.07 2.93" opacity="0.8"/>
              </svg>
              <span>{{ loading ? '处理中…' : (mode === 'login' ? '登录' : '注册') }}</span>
              <svg v-if="!loading" viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12h14M13 6l6 6-6 6"/></svg>
            </button>
          </form>

          <div v-if="googleClientId" class="auth__divider">
            <span class="auth__dividerLine"></span>
            <span class="auth__dividerLabel" data-mono>OR</span>
            <span class="auth__dividerLine"></span>
          </div>

          <div v-if="googleClientId" id="google-signin-btn" class="auth__google"></div>
        </div>
      </section>
    </main>
  </div>
</template>

<style scoped>
.auth {
  min-height: 100dvh;
  background: var(--qg-surface-base);
  color: var(--qg-text-primary);
  font-family: var(--qg-font-body);
  display: flex;
  flex-direction: column;
}

/* ─── Top utility row ─────────────────────────────────────────────── */
.auth__top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px clamp(20px, 4vw, 40px);
  border-bottom: 1px solid var(--qg-border-default);
  background: color-mix(in oklch, var(--qg-surface-base) 92%, transparent);
  backdrop-filter: saturate(160%) blur(8px);
}
.auth__back {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-family: var(--qg-font-mono);
  font-size: 11px;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: var(--qg-text-secondary);
  text-decoration: none;
  padding: 6px 10px 6px 8px;
  border: 1px solid var(--qg-border-default);
  border-radius: var(--qg-radius-md);
  transition: color var(--qg-dur-fast) var(--qg-ease),
              border-color var(--qg-dur-fast) var(--qg-ease);
}
.auth__back:hover { color: var(--qg-text-primary); border-color: var(--qg-border-strong); }

/* ─── Two-column layout ───────────────────────────────────────────── */
.auth__grid {
  flex: 1;
  display: grid;
  grid-template-columns: 1fr;
  gap: 0;
}
@media (min-width: 880px) {
  .auth__grid {
    grid-template-columns: 1.1fr 1fr;
  }
}

/* ─── Left: brand essay ───────────────────────────────────────────── */
.auth__brand {
  padding: clamp(40px, 6vw, 80px) clamp(24px, 5vw, 64px);
  display: flex;
  flex-direction: column;
  gap: clamp(24px, 4vw, 36px);
  border-bottom: 1px solid var(--qg-border-default);
}
@media (min-width: 880px) {
  .auth__brand {
    border-bottom: none;
    border-right: 1px solid var(--qg-border-default);
    min-height: calc(100dvh - 60px);
  }
}

.auth__eyebrow {
  font-size: 11px;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  color: var(--qg-text-tertiary);
}

.auth__wordmark {
  font-family: var(--qg-font-display);
  font-weight: 500;
  font-size: clamp(3rem, 4vw + 1.5rem, 5.25rem);
  line-height: 0.95;
  letter-spacing: -0.035em;
  margin: 0;
  color: var(--qg-text-primary);
  font-variation-settings: 'opsz' 96;
}

.auth__tagline {
  font-size: var(--qg-text-md);
  line-height: 1.65;
  color: var(--qg-text-secondary);
  max-width: 38ch;
  margin: 0;
}

.auth__index {
  margin-top: auto;
  border-top: 1px solid var(--qg-border-default);
  padding-top: 24px;
}
.auth__indexHead {
  font-size: 10px;
  letter-spacing: 0.16em;
  text-transform: uppercase;
  color: var(--qg-text-tertiary);
  margin-bottom: 14px;
}
.auth__indexList {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 0;
}
.auth__indexRow {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  padding: 10px 0;
  border-bottom: 1px dashed var(--qg-border-default);
  gap: 16px;
}
.auth__indexRow:last-child { border-bottom: none; }
.auth__indexName {
  font-family: var(--qg-font-display);
  font-size: var(--qg-text-md);
  font-weight: 500;
  color: var(--qg-text-primary);
  letter-spacing: -0.005em;
}
.auth__indexHint {
  font-family: var(--qg-font-mono);
  font-size: 11px;
  color: var(--qg-text-tertiary);
  letter-spacing: 0.02em;
  text-align: right;
  flex-shrink: 0;
}

.auth__brandFoot {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  font-size: 11px;
  letter-spacing: 0.04em;
  color: var(--qg-text-muted);
  margin-top: 8px;
}
.auth__brandDot { color: var(--qg-text-muted); }

/* ─── Right: form ─────────────────────────────────────────────────── */
.auth__form {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: clamp(40px, 6vw, 64px) clamp(24px, 5vw, 56px);
  background: var(--qg-surface-raised);
}
.auth__formInner {
  width: 100%;
  max-width: 380px;
}

.auth__tabs {
  display: inline-flex;
  background: var(--qg-surface-sunken);
  border: 1px solid var(--qg-border-default);
  border-radius: var(--qg-radius-md);
  padding: 3px;
  gap: 2px;
  margin-bottom: 28px;
}
.auth__tab {
  padding: 6px 16px;
  font-size: var(--qg-text-sm);
  font-weight: 500;
  color: var(--qg-text-tertiary);
  background: transparent;
  border: none;
  border-radius: 7px;
  cursor: pointer;
  letter-spacing: -0.005em;
  transition: background var(--qg-dur-fast) var(--qg-ease),
              color var(--qg-dur-fast) var(--qg-ease);
}
.auth__tab:hover { color: var(--qg-text-primary); }
.auth__tab[aria-selected="true"] {
  background: var(--qg-surface-raised);
  color: var(--qg-text-primary);
  box-shadow: var(--qg-shadow-1);
}

.auth__formTitle {
  font-family: var(--qg-font-display);
  font-size: clamp(1.875rem, 1.4rem + 1.6vw, 2.5rem);
  font-weight: 500;
  letter-spacing: -0.025em;
  line-height: 1.05;
  margin: 0;
  color: var(--qg-text-primary);
  font-variation-settings: 'opsz' 60;
}
.auth__formSub {
  font-size: var(--qg-text-base);
  color: var(--qg-text-secondary);
  margin: 8px 0 28px;
  line-height: 1.5;
}

.auth__fields {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.auth__notice {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 12px;
  border-radius: var(--qg-radius-md);
  font-size: var(--qg-text-sm);
  border: 1px solid transparent;
}
.auth__notice[data-tone="success"] {
  background: var(--qg-success-soft);
  color: var(--qg-success);
  border-color: color-mix(in oklch, var(--qg-success) 25%, transparent);
}
.auth__notice[data-tone="danger"] {
  background: var(--qg-danger-soft);
  color: var(--qg-danger);
  border-color: color-mix(in oklch, var(--qg-danger) 25%, transparent);
}

.auth__field { display: flex; flex-direction: column; gap: 6px; }
.auth__label {
  font-size: 11px;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  font-family: var(--qg-font-mono);
  color: var(--qg-text-tertiary);
}
.auth__input {
  font-family: var(--qg-font-body);
  font-size: var(--qg-text-md);
  color: var(--qg-text-primary);
  background: var(--qg-surface-sunken);
  border: 1px solid var(--qg-border-default);
  border-radius: var(--qg-radius-md);
  padding: 12px 14px;
  outline: none;
  letter-spacing: -0.005em;
  transition: border-color var(--qg-dur-fast) var(--qg-ease),
              background var(--qg-dur-fast) var(--qg-ease);
}
.auth__input::placeholder { color: var(--qg-text-muted); }
.auth__input:focus {
  border-color: var(--qg-border-focus);
  background: var(--qg-surface-base);
  box-shadow: var(--qg-shadow-focus);
}
.auth__input:disabled { opacity: 0.5; cursor: not-allowed; }

.auth__submit {
  margin-top: 6px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  font-family: var(--qg-font-body);
  font-size: var(--qg-text-base);
  font-weight: 500;
  letter-spacing: -0.005em;
  color: var(--qg-accent-on);
  background: var(--qg-accent);
  border: none;
  border-radius: var(--qg-radius-md);
  padding: 13px 18px;
  cursor: pointer;
  transition: background var(--qg-dur-fast) var(--qg-ease),
              transform var(--qg-dur-fast) var(--qg-ease);
}
.auth__submit:hover:not([disabled]) { background: var(--qg-accent-hover); }
.auth__submit:active:not([disabled]) { transform: translateY(0.5px); }
.auth__submit:focus-visible { outline: none; box-shadow: var(--qg-shadow-focus); }
.auth__submit[disabled] { opacity: 0.55; cursor: not-allowed; }
.auth__spinner { animation: auth-spin 0.9s linear infinite; }
@keyframes auth-spin { to { transform: rotate(360deg); } }

.auth__divider {
  display: flex;
  align-items: center;
  gap: 12px;
  margin: 24px 0;
}
.auth__dividerLine {
  flex: 1;
  height: 1px;
  background: var(--qg-border-default);
}
.auth__dividerLabel {
  font-size: 10px;
  letter-spacing: 0.16em;
  color: var(--qg-text-muted);
}

.auth__google {
  display: flex;
  justify-content: center;
}
/* Tame Google's iframe button shadow & rounding */
.auth__google :deep(iframe) {
  border-radius: var(--qg-radius-md) !important;
  filter: saturate(0.9);
}

/* ─── Transitions ─────────────────────────────────────────────────── */
.auth-fade-enter-active,
.auth-fade-leave-active {
  transition: opacity var(--qg-dur-base) var(--qg-ease),
              transform var(--qg-dur-base) var(--qg-ease);
}
.auth-fade-enter-from,
.auth-fade-leave-to {
  opacity: 0;
  transform: translateY(-4px);
}
</style>
