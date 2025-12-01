<script setup>
import { ref, nextTick, onMounted, computed } from 'vue'
import API_BASE_URL from '../config/api'
import { cart } from '../store/cart'

// 聊天状态
const isOpen = ref(false)
const isLoading = ref(false)
const inputMessage = ref('')
const messages = ref([])
const messagesContainer = ref(null)

// 初始欢迎消息
const welcomeMessage = {
  role: 'assistant',
  content: '你好！我是小厨 👨‍🍳 你的专属点餐助手！\n\n我可以帮你：\n🍽️ 查看菜单和推荐菜品\n🛒 帮你加入购物车\n📝 帮你下单\n\n想吃点什么？告诉我你的口味偏好吧~',
  type: 'text'
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
  const toSave = messages.value.slice(-30)
  localStorage.setItem('ai_chat_messages', JSON.stringify(toSave))
}

// 滚动到底部
const scrollToBottom = async () => {
  await nextTick()
  if (messagesContainer.value) {
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
  }
}

// 获取当前购物车信息传给后端
const getCartInfo = () => {
  return cart.items.map(item => ({
    id: item.recipe.id,
    name: item.recipe.title,
    quantity: item.quantity
  }))
}

// 处理 AI 返回的动作
const handleActions = (actions) => {
  for (const action of actions) {
    switch (action.type) {
      case 'add_to_cart':
        // 添加到购物车
        const recipeData = {
          id: action.data.recipe_id,
          title: action.data.recipe_name,
          cover_image: action.data.cover_image
        }
        cart.addItem(recipeData)
        if (action.data.note) {
          cart.updateNote(action.data.recipe_id, action.data.note)
        }
        // 显示成功提示
        messages.value.push({
          role: 'system',
          type: 'action',
          actionType: 'cart_added',
          data: action.data
        })
        break
        
      case 'view_cart':
        // 打开购物车侧边栏
        cart.isOpen = true
        break
        
      case 'place_order':
        // 设置顾客名称并下单
        if (action.data.customer_name) {
          cart.customerName = action.data.customer_name
          cart.submitOrder().then(result => {
            if (result.success) {
              messages.value.push({
                role: 'system',
                type: 'action',
                actionType: 'order_placed',
                data: { orderId: result.orderId }
              })
              saveMessages()
              scrollToBottom()
            }
          })
        }
        break
    }
  }
}

// 发送消息
const sendMessage = async () => {
  const text = inputMessage.value.trim()
  if (!text || isLoading.value) return
  
  // 添加用户消息
  messages.value.push({ role: 'user', content: text, type: 'text' })
  inputMessage.value = ''
  isLoading.value = true
  scrollToBottom()
  
  // 准备发送给 API 的消息（只发送文本消息）
  const apiMessages = messages.value
    .filter(m => m.type === 'text' && (m.role === 'user' || m.role === 'assistant'))
    .map(m => ({ role: m.role, content: m.content }))
  
  try {
    const response = await fetch(`${API_BASE_URL}/api/ai/chat/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ 
        messages: apiMessages,
        cart: getCartInfo()
      })
    })
    
    if (!response.ok) {
      const error = await response.json()
      throw new Error(error.error || '请求失败')
    }
    
    const data = await response.json()
    
    // 添加 AI 回复
    if (data.content) {
      messages.value.push({
        role: 'assistant',
        content: data.content,
        type: 'text'
      })
    }
    
    // 处理动作
    if (data.actions && data.actions.length > 0) {
      handleActions(data.actions)
    }
    
    saveMessages()
    
  } catch (error) {
    messages.value.push({
      role: 'assistant',
      content: `抱歉，我遇到了一点问题 😅\n\n${error.message}\n\n请稍后再试~`,
      type: 'text'
    })
  } finally {
    isLoading.value = false
    scrollToBottom()
  }
}

// 快捷操作
const quickActions = [
  { text: '看看菜单', icon: '📋' },
  { text: '推荐几道菜', icon: '✨' },
  { text: '查看购物车', icon: '🛒' },
]

const sendQuickAction = (text) => {
  inputMessage.value = text
  sendMessage()
}

// 一键添加推荐菜品到购物车
const addRecommendedToCart = (recipe) => {
  inputMessage.value = `我要点 ${recipe.name}`
  sendMessage()
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

// 获取图片URL
const getImageUrl = (path) => {
  if (!path) return null
  if (path.startsWith('http')) return path
  return `${API_BASE_URL}${path}`
}
</script>

<template>
  <div class="fixed bottom-4 right-4 z-50 font-sans">
    <!-- 聊天气泡按钮 -->
    <Transition name="bounce">
      <button
        v-if="!isOpen"
        @click="toggleChat"
        class="w-14 h-14 rounded-full bg-gradient-to-br from-amber-400 via-orange-400 to-amber-500 text-white shadow-lg hover:shadow-xl hover:scale-105 transition-all duration-300 flex items-center justify-center group cursor-pointer border-2 border-amber-300/50"
      >
        <!-- 可爱的小厨师图标 -->
        <svg class="w-8 h-8 group-hover:scale-110 transition-transform drop-shadow-sm" viewBox="0 0 64 64" fill="none">
          <ellipse cx="32" cy="14" rx="16" ry="8" fill="white"/>
          <rect x="18" y="12" width="28" height="12" fill="white"/>
          <ellipse cx="24" cy="10" rx="6" ry="5" fill="white"/>
          <ellipse cx="40" cy="10" rx="6" ry="5" fill="white"/>
          <ellipse cx="32" cy="8" rx="7" ry="6" fill="white"/>
          <circle cx="32" cy="36" r="16" fill="#FFECD2"/>
          <circle cx="26" cy="34" r="3" fill="#4A3728"/>
          <circle cx="38" cy="34" r="3" fill="#4A3728"/>
          <circle cx="27" cy="33" r="1" fill="white"/>
          <circle cx="39" cy="33" r="1" fill="white"/>
          <ellipse cx="22" cy="40" rx="3" ry="2" fill="#FFB5B5" opacity="0.6"/>
          <ellipse cx="42" cy="40" rx="3" ry="2" fill="#FFB5B5" opacity="0.6"/>
          <path d="M27 42 Q32 47 37 42" stroke="#4A3728" stroke-width="2" stroke-linecap="round" fill="none"/>
        </svg>
        <!-- 小气泡提示 -->
        <span class="absolute -top-1 -right-1 w-4 h-4 bg-emerald-500 rounded-full animate-ping"></span>
        <span class="absolute -top-1 -right-1 w-4 h-4 bg-emerald-500 rounded-full flex items-center justify-center">
          <span class="text-[8px] font-bold">AI</span>
        </span>
      </button>
    </Transition>
    
    <!-- 聊天窗口 -->
    <Transition name="chat-window">
      <div
        v-if="isOpen"
        class="w-[340px] sm:w-[400px] h-[560px] bg-white rounded-2xl shadow-2xl flex flex-col overflow-hidden border border-stone-200"
      >
        <!-- 头部 -->
        <div class="bg-gradient-to-r from-amber-500 to-orange-500 text-white px-4 py-3 flex items-center justify-between shrink-0">
          <div class="flex items-center gap-2">
            <div class="w-9 h-9 rounded-full bg-white/20 flex items-center justify-center">
              <svg class="w-7 h-7" viewBox="0 0 64 64" fill="none">
                <ellipse cx="32" cy="14" rx="14" ry="7" fill="white"/>
                <rect x="20" y="12" width="24" height="10" fill="white"/>
                <ellipse cx="25" cy="11" rx="5" ry="4" fill="white"/>
                <ellipse cx="39" cy="11" rx="5" ry="4" fill="white"/>
                <ellipse cx="32" cy="9" rx="6" ry="5" fill="white"/>
                <circle cx="32" cy="34" r="14" fill="#FFECD2"/>
                <circle cx="27" cy="32" r="2.5" fill="#4A3728"/>
                <circle cx="37" cy="32" r="2.5" fill="#4A3728"/>
                <path d="M28 40 Q32 44 36 40" stroke="#4A3728" stroke-width="2" stroke-linecap="round" fill="none"/>
              </svg>
            </div>
            <div>
              <div class="font-semibold text-sm">小厨 AI 点餐助手</div>
              <div class="text-[10px] text-amber-100">可帮你推荐、点餐、下单</div>
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
            <template v-for="(msg, index) in messages" :key="index">
              <!-- 普通文本消息 -->
              <div
                v-if="msg.type === 'text' || !msg.type"
                :class="[
                  'flex',
                  msg.role === 'user' ? 'justify-end' : 'justify-start'
                ]"
              >
                <div
                  :class="[
                    'max-w-[85%] rounded-2xl px-4 py-2.5 text-sm leading-relaxed',
                    msg.role === 'user'
                      ? 'bg-amber-500 text-white rounded-br-md'
                      : 'bg-white text-stone-700 shadow-sm border border-stone-100 rounded-bl-md'
                  ]"
                >
                  <div class="whitespace-pre-wrap">{{ msg.content }}</div>
                </div>
              </div>
              
              <!-- 系统动作消息 - 添加购物车成功 -->
              <div v-else-if="msg.type === 'action' && msg.actionType === 'cart_added'" class="flex justify-center">
                <div class="bg-emerald-50 text-emerald-700 px-4 py-2 rounded-full text-xs flex items-center gap-2 border border-emerald-200">
                  <span>✅</span>
                  <span>{{ msg.data.recipe_name }} 已加入购物车</span>
                </div>
              </div>
              
              <!-- 系统动作消息 - 下单成功 -->
              <div v-else-if="msg.type === 'action' && msg.actionType === 'order_placed'" class="flex justify-center">
                <div class="bg-amber-50 text-amber-700 px-4 py-2 rounded-xl text-xs border border-amber-200">
                  <div class="flex items-center gap-2 font-medium">
                    <span>🎉</span>
                    <span>订单提交成功！</span>
                  </div>
                  <div class="text-amber-600 mt-1">订单号：#{{ msg.data.orderId }}</div>
                </div>
              </div>
            </template>
          </TransitionGroup>
          
          <!-- 加载动画 -->
          <div v-if="isLoading" class="flex justify-start">
            <div class="bg-white text-stone-500 shadow-sm border border-stone-100 rounded-2xl rounded-bl-md px-4 py-3">
              <div class="flex items-center gap-2">
                <div class="flex items-center gap-1">
                  <span class="w-2 h-2 bg-amber-400 rounded-full animate-bounce" style="animation-delay: 0ms"></span>
                  <span class="w-2 h-2 bg-amber-400 rounded-full animate-bounce" style="animation-delay: 150ms"></span>
                  <span class="w-2 h-2 bg-amber-400 rounded-full animate-bounce" style="animation-delay: 300ms"></span>
                </div>
                <span class="text-xs text-stone-400">小厨正在思考...</span>
              </div>
            </div>
          </div>
        </div>
        
        <!-- 快捷操作 -->
        <div class="px-3 py-2 border-t border-stone-100 bg-stone-50 flex gap-2 overflow-x-auto shrink-0">
          <button
            v-for="action in quickActions"
            :key="action.text"
            @click="sendQuickAction(action.text)"
            :disabled="isLoading"
            class="shrink-0 px-3 py-1.5 bg-white border border-stone-200 rounded-full text-xs text-stone-600 hover:bg-amber-50 hover:border-amber-300 hover:text-amber-700 transition-colors disabled:opacity-50 cursor-pointer flex items-center gap-1"
          >
            <span>{{ action.icon }}</span>
            <span>{{ action.text }}</span>
          </button>
        </div>
        
        <!-- 输入区域 -->
        <div class="p-3 border-t border-stone-100 bg-white shrink-0">
          <div class="flex items-end gap-2">
            <textarea
              v-model="inputMessage"
              @keydown="handleKeydown"
              :disabled="isLoading"
              placeholder="告诉小厨你想吃什么..."
              rows="1"
              class="flex-1 resize-none border border-stone-200 rounded-xl px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-amber-500 focus:border-transparent disabled:bg-stone-50 disabled:text-stone-400 max-h-24"
            ></textarea>
            <button
              @click="sendMessage"
              :disabled="!inputMessage.trim() || isLoading"
              class="p-2.5 bg-amber-500 text-white rounded-xl hover:bg-amber-600 disabled:bg-stone-300 disabled:cursor-not-allowed transition-colors shrink-0 cursor-pointer"
            >
              <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8"/>
              </svg>
            </button>
          </div>
          <div class="text-[10px] text-stone-400 text-center mt-2">
            由 DeepSeek AI 驱动 · 可帮你点餐下单
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

/* 横向滚动隐藏滚动条 */
.overflow-x-auto::-webkit-scrollbar {
  display: none;
}
.overflow-x-auto {
  -ms-overflow-style: none;
  scrollbar-width: none;
}
</style>
