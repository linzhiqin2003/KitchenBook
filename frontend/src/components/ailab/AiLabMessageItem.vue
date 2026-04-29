<script setup>
import { ref, computed, nextTick, watch } from 'vue'
import AiLabReasoningTrace from './AiLabReasoningTrace.vue'

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

// 整体思维链折叠（默认折叠）
const traceCollapsed = ref(true)
// 单个步骤展开
const expandedSteps = ref({})

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

// 是否正在直播（流式生成中）
const isLive = computed(() => {
  return props.isStreaming && (Boolean(currentReasoning.value) || Boolean(currentToolCall.value))
})

// 统一的步骤列表（已完成的 subTurns + 当前流式的）
const steps = computed(() => {
  const result = []
  subTurns.value.forEach((turn, turnIndex) => {
    const baseKey = getTurnKey(turn, turnIndex)
    if (turn.reasoning) {
      result.push({
        id: `${baseKey}-r`,
        kind: 'thinking',
        text: turn.reasoning,
        turn,
        status: 'done',
        live: false
      })
    }
    if (turn.toolCall) {
      result.push({
        id: `${baseKey}-t`,
        kind: 'tool',
        toolCall: turn.toolCall,
        status: turn.toolCall.status,
        live: false
      })
    }
  })
  if (currentReasoning.value) {
    result.push({
      id: 'live-reasoning',
      kind: 'thinking',
      text: currentReasoning.value,
      turn: null,
      status: 'running',
      live: true
    })
  }
  if (currentToolCall.value) {
    result.push({
      id: 'live-tool',
      kind: 'tool',
      toolCall: currentToolCall.value,
      status: currentToolCall.value.status,
      live: currentToolCall.value.status === 'running' || currentToolCall.value.status === 'parsing'
    })
  }
  return result
})

const isStepExpanded = (id) => Boolean(expandedSteps.value[id])
const toggleStep = (id) => {
  expandedSteps.value = { ...expandedSteps.value, [id]: !isStepExpanded(id) }
}

// 当只有一个步骤时，顶层展开后直接显示该步骤的详情，不再嵌套子折叠
const singleStep = computed(() => steps.value.length === 1 ? steps.value[0] : null)

// 折叠态显示的标签：流式中显示当前活动，否则显示总结
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
  // 完成后：按工具类型聚合的概况
  const tools = subTurns.value.filter(t => t.toolCall).map(t => t.toolCall)
  const totalThinkingMs = subTurns.value.reduce((s, t) => {
    if (t.reasoningStartedAt && t.reasoningFinishedAt) {
      return s + (t.reasoningFinishedAt - t.reasoningStartedAt)
    }
    return s
  }, 0)
  const parts = []
  if (totalThinkingMs > 0) {
    parts.push(`thought for ${formatDuration(totalThinkingMs)}`)
  }
  if (tools.length) {
    const counts = {}
    for (const t of tools) {
      const name = t.name || 'tool'
      counts[name] = (counts[name] || 0) + 1
    }
    for (const [name, count] of Object.entries(counts)) {
      parts.push(count > 1 ? `called ${name} ${count}x` : `called ${name}`)
    }
  }
  if (!parts.length) return '已思考'
  return parts.join(', ').replace(/^./, c => c.toUpperCase())
})

// 单步骤的标签
const stepLabel = (step) => {
  if (step.kind === 'thinking') {
    if (step.live) return 'Thinking…'
    return 'Thought'
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

// 把毫秒数格式化为 1.2s / 2m 30s / 1h 5m，自动选择合理单位
const formatDuration = (ms) => {
  if (!Number.isFinite(ms) || ms <= 0) return ''
  const totalSeconds = ms / 1000
  if (totalSeconds < 60) {
    return totalSeconds < 10
      ? `${totalSeconds.toFixed(1)}s`
      : `${Math.round(totalSeconds)}s`
  }
  const totalMinutes = Math.floor(totalSeconds / 60)
  if (totalMinutes < 60) {
    const sec = Math.round(totalSeconds - totalMinutes * 60)
    return sec ? `${totalMinutes}m ${sec}s` : `${totalMinutes}m`
  }
  const hours = Math.floor(totalMinutes / 60)
  const remMin = totalMinutes - hours * 60
  return remMin ? `${hours}h ${remMin}m` : `${hours}h`
}

const stepMeta = (step) => {
  if (step.kind === 'thinking') {
    // 优先用真实耗时；流式中没有 finishedAt 则不显示
    const turn = step.turn
    if (turn?.reasoningStartedAt && turn?.reasoningFinishedAt) {
      return formatDuration(turn.reasoningFinishedAt - turn.reasoningStartedAt)
    }
    return ''
  }
  if (step.kind === 'tool') {
    return formatToolDuration(step.toolCall)
  }
  return ''
}

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

  // 图片 ![alt](url) — 必须在普通链接规则之前，否则 ! 之后的 [](url) 会被先吃掉
  html = html.replace(
    /!\[([^\]]*)\]\(([^)\s]+)(?:\s+"([^"]*)")?\)/g,
    (m, alt, url, title) => {
      const safeUrl = escapeHtml(url)
      const safeAlt = escapeHtml(alt || '')
      const titleAttr = title ? ` title="${escapeHtml(title)}"` : (alt ? ` title="${safeAlt}"` : '')
      return `<a href="${safeUrl}" target="_blank" rel="noopener" class="md-img-link"><img src="${safeUrl}" alt="${safeAlt}"${titleAttr} class="md-img" loading="lazy" /></a>`
    }
  )

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

// 段列表：每段 = 一组 subTurns（思考/工具调用）+ 一段文本。
// AiLabView.normalizeAssistantMessage 已保证 message.segments 一定存在。
const segments = computed(() => Array.isArray(props.message.segments) ? props.message.segments : [])
const isLastSegment = (idx) => idx === segments.value.length - 1
const parseSegmentContent = (text) => parseMarkdown(text || '')

// 用户消息里点击图片附件 → 新窗打开看大图
const openImage = (dataUrl) => {
  if (!dataUrl) return
  try { window.open(dataUrl, '_blank', 'noopener') } catch (e) { /* ignore */ }
}
</script>

<template>
  <!-- 用户消息 -->
  <div v-if="message.role === 'user'" class="w-full py-3 px-6 animate-fade-in flex justify-end" style="font-family: var(--ai-font-body);">
    <div class="flex gap-3 flex-row-reverse max-w-3xl">
      <div class="flex flex-col items-end">
        <div class="relative group/bubble">
          <div v-if="!isEditing"
               class="absolute -left-[4.25rem] top-1/2 -translate-y-1/2 flex items-center gap-1 opacity-0 group-hover/bubble:opacity-100 transition-opacity">
            <button @click="copyContent"
                    class="p-1 rounded-md transition-all cursor-pointer"
                    style="color: var(--theme-400);"
                    title="复制">
              <svg v-if="!copied" class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="1.5">
                <path stroke-linecap="round" stroke-linejoin="round" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z"/>
              </svg>
              <svg v-else class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2" style="color: #16a34a;">
                <path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7"/>
              </svg>
            </button>
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
              style="border: 1px solid var(--ai-accent); color: var(--theme-700); font-size: 15px;"
            ></textarea>
            <div class="flex items-center gap-2">
              <button @click="cancelEdit"
                      class="text-xs transition-colors cursor-pointer" style="color: var(--theme-400);">
                取消
              </button>
              <button @click="submitEdit"
                      :disabled="!editContent.trim()"
                      class="px-3 py-1 text-xs rounded-md transition-colors disabled:opacity-50 cursor-pointer"
                      style="background: var(--theme-700); color: var(--theme-50);">
                发送
              </button>
            </div>
          </div>

          <div v-else
               ref="bubbleRef"
               class="rounded-xl px-4 py-3 leading-relaxed break-words max-w-[600px]"
               style="background: var(--theme-100); color: var(--theme-700); font-size: 15.5px;">
            <!-- 图片附件缩略图 -->
            <div
              v-if="message.fileAttachment && message.fileAttachment.type === 'image' && message.fileAttachment.dataUrl"
              :class="['user-attachment-image', message.content && message.content !== '(图片)' ? 'mb-2' : '']"
            >
              <img
                :src="message.fileAttachment.dataUrl"
                :alt="message.fileAttachment.filename || 'image'"
                @click="openImage(message.fileAttachment.dataUrl)"
              />
            </div>
            <!-- PDF 附件标签 -->
            <div
              v-else-if="message.fileAttachment && message.fileAttachment.type === 'pdf'"
              class="user-attachment-pdf"
              :class="message.content ? 'mb-2' : ''"
            >
              <svg class="w-3.5 h-3.5 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="1.6">
                <path stroke-linecap="round" stroke-linejoin="round" d="M9 12h6m-6 4h6m-7 5h8a2 2 0 002-2V8.5L15.5 3H7a2 2 0 00-2 2v14a2 2 0 002 2zm6-18v5h5"/>
              </svg>
              <span class="truncate">{{ message.fileAttachment.filename || 'document.pdf' }}</span>
              <span v-if="message.fileAttachment.pages" class="opacity-60 shrink-0">· {{ message.fileAttachment.pages }} 页</span>
            </div>
            <!-- 文本内容（"（图片）"占位符不渲染，避免和缩略图重复显示无意义文字） -->
            <div
              v-if="message.content && !(message.fileAttachment?.type === 'image' && message.content === '(图片)')"
              class="whitespace-pre-wrap"
            >{{ message.content }}</div>
          </div>
        </div>
      </div>
    </div>
  </div>

  <!-- AI 消息 -->
  <div v-else-if="message.role === 'assistant'" class="w-full py-3 px-6 animate-fade-in flex justify-start" style="font-family: var(--ai-font-body);">
    <div class="flex gap-3 max-w-[calc(100%-48px)]">
      <div class="flex flex-col items-start flex-1 min-w-0">
        <div class="mb-1.5" style="font-size: 13px; font-weight: 600; color: var(--theme-400); letter-spacing: 0.01em;">{{ message.modelName || 'AI' }}</div>

        <!-- 按 segment 循环：每段 = 一组思考/工具调用 + 该段输出的文字 -->
        <template v-for="(seg, segIdx) in segments" :key="seg.id || segIdx">
          <!-- trace 区：这一段产生的思考/工具调用 -->
          <div class="w-full mb-2">
            <AiLabReasoningTrace
              :segment="seg"
              :is-streaming="isStreaming && isLastSegment(segIdx)"
              :is-reasoning-phase="isReasoningPhase && isLastSegment(segIdx)"
            />
          </div>

          <!-- 内容区：这一段的文字输出 -->
          <div
            v-if="seg.content || (isLastSegment(segIdx) && isStreaming && !isReasoningPhase && !seg.currentReasoning && !seg.currentToolCall && (!seg.subTurns || seg.subTurns.length === 0))"
            class="group relative w-full mb-3"
          >
            <div
              v-if="seg.content"
              class="markdown-content prose prose-sm max-w-none leading-relaxed text-gray-900"
              v-html="parseSegmentContent(seg.content)"
            ></div>

            <!-- 流式起始时尚无任何 trace 也无内容 → 显示三点加载 -->
            <div
              v-else-if="isLastSegment(segIdx) && isStreaming"
              class="flex items-center gap-2 py-1" style="color: var(--theme-400);"
            >
              <div class="flex items-center gap-1">
                <span class="w-1.5 h-1.5 rounded-full animate-bounce" style="background: var(--theme-300); animation-delay: 0ms"></span>
                <span class="w-1.5 h-1.5 rounded-full animate-bounce" style="background: var(--theme-300); animation-delay: 150ms"></span>
                <span class="w-1.5 h-1.5 rounded-full animate-bounce" style="background: var(--theme-300); animation-delay: 300ms"></span>
              </div>
            </div>

            <!-- 操作按钮：仅在最后一段且非流式状态时显示 -->
            <div
              v-if="isLastSegment(segIdx) && seg.content && !isStreaming"
              class="flex items-center gap-1 mt-2 text-gray-400 animate-fade-in-soft"
            >
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
        </template>

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

/* === Trace Header (顶层折叠) === */
.trace-header {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  /* 不截断短标签 — "Running terminal" / "Thinking…" 都要完整显示 */
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
  position: relative;
}

.trace-header:hover {
  background: var(--theme-100);
  color: var(--theme-700);
}

.trace-header-text {
  font-size: 0.78rem;
  font-weight: 500;
  /* 短标签（"Thinking…" / "Running terminal"）保持单行不截断；
     长聚合标签溢出时按词换行，绝不在词中间断字 */
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

.trace-chevron.is-open {
  transform: rotate(90deg);
}

.trace-chevron-sm {
  width: 0.7rem;
  height: 0.7rem;
}

.trace-chevron-end {
  margin-left: auto;
}

/* === 步骤列表 === */
.trace-list {
  width: min(100%, 42rem);
  margin: 0.25rem 0;
  padding: 0.25rem 0;
  position: relative;
  /* 多步骤模式下用 ::before 在 icon 中心位置画一条虚线连接 dots；
     单步骤模式下没有 dots，detail 直接平铺，虚线会穿过文本，所以只在
     trace-list 实际包含 .trace-item 时才渲染线 */
}

.trace-list:has(.trace-item)::before {
  content: '';
  position: absolute;
  /* icon 列：宽 0.85rem 居中于 0.425rem，加上左 padding 0.25rem -> 中心 ≈ 0.675rem */
  left: 0.675rem;
  top: 0.6rem;
  bottom: 0.6rem;
  border-left: 1px dashed var(--theme-200, #d8d8d2);
  pointer-events: none;
}

.trace-item {
  position: relative;
}

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

.trace-item-row:hover {
  background: var(--theme-100);
  color: var(--theme-700);
}

.trace-step-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 0.85rem;
  height: 0.85rem;
  flex-shrink: 0;
}

.trace-icon-check {
  width: 0.8rem;
  height: 0.8rem;
  color: var(--theme-400);
}

.trace-icon-cross {
  width: 0.8rem;
  height: 0.8rem;
  color: #b91c1c;
}

.trace-icon-dot {
  width: 0.32rem;
  height: 0.32rem;
  border-radius: 999px;
  background: var(--theme-300, #c8c8c0);
}

.trace-icon-live {
  width: 0.4rem;
  height: 0.4rem;
  border-radius: 999px;
  background: var(--ai-accent, #3d7cc9);
  animation: progressPulse 1.2s ease-in-out infinite;
}

.trace-step-label {
  font-size: 0.78rem;
  font-weight: 500;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
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

/* === 步骤详情 === */
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
  max-height: 18rem;
  overflow-y: auto;
}

.trace-code {
  margin: 0;
  padding: 0.5rem 0.6rem;
  background: var(--theme-50);
  border: 1px solid var(--theme-200);
  border-radius: 0.45rem;
  font-size: 0.7rem;
  line-height: 1.55;
  color: var(--theme-500);
  font-family: var(--ai-font-mono, ui-monospace, monospace);
  white-space: pre-wrap;
  word-break: break-word;
  max-height: 16rem;
  overflow-y: auto;
}

.trace-result-text {
  padding: 0.4rem 0.55rem;
  background: var(--theme-50, #f8f8f6);
  border-radius: 0.45rem;
  font-size: 0.75rem;
  line-height: 1.6;
  color: var(--theme-600);
  white-space: pre-wrap;
  word-break: break-word;
  max-height: 18rem;
  overflow-y: auto;
}

/* === 字体流光（运行中） === */
.trace-shimmer-text {
  background: linear-gradient(
    90deg,
    var(--theme-400, #9a9a91) 0%,
    var(--theme-400, #9a9a91) 35%,
    var(--theme-700, #2d2d28) 50%,
    var(--theme-400, #9a9a91) 65%,
    var(--theme-400, #9a9a91) 100%
  );
  background-size: 220% 100%;
  -webkit-background-clip: text;
  background-clip: text;
  -webkit-text-fill-color: transparent;
  color: transparent;
  animation: textShimmer 1.8s linear infinite;
}

@keyframes textShimmer {
  0% { background-position: 120% 0; }
  100% { background-position: -120% 0; }
}

/* URL favicon 标签容器 */
.trace-url-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 0.3rem;
  margin: 0;
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
  font-size: 15.5px;
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
  background: var(--theme-50, #f8f8f6);
  border: 1px solid var(--theme-200, #e4e4df);
  border-radius: 8px;
  padding: 0.875em 1em;
  margin: 0.75em 0;
  overflow-x: auto;
}

.markdown-content :deep(pre code),
.markdown-content :deep(.code-block code) {
  background: transparent;
  color: var(--theme-700, #2d2d28);
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

/* === Agent 发的图片（markdown image） === */
.markdown-content :deep(.md-img-link) {
  display: block;            /* inline-block 会留 baseline 间距 */
  margin: 0.5em 0;
  border-radius: 0.5rem;
  overflow: hidden;
  text-decoration: none;
  width: fit-content;
  max-width: 100%;
  line-height: 0;            /* 杀掉文字行高造成的额外间隙 */
  transition: transform 0.15s ease, box-shadow 0.15s ease;
}
.markdown-content :deep(.md-img-link:hover) {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
}
.markdown-content :deep(.md-img) {
  display: block;
  max-width: 100%;
  max-height: 420px;
  width: auto;
  height: auto;
  border-radius: 0.5rem;
  cursor: zoom-in;
}

/* === 用户消息附件 === */
.user-attachment-image img {
  display: block;
  max-width: 100%;
  max-height: 320px;
  border-radius: 0.5rem;
  cursor: zoom-in;
  object-fit: cover;
}

.user-attachment-pdf {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  padding: 0.35rem 0.6rem;
  border-radius: 0.5rem;
  background: rgba(255, 255, 255, 0.55);
  color: var(--theme-700);
  font-size: 13px;
  max-width: 100%;
}
</style>
