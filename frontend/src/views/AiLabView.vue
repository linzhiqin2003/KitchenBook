<script setup>
import { ref, computed, nextTick, onMounted, watch } from 'vue'
import API_BASE_URL from '../config/api'
import { AiLabSidebar, AiLabWelcome, AiLabInput, AiLabChatArea } from '../components/ailab'

// ===== 会话管理状态 =====
const conversations = ref([])
const currentConversationId = ref(null)
const currentConversation = ref(null)
// 移动端默认折叠侧边栏
const isSidebarCollapsed = ref(window.innerWidth < 1024)
const isLoadingConversations = ref(false)

// ===== 聊天状态 =====
const isLoading = ref(false)
const inputMessage = ref('')
const messages = ref([])
const chatAreaRef = ref(null)

// ===== 图片/语音状态 =====
const selectedImage = ref(null)
const imagePreview = ref(null)
const isOcrProcessing = ref(false)
const ocrResult = ref(null)
const fileInputRef = ref(null)
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

const normalizeAssistantMessage = (message) => {
  if (message?.role !== 'assistant') {
    return message
  }
  return {
    ...message,
    phase: message.phase || STREAM_PHASE.IDLE,
    subTurns: Array.isArray(message.subTurns) ? message.subTurns : [],
    currentReasoning: message.currentReasoning || '',
    currentToolCall: message.currentToolCall || null
  }
}

const normalizeMessagesForUI = (list) => {
  return (list || []).map(normalizeAssistantMessage)
}

// ===== API 调用 =====

// 获取会话列表
const fetchConversations = async () => {
  isLoadingConversations.value = true
  try {
    const response = await fetch(`${API_BASE_URL}/api/ai/conversations/`)
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
    const response = await fetch(`${API_BASE_URL}/api/ai/conversations/${id}/`)
    if (response.ok) {
      const data = await response.json()
      currentConversation.value = data
      messages.value = normalizeMessagesForUI(data.messages || [])
      await nextTick()
      chatAreaRef.value?.scrollToBottom()
      renderMath()
    }
  } catch (error) {
    console.error('获取会话详情失败:', error)
  }
}

// 创建新会话
const createConversation = async () => {
  try {
    const response = await fetch(`${API_BASE_URL}/api/ai/conversations/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ title: '新对话' })
    })
    if (response.ok) {
      const data = await response.json()
      conversations.value.unshift(data)
      await selectConversation(data.id)
    }
  } catch (error) {
    console.error('创建会话失败:', error)
  }
}

// 选择会话
const selectConversation = async (id) => {
  currentConversationId.value = id
  await fetchConversation(id)
}

// 删除会话
const deleteConversation = async (id) => {
  if (!confirm('确定要删除这个对话吗？')) return

  try {
    const response = await fetch(`${API_BASE_URL}/api/ai/conversations/${id}/`, {
      method: 'DELETE'
    })
    if (response.ok) {
      conversations.value = conversations.value.filter(c => c.id !== id)
      if (currentConversationId.value === id) {
        currentConversationId.value = null
        currentConversation.value = null
        messages.value = []
      }
    }
  } catch (error) {
    console.error('删除会话失败:', error)
  }
}

// 保存消息到后端
const saveMessage = async (conversationId, role, content, reasoning = null) => {
  try {
    const response = await fetch(`${API_BASE_URL}/api/ai/conversations/${conversationId}/messages/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ role, content, reasoning })
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
      method: 'DELETE'
    })
  } catch (error) {
    console.error('删除消息失败:', error)
  }
}

// ===== 消息发送 =====
const sendMessage = async (content = null) => {
  const text = content || inputMessage.value.trim()
  if (!text || isLoading.value) return

  // 如果没有当前会话，先创建一个
  if (!currentConversationId.value) {
    await createConversation()
  }

  // 添加用户消息
  const userMessage = { role: 'user', content: text, type: 'text' }
  messages.value.push(userMessage)
  inputMessage.value = ''

  // 保存用户消息到后端
  const savedUserMsg = await saveMessage(currentConversationId.value, 'user', text)
  if (savedUserMsg) {
    userMessage.id = savedUserMsg.id
  }

  // 刷新会话列表以更新标题
  fetchConversations()

  // 开始流式响应
  await streamResponse()
}

// 流式响应
const streamResponse = async () => {
  isLoading.value = true
  currentReasoning.value = ''
  currentContent.value = ''
  isReasoningPhase.value = false
  stats.value = { reasoningLength: 0, contentLength: 0, startTime: Date.now(), endTime: null }

  // 添加空的 AI 消息用于流式填充
  const aiMessageIndex = messages.value.length
  currentStreamingIndex.value = aiMessageIndex
  messages.value.push({
    role: 'assistant',
    content: '',
    reasoning: '',
    type: 'text',
    isStreaming: true,
    phase: STREAM_PHASE.REASONING,
    subTurns: [],
    currentReasoning: '',
    currentToolCall: null
  })

  let streamPhase = STREAM_PHASE.REASONING
  let activeReasoning = ''
  let activeToolIndex = null
  let hasDoneEvent = false
  const streamSubTurns = []
  const streamToolCalls = new Map()

  const getAiMessage = () => messages.value[aiMessageIndex]

  const syncTraceState = () => {
    const aiMsg = getAiMessage()
    if (!aiMsg) return
    aiMsg.phase = streamPhase
    aiMsg.subTurns = streamSubTurns.map(turn => ({
      ...turn,
      toolCall: turn.toolCall ? { ...turn.toolCall } : null
    }))
    aiMsg.currentReasoning = activeReasoning
    if (activeToolIndex === null) {
      aiMsg.currentToolCall = null
      return
    }
    const activeCall = streamToolCalls.get(activeToolIndex)
    aiMsg.currentToolCall = activeCall ? { ...activeCall } : null
  }

  const pushSubTurns = () => {
    const hasReasoning = Boolean(activeReasoning.trim())
    if (!hasReasoning && streamToolCalls.size === 0) {
      return
    }

    const orderedToolCalls = Array.from(streamToolCalls.values()).sort((a, b) => a.index - b.index)
    if (orderedToolCalls.length === 0) {
      streamSubTurns.push({
        id: createTraceId(),
        reasoning: activeReasoning.trim(),
        toolCall: null
      })
    } else {
      orderedToolCalls.forEach((toolCall, index) => {
        streamSubTurns.push({
          id: createTraceId(),
          reasoning: index === 0 ? activeReasoning.trim() : '',
          toolCall: { ...toolCall }
        })
      })
    }

    activeReasoning = ''
    streamToolCalls.clear()
    activeToolIndex = null
    syncTraceState()
  }

  const setPhase = (nextPhase) => {
    if (nextPhase === streamPhase) {
      return
    }

    // 工具调用结束后切回 reasoning/answering 时，归档本轮 sub-turn
    if (
      (nextPhase === STREAM_PHASE.REASONING || nextPhase === STREAM_PHASE.ANSWERING || nextPhase === STREAM_PHASE.IDLE) &&
      streamToolCalls.size > 0
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
    const existing = streamToolCalls.get(index) || {
      id: fragment.id || `call_${createTraceId()}`,
      index,
      name: '',
      argumentsText: '',
      parsedArguments: null,
      status: TOOL_STATUS.PARSING,
      result: '',
      error: '',
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
    if (fragment.durationMs && !existing.finishedAt) {
      existing.finishedAt = existing.startedAt + fragment.durationMs
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
    setPhase(STREAM_PHASE.REASONING)
    currentReasoning.value += chunk
    activeReasoning += chunk
    const aiMsg = getAiMessage()
    if (aiMsg) {
      aiMsg.reasoning = currentReasoning.value
    }
    syncTraceState()
    chatAreaRef.value?.scrollToBottom()
  }

  const appendContentChunk = (chunk) => {
    if (!chunk) return
    setPhase(STREAM_PHASE.ANSWERING)
    currentContent.value += chunk
    const aiMsg = getAiMessage()
    if (aiMsg) {
      aiMsg.content = currentContent.value
    }
    syncTraceState()
    chatAreaRef.value?.scrollToBottom()
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

    if (eventType === 'tool_execution_start') {
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
        eventType === 'tool_execution_start'
          ? TOOL_STATUS.RUNNING
          : eventType === 'tool_execution_error'
            ? TOOL_STATUS.ERROR
            : eventType === 'tool_execution_result' || eventType === 'tool_result'
              ? TOOL_STATUS.SUCCESS
              : TOOL_STATUS.PARSING
      ),
      result: payload.result ?? payload.output,
      error: payload.error,
      durationMs: payload.duration_ms || payload.durationMs
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
    .filter(m => m.type === 'text' && (m.role === 'user' || m.role === 'assistant') && !m.isStreaming)
    .map(m => ({
      role: m.role,
      content: m.content?.replace(/\n\n\*\[已停止生成\]\*$/, '') || ''
    }))
    .filter(m => m.content)

  abortController = new AbortController()

  try {
    const response = await fetch(`${API_BASE_URL}/api/ai/speciale/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ messages: apiMessages }),
      signal: abortController.signal
    })

    if (!response.ok) {
      const error = await response.json()
      throw new Error(error.error || '请求失败')
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

      for (const line of lines) {
        if (!line || line.startsWith(':')) continue

        if (line.startsWith('data: ')) {
          const data = line.slice(6).trim()
          if (data === '[DONE]') break
          if (!data) continue

          try {
            const parsed = JSON.parse(data)
            handleStreamEvent(parsed)
          } catch (e) {
            if (!(e instanceof SyntaxError)) {
              throw e
            }
          }
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

    // 保存 AI 消息到后端
    const savedAiMsg = await saveMessage(
      currentConversationId.value,
      'assistant',
      currentContent.value,
      currentReasoning.value
    )
    if (savedAiMsg) {
      messages.value[aiMessageIndex].id = savedAiMsg.id
    }

    renderMath()

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

// 编辑消息
const handleEditMessage = async (messageId, newContent, index) => {
  if (!messageId || !newContent) return

  // 删除该消息及后续
  await deleteMessageAndFollowing(messageId)

  // 从本地移除该消息及后续
  messages.value = messages.value.slice(0, index)

  // 重新发送
  await sendMessage(newContent)
}

// 重新生成
const handleRegenerate = async (messageId, index) => {
  if (!messageId) return

  // 找到对应的用户消息
  let userMessageIndex = index - 1
  while (userMessageIndex >= 0 && messages.value[userMessageIndex].role !== 'user') {
    userMessageIndex--
  }

  if (userMessageIndex < 0) return

  const userContent = messages.value[userMessageIndex].content

  // 删除 AI 消息
  await deleteMessageAndFollowing(messageId)

  // 从本地移除该消息及后续
  messages.value = messages.value.slice(0, index)

  // 重新生成
  await streamResponse()
}

// ===== 图片处理 =====
const triggerFileInput = () => {
  fileInputRef.value?.click()
}

const handleFileSelect = (event) => {
  const file = event.target.files?.[0]
  if (!file) return

  if (!file.type.startsWith('image/')) {
    alert('请选择图片文件')
    return
  }

  if (file.size > 10 * 1024 * 1024) {
    alert('图片大小不能超过 10MB')
    return
  }

  selectedImage.value = file

  const reader = new FileReader()
  reader.onload = (e) => {
    imagePreview.value = e.target.result
  }
  reader.readAsDataURL(file)
  ocrResult.value = null
}

const removeImage = () => {
  selectedImage.value = null
  imagePreview.value = null
  ocrResult.value = null
  if (fileInputRef.value) {
    fileInputRef.value.value = ''
  }
}

const processOCR = async () => {
  if (!selectedImage.value || isOcrProcessing.value) return

  isOcrProcessing.value = true
  ocrResult.value = null

  try {
    const formData = new FormData()
    formData.append('image', selectedImage.value)

    const response = await fetch(`${API_BASE_URL}/api/ai/ocr/`, {
      method: 'POST',
      body: formData
    })

    const data = await response.json()

    if (!response.ok) {
      throw new Error(data.error || 'OCR 识别失败')
    }

    ocrResult.value = data.markdown
    inputMessage.value = `请解答以下题目：\n\n${data.markdown}`

  } catch (error) {
    alert(`OCR 识别失败: ${error.message}`)
  } finally {
    isOcrProcessing.value = false
  }
}

const handlePaste = (event) => {
  const items = event.clipboardData?.items
  if (!items) return

  for (const item of items) {
    if (item.type.startsWith('image/')) {
      event.preventDefault()
      const file = item.getAsFile()
      if (file) {
        selectedImage.value = file
        const reader = new FileReader()
        reader.onload = (e) => {
          imagePreview.value = e.target.result
        }
        reader.readAsDataURL(file)
        ocrResult.value = null
      }
      break
    }
  }
}

const handleSend = async () => {
  if (selectedImage.value && !ocrResult.value) {
    await processOCR()
    if (!ocrResult.value) return
  }
  await sendMessage()
  removeImage()
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
onMounted(async () => {
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
  <div class="h-dvh w-full fixed inset-0 bg-gradient-to-br from-slate-50 via-white to-violet-50/30 flex overflow-hidden">
    <!-- 侧边栏 -->
    <AiLabSidebar
      :conversations="conversations"
      :current-id="currentConversationId"
      :is-collapsed="isSidebarCollapsed"
      @select="selectConversation"
      @new="createConversation"
      @delete="deleteConversation"
      @toggle-collapse="toggleSidebar"
    />

    <!-- 主内容区 -->
    <div class="flex-1 flex flex-col min-w-0">
      <!-- 移动端顶部栏 -->
      <header class="shrink-0 h-14 bg-white/80 backdrop-blur-sm border-b border-gray-200 flex items-center px-4 gap-3 lg:hidden">
        <button
          @click="toggleSidebar"
          class="w-9 h-9 rounded-lg hover:bg-gray-100 flex items-center justify-center transition-colors cursor-pointer"
        >
          <svg class="w-5 h-5 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16"/>
          </svg>
        </button>

        <div class="flex items-center gap-2 flex-1 min-w-0">
          <div class="w-8 h-8 rounded-lg bg-gradient-to-br from-violet-500 to-purple-600 flex items-center justify-center shadow-md shrink-0">
            <span class="text-sm">✨</span>
          </div>
          <div class="min-w-0">
            <h1 class="text-sm font-semibold text-gray-800 truncate">AI Lab</h1>
          </div>
        </div>

        <router-link
          to="/ai-lab/studio"
          class="w-9 h-9 rounded-lg bg-violet-50 hover:bg-violet-100 flex items-center justify-center transition-colors"
          title="AI Studio"
        >
          <span class="text-sm">🎙️</span>
        </router-link>
      </header>

      <!-- 欢迎屏 / 聊天区域 -->
      <AiLabWelcome
        v-if="!hasMessages"
        :is-loading="isLoading"
        @ask="handleQuickAsk"
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

      <!-- 图片预览 -->
      <Transition name="fade">
        <div v-if="imagePreview" class="shrink-0 px-4 pb-2">
          <div class="max-w-4xl mx-auto p-3 bg-gray-50 rounded-xl border border-gray-200">
            <div class="flex items-start gap-3">
              <div class="relative shrink-0">
                <img
                  :src="imagePreview"
                  alt="预览"
                  class="w-20 h-20 object-cover rounded-lg border border-gray-200"
                />
                <button
                  @click="removeImage"
                  class="absolute -top-2 -right-2 w-6 h-6 bg-red-500 hover:bg-red-600 text-white rounded-full flex items-center justify-center shadow-md cursor-pointer"
                >
                  <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
                  </svg>
                </button>
              </div>
              <div class="flex-1 min-w-0">
                <div class="text-sm text-gray-600 mb-2 truncate">{{ selectedImage?.name }}</div>
                <div v-if="ocrResult" class="text-xs text-green-600 flex items-center gap-1">
                  <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/>
                  </svg>
                  已识别
                </div>
                <button
                  v-else
                  @click="processOCR"
                  :disabled="isOcrProcessing"
                  class="px-3 py-1.5 text-xs bg-violet-600 hover:bg-violet-500 text-white rounded-lg disabled:bg-gray-300 cursor-pointer flex items-center gap-1.5"
                >
                  <svg v-if="isOcrProcessing" class="w-3.5 h-3.5 animate-spin" fill="none" viewBox="0 0 24 24">
                    <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                    <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"></path>
                  </svg>
                  {{ isOcrProcessing ? '识别中...' : '识别图片' }}
                </button>
              </div>
            </div>
          </div>
        </div>
      </Transition>

      <!-- 隐藏的文件输入 -->
      <input
        ref="fileInputRef"
        type="file"
        accept="image/*"
        class="hidden"
        @change="handleFileSelect"
      />

      <!-- 输入区域（有消息时显示） -->
      <AiLabInput
        v-if="hasMessages"
        v-model="inputMessage"
        :is-loading="isLoading"
        :is-recording="isRecording"
        :is-transcribing="isTranscribing"
        :is-ocr-processing="isOcrProcessing"
        :recording-duration="recordingDuration"
        :has-image="!!selectedImage"
        @send="handleSend"
        @stop="stopGeneration"
        @image-click="triggerFileInput"
        @voice-click="toggleRecording"
        @paste="handlePaste"
      />
    </div>

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

<style scoped>
/* 主题变量 */
:root {
  --theme-50: #f5f3ff;
  --theme-100: #ede9fe;
  --theme-200: #ddd6fe;
  --theme-300: #c4b5fd;
  --theme-400: #a78bfa;
  --theme-500: #8b5cf6;
  --theme-600: #7c3aed;
  --theme-700: #6d28d9;
  --theme-gradient: linear-gradient(135deg, #8b5cf6, #d946ef);
  --theme-gradient-btn: linear-gradient(to right, #8b5cf6, #9333ea);
  --theme-shadow: rgba(139, 92, 246, 0.2);
}

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
