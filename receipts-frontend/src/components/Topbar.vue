<template>
  <div class="topbar">
    <h1>
      <component :is="iconComponent" :size="24" class="topbar-icon" />
      {{ title }}
    </h1>
    <div class="topbar-right">
      <div v-if="authStore.isOrgMode" class="org-badge">
        <Building2 :size="12" />
        {{ currentOrgName }}
      </div>
      <div class="badge">
        <Sparkles :size="14" />
        AI 智能记账
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue";
import { useRoute } from "vue-router";
import { BarChart3, UploadCloud, ClipboardList, ScanSearch, Sparkles, Building2, Settings } from "lucide-vue-next";
import { useAuthStore } from "../stores/auth";
import { useOrgStore } from "../stores/org";

const route = useRoute();
const authStore = useAuthStore();
const orgStore = useOrgStore();

const title = computed(() => {
  if (route.name === "upload") return "上传新收据";
  if (route.name === "receipts") return "账单列表";
  if (route.name === "receipt-detail") return "收据校对";
  if (route.name === "org-settings") return "组织管理";
  return "仪表盘";
});

const iconComponent = computed(() => {
  if (route.name === "upload") return UploadCloud;
  if (route.name === "receipts") return ClipboardList;
  if (route.name === "receipt-detail") return ScanSearch;
  if (route.name === "org-settings") return Settings;
  return BarChart3;
});

const currentOrgName = computed(() => {
  if (!authStore.activeOrgId) return "";
  const org = orgStore.orgs.find(o => o.id === authStore.activeOrgId);
  return org?.name || "组织";
});
</script>

<style scoped>
.topbar-icon {
  vertical-align: -4px;
  margin-right: 6px;
  color: var(--accent);
}

.topbar-right {
  display: flex;
  align-items: center;
  gap: 10px;
}

.org-badge {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 4px 12px;
  font-size: 12px;
  font-weight: 600;
  color: #3b82f6;
  background: rgba(59, 130, 246, 0.08);
  border: 1px solid rgba(59, 130, 246, 0.15);
  border-radius: 20px;
}

@media (max-width: 640px) {
  .topbar-icon {
    display: none;
  }

  .topbar {
    flex-wrap: wrap;
    gap: 8px;
  }

  .topbar h1 {
    font-size: 20px;
  }

  .topbar-right {
    gap: 6px;
  }

  .org-badge {
    font-size: 11px;
    padding: 3px 8px;
  }
}
</style>
