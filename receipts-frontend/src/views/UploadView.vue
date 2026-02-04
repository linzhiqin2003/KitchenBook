<template>
  <!-- ─── 上传区域：解析完成后隐藏 ─── -->
  <div v-if="!receipt" class="panel upload-panel">
    <h2>上传收据照片</h2>
    <p class="desc">上传后将自动调用视觉大模型解析，并生成可编辑账单。</p>

    <div
      class="drop-zone"
      :class="{ 'drop-zone--active': isDragging, 'drop-zone--has-file': !!preview }"
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
        style="display: none"
        @change="onFileChange"
      />

      <template v-if="!preview">
        <ImagePlus :size="44" class="drop-zone__icon" />
        <div class="drop-zone__title">拖拽图片到此处，或点击选择文件</div>
        <div class="drop-zone__subtitle">支持 JPG / PNG / HEIC 格式</div>
      </template>

      <template v-else>
        <div class="preview-wrapper">
          <img :src="preview" alt="preview" class="preview-img" />
          <div class="preview-info">
            <div class="preview-name">{{ file?.name }}</div>
            <div class="preview-size">{{ formatSize(file?.size || 0) }}</div>
            <button class="button ghost" style="margin-top: 8px; padding: 6px 14px; font-size: 12px;" @click.stop="clearFile">
              重新选择
            </button>
          </div>
        </div>
      </template>
    </div>

    <div class="upload-actions">
      <button
        class="button"
        :class="{ 'button--loading': loading }"
        :disabled="!file || loading"
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
    <div v-if="receipt.image" class="panel image-panel" style="margin-bottom: 20px;">
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
    <ReceiptItemTable :items="items" :show-discard="true" :show-confirm="true" @update:items="items = $event" @save="save" @confirm="confirmAndReset" @discard="resetPage(true)" />
  </template>
</template>

<script setup lang="ts">
import { computed, ref } from "vue";
import { ChevronDown, ChevronUp, X, ImagePlus, Loader2, CheckCircle2 } from "lucide-vue-next";
import { uploadReceiptStream, updateReceipt, confirmReceipt, deleteReceipt } from "../api/receipts";
import ReceiptItemTable from "../components/ReceiptItemTable.vue";
import { useAuthStore } from "../stores/auth";

const authStore = useAuthStore();

const MEDIA_BASE = (import.meta.env.VITE_MEDIA_BASE || "/media").replace(/\/$/, "");

const fileInput = ref<HTMLInputElement | null>(null);
const file = ref<File | null>(null);
const preview = ref<string | null>(null);
const loading = ref(false);
const phase = ref<"uploading" | "thinking" | "generating">("uploading");
const error = ref<string | null>(null);
const receipt = ref<any>(null);
const items = ref<any[]>([]);
const isDragging = ref(false);
const message = ref<string | null>(null);
const showImage = ref(false);
const fullscreen = ref(false);

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

const triggerFileInput = () => {
  fileInput.value?.click();
};

const handleFile = (f: File) => {
  file.value = f;
  preview.value = URL.createObjectURL(f);
  error.value = null;
};

const onFileChange = (event: Event) => {
  const target = event.target as HTMLInputElement;
  if (!target.files?.length) return;
  handleFile(target.files[0]);
};

const onDrop = (event: DragEvent) => {
  isDragging.value = false;
  const files = event.dataTransfer?.files;
  if (files?.length) {
    handleFile(files[0]);
  }
};

const clearFile = () => {
  file.value = null;
  preview.value = null;
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
  file.value = null;
  preview.value = null;
  showImage.value = false;
  fullscreen.value = false;
  if (fileInput.value) fileInput.value.value = "";
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
  if (!file.value) return;
  loading.value = true;
  phase.value = "uploading";
  error.value = null;
  receipt.value = null;
  try {
    const data = await uploadReceiptStream(
      file.value,
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

const confirmAndReset = async (itemsData?: any[]) => {
  if (!receipt.value) return;
  await save(itemsData);
  await confirmReceipt(receipt.value.id);
  message.value = null;
  resetPage();
};

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

.preview-wrapper {
  display: flex;
  align-items: center;
  gap: 20px;
  text-align: left;
}

.preview-img {
  width: 120px;
  height: 120px;
  object-fit: cover;
  border-radius: var(--radius);
  box-shadow: var(--shadow-sm);
}

.preview-name {
  font-weight: 600;
  font-size: 14px;
  word-break: break-all;
}

.preview-size {
  color: var(--muted);
  font-size: 13px;
  margin-top: 4px;
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

@media (max-width: 640px) {
  .drop-zone {
    padding: 28px 16px;
  }

  .preview-wrapper {
    flex-wrap: wrap;
    justify-content: center;
  }

  .preview-img {
    width: 100px;
    height: 100px;
  }

  .action-bar {
    flex-wrap: wrap;
  }

  .action-bar .button {
    flex: 1;
    text-align: center;
  }
}
</style>
