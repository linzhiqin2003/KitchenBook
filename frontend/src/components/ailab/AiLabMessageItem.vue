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

// 整体思维链折叠（非流式默认折叠）
const traceCollapsed = ref(!props.isStreaming)
// 单个工具调用整体折叠
const toolCollapsed = ref({})

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

// 流式结束后自动折叠思维链
watch(() => props.isStreaming, (streaming, wasStreaming) => {
  if (wasStreaming && !streaming && hasTraceTimeline.value) {
    traceCollapsed.value = true
  }
})

// 工具调用整体折叠（完成的默认折叠，进行中的展开）
const isToolCollapsed = (toolCall, fallback = '') => {
  const key = getToolKey(toolCall, fallback)
  if (toolCollapsed.value[key] === undefined) {
    return toolCall?.status === 'success' || toolCall?.status === 'error'
  }
  return toolCollapsed.value[key]
}

const toggleToolCollapse = (toolCall, fallback = '') => {
  const key = getToolKey(toolCall, fallback)
  toolCollapsed.value[key] = !isToolCollapsed(toolCall, fallback)
}

// 折叠时的摘要文字
const traceSummary = computed(() => {
  const tools = subTurns.value.filter(t => t.toolCall)
  if (!tools.length) {
    const total = subTurns.value.reduce((s, t) => s + (t.reasoning?.length || 0), 0)
    return total ? `${total} 字思考` : ''
  }
  const names = [...new Set(tools.map(t => displayToolName(t.toolCall)))]
  if (names.length === 1) {
    return tools.length > 1 ? `${tools.length}x ${names[0]}` : names[0]
  }
  return `${tools.length}次工具调用`
})

const formatToolStatus = (status = 'parsing') => {
  switch (status) {
    case 'running':
      return { label: '执行中', icon: 'dot', iconClass: 'trace-orb-running', textClass: 'trace-pill-muted', cardClass: 'tool-step-running', spinning: true }
    case 'success':
      return { label: '已完成', icon: 'check', iconClass: 'trace-orb-check', textClass: 'trace-pill-muted', cardClass: 'tool-step-success', spinning: false }
    case 'error':
      return { label: '失败', icon: 'cross', iconClass: 'trace-orb-cross', textClass: 'trace-pill-error', cardClass: 'tool-step-error', spinning: false }
    case 'pending':
      return { label: '等待执行', icon: 'dot', iconClass: 'trace-orb-neutral', textClass: 'trace-pill-muted', cardClass: 'tool-step-pending', spinning: false }
    default:
      return { label: '参数拼接中', icon: 'dot', iconClass: 'trace-orb-neutral', textClass: 'trace-pill-muted', cardClass: 'tool-step-parsing', spinning: false }
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

  // 规范化多余空行（3+ 连续换行 → 2 个，避免产生空白段落）
  html = html.replace(/\n{3,}/g, '\n\n')

  // 合并被空行分隔的列表项（确保它们分组到同一个 <ul>/<ol>）
  html = html.replace(/(^\s*[-*]\s+.+$)\n\n+(?=^\s*[-*]\s+)/gm, '$1\n')
  html = html.replace(/(^\s*\d+\.\s+.+$)\n\n+(?=^\s*\d+\.\s+)/gm, '$1\n')

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

  // 引用块 — 合并连续 > 行为一个 blockquote
  html = html.replace(/(^>.*$\n?)+/gm, (block) => {
    const inner = block.split('\n')
      .map(line => line.replace(/^>\s?/, ''))
      .join('\n')
      .trim()
    return `<blockquote class="md-quote">${inner.replace(/\n/g, '<br>')}</blockquote>`
  })

  // 水平线
  html = html.replace(/^---$/gm, '<hr class="md-hr" />')

  // 表格
  html = html.replace(/(^\|.+\|$\n?){2,}/gm, (tableBlock) => {
    const rows = tableBlock.trim().split('\n').filter(r => r.trim())
    if (rows.length < 2) return tableBlock
    if (!/^\|[\s\-:|]+\|$/.test(rows[1])) return tableBlock
    const parseRow = (row) => row.replace(/^\|/, '').replace(/\|$/, '').split('|').map(c => c.trim())
    const headers = parseRow(rows[0])
    const dataRows = rows.slice(2)
    let t = '<table><thead><tr>'
    headers.forEach(h => { t += `<th>${h}</th>` })
    t += '</tr></thead><tbody>'
    dataRows.forEach(row => {
      if (/^\|[\s\-:|]+\|$/.test(row)) return
      const cells = parseRow(row)
      t += '<tr>'
      cells.forEach(c => { t += `<td>${c}</td>` })
      t += '</tr>'
    })
    t += '</tbody></table>'
    return t
  })

  // 段落（过滤空块避免多余间距）
  html = html.split('\n\n').filter(b => b.trim()).map(block => {
    if (block.match(/^<(h[1-6]|ul|ol|pre|blockquote|hr|table|li)/) ||
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

  // 最终清理：移除空段落，合并相邻列表
  html = html.replace(/<p class="md-p">\s*(<br\s*\/?>)?\s*<\/p>/g, '')
  html = html.replace(/<\/ul>\s*<ul class="md-ul">/g, '')
  html = html.replace(/<\/ol>\s*<ol class="md-ol">/g, '')

  return html
}

const parsedContent = computed(() => parseMarkdown(props.message.content))
</script>

<template>
  <!-- 用户消息 -->
  <div v-if="message.role === 'user'" class="w-full py-3 px-6 animate-fade-in flex justify-end" style="font-family: var(--ai-font-body);">
    <div class="flex gap-3 flex-row-reverse max-w-3xl">
      <div class="flex flex-col items-end">
        <div class="relative group/bubble">
          <div v-if="!isEditing"
               class="absolute -left-9 top-1/2 -translate-y-1/2 opacity-0 group-hover/bubble:opacity-100 transition-opacity">
            <button @click="startEdit"
                    class="p-1 rounded-md transition-all cursor-pointer"
                    style="color: var(--theme-400);"
                    title="编辑消息">
              <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="1.5">
                <path stroke-linecap="round" stroke-linejoin="round" d="M16.862 4.487l1.687-1.688a1.875 1.875 0 112.652 2.652L6.832 19.82a4.5 4.5 0 01-1.897 1.13l-2.685.8.8-2.685a4.5 4.5 0 011.13-1.897L16.863 4.487z"/>
              </svg>
            </button>
          </div>

          <div v-if="isEditing" class="flex flex-col items-end gap-2">
            <textarea
              ref="editTextarea"
              v-model="editContent"
              @keydown.ctrl.enter="submitEdit"
              @keydown.esc="cancelEdit"
              @input="autoResizeTextarea"
              :style="{ width: editBoxWidth + 'px' }"
              class="rounded-xl px-4 py-3 bg-white leading-relaxed resize-none focus:outline-none overflow-hidden"
              style="border: 1px solid var(--ai-accent); color: var(--theme-700); font-size: 14px;"
            ></textarea>
            <div class="flex items-center gap-2">
              <button @click="submitEdit"
                      :disabled="!editContent.trim()"
                      class="px-3 py-1 text-xs rounded-md transition-colors disabled:opacity-50 cursor-pointer"
                      style="background: var(--theme-700); color: var(--theme-50);">
                发送
              </button>
              <button @click="cancelEdit"
                      class="text-xs transition-colors cursor-pointer" style="color: var(--theme-400);">
                取消
              </button>
            </div>
          </div>

          <div v-else
               ref="bubbleRef"
               class="rounded-xl px-4 py-3 leading-relaxed whitespace-pre-wrap break-words max-w-[600px]"
               style="background: var(--theme-100); color: var(--theme-700); font-size: 14px;">
            {{ message.content }}
          </div>
        </div>
      </div>
    </div>
  </div>

  <!-- AI 消息 -->
  <div v-else-if="message.role === 'assistant'" class="w-full py-3 px-6 animate-fade-in flex justify-start" style="font-family: var(--ai-font-body);">
    <div class="flex gap-3 max-w-[calc(100%-48px)]">
      <div class="flex flex-col items-start flex-1 min-w-0">
        <div class="mb-1.5" style="font-size: 12px; font-weight: 600; color: var(--theme-400); letter-spacing: 0.01em;">{{ message.modelName || 'AI' }}</div>

        <!-- 工具调用时间线 -->
        <div v-if="hasTraceTimeline || shouldShowLegacyReasoning" class="w-full mb-3">
          <template v-if="hasTraceTimeline">
            <!-- 思维链折叠头 -->
            <button class="trace-header" @click="traceCollapsed = !traceCollapsed">
              <span class="trace-header-icon">
                <svg
                  :class="['w-3.5 h-3.5 shrink-0 transition-transform', { 'rotate-90': !traceCollapsed }]"
                  fill="none" stroke="currentColor" viewBox="0 0 24 24"
                >
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.2" d="M9 5l7 7-7 7"/>
                </svg>
              </span>
              <span class="trace-header-text">
                <span class="trace-header-label">已思考</span>
                <span v-if="traceCollapsed && traceSummary" class="trace-header-summary">{{ traceSummary }}</span>
              </span>
              <span v-if="!traceCollapsed && isStreaming && (currentReasoning || currentToolCall)" class="trace-header-live">Live</span>
            </button>

            <!-- 展开内容 -->
            <Transition name="collapse">
            <div v-if="!traceCollapsed" class="trace-timeline">
            <div
              v-for="(turn, turnIndex) in subTurns"
              :key="getTurnKey(turn, turnIndex)"
            >
              <!-- 思考：直接展示，不折叠 -->
              <div v-if="turn.reasoning" class="trace-step">
                <div v-if="turn.reasoning.length <= 120" class="trace-row trace-row-static trace-row-thought">
                  <span class="trace-kind">思考</span>
                  <span class="trace-inline-text">{{ turn.reasoning }}</span>
                </div>
                <template v-else>
                  <div class="trace-row trace-row-static trace-row-thought">
                    <span class="trace-kind">思考</span>
                    <span class="trace-meta">{{ turn.reasoning.length }} 字</span>
                  </div>
                  <div class="trace-body">{{ turn.reasoning }}</div>
                </template>
              </div>

              <!-- 工具调用：整体折叠 -->
              <div v-if="turn.toolCall" class="trace-step">
                <button
                  :class="['trace-row trace-tool-row', formatToolStatus(turn.toolCall.status).cardClass]"
                  @click="toggleToolCollapse(turn.toolCall, getTurnKey(turn, turnIndex))"
                >
                  <span :class="['trace-tool-orb', formatToolStatus(turn.toolCall.status).iconClass]">
                    <svg v-if="formatToolStatus(turn.toolCall.status).icon === 'check'" viewBox="0 0 12 12" fill="none" stroke="currentColor">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.5 6.5l2.4 2.4L9.5 3.5"/>
                    </svg>
                    <svg v-else-if="formatToolStatus(turn.toolCall.status).icon === 'cross'" viewBox="0 0 12 12" fill="none" stroke="currentColor">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 3l6 6M9 3l-6 6"/>
                    </svg>
                  </span>
                  <span class="trace-tool-main">
                    <span class="trace-tool-name">{{ displayToolName(turn.toolCall) }}</span>
                  </span>
                  <span :class="['trace-status-pill', formatToolStatus(turn.toolCall.status).textClass]">{{ formatToolStatus(turn.toolCall.status).label }}</span>
                  <span v-if="formatToolDuration(turn.toolCall)" class="trace-duration">{{ formatToolDuration(turn.toolCall) }}</span>
                  <svg
                    :class="['trace-row-chevron', { 'rotate-90': !isToolCollapsed(turn.toolCall, getTurnKey(turn, turnIndex)) }]"
                    fill="none" stroke="currentColor" viewBox="0 0 24 24"
                  >
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.2" d="M9 5l7 7-7 7"/>
                  </svg>
                </button>
                <Transition name="collapse">
                  <div v-if="!isToolCollapsed(turn.toolCall, getTurnKey(turn, turnIndex))" class="trace-tool-detail">
                    <pre v-if="hasToolArguments(turn.toolCall)" class="trace-code">{{ formatToolArguments(turn.toolCall) }}</pre>
                    <div v-if="formatToolResult(turn.toolCall)"
                         :class="['trace-result-text', turn.toolCall.status === 'error' ? 'text-red-600' : 'text-slate-700']"
                    >{{ formatToolResult(turn.toolCall) }}</div>
                  </div>
                </Transition>
              </div>
            </div>

            <!-- 当前思考（流式） -->
            <div v-if="currentReasoning" class="trace-step">
              <div class="trace-row trace-row-thought">
                <span class="trace-live-orb"></span>
                <span class="trace-kind trace-kind-live">思考中</span>
              </div>
              <div class="trace-body trace-body-live">{{ currentReasoning }}</div>
            </div>

            <!-- 当前工具调用（流式） -->
            <div v-if="currentToolCall" class="trace-step">
              <div :class="['trace-row trace-tool-row', formatToolStatus(currentToolCall.status).cardClass]">
                <span :class="['trace-tool-orb', formatToolStatus(currentToolCall.status).iconClass, formatToolStatus(currentToolCall.status).spinning && 'animate-pulse']">
                  <svg v-if="formatToolStatus(currentToolCall.status).icon === 'check'" viewBox="0 0 12 12" fill="none" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.5 6.5l2.4 2.4L9.5 3.5"/>
                  </svg>
                  <svg v-else-if="formatToolStatus(currentToolCall.status).icon === 'cross'" viewBox="0 0 12 12" fill="none" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 3l6 6M9 3l-6 6"/>
                  </svg>
                </span>
                <span class="trace-tool-main">
                  <span class="trace-tool-name">{{ displayToolName(currentToolCall) }}</span>
                </span>
                <span :class="['trace-status-pill', formatToolStatus(currentToolCall.status).textClass]">{{ formatToolStatus(currentToolCall.status).label }}</span>
                <span v-if="formatToolDuration(currentToolCall)" class="trace-duration">{{ formatToolDuration(currentToolCall) }}</span>
              </div>
              <!-- 工具执行进度：URL 标签 + 文字 -->
              <template v-if="currentToolCall.status === 'running'">
                <div v-if="currentToolCall.progressUrls && currentToolCall.progressUrls.length" class="trace-url-tags">
                  <span
                    v-for="(u, ui) in currentToolCall.progressUrls"
                    :key="ui"
                    :class="['url-tag', u.status === 'done' ? 'url-tag-done' : u.status === 'fail' ? 'url-tag-fail' : 'url-tag-pending']"
                  >
                    <img
                      :src="`https://www.google.com/s2/favicons?domain=${u.domain}&sz=16`"
                      class="url-tag-icon"
                      loading="lazy"
                      @error="$event.target.style.display='none'"
                    />
                    <span class="url-tag-text">{{ u.domain }}</span>
                    <svg v-if="u.status === 'done'" class="url-tag-check" viewBox="0 0 16 16" fill="currentColor"><path d="M12.207 4.793a1 1 0 0 1 0 1.414l-5 5a1 1 0 0 1-1.414 0l-2.5-2.5a1 1 0 0 1 1.414-1.414L6.5 9.086l4.293-4.293a1 1 0 0 1 1.414 0z"/></svg>
                    <span v-else-if="u.status === 'pending'" class="url-tag-spinner"></span>
                  </span>
                </div>
                <div v-if="currentToolCall.progressMessage" class="trace-progress">
                  <span class="trace-progress-dot"></span>
                  {{ currentToolCall.progressMessage }}
                </div>
              </template>
              <!-- 参数和结果直接展示 -->
              <div v-if="hasToolArguments(currentToolCall)" class="trace-tool-detail">
                <pre class="trace-code">{{ formatToolArguments(currentToolCall) }}</pre>
              </div>
              <div v-if="formatToolResult(currentToolCall)" class="trace-tool-detail">
                <div
                  :class="['trace-result-text', currentToolCall.status === 'error' ? 'text-red-600' : 'text-slate-700']"
                >{{ formatToolResult(currentToolCall) }}</div>
              </div>
            </div>
            </div>
            </Transition>
          </template>

          <!-- 兼容旧数据结构 -->
          <template v-else-if="shouldShowLegacyReasoning">
            <div class="trace-timeline">
              <div class="trace-step">
                <button @click="emit('toggle-reasoning', index)" class="trace-row trace-tool-row">
                  <svg
                    :class="['trace-row-chevron', { 'rotate-90': !reasoningCollapsed }]"
                    fill="none" stroke="currentColor" viewBox="0 0 24 24"
                  >
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.2" d="M9 5l7 7-7 7"/>
                  </svg>
                  <span class="trace-tool-main">
                    <span class="trace-tool-name">已思考</span>
                  </span>
                  <span v-if="isStreaming && isReasoningPhase" class="trace-status-pill text-amber-600">思考中</span>
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
          <div v-else-if="isStreaming && !message.reasoning" class="flex items-center gap-2 py-1" style="color: var(--theme-400);">
            <div class="flex items-center gap-1">
              <span class="w-1.5 h-1.5 rounded-full animate-bounce" style="background: var(--theme-300); animation-delay: 0ms"></span>
              <span class="w-1.5 h-1.5 rounded-full animate-bounce" style="background: var(--theme-300); animation-delay: 150ms"></span>
              <span class="w-1.5 h-1.5 rounded-full animate-bounce" style="background: var(--theme-300); animation-delay: 300ms"></span>
            </div>
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

        <!-- 耗时信息（token 用量统一在底部状态栏展示） -->
        <div v-if="message.stats && message.stats.endTime" class="flex items-center gap-4 mt-2 text-xs text-gray-400 animate-fade-in-soft">
          <span class="flex items-center gap-1">
            <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"/>
            </svg>
            {{ ((message.stats.endTime - message.stats.startTime) / 1000).toFixed(1) }}s
          </span>
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

/* (avatar removed in redesign) */

/* === Trace Header (整体折叠) === */
.trace-header {
  display: flex;
  align-items: center;
  gap: 0.35rem;
  width: min(100%, 42rem);
  padding: 0.18rem 0;
  cursor: pointer;
  user-select: none;
  border: 0;
  background: transparent;
  transition: color 0.16s ease;
}

.trace-header:hover {
  color: var(--theme-600);
}

.trace-header-icon {
  display: grid;
  place-items: center;
  width: 0.95rem;
  height: 0.95rem;
  color: var(--theme-400);
}

.trace-header-text {
  display: flex;
  align-items: baseline;
  gap: 0.45rem;
  min-width: 0;
  flex: 1;
}

.trace-header-label {
  font-size: 0.75rem;
  font-weight: 600;
  color: var(--theme-500);
}

.trace-header-summary {
  font-size: 0.7rem;
  color: var(--theme-400);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  min-width: 0;
}

.trace-header-live {
  font-size: 0.65rem;
  font-weight: 600;
  color: var(--ai-accent);
  padding: 0 0.3rem;
  border-radius: 999px;
  background: var(--ai-accent-soft);
  border: 0;
  animation: progressPulse 1.2s ease-in-out infinite;
}

/* === Trace Timeline === */
.trace-timeline {
  position: relative;
  width: min(100%, 42rem);
  margin-top: 0.2rem;
  padding: 0.15rem 0 0.1rem 0.8rem;
  border-left: 1px solid var(--theme-200, #e4e4df);
  background: transparent;
}

.trace-timeline::before {
  display: none;
}

.trace-step {
  position: relative;
  padding: 0.12rem 0;
}

.trace-row {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  min-height: 1.45rem;
  cursor: pointer;
  padding: 0.08rem 0;
}

.trace-label {
  font-size: 0.75rem;
  font-weight: 600;
  flex-shrink: 0;
}

.trace-meta {
  font-size: 0.65rem;
  color: #94a3b8;
  flex-shrink: 0;
}

.trace-row-static {
  cursor: default;
}

.trace-row-thought {
  align-items: flex-start;
}

.trace-kind {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 1.9rem;
  height: 1.1rem;
  padding: 0;
  color: var(--theme-400);
  background: transparent;
  border: 0;
  font-size: 0.66rem;
  font-weight: 600;
}

.trace-kind-live {
  color: var(--ai-accent);
  background: transparent;
}

.trace-inline-text {
  padding-top: 0.04rem;
  font-size: 0.74rem;
  color: var(--theme-400);
  line-height: 1.65;
}

.trace-body {
  margin: 0.12rem 0 0.35rem 0;
  padding: 0 0 0 2.15rem;
  font-size: 0.74rem;
  line-height: 1.65;
  color: var(--theme-400);
  max-height: 14rem;
  overflow-y: auto;
  white-space: pre-wrap;
  border-radius: 0;
  background: transparent;
  border: 0;
}

.trace-body-live {
  box-shadow: none;
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
  margin: 0;
  padding: 0.45rem 0.55rem;
  background: var(--theme-50);
  border: 1px solid var(--theme-200);
  border-radius: 0.45rem;
  font-size: 0.7rem;
  line-height: 1.55;
  color: var(--theme-500);
  white-space: pre-wrap;
  word-break: break-word;
}

.trace-result-text {
  padding: 0.15rem 0 0 0;
  border-radius: 0;
  background: transparent;
  border: 0;
  font-size: 0.75rem;
  line-height: 1.58;
  white-space: pre-wrap;
  word-break: break-word;
}

.trace-tool-row {
  width: 100%;
  min-width: 0;
  padding: 0.08rem 0;
  border: 0;
  border-radius: 0;
  background: transparent;
  transition: color 0.16s ease;
}

.trace-tool-row:hover {
  transform: none;
  background: transparent;
  box-shadow: none;
}

.trace-tool-main {
  display: flex;
  align-items: baseline;
  gap: 0.5rem;
  min-width: 0;
  flex: 1;
}

.trace-tool-name {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  color: var(--theme-600);
  font-family: var(--ai-font-mono);
  font-size: 0.74rem;
  font-weight: 700;
}

.trace-tool-orb {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 0.42rem;
  height: 0.42rem;
  border-radius: 999px;
  flex-shrink: 0;
  box-shadow: none;
  color: transparent;
}

.trace-tool-orb svg {
  width: 0.7rem;
  height: 0.7rem;
}

/* 中性灰点（pending / parsing） */
.trace-orb-neutral {
  background: var(--theme-300, #c8c8c0);
}

/* 运行中：保留蓝色脉动作为唯一动态强调 */
.trace-orb-running {
  background: #3b82f6;
}

/* 已完成：极小灰色对勾，无填充背景 */
.trace-orb-check {
  width: 0.7rem;
  height: 0.7rem;
  background: transparent;
  color: var(--theme-400, #9a9a91);
}

/* 失败：红色叉，整体仍克制 */
.trace-orb-cross {
  width: 0.7rem;
  height: 0.7rem;
  background: transparent;
  color: #b91c1c;
}

/* 状态文字配色 */
.trace-pill-muted {
  color: var(--theme-400, #9a9a91);
}

.trace-pill-error {
  color: #b91c1c;
}

.trace-status-pill {
  display: inline-flex;
  align-items: center;
  height: auto;
  padding: 0;
  border-radius: 999px;
  background: transparent;
  border: 0;
  font-size: 0.64rem;
  font-weight: 600;
  white-space: nowrap;
}

.trace-duration {
  color: #94a3b8;
  font-size: 0.64rem;
  font-variant-numeric: tabular-nums;
  white-space: nowrap;
}

.trace-row-chevron {
  width: 0.82rem;
  height: 0.82rem;
  color: #94a3b8;
  flex-shrink: 0;
  transition: transform 0.18s ease, color 0.18s ease;
}

.trace-tool-row:hover .trace-row-chevron {
  color: var(--theme-500);
}

.trace-tool-detail {
  display: grid;
  gap: 0.35rem;
  margin: 0.25rem 0 0.25rem 1rem;
}

.trace-live-orb {
  width: 0.42rem;
  height: 0.42rem;
  margin: 0.38rem 0.3rem 0 0.12rem;
  border-radius: 999px;
  background: var(--ai-accent);
  box-shadow: none;
  animation: progressPulse 1.2s ease-in-out infinite;
  flex-shrink: 0;
}

.tool-step-running {
  background: transparent;
}

.tool-step-success {
  background: transparent;
}

.tool-step-error {
  background: transparent;
}

.tool-step-parsing {
  background: transparent;
}

/* URL favicon 标签容器 */
.trace-url-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 0.3rem;
  margin: 0.35rem 0 0.25rem 1rem;
  animation: fadeInSoft 0.2s ease-out;
}

.url-tag {
  display: inline-flex;
  align-items: center;
  gap: 0.25rem;
  padding: 0.15rem 0.45rem 0.15rem 0.3rem;
  border-radius: 999px;
  font-size: 0.65rem;
  line-height: 1;
  white-space: nowrap;
  transition: all 0.25s ease;
}

.url-tag-done {
  background: #ecfdf5;
  color: #059669;
  border: 1px solid #a7f3d0;
}

.url-tag-fail {
  background: #fef2f2;
  color: #b91c1c;
  border: 1px solid #fecaca;
  opacity: 0.7;
}

.url-tag-pending {
  background: #f8fafc;
  color: #94a3b8;
  border: 1px solid #e2e8f0;
  opacity: 0.55;
}

.url-tag-icon {
  width: 12px;
  height: 12px;
  border-radius: 2px;
  flex-shrink: 0;
}

.url-tag-text {
  max-width: 120px;
  overflow: hidden;
  text-overflow: ellipsis;
}

.url-tag-check {
  width: 12px;
  height: 12px;
  color: #10b981;
  flex-shrink: 0;
}

.url-tag-spinner {
  width: 8px;
  height: 8px;
  border: 1.5px solid #cbd5e1;
  border-top-color: #3b82f6;
  border-radius: 50%;
  animation: spin 0.6s linear infinite;
  flex-shrink: 0;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.trace-progress {
  display: flex;
  align-items: center;
  gap: 0.375rem;
  margin: 0.25rem 0 0.125rem 1rem;
  font-size: 0.7rem;
  color: #3b82f6;
  animation: fadeInSoft 0.2s ease-out;
}

.trace-progress-dot {
  width: 5px;
  height: 5px;
  border-radius: 50%;
  background: #3b82f6;
  animation: progressPulse 1.2s ease-in-out infinite;
  flex-shrink: 0;
}

@keyframes progressPulse {
  0%, 100% { opacity: 0.4; transform: scale(0.8); }
  50% { opacity: 1; transform: scale(1.2); }
}

/* Markdown — The Quiet Studio */
.markdown-content {
  color: var(--theme-700, #2d2d28);
  line-height: 1.7;
  font-size: 14px;
}

.markdown-content :deep(p) {
  margin: 0.625em 0;
}

.markdown-content :deep(h1),
.markdown-content :deep(h2),
.markdown-content :deep(h3),
.markdown-content :deep(h4) {
  font-weight: 600;
  color: var(--theme-700, #2d2d28);
  margin-top: 1.25em;
  margin-bottom: 0.4em;
  letter-spacing: -0.01em;
}

.markdown-content :deep(h1) { font-size: 1.4em; }
.markdown-content :deep(h2) { font-size: 1.2em; }
.markdown-content :deep(h3) { font-size: 1.05em; }

.markdown-content :deep(ul),
.markdown-content :deep(ol) {
  padding-left: 1.5em;
  margin: 0.625em 0;
}

.markdown-content :deep(li) { margin: 0.2em 0; }
.markdown-content :deep(ul) { list-style-type: disc; }
.markdown-content :deep(ul ul) { list-style-type: circle; }

.markdown-content :deep(strong) {
  font-weight: 600;
  color: var(--theme-700, #2d2d28);
}

.markdown-content :deep(em) {
  font-style: italic;
  color: var(--theme-500, #6b6b63);
}

.markdown-content :deep(a) {
  color: var(--ai-accent, #3d7cc9);
  text-decoration: none;
  border-bottom: 1px solid transparent;
  transition: border-color 0.2s;
}

.markdown-content :deep(a:hover) {
  border-bottom-color: var(--ai-accent, #3d7cc9);
}

.markdown-content :deep(code:not(pre code)),
.markdown-content :deep(.inline-code) {
  background: var(--theme-100, #f0f0ed);
  color: var(--theme-600, #484843);
  padding: 0.15em 0.35em;
  border-radius: 4px;
  font-size: 0.88em;
  font-family: var(--ai-font-mono, 'Geist Mono', ui-monospace, monospace);
}

.markdown-content :deep(pre),
.markdown-content :deep(.code-block) {
  background: #1c1c1e;
  border-radius: 8px;
  padding: 0.875em 1em;
  margin: 0.75em 0;
  overflow-x: auto;
  border: 1px solid rgba(255,255,255,0.06);
}

.markdown-content :deep(pre code),
.markdown-content :deep(.code-block code) {
  background: transparent;
  color: #d4d4d8;
  padding: 0;
  font-size: 0.85em;
  line-height: 1.65;
  font-family: var(--ai-font-mono, 'Geist Mono', ui-monospace, monospace);
}

.markdown-content :deep(blockquote),
.markdown-content :deep(.md-quote) {
  background: var(--theme-100, #f0f0ed);
  padding: 0.75em 1em;
  margin: 0.75em 0;
  border-radius: 8px;
  color: var(--theme-500, #6b6b63);
}

.markdown-content :deep(blockquote p) { margin: 0; }

.markdown-content :deep(hr) {
  border: none;
  height: 1px;
  background: var(--theme-200, #e4e4df);
  margin: 1.25em 0;
}

.markdown-content :deep(table) {
  width: 100%;
  border-collapse: collapse;
  margin: 0.75em 0;
  font-size: 0.9em;
}

.markdown-content :deep(th),
.markdown-content :deep(td) {
  border: 1px solid var(--theme-200, #e4e4df);
  padding: 0.5em 0.75em;
  text-align: left;
}

.markdown-content :deep(th) {
  background: var(--theme-100, #f0f0ed);
  font-weight: 600;
  color: var(--theme-700, #2d2d28);
}

.markdown-content :deep(tr:nth-child(even)) {
  background: var(--theme-50, #f8f8f6);
}

.markdown-content :deep(img) {
  max-width: 100%;
  border-radius: 8px;
  margin: 0.75em 0;
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
  color: var(--ai-accent, #3d7cc9);
  background: var(--ai-accent-soft, #edf2f8);
  padding: 0.05em 0.35em;
  border-radius: 3px;
  text-decoration: none;
  border-bottom: none !important;
  vertical-align: super;
  line-height: 1;
  transition: background 0.15s, color 0.15s;
}

.markdown-content :deep(.ref-link:hover) {
  background: var(--ai-accent, #3d7cc9);
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
