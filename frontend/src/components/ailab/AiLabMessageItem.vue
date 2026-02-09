<script setup>
import { ref, computed, nextTick, watch } from 'vue'

const props = defineProps({
  message: {
    type: Object,
    required: true
  },
  index: {
    type: Number,
    required: true
  },
  isStreaming: {
    type: Boolean,
    default: false
  },
  isReasoningPhase: {
    type: Boolean,
    default: false
  },
  reasoningCollapsed: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['edit', 'regenerate', 'toggle-reasoning', 'copy'])

// 编辑状态
const isEditing = ref(false)
const editContent = ref('')
const editTextarea = ref(null)
const bubbleRef = ref(null)
const editBoxWidth = ref(400)

// 复制状态
const copied = ref(false)

// 进入编辑模式
const startEdit = async () => {
  // 获取原气泡宽度
  if (bubbleRef.value) {
    editBoxWidth.value = Math.max(bubbleRef.value.offsetWidth, 200)
  }
  editContent.value = props.message.content
  isEditing.value = true
  await nextTick()
  if (editTextarea.value) {
    autoResizeTextarea()
    editTextarea.value.focus()
    editTextarea.value.select()
  }
}

// 自动调整 textarea 高度
function autoResizeTextarea() {
  if (!editTextarea.value) return
  editTextarea.value.style.height = 'auto'
  editTextarea.value.style.height = editTextarea.value.scrollHeight + 'px'
}

// 取消编辑
const cancelEdit = () => {
  isEditing.value = false
  editContent.value = ''
}

// 提交编辑
const submitEdit = () => {
  if (editContent.value.trim()) {
    emit('edit', props.message.id, editContent.value.trim())
    isEditing.value = false
  }
}

// 复制内容
const copyContent = async () => {
  try {
    await navigator.clipboard.writeText(props.message.content)
    copied.value = true
    setTimeout(() => {
      copied.value = false
    }, 2000)
  } catch (e) {
    console.error('复制失败:', e)
  }
}

const reasoningTurnCollapsed = ref({})
const toolArgsCollapsed = ref({})
const toolResultCollapsed = ref({})

const subTurns = computed(() => Array.isArray(props.message.subTurns) ? props.message.subTurns : [])
const currentReasoning = computed(() => props.message.currentReasoning || '')
const currentToolCall = computed(() => props.message.currentToolCall || null)

const hasTraceTimeline = computed(() => {
  return subTurns.value.length > 0 || Boolean(currentReasoning.value) || Boolean(currentToolCall.value)
})

const shouldShowLegacyReasoning = computed(() => {
  return Boolean(props.message.reasoning) && !hasTraceTimeline.value
})

const getTurnKey = (turn, turnIndex) => {
  return turn?.id || `${props.index}-${turnIndex}`
}

const getToolKey = (toolCall, fallback = '') => {
  return toolCall?.id || `${fallback || `tool-${props.index}`}-${toolCall?.index ?? 0}`
}

const isTurnCollapsed = (turn, turnIndex) => {
  const key = getTurnKey(turn, turnIndex)
  if (reasoningTurnCollapsed.value[key] === undefined) {
    return true
  }
  return reasoningTurnCollapsed.value[key]
}

const toggleTurnCollapse = (turn, turnIndex) => {
  const key = getTurnKey(turn, turnIndex)
  reasoningTurnCollapsed.value[key] = !isTurnCollapsed(turn, turnIndex)
}

const isToolArgsCollapsed = (toolCall, fallback = '') => {
  const key = getToolKey(toolCall, fallback)
  if (toolArgsCollapsed.value[key] === undefined) {
    return toolCall?.status !== 'parsing'
  }
  return toolArgsCollapsed.value[key]
}

const toggleToolArgs = (toolCall, fallback = '') => {
  const key = getToolKey(toolCall, fallback)
  toolArgsCollapsed.value[key] = !isToolArgsCollapsed(toolCall, fallback)
}

watch(subTurns, (turns) => {
  turns.forEach((turn, turnIndex) => {
    const key = getTurnKey(turn, turnIndex)
    if (reasoningTurnCollapsed.value[key] === undefined) {
      reasoningTurnCollapsed.value[key] = true
    }
    if (turn?.toolCall) {
      const toolKey = getToolKey(turn.toolCall, key)
      if (toolArgsCollapsed.value[toolKey] === undefined) {
        toolArgsCollapsed.value[toolKey] = true
      }
    }
  })
}, { deep: true, immediate: true })

watch(currentToolCall, (toolCall) => {
  if (!toolCall) return
  const key = getToolKey(toolCall, `current-${props.index}`)
  if (toolArgsCollapsed.value[key] === undefined) {
    toolArgsCollapsed.value[key] = false
  }
}, { deep: true, immediate: true })

const summarizeText = (text, maxLength = 58) => {
  const normalized = String(text || '').replace(/\s+/g, ' ').trim()
  if (!normalized) return '思考过程'
  if (normalized.length <= maxLength) return normalized
  return `${normalized.slice(0, maxLength)}...`
}

const formatToolStatus = (status = 'parsing') => {
  switch (status) {
    case 'running':
      return { label: '执行中', dotClass: 'bg-blue-500', textClass: 'text-blue-600', cardClass: 'tool-step-running', spinning: true }
    case 'success':
      return { label: '已完成', dotClass: 'bg-emerald-500', textClass: 'text-emerald-600', cardClass: 'tool-step-success', spinning: false }
    case 'error':
      return { label: '失败', dotClass: 'bg-red-500', textClass: 'text-red-600', cardClass: 'tool-step-error', spinning: false }
    case 'pending':
      return { label: '等待执行', dotClass: 'bg-slate-500', textClass: 'text-slate-500', cardClass: 'tool-step-pending', spinning: false }
    default:
      return { label: '参数拼接中', dotClass: 'bg-amber-500', textClass: 'text-amber-600', cardClass: 'tool-step-parsing', spinning: false }
  }
}

const displayToolName = (toolCall) => {
  return toolCall?.name || 'unnamed_tool'
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
    try {
      return JSON.stringify(parsed, null, 2)
    } catch {
      // ignore and fallback to raw
    }
  }
  if (toolCall.argumentsText) {
    return toolCall.argumentsText
  }
  return '{}'
}

const formatToolResult = (toolCall) => {
  if (!toolCall) return ''
  if (toolCall.status === 'error') {
    return toolCall.error || toolCall.result || '工具执行失败'
  }
  return toolCall.result || ''
}

const hasToolArguments = (toolCall) => {
  const args = formatToolArguments(toolCall)
  return args && args !== '{}'
}

// 工具结果折叠控制
const isToolResultCollapsed = (toolCall, fallback = '') => {
  const key = getToolKey(toolCall, fallback)
  if (toolResultCollapsed.value[key] === undefined) {
    return true // 默认折叠
  }
  return toolResultCollapsed.value[key]
}

const toggleToolResult = (toolCall, fallback = '') => {
  const key = getToolKey(toolCall, fallback)
  toolResultCollapsed.value[key] = !isToolResultCollapsed(toolCall, fallback)
}

// 从工具结果文本中解析 [REF:n] → URL 映射
const parseRefMap = (text) => {
  if (!text) return {}
  const map = {}
  // 匹配 [REF:n] ... https://url（同一行内，取最后出现的 URL）
  const re = /\[REF:(\d+)\][^\n]*(https?:\/\/\S+)/g
  let m
  while ((m = re.exec(text)) !== null) {
    if (!map[m[1]]) {
      map[m[1]] = m[2].replace(/[)\],.;:]+$/, '')
    }
  }
  return map
}

// 全局引用映射（从所有工具结果中收集）
const globalRefMap = computed(() => {
  const map = {}
  for (const turn of subTurns.value) {
    if (turn.toolCall?.result) {
      Object.assign(map, parseRefMap(turn.toolCall.result))
    }
  }
  if (currentToolCall.value?.result) {
    Object.assign(map, parseRefMap(currentToolCall.value.result))
  }
  return map
})

// HTML 转义
const escapeHtml = (text) => {
  const div = document.createElement('div')
  div.textContent = text
  return div.innerHTML
}

// Markdown 解析
const parseMarkdown = (markdown) => {
  if (!markdown) return ''

  let html = markdown

  // 保存数学公式
  const mathBlocks = []
  html = html.replace(/\\\[([\s\S]*?)\\\]/g, (match, formula) => {
    const placeholder = `__MATH_BLOCK_${mathBlocks.length}__`
    mathBlocks.push({ type: 'block', formula: formula.trim() })
    return placeholder
  })
  html = html.replace(/\$\$([\s\S]*?)\$\$/g, (match, formula) => {
    const placeholder = `__MATH_BLOCK_${mathBlocks.length}__`
    mathBlocks.push({ type: 'block', formula: formula.trim() })
    return placeholder
  })
  html = html.replace(/\\\(([\s\S]*?)\\\)/g, (match, formula) => {
    const placeholder = `__MATH_INLINE_${mathBlocks.length}__`
    mathBlocks.push({ type: 'inline', formula: formula.trim() })
    return placeholder
  })
  html = html.replace(/\$([^\$\n]+?)\$/g, (match, formula) => {
    const placeholder = `__MATH_INLINE_${mathBlocks.length}__`
    mathBlocks.push({ type: 'inline', formula: formula.trim() })
    return placeholder
  })

  // 保存代码块
  const codeBlocks = []
  html = html.replace(/```(\w+)?\n?([\s\S]*?)```/g, (match, lang, code) => {
    const placeholder = `__CODE_BLOCK_${codeBlocks.length}__`
    codeBlocks.push({ lang: lang || 'text', code: code.trim() })
    return placeholder
  })

  // 保存行内代码
  const inlineCodes = []
  html = html.replace(/`([^`]+)`/g, (match, code) => {
    const placeholder = `__INLINE_CODE_${inlineCodes.length}__`
    inlineCodes.push(code)
    return placeholder
  })

  // 标题
  html = html.replace(/^#### (.+)$/gm, '<h4 class="md-h4">$1</h4>')
  html = html.replace(/^### (.+)$/gm, '<h3 class="md-h3">$1</h3>')
  html = html.replace(/^## (.+)$/gm, '<h2 class="md-h2">$1</h2>')
  html = html.replace(/^# (.+)$/gm, '<h1 class="md-h1">$1</h1>')

  // 粗体和斜体
  html = html.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
  html = html.replace(/\*(.+?)\*/g, '<em>$1</em>')

  // 链接
  html = html.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" class="md-link" target="_blank" rel="noopener">$1</a>')

  // [REF:n] → 可点击超链接
  const refMap = globalRefMap.value
  html = html.replace(/\[REF:(\d+)\]/g, (match, num) => {
    const url = refMap[num]
    if (url) {
      return `<a href="${escapeHtml(url)}" class="ref-link" target="_blank" rel="noopener" title="${escapeHtml(url)}">[${num}]</a>`
    }
    return `<span class="ref-tag">[${num}]</span>`
  })

  // 无序列表
  html = html.replace(/^\s*[-*]\s+(.+)$/gm, '<li class="md-li">$1</li>')
  html = html.replace(/(<li class="md-li">.*<\/li>\n?)+/g, '<ul class="md-ul">$&</ul>')

  // 有序列表
  html = html.replace(/^\s*\d+\.\s+(.+)$/gm, '<li class="md-oli">$1</li>')
  html = html.replace(/(<li class="md-oli">.*<\/li>\n?)+/g, '<ol class="md-ol">$&</ol>')

  // 引用块
  html = html.replace(/^>\s*(.+)$/gm, '<blockquote class="md-quote">$1</blockquote>')

  // 水平线
  html = html.replace(/^---$/gm, '<hr class="md-hr" />')

  // 段落
  html = html.split('\n\n').map(block => {
    if (block.match(/^<(h[1-6]|ul|ol|pre|blockquote|hr)/) ||
        block.includes('__CODE_BLOCK_') ||
        block.includes('__MATH_BLOCK_')) {
      return block
    }
    if (block.trim() && !block.match(/^<[a-z]/i)) {
      return `<p class="md-p">${block.replace(/\n/g, '<br>')}</p>`
    }
    return block
  }).join('\n')

  // 恢复代码块
  codeBlocks.forEach((block, i) => {
    const escapedCode = escapeHtml(block.code)
    html = html.replace(
      `__CODE_BLOCK_${i}__`,
      `<pre class="code-block" data-lang="${block.lang}"><code>${escapedCode}</code></pre>`
    )
  })

  // 恢复行内代码
  inlineCodes.forEach((code, i) => {
    html = html.replace(
      `__INLINE_CODE_${i}__`,
      `<code class="inline-code">${escapeHtml(code)}</code>`
    )
  })

  // 恢复数学公式
  mathBlocks.forEach((block, i) => {
    if (block.type === 'block') {
      html = html.replace(
        `__MATH_BLOCK_${i}__`,
        `<div class="math-block">\\[${escapeHtml(block.formula)}\\]</div>`
      )
    } else {
      html = html.replace(
        `__MATH_INLINE_${i}__`,
        `<span class="math-inline">\\(${escapeHtml(block.formula)}\\)</span>`
      )
    }
  })

  return html
}

const parsedContent = computed(() => parseMarkdown(props.message.content))
</script>

<template>
  <!-- 用户消息 -->
  <div v-if="message.role === 'user'" class="w-full py-4 px-6 animate-fade-in flex justify-end">
    <div class="flex gap-3 flex-row-reverse max-w-3xl">
      <!-- 用户头像 -->
      <div class="flex-shrink-0">
        <div class="w-9 h-9 rounded-full flex items-center justify-center shadow-lg shadow-violet-500/20 text-white text-sm font-medium"
             style="background: linear-gradient(135deg, #8b5cf6, #d946ef);">
          U
        </div>
      </div>

      <!-- 消息内容 -->
      <div class="flex flex-col items-end">
        <div class="text-xs font-medium mb-1.5 text-violet-500">You</div>

        <div class="relative group/bubble">
          <!-- 编辑按钮 -->
          <div v-if="!isEditing"
               class="absolute -left-10 top-1/2 -translate-y-1/2 opacity-0 group-hover/bubble:opacity-100 transition-opacity">
            <button @click="startEdit"
                    class="p-1.5 rounded-full hover:bg-gray-100 text-gray-400 hover:text-gray-600 transition-all cursor-pointer"
                    title="编辑消息">
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z"/>
              </svg>
            </button>
          </div>

          <!-- 编辑模式 -->
          <div v-if="isEditing" class="flex flex-col items-end gap-2">
            <textarea
              ref="editTextarea"
              v-model="editContent"
              @keydown.ctrl.enter="submitEdit"
              @keydown.esc="cancelEdit"
              @input="autoResizeTextarea"
              :style="{ width: editBoxWidth + 'px' }"
              class="rounded-2xl px-5 py-2.5 bg-white border-2 border-violet-300 text-gray-900 leading-relaxed resize-none focus:outline-none focus:border-violet-400 overflow-hidden"
            ></textarea>
            <div class="flex items-center gap-2">
              <button @click="submitEdit"
                      :disabled="!editContent.trim()"
                      class="px-3 py-1.5 text-xs bg-violet-500 text-white rounded-full hover:bg-violet-600 transition-colors disabled:opacity-50 cursor-pointer">
                发送
              </button>
              <button @click="cancelEdit"
                      class="text-xs text-gray-400 hover:text-gray-600 transition-colors cursor-pointer">
                取消
              </button>
            </div>
          </div>

          <!-- 正常显示 -->
          <div v-else
               ref="bubbleRef"
               class="rounded-2xl px-6 py-4 bg-violet-100 text-gray-900 leading-relaxed text-sm whitespace-pre-wrap break-words max-w-[600px]">
            {{ message.content }}
          </div>
        </div>
      </div>
    </div>
  </div>

  <!-- AI 消息 -->
  <div v-else-if="message.role === 'assistant'" class="w-full py-4 px-6 animate-fade-in flex justify-start">
    <div class="flex gap-3 max-w-[calc(100%-48px)]">
      <!-- AI 头像 -->
      <div class="flex-shrink-0">
        <div class="w-9 h-9 rounded-xl flex items-center justify-center shadow-lg theme-avatar">
          <span class="text-white text-sm">✨</span>
        </div>
      </div>

      <!-- 消息内容 -->
      <div class="flex flex-col items-start flex-1 min-w-0">
        <div class="text-xs font-medium mb-2 text-indigo-500">{{ message.modelName || 'DeepSeek Reasoner' }}</div>

        <!-- 工具调用时间线 -->
        <div v-if="hasTraceTimeline || shouldShowLegacyReasoning" class="w-full mb-3">
          <template v-if="hasTraceTimeline">
            <div class="trace-timeline">
            <div
              v-for="(turn, turnIndex) in subTurns"
              :key="getTurnKey(turn, turnIndex)"
            >
              <div v-if="turn.reasoning" class="trace-step">
                <div v-if="turn.reasoning.length <= 80" class="trace-row trace-row-static">
                  <span class="trace-label text-slate-400">思考</span>
                  <span class="trace-inline-text">{{ turn.reasoning }}</span>
                </div>
                <template v-else>
                  <button class="trace-row" @click="toggleTurnCollapse(turn, turnIndex)">
                    <svg
                      :class="['w-3 h-3 shrink-0 transition-transform text-slate-400', { 'rotate-90': !isTurnCollapsed(turn, turnIndex) }]"
                      fill="none" stroke="currentColor" viewBox="0 0 24 24"
                    >
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"/>
                    </svg>
                    <span class="trace-label text-slate-400">思考</span>
                    <span class="trace-summary">{{ summarizeText(turn.reasoning) }}</span>
                    <span class="trace-meta">{{ turn.reasoning.length }} 字</span>
                  </button>
                  <Transition name="collapse">
                    <div v-if="!isTurnCollapsed(turn, turnIndex)" class="trace-body">{{ turn.reasoning }}</div>
                  </Transition>
                </template>
              </div>

              <div v-if="turn.toolCall" class="trace-step">
                <div class="trace-row">
                  <span
                    :class="['trace-dot', formatToolStatus(turn.toolCall.status).dotClass, formatToolStatus(turn.toolCall.status).spinning && 'animate-pulse']"
                  ></span>
                  <span class="trace-label font-mono text-slate-700">{{ displayToolName(turn.toolCall) }}</span>
                  <span :class="['trace-meta', formatToolStatus(turn.toolCall.status).textClass]">{{ formatToolStatus(turn.toolCall.status).label }}</span>
                  <span v-if="formatToolDuration(turn.toolCall)" class="trace-meta text-slate-400">{{ formatToolDuration(turn.toolCall) }}</span>
                </div>
                <div v-if="hasToolArguments(turn.toolCall)" class="ml-4 mt-0.5">
                  <button
                    class="trace-toggle"
                    @click="toggleToolArgs(turn.toolCall, getTurnKey(turn, turnIndex))"
                  >
                    <svg
                      :class="['w-3 h-3 transition-transform', { 'rotate-90': !isToolArgsCollapsed(turn.toolCall, getTurnKey(turn, turnIndex)) }]"
                      fill="none" stroke="currentColor" viewBox="0 0 24 24"
                    >
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"/>
                    </svg>
                    参数
                  </button>
                  <Transition name="collapse">
                    <pre
                      v-if="!isToolArgsCollapsed(turn.toolCall, getTurnKey(turn, turnIndex))"
                      class="trace-code"
                    >{{ formatToolArguments(turn.toolCall) }}</pre>
                  </Transition>
                </div>
                <div v-if="formatToolResult(turn.toolCall)" class="ml-4 mt-0.5">
                  <button
                    class="trace-toggle"
                    @click="toggleToolResult(turn.toolCall, getTurnKey(turn, turnIndex))"
                  >
                    <svg
                      :class="['w-3 h-3 transition-transform', { 'rotate-90': !isToolResultCollapsed(turn.toolCall, getTurnKey(turn, turnIndex)) }]"
                      fill="none" stroke="currentColor" viewBox="0 0 24 24"
                    >
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"/>
                    </svg>
                    {{ turn.toolCall.status === 'error' ? '错误' : '结果' }}
                  </button>
                  <Transition name="collapse">
                    <div
                      v-if="!isToolResultCollapsed(turn.toolCall, getTurnKey(turn, turnIndex))"
                      :class="['trace-result-text', turn.toolCall.status === 'error' ? 'text-red-600' : 'text-slate-700']"
                    >{{ formatToolResult(turn.toolCall) }}</div>
                  </Transition>
                </div>
              </div>
            </div>

            <div v-if="currentReasoning" class="trace-step">
              <div class="trace-row">
                <span class="w-2 h-2 rounded-full bg-amber-500 animate-pulse shrink-0"></span>
                <span class="trace-label text-amber-600">思考中...</span>
              </div>
              <div class="trace-body trace-body-live">{{ currentReasoning }}</div>
            </div>

            <div v-if="currentToolCall" class="trace-step">
              <div class="trace-row">
                <span
                  :class="['trace-dot', formatToolStatus(currentToolCall.status).dotClass, formatToolStatus(currentToolCall.status).spinning && 'animate-pulse']"
                ></span>
                <span class="trace-label font-mono text-slate-700">{{ displayToolName(currentToolCall) }}</span>
                <span :class="['trace-meta', formatToolStatus(currentToolCall.status).textClass]">{{ formatToolStatus(currentToolCall.status).label }}</span>
                <span v-if="formatToolDuration(currentToolCall)" class="trace-meta text-slate-400">{{ formatToolDuration(currentToolCall) }}</span>
              </div>
              <div v-if="hasToolArguments(currentToolCall)" class="ml-4 mt-0.5">
                <button
                  class="trace-toggle"
                  @click="toggleToolArgs(currentToolCall, `current-${index}`)"
                >
                  <svg
                    :class="['w-3 h-3 transition-transform', { 'rotate-90': !isToolArgsCollapsed(currentToolCall, `current-${index}`) }]"
                    fill="none" stroke="currentColor" viewBox="0 0 24 24"
                  >
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"/>
                  </svg>
                  参数
                </button>
                <Transition name="collapse">
                  <pre
                    v-if="!isToolArgsCollapsed(currentToolCall, `current-${index}`)"
                    class="trace-code"
                  >{{ formatToolArguments(currentToolCall) }}</pre>
                </Transition>
              </div>
              <div v-if="formatToolResult(currentToolCall)" class="ml-4 mt-0.5">
                <button
                  class="trace-toggle"
                  @click="toggleToolResult(currentToolCall, `current-${index}`)"
                >
                  <svg
                    :class="['w-3 h-3 transition-transform', { 'rotate-90': !isToolResultCollapsed(currentToolCall, `current-${index}`) }]"
                    fill="none" stroke="currentColor" viewBox="0 0 24 24"
                  >
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"/>
                  </svg>
                  {{ currentToolCall.status === 'error' ? '错误' : '结果' }}
                </button>
                <Transition name="collapse">
                  <div
                    v-if="!isToolResultCollapsed(currentToolCall, `current-${index}`)"
                    :class="['trace-result-text', currentToolCall.status === 'error' ? 'text-red-600' : 'text-slate-700']"
                  >{{ formatToolResult(currentToolCall) }}</div>
                </Transition>
              </div>
            </div>
            </div>
          </template>

          <!-- 兼容旧数据结构 -->
          <template v-else-if="shouldShowLegacyReasoning">
            <div class="trace-timeline">
              <div class="trace-step">
                <button @click="emit('toggle-reasoning', index)" class="trace-row">
                  <svg
                    :class="['w-3 h-3 shrink-0 transition-transform text-slate-400', { 'rotate-90': !reasoningCollapsed }]"
                    fill="none" stroke="currentColor" viewBox="0 0 24 24"
                  >
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"/>
                  </svg>
                  <span class="trace-label text-slate-500">思考过程</span>
                  <span v-if="isStreaming && isReasoningPhase" class="trace-meta text-amber-600">思考中...</span>
                  <span v-else class="trace-meta">{{ message.reasoning.length }} 字</span>
                </button>
                <Transition name="collapse">
                  <div v-if="!reasoningCollapsed" class="trace-body">{{ message.reasoning }}</div>
                </Transition>
              </div>
            </div>
          </template>
        </div>

        <!-- 主要内容 -->
        <div
          v-if="message.content || (!isReasoningPhase && isStreaming && !currentReasoning && !currentToolCall && subTurns.length === 0 && !shouldShowLegacyReasoning)"
          class="group relative w-full"
        >
          <div
            v-if="message.content"
            class="markdown-content prose prose-sm max-w-none leading-relaxed text-gray-900"
            v-html="parsedContent"
          ></div>

          <!-- 加载中状态 -->
          <div v-else-if="isStreaming && !message.reasoning" class="flex items-center gap-2 text-gray-400 py-1">
            <div class="flex items-center gap-1">
              <span class="w-2 h-2 bg-violet-400 rounded-full animate-bounce" style="animation-delay: 0ms"></span>
              <span class="w-2 h-2 bg-violet-400 rounded-full animate-bounce" style="animation-delay: 150ms"></span>
              <span class="w-2 h-2 bg-violet-400 rounded-full animate-bounce" style="animation-delay: 300ms"></span>
            </div>
            <span class="text-xs">正在连接...</span>
          </div>

          <!-- AI 消息操作按钮 -->
          <div v-if="message.content && !isStreaming"
               class="flex items-center gap-1 mt-2 text-gray-400 animate-fade-in-soft">
            <button @click="copyContent"
                    class="flex items-center gap-1 px-2 py-1 rounded hover:bg-gray-100 hover:text-gray-600 transition-colors text-xs cursor-pointer">
              <svg v-if="!copied" class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z"/>
              </svg>
              <svg v-else class="w-3.5 h-3.5 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/>
              </svg>
              <span>{{ copied ? '已复制' : '复制' }}</span>
            </button>
            <button @click="emit('regenerate', message.id)"
                    class="flex items-center gap-1 px-2 py-1 rounded hover:bg-gray-100 hover:text-gray-600 transition-colors text-xs cursor-pointer">
              <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"/>
              </svg>
              <span>再次生成</span>
            </button>
          </div>
        </div>

        <!-- 统计信息 -->
        <div v-if="message.stats && message.stats.endTime" class="flex items-center gap-4 mt-2 text-xs text-gray-400 animate-fade-in-soft">
          <span class="flex items-center gap-1">
            <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"/>
            </svg>
            {{ ((message.stats.endTime - message.stats.startTime) / 1000).toFixed(1) }}s
          </span>
          <span>思考 {{ message.stats.reasoningLength }} 字</span>
          <span>回答 {{ message.stats.contentLength }} 字</span>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.animate-fade-in {
  animation: fadeIn 0.3s ease-out;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(8px); }
  to { opacity: 1; transform: translateY(0); }
}

/* 柔和淡入（无位移，避免布局跳动） */
.animate-fade-in-soft {
  animation: fadeInSoft 0.3s ease-out;
}

@keyframes fadeInSoft {
  from { opacity: 0; }
  to { opacity: 1; }
}

/* 折叠动画 */
.collapse-enter-active,
.collapse-leave-active {
  transition: all 0.3s ease;
  overflow: hidden;
}
.collapse-enter-from,
.collapse-leave-to {
  opacity: 0;
  max-height: 0;
}

/* 自定义滚动条 */
.custom-scrollbar::-webkit-scrollbar { width: 6px; }
.custom-scrollbar::-webkit-scrollbar-track { background: transparent; }
.custom-scrollbar::-webkit-scrollbar-thumb {
  background: rgba(200, 180, 140, 0.4);
  border-radius: 3px;
}
.custom-scrollbar::-webkit-scrollbar-thumb:hover {
  background: rgba(200, 180, 140, 0.6);
}

/* Theme avatar */
.theme-avatar {
  background: var(--theme-gradient);
  box-shadow: 0 4px 14px var(--theme-shadow);
}

/* === Trace Timeline === */
.trace-timeline {
  border-left: 2px solid #e2e8f0;
  padding-left: 0.875rem;
  margin-left: 0.125rem;
}

.trace-step {
  padding: 0.2rem 0;
}

.trace-row {
  display: flex;
  align-items: center;
  gap: 0.375rem;
  cursor: pointer;
  padding: 0.1rem 0;
}

.trace-label {
  font-size: 0.75rem;
  font-weight: 600;
  flex-shrink: 0;
}

.trace-summary {
  font-size: 0.75rem;
  color: #94a3b8;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  min-width: 0;
}

.trace-meta {
  font-size: 0.65rem;
  color: #94a3b8;
  flex-shrink: 0;
}

.trace-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  flex-shrink: 0;
}

.trace-row-static {
  cursor: default;
}

.trace-inline-text {
  font-size: 0.7rem;
  color: #94a3b8;
  line-height: 1.5;
}

.trace-body {
  margin: 0.125rem 0 0.25rem 0;
  padding-left: 1.125rem;
  font-size: 0.7rem;
  line-height: 1.6;
  color: #94a3b8;
  max-height: 14rem;
  overflow-y: auto;
  white-space: pre-wrap;
}

.trace-body-live {
  border-left: 2px solid #f59e0b;
}

.trace-toggle {
  display: flex;
  align-items: center;
  gap: 0.25rem;
  font-size: 0.65rem;
  color: #94a3b8;
  cursor: pointer;
  transition: color 0.15s;
}

.trace-toggle:hover {
  color: #64748b;
}

.trace-code {
  margin: 0.25rem 0;
  padding: 0.4rem 0.5rem;
  background: #f8fafc;
  border-radius: 0.375rem;
  font-size: 0.7rem;
  line-height: 1.5;
  color: #334155;
  white-space: pre-wrap;
  word-break: break-word;
}

.trace-result-label {
  font-size: 0.6rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: #94a3b8;
}

.trace-result-text {
  font-size: 0.75rem;
  line-height: 1.5;
  white-space: pre-wrap;
  word-break: break-word;
}

/* Markdown 样式 */
.markdown-content {
  color: #1f2937;
  line-height: 1.75;
}

.markdown-content :deep(p) {
  margin: 0.75em 0;
}

.markdown-content :deep(h1),
.markdown-content :deep(h2),
.markdown-content :deep(h3),
.markdown-content :deep(h4) {
  font-weight: 600;
  color: #111827;
  margin-top: 1.5em;
  margin-bottom: 0.5em;
}

.markdown-content :deep(h1) { font-size: 1.5em; }
.markdown-content :deep(h2) { font-size: 1.25em; }
.markdown-content :deep(h3) { font-size: 1.1em; }

.markdown-content :deep(ul),
.markdown-content :deep(ol) {
  padding-left: 1.5em;
  margin: 0.75em 0;
}

.markdown-content :deep(li) {
  margin: 0.25em 0;
}

.markdown-content :deep(ul) {
  list-style-type: disc;
}

.markdown-content :deep(ul ul) {
  list-style-type: circle;
}

.markdown-content :deep(strong) {
  font-weight: 600;
  color: #111827;
}

.markdown-content :deep(em) {
  font-style: italic;
  color: #4b5563;
}

.markdown-content :deep(a) {
  color: #7c3aed;
  text-decoration: none;
  border-bottom: 1px solid transparent;
  transition: border-color 0.2s;
}

.markdown-content :deep(a:hover) {
  border-bottom-color: #7c3aed;
}

/* 行内代码 */
.markdown-content :deep(code:not(pre code)),
.markdown-content :deep(.inline-code) {
  background: linear-gradient(135deg, #f3e8ff, #ede9fe);
  color: #6d28d9;
  padding: 0.15em 0.4em;
  border-radius: 0.25em;
  font-size: 0.9em;
  font-family: 'SF Mono', 'Monaco', 'Menlo', monospace;
}

/* 代码块 */
.markdown-content :deep(pre),
.markdown-content :deep(.code-block) {
  background: linear-gradient(135deg, #1e1e2e, #2d2d3d);
  border-radius: 0.75em;
  padding: 1em;
  margin: 1em 0;
  overflow-x: auto;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
}

.markdown-content :deep(pre code),
.markdown-content :deep(.code-block code) {
  background: transparent;
  color: #e2e8f0;
  padding: 0;
  font-size: 0.875em;
  line-height: 1.7;
  font-family: 'SF Mono', 'Monaco', 'Menlo', monospace;
}

/* 引用块 */
.markdown-content :deep(blockquote),
.markdown-content :deep(.md-quote) {
  border-left: 4px solid #a78bfa;
  background: linear-gradient(135deg, #f5f3ff, #faf5ff);
  padding: 0.75em 1em;
  margin: 1em 0;
  border-radius: 0 0.5em 0.5em 0;
  color: #4b5563;
}

.markdown-content :deep(blockquote p) {
  margin: 0;
}

/* 水平线 */
.markdown-content :deep(hr) {
  border: none;
  height: 1px;
  background: linear-gradient(90deg, transparent, #d1d5db, transparent);
  margin: 1.5em 0;
}

/* 表格 */
.markdown-content :deep(table) {
  width: 100%;
  border-collapse: collapse;
  margin: 1em 0;
  font-size: 0.9em;
}

.markdown-content :deep(th),
.markdown-content :deep(td) {
  border: 1px solid #e5e7eb;
  padding: 0.5em 0.75em;
  text-align: left;
}

.markdown-content :deep(th) {
  background: linear-gradient(135deg, #f9fafb, #f3f4f6);
  font-weight: 600;
  color: #374151;
}

.markdown-content :deep(tr:nth-child(even)) {
  background-color: #f9fafb;
}

/* 图片 */
.markdown-content :deep(img) {
  max-width: 100%;
  border-radius: 0.5em;
  margin: 1em 0;
}

/* 数学公式样式 */
.markdown-content :deep(.math-block) {
  margin: 0.75rem 0;
  padding: 1rem;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 0.5rem;
  overflow-x: auto;
  text-align: center;
}

.markdown-content :deep(.math-inline) {
  display: inline !important;
  padding: 0 0.1rem;
  white-space: nowrap;
}

.markdown-content :deep(.math-inline mjx-container),
.markdown-content :deep(.math-inline mjx-container[jax="SVG"]),
.markdown-content :deep(.math-inline mjx-container[jax="CHTML"]) {
  display: inline !important;
  margin: 0 !important;
  padding: 0 !important;
  vertical-align: baseline !important;
}

.markdown-content :deep(.math-inline mjx-container svg) {
  display: inline !important;
  vertical-align: middle;
}

.markdown-content :deep(.math-block mjx-container) {
  display: block !important;
  margin: 0 auto;
}

.markdown-content :deep(mjx-container) {
  color: #1f2937 !important;
}

/* 引用标记超链接 */
.markdown-content :deep(.ref-link) {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 0.7em;
  font-weight: 600;
  color: #7c3aed;
  background: #f3e8ff;
  padding: 0.05em 0.35em;
  border-radius: 0.25em;
  text-decoration: none;
  border-bottom: none !important;
  vertical-align: super;
  line-height: 1;
  transition: background 0.15s, color 0.15s;
}

.markdown-content :deep(.ref-link:hover) {
  background: #7c3aed;
  color: #fff;
  border-bottom: none !important;
}

.markdown-content :deep(.ref-tag) {
  display: inline-flex;
  font-size: 0.7em;
  font-weight: 600;
  color: #94a3b8;
  background: #f1f5f9;
  padding: 0.05em 0.35em;
  border-radius: 0.25em;
  vertical-align: super;
  line-height: 1;
}
</style>
