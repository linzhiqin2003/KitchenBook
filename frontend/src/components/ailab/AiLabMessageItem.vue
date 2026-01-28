<script setup>
import { ref, computed, nextTick } from 'vue'

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

// 复制状态
const copied = ref(false)

// 进入编辑模式
const startEdit = async () => {
  editContent.value = props.message.content
  isEditing.value = true
  await nextTick()
  editTextarea.value?.focus()
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
  <div v-if="message.role === 'user'" class="flex justify-end w-full group">
    <div class="max-w-[85%] md:max-w-[70%] min-w-[120px] relative">
      <!-- 编辑模式 -->
      <div v-if="isEditing" class="bg-violet-50 rounded-2xl rounded-br-sm px-4 py-3 border-2 border-violet-300">
        <textarea
          ref="editTextarea"
          v-model="editContent"
          class="w-full bg-transparent border-0 text-gray-800 focus:outline-none resize-none text-sm leading-relaxed min-h-[60px]"
          @keydown.enter.exact.prevent="submitEdit"
          @keydown.esc="cancelEdit"
        ></textarea>
        <div class="flex justify-end gap-2 mt-2 pt-2 border-t border-violet-200">
          <button
            @click="cancelEdit"
            class="px-3 py-1.5 text-xs text-gray-500 hover:text-gray-700 cursor-pointer"
          >
            取消
          </button>
          <button
            @click="submitEdit"
            class="px-3 py-1.5 text-xs bg-violet-600 hover:bg-violet-500 text-white rounded-lg cursor-pointer"
          >
            重新发送
          </button>
        </div>
      </div>

      <!-- 正常显示 -->
      <div v-else class="bg-gradient-to-br from-violet-500 to-purple-600 text-white rounded-2xl rounded-br-sm px-4 py-3 shadow-md">
        <div class="whitespace-pre-wrap text-sm leading-relaxed break-words">{{ message.content }}</div>
      </div>

      <!-- 编辑按钮 -->
      <button
        v-if="!isEditing && !isStreaming"
        @click="startEdit"
        class="absolute -left-10 top-1/2 -translate-y-1/2 w-8 h-8 rounded-lg bg-white border border-gray-200 opacity-0 group-hover:opacity-100 hover:bg-gray-50 flex items-center justify-center transition-all cursor-pointer shadow-sm"
        title="编辑消息"
      >
        <svg class="w-4 h-4 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z"/>
        </svg>
      </button>
    </div>
  </div>

  <!-- AI 消息 -->
  <div v-else-if="message.role === 'assistant'" class="flex justify-start w-full">
    <div class="max-w-[95%] md:max-w-[85%] min-w-[200px] space-y-3">
      <!-- 头像和名称 -->
      <div class="flex items-center gap-2">
        <div class="w-8 h-8 rounded-lg bg-gradient-to-br from-violet-500 to-purple-600 flex items-center justify-center shadow-md">
          <span class="text-sm">✨</span>
        </div>
        <span class="text-sm font-medium text-gray-700">DeepSeek Reasoner</span>
      </div>

      <!-- 思维链展示 -->
      <div v-if="message.reasoning" class="rounded-xl overflow-hidden border border-amber-200 shadow-sm">
        <button
          @click="emit('toggle-reasoning', index)"
          class="w-full text-left cursor-pointer flex items-center gap-2 px-4 py-2.5 bg-amber-50 hover:bg-amber-100 transition-colors"
        >
          <div class="w-6 h-6 rounded-full bg-gradient-to-br from-amber-400 to-orange-500 flex items-center justify-center shrink-0">
            <span class="text-xs">💭</span>
          </div>
          <span class="text-sm font-medium text-amber-700">已深度思考</span>
          <span class="text-xs text-amber-600/70 ml-auto flex items-center gap-2">
            <span v-if="isStreaming && isReasoningPhase" class="flex items-center gap-1 text-amber-600">
              <svg class="w-3 h-3 animate-spin" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              思考中...
            </span>
            <span v-else>{{ message.reasoning.length }} 字</span>
            <svg
              class="w-4 h-4 transition-transform text-amber-500"
              :class="{ 'rotate-180': !reasoningCollapsed }"
              fill="none" stroke="currentColor" viewBox="0 0 24 24"
            >
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"/>
            </svg>
          </span>
        </button>
        <Transition name="collapse">
          <div
            v-if="!reasoningCollapsed"
            class="bg-amber-50/50 px-4 py-3 max-h-64 overflow-y-auto custom-scrollbar border-t border-amber-200"
          >
            <div class="text-gray-600 leading-relaxed whitespace-pre-wrap font-mono text-xs">{{ message.reasoning }}</div>
          </div>
        </Transition>
      </div>

      <!-- 主要内容 -->
      <div
        v-if="message.content || (!isReasoningPhase && isStreaming && !message.reasoning)"
        class="group relative bg-white rounded-2xl rounded-tl-sm px-4 py-3 border border-gray-200 shadow-sm"
      >
        <div
          v-if="message.content"
          class="markdown-content text-sm leading-relaxed"
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

        <!-- 操作按钮 -->
        <div
          v-if="message.content && !isStreaming"
          class="absolute -bottom-3 right-4 flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity"
        >
          <button
            @click="copyContent"
            :class="[
              'w-7 h-7 rounded-lg bg-white border border-gray-200 flex items-center justify-center transition-all cursor-pointer shadow-sm',
              copied ? 'text-green-500 border-green-200' : 'hover:bg-gray-50 text-gray-400 hover:text-gray-600'
            ]"
            :title="copied ? '已复制' : '复制'"
          >
            <svg v-if="copied" class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/>
            </svg>
            <svg v-else class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z"/>
            </svg>
          </button>
          <button
            @click="emit('regenerate', message.id)"
            class="w-7 h-7 rounded-lg bg-white border border-gray-200 hover:bg-gray-50 flex items-center justify-center transition-all cursor-pointer shadow-sm text-gray-400 hover:text-gray-600"
            title="重新生成"
          >
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"/>
            </svg>
          </button>
        </div>
      </div>

      <!-- 统计信息 -->
      <div v-if="message.stats && message.stats.endTime" class="flex items-center gap-4 px-1 text-xs text-gray-400">
        <span class="flex items-center gap-1">
          <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"/>
          </svg>
          {{ ((message.stats.endTime - message.stats.startTime) / 1000).toFixed(1) }}s
        </span>
        <span>💭 思考 {{ message.stats.reasoningLength }} 字</span>
        <span>📝 回答 {{ message.stats.contentLength }} 字</span>
      </div>
    </div>
  </div>
</template>

<style scoped>
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

/* Markdown 样式 */
.markdown-content {
  color: #374151;
}

.markdown-content :deep(.md-h1) {
  font-size: 1.5rem;
  font-weight: 700;
  color: #111827;
  margin: 1.25rem 0 0.75rem;
  padding-bottom: 0.5rem;
  border-bottom: 1px solid #e5e7eb;
}

.markdown-content :deep(.md-h2) {
  font-size: 1.25rem;
  font-weight: 600;
  color: #1f2937;
  margin: 1rem 0 0.5rem;
}

.markdown-content :deep(.md-h3) {
  font-size: 1.1rem;
  font-weight: 600;
  color: #374151;
  margin: 0.75rem 0 0.5rem;
}

.markdown-content :deep(.md-h4) {
  font-size: 1rem;
  font-weight: 600;
  color: #4b5563;
  margin: 0.5rem 0 0.25rem;
}

.markdown-content :deep(.md-p) {
  margin: 0.5rem 0;
  line-height: 1.7;
}

.markdown-content :deep(.md-ul),
.markdown-content :deep(.md-ol) {
  margin: 0.5rem 0;
  padding-left: 1.5rem;
}

.markdown-content :deep(.md-li),
.markdown-content :deep(.md-oli) {
  margin: 0.25rem 0;
  line-height: 1.6;
}

.markdown-content :deep(.md-ul) {
  list-style-type: disc;
}

.markdown-content :deep(.md-ol) {
  list-style-type: decimal;
}

.markdown-content :deep(.md-quote) {
  border-left: 3px solid #8b5cf6;
  padding-left: 1rem;
  margin: 0.75rem 0;
  color: #6b7280;
  font-style: italic;
}

.markdown-content :deep(.md-link) {
  color: #7c3aed;
  text-decoration: underline;
  text-underline-offset: 2px;
}

.markdown-content :deep(.md-link:hover) {
  color: #8b5cf6;
}

.markdown-content :deep(.md-hr) {
  border: none;
  border-top: 1px solid #e5e7eb;
  margin: 1rem 0;
}

.markdown-content :deep(.code-block) {
  background: linear-gradient(135deg, #1e1b4b 0%, #312e81 100%);
  border: 1px solid #4c1d95;
  border-radius: 0.75rem;
  padding: 1rem;
  margin: 0.75rem 0;
  overflow-x: auto;
  font-family: 'JetBrains Mono', 'Fira Code', 'Consolas', monospace;
  font-size: 0.8rem;
  line-height: 1.5;
}

.markdown-content :deep(.code-block code) {
  color: #e2e8f0;
}

.markdown-content :deep(.inline-code) {
  background: linear-gradient(135deg, #f5f3ff 0%, #ede9fe 100%);
  color: #7c3aed;
  padding: 0.1rem 0.35rem;
  border-radius: 0.25rem;
  font-family: 'JetBrains Mono', 'Fira Code', 'Consolas', monospace;
  font-size: 0.85em;
  border: 1px solid #ddd6fe;
}

.markdown-content :deep(strong) {
  color: #111827;
  font-weight: 600;
}

.markdown-content :deep(em) {
  color: #4b5563;
  font-style: italic;
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
</style>
