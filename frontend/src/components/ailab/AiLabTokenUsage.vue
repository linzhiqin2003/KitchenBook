<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'

const props = defineProps({
  // 最近一次请求的 token 数（代表当前 context 占用）
  promptTokens: { type: Number, default: 0 },
  completionTokens: { type: Number, default: 0 },
  // 整个 session 的累计统计
  totalPromptTokens: { type: Number, default: 0 },
  totalCompletionTokens: { type: Number, default: 0 },
  turnCount: { type: Number, default: 0 },
  // context 上限
  contextLimit: { type: Number, default: 1_000_000 },
})

const isExpanded = ref(false)
const wrapperRef = ref(null)

// 当前 context 占用 = 最近一次的 prompt + completion
const contextTokens = computed(() => props.promptTokens + props.completionTokens)

const percent = computed(() => {
  if (props.contextLimit <= 0) return 0
  return (contextTokens.value / props.contextLimit) * 100
})

const percentLabel = computed(() => {
  const p = percent.value
  if (p === 0) return '0%'
  if (p < 0.1) return '<0.1%'
  if (p < 10) return `${p.toFixed(2)}%`
  return `${p.toFixed(1)}%`
})

// 进度条颜色：随占用率渐变
const barColor = computed(() => {
  const p = percent.value
  if (p < 50) return 'var(--ai-accent)'
  if (p < 80) return '#d97706' // amber-600
  return '#dc2626' // red-600
})

const formatNumber = (n) => {
  if (!n) return '0'
  if (n < 1000) return String(n)
  if (n < 1_000_000) return `${(n / 1000).toFixed(n < 10_000 ? 2 : 1)}K`
  return `${(n / 1_000_000).toFixed(2)}M`
}

const formatLimit = (n) => {
  if (n >= 1_000_000) return `${n / 1_000_000}M`
  if (n >= 1000) return `${n / 1000}K`
  return String(n)
}

const contextLabel = computed(() => formatNumber(contextTokens.value))
const limitLabel = computed(() => formatLimit(props.contextLimit))

const togglePanel = () => {
  isExpanded.value = !isExpanded.value
}

const handleOutsideClick = (e) => {
  if (!wrapperRef.value) return
  if (!wrapperRef.value.contains(e.target)) {
    isExpanded.value = false
  }
}

onMounted(() => {
  document.addEventListener('click', handleOutsideClick)
})

onUnmounted(() => {
  document.removeEventListener('click', handleOutsideClick)
})
</script>

<template>
  <div ref="wrapperRef" class="relative inline-block">
    <!-- 触发器：xxx / 1M (xx%) -->
    <button
      @click.stop="togglePanel"
      class="flex items-center gap-1.5 px-2 py-0.5 rounded-md transition-colors cursor-pointer hover:bg-[var(--theme-100)]"
      :class="{ 'bg-[var(--theme-100)]': isExpanded }"
      style="font-size: 12px; color: var(--theme-500);"
      :title="`Context window: ${contextTokens.toLocaleString()} / ${contextLimit.toLocaleString()} tokens`"
    >
      <span class="font-mono tracking-tight">
        {{ contextLabel }} / {{ limitLabel }}
      </span>
      <span style="color: var(--theme-400);">({{ percentLabel }})</span>
      <svg
        class="w-3 h-3 transition-transform"
        :class="{ 'rotate-180': isExpanded }"
        fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2"
      >
        <path stroke-linecap="round" stroke-linejoin="round" d="M19.5 8.25l-7.5 7.5-7.5-7.5" />
      </svg>
    </button>

    <!-- 详情面板 -->
    <Transition name="panel">
      <div
        v-if="isExpanded"
        class="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 w-[320px] rounded-xl shadow-lg overflow-hidden z-30"
        style="background: var(--theme-50); border: 1px solid var(--theme-200);"
        @click.stop
      >
        <!-- 标题 -->
        <div class="px-4 pt-3 pb-2 flex items-center justify-between" style="border-bottom: 1px solid var(--theme-100);">
          <span class="text-[12px] font-semibold tracking-wide uppercase" style="color: var(--theme-700);">
            Context Window
          </span>
          <span class="text-[11px] font-mono" style="color: var(--theme-400);">Hermes</span>
        </div>

        <!-- 当前 Context 大数字 -->
        <div class="px-4 pt-3 pb-2">
          <div class="flex items-baseline gap-1.5">
            <span class="text-[22px] font-semibold font-mono leading-none" style="color: var(--theme-700);">
              {{ contextLabel }}
            </span>
            <span class="text-[12px]" style="color: var(--theme-400);">
              / {{ limitLabel }} tokens
            </span>
          </div>
          <div class="text-[11px] mt-1" style="color: var(--theme-500);">
            占用 {{ percentLabel }}
          </div>
          <!-- 进度条 -->
          <div class="mt-2 h-1.5 rounded-full overflow-hidden" style="background: var(--theme-200);">
            <div
              class="h-full rounded-full transition-all duration-500"
              :style="{ width: `${Math.min(percent, 100)}%`, background: barColor }"
            ></div>
          </div>
        </div>

        <!-- 分段细节 -->
        <div class="px-4 py-2 space-y-1.5" style="border-top: 1px solid var(--theme-100);">
          <div class="flex items-center justify-between text-[12px]">
            <span class="flex items-center gap-1.5" style="color: var(--theme-500);">
              <span class="w-1.5 h-1.5 rounded-full" style="background: #3d7cc9;"></span>
              输入 prompt
            </span>
            <span class="font-mono" style="color: var(--theme-700);">{{ formatNumber(promptTokens) }}</span>
          </div>
          <div class="flex items-center justify-between text-[12px]">
            <span class="flex items-center gap-1.5" style="color: var(--theme-500);">
              <span class="w-1.5 h-1.5 rounded-full" style="background: #16a34a;"></span>
              输出 completion
            </span>
            <span class="font-mono" style="color: var(--theme-700);">{{ formatNumber(completionTokens) }}</span>
          </div>
        </div>

        <!-- Session 累计 -->
        <div class="px-4 py-2.5" style="border-top: 1px solid var(--theme-100); background: var(--theme-100);">
          <div class="text-[11px] font-semibold tracking-wide uppercase mb-1.5" style="color: var(--theme-500);">
            Session 累计
          </div>
          <div class="space-y-1">
            <div class="flex items-center justify-between text-[12px]">
              <span style="color: var(--theme-500);">轮次</span>
              <span class="font-mono" style="color: var(--theme-700);">{{ turnCount }}</span>
            </div>
            <div class="flex items-center justify-between text-[12px]">
              <span style="color: var(--theme-500);">输入累计</span>
              <span class="font-mono" style="color: var(--theme-700);">{{ formatNumber(totalPromptTokens) }}</span>
            </div>
            <div class="flex items-center justify-between text-[12px]">
              <span style="color: var(--theme-500);">输出累计</span>
              <span class="font-mono" style="color: var(--theme-700);">{{ formatNumber(totalCompletionTokens) }}</span>
            </div>
            <div class="flex items-center justify-between text-[12px] pt-1" style="border-top: 1px dashed var(--theme-200);">
              <span class="font-medium" style="color: var(--theme-600);">总计</span>
              <span class="font-mono font-semibold" style="color: var(--theme-700);">
                {{ formatNumber(totalPromptTokens + totalCompletionTokens) }}
              </span>
            </div>
          </div>
        </div>
      </div>
    </Transition>
  </div>
</template>

<style scoped>
.panel-enter-active,
.panel-leave-active {
  transition: opacity 0.18s ease, transform 0.18s ease;
}
.panel-enter-from,
.panel-leave-to {
  opacity: 0;
  transform: translate(-50%, 4px);
}
.panel-enter-to,
.panel-leave-from {
  opacity: 1;
  transform: translate(-50%, 0);
}
</style>
