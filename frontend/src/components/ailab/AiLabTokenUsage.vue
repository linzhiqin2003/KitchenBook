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
  // Hermes 扩展：{ sections: { key: {label, tokens} }, total_local, encoding }
  breakdown: { type: Object, default: null },
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

// ── Breakdown ──────────────────────────────────────────────────────────
// 每段固定一个颜色，跟 Claude Code 的拆解面板观感对齐。
const SECTION_COLOR = {
  identity: '#3d7cc9',
  user_system: '#5b8dd6',
  tool_guidance: '#7aa3e0',
  memory_files: '#a78bfa',
  skills: '#ec4899',
  context_files: '#f59e0b',
  env_meta: '#84cc16',
  ephemeral_system: '#14b8a6',
  tools: '#10b981',
  messages: '#22c55e',
}

const breakdownSections = computed(() => {
  const raw = props.breakdown && props.breakdown.sections
  if (!raw || typeof raw !== 'object') return []
  // sections 已经是有序对象（Hermes 端按 BREAKDOWN_LABELS 顺序输出）
  return Object.entries(raw).map(([key, info]) => ({
    key,
    label: info?.label || key,
    tokens: Number(info?.tokens) || 0,
    color: SECTION_COLOR[key] || '#94a3b8',
  })).filter(s => s.tokens > 0)
})

const breakdownTotalLocal = computed(() => {
  if (!props.breakdown) return 0
  return Number(props.breakdown.total_local) || breakdownSections.value.reduce((a, b) => a + b.tokens, 0)
})

const breakdownEncoding = computed(() => props.breakdown?.encoding || '')

// 进度条以 contextLimit 为分母，每段的宽度 = tokens / contextLimit
const sectionWidthPercent = (tokens) => {
  if (!props.contextLimit) return 0
  return (tokens / props.contextLimit) * 100
}

// 列表里展示的"占比"：相对 prompt_tokens（API 真值）
const sectionShareLabel = (tokens) => {
  const denom = props.promptTokens || breakdownTotalLocal.value
  if (!denom) return ''
  const p = (tokens / denom) * 100
  if (p < 0.1) return '<0.1%'
  if (p < 10) return `${p.toFixed(1)}%`
  return `${p.toFixed(0)}%`
}

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
        class="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 w-[340px] rounded-xl shadow-lg overflow-hidden z-30"
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

          <!-- 堆叠进度条：始终按段拆 + completion，缺数据时空着 -->
          <div class="mt-2 h-1.5 rounded-full overflow-hidden flex" style="background: var(--theme-200);">
            <div
              v-for="seg in breakdownSections"
              :key="seg.key"
              class="h-full transition-all duration-500"
              :style="{ width: `${sectionWidthPercent(seg.tokens)}%`, background: seg.color }"
              :title="`${seg.label}: ${seg.tokens.toLocaleString()} tokens`"
            ></div>
            <div
              v-if="completionTokens > 0"
              class="h-full transition-all duration-500"
              :style="{ width: `${sectionWidthPercent(completionTokens)}%`, background: '#16a34a' }"
              :title="`输出 completion: ${completionTokens.toLocaleString()} tokens`"
            ></div>
          </div>
        </div>

        <!-- Prompt 组成（breakdown）— 永远展示这个布局，无数据时只显示 completion 行 -->
        <div
          class="px-4 py-2 space-y-1"
          style="border-top: 1px solid var(--theme-100);"
        >
          <div class="flex items-center justify-between mb-1.5">
            <span class="text-[11px] font-semibold tracking-wide uppercase" style="color: var(--theme-500);">
              Prompt 组成
            </span>
            <span v-if="breakdownEncoding" class="text-[10px] font-mono" style="color: var(--theme-400);">
              {{ breakdownEncoding }}
            </span>
          </div>
          <template v-if="breakdownSections.length">
            <div
              v-for="seg in breakdownSections"
              :key="seg.key"
              class="flex items-center justify-between text-[12px]"
            >
              <span class="flex items-center gap-1.5 min-w-0" style="color: var(--theme-600);">
                <span class="w-1.5 h-1.5 rounded-full shrink-0" :style="{ background: seg.color }"></span>
                <span class="truncate">{{ seg.label }}</span>
              </span>
              <span class="flex items-center gap-2 shrink-0 font-mono" style="color: var(--theme-700);">
                <span>{{ formatNumber(seg.tokens) }}</span>
                <span class="text-[11px]" style="color: var(--theme-400); min-width: 36px; text-align: right;">
                  {{ sectionShareLabel(seg.tokens) }}
                </span>
              </span>
            </div>
          </template>
          <div v-else class="text-[12px] py-1" style="color: var(--theme-400);">
            发出第一条消息后这里会显示 prompt 各段 token 占用
          </div>
          <!-- 输出 completion 单独列出，跟堆叠条对齐 -->
          <div class="flex items-center justify-between text-[12px]">
            <span class="flex items-center gap-1.5 min-w-0" style="color: var(--theme-600);">
              <span class="w-1.5 h-1.5 rounded-full shrink-0" style="background: #16a34a;"></span>
              <span class="truncate">输出 completion</span>
            </span>
            <span class="flex items-center gap-2 shrink-0 font-mono" style="color: var(--theme-700);">
              <span>{{ formatNumber(completionTokens) }}</span>
              <span class="text-[11px]" style="color: var(--theme-400); min-width: 36px; text-align: right;"></span>
            </span>
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
