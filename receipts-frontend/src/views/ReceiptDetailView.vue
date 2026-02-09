<template>
  <div class="detail-nav">
    <button class="button ghost" @click="discard">
      <ArrowLeft :size="16" />
      返回列表
    </button>
  </div>

  <div v-if="receipt && receipt.image" class="panel image-panel" style="margin-bottom: 20px;">
    <div class="image-header">
      <h2>原始收据</h2>
      <button class="button ghost" @click="showImage = !showImage">
        <component :is="showImage ? ChevronUp : ChevronDown" :size="16" />
        {{ showImage ? '收起' : '查看图片' }}
      </button>
    </div>
    <div v-if="showImage" class="image-viewer">
      <img :src="imageUrl" alt="收据原始图片" class="receipt-image" @click="fullscreen = true" />
    </div>
    <Teleport to="body">
      <div v-if="fullscreen" class="lightbox" @click="fullscreen = false">
        <img :src="imageUrl" alt="收据原始图片" class="lightbox-img" />
        <button class="lightbox-close" @click.stop="fullscreen = false">
          <X :size="24" />
        </button>
      </div>
    </Teleport>
  </div>

  <div v-if="receipt" class="panel" style="margin-bottom: 20px;">
    <div class="detail-title-row">
      <h2>基本信息</h2>
      <span v-if="!isOwner" class="readonly-badge">只读 · 由 {{ receipt.uploader_name || '他人' }} 上传</span>
    </div>
    <div class="form-grid">
      <div class="form-field">
        <label>商店</label>
        <input class="input" v-model="receipt.merchant" :readonly="!isOwner" />
      </div>
      <div class="form-field">
        <label>地址</label>
        <input class="input" v-model="receipt.address" :readonly="!isOwner" />
      </div>
      <div class="form-field">
        <label>日期时间</label>
        <input class="input" type="datetime-local" v-model="localDatetime" :readonly="!isOwner" />
      </div>
      <div class="form-field">
        <label>币种</label>
        <input class="input" v-model="receipt.currency" :readonly="!isOwner" />
      </div>
      <div class="form-field">
        <label>小计</label>
        <input class="input" v-model="receipt.subtotal" :readonly="!isOwner" />
        <span v-if="convert(receipt.subtotal)" class="converted-hint">{{ convert(receipt.subtotal) }}</span>
      </div>
      <div class="form-field">
        <label>税费</label>
        <input class="input" v-model="receipt.tax" :readonly="!isOwner" />
        <span v-if="convert(receipt.tax)" class="converted-hint">{{ convert(receipt.tax) }}</span>
      </div>
      <div class="form-field">
        <label>折扣</label>
        <input class="input" v-model="receipt.discount" :readonly="!isOwner" />
        <span v-if="convert(receipt.discount)" class="converted-hint">{{ convert(receipt.discount) }}</span>
      </div>
      <div class="form-field">
        <label>总计</label>
        <input class="input" v-model="receipt.total" :readonly="!isOwner" />
        <span v-if="convert(receipt.total)" class="converted-hint">{{ convert(receipt.total) }}</span>
      </div>
      <div class="form-field">
        <label>付款人</label>
        <input class="input" v-model="receipt.payer" :readonly="!isOwner" />
      </div>
      <div class="form-field">
        <label>备注</label>
        <textarea class="textarea" v-model="receipt.notes" rows="2" :readonly="!isOwner"></textarea>
      </div>
    </div>
    <div v-if="message" class="alert" :class="message.startsWith('保存失败') ? 'error' : 'success'" style="margin-top: 12px;">{{ message }}</div>
  </div>

  <ReceiptItemTable
    v-if="receipt && isOwner"
    :items="items"
    :subtotal="parseFloat(receipt.subtotal) || 0"
    :tax="parseFloat(receipt.tax) || 0"
    :discount="parseFloat(receipt.discount) || 0"
    :showDiscard="true"
    :showConfirm="receipt.status === 'ready'"
    :hideActions="receipt.status === 'confirmed' && orgStore.orgs.length > 0"
    :orgs="orgStore.orgs"
    :currentOrgId="authStore.activeOrgId"
    :showOrgSelector="receipt.status !== 'confirmed' && orgStore.orgs.length > 0"
    @update:items="items = $event"
    @save="saveAndBack"
    @confirm="confirmAndBack"
    @discard="discard"
  />

  <!-- 已确认收据：商品账目归属面板（独立于上方可编辑表格） -->
  <div v-if="receipt && isOwner && receipt.status === 'confirmed' && orgStore.orgs.length" class="panel" style="margin-top: 20px;">
    <h2>商品账目归属</h2>
    <p class="move-hint">调整明细归属后点击「提交归属调整」，系统将自动在目标组织中生成对应收据，税费和折扣按比例分摊。</p>
    <div class="item-table-wrapper">
      <table class="table">
        <thead>
          <tr>
            <th>商品</th>
            <th>总价</th>
            <th>目标空间</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(item, index) in items" :key="index" class="item-row">
            <td data-label="商品">{{ item.name || '-' }}</td>
            <td data-label="总价">{{ item.total_price ?? '-' }}</td>
            <td data-label="目标" class="move-cell">
              <select class="input move-select" v-model="moveTargets[index]">
                <option value="">个人</option>
                <option v-for="org in orgStore.orgs" :key="org.id" :value="org.id">{{ org.name }}</option>
              </select>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
    <div v-if="moveMessage" class="alert" :class="moveMessage.startsWith('失败') ? 'error' : 'success'" style="margin-top: 12px;">{{ moveMessage }}</div>
    <div class="move-bottom-actions">
      <button class="button ghost danger-text" @click="discard">退出不保存</button>
      <button class="button" @click="saveAndBack()">保存修改</button>
      <button
        v-if="hasOrgChanges"
        class="button secondary"
        @click="batchMoveItems"
      >
        提交归属调整
      </button>
    </div>
  </div>

  <!-- 非所有者：只读商品列表 -->
  <div v-if="receipt && !isOwner && items.length" class="panel">
    <h2>商品明细</h2>
    <div class="item-table-wrapper">
      <table class="table">
        <thead>
          <tr>
            <th>主类</th>
            <th>子类</th>
            <th>商品</th>
            <th>品牌</th>
            <th>数量</th>
            <th>单位</th>
            <th>单价</th>
            <th>总价</th>
            <th v-if="parseFloat(receipt.tax)">分摊税费</th>
            <th v-if="parseFloat(receipt.discount)">分摊折扣</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(item, index) in items" :key="index">
            <td data-label="主类">{{ item.main_category || '-' }}</td>
            <td data-label="子类">{{ item.sub_category || '-' }}</td>
            <td data-label="商品">{{ item.name || '-' }}</td>
            <td data-label="品牌">{{ item.brand || '-' }}</td>
            <td data-label="数量">{{ item.quantity }}</td>
            <td data-label="单位">{{ item.unit || '-' }}</td>
            <td data-label="单价">{{ item.unit_price ?? '-' }}</td>
            <td data-label="总价">{{ item.total_price ?? '-' }}</td>
            <td v-if="parseFloat(receipt.tax)" data-label="分摊税费" class="prorate-cell">{{ readonlyProrated[index]?.tax ?? '-' }}</td>
            <td v-if="parseFloat(receipt.discount)" data-label="分摊折扣" class="prorate-cell">{{ readonlyProrated[index]?.discount ?? '-' }}</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, onMounted, reactive, ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";
import { ArrowLeft, ChevronDown, ChevronUp, X } from "lucide-vue-next";
import { confirmReceipt, confirmReceiptWithSplit, deleteReceipt, getExchangeRate, getReceipt, moveReceiptItems, updateReceipt } from "../api/receipts";
import ReceiptItemTable from "../components/ReceiptItemTable.vue";
import { useAuthStore } from "../stores/auth";
import { useOrgStore } from "../stores/org";

const MEDIA_BASE = (import.meta.env.VITE_MEDIA_BASE || "/media").replace(/\/$/, "");

const route = useRoute();
const router = useRouter();
const authStore = useAuthStore();
const orgStore = useOrgStore();
const receipt = ref<any>(null);
const items = ref<any[]>([]);
const message = ref<string | null>(null);
const moveMessage = ref<string | null>(null);
const showImage = ref(false);
const fullscreen = ref(false);
const isEmptyOnLoad = ref(false);
const isOwner = computed(() => receipt.value?.user_id === authStore.user?.id);
const moveTargets = reactive<Record<number, string>>({});
const exchangeRate = ref<number | null>(null);
const currentOrgIdStr = computed(() => authStore.activeOrgId || "");

// baseline refs — 记录加载时的基准值，作为等比缩放参照
const baselineSubtotal = ref(0);
const baselineTax = ref(0);
const baselineDiscount = ref(0);
let programmaticUpdate = false;

const imageUrl = computed(() => {
  if (!receipt.value?.image) return "";
  const img = receipt.value.image;
  if (img.startsWith("http")) return img;
  return MEDIA_BASE + (img.startsWith("/") ? img : "/" + img);
});

// ISO string ↔ datetime-local format
const toLocalDatetime = (iso: string | null) => {
  if (!iso) return "";
  const d = new Date(iso);
  if (isNaN(d.getTime())) return "";
  const pad = (n: number) => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`;
};

const localDatetime = computed({
  get: () => toLocalDatetime(receipt.value?.purchased_at),
  set: (val: string) => {
    if (!receipt.value) return;
    receipt.value.purchased_at = val ? new Date(val).toISOString() : null;
  }
});

const recalcReady = ref(false);

const load = async () => {
  try {
    recalcReady.value = false;
    const data = await getReceipt(route.params.id as string);
    receipt.value = data;
    items.value = data.items || [];
    // 初始化 baseline
    baselineSubtotal.value = parseFloat(data.subtotal) || 0;
    baselineTax.value = parseFloat(data.tax) || 0;
    baselineDiscount.value = parseFloat(data.discount) || 0;
    // 判断加载时是否为空记录（手动新建且从未保存过有效数据）
    const loadedItems = data.items || [];
    isEmptyOnLoad.value = !data.merchant && !data.address && !data.purchased_at
      && !data.total && !data.notes && loadedItems.length === 0;
    await nextTick();
    recalcReady.value = true;
  } catch (err) {
    console.error("加载收据失败:", err);
    recalcReady.value = true;
  }
};

// 从商品明细重新计算小计和总计，等比缩放 tax/discount
const recalcTotals = () => {
  if (!receipt.value) return;
  const newSubtotal = items.value.reduce((sum, item) => {
    return sum + (parseFloat(item.total_price) || 0);
  }, 0);
  receipt.value.subtotal = parseFloat(newSubtotal.toFixed(2));
  if (baselineSubtotal.value > 0) {
    const ratio = newSubtotal / baselineSubtotal.value;
    programmaticUpdate = true;
    receipt.value.tax = parseFloat((baselineTax.value * ratio).toFixed(2));
    receipt.value.discount = parseFloat((baselineDiscount.value * ratio).toFixed(2));
    programmaticUpdate = false;
  }
  recalcTotal();
};

// 仅重算总计 = 小计 + 税费 - 折扣
const recalcTotal = () => {
  if (!receipt.value) return;
  const subtotal = parseFloat(receipt.value.subtotal) || 0;
  const tax = parseFloat(receipt.value.tax) || 0;
  const discount = parseFloat(receipt.value.discount) || 0;
  receipt.value.total = parseFloat((subtotal + tax - discount).toFixed(2));
};

// 商品明细变化时自动重算小计和总计
watch(items, () => {
  if (recalcReady.value) recalcTotals();
});

// 税费或折扣变化时：用户手动改则更新 baseline，然后重算总计
watch(
  () => [receipt.value?.tax, receipt.value?.discount],
  () => {
    if (!recalcReady.value) return;
    if (!programmaticUpdate) {
      baselineTax.value = parseFloat(receipt.value?.tax) || 0;
      baselineDiscount.value = parseFloat(receipt.value?.discount) || 0;
      baselineSubtotal.value = parseFloat(receipt.value?.subtotal) || 0;
    }
    recalcTotal();
  }
);

const saveAndBack = async (itemsData?: any[]) => {
  if (!receipt.value) return;
  message.value = null;
  try {
    const payload = {
      merchant: receipt.value.merchant,
      address: receipt.value.address,
      purchased_at: receipt.value.purchased_at,
      currency: receipt.value.currency,
      subtotal: receipt.value.subtotal,
      tax: receipt.value.tax,
      discount: receipt.value.discount,
      total: receipt.value.total,
      notes: receipt.value.notes,
      payer: receipt.value.payer,
      items: itemsData || items.value
    };
    await updateReceipt(receipt.value.id, payload);
    router.push("/receipts");
  } catch (err: any) {
    message.value = "保存失败：" + (err?.response?.data?.detail || err?.message || "请稍后重试");
  }
};

const discard = async () => {
  if (!receipt.value) return;
  if (isEmptyOnLoad.value) {
    // 原始记录就是空的（手动新建从未保存），直接删除
    try {
      await deleteReceipt(receipt.value.id);
    } catch { /* 忽略删除失败 */ }
  }
  // 有数据的记录：丢弃本次编辑，保留服务端已有数据
  router.push("/receipts");
};

const doConfirm = async (itemsList: any[], force = false) => {
  const currentOrg = authStore.activeOrgId || "";
  const hasOrgDiff = itemsList.some((it: any) => {
    const target = it.target_org_id ?? currentOrg;
    return target !== currentOrg;
  });

  if (hasOrgDiff) {
    const itemOrgs: Record<string, string> = {};
    itemsList.forEach((it: any, idx: number) => {
      itemOrgs[String(idx)] = it.target_org_id ?? currentOrg;
    });
    await confirmReceiptWithSplit(receipt.value.id, itemOrgs, force);
  } else {
    await confirmReceipt(receipt.value.id, force);
  }
};

const confirmAndBack = async (itemsData?: any[]) => {
  if (!receipt.value) return;
  message.value = null;
  try {
    const itemsList = itemsData || items.value;
    const payload = {
      merchant: receipt.value.merchant,
      address: receipt.value.address,
      purchased_at: receipt.value.purchased_at,
      currency: receipt.value.currency,
      subtotal: receipt.value.subtotal,
      tax: receipt.value.tax,
      discount: receipt.value.discount,
      total: receipt.value.total,
      notes: receipt.value.notes,
      payer: receipt.value.payer,
      items: itemsList,
    };
    await updateReceipt(receipt.value.id, payload);

    try {
      await doConfirm(itemsList);
    } catch (err: any) {
      if (err?.response?.status === 409) {
        const dup = err.response.data?.duplicate;
        const dupDate = dup?.date ? new Date(dup.date).toLocaleDateString() : "未知日期";
        const ok = window.confirm(
          `检测到重复收据：${dup?.merchant || "未知"} / ${dupDate} / ${dup?.total || "?"}\n是否仍要入库？`
        );
        if (ok) {
          await doConfirm(itemsList, true);
        } else {
          return;
        }
      } else {
        throw err;
      }
    }

    router.push("/receipts");
  } catch (err: any) {
    message.value = "操作失败：" + (err?.response?.data?.detail || err?.message || "请稍后重试");
  }
};

const syncMoveTargets = () => {
  const orgId = authStore.activeOrgId || "";
  items.value.forEach((_: any, idx: number) => {
    if (!(idx in moveTargets)) {
      moveTargets[idx] = orgId;
    }
  });
  // 清除多余的 key（删除行后）
  Object.keys(moveTargets).forEach((k) => {
    if (Number(k) >= items.value.length) {
      delete moveTargets[Number(k)];
    }
  });
};

// items 变化时（增删行）自动同步归属表
watch(items, syncMoveTargets, { deep: false });

// 是否有归属变动（任何 item 的目标 org 与当前 org 不同）
const hasOrgChanges = computed(() => {
  const cur = currentOrgIdStr.value;
  return items.value.some((_: any, idx: number) => (moveTargets[idx] ?? cur) !== cur);
});

const batchMoveItems = async () => {
  if (!receipt.value) return;
  moveMessage.value = null;
  const cur = currentOrgIdStr.value;
  const moves: Array<{ item_id: string | number; target_org_id: string }> = [];
  items.value.forEach((item: any, idx: number) => {
    const target = moveTargets[idx] ?? cur;
    if (target !== cur && item.id) {
      moves.push({ item_id: item.id, target_org_id: target });
    }
  });
  if (!moves.length) return;
  try {
    const result = await moveReceiptItems(receipt.value.id, moves);
    if (result.deleted) {
      router.push("/receipts");
      return;
    }
    // 清空旧的 index→org 映射，避免残留值污染重新加载后的列表
    Object.keys(moveTargets).forEach(k => delete moveTargets[Number(k)]);
    await load();
    syncMoveTargets();
    moveMessage.value = `已成功调整 ${moves.length} 条明细的归属`;
  } catch (err: any) {
    moveMessage.value = "失败：" + (err?.response?.data?.detail || err?.message || "请重试");
  }
};

// 只读表格的分摊计算
const readonlyProrated = computed(() => {
  const sub = parseFloat(receipt.value?.subtotal) || 0;
  const tax = parseFloat(receipt.value?.tax) || 0;
  const disc = parseFloat(receipt.value?.discount) || 0;
  if (sub <= 0) return items.value.map(() => ({ tax: '0.00', discount: '0.00' }));
  let taxRemain = tax;
  let discRemain = disc;
  return items.value.map((item, i) => {
    const price = parseFloat(item.total_price) || 0;
    if (i === items.value.length - 1) {
      return { tax: taxRemain.toFixed(2), discount: discRemain.toFixed(2) };
    }
    const t = parseFloat((tax * price / sub).toFixed(2));
    const d = parseFloat((disc * price / sub).toFixed(2));
    taxRemain -= t;
    discRemain -= d;
    return { tax: t.toFixed(2), discount: d.toFixed(2) };
  });
});

const convert = (value: string | number | null | undefined): string | null => {
  if (value == null || value === "" || exchangeRate.value == null) return null;
  const num = Number(value);
  if (isNaN(num) || num === 0) return null;
  const currency = receipt.value?.currency?.toUpperCase();
  if (currency === "GBP") {
    return `≈ ¥${(num * exchangeRate.value).toFixed(2)}`;
  } else if (currency === "CNY" || currency === "RMB") {
    return `≈ £${(num / exchangeRate.value).toFixed(2)}`;
  }
  return null;
};

onMounted(async () => {
  await load();
  syncMoveTargets();
  if (authStore.isLoggedIn) {
    try { await orgStore.fetchOrgs(); } catch { /* ignore */ }
  }
  // Non-blocking exchange rate fetch
  getExchangeRate()
    .then((res) => { exchangeRate.value = res.rate; })
    .catch(() => { /* silently ignore */ });
});
</script>

<style scoped>
.detail-title-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
}

.detail-title-row h2 {
  margin: 0;
}

.readonly-badge {
  font-size: 12px;
  font-weight: 500;
  color: var(--muted, #8e8e93);
  background: rgba(0, 0, 0, 0.04);
  padding: 4px 10px;
  border-radius: 20px;
}

.detail-nav {
  margin-bottom: 16px;
}

.detail-nav .button {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.form-field label {
  display: block;
  margin-bottom: 6px;
  color: var(--muted);
  font-size: 12px;
  text-transform: uppercase;
  letter-spacing: 0.8px;
  font-weight: 500;
}

.converted-hint {
  display: block;
  margin-top: 4px;
  font-size: 12px;
  color: var(--muted, #8e8e93);
}

.action-bar {
  margin-top: 20px;
  display: flex;
  gap: 12px;
}

@media (max-width: 640px) {
  .action-bar {
    flex-wrap: wrap;
  }

  .action-bar .button {
    flex: 1;
    text-align: center;
  }

  .detail-title-row {
    flex-wrap: wrap;
    gap: 8px;
  }

  .readonly-badge {
    font-size: 11px;
  }

  .receipt-image {
    max-height: 260px;
  }

  .image-header .button {
    padding: 6px 10px;
    font-size: 12px;
  }

  /* 只读表格卡片化 */
  .item-table-wrapper :deep(thead) {
    display: none;
  }

  .item-table-wrapper :deep(tbody tr) {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 4px 12px;
    padding: 12px 0;
    border-bottom: 1px solid var(--border, rgba(0,0,0,0.06));
  }

  .item-table-wrapper :deep(tbody tr td) {
    padding: 2px 0;
    border: none;
    font-size: 13px;
  }

  .item-table-wrapper :deep(tbody tr td::before) {
    content: attr(data-label);
    display: block;
    font-size: 10px;
    font-weight: 600;
    color: var(--muted, #8e8e93);
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }
}

.prorate-cell {
  color: var(--muted, #8e8e93);
  text-align: right;
  font-size: 13px;
}

/* Move cell */
.move-cell {
  min-width: 180px;
}

.move-row {
  display: flex;
  align-items: center;
  gap: 6px;
}

.move-select {
  flex: 1;
  min-width: 80px;
  font-size: 13px;
}

.move-hint {
  font-size: 13px;
  color: var(--muted, #8e8e93);
  margin: -4px 0 14px;
}

.move-bottom-actions {
  margin-top: 16px;
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

@media (max-width: 640px) {
  .move-bottom-actions {
    flex-direction: column;
  }
  .move-bottom-actions .button {
    width: 100%;
    text-align: center;
    justify-content: center;
  }
}

/* Image viewer */
.image-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.image-header h2 {
  margin: 0;
}

.image-header .button {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 6px 14px;
  font-size: 13px;
  min-height: auto;
}

.image-viewer {
  margin-top: 14px;
  text-align: center;
}

.receipt-image {
  max-width: 100%;
  max-height: 400px;
  object-fit: contain;
  border-radius: var(--radius);
  box-shadow: var(--shadow);
  cursor: zoom-in;
  transition: transform 0.2s ease;
}

.receipt-image:hover {
  transform: scale(1.01);
}

.lightbox {
  position: fixed;
  inset: 0;
  z-index: 1000;
  background: rgba(0, 0, 0, 0.85);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: zoom-out;
  animation: fadeIn 0.2s ease;
}

.lightbox-img {
  max-width: 90vw;
  max-height: 90vh;
  object-fit: contain;
  border-radius: 8px;
}

.lightbox-close {
  position: absolute;
  top: 20px;
  right: 20px;
  width: 44px;
  height: 44px;
  border: none;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.15);
  color: #fff;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background 0.2s ease;
}

.lightbox-close:hover {
  background: rgba(255, 255, 255, 0.3);
}

</style>
