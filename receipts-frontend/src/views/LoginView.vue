<template>
  <div class="auth-page">
    <!-- Floating ambient blobs -->
    <div class="auth-ambient">
      <div class="auth-blob auth-blob--1"></div>
      <div class="auth-blob auth-blob--2"></div>
      <div class="auth-blob auth-blob--3"></div>
    </div>

    <div class="auth-wrapper">
      <!-- App Icon + Brand -->
      <div class="auth-brand" :style="{ animationDelay: '0s' }">
        <div class="auth-app-icon">
          <BookOpenText :size="28" color="#fff" />
        </div>
        <span class="auth-app-name">Receipt Ledger</span>
      </div>

      <!-- Title -->
      <div class="auth-header" :style="{ animationDelay: '0.06s' }">
        <h1>欢迎回来</h1>
        <p>登录以继续管理你的收据</p>
      </div>

      <!-- Form Card (iOS grouped style) -->
      <form class="auth-form" @submit.prevent="handleLogin" :style="{ animationDelay: '0.12s' }">
        <div class="ios-group">
          <div class="ios-field">
            <Mail :size="17" class="ios-field__icon" />
            <input
              type="email"
              v-model="email"
              required
              placeholder="邮箱地址"
              autocomplete="email"
            />
          </div>
          <div class="ios-divider"></div>
          <div class="ios-field">
            <Lock :size="17" class="ios-field__icon" />
            <input
              :type="showPassword ? 'text' : 'password'"
              v-model="password"
              required
              placeholder="密码"
              autocomplete="current-password"
            />
            <button type="button" class="ios-field__toggle" @click="showPassword = !showPassword" tabindex="-1">
              <EyeOff v-if="showPassword" :size="17" />
              <Eye v-else :size="17" />
            </button>
          </div>
        </div>

        <!-- Error -->
        <Transition name="ios-alert">
          <div v-if="error" class="ios-error">
            <AlertCircle :size="15" />
            <span>{{ error }}</span>
          </div>
        </Transition>

        <!-- Submit -->
        <button class="ios-button" type="submit" :disabled="loading" :class="{ 'ios-button--loading': loading }">
          <Loader2 v-if="loading" :size="18" class="ios-spinner" />
          <span>{{ loading ? '登录中…' : '登录' }}</span>
        </button>
      </form>

      <!-- Features -->
      <div class="auth-features" :style="{ animationDelay: '0.18s' }">
        <div class="auth-feature-chip">
          <ScanLine :size="14" />
          <span>拍照即录入</span>
        </div>
        <div class="auth-feature-chip">
          <Users :size="14" />
          <span>团队协作</span>
        </div>
        <div class="auth-feature-chip">
          <BarChart3 :size="14" />
          <span>消费洞察</span>
        </div>
      </div>

      <!-- Footer -->
      <div class="auth-footer" :style="{ animationDelay: '0.24s' }">
        还没有账号？<RouterLink to="/register">注册</RouterLink>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from "vue";
import { useRouter } from "vue-router";
import { BookOpenText, Mail, Lock, Eye, EyeOff, Loader2, ScanLine, Users, BarChart3, AlertCircle } from "lucide-vue-next";
import { useAuthStore } from "../stores/auth";

const router = useRouter();
const authStore = useAuthStore();

const email = ref("");
const password = ref("");
const showPassword = ref(false);
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
/* ── Page ── */
.auth-page {
  min-height: 100vh;
  min-height: 100svh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f2f2f7;
  padding: 20px;
  position: relative;
  overflow: hidden;
}

/* ── Ambient blobs ── */
.auth-ambient {
  position: fixed;
  inset: 0;
  pointer-events: none;
  z-index: 0;
}

.auth-blob {
  position: absolute;
  border-radius: 50%;
  filter: blur(80px);
  opacity: 0.5;
}

.auth-blob--1 {
  width: 400px;
  height: 400px;
  background: rgba(0, 122, 255, 0.15);
  top: -10%;
  right: -5%;
  animation: blobDrift 14s ease-in-out infinite;
}

.auth-blob--2 {
  width: 300px;
  height: 300px;
  background: rgba(88, 86, 214, 0.12);
  bottom: -5%;
  left: -5%;
  animation: blobDrift 18s ease-in-out infinite reverse;
}

.auth-blob--3 {
  width: 200px;
  height: 200px;
  background: rgba(52, 199, 89, 0.1);
  top: 40%;
  left: 30%;
  animation: blobDrift 12s ease-in-out infinite 2s;
}

@keyframes blobDrift {
  0%, 100% { transform: translate(0, 0) scale(1); }
  33% { transform: translate(20px, -30px) scale(1.05); }
  66% { transform: translate(-15px, 20px) scale(0.95); }
}

/* ── Wrapper ── */
.auth-wrapper {
  position: relative;
  z-index: 1;
  width: 100%;
  max-width: 400px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 24px;
}

/* Staggered entrance animation for children */
.auth-brand,
.auth-header,
.auth-form,
.auth-features,
.auth-footer {
  animation: iosSlideUp 0.6s cubic-bezier(0.2, 0.8, 0.2, 1) both;
}

@keyframes iosSlideUp {
  from {
    opacity: 0;
    transform: translateY(24px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* ── Brand ── */
.auth-brand {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
}

.auth-app-icon {
  width: 64px;
  height: 64px;
  border-radius: 16px;
  background: linear-gradient(145deg, #007aff, #5856d6);
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow:
    0 8px 24px rgba(0, 122, 255, 0.3),
    0 2px 8px rgba(0, 122, 255, 0.15);
}

.auth-app-name {
  font-family: "Space Grotesk", -apple-system, sans-serif;
  font-size: 15px;
  font-weight: 600;
  color: var(--muted, #8e8e93);
  letter-spacing: 0.3px;
}

/* ── Header ── */
.auth-header {
  text-align: center;
}

.auth-header h1 {
  font-family: -apple-system, "SF Pro Display", "Space Grotesk", sans-serif;
  font-size: 28px;
  font-weight: 700;
  margin: 0 0 6px;
  color: #1c1c1e;
  letter-spacing: -0.5px;
}

.auth-header p {
  font-size: 15px;
  color: #8e8e93;
  margin: 0;
}

/* ── iOS Grouped Form ── */
.auth-form {
  width: 100%;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.ios-group {
  background: rgba(255, 255, 255, 0.82);
  backdrop-filter: blur(20px) saturate(180%);
  -webkit-backdrop-filter: blur(20px) saturate(180%);
  border-radius: 14px;
  border: 0.5px solid rgba(0, 0, 0, 0.06);
  box-shadow:
    0 1px 3px rgba(0, 0, 0, 0.04),
    0 4px 16px rgba(0, 0, 0, 0.03);
  overflow: hidden;
  transition: box-shadow 0.3s ease;
}

.ios-group:focus-within {
  box-shadow:
    0 1px 3px rgba(0, 0, 0, 0.04),
    0 4px 16px rgba(0, 0, 0, 0.03),
    0 0 0 3.5px rgba(0, 122, 255, 0.18);
}

.ios-field {
  display: flex;
  align-items: center;
  padding: 0 16px;
  min-height: 50px;
  gap: 12px;
}

.ios-field__icon {
  color: #8e8e93;
  flex-shrink: 0;
  transition: color 0.25s ease;
}

.ios-field:focus-within .ios-field__icon {
  color: #007aff;
}

.ios-field input {
  flex: 1;
  border: none;
  outline: none;
  background: transparent;
  font-family: inherit;
  font-size: 16px;
  color: #1c1c1e;
  padding: 14px 0;
  min-width: 0;
}

.ios-field input::placeholder {
  color: #c7c7cc;
}

.ios-field__toggle {
  background: none;
  border: none;
  padding: 4px;
  cursor: pointer;
  color: #8e8e93;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 8px;
  transition: color 0.2s, background 0.2s;
}

.ios-field__toggle:hover {
  color: #636366;
  background: rgba(0, 0, 0, 0.04);
}

.ios-divider {
  height: 0.5px;
  background: rgba(0, 0, 0, 0.08);
  margin-left: 45px;
}

/* ── Error ── */
.ios-error {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 14px;
  background: rgba(255, 59, 48, 0.08);
  border-radius: 12px;
  color: #ff3b30;
  font-size: 14px;
  font-weight: 500;
}

.ios-error svg {
  flex-shrink: 0;
}

.ios-alert-enter-active {
  animation: iosShake 0.4s ease;
}

.ios-alert-leave-active {
  transition: opacity 0.2s ease, transform 0.2s ease;
}

.ios-alert-leave-to {
  opacity: 0;
  transform: translateY(-4px);
}

@keyframes iosShake {
  0% { transform: translateX(0); opacity: 0; }
  15% { transform: translateX(-6px); opacity: 1; }
  30% { transform: translateX(5px); }
  45% { transform: translateX(-4px); }
  60% { transform: translateX(2px); }
  75% { transform: translateX(-1px); }
  100% { transform: translateX(0); }
}

/* ── Button ── */
.ios-button {
  width: 100%;
  height: 50px;
  border: none;
  border-radius: 14px;
  background: #007aff;
  color: #fff;
  font-family: inherit;
  font-size: 17px;
  font-weight: 600;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  letter-spacing: -0.2px;
  transition: all 0.2s cubic-bezier(0.2, 0.8, 0.2, 1);
  -webkit-tap-highlight-color: transparent;
  position: relative;
  overflow: hidden;
}

.ios-button::after {
  content: "";
  position: absolute;
  inset: 0;
  background: linear-gradient(180deg, rgba(255,255,255,0.18) 0%, transparent 50%);
  pointer-events: none;
}

.ios-button:hover:not(:disabled) {
  background: #0066d6;
  transform: translateY(-1px);
  box-shadow: 0 6px 20px rgba(0, 122, 255, 0.3);
}

.ios-button:active:not(:disabled) {
  transform: scale(0.97);
  box-shadow: none;
}

.ios-button:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}

.ios-button--loading {
  pointer-events: none;
}

.ios-spinner {
  animation: spin 0.7s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* ── Features ── */
.auth-features {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  justify-content: center;
}

.auth-feature-chip {
  display: flex;
  align-items: center;
  gap: 5px;
  padding: 6px 12px;
  border-radius: 20px;
  background: rgba(255, 255, 255, 0.65);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border: 0.5px solid rgba(0, 0, 0, 0.05);
  font-size: 12px;
  font-weight: 500;
  color: #636366;
}

.auth-feature-chip svg {
  color: #007aff;
  flex-shrink: 0;
}

/* ── Footer ── */
.auth-footer {
  text-align: center;
  font-size: 15px;
  color: #8e8e93;
}

.auth-footer a {
  color: #007aff;
  text-decoration: none;
  font-weight: 600;
}

.auth-footer a:active {
  opacity: 0.6;
}

/* ── Responsive ── */
@media (max-width: 480px) {
  .auth-page {
    padding: 0;
    align-items: flex-start;
    background: #f2f2f7;
  }

  .auth-wrapper {
    max-width: 100%;
    padding: 60px 24px 40px;
    gap: 20px;
  }

  .auth-app-icon {
    width: 56px;
    height: 56px;
    border-radius: 14px;
  }

  .auth-header h1 {
    font-size: 24px;
  }

  .ios-field input {
    font-size: 16px; /* prevent iOS zoom */
  }
}
</style>
