<script setup>
import { ref, nextTick, onMounted, computed } from 'vue'
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

// 计算思考时长
const thinkingDuration = computed(() => {
  if (stats.value.startTime && stats.value.endTime) {
    return ((stats.value.endTime - stats.value.startTime) / 1000).toFixed(1)
  }
  return null
})

// 初始欢迎消息
const welcomeMessage = {
  role: 'assistant',
  content: '你好！我是 DeepSeek V3.2 Speciale 🧠\n\n我是一个强大的思考模型，擅长复杂推理和深度分析。你可以问我：\n\n• 数学推理和证明\n• 代码分析和算法设计\n• 逻辑推理和问题解决\n• 深度分析和创意写作\n\n我的思考过程会完整展示给你，让你看到 AI 是如何一步步推理的。',
  reasoning: null,
  type: 'text'
}

onMounted(() => {
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
  <div class="min-h-screen bg-gradient-to-br from-slate-900 via-purple-950 to-slate-900 text-white">
    <!-- 顶部导航 -->
    <header class="sticky top-0 z-30 backdrop-blur-xl bg-slate-900/70 border-b border-purple-500/20">
      <div class="container mx-auto px-4 py-3 flex items-center justify-between">
        <div class="flex items-center gap-3">
          <router-link to="/" class="text-purple-400 hover:text-purple-300 transition-colors">
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 19l-7-7m0 0l7-7m-7 7h18"/>
            </svg>
          </router-link>
          <div class="flex items-center gap-2">
            <div class="w-10 h-10 rounded-xl bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center shadow-lg shadow-purple-500/30">
              <span class="text-xl">🧠</span>
            </div>
            <div>
              <h1 class="text-lg font-bold bg-gradient-to-r from-purple-400 to-pink-400 bg-clip-text text-transparent">
                DeepSeek V3.2 Speciale
              </h1>
              <p class="text-xs text-purple-300/70">思考模型 · 可见推理链</p>
            </div>
          </div>
        </div>
        <button 
          @click="clearChat" 
          class="px-3 py-1.5 text-xs bg-purple-500/20 hover:bg-purple-500/30 border border-purple-500/30 rounded-lg transition-colors flex items-center gap-1.5 cursor-pointer"
        >
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/>
          </svg>
          清空对话
        </button>
      </div>
    </header>
    
    <!-- 主体内容 -->
    <div class="container mx-auto px-4 py-6 flex flex-col" style="height: calc(100vh - 64px);">
      <!-- 消息列表 -->
      <div 
        ref="messagesContainer" 
        class="flex-1 overflow-y-auto space-y-6 pb-4 scrollbar-thin scrollbar-thumb-purple-500/30 scrollbar-track-transparent"
      >
        <TransitionGroup name="message">
          <template v-for="(msg, index) in messages" :key="index">
            <!-- 用户消息 -->
            <div v-if="msg.role === 'user'" class="flex justify-end">
              <div class="max-w-[80%] md:max-w-[60%]">
                <div class="bg-gradient-to-r from-purple-600 to-pink-600 rounded-2xl rounded-br-md px-5 py-3 shadow-lg shadow-purple-500/20">
                  <div class="whitespace-pre-wrap text-sm leading-relaxed">{{ msg.content }}</div>
                </div>
              </div>
            </div>
            
            <!-- AI 消息 -->
            <div v-else-if="msg.role === 'assistant'" class="flex justify-start">
              <div class="max-w-[90%] md:max-w-[75%] space-y-3">
                <!-- 思维链展示 -->
                <div v-if="msg.reasoning" class="relative">
                  <button 
                    @click="toggleReasoning(index)"
                    class="w-full text-left cursor-pointer"
                  >
                    <div class="flex items-center gap-2 px-4 py-2.5 bg-gradient-to-r from-violet-900/50 to-purple-900/50 rounded-t-xl border border-purple-500/30 border-b-0">
                      <div class="w-6 h-6 rounded-full bg-gradient-to-br from-violet-400 to-purple-500 flex items-center justify-center">
                        <span class="text-xs">💭</span>
                      </div>
                      <span class="text-sm font-medium text-purple-300">思维链</span>
                      <span class="text-xs text-purple-400/70 ml-auto flex items-center gap-1">
                        <span v-if="msg.isStreaming && isReasoningPhase" class="flex items-center gap-1">
                          <svg class="w-3 h-3 animate-spin" fill="none" viewBox="0 0 24 24">
                            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                          </svg>
                          思考中...
                        </span>
                        <span v-else>{{ msg.reasoning.length }} 字</span>
                        <svg 
                          class="w-4 h-4 transition-transform" 
                          :class="{ 'rotate-180': !reasoningCollapsed[index] }"
                          fill="none" stroke="currentColor" viewBox="0 0 24 24"
                        >
                          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"/>
                        </svg>
                      </span>
                    </div>
                  </button>
                  <Transition name="collapse">
                    <div 
                      v-if="!reasoningCollapsed[index]"
                      class="bg-slate-900/80 border border-purple-500/30 border-t-0 rounded-b-xl px-4 py-3 max-h-80 overflow-y-auto scrollbar-thin scrollbar-thumb-purple-500/30"
                    >
                      <div class="text-sm text-purple-200/80 leading-relaxed whitespace-pre-wrap font-mono">{{ msg.reasoning }}</div>
                    </div>
                  </Transition>
                </div>
                
                <!-- 主要内容 -->
                <div class="bg-slate-800/80 border border-slate-700/50 rounded-2xl rounded-bl-md px-5 py-3 shadow-lg">
                  <div v-if="msg.content" class="whitespace-pre-wrap text-sm leading-relaxed text-slate-200">{{ msg.content }}</div>
                  
                  <!-- 加载中状态 -->
                  <div v-else-if="msg.isStreaming && !isReasoningPhase" class="flex items-center gap-2 text-purple-300">
                    <div class="flex items-center gap-1">
                      <span class="w-2 h-2 bg-purple-400 rounded-full animate-bounce" style="animation-delay: 0ms"></span>
                      <span class="w-2 h-2 bg-purple-400 rounded-full animate-bounce" style="animation-delay: 150ms"></span>
                      <span class="w-2 h-2 bg-purple-400 rounded-full animate-bounce" style="animation-delay: 300ms"></span>
                    </div>
                    <span class="text-xs">{{ isReasoningPhase ? '深度思考中...' : '准备回答...' }}</span>
                  </div>
                </div>
                
                <!-- 统计信息 -->
                <div v-if="msg.stats && msg.stats.endTime" class="flex items-center gap-4 px-2 text-xs text-purple-400/60">
                  <span class="flex items-center gap-1">
                    <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"/>
                    </svg>
                    {{ ((msg.stats.endTime - msg.stats.startTime) / 1000).toFixed(1) }}s
                  </span>
                  <span class="flex items-center gap-1">
                    <span>💭</span>
                    思考 {{ msg.stats.reasoningLength }} 字
                  </span>
                  <span class="flex items-center gap-1">
                    <span>📝</span>
                    回答 {{ msg.stats.contentLength }} 字
                  </span>
                </div>
              </div>
            </div>
          </template>
        </TransitionGroup>
        
        <!-- 空状态提示 -->
        <div v-if="messages.length <= 1" class="text-center py-8">
          <div class="text-purple-400/50 mb-6">试试这些问题：</div>
          <div class="flex flex-wrap justify-center gap-3">
            <button
              v-for="q in exampleQuestions"
              :key="q.text"
              @click="askExample(q.text)"
              :disabled="isLoading"
              class="px-4 py-2 bg-purple-500/10 hover:bg-purple-500/20 border border-purple-500/30 rounded-xl text-sm text-purple-300 transition-colors disabled:opacity-50 cursor-pointer flex items-center gap-2"
            >
              <span>{{ q.icon }}</span>
              <span>{{ q.text }}</span>
            </button>
          </div>
        </div>
      </div>
      
      <!-- 输入区域 -->
      <div class="shrink-0 pt-4 border-t border-purple-500/20">
        <div class="bg-slate-800/50 rounded-2xl p-3 border border-purple-500/20">
          <div class="flex items-end gap-3">
            <textarea
              v-model="inputMessage"
              @keydown="handleKeydown"
              :disabled="isLoading"
              placeholder="问我任何需要深度思考的问题..."
              rows="2"
              class="flex-1 resize-none bg-transparent border-0 text-sm text-white placeholder-purple-400/50 focus:outline-none focus:ring-0 max-h-32"
            ></textarea>
            <button
              @click="sendMessage"
              :disabled="!inputMessage.trim() || isLoading"
              class="p-3 bg-gradient-to-r from-purple-600 to-pink-600 text-white rounded-xl hover:from-purple-500 hover:to-pink-500 disabled:from-slate-600 disabled:to-slate-600 disabled:cursor-not-allowed transition-all shrink-0 cursor-pointer shadow-lg shadow-purple-500/30 disabled:shadow-none"
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
        <div class="text-center mt-3 text-xs text-purple-400/50">
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
  padding-top: 0;
  padding-bottom: 0;
}

/* 自定义滚动条 */
.scrollbar-thin::-webkit-scrollbar { width: 6px; }
.scrollbar-thin::-webkit-scrollbar-track { background: transparent; }
.scrollbar-thin::-webkit-scrollbar-thumb { 
  background: rgba(168, 85, 247, 0.3); 
  border-radius: 3px; 
}
.scrollbar-thin::-webkit-scrollbar-thumb:hover { 
  background: rgba(168, 85, 247, 0.5); 
}
</style>

