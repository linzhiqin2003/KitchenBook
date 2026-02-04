<template>
  <div class="panel" style="margin-bottom: 20px;">
    <div class="panel-header">
      <h2>我的组织</h2>
      <button class="button" @click="showCreateForm = !showCreateForm">
        <Plus :size="16" />
        创建组织
      </button>
    </div>

    <div v-if="showCreateForm" class="create-form">
      <input class="input" v-model="newOrgName" placeholder="组织名称" @keyup.enter="createOrg" />
      <button class="button" @click="createOrg" :disabled="!newOrgName.trim()">确定</button>
    </div>

    <div v-if="!orgStore.orgs.length" class="empty-hint">
      还没有加入任何组织，创建一个或通过邀请链接加入。
    </div>

    <div
      v-for="org in orgStore.orgs"
      :key="org.id"
      class="org-card"
      :class="{ active: authStore.activeOrgId === org.id }"
    >
      <!-- Card Header -->
      <div class="org-header">
        <div class="org-icon">
          <Building2 :size="16" />
        </div>
        <div class="org-detail">
          <div class="org-name">{{ org.name }}</div>
          <div class="org-meta">
            <Users2 :size="12" />
            <span>{{ org.member_count }} 位成员</span>
          </div>
        </div>
        <span v-if="authStore.activeOrgId === org.id" class="status-dot"></span>
        <button
          v-if="myRole[org.id] === 'member'"
          class="action-link danger-text"
          @click="handleLeaveOrg(org)"
        >
          <LogOut :size="12" />
          退出
        </button>
        <button
          v-if="myRole[org.id] === 'owner'"
          class="action-link danger-text"
          @click="handleDissolveOrg(org)"
        >
          <Trash2 :size="12" />
          解散
        </button>
      </div>

      <!-- Tab Bar -->
      <div class="org-tabs">
        <button
          class="org-tab"
          :class="{ active: activeTab[org.id] === 'members' }"
          @click="setTab(org.id, 'members')"
        >
          <Users2 :size="14" />
          成员
        </button>
        <button
          class="org-tab"
          :class="{ active: activeTab[org.id] === 'invite' }"
          @click="setTab(org.id, 'invite')"
        >
          <Link2 :size="14" />
          邀请
        </button>
      </div>

      <!-- Tab Content: Members -->
      <Transition name="tab-fade">
        <div v-if="activeTab[org.id] === 'members'" class="tab-content">
          <div v-if="!members[org.id]?.length" class="tab-empty">
            <Loader2 v-if="loadingMembers[org.id]" :size="16" class="spinner" />
            <span v-else>暂无成员数据</span>
          </div>
          <div v-else class="members-list">
            <div v-for="m in members[org.id]" :key="m.id" class="member-row">
              <div class="member-avatar">
                <img v-if="m.avatar_display" :src="m.avatar_display" class="member-avatar-img" />
                <span v-else>{{ (m.nickname || m.email).charAt(0).toUpperCase() }}</span>
              </div>
              <div class="member-info">
                <div class="member-name">
                  {{ m.nickname || m.email }}
                  <span class="role-badge" :class="m.role">
                    {{ m.role === 'owner' ? '管理员' : '成员' }}
                  </span>
                </div>
                <div class="member-email" v-if="m.nickname">{{ m.email }}</div>
              </div>
              <button
                v-if="myRole[org.id] === 'owner' && m.role === 'member' && m.email !== authStore.user?.email"
                class="button ghost danger-text remove-btn"
                @click="handleRemoveMember(org.id, m)"
              >
                <UserMinus :size="14" />
              </button>
            </div>
          </div>
        </div>
      </Transition>

      <!-- Tab Content: Invite -->
      <Transition name="tab-fade">
        <div v-if="activeTab[org.id] === 'invite'" class="tab-content">
          <div v-if="inviteLink[org.id]" class="invite-link-box">
            <div class="invite-url">
              <Link2 :size="14" class="invite-url-icon" />
              <input class="input invite-input" :value="inviteLink[org.id]" readonly />
            </div>
            <button class="button ghost copy-btn" @click="copyInviteLink(org.id)">
              <ClipboardCopy v-if="!copied[org.id]" :size="14" />
              <ClipboardCheck v-else :size="14" />
              {{ copied[org.id] ? '已复制' : '复制' }}
            </button>
          </div>
          <div v-else class="invite-generate">
            <p class="invite-hint">生成一次性邀请链接，分享给你想邀请的成员。</p>
            <button class="button" @click="generateInvite(org.id)">
              <Link2 :size="15" />
              生成邀请链接
            </button>
          </div>
        </div>
      </Transition>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from "vue";
import {
  Plus, Building2, Users2,
  Link2, Loader2, ClipboardCopy, ClipboardCheck,
  UserMinus, LogOut, Trash2
} from "lucide-vue-next";
import { useAuthStore } from "../stores/auth";
import { useOrgStore } from "../stores/org";
import type { OrgMember } from "../stores/org";

const authStore = useAuthStore();
const orgStore = useOrgStore();

const showCreateForm = ref(false);
const newOrgName = ref("");

const activeTab = reactive<Record<string, string>>({});
const members = reactive<Record<string, OrgMember[]>>({});
const loadingMembers = reactive<Record<string, boolean>>({});
const myRole = reactive<Record<string, string>>({});
const inviteLink = reactive<Record<string, string>>({});
const copied = reactive<Record<string, boolean>>({});

async function createOrg() {
  if (!newOrgName.value.trim()) return;
  await orgStore.createOrg(newOrgName.value.trim());
  newOrgName.value = "";
  showCreateForm.value = false;
}

async function setTab(orgId: string, tab: string) {
  if (activeTab[orgId] === tab) {
    activeTab[orgId] = "";
    return;
  }
  activeTab[orgId] = tab;

  if (tab === "members" && !members[orgId]) {
    loadingMembers[orgId] = true;
    try {
      members[orgId] = await orgStore.fetchMembers(orgId);
      const me = members[orgId]?.find((m) => m.email === authStore.user?.email);
      if (me) myRole[orgId] = me.role;
    } catch { /* ignore */ }
    loadingMembers[orgId] = false;
  }
}

async function generateInvite(orgId: string) {
  const invite = await orgStore.createInvite(orgId);
  inviteLink[orgId] = `${window.location.origin}/invite/${invite.id}`;
}

function copyInviteLink(orgId: string) {
  navigator.clipboard.writeText(inviteLink[orgId]);
  copied[orgId] = true;
  setTimeout(() => { copied[orgId] = false; }, 2000);
}

async function handleRemoveMember(orgId: string, m: OrgMember) {
  if (!window.confirm(`确定移除成员「${m.nickname || m.email}」？`)) return;
  try {
    await orgStore.removeMember(orgId, m.id);
    members[orgId] = members[orgId].filter((x) => x.id !== m.id);
  } catch (e: any) {
    alert(e.response?.data?.detail || "操作失败");
  }
}

async function handleLeaveOrg(org: { id: string; name: string }) {
  if (!window.confirm(`确定退出「${org.name}」？`)) return;
  try {
    await orgStore.leaveOrg(org.id);
    if (authStore.activeOrgId === org.id) authStore.switchOrg("");
  } catch (e: any) {
    alert(e.response?.data?.detail || "操作失败");
  }
}

async function handleDissolveOrg(org: { id: string; name: string }) {
  if (!window.confirm(`确定解散「${org.name}」？此操作不可撤销。`)) return;
  try {
    await orgStore.dissolveOrg(org.id);
    if (authStore.activeOrgId === org.id) authStore.switchOrg("");
  } catch (e: any) {
    alert(e.response?.data?.detail || "操作失败");
  }
}

onMounted(async () => {
  await orgStore.fetchOrgs();
});
</script>

<style scoped>
.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.panel-header h2 {
  margin: 0;
}

.panel-header .button {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.create-form {
  display: flex;
  gap: 10px;
  margin-bottom: 16px;
}

.create-form .input {
  flex: 1;
}

.empty-hint {
  color: var(--muted);
  font-size: 14px;
  text-align: center;
  padding: 24px 0;
}

/* ── Org Card ── */

.org-card {
  border: 1px solid var(--border, #e5e5e5);
  border-radius: 14px;
  padding: 0;
  margin-bottom: 12px;
  transition: all 0.2s ease;
  overflow: hidden;
}

.org-card.active {
  border-color: rgba(0, 122, 255, 0.25);
  background: rgba(0, 122, 255, 0.02);
}

/* ── Card Header ── */

.org-header {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px 18px;
}

.org-icon {
  width: 38px;
  height: 38px;
  border-radius: 10px;
  background: linear-gradient(135deg, #e0e7ff, #c7d2fe);
  color: #4f46e5;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.org-card.active .org-icon {
  background: linear-gradient(135deg, var(--accent, #007aff), #5ac8fa);
  color: #fff;
}

.org-detail {
  flex: 1;
  min-width: 0;
}

.org-name {
  font-size: 15px;
  font-weight: 600;
  color: var(--text, #1c1c1e);
  line-height: 1.3;
}

.org-meta {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  color: var(--muted, #8e8e93);
  margin-top: 2px;
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--accent, #007aff);
  flex-shrink: 0;
  box-shadow: 0 0 0 3px rgba(0, 122, 255, 0.15);
}

/* ── Tabs ── */

.org-tabs {
  display: flex;
  border-top: 1px solid var(--border, rgba(0, 0, 0, 0.06));
}

.org-tab {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 10px 0;
  border: none;
  border-bottom: 2px solid transparent;
  background: transparent;
  color: var(--muted, #8e8e93);
  font-size: 13px;
  font-weight: 500;
  font-family: inherit;
  cursor: pointer;
  transition: all 0.15s ease;
}

.org-tab:hover {
  color: var(--text, #1c1c1e);
  background: rgba(0, 0, 0, 0.02);
}

.org-tab.active {
  color: var(--accent, #007aff);
  border-bottom-color: var(--accent, #007aff);
}

.org-tab + .org-tab {
  border-left: 1px solid var(--border, rgba(0, 0, 0, 0.06));
}

/* ── Tab Content ── */

.tab-content {
  padding: 14px 18px;
  border-top: 1px solid var(--border, rgba(0, 0, 0, 0.06));
  background: rgba(0, 0, 0, 0.015);
}

.tab-empty {
  text-align: center;
  padding: 16px 0;
  color: var(--muted, #8e8e93);
  font-size: 13px;
}

/* ── Members ── */

.members-list {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.member-row {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 10px;
  border-radius: 8px;
  transition: background 0.15s ease;
}

.member-row:hover {
  background: rgba(0, 0, 0, 0.03);
}

.member-avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: linear-gradient(135deg, #3b82f6, #60a5fa);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  font-size: 13px;
  flex-shrink: 0;
  overflow: hidden;
}

.member-avatar-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.member-info {
  flex: 1;
  min-width: 0;
}

.member-name {
  font-weight: 500;
  font-size: 13px;
  color: var(--text, #1c1c1e);
  display: flex;
  align-items: center;
  gap: 6px;
}

.member-email {
  font-size: 11px;
  color: var(--muted, #8e8e93);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.role-badge {
  font-size: 11px;
  font-weight: 600;
  padding: 3px 8px;
  border-radius: 20px;
  flex-shrink: 0;
}

.role-badge.owner {
  background: rgba(255, 149, 0, 0.1);
  color: #ff9500;
}

.role-badge.member {
  background: rgba(0, 0, 0, 0.04);
  color: var(--muted, #8e8e93);
}

/* ── Remove Button ── */

.remove-btn {
  padding: 4px 8px !important;
  min-height: auto;
  flex-shrink: 0;
}

/* ── Actions ── */

.action-link {
  background: none;
  border: none;
  font-family: inherit;
  font-size: 12px;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 4px 0;
  opacity: 0.5;
  transition: opacity 0.15s ease;
}

.action-link:hover {
  opacity: 1;
}

.danger-text {
  color: #ff3b30 !important;
}

/* ── Invite ── */

.invite-generate {
  text-align: center;
  padding: 8px 0;
}

.invite-hint {
  font-size: 13px;
  color: var(--muted, #8e8e93);
  margin: 0 0 12px;
}

.invite-generate .button {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.invite-link-box {
  display: flex;
  gap: 8px;
  align-items: center;
}

.invite-url {
  flex: 1;
  position: relative;
  min-width: 0;
}

.invite-url-icon {
  position: absolute;
  left: 12px;
  top: 50%;
  transform: translateY(-50%);
  color: var(--muted, #8e8e93);
  pointer-events: none;
}

.invite-input {
  padding-left: 34px !important;
  font-size: 12px !important;
  font-family: "SF Mono", Monaco, Menlo, monospace;
}

.copy-btn {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  white-space: nowrap;
  font-size: 12px;
  flex-shrink: 0;
}

/* ── Spinner ── */

.spinner {
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* ── Tab Transition ── */

.tab-fade-enter-active {
  transition: opacity 0.15s ease;
}
.tab-fade-leave-active {
  transition: opacity 0.1s ease;
}
.tab-fade-enter-from,
.tab-fade-leave-to {
  opacity: 0;
}

/* ── Mobile ── */

@media (max-width: 640px) {
  .panel-header h2 {
    font-size: 15px;
  }

  .org-card {
    border-radius: 10px;
  }

  .org-header {
    padding: 12px 14px;
    gap: 10px;
  }

  .org-icon {
    width: 32px;
    height: 32px;
    border-radius: 8px;
  }

  .org-name {
    font-size: 14px;
  }

  .org-tab {
    padding: 10px 0;
    min-height: 44px;
  }

  .tab-content {
    padding: 12px 14px;
  }

  .member-row {
    padding: 8px 6px;
    gap: 8px;
  }

  .member-avatar {
    width: 28px;
    height: 28px;
    font-size: 12px;
  }

  .member-name {
    font-size: 13px;
    flex-wrap: wrap;
  }

  .role-badge {
    font-size: 10px;
    padding: 2px 6px;
  }

  .invite-link-box {
    flex-direction: column;
    align-items: stretch;
  }

  .copy-btn {
    align-self: flex-end;
  }

  .action-link {
    font-size: 11px;
  }
}
</style>
