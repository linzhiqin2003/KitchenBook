<script setup>
import { ref, nextTick, onMounted } from 'vue'
import API_BASE_URL from '../config/api'

// 聊天状态
const isLoading = ref(false)
const inputMessage = ref('')
const messages = ref([])
const messagesContainer = ref(null)

// 当前流式状态
const currentReasoning = ref('')
const currentContent = ref('')
const isReasoningPhase = ref(false)
const isContentPhase = ref(false)
const reasoningCollapsed = ref({}) // 按消息索引存储折叠状态

// 统计信息
const stats = ref({
  reasoningLength: 0,
  contentLength: 0,
  startTime: null,
  endTime: null
})

// HTML 转义
const escapeHtml = (text) => {
  const div = document.createElement('div')
  div.textContent = text
  return div.innerHTML
}

// Markdown 解析器（支持 LaTeX 数学公式）
const parseMarkdown = (markdown) => {
  if (!markdown) return ''
  
  let html = markdown
  
  // 先保存 LaTeX 数学公式块，防止被其他规则处理
  const mathBlocks = []
  // 块级公式 \[ ... \] 或 $$ ... $$
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
  // 行内公式 \( ... \) 或 $ ... $
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
  
  // 先保存代码块，防止被其他规则处理
  const codeBlocks = []
  html = html.replace(/```(\w+)?\n?([\s\S]*?)```/g, (match, lang, code) => {
    const placeholder = `__CODE_BLOCK_${codeBlocks.length}__`
    codeBlocks.push({
      lang: lang || 'text',
      code: code.trim()
    })
    return placeholder
  })
  
  // 行内代码 - 也先保存
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
  
  // 段落 (连续的非空行)
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

// 渲染数学公式
const renderMath = async () => {
  await nextTick()
  if (window.MathJax) {
    window.MathJax.typesetPromise?.()
  }
}

// 初始欢迎消息
const welcomeMessage = {
  role: 'assistant',
  content: '你好！我是 **DeepSeek V3.2 Speciale** 🧠\n\n我是一个强大的思考模型，擅长复杂推理和深度分析。你可以问我：\n\n- 数学推理和证明\n- 代码分析和算法设计\n- 逻辑推理和问题解决\n- 深度分析和创意写作\n\n我的思考过程会完整展示给你，让你看到 AI 是如何一步步推理的。',
  reasoning: null,
  type: 'text'
}

onMounted(() => {
  // 加载 MathJax
  if (!window.MathJax) {
    window.MathJax = {
      tex: {
        inlineMath: [['\\(', '\\)']],
        displayMath: [['\\[', '\\]']],
      },
      svg: {
        fontCache: 'global'
      },
      startup: {
        ready: () => {
          window.MathJax.startup.defaultReady()
        }
      }
    }
    const script = document.createElement('script')
    script.src = 'https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-svg.js'
    script.async = true
    document.head.appendChild(script)
  }
  
  const saved = localStorage.getItem('ai_lab_messages')
  if (saved) {
    try {
      messages.value = JSON.parse(saved)
    } catch (e) {
      messages.value = [welcomeMessage]
    }
  } else {
    messages.value = [welcomeMessage]
  }
  
  // 初始渲染数学公式
  setTimeout(renderMath, 500)
})

const saveMessages = () => {
  const toSave = messages.value.slice(-20) // 保存最近20条
  localStorage.setItem('ai_lab_messages', JSON.stringify(toSave))
}

const scrollToBottom = async () => {
  await nextTick()
  if (messagesContainer.value) {
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
  }
}

// 切换思维链折叠状态
const toggleReasoning = (index) => {
  reasoningCollapsed.value[index] = !reasoningCollapsed.value[index]
}

// 发送消息
const sendMessage = async () => {
  const text = inputMessage.value.trim()
  if (!text || isLoading.value) return
  
  messages.value.push({ role: 'user', content: text, type: 'text' })
  inputMessage.value = ''
  isLoading.value = true
  currentReasoning.value = ''
  currentContent.value = ''
  isReasoningPhase.value = false
  isContentPhase.value = false
  stats.value = { reasoningLength: 0, contentLength: 0, startTime: Date.now(), endTime: null }
  scrollToBottom()
  
  // 构建 API 消息（不包含 reasoning）
  const apiMessages = messages.value
    .filter(m => m.type === 'text' && (m.role === 'user' || m.role === 'assistant'))
    .map(m => ({ role: m.role, content: m.content }))
  
  // 添加一个空的 AI 消息用于流式填充
  const aiMessageIndex = messages.value.length
  messages.value.push({
    role: 'assistant',
    content: '',
    reasoning: '',
    type: 'text',
    isStreaming: true
  })
  
  try {
    const response = await fetch(`${API_BASE_URL}/api/ai/speciale/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ messages: apiMessages })
    })
    
    if (!response.ok) {
      const error = await response.json()
      throw new Error(error.error || '请求失败')
    }
    
    const reader = response.body.getReader()
    const decoder = new TextDecoder()
    
    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      
      const chunk = decoder.decode(value)
      const lines = chunk.split('\n')
      
      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const data = line.slice(6)
          if (data === '[DONE]') break
          
          try {
            const parsed = JSON.parse(data)
            
            switch (parsed.type) {
              case 'status':
                // 状态更新
                break
                
              case 'reasoning_start':
                isReasoningPhase.value = true
                break
                
              case 'reasoning':
                currentReasoning.value += parsed.content
                messages.value[aiMessageIndex].reasoning = currentReasoning.value
                scrollToBottom()
                break
                
              case 'reasoning_end':
                isReasoningPhase.value = false
                break
                
              case 'content_start':
                isContentPhase.value = true
                break
                
              case 'content':
                currentContent.value += parsed.content
                messages.value[aiMessageIndex].content = currentContent.value
                scrollToBottom()
                renderMath()
                break
                
              case 'done':
                stats.value.reasoningLength = parsed.reasoning_length
                stats.value.contentLength = parsed.content_length
                stats.value.endTime = Date.now()
                break
                
              case 'error':
                throw new Error(parsed.error)
            }
          } catch (e) {
            if (e.message !== 'Unexpected end of JSON input') {
              console.error('Parse error:', e)
            }
          }
        }
      }
    }
    
    messages.value[aiMessageIndex].isStreaming = false
    messages.value[aiMessageIndex].stats = { ...stats.value }
    saveMessages()
    renderMath()
    
  } catch (error) {
    messages.value[aiMessageIndex].content = `抱歉，我遇到了一点问题 😅\n\n${error.message}\n\n请稍后再试~`
    messages.value[aiMessageIndex].reasoning = ''
    messages.value[aiMessageIndex].isStreaming = false
  } finally {
    isLoading.value = false
    isReasoningPhase.value = false
    isContentPhase.value = false
    scrollToBottom()
  }
}

const clearChat = () => {
  messages.value = [welcomeMessage]
  localStorage.removeItem('ai_lab_messages')
  reasoningCollapsed.value = {}
}

const handleKeydown = (e) => {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault()
    sendMessage()
  }
}

// 示例问题
const exampleQuestions = [
  { text: '证明根号2是无理数', icon: '📐' },
  { text: '用动态规划解决背包问题', icon: '💻' },
  { text: '分析量子纠缠的本质', icon: '⚛️' },
  { text: '写一首关于AI的诗', icon: '✨' }
]

const askExample = (text) => {
  inputMessage.value = text
  sendMessage()
}
</script>

<template>
  <div class="h-screen w-screen fixed inset-0 bg-gradient-to-b from-slate-50 to-white text-gray-800 flex flex-col overflow-hidden">
    <!-- 顶部导航栏 -->
    <header class="shrink-0 h-14 bg-white border-b border-gray-200 flex items-center px-4 gap-4 shadow-sm">
      <router-link 
        to="/" 
        class="w-9 h-9 rounded-lg bg-gray-100 hover:bg-gray-200 flex items-center justify-center transition-colors"
        title="返回首页"
      >
        <svg class="w-5 h-5 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 19l-7-7m0 0l7-7m-7 7h18"/>
        </svg>
      </router-link>
      
      <div class="flex items-center gap-3 flex-1">
        <div class="w-9 h-9 rounded-lg bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center shadow-md">
          <span class="text-lg">🧠</span>
        </div>
        <div>
          <h1 class="text-base font-semibold text-gray-800 leading-tight">DeepSeek V3.2 Speciale</h1>
          <p class="text-xs text-gray-400">思考模型 · 可见推理链</p>
        </div>
      </div>
      
      <button 
        @click="clearChat" 
        class="h-9 px-3 text-xs text-gray-500 hover:text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-lg transition-colors flex items-center gap-2 cursor-pointer"
      >
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/>
        </svg>
        <span class="hidden sm:inline">清空对话</span>
      </button>
    </header>
    
    <!-- 消息区域 -->
    <div 
      ref="messagesContainer" 
      class="flex-1 overflow-y-auto px-4 py-6"
    >
      <div class="max-w-4xl mx-auto space-y-6">
        <TransitionGroup name="message">
          <template v-for="(msg, index) in messages" :key="index">
            <!-- 用户消息 -->
            <div v-if="msg.role === 'user'" class="flex justify-end">
              <div class="max-w-[85%] md:max-w-[70%]">
                <div class="bg-indigo-600 text-white rounded-2xl rounded-br-sm px-4 py-3 shadow-md">
                  <div class="whitespace-pre-wrap text-sm leading-relaxed">{{ msg.content }}</div>
                </div>
              </div>
            </div>
            
            <!-- AI 消息 -->
            <div v-else-if="msg.role === 'assistant'" class="flex justify-start">
              <div class="max-w-[95%] md:max-w-[85%] space-y-3">
                <!-- 思维链展示 -->
                <div v-if="msg.reasoning" class="rounded-xl overflow-hidden border border-amber-200 shadow-sm">
                  <button 
                    @click="toggleReasoning(index)"
                    class="w-full text-left cursor-pointer flex items-center gap-2 px-4 py-2.5 bg-amber-50 hover:bg-amber-100 transition-colors"
                  >
                    <div class="w-6 h-6 rounded-full bg-gradient-to-br from-amber-400 to-orange-500 flex items-center justify-center shrink-0">
                      <span class="text-xs">💭</span>
                    </div>
                    <span class="text-sm font-medium text-amber-700">思维链</span>
                    <span class="text-xs text-amber-600/70 ml-auto flex items-center gap-2">
                      <span v-if="msg.isStreaming && isReasoningPhase" class="flex items-center gap-1 text-amber-600">
                        <svg class="w-3 h-3 animate-spin" fill="none" viewBox="0 0 24 24">
                          <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                          <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                        </svg>
                        思考中...
                      </span>
                      <span v-else>{{ msg.reasoning.length }} 字</span>
                      <svg 
                        class="w-4 h-4 transition-transform text-amber-500" 
                        :class="{ 'rotate-180': !reasoningCollapsed[index] }"
                        fill="none" stroke="currentColor" viewBox="0 0 24 24"
                      >
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"/>
                      </svg>
                    </span>
                  </button>
                  <Transition name="collapse">
                    <div 
                      v-if="!reasoningCollapsed[index]"
                      class="bg-amber-50/50 px-4 py-3 max-h-64 overflow-y-auto custom-scrollbar border-t border-amber-200"
                    >
                      <div class="text-gray-600 leading-relaxed whitespace-pre-wrap font-mono text-xs">{{ msg.reasoning }}</div>
                    </div>
                  </Transition>
                </div>
                
                <!-- 主要内容 -->
                <div class="bg-white rounded-2xl rounded-bl-sm px-4 py-3 border border-gray-200 shadow-sm">
                  <div 
                    v-if="msg.content" 
                    class="markdown-content text-sm leading-relaxed"
                    v-html="parseMarkdown(msg.content)"
                  ></div>
                  
                  <!-- 加载中状态 -->
                  <div v-else-if="msg.isStreaming" class="flex items-center gap-2 text-gray-400 py-1">
                    <div class="flex items-center gap-1">
                      <span class="w-2 h-2 bg-indigo-400 rounded-full animate-bounce" style="animation-delay: 0ms"></span>
                      <span class="w-2 h-2 bg-indigo-400 rounded-full animate-bounce" style="animation-delay: 150ms"></span>
                      <span class="w-2 h-2 bg-indigo-400 rounded-full animate-bounce" style="animation-delay: 300ms"></span>
                    </div>
                    <span class="text-xs">{{ isReasoningPhase ? '深度思考中...' : '准备回答...' }}</span>
                  </div>
                </div>
                
                <!-- 统计信息 -->
                <div v-if="msg.stats && msg.stats.endTime" class="flex items-center gap-4 px-1 text-xs text-gray-400">
                  <span class="flex items-center gap-1">
                    <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"/>
                    </svg>
                    {{ ((msg.stats.endTime - msg.stats.startTime) / 1000).toFixed(1) }}s
                  </span>
                  <span>💭 思考 {{ msg.stats.reasoningLength }} 字</span>
                  <span>📝 回答 {{ msg.stats.contentLength }} 字</span>
                </div>
              </div>
            </div>
          </template>
        </TransitionGroup>
        
        <!-- 空状态提示 -->
        <div v-if="messages.length <= 1" class="text-center py-12">
          <div class="text-gray-400 mb-8">试试这些问题：</div>
          <div class="flex flex-wrap justify-center gap-3">
            <button
              v-for="q in exampleQuestions"
              :key="q.text"
              @click="askExample(q.text)"
              :disabled="isLoading"
              class="px-4 py-2.5 bg-white hover:bg-gray-50 border border-gray-200 hover:border-gray-300 rounded-xl text-sm text-gray-600 transition-all disabled:opacity-50 cursor-pointer flex items-center gap-2 shadow-sm"
            >
              <span>{{ q.icon }}</span>
              <span>{{ q.text }}</span>
            </button>
          </div>
        </div>
      </div>
    </div>
    
    <!-- 输入区域 -->
    <div class="shrink-0 bg-white border-t border-gray-200 p-4">
      <div class="max-w-4xl mx-auto">
        <div class="bg-gray-50 rounded-xl border border-gray-200 focus-within:border-indigo-400 focus-within:ring-2 focus-within:ring-indigo-100 transition-all">
          <div class="flex items-end gap-3 p-3">
            <textarea
              v-model="inputMessage"
              @keydown="handleKeydown"
              :disabled="isLoading"
              placeholder="问我任何需要深度思考的问题..."
              rows="1"
              class="flex-1 resize-none bg-transparent border-0 text-sm text-gray-800 placeholder-gray-400 focus:outline-none focus:ring-0 max-h-32 min-h-[24px]"
              style="field-sizing: content;"
            ></textarea>
            <button
              @click="sendMessage"
              :disabled="!inputMessage.trim() || isLoading"
              class="w-10 h-10 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg disabled:bg-gray-200 disabled:text-gray-400 disabled:cursor-not-allowed transition-colors shrink-0 cursor-pointer flex items-center justify-center shadow-sm"
            >
              <svg v-if="!isLoading" class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8"/>
              </svg>
              <svg v-else class="w-5 h-5 animate-spin" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
            </button>
          </div>
        </div>
        <div class="text-center mt-2 text-xs text-gray-400">
          由 DeepSeek V3.2 Speciale 驱动 · 思考过程完全可见
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
/* 消息动画 */
.message-enter-active { animation: message-in 0.3s ease-out; }
@keyframes message-in {
  0% { opacity: 0; transform: translateY(10px); }
  100% { opacity: 1; transform: translateY(0); }
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

/* 消息区域滚动条 */
.overflow-y-auto::-webkit-scrollbar { width: 8px; }
.overflow-y-auto::-webkit-scrollbar-track { background: transparent; }
.overflow-y-auto::-webkit-scrollbar-thumb { 
  background: rgba(150, 150, 170, 0.3); 
  border-radius: 4px; 
}
.overflow-y-auto::-webkit-scrollbar-thumb:hover { 
  background: rgba(150, 150, 170, 0.5); 
}

/* Markdown 内容样式 */
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
  border-left: 3px solid #6366f1;
  padding-left: 1rem;
  margin: 0.75rem 0;
  color: #6b7280;
  font-style: italic;
}

.markdown-content :deep(.md-link) {
  color: #4f46e5;
  text-decoration: underline;
  text-underline-offset: 2px;
}

.markdown-content :deep(.md-link:hover) {
  color: #6366f1;
}

.markdown-content :deep(.md-hr) {
  border: none;
  border-top: 1px solid #e5e7eb;
  margin: 1rem 0;
}

.markdown-content :deep(.code-block) {
  background: #1e293b;
  border: 1px solid #334155;
  border-radius: 0.5rem;
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
  background: #f1f5f9;
  color: #6366f1;
  padding: 0.1rem 0.35rem;
  border-radius: 0.25rem;
  font-family: 'JetBrains Mono', 'Fira Code', 'Consolas', monospace;
  font-size: 0.85em;
  border: 1px solid #e2e8f0;
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
  padding: 0 0.2rem;
}

/* MathJax 样式覆盖 */
.markdown-content :deep(mjx-container) {
  color: #1f2937 !important;
}
</style>
