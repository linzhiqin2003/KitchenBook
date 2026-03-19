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
        <h1>创建账号</h1>
        <p>注册后即可开始使用</p>
      </div>

      <!-- Form Card (iOS grouped style) -->
      <form class="auth-form" @submit.prevent="handleRegister" :style="{ animationDelay: '0.12s' }">
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
            <UserIcon :size="17" class="ios-field__icon" />
            <input
              v-model="nickname"
              required
              placeholder="昵称"
              autocomplete="nickname"
            />
          </div>
          <div class="ios-divider"></div>
          <div class="ios-field">
            <Lock :size="17" class="ios-field__icon" />
            <input
              :type="showPassword ? 'text' : 'password'"
              v-model="password"
              required
              minlength="6"
              placeholder="密码（至少 6 位）"
              autocomplete="new-password"
            />
            <button type="button" class="ios-field__toggle" @click="showPassword = !showPassword" tabindex="-1">
              <EyeOff v-if="showPassword" :size="17" />
              <Eye v-else :size="17" />
            </button>
          </div>
          <div class="ios-divider"></div>
          <div class="ios-field">
            <Lock :size="17" class="ios-field__icon" />
            <input
              :type="showPassword ? 'text' : 'password'"
              v-model="password2"
              required
              placeholder="确认密码"
              autocomplete="new-password"
            />
          </div>
        </div>

        <!-- Error / Success -->
        <Transition name="ios-alert">
          <div v-if="error" class="ios-error">
            <AlertCircle :size="15" />
            <span>{{ error }}</span>
          </div>
        </Transition>
        <Transition name="ios-success">
          <div v-if="success" class="ios-success">
            <CheckCircle2 :size="15" />
            <span>{{ success }}</span>
          </div>
        </Transition>

        <!-- Submit -->
        <button class="ios-button" type="submit" :disabled="loading" :class="{ 'ios-button--loading': loading }">
          <Loader2 v-if="loading" :size="18" class="ios-spinner" />
          <span>{{ loading ? '注册中…' : '注册' }}</span>
        </button>
      </form>

      <!-- Footer -->
      <div class="auth-footer" :style="{ animationDelay: '0.18s' }">
        已有账号？<RouterLink to="/login">登录</RouterLink>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from "vue";
import { useRouter } from "vue-router";
import { BookOpenText, Mail, Lock, Eye, EyeOff, Loader2, AlertCircle, CheckCircle2, User as UserIcon } from "lucide-vue-next";
import { useAuthStore } from "../stores/auth";

const router = useRouter();
const authStore = useAuthStore();

const email = ref("");
const nickname = ref("");
const password = ref("");
const password2 = ref("");
const showPassword = ref(false);
const loading = ref(false);
const error = ref("");
const success = ref("");

async function handleRegister() {
  error.value = "";
  success.value = "";

  if (!nickname.value.trim()) {
    error.value = "请输入昵称";
    return;
  }
  if (password.value !== password2.value) {
    error.value = "两次输入的密码不一致";
    return;
  }

  loading.value = true;
  try {
    await authStore.register(email.value, password.value, nickname.value);
    success.value = "注册成功，正在自动登录...";
    await authStore.login(email.value, password.value);
    router.push("/");
  } catch (err: any) {
    if (!err.response) {
      error.value = "无法连接服务器，请检查网络或稍后重试";
    } else {
      const data = err.response.data;
      if (data?.email) {
        error.value = Array.isArray(data.email) ? data.email[0] : data.email;
      } else if (data?.nickname) {
        error.value = Array.isArray(data.nickname) ? data.nickname[0] : data.nickname;
      } else if (data?.password) {
        error.value = Array.isArray(data.password) ? data.password[0] : data.password;
      } else {
        error.value = data?.detail || "注册失败，请稍后重试";
      }
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
  background: rgba(88, 86, 214, 0.15);
  top: -10%;
  left: -5%;
  animation: blobDrift 14s ease-in-out infinite;
}

.auth-blob--2 {
  width: 300px;
  height: 300px;
  background: rgba(0, 122, 255, 0.12);
  bottom: -5%;
  right: -5%;
  animation: blobDrift 18s ease-in-out infinite reverse;
}

.auth-blob--3 {
  width: 200px;
  height: 200px;
  background: rgba(255, 159, 10, 0.1);
  top: 50%;
  right: 30%;
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
  background: linear-gradient(145deg, #5856d6, #007aff);
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow:
    0 8px 24px rgba(88, 86, 214, 0.3),
    0 2px 8px rgba(88, 86, 214, 0.15);
}

.auth-app-name {
  font-family: "Space Grotesk", -apple-system, sans-serif;
  font-size: 15px;
  font-weight: 600;
  color: #8e8e93;
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

/* ── Error / Success ── */
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

.ios-success {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 14px;
  background: rgba(52, 199, 89, 0.08);
  border-radius: 12px;
  color: #34c759;
  font-size: 14px;
  font-weight: 500;
}

.ios-success svg {
  flex-shrink: 0;
}

.ios-alert-enter-active {
  animation: iosShake 0.4s ease;
}

.ios-alert-leave-active,
.ios-success-leave-active {
  transition: opacity 0.2s ease, transform 0.2s ease;
}

.ios-alert-leave-to,
.ios-success-leave-to {
  opacity: 0;
  transform: translateY(-4px);
}

.ios-success-enter-active {
  transition: opacity 0.3s ease, transform 0.3s ease;
}

.ios-success-enter-from {
  opacity: 0;
  transform: translateY(8px);
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
    padding: 48px 24px 40px;
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
    font-size: 16px;
  }
}
</style>
