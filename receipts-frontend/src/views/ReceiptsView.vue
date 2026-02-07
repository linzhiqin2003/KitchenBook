<template>
  <div class="panel">
    <div class="panel-header">
      <h2>账单列表</h2>
      <div class="panel-header__actions">
        <button class="button accent" @click="openAiChat" :disabled="aiLoading">
          <Sparkles :size="16" />
          AI 智能记账
        </button>
        <button class="button" @click="createManual" :disabled="creating">
          <PenLine :size="16" />
          {{ creating ? '创建中...' : '手动记账' }}
        </button>
      </div>
    </div>

    <!-- AI 对话记账 -->
    <div v-if="showAiChat" class="ai-chat-panel">
      <div class="ai-chat-header">
        <Sparkles :size="16" class="ai-chat-icon" />
        <span>AI 智能记账</span>
        <button class="ai-close-btn" @click="closeAiChat"><X :size="16" /></button>
      </div>
      <div class="ai-chat-messages">
        <div
          v-for="(msg, i) in aiMessages"
          :key="i"
          :class="['ai-msg', msg.role === 'user' ? 'ai-msg--user' : 'ai-msg--bot']"
        >
          <div class="ai-msg-bubble">{{ msg.content }}</div>
        </div>
        <div v-if="aiLoading" class="ai-msg ai-msg--bot">
          <div class="ai-msg-bubble ai-msg-typing">
            <Loader2 :size="14" class="spin" />
            思考中...
          </div>
        </div>
      </div>
      <div class="ai-chat-input">
        <textarea
          v-model="aiInput"
          class="input ai-chat-textarea"
          rows="1"
          placeholder="输入消息..."
          :disabled="aiLoading"
          @keydown="handleAiKeydown"
        />
        <button
          class="button accent ai-send-btn"
          @click="sendAiMessage"
          :disabled="aiLoading || !aiInput.trim()"
        >
          <Send :size="16" />
        </button>
      </div>
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
          <th class="sortable" @click="toggleSort('purchased_at')">
            购买日期
            <ArrowUpDown v-if="sortField !== 'purchased_at'" :size="13" class="sort-icon idle" />
            <ArrowUp v-else-if="sortDir === 'asc'" :size="13" class="sort-icon" />
            <ArrowDown v-else :size="13" class="sort-icon" />
          </th>
          <th>商店</th>
          <th>付款人</th>
          <th>金额</th>
          <th>状态</th>
          <th class="sortable" @click="toggleSort('created_at')">
            创建时间
            <ArrowUpDown v-if="sortField !== 'created_at'" :size="13" class="sort-icon idle" />
            <ArrowUp v-else-if="sortDir === 'asc'" :size="13" class="sort-icon" />
            <ArrowDown v-else :size="13" class="sort-icon" />
          </th>
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
import { ArrowDown, ArrowUp, ArrowUpDown, FileText, Loader2, PenLine, Search, Send, Sparkles, Upload, X } from "lucide-vue-next";
import { aiGenerate, createReceipt, deleteReceipt, listReceipts } from "../api/receipts";
import type { AiChatMessage } from "../api/receipts";
import { useAuthStore } from "../stores/auth";

const router = useRouter();
const authStore = useAuthStore();
const receipts = ref<any[]>([]);
const creating = ref(false);

// AI chat
const showAiChat = ref(false);
const aiMessages = ref<AiChatMessage[]>([]);
const aiInput = ref("");
const aiLoading = ref(false);

const openAiChat = () => {
  showAiChat.value = true;
  if (!aiMessages.value.length) {
    aiMessages.value = [{ role: "assistant", content: "你好！请描述你的购物经历，我来帮你生成账单。\n\n例如：昨天在 Tesco 买了牛奶 3.5 磅、面包 1.2 磅" }];
  }
};

const closeAiChat = () => {
  showAiChat.value = false;
};

const resetAiChat = () => {
  aiMessages.value = [];
  aiInput.value = "";
  showAiChat.value = false;
};

const sendAiMessage = async () => {
  const text = aiInput.value.trim();
  if (!text || aiLoading.value) return;

  aiMessages.value.push({ role: "user", content: text });
  aiInput.value = "";
  aiLoading.value = true;

  // Only send the actual conversation (skip the initial greeting)
  const apiMessages = aiMessages.value.filter((_, i) => i > 0);

  try {
    const res = await aiGenerate(apiMessages);
    if (res.type === "chat") {
      aiMessages.value.push({ role: "assistant", content: res.message });
    } else {
      resetAiChat();
      router.push(`/receipts/${res.receipt.id}`);
    }
  } catch (e: any) {
    aiMessages.value.push({
      role: "assistant",
      content: `抱歉，出了点问题：${e?.response?.data?.detail || e?.message || "请重试"}`,
    });
  } finally {
    aiLoading.value = false;
  }
};

const handleAiKeydown = (e: KeyboardEvent) => {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    sendAiMessage();
  }
};

// Filters
const filterMerchant = ref("");
const filterPayer = ref("");
const filterDateFrom = ref("");
const filterDateTo = ref("");

// Sort
const sortField = ref<"purchased_at" | "created_at" | "">("");
const sortDir = ref<"asc" | "desc">("desc");

function toggleSort(field: "purchased_at" | "created_at") {
  if (sortField.value === field) {
    if (sortDir.value === "desc") sortDir.value = "asc";
    else { sortField.value = ""; sortDir.value = "desc"; }
  } else {
    sortField.value = field;
    sortDir.value = "desc";
  }
}

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
  if (sortField.value) {
    const field = sortField.value;
    const dir = sortDir.value === "asc" ? 1 : -1;
    list = [...list].sort((a, b) => {
      const ta = new Date(a[field] || 0).getTime();
      const tb = new Date(b[field] || 0).getTime();
      return (ta - tb) * dir;
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

.panel-header__actions {
  display: flex;
  gap: 8px;
  align-items: center;
}

.panel-header .button {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.button.accent {
  background: var(--accent, #007aff);
  color: #fff;
  border-color: var(--accent, #007aff);
}

.button.accent:hover:not(:disabled) {
  opacity: 0.9;
}

.button.accent:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* ── AI Chat Panel ── */

.ai-chat-panel {
  margin-bottom: 16px;
  border: 1px solid var(--accent, #007aff);
  border-radius: 10px;
  background: var(--surface, #fff);
  overflow: hidden;
}

.ai-chat-header {
  display: flex;
  align-items: center;
  gap: 6px;
  font-weight: 600;
  font-size: 14px;
  padding: 12px 16px;
  border-bottom: 1px solid var(--border, #e5e5ea);
}

.ai-chat-icon {
  color: var(--accent, #007aff);
}

.ai-close-btn {
  margin-left: auto;
  background: none;
  border: none;
  cursor: pointer;
  color: var(--muted, #8e8e93);
  padding: 4px;
  border-radius: 6px;
}

.ai-close-btn:hover {
  background: var(--hover, rgba(0,0,0,0.05));
}

.ai-chat-messages {
  padding: 12px 16px;
  max-height: 320px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.ai-msg {
  display: flex;
}

.ai-msg--user {
  justify-content: flex-end;
}

.ai-msg--bot {
  justify-content: flex-start;
}

.ai-msg-bubble {
  max-width: 80%;
  padding: 8px 12px;
  border-radius: 12px;
  font-size: 14px;
  line-height: 1.5;
  white-space: pre-wrap;
  word-break: break-word;
}

.ai-msg--user .ai-msg-bubble {
  background: var(--accent, #007aff);
  color: #fff;
  border-bottom-right-radius: 4px;
}

.ai-msg--bot .ai-msg-bubble {
  background: var(--bg-secondary, #f2f2f7);
  color: var(--text, #1c1c1e);
  border-bottom-left-radius: 4px;
}

.ai-msg-typing {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  color: var(--muted, #8e8e93);
  font-size: 13px;
}

.ai-chat-input {
  display: flex;
  align-items: flex-end;
  gap: 8px;
  padding: 10px 16px;
  border-top: 1px solid var(--border, #e5e5ea);
}

.ai-chat-textarea {
  flex: 1;
  resize: none;
  font-size: 14px;
  min-height: 36px;
  max-height: 80px;
  box-sizing: border-box;
  padding: 8px 10px;
}

.ai-send-btn {
  padding: 8px 12px;
  flex-shrink: 0;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.spin {
  animation: spin 1s linear infinite;
}

/* ── Filter Bar ── */

.filter-bar {
  margin-bottom: 16px;
}

.filter-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
  max-width: 100%;
  overflow: hidden;
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
  max-width: 100%;
  box-sizing: border-box;
  width: 100%;
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

/* ── Sortable Headers ── */

.sortable {
  cursor: pointer;
  user-select: none;
  white-space: nowrap;
}

.sortable:hover {
  color: var(--accent, #007aff);
}

.sort-icon {
  vertical-align: middle;
  margin-left: 2px;
}

.sort-icon.idle {
  opacity: 0.3;
}

.sortable:hover .sort-icon.idle {
  opacity: 0.6;
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

  /* 日期输入框各占一整行，避免 iOS 原生控件溢出 */
  .filter-field:nth-child(3),
  .filter-field:nth-child(4) {
    grid-column: 1 / -1;
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
