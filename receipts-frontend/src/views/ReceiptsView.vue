<template>
  <div class="panel">
    <div class="panel-header">
      <h2>账单列表</h2>
      <button class="button" @click="createManual" :disabled="creating">
        <PenLine :size="16" />
        {{ creating ? '创建中...' : '手动记账' }}
      </button>
    </div>

    <!-- 筛选栏 -->
    <div class="filter-bar">
      <div class="filter-grid">
        <div class="filter-field">
          <label>商店</label>
          <select class="input" v-model="filterMerchant">
            <option value="">全部</option>
            <option v-for="m in merchantOptions" :key="m" :value="m">{{ m }}</option>
          </select>
        </div>
        <div class="filter-field">
          <label>付款人</label>
          <select class="input" v-model="filterPayer">
            <option value="">全部</option>
            <option v-for="p in payerOptions" :key="p" :value="p">{{ p }}</option>
          </select>
        </div>
        <div class="filter-field">
          <label>开始日期</label>
          <input class="input" type="date" v-model="filterDateFrom" />
        </div>
        <div class="filter-field">
          <label>结束日期</label>
          <input class="input" type="date" v-model="filterDateTo" />
        </div>
      </div>
      <div v-if="hasActiveFilter" class="filter-footer">
        <span class="filter-summary">共 {{ filteredReceipts.length }} / {{ receipts.length }} 条</span>
        <button class="button ghost" @click="clearFilters">
          <X :size="14" />
          清除筛选
        </button>
      </div>
    </div>

    <table v-if="filteredReceipts.length" class="table">
      <thead>
        <tr>
          <th>购买日期</th>
          <th>商店</th>
          <th>付款人</th>
          <th>金额</th>
          <th>状态</th>
          <th>创建时间</th>
          <th>操作</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="receipt in filteredReceipts" :key="receipt.id" class="receipt-row">
          <td data-label="购买日期">{{ formatDate(receipt.purchased_at) }}</td>
          <td data-label="商店">{{ receipt.merchant || "-" }}</td>
          <td data-label="付款人">{{ receipt.payer || "-" }}</td>
          <td data-label="金额">{{ formatGBP(receipt.total) }}</td>
          <td data-label="状态">{{ receipt.status === 'confirmed' ? '已确认' : receipt.status === 'ready' ? '待确认' : receipt.status }}</td>
          <td data-label="创建时间">{{ formatDateTime(receipt.created_at) }}</td>
          <td data-label="操作" class="receipt-action">
            <RouterLink class="button ghost" :to="`/receipts/${receipt.id}`">{{ isOwner(receipt) ? '编辑' : '查看' }}</RouterLink>
            <button v-if="isOwner(receipt)" class="button danger" @click="remove(receipt)">删除</button>
          </td>
        </tr>
      </tbody>
    </table>
    <div v-else-if="receipts.length" class="empty-state">
      <Search :size="48" class="empty-state__icon" />
      <div class="empty-state__title">无匹配结果</div>
      <div class="empty-state__text">尝试调整筛选条件</div>
      <button class="button ghost" style="margin-top: 12px;" @click="clearFilters">清除筛选</button>
    </div>
    <div v-else class="empty-state">
      <FileText :size="48" class="empty-state__icon" />
      <div class="empty-state__title">暂无账单</div>
      <div class="empty-state__text">上传收据照片即可开始记账</div>
      <RouterLink class="button" to="/upload" style="margin-top: 16px; display: inline-flex; align-items: center; gap: 6px;">
        <Upload :size="16" />
        去上传
      </RouterLink>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { RouterLink, useRouter } from "vue-router";
import { FileText, PenLine, Search, Upload, X } from "lucide-vue-next";
import { createReceipt, deleteReceipt, listReceipts } from "../api/receipts";
import { useAuthStore } from "../stores/auth";

const router = useRouter();
const authStore = useAuthStore();
const receipts = ref<any[]>([]);
const creating = ref(false);

// Filters
const filterMerchant = ref("");
const filterPayer = ref("");
const filterDateFrom = ref("");
const filterDateTo = ref("");

const merchantOptions = computed(() => {
  const set = new Set<string>();
  receipts.value.forEach(r => { if (r.merchant) set.add(r.merchant); });
  return [...set].sort();
});

const payerOptions = computed(() => {
  const set = new Set<string>();
  receipts.value.forEach(r => { if (r.payer) set.add(r.payer); });
  return [...set].sort();
});

const hasActiveFilter = computed(() =>
  !!(filterMerchant.value || filterPayer.value || filterDateFrom.value || filterDateTo.value)
);

const filteredReceipts = computed(() => {
  let list = receipts.value;
  if (filterMerchant.value) {
    list = list.filter(r => r.merchant === filterMerchant.value);
  }
  if (filterPayer.value) {
    list = list.filter(r => r.payer === filterPayer.value);
  }
  if (filterDateFrom.value) {
    const from = new Date(filterDateFrom.value);
    list = list.filter(r => {
      if (!r.purchased_at) return false;
      return new Date(r.purchased_at) >= from;
    });
  }
  if (filterDateTo.value) {
    const to = new Date(filterDateTo.value + "T23:59:59");
    list = list.filter(r => {
      if (!r.purchased_at) return false;
      return new Date(r.purchased_at) <= to;
    });
  }
  return list;
});

const clearFilters = () => {
  filterMerchant.value = "";
  filterPayer.value = "";
  filterDateFrom.value = "";
  filterDateTo.value = "";
};

const isOwner = (receipt: any) => receipt.user_id === authStore.user?.id;

const createManual = async () => {
  creating.value = true;
  try {
    const receipt = await createReceipt();
    router.push(`/receipts/${receipt.id}`);
  } catch (e) {
    alert("创建失败，请重试");
  } finally {
    creating.value = false;
  }
};

const formatGBP = (value: number | string | null) => {
  const num = Number(value || 0);
  return new Intl.NumberFormat("en-GB", { style: "currency", currency: "GBP" }).format(num);
};

const formatDate = (value: string | null) => {
  if (!value) return "-";
  const d = new Date(value);
  if (isNaN(d.getTime())) return value;
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, "0");
  const day = String(d.getDate()).padStart(2, "0");
  return `${y}/${m}/${day}`;
};

const formatDateTime = (value: string | null) => {
  if (!value) return "-";
  const d = new Date(value);
  if (isNaN(d.getTime())) return value;
  const pad = (n: number) => String(n).padStart(2, "0");
  return `${d.getFullYear()}/${pad(d.getMonth() + 1)}/${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`;
};

const remove = async (receipt: any) => {
  if (!window.confirm("确定删除此账单？此操作不可撤销。")) return;
  await deleteReceipt(receipt.id);
  receipts.value = receipts.value.filter((r: any) => r.id !== receipt.id);
};

onMounted(async () => {
  try {
    receipts.value = await listReceipts();
  } catch (err: any) {
    if (err?.response?.status === 401) return;
    console.error("Failed to load receipts:", err);
  }
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

/* ── Filter Bar ── */

.filter-bar {
  margin-bottom: 16px;
}

.filter-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
}

.filter-field {
  display: flex;
  flex-direction: column;
  gap: 4px;
  min-width: 0;
}

.filter-field label {
  font-size: 11px;
  font-weight: 600;
  color: var(--muted, #8e8e93);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.filter-field .input {
  font-size: 13px;
  padding: 7px 10px;
  min-height: 36px;
}

.filter-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: 10px;
}

.filter-footer .button {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 13px;
  padding: 6px 12px;
  min-height: 34px;
  white-space: nowrap;
}

.filter-summary {
  font-size: 12px;
  color: var(--muted, #8e8e93);
}

/* ── Empty State ── */

.empty-state {
  text-align: center;
  padding: 48px 0;
  animation: fadeIn 0.4s ease;
}

.empty-state__icon {
  color: var(--muted);
  margin-bottom: 14px;
}

.empty-state__title {
  font-size: 17px;
  font-weight: 600;
  margin-bottom: 6px;
}

.empty-state__text {
  color: var(--muted);
  font-size: 14px;
}

/* ── Actions ── */

.receipt-action {
  display: flex;
  gap: 8px;
  align-items: center;
}

.receipt-action .button {
  padding: 6px 14px;
  font-size: 13px;
}

/* ── Mobile ── */

@media (max-width: 640px) {
  .filter-grid {
    grid-template-columns: 1fr 1fr;
    gap: 10px;
  }

  .table thead {
    display: none;
  }

  .receipt-row {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    padding: 14px 0;
    border-bottom: 1px solid var(--border);
  }

  .receipt-row td {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 0;
    border-bottom: none;
  }

  .receipt-row td::before {
    content: attr(data-label);
    font-size: 11px;
    font-weight: 600;
    color: var(--muted);
  }

  .receipt-action {
    width: 100%;
    margin-top: 4px;
    display: flex;
    gap: 8px;
  }

  .receipt-action::before {
    display: none;
  }

  .receipt-action .button {
    flex: 1;
    text-align: center;
  }
}
</style>
