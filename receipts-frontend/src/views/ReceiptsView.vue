<template>
  <div class="panel">
    <div class="panel-header">
      <h2>账单列表</h2>
      <button class="button" @click="createManual" :disabled="creating">
        <PenLine :size="16" />
        {{ creating ? '创建中...' : '手动记账' }}
      </button>
    </div>
    <table v-if="receipts.length" class="table">
      <thead>
        <tr>
          <th>日期</th>
          <th>商店</th>
          <th>付款人</th>
          <th>金额</th>
          <th>状态</th>
          <th>操作</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="receipt in receipts" :key="receipt.id" class="receipt-row">
          <td data-label="日期">{{ formatDate(receipt.purchased_at) }}</td>
          <td data-label="商店">{{ receipt.merchant || "-" }}</td>
          <td data-label="付款人">{{ receipt.payer || "-" }}</td>
          <td data-label="金额">{{ formatGBP(receipt.total) }}</td>
          <td data-label="状态">{{ receipt.status === 'confirmed' ? '已确认' : receipt.status === 'ready' ? '待确认' : receipt.status }}</td>
          <td data-label="操作" class="receipt-action">
            <RouterLink class="button ghost" :to="`/receipts/${receipt.id}`">{{ isOwner(receipt) ? '编辑' : '查看' }}</RouterLink>
            <button v-if="isOwner(receipt)" class="button danger" @click="remove(receipt)">删除</button>
          </td>
        </tr>
      </tbody>
    </table>
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
import { onMounted, ref } from "vue";
import { RouterLink, useRouter } from "vue-router";
import { FileText, PenLine, Upload } from "lucide-vue-next";
import { createReceipt, deleteReceipt, listReceipts } from "../api/receipts";
import { useAuthStore } from "../stores/auth";

const router = useRouter();
const authStore = useAuthStore();
const receipts = ref<any[]>([]);
const creating = ref(false);

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

.receipt-action {
  display: flex;
  gap: 8px;
  align-items: center;
}

.receipt-action .button {
  padding: 6px 14px;
  font-size: 13px;
}

@media (max-width: 640px) {
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
