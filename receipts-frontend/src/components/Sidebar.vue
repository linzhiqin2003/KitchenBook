<template>
  <aside class="sidebar" :class="{ collapsed }">
    <div class="brand">
      <div class="brand-icon" :class="{ clickable: collapsed }" @click="collapsed && $emit('toggle')" :title="collapsed ? '展开' : ''">
        <BookOpenText :size="16" color="#fff" />
      </div>
      <span class="brand-text">收据记账本</span>
      <button v-if="!collapsed" class="collapse-btn" @click="$emit('toggle')" title="收起">
        <PanelLeftClose :size="15" />
      </button>
    </div>

    <nav class="nav">
      <RouterLink to="/">
        <span class="nav-icon"><LayoutDashboard :size="18" /></span>
        <span class="nav-label">仪表盘</span>
      </RouterLink>
      <RouterLink to="/upload">
        <span class="nav-icon"><Upload :size="18" /></span>
        <span class="nav-label">上传</span>
      </RouterLink>
      <RouterLink to="/receipts">
        <span class="nav-icon"><FileText :size="18" /></span>
        <span class="nav-label desktop-label">历史收据</span>
        <span class="nav-label mobile-label">收据</span>
      </RouterLink>
      <RouterLink to="/org-settings" class="desktop-nav-only">
        <span class="nav-icon"><Building2 :size="15" /></span>
        <span class="nav-label">组织</span>
      </RouterLink>
      <!-- Mobile-only: user tab (last position) -->
      <button v-if="authStore.isLoggedIn" class="mobile-user-tab" @click="mobileSheetOpen = true">
        <span class="nav-icon"><CircleUserRound :size="18" /></span>
        <span class="nav-label">我的</span>
      </button>
    </nav>

    <!-- Mobile bottom sheet (teleported to body) -->
    <Teleport to="body">
      <Transition name="sheet">
        <div v-if="mobileSheetOpen" class="sheet-backdrop" @click="mobileSheetOpen = false">
          <div class="sheet-container" @click.stop>
            <div class="sheet-handle"></div>
            <!-- User info -->
            <div class="sheet-user">
              <div class="sheet-avatar">
                <img v-if="authStore.user?.avatar_display" :src="authStore.user.avatar_display" class="avatar-img" />
                <span v-else>{{ avatarLetter }}</span>
              </div>
              <div class="sheet-user-detail">
                <div class="sheet-user-name">{{ authStore.displayName }}</div>
                <div class="sheet-user-email">{{ authStore.user?.email }}</div>
              </div>
            </div>
            <div class="sheet-divider"></div>
            <!-- Org switcher -->
            <div class="sheet-section-label">切换空间</div>
            <button
              class="sheet-item"
              :class="{ active: !authStore.activeOrgId }"
              @click="selectOrgMobile('')"
            >
              <User :size="18" />
              <span>个人模式</span>
              <Check v-if="!authStore.activeOrgId" :size="16" class="sheet-check" />
            </button>
            <template v-if="orgStore.orgs.length">
              <button
                v-for="org in orgStore.orgs"
                :key="org.id"
                class="sheet-item"
                :class="{ active: authStore.activeOrgId === org.id }"
                @click="selectOrgMobile(org.id)"
              >
                <Building2 :size="18" />
                <span>{{ org.name }}</span>
                <Check v-if="authStore.activeOrgId === org.id" :size="16" class="sheet-check" />
              </button>
            </template>
            <div class="sheet-divider"></div>
            <button class="sheet-item" @click="goToOrgSettings">
              <Building2 :size="18" />
              <span>组织管理</span>
            </button>
            <button class="sheet-item" @click="goToProfileMobile">
              <UserCog :size="18" />
              <span>个人资料</span>
            </button>
            <button class="sheet-item sheet-item--danger" @click="handleLogoutMobile">
              <LogOut :size="18" />
              <span>登出</span>
            </button>
          </div>
        </div>
      </Transition>
    </Teleport>

    <!-- User info + Org switcher (bottom) -->
    <div v-if="authStore.isLoggedIn && !collapsed" class="user-block">
      <input
        ref="avatarInput"
        type="file"
        accept="image/*"
        style="display: none"
        @change="handleAvatarUpload"
      />
      <button class="user-trigger" @click="dropdownOpen = !dropdownOpen">
        <div class="user-avatar" @click.stop="avatarInput?.click()" title="点击上传头像">
          <img v-if="authStore.user?.avatar_display" :src="authStore.user.avatar_display" class="avatar-img" />
          <span v-else>{{ avatarLetter }}</span>
        </div>
        <div class="user-detail">
          <div class="user-name">{{ authStore.displayName }}</div>
          <div class="user-org-label">{{ currentOrgLabel }}</div>
        </div>
        <ChevronsUpDown :size="14" class="user-chevron" />
      </button>

      <Transition name="dropdown">
        <div v-if="dropdownOpen" class="dropdown-menu">
          <div class="dropdown-section-label">切换空间</div>
          <button
            class="dropdown-item"
            :class="{ active: !authStore.activeOrgId }"
            @click="selectOrg('')"
          >
            <User :size="15" />
            <span>个人模式</span>
            <Check v-if="!authStore.activeOrgId" :size="14" class="dropdown-check" />
          </button>
          <template v-if="orgStore.orgs.length">
            <button
              v-for="org in orgStore.orgs"
              :key="org.id"
              class="dropdown-item"
              :class="{ active: authStore.activeOrgId === org.id }"
              @click="selectOrg(org.id)"
            >
              <Building2 :size="15" />
              <span>{{ org.name }}</span>
              <Check v-if="authStore.activeOrgId === org.id" :size="14" class="dropdown-check" />
            </button>
          </template>
          <div class="dropdown-divider"></div>
          <button class="dropdown-item" @click="goToProfile">
            <UserCog :size="15" />
            <span>个人资料</span>
          </button>
          <button class="dropdown-item dropdown-item--danger" @click="handleLogout">
            <LogOut :size="15" />
            <span>登出</span>
          </button>
        </div>
      </Transition>
    </div>

    <!-- Collapsed: avatar only -->
    <div v-if="authStore.isLoggedIn && collapsed" class="user-block-collapsed">
      <div class="user-avatar" @click="avatarInputCollapsed?.click()" title="点击上传头像" style="cursor: pointer">
        <img v-if="authStore.user?.avatar_display" :src="authStore.user.avatar_display" class="avatar-img" />
        <span v-else>{{ avatarLetter }}</span>
      </div>
      <input
        ref="avatarInputCollapsed"
        type="file"
        accept="image/*"
        style="display: none"
        @change="handleAvatarUpload"
      />
    </div>
  </aside>

  <!-- Click-away overlay -->
  <div v-if="dropdownOpen" class="dropdown-backdrop" @click="dropdownOpen = false"></div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { RouterLink, useRouter } from "vue-router";
import {
  BookOpenText, LayoutDashboard, Upload, FileText, Building2,
  LogOut, PanelLeftClose, PanelLeftOpen, ChevronsUpDown, Check, User, CircleUserRound, UserCog
} from "lucide-vue-next";
import { useAuthStore } from "../stores/auth";
import { useOrgStore } from "../stores/org";
import api from "../api/client";

defineProps<{ collapsed: boolean }>();
defineEmits<{ (e: "toggle"): void }>();

const router = useRouter();
const authStore = useAuthStore();
const orgStore = useOrgStore();
const dropdownOpen = ref(false);
const mobileSheetOpen = ref(false);
const avatarInput = ref<HTMLInputElement | null>(null);
const avatarInputCollapsed = ref<HTMLInputElement | null>(null);

async function handleAvatarUpload(e: Event) {
  const input = e.target as HTMLInputElement;
  const file = input.files?.[0];
  if (!file) return;
  if (!file.type.startsWith("image/")) {
    alert("请选择图片文件");
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
  } catch {
    alert("头像上传失败，请重试");
  }
  input.value = "";
}

const avatarLetter = computed(() => {
  const name = authStore.displayName;
  return name ? name.charAt(0).toUpperCase() : "?";
});

const currentOrgLabel = computed(() => {
  if (!authStore.activeOrgId) return "个人模式";
  const org = orgStore.orgs.find(o => o.id === authStore.activeOrgId);
  return org?.name || "组织";
});

function selectOrg(orgId: string) {
  dropdownOpen.value = false;
  if (orgId === authStore.activeOrgId) return;
  authStore.switchOrg(orgId);
  window.location.reload();
}

function handleLogout() {
  dropdownOpen.value = false;
  authStore.logout();
  router.push("/login");
}

function selectOrgMobile(orgId: string) {
  mobileSheetOpen.value = false;
  if (orgId === authStore.activeOrgId) return;
  authStore.switchOrg(orgId);
  window.location.reload();
}

function goToOrgSettings() {
  mobileSheetOpen.value = false;
  router.push("/org-settings");
}

function goToProfile() {
  dropdownOpen.value = false;
  router.push("/profile");
}

function goToProfileMobile() {
  mobileSheetOpen.value = false;
  router.push("/profile");
}

function handleLogoutMobile() {
  mobileSheetOpen.value = false;
  authStore.logout();
  router.push("/login");
}

onMounted(async () => {
  if (authStore.isLoggedIn) {
    try {
      await orgStore.fetchOrgs();
    } catch { /* ignore */ }
  }
});
</script>

<style scoped>
/* ── User Block ── */

.user-block {
  position: relative;
  margin-top: auto;
}

.user-trigger {
  display: flex;
  align-items: center;
  gap: 10px;
  width: 100%;
  padding: 10px;
  border: 1px solid transparent;
  border-radius: var(--radius-sm, 10px);
  background: transparent;
  cursor: pointer;
  font-family: inherit;
  transition: all 0.2s ease;
  text-align: left;
}

.user-trigger:hover {
  background: rgba(0, 0, 0, 0.04);
}

.user-trigger:active {
  background: rgba(0, 0, 0, 0.06);
}

.user-avatar {
  width: 34px;
  height: 34px;
  border-radius: 10px;
  background: linear-gradient(135deg, var(--accent, #007aff), #5ac8fa);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  font-size: 14px;
  flex-shrink: 0;
  cursor: pointer;
  overflow: hidden;
  transition: opacity 0.15s ease;
}

.user-avatar:hover {
  opacity: 0.85;
}

.avatar-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.user-detail {
  flex: 1;
  min-width: 0;
}

.user-name {
  font-size: 13px;
  font-weight: 600;
  color: var(--text, #1c1c1e);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  line-height: 1.3;
}

.user-org-label {
  font-size: 11px;
  color: var(--muted, #8e8e93);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  line-height: 1.3;
}

.user-chevron {
  color: var(--muted, #8e8e93);
  flex-shrink: 0;
  opacity: 0.6;
}

.user-block-collapsed {
  display: flex;
  justify-content: center;
  padding: 8px 0;
  margin-top: auto;
}

/* ── Dropdown ── */

.dropdown-backdrop {
  position: fixed;
  inset: 0;
  z-index: 999;
}

.dropdown-menu {
  position: absolute;
  bottom: calc(100% + 6px);
  left: 0;
  right: 0;
  z-index: 1000;
  background: var(--panel-solid, #fff);
  border: 1px solid var(--border, rgba(0, 0, 0, 0.08));
  border-radius: var(--radius, 14px);
  padding: 6px;
  box-shadow:
    0 8px 32px rgba(0, 0, 0, 0.12),
    0 2px 8px rgba(0, 0, 0, 0.06);
}

.dropdown-section-label {
  padding: 6px 10px 4px;
  font-size: 11px;
  font-weight: 600;
  color: var(--muted, #8e8e93);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.dropdown-item {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 100%;
  padding: 8px 10px;
  border: none;
  border-radius: 8px;
  background: transparent;
  color: var(--text, #1c1c1e);
  font-size: 13px;
  font-weight: 500;
  font-family: inherit;
  cursor: pointer;
  transition: all 0.15s ease;
  text-align: left;
}

.dropdown-item svg:first-child {
  color: var(--muted, #8e8e93);
  flex-shrink: 0;
}

.dropdown-item span {
  flex: 1;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.dropdown-item:hover {
  background: var(--accent-soft, rgba(0, 122, 255, 0.08));
}

.dropdown-item.active {
  color: var(--accent, #007aff);
  font-weight: 600;
}

.dropdown-item.active svg:first-child {
  color: var(--accent, #007aff);
}

.dropdown-check {
  color: var(--accent, #007aff);
  flex-shrink: 0;
  margin-left: auto;
}

.dropdown-divider {
  height: 1px;
  background: var(--border, rgba(0, 0, 0, 0.08));
  margin: 4px 6px;
}

.dropdown-item--danger {
  color: var(--danger, #ff3b30);
}

.dropdown-item--danger svg:first-child {
  color: var(--danger, #ff3b30) !important;
}

.dropdown-item--danger:hover {
  background: rgba(255, 59, 48, 0.08);
}

/* ── Transition ── */

.dropdown-enter-active {
  transition: opacity 0.15s ease, transform 0.15s cubic-bezier(0.16, 1, 0.3, 1);
}
.dropdown-leave-active {
  transition: opacity 0.1s ease, transform 0.1s ease;
}
.dropdown-enter-from,
.dropdown-leave-to {
  opacity: 0;
  transform: translateY(6px) scale(0.97);
}

/* ── Collapse Button (in brand row) ── */

.collapse-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 26px;
  height: 26px;
  border: none;
  border-radius: 6px;
  background: transparent;
  color: var(--muted, #8e8e93);
  cursor: pointer;
  transition: all 0.2s ease;
  margin-left: auto;
  flex-shrink: 0;
  padding: 0;
  opacity: 0;
}

.sidebar:hover .collapse-btn {
  opacity: 1;
}

.collapse-btn:hover {
  background: rgba(0, 0, 0, 0.06);
  color: var(--text, #1c1c1e);
}

/* ── Shared label transitions ── */

.brand-text,
.nav-label,
.footer {
  overflow: hidden;
  white-space: nowrap;
  transition: opacity 0.2s ease, width 0.2s ease;
}

.collapsed .brand-text,
.collapsed .nav-label,
.collapsed .footer {
  opacity: 0;
  width: 0;
  pointer-events: none;
}

.collapsed .brand {
  justify-content: center;
}

.brand-icon.clickable {
  cursor: pointer;
  transition: transform 0.15s ease;
}

.brand-icon.clickable:hover {
  transform: scale(1.08);
}

.collapsed .nav a {
  justify-content: center;
  padding: 10px;
}

/* ── Mobile ── */

@media (max-width: 640px) {
  .collapse-btn {
    display: none !important;
  }

  .sidebar-bottom {
    display: none !important;
  }

  .user-block,
  .user-block-collapsed {
    display: none !important;
  }

  /* Override collapsed styles on mobile — always show labels */
  .collapsed .brand-text,
  .collapsed .nav-label,
  .collapsed .footer {
    opacity: 1;
    width: auto;
    pointer-events: auto;
  }

  .nav-label {
    font-size: 11px !important;
    opacity: 1 !important;
    width: auto !important;
    pointer-events: auto !important;
  }

  .collapsed .nav a {
    justify-content: center;
    padding: 6px 4px;
  }

  .collapsed .brand {
    display: none !important;
  }
}

/* ── Mobile/Desktop label switching ── */

.mobile-label {
  display: none;
}

@media (max-width: 640px) {
  .desktop-label {
    display: none !important;
  }
  .mobile-label {
    display: inline !important;
  }
  .desktop-nav-only {
    display: none !important;
  }
}

/* ── Mobile User Tab ── */

.mobile-user-tab {
  display: none;
}

@media (max-width: 640px) {
  .mobile-user-tab {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 2px;
    background: none;
    border: none;
    font-family: inherit;
    cursor: pointer;
    padding: 6px 4px;
    color: var(--muted, #8e8e93);
    font-size: 11px;
    font-weight: 500;
    -webkit-tap-highlight-color: transparent;
  }

  .mobile-user-avatar {
    width: 24px;
    height: 24px;
    border-radius: 50%;
    background: linear-gradient(135deg, var(--accent, #007aff), #5ac8fa);
    color: #fff;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: 700;
    font-size: 11px;
    overflow: hidden;
  }

  .mobile-user-avatar .avatar-img {
    width: 100%;
    height: 100%;
    object-fit: cover;
  }
}

/* ── Bottom Sheet ── */

.sheet-backdrop {
  position: fixed;
  inset: 0;
  z-index: 9999;
  background: rgba(0, 0, 0, 0.4);
  display: flex;
  align-items: flex-end;
  justify-content: center;
  -webkit-tap-highlight-color: transparent;
}

.sheet-container {
  width: 100%;
  max-width: 500px;
  background: var(--panel-solid, #fff);
  border-radius: 16px 16px 0 0;
  padding: 12px 20px calc(env(safe-area-inset-bottom, 16px) + 16px);
  max-height: 70vh;
  overflow-y: auto;
  -webkit-overflow-scrolling: touch;
}

.sheet-handle {
  width: 36px;
  height: 4px;
  background: rgba(0, 0, 0, 0.15);
  border-radius: 2px;
  margin: 0 auto 16px;
}

.sheet-user {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 4px 0 12px;
}

.sheet-avatar {
  width: 44px;
  height: 44px;
  border-radius: 50%;
  background: linear-gradient(135deg, var(--accent, #007aff), #5ac8fa);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  font-size: 17px;
  flex-shrink: 0;
  overflow: hidden;
}

.sheet-avatar .avatar-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.sheet-user-detail {
  flex: 1;
  min-width: 0;
}

.sheet-user-name {
  font-size: 16px;
  font-weight: 600;
  color: var(--text, #1c1c1e);
  line-height: 1.3;
}

.sheet-user-email {
  font-size: 13px;
  color: var(--muted, #8e8e93);
  line-height: 1.3;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.sheet-divider {
  height: 1px;
  background: var(--border, rgba(0, 0, 0, 0.08));
  margin: 8px 0;
}

.sheet-section-label {
  padding: 8px 4px 4px;
  font-size: 12px;
  font-weight: 600;
  color: var(--muted, #8e8e93);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.sheet-item {
  display: flex;
  align-items: center;
  gap: 12px;
  width: 100%;
  padding: 12px 4px;
  border: none;
  border-radius: 10px;
  background: transparent;
  color: var(--text, #1c1c1e);
  font-size: 15px;
  font-weight: 500;
  font-family: inherit;
  cursor: pointer;
  transition: background 0.15s ease;
  text-align: left;
  -webkit-tap-highlight-color: transparent;
}

.sheet-item svg:first-child {
  color: var(--muted, #8e8e93);
  flex-shrink: 0;
}

.sheet-item span {
  flex: 1;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.sheet-item:active {
  background: rgba(0, 0, 0, 0.04);
}

.sheet-item.active {
  color: var(--accent, #007aff);
  font-weight: 600;
}

.sheet-item.active svg:first-child {
  color: var(--accent, #007aff);
}

.sheet-check {
  color: var(--accent, #007aff);
  flex-shrink: 0;
}

.sheet-item--danger {
  color: var(--danger, #ff3b30);
}

.sheet-item--danger svg:first-child {
  color: var(--danger, #ff3b30) !important;
}

/* Sheet transitions */
.sheet-enter-active {
  transition: opacity 0.25s ease;
}
.sheet-enter-active .sheet-container {
  transition: transform 0.3s cubic-bezier(0.16, 1, 0.3, 1);
}
.sheet-leave-active {
  transition: opacity 0.2s ease;
}
.sheet-leave-active .sheet-container {
  transition: transform 0.2s ease;
}

.sheet-enter-from,
.sheet-leave-to {
  opacity: 0;
}
.sheet-enter-from .sheet-container,
.sheet-leave-to .sheet-container {
  transform: translateY(100%);
}
</style>
