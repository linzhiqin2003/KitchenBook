<template>
  <div class="panel">
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
            <th v-if="showOrgSelector">归属</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(item, index) in localItems" :key="index" class="item-row">
            <td data-label="主类"><input class="input" v-model="item.main_category" /></td>
            <td data-label="子类"><input class="input" v-model="item.sub_category" /></td>
            <td data-label="商品"><input class="input" v-model="item.name" /></td>
            <td data-label="品牌"><input class="input" v-model="item.brand" /></td>
            <td data-label="数量"><input class="input" v-model="item.quantity" /></td>
            <td data-label="单位"><input class="input" v-model="item.unit" /></td>
            <td data-label="单价"><input class="input" v-model="item.unit_price" /></td>
            <td data-label="总价"><input class="input" v-model="item.total_price" /></td>
            <td v-if="showOrgSelector" data-label="归属">
              <select class="input org-select" v-model="item.target_org_id">
                <option value="">个人</option>
                <option v-for="org in orgs" :key="org.id" :value="org.id">{{ org.name }}</option>
              </select>
            </td>
            <td class="row-actions">
              <button class="btn-delete" @click="removeRow(index)" title="删除此行">
                <Trash2 :size="15" />
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
    <div class="item-actions">
      <button class="button ghost" @click="addRow">新增行</button>
      <div v-if="!hideActions" class="item-actions__right">
        <button v-if="showDiscard" class="button ghost danger-text" @click="emit('discard')">退出不保存</button>
        <button class="button" @click="onSave">保存修改</button>
        <button v-if="showConfirm" class="button secondary" @click="onConfirm">确认入库</button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { reactive, watch, watchEffect } from "vue";
import { Trash2 } from "lucide-vue-next";
import type { ReceiptItemPayload } from "../api/receipts";

interface OrgOption {
  id: string;
  name: string;
}

const props = withDefaults(defineProps<{
  items: ReceiptItemPayload[];
  showDiscard?: boolean;
  showConfirm?: boolean;
  hideActions?: boolean;
  orgs?: OrgOption[];
  currentOrgId?: string;
  showOrgSelector?: boolean;
}>(), {
  showDiscard: false,
  showConfirm: false,
  hideActions: false,
  orgs: () => [],
  currentOrgId: "",
  showOrgSelector: false,
});
const emit = defineEmits<{
  (e: "update:items", value: ReceiptItemPayload[]): void;
  (e: "save", items: ReceiptItemPayload[]): void;
  (e: "confirm", items: ReceiptItemPayload[]): void;
  (e: "discard"): void;
}>();

const localItems = reactive<ReceiptItemPayload[]>([]);

const sync = (items: ReceiptItemPayload[]) => {
  localItems.splice(0, localItems.length, ...items.map((item) => ({
    ...item,
    target_org_id: item.target_org_id ?? props.currentOrgId,
  })));
};

let skipNextSync = false;

watch(
  () => props.items,
  (value) => {
    if (skipNextSync) { skipNextSync = false; return; }
    sync(value || []);
  },
  { immediate: true }
);

const addRow = () => {
  localItems.push({ name: "", quantity: 1, main_category: "", sub_category: "", target_org_id: props.currentOrgId });
  emitUpdate();
};

const removeRow = (index: number) => {
  localItems.splice(index, 1);
  emitUpdate();
};

const emitUpdate = () => {
  skipNextSync = true;
  emit("update:items", localItems.map((item, index) => ({ ...item, line_index: index })));
};

// Deep watch: 任何字段编辑都同步到父组件（节流 300ms）
let debounceTimer: ReturnType<typeof setTimeout> | null = null;
watch(
  localItems,
  () => {
    if (debounceTimer) clearTimeout(debounceTimer);
    debounceTimer = setTimeout(emitUpdate, 300);
  },
  { deep: true }
);

const getItems = () => localItems.map((item, index) => ({ ...item, line_index: index }));

const onSave = () => {
  const data = getItems();
  emit("update:items", data);
  emit("save", data);
};

const onConfirm = () => {
  const data = getItems();
  emit("update:items", data);
  emit("confirm", data);
};
</script>

<style scoped>
.item-table-wrapper {
  overflow-x: auto;
}

.row-actions {
  vertical-align: middle;
}

.btn-delete {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border: none;
  border-radius: 8px;
  background: transparent;
  color: var(--muted);
  cursor: pointer;
  transition: all 0.2s ease;
}

.btn-delete:hover {
  background: rgba(255, 59, 48, 0.1);
  color: var(--danger);
}

.item-actions {
  margin-top: 12px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.item-actions__right {
  display: flex;
  gap: 12px;
}

.danger-text {
  color: var(--danger) !important;
}

.org-select {
  min-width: 80px;
  padding-right: 24px;
}

@media (max-width: 640px) {
  .item-table-wrapper :deep(thead) {
    display: none;
  }

  .item-table-wrapper :deep(.item-row) {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 8px;
    padding: 14px 0;
    border-bottom: 1px solid var(--border);
  }

  .item-table-wrapper :deep(.item-row td) {
    display: flex;
    flex-direction: column;
    gap: 4px;
    padding: 0;
    border-bottom: none;
  }

  .item-table-wrapper :deep(.item-row td)::before {
    content: attr(data-label);
    font-size: 11px;
    font-weight: 600;
    color: var(--muted);
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }

  .item-table-wrapper :deep(.item-row td[data-label="商品"]) {
    grid-column: 1 / -1;
  }

  .item-table-wrapper :deep(.item-row .row-actions) {
    grid-column: 1 / -1;
    display: flex;
    justify-content: flex-end;
    padding: 0;
  }

  .item-table-wrapper :deep(.item-row .row-actions)::before {
    display: none;
  }

  .item-actions {
    flex-direction: column;
    gap: 10px;
  }

  .item-actions .button {
    width: 100%;
    text-align: center;
    justify-content: center;
  }

  .item-actions__right {
    flex-direction: column;
    gap: 10px;
    width: 100%;
  }

  .item-actions__right .button {
    width: 100%;
  }
}
</style>
