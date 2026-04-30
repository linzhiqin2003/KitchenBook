<script setup>
import { computed, ref } from 'vue'

const props = defineProps({
  entry: {
    type: Object,
    required: true,
  },
  level: {
    type: Number,
    default: 0,
  },
})

const isDirectory = computed(() => props.entry?.type === 'dir')
const hasChildren = computed(() => isDirectory.value && Array.isArray(props.entry?.children) && props.entry.children.length > 0)
const isExpanded = ref(props.level < 2)

const indentStyle = computed(() => ({
  paddingLeft: `${props.level * 14}px`,
}))

const toggleExpanded = () => {
  if (!isDirectory.value) return
  isExpanded.value = !isExpanded.value
}

const formatSize = (size) => {
  const value = Number(size) || 0
  if (value < 1024) return `${value} B`
  if (value < 1024 * 1024) return `${(value / 1024).toFixed(1)} KB`
  return `${(value / (1024 * 1024)).toFixed(1)} MB`
}

const formatTime = (iso) => {
  if (!iso) return ''
  const date = new Date(iso)
  if (Number.isNaN(date.getTime())) return ''
  return date.toLocaleString('zh-CN', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  })
}
</script>

<template>
  <div>
    <button
      class="w-full flex items-start gap-2 rounded-lg px-2 py-1.5 text-left transition-colors hover:bg-white/70 cursor-pointer"
      :style="indentStyle"
      @click="toggleExpanded"
    >
      <span class="w-4 h-4 shrink-0 mt-0.5 flex items-center justify-center" style="color: #9a9aa0;">
        <svg
          v-if="isDirectory"
          class="w-3.5 h-3.5 transition-transform"
          :style="isExpanded ? 'transform: rotate(90deg);' : ''"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
          stroke-width="1.8"
        >
          <path stroke-linecap="round" stroke-linejoin="round" d="M9 5l7 7-7 7" />
        </svg>
      </span>

      <span class="w-4 h-4 shrink-0 mt-0.5" :style="isDirectory ? 'color: #d97706;' : 'color: #64748b;'">
        <svg v-if="isDirectory" class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="1.6">
          <path stroke-linecap="round" stroke-linejoin="round" d="M2.25 6.75A2.25 2.25 0 014.5 4.5h4.19a2.25 2.25 0 011.59.659l1.06 1.06a2.25 2.25 0 001.59.659h6.56a2.25 2.25 0 012.25 2.25v8.25a2.25 2.25 0 01-2.25 2.25H4.5a2.25 2.25 0 01-2.25-2.25V6.75z" />
        </svg>
        <svg v-else class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="1.6">
          <path stroke-linecap="round" stroke-linejoin="round" d="M19.5 14.25v-8.625a1.125 1.125 0 00-1.125-1.125H8.25m11.25 9.75h-2.625a1.125 1.125 0 00-1.125 1.125V18m4.875-3.75l-3.375 3.375a2.25 2.25 0 01-1.59.659H6.375A1.125 1.125 0 015.25 17.16V5.625A1.125 1.125 0 016.375 4.5H8.25m0 0l2.25 2.25m-2.25-2.25V6.75m0-2.25h6.75" />
        </svg>
      </span>

      <div class="min-w-0 flex-1">
        <div class="flex items-center gap-2 min-w-0">
          <span class="text-[13px] truncate" style="color: #2c2c30;">{{ entry.name }}</span>
          <span
            v-if="!isDirectory && entry.size !== undefined"
            class="text-[11px] shrink-0"
            style="color: #9a9aa0;"
          >{{ formatSize(entry.size) }}</span>
        </div>
        <div class="text-[11px] mt-0.5" style="color: #b0b0b6;">
          <span>{{ formatTime(entry.modified_at) }}</span>
          <span v-if="entry.type === 'symlink' && entry.target"> -> {{ entry.target }}</span>
          <span v-if="entry.error"> · {{ entry.error }}</span>
        </div>
      </div>
    </button>

    <div v-if="hasChildren && isExpanded" class="mt-0.5 space-y-0.5">
      <AiLabWorkspaceTreeNode
        v-for="child in entry.children"
        :key="child.path"
        :entry="child"
        :level="level + 1"
      />
    </div>
  </div>
</template>
