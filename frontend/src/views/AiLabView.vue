<script setup>
import { ref, computed, nextTick, onMounted, onUnmounted, watch } from 'vue'
import API_BASE_URL, { HERMES_API_URL, HERMES_API_KEY } from '../config/api'
import { AiLabSidebar, AiLabWelcome, AiLabInput, AiLabChatArea } from '../components/ailab'
import AiLabPanel from '../components/ailab/AiLabPanel.vue'
import AiLabUserMenu from '../components/ailab/AiLabUserMenu.vue'
import { useRouter } from 'vue-router'

const router = useRouter()
import { useAuthStore } from '../store/auth'

const authStore = useAuthStore()

// 给 Django /api/ai/... 请求带上 JWT —— 后端按 request.user 过滤会话
const djangoHeaders = (extra = {}) => {
  const token = localStorage.getItem('access_token') || ''
  const h = { ...extra }
  if (token) h['Authorization'] = `Bearer ${token}`
  return h
}

// 给 Hermes 请求带上当前用户标识 —— 服务器据此把 memory / config 路径
// scope 到 ~/.hermes/users/<uid>/。无 user 时退回到匿名共享路径。
// session_id 必须按 conversation 隔离 —— 否则用户跨对话切换时 Hermes
// 会把所有消息堆到同一 session，message history 无限累积。memory / config
// 仍然走 user-scope，所以这里多带 conv_id 不影响其他隔离。
const hermesHeaders = (extra = {}) => {
  const uid = authStore.user?.id
  const h = {
    'Authorization': `Bearer ${HERMES_API_KEY}`,
    ...extra,
  }
  if (uid) {
    const cid = currentConversationId.value
    const sid = cid ? `ailab-user-${uid}-conv-${cid}` : `ailab-user-${uid}`
    h['X-Hermes-User-Id'] = String(uid)
    h['X-Hermes-Session-Id'] = sid
  }
  return h
}

// ===== 会话管理状态 =====
const conversations = ref([])
const currentConversationId = ref(null)
const currentConversation = ref(null)
// 移动端默认折叠侧边栏
const isSidebarCollapsed = ref(window.innerWidth < 1024)
const isLoadingConversations = ref(false)
const isPanelOpen = ref(false)
const panelRef = ref(null)
let memoryRefreshTimer = null

// 通知未读数从右侧 Panel 内部的轮询拿，badge 显示在 Panel 切换按钮上
const panelUnreadCount = computed(() => panelRef.value?.notificationsUnread ?? 0)

const refreshMemoryPanel = (delay = 0) => {
  if (memoryRefreshTimer) {
    clearTimeout(memoryRefreshTimer)
  }
  memoryRefreshTimer = setTimeout(() => {
    memoryRefreshTimer = null
    panelRef.value?.refreshMemory()
  }, delay)
}

// ===== 聊天状态 =====
const isLoading = ref(false)
const inputMessage = ref('')
const messages = ref([])
const chatAreaRef = ref(null)

// ===== 文件/语音状态 =====
const selectedFile = ref(null)       // File object
const filePreview = ref(null)        // base64 data URL (images) or filename (PDF)
const fileType = ref(null)           // 'image' | 'pdf'
const isFileProcessing = ref(false)
const fileInputRef = ref(null)
const isDragging = ref(false)

const selectedAttachment = computed(() => {
  if (!selectedFile.value) return null
  return {
    name: selectedFile.value.name,
    size: selectedFile.value.size,
    type: fileType.value,
    preview: filePreview.value,
  }
})
const isRecording = ref(false)
const isTranscribing = ref(false)
const recordingDuration = ref(0)
let mediaRecorder = null
let audioChunks = []
let recordingTimer = null

// ===== 流式状态 =====
const currentReasoning = ref('')
const currentContent = ref('')
const isReasoningPhase = ref(false)
const currentStreamingIndex = ref(null)

// ===== 请求控制 =====
let abortController = null
let currentReader = null

// ===== 统计信息 =====
const stats = ref({
  reasoningLength: 0,
  contentLength: 0,
  startTime: null,
  endTime: null
})

// ===== Token 用量统计（session 级别） =====
const TOKEN_CONTEXT_LIMIT = 1_000_000
const sessionTokens = ref({
  // 最近一次请求的 token 数（代表当前 context 占用）
  promptTokens: 0,
  completionTokens: 0,
  cacheTokens: 0,
  // session 累计
  totalPromptTokens: 0,
  totalCompletionTokens: 0,
  totalCacheTokens: 0,
  turnCount: 0,
  // 最近一次的 prompt 组成（来自 Hermes usage.breakdown，仅前端缓存，不持久化）
  breakdown: null,
})

// breakdown 不进数据库，但用户在多个会话之间切换时不该丢——缓存到模块作用域，
// 按 conversation id 存上一次拿到的 breakdown，切回这个会话时恢复。
const breakdownCache = new Map()

// 单轮（user → assistant）的 token 计费累加器。Hermes 多步 agent 一轮可能
// 产生多次内部 LLM 调用（每次都 emit 一个 usage 事件），此处把它们叠加到同一
// 轮次，等流式结束后随 saveMessage 一起持久化到 AiLabMessage。
const turnUsage = ref({ promptTokens: 0, completionTokens: 0, cacheTokens: 0, modelName: '' })
const resetTurnUsage = () => {
  turnUsage.value = { promptTokens: 0, completionTokens: 0, cacheTokens: 0, modelName: '' }
}

const resetSessionTokens = () => {
  sessionTokens.value = {
    promptTokens: 0,
    completionTokens: 0,
    cacheTokens: 0,
    totalPromptTokens: 0,
    totalCompletionTokens: 0,
    totalCacheTokens: 0,
    turnCount: 0,
    breakdown: null,
  }
}

const saveTokenUsage = async () => {
  if (!currentConversationId.value) return
  try {
    // breakdown 是临时 UI 状态，不进数据库
    const { breakdown: _omit, ...persisted } = sessionTokens.value
    await fetch(`${API_BASE_URL}/api/ai/conversations/${currentConversationId.value}/token-usage/`, {
      method: 'PATCH',
      headers: djangoHeaders({ 'Content-Type': 'application/json' }),
      body: JSON.stringify(persisted)
    })
  } catch (e) { /* silent */ }
}

const recordUsage = (usage, parsedChunk = null) => {
  if (!usage || typeof usage !== 'object') return
  // prompt_tokens 是 Hermes 一轮所有内部 LLM 调用的 prompt 累加（计费量），
  // 上下文窗口要的是最后一次调用真正发给模型的 prompt 大小 —— 用 last_prompt_tokens。
  // 旧版网关没这个字段时回退到 prompt_tokens。
  const billedPrompt = Number(usage.prompt_tokens) || 0
  const lastPrompt = Number(usage.last_prompt_tokens) || billedPrompt
  const completion = Number(usage.completion_tokens) || 0
  // patch12 透传：cache_tokens = cache_read + cache_write（不分读写）
  const cache = Number(usage.cache_tokens) || 0
  if (billedPrompt === 0 && completion === 0) return

  // 累加到本轮（多步 agent 一轮多次 LLM 调用，每次都来一条 usage）
  const reportedModel = (parsedChunk && typeof parsedChunk.model === 'string' && parsedChunk.model.trim()) || ''
  turnUsage.value = {
    promptTokens: turnUsage.value.promptTokens + billedPrompt,
    completionTokens: turnUsage.value.completionTokens + completion,
    cacheTokens: turnUsage.value.cacheTokens + cache,
    modelName: reportedModel || turnUsage.value.modelName,
  }
  // Hermes 扩展字段：{ sections: { key: {label, tokens} }, total_local, encoding }
  const breakdown = (usage.breakdown && typeof usage.breakdown === 'object') ? usage.breakdown : null
  const nextBreakdown = breakdown || sessionTokens.value.breakdown
  sessionTokens.value = {
    // promptTokens 用作 Context Window 的当前值 —— 反映最后一次发给模型的 prompt 大小
    promptTokens: lastPrompt,
    completionTokens: completion,
    cacheTokens: cache,
    // 累计走计费量（每次内部调用都计），便于对账消耗
    totalPromptTokens: sessionTokens.value.totalPromptTokens + billedPrompt,
    totalCompletionTokens: sessionTokens.value.totalCompletionTokens + completion,
    totalCacheTokens: sessionTokens.value.totalCacheTokens + cache,
    turnCount: sessionTokens.value.turnCount + 1,
    breakdown: nextBreakdown,
  }
  // 缓存当前会话的 breakdown，切走再切回来时还能用
  if (nextBreakdown && currentConversationId.value) {
    breakdownCache.set(currentConversationId.value, nextBreakdown)
  }
  saveTokenUsage()
}

// ===== 计算属性 =====
const hasMessages = computed(() => messages.value.length > 0)
const conversationTitle = computed(() => currentConversation.value?.title || '')

const STREAM_PHASE = {
  IDLE: 'idle',
  REASONING: 'reasoning',
  TOOL_CALLING: 'tool_calling',
  TOOL_EXECUTING: 'tool_executing',
  ANSWERING: 'answering',
  ERROR: 'error'
}

const TOOL_STATUS = {
  PARSING: 'parsing',
  PENDING: 'pending',
  RUNNING: 'running',
  SUCCESS: 'success',
  ERROR: 'error'
}

const createTraceId = () => `trace_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`

const formatStructuredValue = (value) => {
  if (value === null || value === undefined) return ''
  if (typeof value === 'string') return value
  try {
    return JSON.stringify(value, null, 2)
  } catch {
    return String(value)
  }
}

const safeParseJson = (raw) => {
  if (!raw || typeof raw !== 'string') return null
  try {
    return JSON.parse(raw)
  } catch {
    return null
  }
}

const normalizeToolStatus = (status) => {
  if (!status) return TOOL_STATUS.PARSING
  const normalized = String(status).toLowerCase()
  if (normalized === 'ok' || normalized === 'done') return TOOL_STATUS.SUCCESS
  if (normalized === 'failed') return TOOL_STATUS.ERROR
  if (Object.values(TOOL_STATUS).includes(normalized)) return normalized
  return TOOL_STATUS.PARSING
}

const MARKDOWN_IMAGE_URL_RE = /!\[[^\]]*]\(([^)\s]+)(?:\s+"[^"]*")?\)/g
const LOCAL_ASSET_PATH_RE = /(^|[^\w/:.-])(\/(?:[\w.-]+\/)+[\w.-]+\.(?:png|jpg|jpeg|gif|webp|pdf|mp4|mov|webm|mkv))\b/gi
const PUBLISHED_ASSET_URL_RE = /(^|[^\w/:.-])(\/media\/ailab\/[\w.-]+\.(?:png|jpg|jpeg|gif|webp|pdf|mp4|mov|webm|mkv))\b/gi

const extractMatches = (text, regex, groupIndex = 1) => {
  if (!text) return []
  const matches = []
  for (const match of text.matchAll(regex)) {
    if (match[groupIndex]) {
      matches.push(match[groupIndex])
    }
  }
  return matches
}

const buildPersistedAssetUrlMap = (streamedContent, persistedContent) => {
  const rewrites = new Map()
  const streamedImageUrls = extractMatches(streamedContent, MARKDOWN_IMAGE_URL_RE, 1)
  const persistedImageUrls = extractMatches(persistedContent, MARKDOWN_IMAGE_URL_RE, 1)
  const imageCount = Math.min(streamedImageUrls.length, persistedImageUrls.length)

  for (let i = 0; i < imageCount; i += 1) {
    if (streamedImageUrls[i] !== persistedImageUrls[i]) {
      rewrites.set(streamedImageUrls[i], persistedImageUrls[i])
    }
  }

  if (rewrites.size > 0) {
    return rewrites
  }

  const streamedLocalPaths = extractMatches(streamedContent, LOCAL_ASSET_PATH_RE, 2)
  const persistedMediaUrls = extractMatches(persistedContent, PUBLISHED_ASSET_URL_RE, 2)
  if (streamedLocalPaths.length === 0 || streamedLocalPaths.length !== persistedMediaUrls.length) {
    return rewrites
  }

  streamedLocalPaths.forEach((path, index) => {
    if (path !== persistedMediaUrls[index]) {
      rewrites.set(path, persistedMediaUrls[index])
    }
  })
  return rewrites
}

const replaceAssetUrls = (text, rewrites) => {
  if (!text || !rewrites || rewrites.size === 0) return text || ''
  let nextText = text
  for (const [from, to] of rewrites.entries()) {
    nextText = nextText.replaceAll(from, to)
  }
  return nextText
}

const syncSegmentsWithPersistedContent = (segments, streamedContent, persistedContent) => {
  if (!Array.isArray(segments) || segments.length === 0) return segments
  if (segments.length === 1) {
    return [{ ...segments[0], content: persistedContent }]
  }

  const rewrites = buildPersistedAssetUrlMap(streamedContent, persistedContent)
  if (rewrites.size === 0) {
    return segments
  }

  return segments.map(seg => ({
    ...seg,
    content: replaceAssetUrls(seg.content || '', rewrites)
  }))
}

const normalizeAssistantMessage = (message) => {
  if (message?.role !== 'assistant') {
    return message
  }
  // 后端字段 sub_turns → 前端 subTurns
  const subTurns = Array.isArray(message.subTurns) ? message.subTurns
    : Array.isArray(message.sub_turns) ? message.sub_turns
    : []
  // segments 是新结构（可能从后端回传，也可能由历史数据合成出唯一一段）
  let segments = Array.isArray(message.segments) ? message.segments : null
  if (!segments || segments.length === 0) {
    // 历史消息：合成单段 segment 兜底
    const synthSubTurns = subTurns.slice()
    // 极旧格式：只有 message.reasoning 没有 subTurns —— 包成一个 thinking subTurn
    if (synthSubTurns.length === 0 && message.reasoning) {
      synthSubTurns.push({
        id: 'legacy-r',
        reasoning: message.reasoning,
        reasoningStartedAt: null,
        reasoningFinishedAt: null,
        toolCall: null,
      })
    }
    segments = [{
      id: 'legacy-0',
      subTurns: synthSubTurns,
      content: message.content || '',
    }]
  }
  return {
    ...message,
    phase: message.phase || STREAM_PHASE.IDLE,
    subTurns,
    segments,
    modelName: message.modelName || message.model_name || null,
    currentReasoning: message.currentReasoning || '',
    currentToolCall: message.currentToolCall || null
  }
}

const normalizeMessagesForUI = (list) => {
  return (list || []).map(m => {
    const normalized = normalizeAssistantMessage(m)
    if (!normalized.type) normalized.type = 'text'
    return normalized
  })
}

// ===== API 调用 =====

// 获取会话列表
const fetchConversations = async () => {
  isLoadingConversations.value = true
  try {
    const response = await fetch(`${API_BASE_URL}/api/ai/conversations/`, { headers: djangoHeaders() })
    if (response.ok) {
      conversations.value = await response.json()
    }
  } catch (error) {
    console.error('获取会话列表失败:', error)
  } finally {
    isLoadingConversations.value = false
  }
}

// 获取会话详情（含消息）
const fetchConversation = async (id) => {
  try {
    const response = await fetch(`${API_BASE_URL}/api/ai/conversations/${id}/`, { headers: djangoHeaders() })
    if (response.ok) {
      const data = await response.json()
      currentConversation.value = data
      messages.value = normalizeMessagesForUI(data.messages || [])
      // 恢复持久化的 token 用量
      if (data.token_usage && typeof data.token_usage === 'object' && Object.keys(data.token_usage).length > 0) {
        sessionTokens.value = {
          // 兜底：老会话没有 cacheTokens / totalCacheTokens 字段，避免显示成 NaN
          cacheTokens: 0,
          totalCacheTokens: 0,
          ...data.token_usage,
          // breakdown 没进库；如果本会话之前在内存里有缓存，切回来时恢复，否则置 null
          breakdown: breakdownCache.get(id) || null,
        }
      } else {
        resetSessionTokens()
      }
      await nextTick()
      chatAreaRef.value?.scrollToBottom(true)
      renderMath()
    }
  } catch (error) {
    console.error('获取会话详情失败:', error)
  }
}

// 创建新会话（实际写入后端 — 仅在用户首条消息发送时调用）
const createConversation = async () => {
  try {
    const response = await fetch(`${API_BASE_URL}/api/ai/conversations/`, {
      method: 'POST',
      headers: djangoHeaders({ 'Content-Type': 'application/json' }),
      body: JSON.stringify({ title: '新对话' })
    })
    if (response.ok) {
      const data = await response.json()
      conversations.value.unshift(data)
      currentConversationId.value = data.id
      currentConversation.value = data
    }
  } catch (error) {
    console.error('创建会话失败:', error)
  }
}

// 进入"新对话"欢迎态：仅清空本地视图，不写后端、不进 sidebar
// 用户发送首条消息时才真正 createConversation()
const startNewConversation = () => {
  currentConversationId.value = null
  currentConversation.value = null
  messages.value = []
  resetSessionTokens()
  inputMessage.value = ''
  removeFile?.()
}

// 选择会话
const selectConversation = async (id) => {
  currentConversationId.value = id
  resetSessionTokens()
  await fetchConversation(id)
}

// 删除会话
const deleteConversation = async (id) => {
  // Sidebar 组件已有自定义确认弹窗，此处无需再弹

  try {
    const response = await fetch(`${API_BASE_URL}/api/ai/conversations/${id}/`, {
      method: 'DELETE',
      headers: djangoHeaders()
    })
    if (response.ok) {
      conversations.value = conversations.value.filter(c => c.id !== id)
      breakdownCache.delete(id)
      if (currentConversationId.value === id) {
        currentConversationId.value = null
        currentConversation.value = null
        messages.value = []
        resetSessionTokens()
      }
    }
  } catch (error) {
    console.error('删除会话失败:', error)
  }
}

// 保存消息到后端
const saveMessage = async (conversationId, role, content, reasoning = null, subTurns = null, modelName = null, usage = null) => {
  try {
    const body = { role, content, reasoning }
    if (subTurns && subTurns.length > 0) {
      body.sub_turns = subTurns
    }
    if (modelName) {
      body.model_name = modelName
    }
    if (usage && (usage.promptTokens || usage.completionTokens || usage.cacheTokens)) {
      body.prompt_tokens = usage.promptTokens || 0
      body.completion_tokens = usage.completionTokens || 0
      body.cache_tokens = usage.cacheTokens || 0
    }
    const response = await fetch(`${API_BASE_URL}/api/ai/conversations/${conversationId}/messages/`, {
      method: 'POST',
      headers: djangoHeaders({ 'Content-Type': 'application/json' }),
      body: JSON.stringify(body)
    })
    if (response.ok) {
      return await response.json()
    }
  } catch (error) {
    console.error('保存消息失败:', error)
  }
  return null
}

// 删除消息及后续
const deleteMessageAndFollowing = async (messageId) => {
  try {
    await fetch(`${API_BASE_URL}/api/ai/messages/${messageId}/`, {
      method: 'DELETE',
      headers: djangoHeaders()
    })
  } catch (error) {
    console.error('删除消息失败:', error)
  }
}

// ===== 消息发送 =====
const sendMessage = async (content = null, options = {}) => {
  const text = content || inputMessage.value.trim()
  if (!text && !selectedFile.value) return
  if (isLoading.value) return

  // 如果没有当前会话，先创建一个
  if (!currentConversationId.value) {
    await createConversation()
  }

  // 处理文件附件
  let fileContent = null
  if (selectedFile.value) {
    if (fileType.value === 'image') {
      // 图片：读取 base64，作为多模态内容发给 Hermes
      fileContent = await new Promise((resolve) => {
        const reader = new FileReader()
        reader.onload = (e) => resolve({
          type: 'image',
          dataUrl: e.target.result,
          filename: selectedFile.value.name,
          size: selectedFile.value.size,
        })
        reader.readAsDataURL(selectedFile.value)
      })
    } else if (fileType.value === 'pdf') {
      // PDF：后端提取文本
      isFileProcessing.value = true
      try {
        const formData = new FormData()
        formData.append('file', selectedFile.value)
        const resp = await fetch(`${API_BASE_URL}/api/ai/pdf-extract/`, { method: 'POST', body: formData })
        const data = await resp.json()
        if (!resp.ok) throw new Error(data.error || 'PDF 解析失败')
        fileContent = { type: 'pdf', text: data.text, filename: data.filename, pages: data.pages }
      } catch (e) {
        alert(`文件处理失败: ${e.message}`)
        isFileProcessing.value = false
        return
      }
      isFileProcessing.value = false
    }
  }

  // 构建用户消息展示内容
  let displayText = text || ''
  if (fileContent?.type === 'pdf') {
    displayText = `${text ? text + '\n\n' : ''}📄 ${fileContent.filename} (${fileContent.pages} 页)`
  } else if (fileContent?.type === 'image') {
    displayText = text || '(图片)'
  }

  const userMessage = { role: 'user', content: displayText, type: 'text', fileAttachment: fileContent }
  messages.value.push(userMessage)
  inputMessage.value = ''
  removeFile()

  // 保存用户消息到后端
  const savedUserMsg = await saveMessage(currentConversationId.value, 'user', displayText)
  if (savedUserMsg) {
    userMessage.id = savedUserMsg.id
  }

  // 刷新会话列表以更新标题
  fetchConversations()

  // 开始流式响应（传入文件内容供 API 调用使用）
  await streamResponse(fileContent, options)

  // AI 标题在后端是异步生成（DeepSeek 1-2s 出结果），流式响应结束后
  // 再拉一次会话列表，把"新对话"换成生成出的真实标题
  fetchConversations()
}

// 流式响应
const streamResponse = async (fileContent = null, options = {}) => {
  // options.useRequestHistory: 让 Hermes 用 request body 的 messages 而不是
  // state.db 里的旧 history。edit / regenerate 删消息后调用必须设 true，
  // 否则 agent 会按 DB 里的旧消息回应，跟前端展示的对不上。
  isLoading.value = true
  currentReasoning.value = ''
  currentContent.value = ''
  isReasoningPhase.value = false
  stats.value = { reasoningLength: 0, contentLength: 0, startTime: Date.now(), endTime: null }
  resetTurnUsage()

  // 添加空的 AI 消息用于流式填充
  const aiMessageIndex = messages.value.length
  currentStreamingIndex.value = aiMessageIndex
  const currentModelName = 'Hermes'
  messages.value.push({
    role: 'assistant',
    content: '',
    reasoning: '',
    type: 'text',
    isStreaming: true,
    phase: STREAM_PHASE.REASONING,
    subTurns: [],
    currentReasoning: '',
    currentToolCall: null,
    modelName: currentModelName
  })

  let streamPhase = STREAM_PHASE.REASONING
  let activeReasoning = ''
  let activeToolIndex = null
  let hasDoneEvent = false
  let activeReasoningStartedAt = null
  // Agent 输出文字 → 又 think/tool → 再输出文字 时，希望两段文字之间穿插各自的 trace。
  // segments 是已归档的段；segmentSubTurns / segmentContent 是当前活动段。
  const messageSegments = []
  let segmentSubTurns = []
  let segmentContent = ''
  const streamToolCalls = new Map()

  const getAiMessage = () => messages.value[aiMessageIndex]

  const archiveSegmentIfBoundary = () => {
    // 在新一段 reasoning / tool 之前调用：如果当前段已经产出了文本（content），
    // 把它冻结成一段历史 segment，开新段承接接下来的 think/tool。
    if (!segmentContent && segmentSubTurns.length === 0) return
    if (!segmentContent) return  // 还没有内容的话先攒着，不切段
    messageSegments.push({
      id: createTraceId(),
      subTurns: segmentSubTurns,
      content: segmentContent,
    })
    segmentSubTurns = []
    segmentContent = ''
  }

  const syncTraceState = () => {
    const aiMsg = getAiMessage()
    if (!aiMsg) return
    aiMsg.phase = streamPhase
    const liveSubTurns = segmentSubTurns.map(turn => ({
      ...turn,
      toolCall: turn.toolCall ? { ...turn.toolCall } : null,
    }))
    const liveToolCall = activeToolIndex === null
      ? null
      : (streamToolCalls.get(activeToolIndex) ? { ...streamToolCalls.get(activeToolIndex) } : null)
    const liveSegment = {
      id: 'live',
      subTurns: liveSubTurns,
      content: segmentContent,
      currentReasoning: activeReasoning,
      currentToolCall: liveToolCall,
    }
    aiMsg.segments = [
      ...messageSegments.map(s => ({
        ...s,
        subTurns: s.subTurns.map(t => ({ ...t, toolCall: t.toolCall ? { ...t.toolCall } : null })),
      })),
      liveSegment,
    ]
    // 兼容字段：旧的 content / subTurns 仍是扁平拼接，方便持久化和搜索
    aiMsg.content = messageSegments.map(s => s.content).join('') + segmentContent
    aiMsg.subTurns = [
      ...messageSegments.flatMap(s => s.subTurns),
      ...liveSubTurns,
    ]
    aiMsg.currentReasoning = activeReasoning
    aiMsg.currentToolCall = liveToolCall
  }

  const pushSubTurns = () => {
    const hasReasoning = Boolean(activeReasoning.trim())
    if (!hasReasoning && streamToolCalls.size === 0) {
      return
    }

    const reasoningStartedAt = activeReasoningStartedAt
    const reasoningFinishedAt = hasReasoning ? Date.now() : null

    const orderedToolCalls = Array.from(streamToolCalls.values()).sort((a, b) => a.index - b.index)
    if (orderedToolCalls.length === 0) {
      segmentSubTurns.push({
        id: createTraceId(),
        reasoning: activeReasoning.trim(),
        reasoningStartedAt,
        reasoningFinishedAt,
        toolCall: null
      })
    } else {
      orderedToolCalls.forEach((toolCall, index) => {
        segmentSubTurns.push({
          id: createTraceId(),
          reasoning: index === 0 ? activeReasoning.trim() : '',
          reasoningStartedAt: index === 0 ? reasoningStartedAt : null,
          reasoningFinishedAt: index === 0 ? reasoningFinishedAt : null,
          toolCall: { ...toolCall }
        })
      })
    }

    activeReasoning = ''
    activeReasoningStartedAt = null
    streamToolCalls.clear()
    activeToolIndex = null
    syncTraceState()
  }

  const setPhase = (nextPhase) => {
    if (nextPhase === streamPhase) {
      return
    }

    const leavingReasoning =
      streamPhase === STREAM_PHASE.REASONING && nextPhase !== STREAM_PHASE.REASONING

    // 1) 离开 REASONING 阶段时，如果有积累的思考内容就归档 → 让 UI 立即停止流光、显示耗时
    // 2) 工具调用结束后切回 reasoning/answering/idle 时，把这一轮的 sub-turn 归档
    if (
      (leavingReasoning && activeReasoning.trim()) ||
      ((nextPhase === STREAM_PHASE.REASONING || nextPhase === STREAM_PHASE.ANSWERING || nextPhase === STREAM_PHASE.IDLE) &&
        streamToolCalls.size > 0)
    ) {
      pushSubTurns()
    }

    streamPhase = nextPhase
    isReasoningPhase.value = nextPhase === STREAM_PHASE.REASONING
    syncTraceState()
  }

  const upsertToolCall = (fragment = {}, options = {}) => {
    const appendArguments = options.appendArguments !== false
    const index = Number.isInteger(fragment.index) ? fragment.index : (activeToolIndex ?? 0)
    // 内容已经输出过、又开始新一轮工具调用 → 切段
    const isNewCall = !streamToolCalls.has(index)
    if (isNewCall && segmentContent) archiveSegmentIfBoundary()
    const existing = streamToolCalls.get(index) || {
      id: fragment.id || `call_${createTraceId()}`,
      index,
      name: '',
      argumentsText: '',
      parsedArguments: null,
      status: TOOL_STATUS.PARSING,
      result: '',
      error: '',
      progressMessage: '',
      progressUrls: [],
      startedAt: Date.now(),
      finishedAt: null
    }

    if (fragment.id) existing.id = fragment.id
    if (fragment.name) existing.name = fragment.name

    if (fragment.argumentsText !== undefined) {
      const incomingArgs = typeof fragment.argumentsText === 'string'
        ? fragment.argumentsText
        : formatStructuredValue(fragment.argumentsText)
      existing.argumentsText = appendArguments ? `${existing.argumentsText}${incomingArgs}` : incomingArgs
    }

    if (fragment.status) {
      existing.status = normalizeToolStatus(fragment.status)
      if (existing.status === TOOL_STATUS.RUNNING && !existing.startedAt) {
        existing.startedAt = Date.now()
      }
      if ((existing.status === TOOL_STATUS.SUCCESS || existing.status === TOOL_STATUS.ERROR) && !existing.finishedAt) {
        existing.finishedAt = Date.now()
      }
    }

    if (fragment.result !== undefined) {
      existing.result = formatStructuredValue(fragment.result)
    }
    if (fragment.error !== undefined) {
      existing.error = formatStructuredValue(fragment.error)
      existing.status = TOOL_STATUS.ERROR
      if (!existing.finishedAt) {
        existing.finishedAt = Date.now()
      }
    }
    if (fragment.startedAt) {
      existing.startedAt = fragment.startedAt
    }
    if (fragment.finishedAt) {
      existing.finishedAt = fragment.finishedAt
    }
    // Hermes 服务端给的 durationMs 是权威值（涵盖整个工具实际执行耗时），
    // 优先把它存到对象上让 formatToolDuration 直接用，比 JS 端 Date.now() 差值更准。
    if (Number.isFinite(fragment.durationMs) && fragment.durationMs > 0) {
      existing.durationMs = fragment.durationMs
      // 同步把 finishedAt 推算到 startedAt + duration，保证两个口径一致
      if (existing.startedAt) {
        existing.finishedAt = existing.startedAt + fragment.durationMs
      }
    }
    if (fragment.progressMessage !== undefined) {
      existing.progressMessage = fragment.progressMessage
    }
    if (fragment.progressUrls !== undefined) {
      existing.progressUrls = fragment.progressUrls
    }
    // 完成后清除进度消息
    if (existing.status === TOOL_STATUS.SUCCESS || existing.status === TOOL_STATUS.ERROR) {
      existing.progressMessage = ''
      existing.progressUrls = []
    }

    existing.parsedArguments = safeParseJson(existing.argumentsText)
    streamToolCalls.set(index, existing)
    activeToolIndex = index
    syncTraceState()
    return existing
  }

  const ingestToolCalls = (toolCalls, options = {}) => {
    if (!Array.isArray(toolCalls)) return
    const appendArguments = options.appendArguments !== false
    const defaultStatus = options.defaultStatus || TOOL_STATUS.PARSING

    for (const call of toolCalls) {
      const callFunction = call?.function || {}
      const hasArguments = callFunction.arguments !== undefined || call.arguments !== undefined || call.args !== undefined
      upsertToolCall({
        index: call?.index,
        id: call?.id,
        name: callFunction.name || call?.name,
        argumentsText: hasArguments ? (callFunction.arguments ?? call.arguments ?? call.args) : undefined,
        status: call?.status || defaultStatus,
        result: call?.result,
        error: call?.error,
        durationMs: call?.duration_ms || call?.durationMs
      }, { appendArguments })
    }
  }

  const appendReasoningChunk = (chunk) => {
    if (!chunk) return
    // 文本段已经产出过 → 这是新一轮 think，归档前一段
    if (segmentContent) archiveSegmentIfBoundary()
    setPhase(STREAM_PHASE.REASONING)
    if (activeReasoningStartedAt === null) {
      activeReasoningStartedAt = Date.now()
    }
    currentReasoning.value += chunk
    activeReasoning += chunk
    const aiMsg = getAiMessage()
    if (aiMsg) {
      aiMsg.reasoning = currentReasoning.value
    }
    syncTraceState()
  }

  const appendContentChunk = (chunk) => {
    if (!chunk) return
    setPhase(STREAM_PHASE.ANSWERING)
    currentContent.value += chunk
    segmentContent += chunk
    syncTraceState()
    renderMath()
  }

  const markToolCallsStatus = (status) => {
    for (const call of streamToolCalls.values()) {
      upsertToolCall({
        index: call.index,
        status
      }, { appendArguments: false })
    }
  }

  const handleOpenAIChunk = (payload) => {
    const delta = payload?.delta || payload?.choices?.[0]?.delta || payload?.chunk?.choices?.[0]?.delta
    const finishReason = payload?.finish_reason ?? payload?.choices?.[0]?.finish_reason ?? payload?.chunk?.choices?.[0]?.finish_reason

    if (typeof delta?.reasoning_content === 'string' && delta.reasoning_content) {
      appendReasoningChunk(delta.reasoning_content)
    }

    if (Array.isArray(delta?.tool_calls) && delta.tool_calls.length > 0) {
      setPhase(STREAM_PHASE.TOOL_CALLING)
      ingestToolCalls(delta.tool_calls, { appendArguments: true, defaultStatus: TOOL_STATUS.PARSING })
    }

    if (typeof delta?.content === 'string' && delta.content) {
      appendContentChunk(delta.content)
    }

    if (finishReason === 'tool_calls') {
      markToolCallsStatus(TOOL_STATUS.PENDING)
    }
    if (finishReason === 'stop') {
      hasDoneEvent = true
      stats.value.endTime = Date.now()
      setPhase(STREAM_PHASE.IDLE)
    }
  }

  const handleToolEvent = (payload, eventType) => {
    const rawToolCall = payload.tool_call || payload.call || payload
    const hasArguments = rawToolCall?.arguments !== undefined || rawToolCall?.args !== undefined || rawToolCall?.function?.arguments !== undefined

    if (eventType === 'tool_execution_start' || eventType === 'tool_progress') {
      setPhase(STREAM_PHASE.TOOL_EXECUTING)
    } else {
      setPhase(STREAM_PHASE.TOOL_CALLING)
    }

    upsertToolCall({
      index: rawToolCall?.index,
      id: rawToolCall?.id || payload.tool_call_id,
      name: rawToolCall?.function?.name || rawToolCall?.name || payload.name,
      argumentsText: hasArguments
        ? (rawToolCall?.function?.arguments ?? rawToolCall?.arguments ?? rawToolCall?.args)
        : undefined,
      status: payload.status || (
        eventType === 'tool_execution_start' || eventType === 'tool_progress'
          ? TOOL_STATUS.RUNNING
          : eventType === 'tool_execution_error'
            ? TOOL_STATUS.ERROR
            : eventType === 'tool_execution_result' || eventType === 'tool_result'
              ? TOOL_STATUS.SUCCESS
              : TOOL_STATUS.PARSING
      ),
      result: payload.result ?? payload.output,
      error: payload.error,
      durationMs: payload.duration_ms || payload.durationMs,
      progressMessage: eventType === 'tool_progress' ? payload.message : undefined,
      progressUrls: eventType === 'tool_progress' && payload.urls ? payload.urls : undefined
    }, { appendArguments: eventType !== 'tool_call' })
  }

  const handleStreamEvent = (parsed) => {
    if (!parsed || typeof parsed !== 'object') return

    switch (parsed.type) {
      case 'reasoning_start':
        setPhase(STREAM_PHASE.REASONING)
        break

      case 'reasoning':
        appendReasoningChunk(parsed.content)
        break

      case 'reasoning_end':
        isReasoningPhase.value = false
        break

      case 'tool_call':
      case 'tool_call_start':
      case 'tool_call_delta':
      case 'tool_call_end':
      case 'tool_execution_start':
      case 'tool_execution_result':
      case 'tool_execution_error':
      case 'tool_result':
      case 'tool_progress':
        handleToolEvent(parsed, parsed.type)
        break

      case 'content_start':
        setPhase(STREAM_PHASE.ANSWERING)
        break

      case 'content':
        appendContentChunk(parsed.content)
        break

      case 'done':
        hasDoneEvent = true
        stats.value.reasoningLength = parsed.reasoning_length ?? currentReasoning.value.length
        stats.value.contentLength = parsed.content_length ?? currentContent.value.length
        stats.value.endTime = Date.now()
        if (parsed.finish_reason === 'tool_calls') {
          markToolCallsStatus(TOOL_STATUS.PENDING)
        }
        setPhase(STREAM_PHASE.IDLE)
        break

      case 'error':
        throw new Error(parsed.error)

      default:
        if (parsed.phase && Object.values(STREAM_PHASE).includes(parsed.phase)) {
          setPhase(parsed.phase)
        }
        if (Array.isArray(parsed.tool_calls) && parsed.tool_calls.length > 0) {
          setPhase(STREAM_PHASE.TOOL_CALLING)
          ingestToolCalls(parsed.tool_calls, { appendArguments: parsed.type === 'tool_calls_delta', defaultStatus: TOOL_STATUS.PARSING })
        }
        if (parsed.delta || parsed.choices || parsed.chunk) {
          handleOpenAIChunk(parsed)
        }
    }
  }

  // 构建 API 消息
  const apiMessages = messages.value
    .filter(m => (m.role === 'user' || m.role === 'assistant') && !m.isStreaming)
    .map(m => {
      const text = m.content?.replace(/\n\n\*\[已停止生成\]\*$/, '') || ''
      // 最后一条用户消息可能有文件附件
      if (m.role === 'user' && m.fileAttachment) {
        const att = m.fileAttachment
        if (att.type === 'image') {
          // 多模态：图片 + 文字
          const parts = []
          if (text && text !== '(图片)') parts.push({ type: 'text', text })
          parts.push({ type: 'image_url', image_url: { url: att.dataUrl } })
          return { role: 'user', content: parts }
        }
        if (att.type === 'pdf') {
          // PDF：将提取的文本附加到消息
          const pdfContext = `[PDF: ${att.filename}, ${att.pages} pages]\n\n${att.text}`
          return { role: 'user', content: text ? `${text}\n\n${pdfContext}` : pdfContext }
        }
      }
      return { role: m.role, content: text }
    })
    .filter(m => m.content)

  abortController = new AbortController()

  try {
    // 把当前对话 ID 传给 Hermes —— 用户关掉浏览器后 Hermes 后台跑完会用它
    // 把最终消息回写到 Django 的 messages/internal/ 端点
    const chatHeaders = hermesHeaders({ 'Content-Type': 'application/json' })
    if (currentConversationId.value) {
      chatHeaders['X-AILab-Conversation-Id'] = String(currentConversationId.value)
    }
    if (options.useRequestHistory) {
      // edit / regenerate 后让 Hermes 信任请求体里的 messages，不要从 state.db 重放旧消息
      chatHeaders['X-Hermes-History-Source'] = 'request'
    }
    const response = await fetch(`${HERMES_API_URL}/v1/chat/completions`, {
      method: 'POST',
      headers: chatHeaders,
      body: JSON.stringify({
        model: 'hermes-agent',
        messages: apiMessages,
        stream: true,
        stream_options: { include_usage: true }
      }),
      signal: abortController.signal
    })

    if (!response.ok) {
      const error = await response.json().catch(() => ({}))
      throw new Error(error.error || `请求失败 (${response.status})`)
    }

    const reader = response.body.getReader()
    currentReader = reader
    const decoder = new TextDecoder()
    let buffer = ''

    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      if (!isLoading.value) break

      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split('\n')
      buffer = lines.pop() || ''

      let currentEventType = null
      for (const line of lines) {
        if (!line || line.startsWith(':')) continue

        // Handle named SSE events (event: hermes.reasoning, etc.)
        if (line.startsWith('event: ')) {
          currentEventType = line.slice(7).trim()
          continue
        }

        if (line.startsWith('data: ')) {
          const data = line.slice(6).trim()
          if (data === '[DONE]') {
            hasDoneEvent = true
            stats.value.reasoningLength = currentReasoning.value.length
            stats.value.contentLength = currentContent.value.length
            stats.value.endTime = Date.now()
            setPhase(STREAM_PHASE.IDLE)
            break
          }
          if (!data) continue

          try {
            const parsed = JSON.parse(data)

            // 捕获 OpenAI 风格 usage 字段（include_usage:true 的最终 chunk，或 Hermes 自带的 usage）
            if (parsed && parsed.usage) {
              recordUsage(parsed.usage, parsed)
            }

            if (currentEventType === 'hermes.reasoning') {
              appendReasoningChunk(parsed.text)
            } else if (currentEventType === 'hermes.tool.start') {
              setPhase(STREAM_PHASE.TOOL_EXECUTING)
              upsertToolCall({
                id: parsed.id,
                name: parsed.name,
                argumentsText: parsed.args,
                status: TOOL_STATUS.RUNNING,
              }, { appendArguments: false })
            } else if (currentEventType === 'hermes.tool.complete') {
              // Hermes 在 tool.completed 事件里给了 duration（秒），优先用它当工具耗时，
              // 别用 JS 端 Date.now() 减出来的差（SSE 批量到达时差近 0 → 显示 0.0s）
              const completeDurationMs = Number.isFinite(parsed.duration)
                ? Math.round(parsed.duration * 1000)
                : (Number.isFinite(parsed.duration_ms) ? parsed.duration_ms : null)
              upsertToolCall({
                id: parsed.id,
                name: parsed.name,
                status: parsed.error ? TOOL_STATUS.ERROR : TOOL_STATUS.SUCCESS,
                result: parsed.result,
                error: parsed.error,
                durationMs: completeDurationMs,
              }, { appendArguments: false })
              if (!parsed.error && parsed.name === 'memory') {
                refreshMemoryPanel(150)
              }
            } else if (currentEventType === 'hermes.tool.progress') {
              setPhase(STREAM_PHASE.TOOL_EXECUTING)
              upsertToolCall({
                name: parsed.tool,
                status: TOOL_STATUS.RUNNING,
                progressMessage: `${parsed.emoji || ''} ${parsed.label || parsed.tool}`.trim(),
              }, { appendArguments: false })
            } else {
              // Standard OpenAI delta chunk
              handleOpenAIChunk(parsed)
            }
          } catch (e) {
            if (!(e instanceof SyntaxError)) {
              throw e
            }
          }
          currentEventType = null
        }
      }
    }

    if (!hasDoneEvent) {
      stats.value.reasoningLength = currentReasoning.value.length
      stats.value.contentLength = currentContent.value.length
      stats.value.endTime = Date.now()
    }

    if (activeReasoning.trim() || streamToolCalls.size > 0) {
      pushSubTurns()
    }

    setPhase(STREAM_PHASE.IDLE)
    const aiMsg = getAiMessage()
    if (aiMsg) {
      aiMsg.isStreaming = false
      aiMsg.phase = STREAM_PHASE.IDLE
      aiMsg.currentReasoning = ''
      aiMsg.currentToolCall = null
      aiMsg.stats = { ...stats.value }
    }

    // 保存 AI 消息到后端（含完整 subTurns + 本轮 token 计费）。
    // 优先用 Hermes 上报的真实模型名（turnUsage.modelName），用于跨会话按
    // 模型分组统计；没有就退到展示用的 currentModelName。
    const persistedModelName = turnUsage.value.modelName || currentModelName
    const savedAiMsg = await saveMessage(
      currentConversationId.value,
      'assistant',
      currentContent.value,
      currentReasoning.value,
      aiMsg?.subTurns || streamSubTurns,
      persistedModelName,
      turnUsage.value,
    )
    if (savedAiMsg) {
      const existingAiMsg = messages.value[aiMessageIndex]
      if (existingAiMsg) {
        const persistedContent = savedAiMsg.content || currentContent.value
        const syncedSegments = syncSegmentsWithPersistedContent(
          existingAiMsg.segments,
          currentContent.value,
          persistedContent,
        )

        messages.value[aiMessageIndex] = normalizeAssistantMessage({
          ...existingAiMsg,
          ...savedAiMsg,
          content: persistedContent,
          segments: syncedSegments,
        })
        currentContent.value = persistedContent
      }
    }

    renderMath()

    // AI 回复完成后刷新 memory（agent 可能在对话中写入了记忆）
    refreshMemoryPanel()

  } catch (error) {
    if (error.name === 'AbortError') {
      return
    }
    const aiMsg = getAiMessage()
    if (aiMsg) {
      aiMsg.content = `抱歉，我遇到了一点问题 😅\n\n${error.message}\n\n请稍后再试~`
      aiMsg.reasoning = currentReasoning.value
      aiMsg.phase = STREAM_PHASE.ERROR
      aiMsg.isStreaming = false
      aiMsg.currentReasoning = ''
      aiMsg.currentToolCall = null
      aiMsg.stats = {
        ...stats.value,
        endTime: Date.now(),
        reasoningLength: currentReasoning.value.length,
        contentLength: currentContent.value.length
      }
    }
  } finally {
    isLoading.value = false
    isReasoningPhase.value = false
    abortController = null
    currentReader = null
    currentStreamingIndex.value = null
    chatAreaRef.value?.scrollToBottom()
  }
}

// 停止生成
const stopGeneration = async () => {
  if (abortController) {
    abortController.abort()
  }
  if (currentReader) {
    try {
      await currentReader.cancel()
    } catch (e) {
      // 忽略取消错误
    }
  }

  if (currentStreamingIndex.value !== null && messages.value[currentStreamingIndex.value]) {
    const msg = messages.value[currentStreamingIndex.value]
    msg.isStreaming = false
    msg.stopped = true
    if (msg.content) {
      msg.content += '\n\n*[已停止生成]*'
    } else if (msg.reasoning) {
      msg.content = '*[已停止生成]*'
    }
    msg.stats = {
      ...stats.value,
      endTime: Date.now(),
      reasoningLength: currentReasoning.value.length,
      contentLength: currentContent.value.length
    }
  }

  isLoading.value = false
  isReasoningPhase.value = false
  abortController = null
  currentReader = null
  currentStreamingIndex.value = null
}

// 编辑消息（删除原 user 消息及后续 → 重新发起）
const handleEditMessage = async (messageId, newContent, index) => {
  if (!messageId || !newContent) return
  await deleteMessageAndFollowing(messageId)
  messages.value = messages.value.slice(0, index)
  // sendMessage 会调 streamResponse；这里要让 Hermes 用 request body 而不是 DB 历史
  await sendMessage(newContent, { useRequestHistory: true })
}

// 重新生成（删除目标 AI 消息及后续 → 直接 streamResponse）
const handleRegenerate = async (messageId, index) => {
  if (!messageId) return
  let userMessageIndex = index - 1
  while (userMessageIndex >= 0 && messages.value[userMessageIndex].role !== 'user') {
    userMessageIndex--
  }
  if (userMessageIndex < 0) return
  await deleteMessageAndFollowing(messageId)
  messages.value = messages.value.slice(0, index)
  // 让 Hermes 把请求体的 messages 当成真实的对话历史
  await streamResponse(null, { useRequestHistory: true })
}

// ===== 文件处理 =====
const triggerFileInput = () => {
  fileInputRef.value?.click()
}

const acceptFile = (file) => {
  if (!file) return
  const isImage = file.type.startsWith('image/')
  const isPdf = file.type === 'application/pdf' || file.name.toLowerCase().endsWith('.pdf')
  if (!isImage && !isPdf) {
    alert('支持图片和 PDF 文件')
    return
  }
  if (file.size > 20 * 1024 * 1024) {
    alert('文件不能超过 20MB')
    return
  }
  selectedFile.value = file
  fileType.value = isImage ? 'image' : 'pdf'
  if (isImage) {
    const reader = new FileReader()
    reader.onload = (e) => { filePreview.value = e.target.result }
    reader.readAsDataURL(file)
  } else {
    filePreview.value = file.name
  }
}

const handleFileSelect = (event) => {
  acceptFile(event.target.files?.[0])
}

const removeFile = () => {
  selectedFile.value = null
  filePreview.value = null
  fileType.value = null
  if (fileInputRef.value) fileInputRef.value.value = ''
}

// 拖拽处理
const handleDragOver = (e) => { e.preventDefault(); isDragging.value = true }
const handleDragLeave = () => { isDragging.value = false }
const handleDrop = (e) => {
  e.preventDefault()
  isDragging.value = false
  const file = e.dataTransfer?.files?.[0]
  if (file) acceptFile(file)
}

const handlePaste = (event) => {
  const items = event.clipboardData?.items
  if (!items) return
  for (const item of items) {
    if (item.type.startsWith('image/') || item.type === 'application/pdf') {
      event.preventDefault()
      acceptFile(item.getAsFile())
      break
    }
  }
}

const handleSend = async () => {
  await sendMessage()
  removeFile()
}

// ===== 语音录制 =====
const toggleRecording = async () => {
  if (isRecording.value) {
    stopRecording()
  } else {
    await startRecording()
  }
}

const startRecording = async () => {
  try {
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
      if (location.protocol === 'http:' && location.hostname !== 'localhost' && location.hostname !== '127.0.0.1') {
        alert('语音输入需要 HTTPS 安全连接。')
      } else {
        alert('您的浏览器不支持语音录制功能。')
      }
      return
    }

    const stream = await navigator.mediaDevices.getUserMedia({
      audio: { channelCount: 1, sampleRate: 16000 }
    })

    const mimeType = MediaRecorder.isTypeSupported('audio/webm;codecs=opus')
      ? 'audio/webm;codecs=opus'
      : 'audio/webm'

    mediaRecorder = new MediaRecorder(stream, { mimeType })
    audioChunks = []
    recordingDuration.value = 0

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

    recordingTimer = setInterval(() => {
      recordingDuration.value++
      if (recordingDuration.value >= 60) {
        stopRecording()
      }
    }, 1000)

    mediaRecorder.start(1000)
    isRecording.value = true

  } catch (error) {
    console.error('录音失败:', error)
    if (error.name === 'NotAllowedError') {
      alert('请允许麦克风访问权限')
    } else if (error.name === 'NotFoundError') {
      alert('未找到麦克风设备')
    } else {
      alert('录音初始化失败: ' + error.message)
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
    alert('语音转录失败: ' + error.message)
  } finally {
    isTranscribing.value = false
    recordingDuration.value = 0
  }
}

// ===== MathJax 渲染 =====
const renderMath = async () => {
  await nextTick()
  if (window.MathJax) {
    window.MathJax.typesetPromise?.()
  }
}

// ===== 侧边栏控制 =====
const toggleSidebar = () => {
  isSidebarCollapsed.value = !isSidebarCollapsed.value
}

// ===== 快捷问题 =====
const handleQuickAsk = (prompt) => {
  inputMessage.value = prompt
  sendMessage()
}

// ===== 初始化 =====
// macOS 窗口圆角会裁切四角，露出 body 背景色；覆盖为浅色，离开时还原
const _prevBodyBg = document.body.style.backgroundColor
document.body.style.backgroundColor = '#f8f8f6' // warm stone-50

onUnmounted(() => {
  if (memoryRefreshTimer) {
    clearTimeout(memoryRefreshTimer)
    memoryRefreshTimer = null
  }
  document.body.style.backgroundColor = _prevBodyBg
})

// 进入 AI Lab 前先检查是否已开通；未开通的访客送到激活页
const verifyAiLabAccess = async () => {
  try {
    const r = await fetch(`${API_BASE_URL}/api/ai/me/`, { headers: djangoHeaders() })
    if (!r.ok) return
    const me = await r.json()
    if (!me.is_owner && !me.ai_lab_enabled) {
      router.replace('/ai-lab/activate')
    }
  } catch { /* silent */ }
}

onMounted(async () => {
  // 门禁优先 —— 未开通用户拉对话列表会 403，不如直接跳激活页
  await verifyAiLabAccess()

  // 加载 MathJax
  if (!window.MathJax) {
    window.MathJax = {
      tex: {
        inlineMath: [['\\(', '\\)']],
        displayMath: [['\\[', '\\]']],
      },
      svg: { fontCache: 'global' },
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

  // 获取会话列表
  await fetchConversations()

  // 如果有会话，选择第一个
  if (conversations.value.length > 0) {
    await selectConversation(conversations.value[0].id)
  }

  setTimeout(renderMath, 500)
})
</script>

<template>
  <div class="h-dvh w-full fixed inset-0 flex overflow-hidden" style="background: #f8f8f6; font-family: var(--ai-font-body);"
       @dragover="handleDragOver" @dragleave="handleDragLeave" @drop="handleDrop">
    <!-- 侧边栏 -->
    <AiLabSidebar
      :conversations="conversations"
      :current-id="currentConversationId"
      :is-collapsed="isSidebarCollapsed"
      @select="selectConversation"
      @new="startNewConversation"
      @delete="deleteConversation"
      @toggle-collapse="toggleSidebar"
    />

    <!-- 主内容区 -->
    <div class="flex-1 flex flex-col min-w-0 relative">
      <!-- 顶部栏（所有屏幕都显示；汉堡按钮仍然只在移动端） -->
      <header class="shrink-0 h-12 border-b flex items-center px-4 gap-3" style="border-color: var(--theme-200); background: var(--theme-50);">
        <button
          @click="toggleSidebar"
          class="w-8 h-8 rounded-md items-center justify-center transition-colors cursor-pointer flex lg:hidden"
          style="color: var(--theme-500);"
        >
          <svg class="w-[18px] h-[18px]" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="1.5">
            <path stroke-linecap="round" stroke-linejoin="round" d="M3.75 6.75h16.5M3.75 12h16.5M3.75 17.25h16.5"/>
          </svg>
        </button>

        <div class="flex items-center gap-2 flex-1 min-w-0 lg:hidden">
          <span class="text-[14px] font-semibold tracking-tight" style="color: var(--theme-700);">MyAgent</span>
        </div>
        <!-- 桌面端会话标题占据中间位置 -->
        <div class="hidden lg:flex flex-1 min-w-0"></div>

        <AiLabUserMenu />

        <!-- Agent Panel 入口（Tools / Skills / Memory / Inbox）+ Inbox 未读 badge -->
        <button
          @click="isPanelOpen = !isPanelOpen"
          class="w-8 h-8 rounded-md flex items-center justify-center transition-colors cursor-pointer relative"
          :style="isPanelOpen ? 'color: var(--theme-700); background: var(--theme-100);' : 'color: var(--theme-400);'"
          title="Agent Panel"
        >
          <svg class="w-[18px] h-[18px]" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="1.5">
            <path stroke-linecap="round" stroke-linejoin="round" d="M10.5 6h9.75M10.5 6a1.5 1.5 0 11-3 0m3 0a1.5 1.5 0 10-3 0M3.75 6H7.5m3 12h9.75m-9.75 0a1.5 1.5 0 01-3 0m3 0a1.5 1.5 0 00-3 0m-3.75 0H7.5m9-6h3.75m-3.75 0a1.5 1.5 0 01-3 0m3 0a1.5 1.5 0 00-3 0m-9.75 0h9.75"/>
          </svg>
          <span
            v-if="panelUnreadCount > 0"
            class="absolute -top-0.5 -right-0.5 min-w-[14px] h-[14px] rounded-full text-[10px] font-semibold flex items-center justify-center px-1"
            style="background: #ef4444; color: #fff;"
          >{{ panelUnreadCount > 99 ? '99+' : panelUnreadCount }}</span>
        </button>
      </header>

      <!-- 欢迎屏 / 聊天区域 -->
      <AiLabWelcome
        v-if="!hasMessages"
        v-model="inputMessage"
        :is-loading="isLoading"
        :is-recording="isRecording"
        :is-transcribing="isTranscribing"
        :is-ocr-processing="isFileProcessing"
        :recording-duration="recordingDuration"
        :has-image="!!selectedFile"
        :file-attachment="selectedAttachment"
        :session-tokens="sessionTokens"
        :context-limit="TOKEN_CONTEXT_LIMIT"
        @ask="handleQuickAsk"
        @send="handleSend"
        @stop="stopGeneration"
        @image-click="triggerFileInput"
        @voice-click="toggleRecording"
        @paste="handlePaste"
        @remove-file="removeFile"
      />

      <AiLabChatArea
        v-else
        ref="chatAreaRef"
        :messages="messages"
        :current-streaming-index="currentStreamingIndex"
        :is-reasoning-phase="isReasoningPhase"
        :conversation-title="conversationTitle"
        @edit="handleEditMessage"
        @regenerate="handleRegenerate"
      />

      <!-- 拖拽遮罩 -->
      <Transition name="fade">
        <div v-if="isDragging" class="absolute inset-0 z-50 flex items-center justify-center" style="background: rgba(248,248,246,0.9); border: 2px dashed var(--theme-300);">
          <div class="text-center">
            <svg class="w-10 h-10 mx-auto mb-2" style="color: var(--theme-400);" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="1.5">
              <path stroke-linecap="round" stroke-linejoin="round" d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5m-13.5-9L12 3m0 0l4.5 4.5M12 3v13.5"/>
            </svg>
            <p class="text-[14px]" style="color: var(--theme-500);">拖放文件到此处</p>
            <p class="text-[12px]" style="color: var(--theme-400);">支持图片和 PDF</p>
          </div>
        </div>
      </Transition>

      <!-- 隐藏的文件输入 -->
      <input
        ref="fileInputRef"
        type="file"
        accept="image/*,.pdf,application/pdf"
        class="hidden"
        @change="handleFileSelect"
      />

      <!-- 输入区域 -->
      <AiLabInput
        v-if="hasMessages"
        v-model="inputMessage"
        :is-loading="isLoading"
        :is-recording="isRecording"
        :is-transcribing="isTranscribing"
        :is-ocr-processing="isFileProcessing"
        :recording-duration="recordingDuration"
        :has-image="!!selectedFile"
        :file-attachment="selectedAttachment"
        :session-tokens="sessionTokens"
        :context-limit="TOKEN_CONTEXT_LIMIT"
        @send="handleSend"
        @stop="stopGeneration"
        @image-click="triggerFileInput"
        @voice-click="toggleRecording"
        @paste="handlePaste"
        @remove-file="removeFile"
      />
    </div>

    <!-- 右侧面板 -->
    <AiLabPanel ref="panelRef" :visible="isPanelOpen" @close="isPanelOpen = false" />

    <!-- 移动端侧边栏遮罩 -->
    <Transition name="fade">
      <div
        v-if="!isSidebarCollapsed"
        class="fixed inset-0 bg-black/50 z-40 lg:hidden"
        @click="isSidebarCollapsed = true"
      ></div>
    </Transition>
  </div>
</template>

<style>
/* The Quiet Studio — CSS variables must be unscoped to cascade into child components */
:root {
  --theme-50: #f8f8f6;
  --theme-100: #f0f0ed;
  --theme-200: #e4e4df;
  --theme-300: #c8c8c1;
  --theme-400: #9c9c93;
  --theme-500: #6b6b63;
  --theme-600: #484843;
  --theme-700: #2d2d28;
  --theme-gradient: #2d2d28;
  --theme-gradient-btn: #2d2d28;
  --theme-shadow: rgba(45, 45, 40, 0.06);
  --ai-accent: #3d7cc9;
  --ai-accent-hover: #2e6ab5;
  --ai-accent-soft: #edf2f8;
  --ai-font-display: 'Bricolage Grotesque', ui-sans-serif, system-ui, -apple-system, sans-serif;
  --ai-font-body: 'Geist', ui-sans-serif, system-ui, -apple-system, 'Helvetica Neue', sans-serif;
  --ai-font-mono: 'Geist Mono', ui-monospace, SFMono-Regular, Menlo, monospace;
}
</style>

<style scoped>

/* 动态视口高度兼容 */
.h-dvh {
  height: 100vh;
  height: 100dvh;
}

/* 淡入淡出动画 */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

/* 全局滚动条 */
::-webkit-scrollbar {
  width: 6px;
  height: 6px;
}

::-webkit-scrollbar-track {
  background: transparent;
}

::-webkit-scrollbar-thumb {
  background: #d1d5db;
  border-radius: 3px;
}

::-webkit-scrollbar-thumb:hover {
  background: #9ca3af;
}

/* 隐藏滚动条但保持功能 */
.scrollbar-hide {
  -ms-overflow-style: none;
  scrollbar-width: none;
}

.scrollbar-hide::-webkit-scrollbar {
  display: none;
}
</style>
