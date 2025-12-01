<script setup>
import { ref, nextTick, onMounted } from 'vue'
import API_BASE_URL from '../config/api'
import { cart } from '../store/cart'

// 聊天状态
const isOpen = ref(false)
const isLoading = ref(false)
const inputMessage = ref('')
const messages = ref([])
const messagesContainer = ref(null)

// 思维链状态（用于当前正在发送的消息）
const currentThinking = ref([])

// 语音录制状态
const isRecording = ref(false)
const isTranscribing = ref(false)
const recordingDuration = ref(0)
let mediaRecorder = null
let audioChunks = []
let recordingTimer = null

// 初始欢迎消息
const welcomeMessage = {
  role: 'assistant',
  content: '你好！我是小厨 👨‍🍳 你的专属点餐助手！\n\n我可以帮你：\n🍽️ 查看菜单和推荐菜品\n🛒 帮你加入购物车\n📝 帮你下单\n\n想吃点什么？告诉我你的口味偏好吧~',
  type: 'text'
}

onMounted(() => {
  const saved = localStorage.getItem('ai_chat_messages')
  if (saved) {
    try {
      const parsed = JSON.parse(saved)
      // 清理可能存在的脏数据
      messages.value = parsed.map(msg => {
        if (msg.role === 'assistant' && msg.content) {
          return { ...msg, content: cleanAiResponse(msg.content) }
        }
        return msg
      })
    } catch (e) {
      messages.value = [welcomeMessage]
    }
  } else {
    messages.value = [welcomeMessage]
  }
})

const saveMessages = () => {
  const toSave = messages.value.slice(-30)
  localStorage.setItem('ai_chat_messages', JSON.stringify(toSave))
}

// 清理 AI 回复中可能出现的工具调用标记 - 更强健的版本
const cleanAiResponse = (text) => {
  if (!text) return text
  
  let cleaned = text
  
  // 1. 匹配 < | DSML | xxx> 格式的完整块（带空格和竖线的变体）- 最重要！
  cleaned = cleaned.replace(/<\s*\|[\s\S]*?<\s*\/\s*\|[^>]*>/gi, '')
  
  // 2. 匹配 <|xxx|> 或 </|xxx|> 或 < | xxx |> 单独标签
  cleaned = cleaned.replace(/<\s*\/?\s*\|[^>]*>/gi, '')
  
  // 3. 移除完整的 DSML 块
  cleaned = cleaned.replace(/<\s*DSML[^>]*>[\s\S]*?<\s*\/\s*DSML[^>]*>/gi, '')
  cleaned = cleaned.replace(/<\s*\/?\s*DSML[^>]*>/gi, '')
  
  // 4. 移除完整的 function_calls 块
  cleaned = cleaned.replace(/<\s*function_calls?\s*>[\s\S]*?<\s*\/\s*function_calls?\s*>/gi, '')
  cleaned = cleaned.replace(/<\s*\/?\s*function_calls?\s*>/gi, '')
  
  // 5. 移除完整的 invoke 块
  cleaned = cleaned.replace(/<\s*invoke[^>]*>[\s\S]*?<\s*\/\s*invoke\s*>/gi, '')
  cleaned = cleaned.replace(/<\s*\/?\s*invoke[^>]*>/gi, '')
  
  // 6. 移除完整的 antml 块
  cleaned = cleaned.replace(/<\s*antml[^>]*>[\s\S]*?<\s*\/\s*antml[^>]*>/gi, '')
  cleaned = cleaned.replace(/<\s*\/?\s*antml[^>]*>/gi, '')
  
  // 7. 移除完整的 tool_call 块
  cleaned = cleaned.replace(/<\s*tool_call[^>]*>[\s\S]*?<\s*\/\s*tool_call\s*>/gi, '')
  cleaned = cleaned.replace(/<\s*\/?\s*tool_call[^>]*>/gi, '')
  
  // 8. 移除 parameter 标签
  cleaned = cleaned.replace(/<\s*\/?\s*parameter[^>]*>/gi, '')
  
  // 9. 移除 <|...|> 格式的特殊标记
  cleaned = cleaned.replace(/<\|[^|]*\|>/g, '')
  
  // 10. 移除 name="..." 或 string="..." 参数残留
  cleaned = cleaned.replace(/\b(name|string)\s*=\s*["'][^"']*["']/gi, '')
  
  // 11. 移除 JSON 代码块残留
  cleaned = cleaned.replace(/```json[\s\S]*?```/gi, '')
  
  // 12. 清理独立的竖线和多余符号
  cleaned = cleaned.replace(/^\s*\|\s*$/gm, '')
  
  // 13. 清理孤立的数字行（参数残留）
  cleaned = cleaned.replace(/^\s*\d+\s*$/gm, '')
  
  // 14. 清理多余空行
  cleaned = cleaned.replace(/\n{3,}/g, '\n\n')
  cleaned = cleaned.replace(/^\s*\n/, '')
  
  // 15. 清理首尾空白
  cleaned = cleaned.trim()
  
  return cleaned
}

// 简单的 Markdown 渲染函数（支持粗体、斜体、列表）
const renderMarkdown = (text) => {
  if (!text) return ''
  
  let html = text
    // 转义 HTML 特殊字符（防止 XSS）
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    // 粗体 **text** 或 __text__
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/__(.+?)__/g, '<strong>$1</strong>')
    // 斜体 *text* 或 _text_（但不匹配已经是粗体的）
    .replace(/(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)/g, '<em>$1</em>')
    .replace(/(?<!_)_(?!_)(.+?)(?<!_)_(?!_)/g, '<em>$1</em>')
    // 行内代码 `code`
    .replace(/`([^`]+)`/g, '<code class="bg-stone-100 px-1 rounded text-amber-700">$1</code>')
    // 换行
    .replace(/\n/g, '<br>')
  
  return html
}

const scrollToBottom = async () => {
  await nextTick()
  if (messagesContainer.value) {
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
  }
}

const getCartInfo = () => {
  return cart.items.map(item => ({
    id: item.recipe.id,
    name: item.recipe.title,
    quantity: item.quantity
  }))
}

// 处理单个动作
const handleAction = (action) => {
  switch (action.type) {
    case 'add_to_cart':
      const recipeData = {
        id: action.data.recipe_id,
        title: action.data.recipe_name,
        cover_image: action.data.cover_image
      }
      cart.addItem(recipeData)
      if (action.data.note) {
        cart.updateNote(action.data.recipe_id, action.data.note)
      }
      messages.value.push({
        role: 'system',
        type: 'action',
        actionType: 'cart_added',
        data: action.data
      })
      break
      
    case 'view_cart':
      cart.isOpen = true
      break
      
    case 'place_order':
      if (action.data.customer_name) {
        cart.customerName = action.data.customer_name
        // 使用静默下单方法，不弹窗不跳转
        cart.submitOrderSilent().then(result => {
          if (result.success) {
            messages.value.push({
              role: 'system',
              type: 'action',
              actionType: 'order_placed',
              data: { orderId: result.orderId }
            })
            saveMessages()
            scrollToBottom()
          } else {
            // 下单失败也要提示
            messages.value.push({
              role: 'system',
              type: 'action',
              actionType: 'order_failed',
              data: { error: result.error }
            })
            saveMessages()
            scrollToBottom()
          }
        })
      }
      break
  }
}

// 获取工具图标和友好名称
const getToolInfo = (tool) => {
  const toolMap = {
    'get_menu': { icon: '📋', name: '查看菜单' },
    'get_recipe_detail': { icon: '🔍', name: '查看菜品详情' },
    'add_to_cart': { icon: '🛒', name: '添加到购物车' },
    'view_cart': { icon: '👀', name: '查看购物车' },
    'place_order': { icon: '📝', name: '提交订单' },
    'get_cart': { icon: '🛒', name: '获取购物车' }
  }
  return toolMap[tool] || { icon: '💭', name: '处理中' }
}

const getToolIcon = (tool) => getToolInfo(tool).icon

// 发送消息（流式处理）
const sendMessage = async () => {
  const text = inputMessage.value.trim()
  if (!text || isLoading.value) return
  
  messages.value.push({ role: 'user', content: text, type: 'text' })
  inputMessage.value = ''
  isLoading.value = true
  currentThinking.value = []
  scrollToBottom()
  
  const apiMessages = messages.value
    .filter(m => m.type === 'text' && (m.role === 'user' || m.role === 'assistant'))
    .map(m => ({ role: m.role, content: m.content }))
  
  // 生成唯一消息 ID
  const messageId = Date.now()
  
  // 添加一个空的 AI 消息用于流式填充
  messages.value.push({
    role: 'assistant',
    content: '',
    type: 'text',
    thinking: [],
    _id: messageId, // 用于追踪这条消息
    _streaming: true // 标记正在流式传输
  })
  
  // 找到当前消息的索引（用函数动态获取，避免索引问题）
  const getAiMessage = () => messages.value.find(m => m._id === messageId)
  
  try {
    const response = await fetch(`${API_BASE_URL}/api/ai/chat/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ 
        messages: apiMessages,
        cart: getCartInfo()
      })
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
            const aiMsg = getAiMessage()
            if (!aiMsg) continue
            
            switch (parsed.type) {
              case 'thinking':
                // 更新思维链
                currentThinking.value.push({
                  text: parsed.content,
                  tool: parsed.tool
                })
                aiMsg.thinking = [...currentThinking.value]
                scrollToBottom()
                break
                
              case 'thinking_done':
                // 思维链完成
                break
                
              case 'content':
                // 流式内容 - 直接追加，最后再清理
                aiMsg.content += parsed.content
                scrollToBottom()
                break
                
              case 'action':
                // 单个动作
                handleAction(parsed.action)
                scrollToBottom()
                break
                
              case 'actions':
                // 批量动作
                for (const action of parsed.actions) {
                  handleAction(action)
                }
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
    
    // 流式结束，清理可能泄露的工具调用标记
    const aiMsg = getAiMessage()
    if (aiMsg) {
      aiMsg.content = cleanAiResponse(aiMsg.content)
      aiMsg._streaming = false
    }
    saveMessages()
    
  } catch (error) {
    const aiMsg = getAiMessage()
    if (aiMsg) {
      aiMsg.content = `抱歉，我遇到了一点问题 😅\n\n${error.message}\n\n请稍后再试~`
      aiMsg.thinking = []
      aiMsg._streaming = false
    }
  } finally {
    isLoading.value = false
    currentThinking.value = []
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

const clearChat = () => {
  messages.value = [welcomeMessage]
  localStorage.removeItem('ai_chat_messages')
}

const handleKeydown = (e) => {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault()
    sendMessage()
  }
}

const toggleChat = () => {
  isOpen.value = !isOpen.value
  if (isOpen.value) {
    nextTick(() => scrollToBottom())
  }
}

// ===== 语音录制功能 =====

const toggleRecording = async () => {
  if (isRecording.value) {
    stopRecording()
  } else {
    await startRecording()
  }
}

const startRecording = async () => {
  try {
    // 检查浏览器支持
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
      if (window.location.protocol !== 'https:' && window.location.hostname !== 'localhost') {
        alert('语音输入需要 HTTPS 安全连接')
      } else {
        alert('您的浏览器不支持语音录制功能')
      }
      return
    }
    
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
    
    // 选择支持的音频格式
    const mimeType = MediaRecorder.isTypeSupported('audio/webm') ? 'audio/webm' : 'audio/mp4'
    mediaRecorder = new MediaRecorder(stream, { mimeType })
    audioChunks = []
    
    mediaRecorder.ondataavailable = (event) => {
      if (event.data.size > 0) {
        audioChunks.push(event.data)
      }
    }
    
    mediaRecorder.onstop = async () => {
      stream.getTracks().forEach(track => track.stop())
      const audioBlob = new Blob(audioChunks, { type: mimeType })
      const duration = recordingDuration.value
      await transcribeAudio(audioBlob, duration)
    }
    
    // 每秒更新录音时长
    recordingTimer = setInterval(() => {
      recordingDuration.value++
      if (recordingDuration.value >= 30) { // 最长 30 秒
        stopRecording()
      }
    }, 1000)
    
    mediaRecorder.start(1000)
    isRecording.value = true
    
  } catch (error) {
    console.error('录音失败:', error)
    if (error.name === 'NotAllowedError') {
      alert('请允许麦克风访问权限')
    } else {
      alert('录音初始化失败')
    }
  }
}

const stopRecording = () => {
  if (mediaRecorder && mediaRecorder.state !== 'inactive') {
    mediaRecorder.stop()
  }
  if (recordingTimer) {
    clearInterval(recordingTimer)
    recordingTimer = null
  }
  isRecording.value = false
}

const transcribeAudio = async (audioBlob, duration = 0) => {
  isTranscribing.value = true
  
  try {
    const formData = new FormData()
    formData.append('audio', audioBlob, 'recording.webm')
    formData.append('duration', duration.toString())
    
    const response = await fetch(`${API_BASE_URL}/api/ai/transcribe/`, {
      method: 'POST',
      body: formData
    })
    
    const data = await response.json()
    
    if (!response.ok) {
      throw new Error(data.error || '转录失败')
    }
    
    if (data.text) {
      inputMessage.value = (inputMessage.value ? inputMessage.value + ' ' : '') + data.text
    }
    
  } catch (error) {
    console.error('转录失败:', error)
    // 静默失败，不弹窗打扰用户
  } finally {
    isTranscribing.value = false
    recordingDuration.value = 0
  }
}

const formatDuration = (seconds) => {
  const mins = Math.floor(seconds / 60)
  const secs = seconds % 60
  return `${mins}:${secs.toString().padStart(2, '0')}`
}
</script>

<template>
  <div class="fixed bottom-16 sm:bottom-20 right-3 sm:right-4 z-50 font-sans">
    <!-- 聊天气泡按钮 -->
    <Transition name="bounce">
      <button
        v-if="!isOpen"
        @click="toggleChat"
        class="w-12 h-12 sm:w-14 sm:h-14 rounded-full bg-gradient-to-br from-amber-400 via-orange-400 to-amber-500 text-white shadow-lg hover:shadow-xl hover:scale-105 transition-all duration-300 flex items-center justify-center group cursor-pointer border-2 border-amber-300/50"
      >
        <svg class="w-7 h-7 sm:w-8 sm:h-8 group-hover:scale-110 transition-transform drop-shadow-sm" viewBox="0 0 64 64" fill="none">
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
        class="fixed sm:relative inset-x-2 sm:inset-auto bottom-2 sm:bottom-auto sm:w-[400px] h-[calc(100dvh-80px)] sm:h-[580px] max-h-[600px] bg-white rounded-2xl shadow-2xl flex flex-col overflow-hidden border border-stone-200"
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
            <button @click="clearChat" class="p-1.5 hover:bg-white/20 rounded-lg transition-colors cursor-pointer" title="清空对话">
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/>
              </svg>
            </button>
            <button @click="toggleChat" class="p-1.5 hover:bg-white/20 rounded-lg transition-colors cursor-pointer">
              <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
              </svg>
            </button>
          </div>
        </div>
        
        <!-- 消息列表 -->
        <div ref="messagesContainer" class="flex-1 overflow-y-auto p-4 space-y-3 bg-gradient-to-b from-stone-50 to-white">
          <TransitionGroup name="message">
            <template v-for="(msg, index) in messages" :key="index">
              <!-- 用户消息 -->
              <div v-if="msg.role === 'user' && msg.type === 'text'" class="flex justify-end">
                <div class="max-w-[85%] bg-amber-500 text-white rounded-2xl rounded-br-md px-4 py-2.5 text-sm leading-relaxed">
                  <div class="whitespace-pre-wrap">{{ msg.content }}</div>
                </div>
              </div>
              
              <!-- AI 消息 -->
              <div v-else-if="msg.role === 'assistant' && (msg.type === 'text' || !msg.type)" class="flex justify-start">
                <div class="max-w-[85%] space-y-2">
                  <!-- 思维链展示 - 简洁版（仅当该消息正在流式传输时显示） -->
                  <Transition name="thinking-fade">
                    <div v-if="msg.thinking && msg.thinking.length > 0 && msg._streaming" class="flex items-center gap-2 px-3 py-2 bg-amber-50/80 rounded-xl border border-amber-100/50">
                      <div class="flex items-center gap-1.5">
                        <div class="w-5 h-5 rounded-full bg-amber-400/20 flex items-center justify-center animate-pulse">
                          <span class="text-xs">{{ getToolIcon(msg.thinking[msg.thinking.length - 1]?.tool) }}</span>
                        </div>
                        <span class="text-xs text-amber-700 font-medium">
                          {{ getToolInfo(msg.thinking[msg.thinking.length - 1]?.tool).name }}...
                        </span>
                      </div>
                      <div class="flex items-center gap-0.5 ml-auto">
                        <span class="w-1.5 h-1.5 bg-amber-400 rounded-full animate-bounce" style="animation-delay: 0ms"></span>
                        <span class="w-1.5 h-1.5 bg-amber-400 rounded-full animate-bounce" style="animation-delay: 100ms"></span>
                        <span class="w-1.5 h-1.5 bg-amber-400 rounded-full animate-bounce" style="animation-delay: 200ms"></span>
                      </div>
                    </div>
                  </Transition>
                  
                  <!-- 完成的操作提示（该消息完成后显示） -->
                  <div v-if="msg.thinking && msg.thinking.length > 0 && !msg._streaming && msg.content" class="flex flex-wrap gap-1.5 mb-1">
                    <span 
                      v-for="(step, stepIdx) in msg.thinking" 
                      :key="stepIdx"
                      class="inline-flex items-center gap-1 px-2 py-0.5 text-[10px] bg-emerald-50 text-emerald-600 rounded-full border border-emerald-100"
                    >
                      <span class="text-emerald-500">✓</span>
                      <span>{{ getToolInfo(step.tool).name }}</span>
                    </span>
                  </div>
                  
                  <!-- 主要内容（支持 Markdown 渲染） -->
                  <div v-if="msg.content" class="bg-white text-stone-700 shadow-sm border border-stone-100 rounded-2xl rounded-bl-md px-4 py-2.5 text-sm leading-relaxed ai-message-content" v-html="renderMarkdown(msg.content)"></div>
                  
                  <!-- 加载中状态（仅当该消息正在流式传输，且没有思维链且没有内容时） -->
                  <div v-else-if="msg._streaming && (!msg.thinking || msg.thinking.length === 0)" class="bg-white text-stone-500 shadow-sm border border-stone-100 rounded-2xl rounded-bl-md px-4 py-3">
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
              
              <!-- 系统动作消息 - 添加购物车成功 -->
              <div v-else-if="msg.type === 'action' && msg.actionType === 'cart_added'" class="flex justify-center">
                <div class="bg-emerald-50 text-emerald-700 px-4 py-2 rounded-full text-xs flex items-center gap-2 border border-emerald-200 shadow-sm">
                  <span>✅</span>
                  <span>{{ msg.data.recipe_name }} 已加入购物车</span>
                </div>
              </div>
              
              <!-- 系统动作消息 - 下单成功 -->
              <div v-else-if="msg.type === 'action' && msg.actionType === 'order_placed'" class="flex justify-center">
                <div class="bg-amber-50 text-amber-700 px-4 py-2 rounded-xl text-xs border border-amber-200 shadow-sm">
                  <div class="flex items-center gap-2 font-medium">
                    <span>🎉</span>
                    <span>订单提交成功！</span>
                  </div>
                  <div class="text-amber-600 mt-1">订单号：#{{ msg.data.orderId }}</div>
                </div>
              </div>
              
              <!-- 系统动作消息 - 下单失败 -->
              <div v-else-if="msg.type === 'action' && msg.actionType === 'order_failed'" class="flex justify-center">
                <div class="bg-red-50 text-red-700 px-4 py-2 rounded-xl text-xs border border-red-200 shadow-sm">
                  <div class="flex items-center gap-2 font-medium">
                    <span>❌</span>
                    <span>下单失败：{{ msg.data.error }}</span>
                  </div>
                </div>
              </div>
            </template>
          </TransitionGroup>
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
        <div class="p-2 sm:p-3 border-t border-stone-100 bg-white shrink-0">
          <div class="flex items-center gap-1.5 sm:gap-2 bg-stone-50 rounded-xl px-2 py-1.5 border border-stone-200 focus-within:border-amber-400 focus-within:ring-2 focus-within:ring-amber-100 transition-all">
            <!-- 语音按钮 -->
            <button
              @click="toggleRecording"
              :disabled="isLoading || isTranscribing"
              :class="[
                'w-8 h-8 rounded-lg transition-all shrink-0 cursor-pointer flex items-center justify-center',
                isRecording 
                  ? 'bg-red-500 hover:bg-red-600 text-white animate-pulse' 
                  : 'bg-amber-100 hover:bg-amber-200 text-amber-600 hover:text-amber-700',
                (isLoading || isTranscribing) && 'opacity-50 cursor-not-allowed'
              ]"
              :title="isRecording ? '停止录音' : '语音输入'"
            >
              <svg v-if="isTranscribing" class="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"></path>
              </svg>
              <svg v-else-if="isRecording" class="w-4 h-4" fill="currentColor" viewBox="0 0 24 24">
                <rect x="6" y="6" width="12" height="12" rx="2"/>
              </svg>
              <svg v-else class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z"/>
              </svg>
            </button>
            
            <!-- 录音时长 -->
            <span v-if="isRecording" class="text-[10px] text-red-500 font-mono min-w-[28px]">
              {{ formatDuration(recordingDuration) }}
            </span>
            
            <textarea
              v-model="inputMessage"
              @keydown="handleKeydown"
              :disabled="isLoading || isRecording"
              :placeholder="isRecording ? '录音中...' : '告诉小厨你想吃什么...'"
              rows="1"
              class="flex-1 resize-none bg-transparent border-0 text-sm focus:outline-none focus:ring-0 disabled:text-stone-400 max-h-20 min-h-[28px] py-1"
              style="field-sizing: content;"
            ></textarea>
            
            <button
              @click="sendMessage"
              :disabled="!inputMessage.trim() || isLoading || isRecording || isTranscribing"
              class="w-8 h-8 bg-amber-500 text-white rounded-lg hover:bg-amber-600 disabled:bg-stone-300 disabled:cursor-not-allowed transition-colors shrink-0 cursor-pointer flex items-center justify-center"
            >
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8"/>
              </svg>
            </button>
          </div>
          <div class="text-[10px] text-stone-400 text-center mt-1.5">
            由 DeepSeek AI 驱动 · 支持语音点餐
          </div>
        </div>
      </div>
    </Transition>
  </div>
</template>

<style scoped>
/* 气泡按钮动画 */
.bounce-enter-active { animation: bounce-in 0.4s ease-out; }
.bounce-leave-active { animation: bounce-in 0.2s ease-in reverse; }
@keyframes bounce-in {
  0% { transform: scale(0); opacity: 0; }
  50% { transform: scale(1.1); }
  100% { transform: scale(1); opacity: 1; }
}

/* 聊天窗口动画 */
.chat-window-enter-active { animation: chat-in 0.3s ease-out; }
.chat-window-leave-active { animation: chat-in 0.2s ease-in reverse; }
@keyframes chat-in {
  0% { opacity: 0; transform: translateY(20px) scale(0.95); }
  100% { opacity: 1; transform: translateY(0) scale(1); }
}

/* 消息动画 */
.message-enter-active { animation: message-in 0.3s ease-out; }
@keyframes message-in {
  0% { opacity: 0; transform: translateY(10px); }
  100% { opacity: 1; transform: translateY(0); }
}

/* 思维链动画 - 简化版 */
.thinking-fade-enter-active { transition: all 0.2s ease-out; }
.thinking-fade-leave-active { transition: all 0.15s ease-in; }
.thinking-fade-enter-from { opacity: 0; transform: scale(0.95); }
.thinking-fade-leave-to { opacity: 0; transform: scale(0.95); }

/* 自定义滚动条 */
.overflow-y-auto::-webkit-scrollbar { width: 6px; }
.overflow-y-auto::-webkit-scrollbar-track { background: transparent; }
.overflow-y-auto::-webkit-scrollbar-thumb { background: #d1d5db; border-radius: 3px; }
.overflow-y-auto::-webkit-scrollbar-thumb:hover { background: #9ca3af; }

.overflow-x-auto::-webkit-scrollbar { display: none; }
.overflow-x-auto { -ms-overflow-style: none; scrollbar-width: none; }

/* AI 消息内容样式 */
.ai-message-content {
  word-break: break-word;
}
.ai-message-content strong {
  font-weight: 600;
  color: #78350f; /* amber-900 */
}
.ai-message-content em {
  font-style: italic;
}
</style>
