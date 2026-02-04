<template>
  <div class="profile-page">
    <div class="profile-card">
      <div class="profile-header">
        <h2 class="profile-title">个人资料</h2>
        <button class="btn-back" @click="router.back()">
          <ArrowLeft :size="16" />
          <span>返回</span>
        </button>
      </div>

      <!-- Avatar -->
      <div class="avatar-section">
        <div class="avatar-wrapper" @click="avatarInput?.click()">
          <img v-if="authStore.user?.avatar_display" :src="authStore.user.avatar_display" class="avatar-img" />
          <span v-else class="avatar-letter">{{ avatarLetter }}</span>
          <div class="avatar-overlay">
            <Camera :size="22" />
          </div>
        </div>
        <input
          ref="avatarInput"
          type="file"
          accept="image/*"
          style="display: none"
          @change="handleAvatarUpload"
        />
        <span class="avatar-hint">点击更换头像</span>
      </div>

      <!-- Alert -->
      <div v-if="alertMsg" class="alert" :class="alertType">{{ alertMsg }}</div>

      <!-- Form -->
      <div class="form-group">
        <label class="form-label">昵称</label>
        <input v-model="nickname" class="form-input" maxlength="30" placeholder="输入昵称" />
      </div>

      <div class="form-group">
        <label class="form-label">邮箱</label>
        <input :value="authStore.user?.email" class="form-input readonly" readonly />
      </div>

      <button class="btn-save" :disabled="saving || !nicknameChanged" @click="saveNickname">
        <Loader2 v-if="saving" :size="16" class="spin" />
        <span>{{ saving ? '保存中…' : '保存修改' }}</span>
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watchEffect } from "vue";
import { ArrowLeft, Camera, Loader2 } from "lucide-vue-next";
import { useRouter } from "vue-router";
import { useAuthStore } from "../stores/auth";
import api from "../api/client";

const router = useRouter();
const authStore = useAuthStore();
const avatarInput = ref<HTMLInputElement | null>(null);
const nickname = ref("");
const saving = ref(false);
const alertMsg = ref("");
const alertType = ref<"success" | "error">("success");

watchEffect(() => {
  if (authStore.user) {
    nickname.value = authStore.user.nickname || "";
  }
});

const avatarLetter = computed(() => {
  const name = authStore.displayName;
  return name ? name.charAt(0).toUpperCase() : "?";
});

const nicknameChanged = computed(() => {
  return nickname.value.trim() !== (authStore.user?.nickname || "");
});

function showAlert(msg: string, type: "success" | "error") {
  alertMsg.value = msg;
  alertType.value = type;
  setTimeout(() => { alertMsg.value = ""; }, 3000);
}

async function handleAvatarUpload(e: Event) {
  const input = e.target as HTMLInputElement;
  const file = input.files?.[0];
  if (!file) return;
  if (!file.type.startsWith("image/")) {
    showAlert("请选择图片文件", "error");
    input.value = "";
    return;
  }
  const form = new FormData();
  form.append("avatar", file);
  try {
    await api.patch("/auth/me/", form, {
      headers: { "Content-Type": "multipart/form-data" },
    });
    await authStore.fetchProfile();
    showAlert("头像更新成功", "success");
  } catch {
    showAlert("头像上传失败，请重试", "error");
  }
  input.value = "";
}

async function saveNickname() {
  const val = nickname.value.trim();
  if (!val) {
    showAlert("昵称不能为空", "error");
    return;
  }
  saving.value = true;
  try {
    await api.patch("/auth/me/", { nickname: val });
    await authStore.fetchProfile();
    showAlert("昵称已更新", "success");
  } catch {
    showAlert("保存失败，请重试", "error");
  } finally {
    saving.value = false;
  }
}
</script>

<style scoped>
.profile-page {
  display: flex;
  justify-content: center;
  padding: 40px 16px;
}

.profile-card {
  width: 100%;
  max-width: 420px;
  background: var(--glass-bg, rgba(255, 255, 255, 0.65));
  backdrop-filter: blur(18px);
  -webkit-backdrop-filter: blur(18px);
  border: 1px solid var(--border, rgba(0, 0, 0, 0.08));
  border-radius: var(--radius, 14px);
  padding: 32px 28px;
}

.profile-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 28px;
}

.profile-title {
  font-size: 20px;
  font-weight: 700;
  color: var(--text, #1c1c1e);
  margin: 0;
}

.btn-back {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 6px 12px;
  border: 1px solid var(--border, rgba(0, 0, 0, 0.1));
  border-radius: 8px;
  background: transparent;
  color: var(--muted, #8e8e93);
  font-size: 13px;
  font-weight: 500;
  font-family: inherit;
  cursor: pointer;
  transition: all 0.15s ease;
}

.btn-back:hover {
  background: rgba(0, 0, 0, 0.04);
  color: var(--text, #1c1c1e);
}

/* Avatar */
.avatar-section {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  margin-bottom: 24px;
}

.avatar-wrapper {
  position: relative;
  width: 80px;
  height: 80px;
  border-radius: 50%;
  cursor: pointer;
  overflow: hidden;
  background: linear-gradient(135deg, var(--accent, #007aff), #5ac8fa);
  display: flex;
  align-items: center;
  justify-content: center;
}

.avatar-wrapper .avatar-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.avatar-letter {
  color: #fff;
  font-size: 30px;
  font-weight: 700;
}

.avatar-overlay {
  position: absolute;
  inset: 0;
  background: rgba(0, 0, 0, 0.35);
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  opacity: 0;
  transition: opacity 0.2s ease;
}

.avatar-wrapper:hover .avatar-overlay {
  opacity: 1;
}

.avatar-hint {
  font-size: 12px;
  color: var(--muted, #8e8e93);
}

/* Alert */
.alert {
  padding: 10px 14px;
  border-radius: 10px;
  font-size: 13px;
  font-weight: 500;
  margin-bottom: 18px;
  text-align: center;
}

.alert.success {
  background: rgba(52, 199, 89, 0.12);
  color: #22863a;
}

.alert.error {
  background: rgba(255, 59, 48, 0.1);
  color: var(--danger, #ff3b30);
}

/* Form */
.form-group {
  margin-bottom: 18px;
}

.form-label {
  display: block;
  font-size: 13px;
  font-weight: 600;
  color: var(--text, #1c1c1e);
  margin-bottom: 6px;
}

.form-input {
  width: 100%;
  padding: 10px 14px;
  border: 1px solid var(--border, rgba(0, 0, 0, 0.1));
  border-radius: 10px;
  font-size: 14px;
  font-family: inherit;
  color: var(--text, #1c1c1e);
  background: var(--panel-solid, #fff);
  outline: none;
  transition: border-color 0.2s ease, box-shadow 0.2s ease;
  box-sizing: border-box;
}

.form-input:focus {
  border-color: var(--accent, #007aff);
  box-shadow: 0 0 0 3px rgba(0, 122, 255, 0.1);
}

.form-input.readonly {
  background: var(--bg, #f0f1f6);
  color: var(--muted, #8e8e93);
  cursor: not-allowed;
}

.btn-save {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  width: 100%;
  padding: 12px;
  border: none;
  border-radius: 10px;
  background: var(--accent, #007aff);
  color: #fff;
  font-size: 14px;
  font-weight: 600;
  font-family: inherit;
  cursor: pointer;
  transition: opacity 0.2s ease;
  margin-top: 8px;
}

.btn-save:hover:not(:disabled) {
  opacity: 0.88;
}

.btn-save:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}

.spin {
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}
</style>
