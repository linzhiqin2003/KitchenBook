<template>
  <div class="invite-page">
    <div class="invite-bg">
      <div class="invite-bg__orb invite-bg__orb--1"></div>
      <div class="invite-bg__orb invite-bg__orb--2"></div>
      <div class="invite-bg__orb invite-bg__orb--3"></div>
    </div>

    <div class="invite-card" :class="{ 'invite-card--success': !!result }">
      <!-- Loading -->
      <div v-if="loading" class="invite-body invite-body--center">
        <div class="invite-loader">
          <div class="invite-loader__ring"></div>
        </div>
        <p class="invite-hint">{{ result ? '加入中...' : '加载邀请信息...' }}</p>
      </div>

      <!-- Error -->
      <div v-else-if="error" class="invite-body invite-body--center">
        <div class="invite-icon invite-icon--error">
          <XCircle :size="28" />
        </div>
        <h2 class="invite-title">无法加入</h2>
        <p class="invite-desc">{{ error }}</p>
        <RouterLink v-if="!authStore.isLoggedIn" class="invite-btn" to="/login">
          <LogIn :size="16" />
          登录后重试
        </RouterLink>
        <RouterLink v-else class="invite-btn invite-btn--ghost" to="/">
          返回首页
        </RouterLink>
      </div>

      <!-- Success -->
      <div v-else-if="result" class="invite-body invite-body--center">
        <div class="invite-icon invite-icon--success">
          <Check :size="28" stroke-width="3" />
        </div>
        <h2 class="invite-title">加入成功</h2>
        <p class="invite-desc">你已成为 <strong>{{ result.org_name }}</strong> 的成员</p>
        <button class="invite-btn" @click="switchAndGo">
          <ArrowRight :size="16" />
          进入组织
        </button>
        <RouterLink class="invite-link" to="/">返回首页</RouterLink>
      </div>

      <!-- Already Member -->
      <div v-else-if="inviteInfo && inviteInfo.already_member" class="invite-body invite-body--center">
        <div class="invite-icon invite-icon--member">
          <CircleCheckBig :size="28" />
        </div>
        <h2 class="invite-title">你已是成员</h2>
        <p class="invite-desc">你已经加入了 <strong>{{ inviteInfo.org_name }}</strong></p>
        <button class="invite-btn" @click="switchToOrg">
          <ArrowRight :size="16" />
          进入组织
        </button>
        <RouterLink class="invite-link" to="/">返回首页</RouterLink>
      </div>

      <!-- Invite Pending -->
      <div v-else-if="inviteInfo" class="invite-body">
        <div class="invite-envelope">
          <div class="invite-envelope__icon">
            <Users :size="24" />
          </div>
        </div>
        <div class="invite-content">
          <p class="invite-label">邀请你加入</p>
          <h2 class="invite-org-name">{{ inviteInfo.org_name }}</h2>
          <div class="invite-meta">
            <div class="invite-meta__item">
              <Shield :size="14" />
              <span>安全的团队空间</span>
            </div>
            <div class="invite-meta__item">
              <Users :size="14" />
              <span>共享收据与账单</span>
            </div>
          </div>
        </div>
        <button class="invite-btn" @click="accept">
          <UserPlus :size="16" />
          接受邀请
        </button>
        <p v-if="!authStore.isLoggedIn" class="invite-footnote">
          需要先 <RouterLink to="/login">登录</RouterLink> 才能加入
        </p>
      </div>
    </div>

    <div class="invite-footer">
      <div class="invite-footer__brand">
        <BookOpenText :size="14" />
        <span>收据记账本</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from "vue";
import { useRoute, useRouter } from "vue-router";
import {
  BookOpenText, Users, UserPlus, Shield,
  XCircle, Check, ArrowRight, LogIn, CircleCheckBig
} from "lucide-vue-next";
import { useAuthStore } from "../stores/auth";
import { useOrgStore } from "../stores/org";

const route = useRoute();
const router = useRouter();
const authStore = useAuthStore();
const orgStore = useOrgStore();

const loading = ref(true);
const error = ref("");
const inviteInfo = ref<any>(null);
const result = ref<any>(null);

async function loadInvite() {
  const inviteId = route.params.id as string;
  try {
    const info = await orgStore.getInviteInfo(inviteId);
    inviteInfo.value = info;
  } catch (err: any) {
    error.value = err?.response?.data?.detail || "邀请链接无效或已过期";
  } finally {
    loading.value = false;
  }
}

async function accept() {
  loading.value = true;
  const inviteId = route.params.id as string;
  try {
    result.value = await orgStore.acceptInvite(inviteId);
    await orgStore.fetchOrgs();
  } catch (err: any) {
    error.value = err?.response?.data?.detail || "接受邀请失败，请稍后重试";
  } finally {
    loading.value = false;
  }
}

function switchAndGo() {
  if (result.value?.org_id) {
    authStore.switchOrg(result.value.org_id);
  }
  router.push("/");
}

function switchToOrg() {
  if (inviteInfo.value?.org_id) {
    authStore.switchOrg(inviteInfo.value.org_id);
  }
  router.push("/");
}

onMounted(loadInvite);
</script>

<style scoped>
.invite-page {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background: linear-gradient(145deg, #e8ecf4 0%, #d5dbe8 40%, #c9d0e0 100%);
  padding: 20px;
  position: relative;
  overflow: hidden;
}

/* ── Animated background orbs ── */
.invite-bg {
  position: absolute;
  inset: 0;
  pointer-events: none;
}

.invite-bg__orb {
  position: absolute;
  border-radius: 50%;
  filter: blur(80px);
  opacity: 0.6;
}

.invite-bg__orb--1 {
  width: 400px;
  height: 400px;
  background: rgba(59, 130, 246, 0.18);
  top: -120px;
  right: -80px;
  animation: orbDrift 14s ease-in-out infinite;
}

.invite-bg__orb--2 {
  width: 300px;
  height: 300px;
  background: rgba(139, 92, 246, 0.12);
  bottom: -80px;
  left: -60px;
  animation: orbDrift 18s ease-in-out infinite reverse;
}

.invite-bg__orb--3 {
  width: 200px;
  height: 200px;
  background: rgba(6, 182, 212, 0.1);
  top: 40%;
  left: 60%;
  animation: orbDrift 12s ease-in-out infinite;
}

@keyframes orbDrift {
  0%, 100% { transform: translate(0, 0) scale(1); }
  33% { transform: translate(15px, -20px) scale(1.05); }
  66% { transform: translate(-10px, 12px) scale(0.95); }
}

/* ── Card ── */
.invite-card {
  position: relative;
  z-index: 1;
  width: 100%;
  max-width: 380px;
  background: rgba(255, 255, 255, 0.72);
  backdrop-filter: blur(40px) saturate(1.4);
  -webkit-backdrop-filter: blur(40px) saturate(1.4);
  border-radius: 24px;
  border: 1px solid rgba(255, 255, 255, 0.6);
  box-shadow:
    0 8px 40px rgba(0, 0, 0, 0.06),
    0 1px 3px rgba(0, 0, 0, 0.04),
    inset 0 1px 0 rgba(255, 255, 255, 0.5);
  overflow: hidden;
  animation: cardAppear 0.5s cubic-bezier(0.34, 1.56, 0.64, 1) both;
}

.invite-card--success {
  border-color: rgba(34, 197, 94, 0.2);
  box-shadow:
    0 8px 40px rgba(34, 197, 94, 0.08),
    0 1px 3px rgba(0, 0, 0, 0.04),
    inset 0 1px 0 rgba(255, 255, 255, 0.5);
}

@keyframes cardAppear {
  from {
    opacity: 0;
    transform: translateY(20px) scale(0.96);
  }
  to {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}

/* ── Body ── */
.invite-body {
  padding: 36px 32px 32px;
}

.invite-body--center {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
}

/* ── Loading ── */
.invite-loader {
  width: 44px;
  height: 44px;
  position: relative;
  margin-bottom: 16px;
}

.invite-loader__ring {
  width: 100%;
  height: 100%;
  border-radius: 50%;
  border: 3px solid rgba(59, 130, 246, 0.12);
  border-top-color: #3b82f6;
  animation: loaderSpin 0.9s cubic-bezier(0.4, 0, 0.2, 1) infinite;
}

@keyframes loaderSpin {
  to { transform: rotate(360deg); }
}

.invite-hint {
  font-size: 14px;
  color: #8e8e93;
  margin: 0;
}

/* ── Icons ── */
.invite-icon {
  width: 56px;
  height: 56px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 16px;
}

.invite-icon--error {
  background: rgba(239, 68, 68, 0.1);
  color: #ef4444;
}

.invite-icon--success {
  background: rgba(34, 197, 94, 0.1);
  color: #22c55e;
  animation: successPop 0.4s cubic-bezier(0.34, 1.56, 0.64, 1) 0.1s both;
}

.invite-icon--member {
  background: rgba(59, 130, 246, 0.1);
  color: #3b82f6;
}

@keyframes successPop {
  from { transform: scale(0.5); opacity: 0; }
  to { transform: scale(1); opacity: 1; }
}

/* ── Envelope (invite pending) ── */
.invite-envelope {
  display: flex;
  justify-content: center;
  margin-bottom: 24px;
}

.invite-envelope__icon {
  width: 64px;
  height: 64px;
  border-radius: 20px;
  background: linear-gradient(135deg, #3b82f6, #6366f1);
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  box-shadow: 0 8px 24px rgba(59, 130, 246, 0.25);
  animation: envelopeBounce 0.6s cubic-bezier(0.34, 1.56, 0.64, 1) 0.2s both;
}

@keyframes envelopeBounce {
  from { transform: scale(0.6) rotate(-8deg); opacity: 0; }
  to { transform: scale(1) rotate(0deg); opacity: 1; }
}

/* ── Text ── */
.invite-title {
  font-size: 22px;
  font-weight: 700;
  color: #1c1c1e;
  margin: 0 0 8px;
  letter-spacing: -0.3px;
}

.invite-desc {
  font-size: 14px;
  color: #8e8e93;
  margin: 0 0 24px;
  line-height: 1.5;
}

.invite-desc strong {
  color: #1c1c1e;
  font-weight: 600;
}

.invite-label {
  font-size: 13px;
  font-weight: 500;
  color: #8e8e93;
  text-transform: uppercase;
  letter-spacing: 0.8px;
  margin: 0 0 6px;
  text-align: center;
}

.invite-org-name {
  font-size: 26px;
  font-weight: 700;
  color: #1c1c1e;
  margin: 0 0 20px;
  text-align: center;
  letter-spacing: -0.3px;
}

/* ── Meta tags ── */
.invite-meta {
  display: flex;
  justify-content: center;
  gap: 16px;
  margin-bottom: 28px;
}

.invite-meta__item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: #8e8e93;
  font-weight: 500;
}

.invite-meta__item svg {
  color: rgba(59, 130, 246, 0.6);
  flex-shrink: 0;
}

/* ── Button ── */
.invite-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  width: 100%;
  height: 50px;
  border: none;
  border-radius: 14px;
  background: linear-gradient(135deg, #3b82f6, #2563eb);
  color: #fff;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
  box-shadow: 0 4px 14px rgba(59, 130, 246, 0.3);
  text-decoration: none;
}

.invite-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 6px 20px rgba(59, 130, 246, 0.35);
}

.invite-btn:active {
  transform: translateY(0) scale(0.98);
  box-shadow: 0 2px 8px rgba(59, 130, 246, 0.25);
}

.invite-btn--ghost {
  background: rgba(0, 0, 0, 0.04);
  color: #1c1c1e;
  box-shadow: none;
}

.invite-btn--ghost:hover {
  background: rgba(0, 0, 0, 0.07);
  box-shadow: none;
}

.invite-btn--ghost:active {
  background: rgba(0, 0, 0, 0.1);
  box-shadow: none;
}

/* ── Link ── */
.invite-link {
  display: block;
  text-align: center;
  margin-top: 14px;
  font-size: 14px;
  color: #8e8e93;
  text-decoration: none;
  transition: color 0.2s;
}

.invite-link:hover {
  color: #3b82f6;
}

/* ── Footnote ── */
.invite-footnote {
  font-size: 13px;
  color: #8e8e93;
  margin: 16px 0 0;
  text-align: center;
}

.invite-footnote a {
  color: #3b82f6;
  font-weight: 600;
  text-decoration: none;
}

.invite-footnote a:hover {
  text-decoration: underline;
}

/* ── Footer ── */
.invite-footer {
  position: relative;
  z-index: 1;
  margin-top: 32px;
}

.invite-footer__brand {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  font-size: 13px;
  font-weight: 500;
  color: rgba(0, 0, 0, 0.25);
}

/* ── Responsive ── */
@media (max-width: 480px) {
  .invite-page {
    padding: 16px;
  }

  .invite-card {
    max-width: 100%;
    border-radius: 20px;
  }

  .invite-body {
    padding: 28px 24px 24px;
  }

  .invite-org-name {
    font-size: 22px;
  }

  .invite-meta {
    flex-direction: column;
    align-items: center;
    gap: 8px;
  }
}
</style>
