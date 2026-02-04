<template>
  <div class="auth-page">
    <div class="auth-container">
      <!-- Left: Hero -->
      <div class="auth-hero">
        <div class="auth-hero__bg">
          <div class="auth-hero__orb auth-hero__orb--1"></div>
          <div class="auth-hero__orb auth-hero__orb--2"></div>
          <div class="auth-hero__orb auth-hero__orb--3"></div>
        </div>
        <div class="auth-hero__content">
          <div class="auth-hero__brand">
            <div class="auth-hero__icon">
              <BookOpenText :size="24" color="#fff" />
            </div>
            <span>Receipt Ledger</span>
          </div>
          <h2 class="auth-hero__title">智能收据管理<br/>轻松掌控每笔开支</h2>
          <p class="auth-hero__desc">AI 自动识别收据，多人协作记账，可视化消费分析</p>
          <div class="auth-hero__features">
            <div class="auth-hero__feature">
              <ScanLine :size="18" />
              <span>拍照即录入</span>
            </div>
            <div class="auth-hero__feature">
              <Users :size="18" />
              <span>团队协作</span>
            </div>
            <div class="auth-hero__feature">
              <BarChart3 :size="18" />
              <span>消费洞察</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Right: Form -->
      <div class="auth-form-side">
        <div class="auth-card">
          <h1>欢迎回来</h1>
          <p class="auth-subtitle">登录以继续管理你的收据</p>
          <form @submit.prevent="handleLogin">
            <div class="form-field">
              <label>邮箱</label>
              <div class="input-wrapper">
                <Mail :size="16" class="input-icon" />
                <input class="input has-icon" type="email" v-model="email" required placeholder="your@email.com" />
              </div>
            </div>
            <div class="form-field">
              <label>密码</label>
              <div class="input-wrapper">
                <Lock :size="16" class="input-icon" />
                <input class="input has-icon" type="password" v-model="password" required placeholder="输入密码" />
              </div>
            </div>
            <div v-if="error" class="alert error">{{ error }}</div>
            <button class="button auth-submit" type="submit" :disabled="loading">
              <Loader2 v-if="loading" :size="18" class="spinner" />
              {{ loading ? '登录中...' : '登录' }}
            </button>
          </form>
          <div class="auth-footer">
            还没有账号？<RouterLink to="/register">注册</RouterLink>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from "vue";
import { useRouter } from "vue-router";
import { BookOpenText, Mail, Lock, Loader2, ScanLine, Users, BarChart3 } from "lucide-vue-next";
import { useAuthStore } from "../stores/auth";

const router = useRouter();
const authStore = useAuthStore();

const email = ref("");
const password = ref("");
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
.auth-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--bg, #f0f1f6);
  padding: 20px;
}

.auth-container {
  display: grid;
  grid-template-columns: 1fr 1fr;
  width: 100%;
  max-width: 960px;
  min-height: 560px;
  border-radius: 24px;
  overflow: hidden;
  box-shadow:
    0 24px 80px rgba(0, 0, 0, 0.08),
    0 4px 16px rgba(0, 0, 0, 0.04);
}

/* ── Hero (Left) ── */

.auth-hero {
  position: relative;
  background: linear-gradient(135deg, #0a1628 0%, #1a2744 50%, #0d1f3c 100%);
  padding: 48px 40px;
  display: flex;
  flex-direction: column;
  justify-content: center;
  overflow: hidden;
}

.auth-hero__bg {
  position: absolute;
  inset: 0;
  pointer-events: none;
}

.auth-hero__orb {
  position: absolute;
  border-radius: 50%;
  filter: blur(60px);
}

.auth-hero__orb--1 {
  width: 300px;
  height: 300px;
  background: rgba(59, 130, 246, 0.25);
  top: -60px;
  right: -40px;
  animation: orbFloat 8s ease-in-out infinite;
}

.auth-hero__orb--2 {
  width: 200px;
  height: 200px;
  background: rgba(99, 102, 241, 0.2);
  bottom: -30px;
  left: -20px;
  animation: orbFloat 10s ease-in-out infinite reverse;
}

.auth-hero__orb--3 {
  width: 150px;
  height: 150px;
  background: rgba(6, 182, 212, 0.15);
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  animation: orbFloat 12s ease-in-out infinite;
}

@keyframes orbFloat {
  0%, 100% { transform: translate(0, 0); }
  33% { transform: translate(10px, -15px); }
  66% { transform: translate(-8px, 10px); }
}

.auth-hero__content {
  position: relative;
  z-index: 1;
}

.auth-hero__brand {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 36px;
  font-weight: 700;
  font-size: 18px;
  color: rgba(255, 255, 255, 0.95);
  font-family: "Space Grotesk", sans-serif;
}

.auth-hero__icon {
  width: 38px;
  height: 38px;
  border-radius: 10px;
  background: linear-gradient(135deg, #3b82f6, #60a5fa);
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 4px 12px rgba(59, 130, 246, 0.35);
}

.auth-hero__title {
  font-family: "Space Grotesk", sans-serif;
  font-size: 28px;
  font-weight: 700;
  line-height: 1.3;
  color: #fff;
  margin: 0 0 16px;
  letter-spacing: -0.3px;
}

.auth-hero__desc {
  font-size: 15px;
  color: rgba(255, 255, 255, 0.55);
  line-height: 1.6;
  margin: 0 0 36px;
}

.auth-hero__features {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.auth-hero__feature {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 14px;
  font-weight: 500;
  color: rgba(255, 255, 255, 0.7);
}

.auth-hero__feature svg {
  color: rgba(96, 165, 250, 0.9);
  flex-shrink: 0;
}

/* ── Form (Right) ── */

.auth-form-side {
  background: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 48px 40px;
}

.auth-card {
  width: 100%;
  max-width: 340px;
}

.auth-card h1 {
  font-family: "Space Grotesk", sans-serif;
  font-size: 26px;
  font-weight: 700;
  margin: 0 0 6px;
  color: var(--text, #1c1c1e);
}

.auth-subtitle {
  font-size: 14px;
  color: var(--muted, #8e8e93);
  margin: 0 0 32px;
}

.form-field {
  margin-bottom: 20px;
}

.form-field label {
  display: block;
  margin-bottom: 6px;
  color: var(--text, #1c1c1e);
  font-size: 13px;
  font-weight: 600;
}

.input-wrapper {
  position: relative;
}

.input-icon {
  position: absolute;
  left: 14px;
  top: 50%;
  transform: translateY(-50%);
  color: var(--muted, #8e8e93);
  pointer-events: none;
}

.input.has-icon {
  padding-left: 40px;
}

.auth-submit {
  width: 100%;
  margin-top: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  height: 46px;
  font-size: 15px;
  border-radius: 12px;
}

.spinner {
  animation: spin 0.8s linear infinite;
}

.auth-footer {
  text-align: center;
  margin-top: 24px;
  font-size: 14px;
  color: var(--muted, #8e8e93);
}

.auth-footer a {
  color: var(--accent, #007aff);
  text-decoration: none;
  font-weight: 600;
}

.auth-footer a:hover {
  text-decoration: underline;
}

/* ── Responsive ── */

@media (max-width: 768px) {
  .auth-container {
    grid-template-columns: 1fr;
    max-width: 440px;
  }

  .auth-hero {
    padding: 32px 28px;
    min-height: auto;
  }

  .auth-hero__title {
    font-size: 22px;
  }

  .auth-hero__features {
    flex-direction: row;
    flex-wrap: wrap;
    gap: 10px 20px;
  }

  .auth-form-side {
    padding: 32px 28px;
  }
}

@media (max-width: 480px) {
  .auth-page {
    padding: 0;
    align-items: stretch;
  }

  .auth-container {
    border-radius: 0;
    min-height: 100vh;
    box-shadow: none;
  }

  .auth-hero {
    padding: 28px 24px;
  }

  .auth-hero__desc {
    display: none;
  }

  .auth-hero__title {
    font-size: 20px;
    margin-bottom: 12px;
  }

  .auth-hero__brand {
    margin-bottom: 20px;
  }

  .auth-form-side {
    padding: 28px 24px;
  }
}
</style>
