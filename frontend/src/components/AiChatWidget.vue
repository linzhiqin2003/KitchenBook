<script setup>
import { ref, nextTick, onMounted, onUnmounted } from 'vue'
import API_BASE_URL from '../config/api'

// 聊天状态
const isOpen = ref(false)
const isLoading = ref(false)
const inputMessage = ref('')
const messages = ref([])
const messagesContainer = ref(null)

// 初始欢迎消息
const welcomeMessage = {
  role: 'assistant',
  content: '你好！我是小厨 👨‍🍳 很高兴为你服务！\n\n想吃点什么？我可以帮你推荐菜品、介绍食材，或者回答关于美食的问题~'
}

onMounted(() => {
  // 加载本地存储的对话历史
  const saved = localStorage.getItem('ai_chat_messages')
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

// 保存对话历史到本地存储
const saveMessages = () => {
  // 只保留最近 20 条消息
  const toSave = messages.value.slice(-20)
  localStorage.setItem('ai_chat_messages', JSON.stringify(toSave))
}

// 滚动到底部
const scrollToBottom = async () => {
  await nextTick()
  if (messagesContainer.value) {
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
  }
}

// 发送消息
const sendMessage = async () => {
  const text = inputMessage.value.trim()
  if (!text || isLoading.value) return
  
  // 添加用户消息
  messages.value.push({ role: 'user', content: text })
  inputMessage.value = ''
  isLoading.value = true
  scrollToBottom()
  
  // 准备发送给 API 的消息（不包括欢迎消息）
  const apiMessages = messages.value
    .filter(m => m !== welcomeMessage || m.role === 'user')
    .map(m => ({ role: m.role, content: m.content }))
  
  // 添加一个空的 AI 消息用于流式填充
  const aiMessageIndex = messages.value.length
  messages.value.push({ role: 'assistant', content: '' })
  
  try {
    const response = await fetch(`${API_BASE_URL}/api/ai/chat/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ messages: apiMessages })
    })
    
    if (!response.ok) {
      const error = await response.json()
      throw new Error(error.error || '请求失败')
    }
    
    // 处理 SSE 流式响应
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
          if (data === '[DONE]') {
            break
          }
          try {
            const parsed = JSON.parse(data)
            if (parsed.content) {
              messages.value[aiMessageIndex].content += parsed.content
              scrollToBottom()
            }
          } catch (e) {
            // 忽略解析错误
          }
        }
      }
    }
    
    saveMessages()
    
  } catch (error) {
    // 移除空的 AI 消息
    messages.value.pop()
    // 显示错误消息
    messages.value.push({
      role: 'assistant',
      content: `抱歉，我遇到了一点问题 😅\n\n${error.message}\n\n请稍后再试~`
    })
  } finally {
    isLoading.value = false
    scrollToBottom()
  }
}

// 清空对话
const clearChat = () => {
  messages.value = [welcomeMessage]
  localStorage.removeItem('ai_chat_messages')
}

// 按回车发送
const handleKeydown = (e) => {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault()
    sendMessage()
  }
}

// 切换打开状态
const toggleChat = () => {
  isOpen.value = !isOpen.value
  if (isOpen.value) {
    nextTick(() => scrollToBottom())
  }
}
</script>

<template>
  <div class="fixed bottom-4 right-4 z-50 font-sans">
    <!-- 聊天气泡按钮 -->
    <Transition name="bounce">
      <button
        v-if="!isOpen"
        @click="toggleChat"
        class="w-14 h-14 rounded-full bg-gradient-to-br from-emerald-500 to-teal-600 text-white shadow-lg hover:shadow-xl hover:scale-105 transition-all duration-300 flex items-center justify-center group cursor-pointer"
      >
        <span class="text-2xl group-hover:scale-110 transition-transform">🤖</span>
        <!-- 小气泡提示 -->
        <span class="absolute -top-1 -right-1 w-4 h-4 bg-amber-400 rounded-full animate-ping"></span>
        <span class="absolute -top-1 -right-1 w-4 h-4 bg-amber-400 rounded-full"></span>
      </button>
    </Transition>
    
    <!-- 聊天窗口 -->
    <Transition name="chat-window">
      <div
        v-if="isOpen"
        class="w-80 sm:w-96 h-[500px] bg-white rounded-2xl shadow-2xl flex flex-col overflow-hidden border border-stone-200"
      >
        <!-- 头部 -->
        <div class="bg-gradient-to-r from-emerald-600 to-teal-600 text-white px-4 py-3 flex items-center justify-between shrink-0">
          <div class="flex items-center gap-2">
            <span class="text-xl">🤖</span>
            <div>
              <div class="font-semibold text-sm">小厨 AI 助手</div>
              <div class="text-[10px] text-emerald-100">随时为您服务</div>
            </div>
          </div>
          <div class="flex items-center gap-1">
            <button
              @click="clearChat"
              class="p-1.5 hover:bg-white/20 rounded-lg transition-colors cursor-pointer"
              title="清空对话"
            >
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/>
              </svg>
            </button>
            <button
              @click="toggleChat"
              class="p-1.5 hover:bg-white/20 rounded-lg transition-colors cursor-pointer"
            >
              <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
              </svg>
            </button>
          </div>
        </div>
        
        <!-- 消息列表 -->
        <div
          ref="messagesContainer"
          class="flex-1 overflow-y-auto p-4 space-y-3 bg-gradient-to-b from-stone-50 to-white"
        >
          <TransitionGroup name="message">
            <div
              v-for="(msg, index) in messages"
              :key="index"
              :class="[
                'flex',
                msg.role === 'user' ? 'justify-end' : 'justify-start'
              ]"
            >
              <div
                :class="[
                  'max-w-[85%] rounded-2xl px-4 py-2.5 text-sm leading-relaxed',
                  msg.role === 'user'
                    ? 'bg-emerald-600 text-white rounded-br-md'
                    : 'bg-white text-stone-700 shadow-sm border border-stone-100 rounded-bl-md'
                ]"
              >
                <div class="whitespace-pre-wrap">{{ msg.content }}</div>
              </div>
            </div>
          </TransitionGroup>
          
          <!-- 加载动画 -->
          <div v-if="isLoading && messages[messages.length - 1]?.content === ''" class="flex justify-start">
            <div class="bg-white text-stone-500 shadow-sm border border-stone-100 rounded-2xl rounded-bl-md px-4 py-3">
              <div class="flex items-center gap-1">
                <span class="w-2 h-2 bg-emerald-400 rounded-full animate-bounce" style="animation-delay: 0ms"></span>
                <span class="w-2 h-2 bg-emerald-400 rounded-full animate-bounce" style="animation-delay: 150ms"></span>
                <span class="w-2 h-2 bg-emerald-400 rounded-full animate-bounce" style="animation-delay: 300ms"></span>
              </div>
            </div>
          </div>
        </div>
        
        <!-- 输入区域 -->
        <div class="p-3 border-t border-stone-100 bg-white shrink-0">
          <div class="flex items-end gap-2">
            <textarea
              v-model="inputMessage"
              @keydown="handleKeydown"
              :disabled="isLoading"
              placeholder="想吃点什么？问问小厨..."
              rows="1"
              class="flex-1 resize-none border border-stone-200 rounded-xl px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent disabled:bg-stone-50 disabled:text-stone-400 max-h-24"
            ></textarea>
            <button
              @click="sendMessage"
              :disabled="!inputMessage.trim() || isLoading"
              class="p-2.5 bg-emerald-600 text-white rounded-xl hover:bg-emerald-700 disabled:bg-stone-300 disabled:cursor-not-allowed transition-colors shrink-0 cursor-pointer"
            >
              <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8"/>
              </svg>
            </button>
          </div>
          <div class="text-[10px] text-stone-400 text-center mt-2">
            由 DeepSeek AI 驱动 · Enter 发送
          </div>
        </div>
      </div>
    </Transition>
  </div>
</template>

<style scoped>
/* 气泡按钮动画 */
.bounce-enter-active {
  animation: bounce-in 0.4s ease-out;
}
.bounce-leave-active {
  animation: bounce-in 0.2s ease-in reverse;
}
@keyframes bounce-in {
  0% { transform: scale(0); opacity: 0; }
  50% { transform: scale(1.1); }
  100% { transform: scale(1); opacity: 1; }
}

/* 聊天窗口动画 */
.chat-window-enter-active {
  animation: chat-in 0.3s ease-out;
}
.chat-window-leave-active {
  animation: chat-in 0.2s ease-in reverse;
}
@keyframes chat-in {
  0% {
    opacity: 0;
    transform: translateY(20px) scale(0.95);
  }
  100% {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}

/* 消息动画 */
.message-enter-active {
  animation: message-in 0.3s ease-out;
}
@keyframes message-in {
  0% {
    opacity: 0;
    transform: translateY(10px);
  }
  100% {
    opacity: 1;
    transform: translateY(0);
  }
}

/* 自定义滚动条 */
.overflow-y-auto::-webkit-scrollbar {
  width: 6px;
}
.overflow-y-auto::-webkit-scrollbar-track {
  background: transparent;
}
.overflow-y-auto::-webkit-scrollbar-thumb {
  background: #d1d5db;
  border-radius: 3px;
}
.overflow-y-auto::-webkit-scrollbar-thumb:hover {
  background: #9ca3af;
}
</style>

