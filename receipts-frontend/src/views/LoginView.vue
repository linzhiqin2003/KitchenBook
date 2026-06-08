<template>
  <div class="login-page">
    <!-- Left: brand panel -->
    <aside class="login-hero" aria-hidden="false">
      <div class="login-hero__grid" aria-hidden="true"></div>
      <div class="login-hero__glow" aria-hidden="true"></div>

      <div class="login-hero__content">
        <div class="login-hero__brand" :style="{ '--delay': '0ms' }">
          <div class="login-hero__logo">
            <Receipt :size="22" stroke-width="1.75" />
          </div>
          <span class="login-hero__name">Receipt Ledger</span>
        </div>

        <div class="login-hero__copy" :style="{ '--delay': '60ms' }">
          <h2>每一笔支出，清清楚楚</h2>
          <p>拍照录入、自动分类、团队共享——让收据管理像记账一样简单。</p>
        </div>

        <ul class="login-hero__features" :style="{ '--delay': '120ms' }">
          <li>
            <span class="login-hero__feature-icon"><ScanLine :size="16" /></span>
            <span>
              <strong>智能识别</strong>
              <small>拍照即可提取金额与商户</small>
            </span>
          </li>
          <li>
            <span class="login-hero__feature-icon"><Users :size="16" /></span>
            <span>
              <strong>团队协作</strong>
              <small>组织内共享账本与权限</small>
            </span>
          </li>
          <li>
            <span class="login-hero__feature-icon"><BarChart3 :size="16" /></span>
            <span>
              <strong>消费洞察</strong>
              <small>图表汇总，趋势一目了然</small>
            </span>
          </li>
        </ul>
      </div>
    </aside>

    <!-- Right: form panel -->
    <main class="login-main">
      <div class="login-card">
        <header class="login-card__header" :style="{ '--delay': '0ms' }">
          <div class="login-card__logo-sm">
            <Receipt :size="20" stroke-width="1.75" />
          </div>
          <h1>欢迎回来</h1>
          <p>登录你的智能账本账号</p>
        </header>

        <form class="login-form" @submit.prevent="handleLogin" :style="{ '--delay': '80ms' }">
          <div class="field">
            <label for="login-email">邮箱</label>
            <div class="field__control" :class="{ 'field__control--focused': emailFocused }">
              <Mail :size="16" class="field__icon" />
              <input
                id="login-email"
                type="email"
                v-model="email"
                required
                placeholder="name@company.com"
                autocomplete="email"
                @focus="emailFocused = true"
                @blur="emailFocused = false"
              />
            </div>
          </div>

          <div class="field">
            <label for="login-password">密码</label>
            <div class="field__control" :class="{ 'field__control--focused': passwordFocused }">
              <Lock :size="16" class="field__icon" />
              <input
                id="login-password"
                :type="showPassword ? 'text' : 'password'"
                v-model="password"
                required
                placeholder="输入密码"
                autocomplete="current-password"
                @focus="passwordFocused = true"
                @blur="passwordFocused = false"
              />
              <button
                type="button"
                class="field__toggle"
                :aria-label="showPassword ? '隐藏密码' : '显示密码'"
                @click="showPassword = !showPassword"
                tabindex="-1"
              >
                <EyeOff v-if="showPassword" :size="16" />
                <Eye v-else :size="16" />
              </button>
            </div>
          </div>

          <Transition name="alert">
            <div v-if="error" class="alert-error" role="alert">
              <AlertCircle :size="15" />
              <span>{{ error }}</span>
            </div>
          </Transition>

          <button class="btn-primary" type="submit" :disabled="loading">
            <Loader2 v-if="loading" :size="17" class="btn-spinner" />
            <span>{{ loading ? "登录中…" : "登录" }}</span>
          </button>
        </form>

        <footer class="login-card__footer" :style="{ '--delay': '160ms' }">
          还没有账号？
          <RouterLink to="/register">免费注册</RouterLink>
        </footer>
      </div>
    </main>
  </div>
</template>

<script setup lang="ts">
import { ref } from "vue";
import { useRouter } from "vue-router";
import {
  Receipt,
  Mail,
  Lock,
  Eye,
  EyeOff,
  Loader2,
  ScanLine,
  Users,
  BarChart3,
  AlertCircle,
} from "lucide-vue-next";
import { useAuthStore } from "../stores/auth";

const router = useRouter();
const authStore = useAuthStore();

const email = ref("");
const password = ref("");
const showPassword = ref(false);
const emailFocused = ref(false);
const passwordFocused = ref(false);
const loading = ref(false);
const error = ref("");

async function handleLogin() {
  loading.value = true;
  error.value = "";
  try {
    await authStore.login(email.value, password.value);
    router.push("/");
  } catch (err: any) {
    if (!err.response) {
      error.value = "无法连接服务器，请检查网络或稍后重试";
    } else {
      error.value = err.response.data?.detail || "登录失败，请检查邮箱和密码";
    }
  } finally {
    loading.value = false;
  }
}
</script>

<style scoped>
@import url("https://fonts.googleapis.com/css2?family=Sora:wght@500;600;700&family=Source+Sans+3:wght@400;500;600&display=swap");

/* ── Tokens ── */
.login-page {
  --space-xs: 4px;
  --space-sm: 8px;
  --space-md: 12px;
  --space-lg: 16px;
  --space-xl: 24px;
  --space-2xl: 32px;
  --space-3xl: 48px;
  --space-4xl: 64px;

  --hero-bg: oklch(0.26 0.035 255);
  --hero-text: oklch(0.93 0.01 255);
  --hero-muted: oklch(0.68 0.025 255);
  --hero-accent: oklch(0.72 0.11 175);

  --surface: oklch(0.995 0.004 200);
  --surface-raised: oklch(1 0 0);
  --text: oklch(0.28 0.02 255);
  --text-muted: oklch(0.52 0.02 255);
  --text-faint: oklch(0.68 0.015 255);
  --border: oklch(0.90 0.012 200);
  --border-focus: oklch(0.78 0.04 175);
  --accent: oklch(0.48 0.11 175);
  --accent-hover: oklch(0.42 0.11 175);
  --accent-soft: oklch(0.48 0.11 175 / 0.1);
  --danger: oklch(0.55 0.2 25);
  --danger-soft: oklch(0.55 0.2 25 / 0.08);

  --ease-out: cubic-bezier(0.25, 1, 0.5, 1);
  --duration: 240ms;
  --radius: 10px;
  --radius-lg: 14px;

  min-height: 100vh;
  min-height: 100svh;
  display: grid;
  grid-template-columns: 1fr 1fr;
  font-family: "Source Sans 3", system-ui, sans-serif;
  color: var(--text);
  background: var(--surface);
}

/* ── Hero panel ── */
.login-hero {
  position: relative;
  display: flex;
  align-items: center;
  padding: var(--space-4xl) var(--space-3xl);
  background: var(--hero-bg);
  color: var(--hero-text);
  overflow: hidden;
}

.login-hero__grid {
  position: absolute;
  inset: 0;
  background-image:
    linear-gradient(oklch(1 0 0 / 0.04) 1px, transparent 1px),
    linear-gradient(90deg, oklch(1 0 0 / 0.04) 1px, transparent 1px);
  background-size: 48px 48px;
  mask-image: radial-gradient(ellipse 80% 70% at 30% 50%, black 20%, transparent 75%);
}

.login-hero__glow {
  position: absolute;
  width: 420px;
  height: 420px;
  top: 10%;
  right: -80px;
  border-radius: 50%;
  background: oklch(0.55 0.12 175 / 0.18);
  filter: blur(80px);
  pointer-events: none;
}

.login-hero__content {
  position: relative;
  z-index: 1;
  max-width: 420px;
  display: flex;
  flex-direction: column;
  gap: var(--space-3xl);
}

.login-hero__brand,
.login-hero__copy,
.login-hero__features {
  animation: riseIn var(--duration) var(--ease-out) both;
  animation-delay: var(--delay, 0ms);
}

.login-hero__brand {
  display: flex;
  align-items: center;
  gap: var(--space-md);
}

.login-hero__logo {
  width: 40px;
  height: 40px;
  border-radius: var(--radius);
  background: oklch(0.48 0.11 175);
  display: flex;
  align-items: center;
  justify-content: center;
  color: oklch(0.98 0.01 175);
}

.login-hero__name {
  font-family: "Sora", sans-serif;
  font-size: 0.9375rem;
  font-weight: 600;
  letter-spacing: 0.02em;
  color: var(--hero-muted);
}

.login-hero__copy h2 {
  font-family: "Sora", sans-serif;
  font-size: 1.75rem;
  font-weight: 700;
  line-height: 1.25;
  letter-spacing: -0.03em;
  margin: 0 0 var(--space-md);
  color: var(--hero-text);
}

.login-hero__copy p {
  margin: 0;
  font-size: 1rem;
  line-height: 1.6;
  color: var(--hero-muted);
  max-width: 36ch;
}

.login-hero__features {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: var(--space-lg);
}

.login-hero__features li {
  display: flex;
  align-items: flex-start;
  gap: var(--space-md);
}

.login-hero__feature-icon {
  width: 32px;
  height: 32px;
  border-radius: var(--radius);
  background: oklch(1 0 0 / 0.06);
  border: 1px solid oklch(1 0 0 / 0.08);
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--hero-accent);
  flex-shrink: 0;
}

.login-hero__features strong {
  display: block;
  font-size: 0.875rem;
  font-weight: 600;
  color: var(--hero-text);
  margin-bottom: 2px;
}

.login-hero__features small {
  display: block;
  font-size: 0.8125rem;
  color: var(--hero-muted);
  line-height: 1.4;
}

/* ── Form panel ── */
.login-main {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: var(--space-xl) var(--space-2xl);
  background: var(--surface);
}

.login-card {
  width: 100%;
  max-width: 400px;
  display: flex;
  flex-direction: column;
  gap: var(--space-2xl);
}

.login-card__header,
.login-form,
.login-card__footer {
  animation: riseIn var(--duration) var(--ease-out) both;
  animation-delay: var(--delay, 0ms);
}

.login-card__header {
  display: flex;
  flex-direction: column;
  gap: var(--space-sm);
}

.login-card__logo-sm {
  display: none;
}

.login-card__header h1 {
  font-family: "Sora", sans-serif;
  font-size: 1.625rem;
  font-weight: 700;
  letter-spacing: -0.03em;
  margin: 0;
  color: var(--text);
}

.login-card__header p {
  margin: 0;
  font-size: 0.9375rem;
  color: var(--text-muted);
}

/* ── Form ── */
.login-form {
  display: flex;
  flex-direction: column;
  gap: var(--space-xl);
}

.field {
  display: flex;
  flex-direction: column;
  gap: var(--space-sm);
}

.field label {
  font-size: 0.8125rem;
  font-weight: 600;
  color: var(--text);
  letter-spacing: 0.01em;
}

.field__control {
  display: flex;
  align-items: center;
  gap: var(--space-md);
  padding: 0 var(--space-lg);
  height: 44px;
  background: var(--surface-raised);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  transition:
    border-color var(--duration) var(--ease-out),
    box-shadow var(--duration) var(--ease-out);
}

.field__control--focused,
.field__control:focus-within {
  border-color: var(--border-focus);
  box-shadow: 0 0 0 3px var(--accent-soft);
}

.field__icon {
  color: var(--text-faint);
  flex-shrink: 0;
  transition: color var(--duration) var(--ease-out);
}

.field__control:focus-within .field__icon {
  color: var(--accent);
}

.field__control input {
  flex: 1;
  border: none;
  outline: none;
  background: transparent;
  font-family: inherit;
  font-size: 0.9375rem;
  color: var(--text);
  min-width: 0;
}

.field__control input::placeholder {
  color: var(--text-faint);
}

.field__toggle {
  background: none;
  border: none;
  padding: var(--space-xs);
  cursor: pointer;
  color: var(--text-faint);
  display: flex;
  align-items: center;
  border-radius: 6px;
  transition: color var(--duration) var(--ease-out);
}

.field__toggle:hover {
  color: var(--text-muted);
}

/* ── Alert ── */
.alert-error {
  display: flex;
  align-items: flex-start;
  gap: var(--space-sm);
  padding: var(--space-md) var(--space-lg);
  background: var(--danger-soft);
  border: 1px solid oklch(0.55 0.2 25 / 0.15);
  border-radius: var(--radius);
  color: var(--danger);
  font-size: 0.875rem;
  font-weight: 500;
  line-height: 1.45;
}

.alert-error svg {
  flex-shrink: 0;
  margin-top: 1px;
}

.alert-enter-active {
  animation: alertIn 320ms var(--ease-out);
}

.alert-leave-active {
  transition: opacity 180ms var(--ease-out), transform 180ms var(--ease-out);
}

.alert-leave-to {
  opacity: 0;
  transform: translateY(-4px);
}

@keyframes alertIn {
  from {
    opacity: 0;
    transform: translateY(6px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* ── Button ── */
.btn-primary {
  width: 100%;
  height: 44px;
  border: none;
  border-radius: var(--radius);
  background: var(--accent);
  color: oklch(0.99 0.005 175);
  font-family: inherit;
  font-size: 0.9375rem;
  font-weight: 600;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-sm);
  transition:
    background var(--duration) var(--ease-out),
    transform var(--duration) var(--ease-out);
  -webkit-tap-highlight-color: transparent;
}

.btn-primary:hover:not(:disabled) {
  background: var(--accent-hover);
}

.btn-primary:active:not(:disabled) {
  transform: scale(0.985);
}

.btn-primary:disabled {
  opacity: 0.55;
  cursor: not-allowed;
}

.btn-spinner {
  animation: spin 0.7s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

/* ── Footer ── */
.login-card__footer {
  font-size: 0.9375rem;
  color: var(--text-muted);
}

.login-card__footer a {
  color: var(--accent);
  font-weight: 600;
  text-decoration: none;
  margin-left: 4px;
  transition: color var(--duration) var(--ease-out);
}

.login-card__footer a:hover {
  color: var(--accent-hover);
}

/* ── Animations ── */
@keyframes riseIn {
  from {
    opacity: 0;
    transform: translateY(16px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* ── Responsive ── */
@media (max-width: 900px) {
  .login-page {
    grid-template-columns: 1fr;
  }

  .login-hero {
    display: none;
  }

  .login-main {
    padding: var(--space-3xl) var(--space-xl);
    min-height: 100svh;
    align-items: flex-start;
    padding-top: clamp(48px, 12vh, 96px);
  }

  .login-card__logo-sm {
    display: flex;
    width: 36px;
    height: 36px;
    border-radius: var(--radius);
    background: var(--accent);
    color: oklch(0.99 0.005 175);
    align-items: center;
    justify-content: center;
    margin-bottom: var(--space-sm);
  }
}

@media (max-width: 480px) {
  .login-main {
    padding: var(--space-2xl) var(--space-lg);
    padding-top: clamp(40px, 10vh, 72px);
  }

  .login-card__header h1 {
    font-size: 1.5rem;
  }

  .field__control input {
    font-size: 16px;
  }
}

@media (prefers-reduced-motion: reduce) {
  .login-hero__brand,
  .login-hero__copy,
  .login-hero__features,
  .login-card__header,
  .login-form,
  .login-card__footer {
    animation: none;
  }

  .btn-primary:active:not(:disabled) {
    transform: none;
  }
}
</style>
