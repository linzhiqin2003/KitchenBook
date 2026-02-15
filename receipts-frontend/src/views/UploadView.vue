<template>
  <!-- ─── 上传区域：解析完成后隐藏 ─── -->
  <div v-if="!receipt" class="panel upload-panel">
    <h2>上传收据照片</h2>
    <p class="desc">上传后将自动调用视觉大模型解析，并生成可编辑账单。支持多张图片（最多 5 张）。</p>

    <div
      class="drop-zone"
      :class="{ 'drop-zone--active': isDragging, 'drop-zone--has-file': files.length > 0 }"
      @dragenter.prevent="isDragging = true"
      @dragover.prevent="isDragging = true"
      @dragleave.prevent="isDragging = false"
      @drop.prevent="onDrop"
      @click="triggerFileInput"
    >
      <input
        ref="fileInput"
        type="file"
        accept="image/*"
        multiple
        style="display: none"
        @change="onFileChange"
      />

      <template v-if="files.length === 0">
        <ImagePlus :size="44" class="drop-zone__icon" />
        <div class="drop-zone__title">拖拽图片到此处，或点击选择文件</div>
        <div class="drop-zone__subtitle">支持 JPG / PNG / HEIC 格式，最多 5 张</div>
      </template>

      <template v-else>
        <div class="thumbs-grid" @click.stop>
          <div v-for="(p, idx) in previews" :key="idx" class="thumb-item">
            <img :src="p" alt="preview" class="thumb-img" />
            <span class="thumb-index">{{ idx + 1 }}</span>
            <button class="thumb-remove" @click.stop="removeFile(idx)">
              <X :size="14" />
            </button>
          </div>
          <div v-if="files.length < 5" class="thumb-add" @click.stop="triggerFileInput">
            <Plus :size="24" />
          </div>
        </div>
        <div class="thumbs-summary">
          {{ files.length }} 张图片，共 {{ formatSize(totalSize) }}
          <button class="button ghost" style="margin-left: 12px; padding: 4px 10px; font-size: 12px;" @click.stop="clearFiles">
            全部清除
          </button>
        </div>
      </template>
    </div>

    <div class="upload-actions">
      <button
        class="button"
        :class="{ 'button--loading': loading }"
        :disabled="files.length === 0 || loading"
        @click="submit"
      >
        <Loader2 v-if="loading" :size="16" class="spinner-icon" />
        {{ loading ? phaseLabel : "开始解析" }}
      </button>
    </div>

    <div v-if="error" class="alert error" style="margin-top: 16px;">
      {{ error }}
    </div>
  </div>

  <!-- ─── 解析结果：内联展示 ─── -->
  <template v-if="receipt">
    <!-- 原始图片 -->
    <div v-if="imageUrls.length" class="panel image-panel" style="margin-bottom: 20px;">
      <div class="image-header">
        <h2>原始收据</h2>
        <button class="button ghost" @click="showImage = !showImage">
          <component :is="showImage ? ChevronUp : ChevronDown" :size="16" />
          {{ showImage ? '收起' : '查看图片' }}
        </button>
      </div>
      <div v-if="showImage" class="image-gallery">
        <img
          v-for="(url, idx) in imageUrls"
          :key="idx"
          :src="url"
          alt="收据原始图片"
          class="receipt-image"
          @click="lightboxIndex = idx"
        />
      </div>
      <Teleport to="body">
        <div v-if="lightboxIndex !== null" class="lightbox" @click="lightboxIndex = null">
          <button v-if="imageUrls.length > 1" class="lightbox-nav lightbox-prev" @click.stop="lightboxPrev">
            <ChevronLeft :size="28" />
          </button>
          <img :src="imageUrls[lightboxIndex]" alt="收据原始图片" class="lightbox-img" @click.stop />
          <button v-if="imageUrls.length > 1" class="lightbox-nav lightbox-next" @click.stop="lightboxNext">
            <ChevronRight :size="28" />
          </button>
          <div v-if="imageUrls.length > 1" class="lightbox-counter">{{ lightboxIndex + 1 }} / {{ imageUrls.length }}</div>
          <button class="lightbox-close" @click.stop="lightboxIndex = null">
            <X :size="24" />
          </button>
        </div>
      </Teleport>
    </div>

    <!-- 基本信息 -->
    <div class="panel" style="margin-bottom: 20px;">
      <div class="result-header">
        <CheckCircle2 :size="20" class="result-header__icon" />
        <h2 style="margin: 0;">解析结果</h2>
      </div>
      <div class="form-grid">
        <div class="form-field">
          <label>商店</label>
          <input class="input" v-model="receipt.merchant" />
        </div>
        <div class="form-field">
          <label>地址</label>
          <input class="input" v-model="receipt.address" />
        </div>
        <div class="form-field">
          <label>日期时间</label>
          <input class="input" type="datetime-local" v-model="localDatetime" />
        </div>
        <div class="form-field">
          <label>币种</label>
          <input class="input" v-model="receipt.currency" />
        </div>
        <div class="form-field">
          <label>小计</label>
          <input class="input" v-model="receipt.subtotal" />
        </div>
        <div class="form-field">
          <label>税费</label>
          <input class="input" v-model="receipt.tax" />
        </div>
        <div class="form-field">
          <label>折扣</label>
          <input class="input" v-model="receipt.discount" />
        </div>
        <div class="form-field">
          <label>总计</label>
          <input class="input" v-model="receipt.total" />
        </div>
        <div class="form-field">
          <label>付款人</label>
          <input class="input" v-model="receipt.payer" />
        </div>
        <div class="form-field">
          <label>备注</label>
          <textarea class="textarea" v-model="receipt.notes" rows="2"></textarea>
        </div>
      </div>
      <div v-if="message" class="alert success" style="margin-top: 12px;">{{ message }}</div>
    </div>

    <!-- 商品明细 -->
    <ReceiptItemTable
      :items="items"
      :show-discard="true"
      :show-confirm="true"
      :orgs="orgStore.orgs"
      :currentOrgId="authStore.activeOrgId"
      :showOrgSelector="orgStore.orgs.length > 0"
      @update:items="items = $event"
      @save="save"
      @confirm="confirmAndReset"
      @discard="resetPage(true)"
    />
  </template>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { ChevronDown, ChevronLeft, ChevronRight, ChevronUp, X, Plus, ImagePlus, Loader2, CheckCircle2 } from "lucide-vue-next";
import { uploadReceiptStream, updateReceipt, confirmReceipt, confirmReceiptWithSplit, deleteReceipt } from "../api/receipts";
import ReceiptItemTable from "../components/ReceiptItemTable.vue";
import { useAuthStore } from "../stores/auth";
import { useOrgStore } from "../stores/org";

const authStore = useAuthStore();
const orgStore = useOrgStore();

const MAX_FILES = 5;
const MEDIA_BASE = (import.meta.env.VITE_MEDIA_BASE || "/media").replace(/\/$/, "");

const fileInput = ref<HTMLInputElement | null>(null);
const files = ref<File[]>([]);
const previews = ref<string[]>([]);
const loading = ref(false);
const phase = ref<"uploading" | "thinking" | "generating">("uploading");
const error = ref<string | null>(null);
const receipt = ref<any>(null);
const items = ref<any[]>([]);
const isDragging = ref(false);
const message = ref<string | null>(null);
const showImage = ref(false);
const lightboxIndex = ref<number | null>(null);

const totalSize = computed(() => files.value.reduce((sum, f) => sum + f.size, 0));

const resolveImageUrl = (img: string) => {
  if (!img) return "";
  if (img.startsWith("http")) return img;
  return MEDIA_BASE + (img.startsWith("/") ? img : "/" + img);
};

const imageUrls = computed(() => {
  if (!receipt.value) return [];
  // Prefer images[] (ReceiptImage records)
  const imgs = receipt.value.images;
  if (imgs && imgs.length > 0) {
    return imgs.map((ri: any) => resolveImageUrl(ri.image));
  }
  // Fallback to legacy image field
  if (receipt.value.image) {
    return [resolveImageUrl(receipt.value.image)];
  }
  return [];
});

const lightboxPrev = () => {
  if (lightboxIndex.value !== null && lightboxIndex.value > 0) {
    lightboxIndex.value--;
  } else if (lightboxIndex.value === 0) {
    lightboxIndex.value = imageUrls.value.length - 1;
  }
};

const lightboxNext = () => {
  if (lightboxIndex.value !== null && lightboxIndex.value < imageUrls.value.length - 1) {
    lightboxIndex.value++;
  } else if (lightboxIndex.value === imageUrls.value.length - 1) {
    lightboxIndex.value = 0;
  }
};

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

const triggerFileInput = () => {
  fileInput.value?.click();
};

const addFiles = (newFiles: File[]) => {
  const remaining = MAX_FILES - files.value.length;
  const toAdd = newFiles.slice(0, remaining);
  for (const f of toAdd) {
    files.value.push(f);
    previews.value.push(URL.createObjectURL(f));
  }
  error.value = null;
};

const removeFile = (idx: number) => {
  URL.revokeObjectURL(previews.value[idx]);
  files.value.splice(idx, 1);
  previews.value.splice(idx, 1);
};

const onFileChange = (event: Event) => {
  const target = event.target as HTMLInputElement;
  if (!target.files?.length) return;
  addFiles(Array.from(target.files));
  // Reset input so the same file can be re-selected
  target.value = "";
};

const onDrop = (event: DragEvent) => {
  isDragging.value = false;
  const droppedFiles = event.dataTransfer?.files;
  if (droppedFiles?.length) {
    addFiles(Array.from(droppedFiles));
  }
};

const clearFiles = () => {
  previews.value.forEach(p => URL.revokeObjectURL(p));
  files.value = [];
  previews.value = [];
  if (fileInput.value) fileInput.value.value = "";
};

const formatSize = (bytes: number) => {
  if (bytes < 1024) return bytes + " B";
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + " KB";
  return (bytes / (1024 * 1024)).toFixed(1) + " MB";
};

const resetPage = async (shouldDelete = false) => {
  if (shouldDelete && receipt.value?.id) {
    try {
      await deleteReceipt(receipt.value.id);
    } catch (e) {
      console.error("删除收据失败:", e);
    }
  }
  receipt.value = null;
  items.value = [];
  message.value = null;
  clearFiles();
  showImage.value = false;
  lightboxIndex.value = null;
};

const phaseLabel = computed(() => {
  switch (phase.value) {
    case "uploading": return "上传中...";
    case "thinking": return "模型思考中...";
    case "generating": return "生成结果中...";
    default: return "解析中...";
  }
});

const submit = async () => {
  if (files.value.length === 0) return;
  loading.value = true;
  phase.value = "uploading";
  error.value = null;
  receipt.value = null;
  try {
    const data = await uploadReceiptStream(
      files.value.length === 1 ? files.value[0] : files.value,
      authStore.displayName || "",
      (p) => { phase.value = p as any; },
    );
    receipt.value = data;
    items.value = data.items || [];
    message.value = null;
  } catch (err: any) {
    if (err?.message?.includes("timeout")) {
      error.value = "请求超时，图片可能已上传成功，请到账单列表查看";
    } else {
      error.value = err?.message || "解析失败，请稍后重试";
    }
  } finally {
    loading.value = false;
  }
};

const save = async (itemsData?: any[]) => {
  if (!receipt.value) return;
  message.value = null;
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
  const data = await updateReceipt(receipt.value.id, payload);
  receipt.value = data;
  items.value = data.items || [];
  message.value = "已保存。";
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

const confirmAndReset = async (itemsData?: any[]) => {
  if (!receipt.value) return;
  const itemsList = itemsData || items.value;
  await save(itemsList);

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

  message.value = null;
  resetPage();
};

onMounted(async () => {
  if (authStore.isLoggedIn) {
    try { await orgStore.fetchOrgs(); } catch { /* ignore */ }
  }
});

</script>

<style scoped>
.upload-panel {
  max-width: 100%;
}

.desc {
  color: var(--muted);
  font-size: 14px;
  margin: 0 0 20px;
}

.drop-zone {
  border: 2px dashed rgba(0, 122, 255, 0.2);
  border-radius: var(--radius-lg);
  padding: 48px 24px;
  text-align: center;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.25, 0.46, 0.45, 0.94);
  background: rgba(0, 122, 255, 0.02);
}

.drop-zone:hover {
  border-color: rgba(0, 122, 255, 0.35);
  background: rgba(0, 122, 255, 0.04);
}

.drop-zone--active {
  border-color: var(--accent);
  background: rgba(0, 122, 255, 0.06);
  transform: scale(1.01);
}

.drop-zone--has-file {
  padding: 20px;
  border-style: solid;
  border-color: rgba(0, 122, 255, 0.15);
  cursor: default;
}

.drop-zone__icon {
  color: var(--muted);
  margin-bottom: 12px;
}

.drop-zone__title {
  font-size: 15px;
  font-weight: 600;
  color: var(--text);
}

.drop-zone__subtitle {
  font-size: 13px;
  color: var(--muted);
  margin-top: 6px;
}

/* ─── Thumbnails grid ─── */
.thumbs-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  justify-content: center;
}

.thumb-item {
  position: relative;
  width: 100px;
  height: 100px;
  border-radius: var(--radius);
  overflow: hidden;
  box-shadow: var(--shadow-sm);
}

.thumb-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.thumb-index {
  position: absolute;
  top: 4px;
  left: 4px;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: rgba(0, 0, 0, 0.55);
  color: #fff;
  font-size: 11px;
  font-weight: 600;
  display: flex;
  align-items: center;
  justify-content: center;
}

.thumb-remove {
  position: absolute;
  top: 4px;
  right: 4px;
  width: 22px;
  height: 22px;
  border-radius: 50%;
  border: none;
  background: rgba(255, 59, 48, 0.85);
  color: #fff;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0;
  transition: opacity 0.15s ease;
}

.thumb-item:hover .thumb-remove {
  opacity: 1;
}

.thumb-add {
  width: 100px;
  height: 100px;
  border-radius: var(--radius);
  border: 2px dashed rgba(0, 122, 255, 0.25);
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--muted);
  cursor: pointer;
  transition: border-color 0.2s, color 0.2s;
}

.thumb-add:hover {
  border-color: var(--accent);
  color: var(--accent);
}

.thumbs-summary {
  margin-top: 12px;
  font-size: 13px;
  color: var(--muted);
  display: flex;
  align-items: center;
  justify-content: center;
}

.upload-actions {
  margin-top: 20px;
  display: flex;
  justify-content: center;
}

.button--loading {
  display: inline-flex;
  align-items: center;
  gap: 8px;
}

.spinner-icon {
  animation: spin 0.8s linear infinite;
}

/* ─── 解析结果区域 ─── */

.result-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 18px;
}

.result-header__icon {
  color: var(--success);
  flex-shrink: 0;
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

.action-bar {
  margin-top: 20px;
  display: flex;
  gap: 12px;
}

/* Image gallery */
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

.image-gallery {
  margin-top: 14px;
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  justify-content: center;
}

.receipt-image {
  max-width: 100%;
  max-height: 300px;
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
  max-width: 85vw;
  max-height: 85vh;
  object-fit: contain;
  border-radius: 8px;
  cursor: default;
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

.lightbox-nav {
  position: absolute;
  top: 50%;
  transform: translateY(-50%);
  width: 48px;
  height: 48px;
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

.lightbox-nav:hover {
  background: rgba(255, 255, 255, 0.3);
}

.lightbox-prev {
  left: 20px;
}

.lightbox-next {
  right: 20px;
}

.lightbox-counter {
  position: absolute;
  bottom: 24px;
  left: 50%;
  transform: translateX(-50%);
  color: rgba(255, 255, 255, 0.8);
  font-size: 14px;
  font-weight: 500;
  background: rgba(0, 0, 0, 0.4);
  padding: 4px 14px;
  border-radius: 20px;
}

@media (max-width: 640px) {
  .drop-zone {
    padding: 28px 16px;
  }

  .thumb-item {
    width: 80px;
    height: 80px;
  }

  .thumb-add {
    width: 80px;
    height: 80px;
  }

  .thumb-remove {
    opacity: 1;
  }

  .action-bar {
    flex-wrap: wrap;
  }

  .action-bar .button {
    flex: 1;
    text-align: center;
  }

  .receipt-image {
    max-height: 220px;
  }
}
</style>
