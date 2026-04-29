<script setup>
import { ref, computed, watch } from 'vue'

const props = defineProps({
  // 一个 segment：{ subTurns, content, currentReasoning, currentToolCall }
  segment: { type: Object, required: true },
  // 这一段是否仍在直播（即流式状态下的最后一段）
  isStreaming: { type: Boolean, default: false },
  // 父组件传入的"思维链阶段"标记，决定 shimmer 是否生效
  isReasoningPhase: { type: Boolean, default: false },
})

// 折叠状态：默认折叠
const traceCollapsed = ref(true)
// 单步骤列表里被点开的步骤 id
const expandedSteps = ref({})

const subTurns = computed(() => Array.isArray(props.segment?.subTurns) ? props.segment.subTurns : [])
const currentReasoning = computed(() => props.segment?.currentReasoning || '')
const currentToolCall = computed(() => props.segment?.currentToolCall || null)

const hasTraceTimeline = computed(() => {
  return subTurns.value.length > 0 || Boolean(currentReasoning.value) || Boolean(currentToolCall.value)
})

const isLive = computed(() => {
  return props.isStreaming && (Boolean(currentReasoning.value) || Boolean(currentToolCall.value))
})

const getTurnKey = (turn, turnIndex) => turn?.id || `t-${turnIndex}`

// 已完成 subTurns + 当前 live 的步骤合并
const steps = computed(() => {
  const result = []
  subTurns.value.forEach((turn, turnIndex) => {
    const baseKey = getTurnKey(turn, turnIndex)
    if (turn.reasoning) {
      result.push({
        id: `${baseKey}-r`,
        kind: 'thinking',
        text: turn.reasoning,
        status: 'done',
        live: false,
        durationMs: turn.reasoningStartedAt && turn.reasoningFinishedAt
          ? turn.reasoningFinishedAt - turn.reasoningStartedAt
          : 0,
      })
    }
    if (turn.toolCall) {
      result.push({
        id: `${baseKey}-t`,
        kind: 'tool',
        toolCall: turn.toolCall,
        status: turn.toolCall.status,
        live: false,
      })
    }
  })
  if (currentReasoning.value) {
    result.push({
      id: 'live-reasoning',
      kind: 'thinking',
      text: currentReasoning.value,
      status: 'running',
      live: true,
    })
  }
  if (currentToolCall.value) {
    result.push({
      id: 'live-tool',
      kind: 'tool',
      toolCall: currentToolCall.value,
      status: currentToolCall.value.status,
      live: currentToolCall.value.status === 'running' || currentToolCall.value.status === 'parsing',
    })
  }
  return result
})

const singleStep = computed(() => steps.value.length === 1 ? steps.value[0] : null)

const headerLabel = computed(() => {
  if (isLive.value) {
    if (currentToolCall.value) {
      const name = currentToolCall.value.name || 'tool'
      const status = currentToolCall.value.status
      if (status === 'parsing' || status === 'pending') return `Calling ${name}`
      if (status === 'running') return `Running ${name}`
      return name
    }
    if (currentReasoning.value) return 'Thinking…'
  }
  // 完成态：聚合摘要
  const tools = subTurns.value.filter(t => t.toolCall).map(t => t.toolCall)
  const totalThinkingMs = subTurns.value.reduce((s, t) => {
    if (t.reasoningStartedAt && t.reasoningFinishedAt) return s + (t.reasoningFinishedAt - t.reasoningStartedAt)
    return s
  }, 0)
  const parts = []
  if (totalThinkingMs > 0) parts.push(`thought for ${formatDuration(totalThinkingMs)}`)
  if (tools.length) {
    const counts = {}
    for (const t of tools) {
      const name = t.name || 'tool'
      counts[name] = (counts[name] || 0) + 1
    }
    for (const [name, count] of Object.entries(counts)) {
      parts.push(count > 1 ? `ran ${name} ${count}x` : `ran ${name}`)
    }
  }
  if (!parts.length) return 'Thought'
  return parts.join(', ').replace(/^./, c => c.toUpperCase())
})

const stepLabel = (step) => {
  if (step.kind === 'thinking') {
    return step.live ? 'Thinking…' : 'Thought'
  }
  if (step.kind === 'tool') {
    const name = step.toolCall?.name || 'tool'
    if (step.live) {
      if (step.status === 'parsing' || step.status === 'pending') return `Calling ${name}`
      return `Running ${name}`
    }
    return `Ran ${name}`
  }
  return ''
}

const formatDuration = (ms) => {
  if (!Number.isFinite(ms) || ms <= 0) return ''
  const totalSeconds = ms / 1000
  if (totalSeconds < 60) {
    return totalSeconds < 10 ? `${totalSeconds.toFixed(1)}s` : `${Math.round(totalSeconds)}s`
  }
  const totalMinutes = Math.floor(totalSeconds / 60)
  if (totalMinutes < 60) {
    const sec = Math.round(totalSeconds - totalMinutes * 60)
    return sec ? `${totalMinutes}m ${sec}s` : `${totalMinutes}m`
  }
  const hours = Math.floor(totalMinutes / 60)
  const m = totalMinutes - hours * 60
  return m ? `${hours}h ${m}m` : `${hours}h`
}

const stepMeta = (step) => {
  if (step.kind === 'thinking') {
    return formatDuration(step.durationMs || 0)
  }
  if (step.kind === 'tool') {
    return formatToolDuration(step.toolCall)
  }
  return ''
}

const formatToolDuration = (toolCall) => {
  if (!toolCall?.startedAt || !toolCall?.finishedAt) return ''
  const seconds = (toolCall.finishedAt - toolCall.startedAt) / 1000
  if (!Number.isFinite(seconds) || seconds < 0) return ''
  return `${seconds.toFixed(1)}s`
}

const formatToolArguments = (toolCall) => {
  if (!toolCall) return '{}'
  const parsed = toolCall.parsedArguments
  if (parsed && typeof parsed === 'object') {
    try { return JSON.stringify(parsed, null, 2) } catch { /* ignore */ }
  }
  if (toolCall.argumentsText) return toolCall.argumentsText
  return '{}'
}

const formatToolResult = (toolCall) => {
  if (!toolCall) return ''
  if (toolCall.status === 'error') return toolCall.error || toolCall.result || '工具执行失败'
  return toolCall.result || ''
}

const hasToolArguments = (toolCall) => {
  const args = formatToolArguments(toolCall)
  return args && args !== '{}'
}

const isStepExpanded = (id) => Boolean(expandedSteps.value[id])
const toggleStep = (id) => {
  expandedSteps.value = { ...expandedSteps.value, [id]: !isStepExpanded(id) }
}

// 流式中保持展开，结束（reasoning → answering 或 done）后自动折叠一次
const autoCollapsedOnce = ref(false)
watch(
  () => isLive.value,
  (live, prevLive) => {
    if (live && !autoCollapsedOnce.value) {
      // 进入直播时打开
      traceCollapsed.value = false
    }
    if (prevLive && !live && !autoCollapsedOnce.value) {
      // 直播结束 → 自动折叠一次
      traceCollapsed.value = true
      autoCollapsedOnce.value = true
    }
  },
  { immediate: true }
)
</script>

<template>
  <div v-if="hasTraceTimeline" class="w-full">
    <!-- 折叠头：流式中显示当前活动；完成后显示聚合摘要 -->
    <button class="trace-header" @click="traceCollapsed = !traceCollapsed">
      <span :class="['trace-header-text', { 'trace-shimmer-text': isLive }]">{{ headerLabel }}</span>
      <svg
        :class="['trace-chevron', { 'is-open': !traceCollapsed }]"
        fill="none" stroke="currentColor" viewBox="0 0 24 24"
      >
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.2" d="M9 5l7 7-7 7"/>
      </svg>
    </button>

    <Transition name="collapse">
      <div v-if="!traceCollapsed" class="trace-list">
        <!-- 单步骤：直接展开详情 -->
        <template v-if="singleStep">
          <div v-if="singleStep.kind === 'thinking'" class="trace-thinking-text">{{ singleStep.text }}</div>
          <template v-else-if="singleStep.kind === 'tool'">
            <pre v-if="hasToolArguments(singleStep.toolCall)" class="trace-code">{{ formatToolArguments(singleStep.toolCall) }}</pre>
            <div
              v-if="formatToolResult(singleStep.toolCall)"
              :class="['trace-result-text', singleStep.toolCall.status === 'error' ? 'text-red-600' : '']"
            >{{ formatToolResult(singleStep.toolCall) }}</div>
          </template>
        </template>

        <!-- 多步骤：每条折叠 -->
        <template v-else>
          <div
            v-for="step in steps"
            :key="step.id"
            class="trace-item"
          >
            <button class="trace-item-row" @click="toggleStep(step.id)">
              <span class="trace-step-icon">
                <svg v-if="step.kind === 'tool' && step.status === 'success'" viewBox="0 0 12 12" fill="none" stroke="currentColor" class="trace-icon-check">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.5 6.5l2.4 2.4L9.5 3.5"/>
                </svg>
                <svg v-else-if="step.kind === 'tool' && step.status === 'error'" viewBox="0 0 12 12" fill="none" stroke="currentColor" class="trace-icon-cross">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 3l6 6M9 3l-6 6"/>
                </svg>
                <span v-else-if="step.live" class="trace-icon-live"></span>
                <span v-else class="trace-icon-dot"></span>
              </span>

              <span :class="['trace-step-label', step.kind === 'tool' && 'trace-step-label-mono', { 'trace-shimmer-text': step.live }]">{{ stepLabel(step) }}</span>
              <span v-if="stepMeta(step)" class="trace-step-meta">{{ stepMeta(step) }}</span>

              <svg
                :class="['trace-chevron', 'trace-chevron-sm', 'trace-chevron-end', { 'is-open': isStepExpanded(step.id) }]"
                fill="none" stroke="currentColor" viewBox="0 0 24 24"
              >
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.2" d="M9 5l7 7-7 7"/>
              </svg>
            </button>

            <Transition name="collapse">
              <div v-if="isStepExpanded(step.id)" class="trace-item-detail">
                <div v-if="step.kind === 'thinking'" class="trace-thinking-text">{{ step.text }}</div>
                <template v-else-if="step.kind === 'tool'">
                  <pre v-if="hasToolArguments(step.toolCall)" class="trace-code">{{ formatToolArguments(step.toolCall) }}</pre>
                  <div
                    v-if="formatToolResult(step.toolCall)"
                    :class="['trace-result-text', step.toolCall.status === 'error' ? 'text-red-600' : '']"
                  >{{ formatToolResult(step.toolCall) }}</div>
                </template>
              </div>
            </Transition>
          </div>
        </template>
      </div>
    </Transition>
  </div>
</template>

<style scoped>
.trace-header {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  max-width: 100%;
  padding: 0.2rem 0.5rem;
  margin-left: -0.5rem;
  cursor: pointer;
  user-select: none;
  border: 0;
  background: transparent;
  border-radius: 0.4rem;
  transition: background 0.16s ease, color 0.16s ease;
  color: var(--theme-500);
}
.trace-header:hover {
  background: var(--theme-100);
  color: var(--theme-700);
}
.trace-header-text {
  font-size: 0.78rem;
  font-weight: 500;
  white-space: normal;
  overflow-wrap: break-word;
}
.trace-chevron {
  width: 0.78rem;
  height: 0.78rem;
  color: var(--theme-400);
  flex-shrink: 0;
  transition: transform 0.18s ease, color 0.18s ease;
  margin-left: auto;
}
.trace-chevron.is-open { transform: rotate(90deg); }
.trace-chevron-sm { width: 0.7rem; height: 0.7rem; }
.trace-chevron-end { margin-left: auto; }

.trace-list {
  width: min(100%, 42rem);
  margin: 0.25rem 0;
  padding: 0.25rem 0;
  position: relative;
}
/* 只在多步骤（包含 .trace-item）时画连接虚线，避免单步骤展开时穿过详情文本 */
.trace-list:has(.trace-item)::before {
  content: '';
  position: absolute;
  left: 0.675rem;
  top: 0.6rem;
  bottom: 0.6rem;
  border-left: 1px dashed var(--theme-200, #d8d8d2);
  pointer-events: none;
}
.trace-item { position: relative; }
.trace-item-row {
  display: flex;
  align-items: center;
  gap: 0.45rem;
  width: 100%;
  padding: 0.18rem 0.5rem 0.18rem 0.25rem;
  border: 0;
  background: transparent;
  border-radius: 0.4rem;
  cursor: pointer;
  text-align: left;
  color: var(--theme-500);
  transition: background 0.16s ease, color 0.16s ease;
  position: relative;
}
.trace-item-row:hover { background: var(--theme-100); color: var(--theme-700); }

.trace-step-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 0.85rem;
  height: 0.85rem;
  flex-shrink: 0;
}
.trace-icon-check { width: 0.8rem; height: 0.8rem; color: var(--theme-400); }
.trace-icon-cross { width: 0.8rem; height: 0.8rem; color: #b91c1c; }
.trace-icon-dot {
  width: 0.32rem; height: 0.32rem; border-radius: 999px;
  background: var(--theme-300, #c8c8c0);
}
.trace-icon-live {
  width: 0.4rem; height: 0.4rem; border-radius: 999px;
  background: var(--ai-accent, #3d7cc9);
  animation: progressPulse 1.2s ease-in-out infinite;
}
.trace-step-label {
  font-size: 0.78rem;
  font-weight: 500;
  white-space: normal;
  overflow-wrap: break-word;
  min-width: 0;
}
.trace-step-label-mono {
  font-family: var(--ai-font-mono, ui-monospace, monospace);
  font-weight: 600;
  color: var(--theme-600);
}
.trace-step-meta {
  font-size: 0.68rem;
  color: var(--theme-400);
  font-variant-numeric: tabular-nums;
  white-space: nowrap;
  flex-shrink: 0;
}
.trace-item-detail {
  margin: 0.25rem 0 0.45rem 1.55rem;
  display: grid;
  gap: 0.4rem;
  animation: fadeInSoft 0.18s ease-out;
}
.trace-thinking-text {
  padding: 0.45rem 0.6rem;
  font-size: 0.76rem;
  line-height: 1.7;
  color: var(--theme-500);
  background: var(--theme-50, #f8f8f6);
  border-radius: 0.45rem;
  white-space: pre-wrap;
  word-break: break-word;
  max-height: 22rem;
  overflow-y: auto;
}
.trace-code {
  padding: 0.5rem 0.7rem;
  font-size: 0.7rem;
  line-height: 1.55;
  background: var(--theme-50, #f8f8f6);
  border-radius: 0.4rem;
  font-family: var(--ai-font-mono, ui-monospace, monospace);
  color: var(--theme-700);
  white-space: pre-wrap;
  word-break: break-word;
  max-height: 22rem;
  overflow-y: auto;
}
.trace-result-text {
  padding: 0.45rem 0.6rem;
  font-size: 0.74rem;
  line-height: 1.6;
  color: var(--theme-600);
  background: var(--theme-50, #f8f8f6);
  border-radius: 0.45rem;
  white-space: pre-wrap;
  word-break: break-word;
  max-height: 22rem;
  overflow-y: auto;
}

/* 把这几个细节框的滚动条做细做淡 —— 默认那条 macOS 灰白滚动条
   太抢戏，跟 trace 的轻量风格冲突 */
.trace-thinking-text,
.trace-code,
.trace-result-text {
  scrollbar-width: thin;
  scrollbar-color: rgba(15, 23, 42, 0.18) transparent;
}
.trace-thinking-text::-webkit-scrollbar,
.trace-code::-webkit-scrollbar,
.trace-result-text::-webkit-scrollbar {
  width: 4px;
  height: 4px;
}
.trace-thinking-text::-webkit-scrollbar-track,
.trace-code::-webkit-scrollbar-track,
.trace-result-text::-webkit-scrollbar-track {
  background: transparent;
}
.trace-thinking-text::-webkit-scrollbar-thumb,
.trace-code::-webkit-scrollbar-thumb,
.trace-result-text::-webkit-scrollbar-thumb {
  background: rgba(15, 23, 42, 0.18);
  border-radius: 2px;
}
.trace-thinking-text:hover::-webkit-scrollbar-thumb,
.trace-code:hover::-webkit-scrollbar-thumb,
.trace-result-text:hover::-webkit-scrollbar-thumb {
  background: rgba(15, 23, 42, 0.3);
}

.trace-shimmer-text {
  background: linear-gradient(
    90deg,
    var(--theme-400, #94948c) 0%,
    var(--theme-700, #2d2d28) 50%,
    var(--theme-400, #94948c) 100%
  );
  background-size: 200% 100%;
  -webkit-background-clip: text;
  background-clip: text;
  -webkit-text-fill-color: transparent;
  color: transparent;
  animation: shimmerSweep 1.6s linear infinite;
}

@keyframes progressPulse {
  0%, 100% { opacity: 0.55; transform: scale(1); }
  50%      { opacity: 1;    transform: scale(1.18); }
}
@keyframes shimmerSweep {
  0%   { background-position: 100% 0; }
  100% { background-position: -100% 0; }
}
@keyframes fadeInSoft {
  from { opacity: 0; transform: translateY(-2px); }
  to   { opacity: 1; transform: translateY(0); }
}

.collapse-enter-active, .collapse-leave-active {
  transition: opacity 0.18s ease, max-height 0.22s ease;
  overflow: hidden;
}
.collapse-enter-from, .collapse-leave-to { opacity: 0; max-height: 0; }
.collapse-enter-to, .collapse-leave-from { opacity: 1; max-height: 600px; }
</style>
