<template>
  <transition name="fade-up">
    <div class="chat-wrapper" v-if="questionAnswered">
      
      <!-- 1. Floating Toggle Button (Visible when chat is closed) -->
      <button 
        v-show="!isOpen"
        @click="isOpen = true"
        class="chat-toggle-fab"
        title="打开AI助手"
      >
        <div class="fab-icon">💬</div>
      </button>

      <!-- 2. Main Chat Window -->
      <transition name="scale-in">
        <div 
          v-if="isOpen" 
          class="chat-window"
          :style="{ width: windowWidth + 'px', height: windowHeight + 'px' }"
        >
          <!-- Resize Handle (Top-Left) -->
          <div class="resize-handle" @mousedown.prevent="startResize">
            <svg viewBox="0 0 24 24" width="24" height="24" fill="none" class="resize-icon">
              <path d="M15 6L6 15" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
              <path d="M20 11L11 20" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
            </svg>
          </div>
          
          <!-- Header -->
          <div class="chat-header">
            <div class="header-left">
              <div class="avatar-circle">
                <span class="avatar-emoji">{{ mode === 'qa' ? '🎓' : '🧐' }}</span>
              </div>
              <div class="header-text">
                <div class="header-title">{{ mode === 'qa' ? 'AI Tutor' : 'AI Reviewer' }}</div>
                <!-- <div class="header-subtitle">Your Study Companion</div> -->
              </div>
            </div>

            <div class="header-right">
              <!-- Mode Switcher -->
              <div class="mode-switch">
                <button 
                  @click="mode = 'qa'"
                  :class="{ active: mode === 'qa' }"
                  class="switch-item"
                >
                  答疑
                </button>
                <button 
                  @click="mode = 'review'"
                  :class="{ active: mode === 'review' }"
                  class="switch-item"
                >
                  审核
                </button>
              </div>

              <!-- Close Button -->
              <button @click="isOpen = false" class="close-btn" title="关闭">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M18 6L6 18M6 6L18 18" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
              </button>
            </div>
          </div>

          <!-- Status Bar (Mode Indicator) -->
          <div class="status-bar" :class="mode">
            <div class="status-dot"></div>
            <span>{{ mode === 'qa' ? '正在为您解答疑惑...' : '正在审核题目质量...' }}</span>
          </div>

          <!-- Messages Area -->
          <div class="chat-messages" ref="messagesContainer">
            <!-- Empty State -->
            <div v-if="messages.length === 0" class="empty-state">
              <div class="empty-icon">{{ mode === 'qa' ? '🎓' : '🧐' }}</div>
              <h3>{{ mode === 'qa' ? '我是您的 AI 导师' : '题目质量审核员' }}</h3>
              <p>
                {{ mode === 'qa' ? '对当前题目有任何疑问？' : '觉得这道题有问题？' }}<br>
                {{ mode === 'qa' ? '随时向我提问，我会为您答疑解惑。' : '告诉我已发现的错误，我们一起修正它。' }}
              </p>
            </div>

            <!-- Message List -->
            <div
              v-for="(msg, index) in messages"
              :key="index"
              class="message-row"
              :class="msg.role"
            >
              <div class="message-avatar">
                <template v-if="msg.role === 'user'">
                  🧑‍🎓
                </template>
                <template v-else>
                  {{ mode === 'qa' ? '🎓' : '🧐' }}
                </template>
              </div>
              <div class="message-bubble-container">
                <div class="message-bubble" v-html="formatMessage(msg.content)"></div>
                
                <!-- Delete Recommendation Action -->
                <div v-if="msg.recommendDelete" class="action-card warning">
                  <div class="action-header">
                    <span class="icon">⚠️</span>
                    <span class="title">建议删除此题</span>
                  </div>
                  <button 
                    @click="requestDeletion" 
                    class="action-btn danger"
                    :disabled="deleteLoading"
                  >
                    {{ deleteLoading ? '确认中...' : '确认删除' }}
                  </button>
                </div>
              </div>
            </div>

            <!-- Streaming Pending -->
            <div v-if="streamingContent" class="message-row assistant">
              <div class="message-avatar">{{ mode === 'qa' ? '🎓' : '🧐' }}</div>
              <div class="message-bubble-container">
                <div class="message-bubble">
                  <span v-html="formatMessage(streamingContent)"></span>
                  <span class="cursor">▋</span>
                </div>
              </div>
            </div>

            <!-- Loading Indicator -->
             <div v-if="loading && !streamingContent" class="message-row assistant">
              <div class="message-avatar">{{ mode === 'qa' ? '🎓' : '🧐' }}</div>
              <div class="message-bubble">
                <div class="typing-dots">
                  <span></span><span></span><span></span>
                </div>
              </div>
            </div>

            <!-- Delete Result Feedback -->
            <div v-if="deleteResult" class="system-notice">
              <div v-if="deleteResult.deleted" class="notice-content success">
                ✅ 题目已成功删除
              </div>
              <div v-else class="notice-content error">
                <div class="notice-title">❌ 删除请求被拒绝</div>
                <div class="notice-desc">{{ deleteResult.reasoning }}</div>
              </div>
              <button @click="deleteResult = null" class="notice-close">✕</button>
            </div>

          </div>

          <!-- Footer Input -->
          <div class="chat-footer">
            <div class="input-container">
              <textarea
                v-model="inputText"
                @compositionstart="isComposing = true"
                @compositionend="onCompositionEnd"
                @keydown.enter.exact="handleEnter"
                placeholder="输入你的问题..."
                rows="1"
                class="chat-input"
                :disabled="loading"
              ></textarea>
              <button 
                @click="sendMessage"
                class="send-btn"
                :disabled="!inputText.trim() || loading"
              >
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M22 2L11 13M22 2L15 22L11 13M11 13L2 9L22 2"/>
                </svg>
              </button>
            </div>
          </div>

        </div>
      </transition>

    </div>
  </transition>
</template>

<script setup>
import { ref, watch, nextTick, defineProps, defineEmits } from 'vue';
import { questionApi } from '../api';
import { marked } from 'marked';

// Configure marked
marked.use({
  breaks: true, // Enable line breaks
  gfm: true     // Enable GitHub Flavored Markdown
});

const props = defineProps({
  currentQuestion: { type: Object, default: null },
  courseId: { type: String, default: null },
  questionAnswered: { type: Boolean, default: false },
  userAnswer: { type: Object, default: null }
});

const emit = defineEmits(['question-deleted']);

// State
const isOpen = ref(false);
const mode = ref('qa');
const messages = ref([]);
const inputText = ref('');
const isComposing = ref(false);
const loading = ref(false);
const streamingContent = ref('');
const deleteLoading = ref(false);
const deleteResult = ref(null);
const messagesContainer = ref(null);

// Resizable State
const windowWidth = ref(380);
const windowHeight = ref(600);
const isResizing = ref(false);

// Resize Logic
function startResize(e) {
  isResizing.value = true;
  const startX = e.clientX;
  const startY = e.clientY;
  const startWidth = windowWidth.value;
  const startHeight = windowHeight.value;

  function onMouseMove(e) {
    if (!isResizing.value) return;
    // Calculate deltas (Moving left increases width, moving up increases height)
    const deltaX = startX - e.clientX;
    const deltaY = startY - e.clientY;

    // Apply limits (Min: 300x400, Max: 800x900)
    windowWidth.value = Math.max(300, Math.min(800, startWidth + deltaX));
    windowHeight.value = Math.max(400, Math.min(900, startHeight + deltaY));
  }

  function onMouseUp() {
    isResizing.value = false;
    document.removeEventListener('mousemove', onMouseMove);
    document.removeEventListener('mouseup', onMouseUp);
  }

  document.addEventListener('mousemove', onMouseMove);
  document.addEventListener('mouseup', onMouseUp);
}

// Reset messages when mode changes
watch(mode, () => {
  messages.value = [];
  deleteResult.value = null;
  streamingContent.value = '';
});

// Reset when question changes
watch(() => props.currentQuestion?.id, () => {
  messages.value = [];
  deleteResult.value = null;
  streamingContent.value = '';
});

// Close when question is not answered (new question)
watch(() => props.questionAnswered, (answered) => {
  if (!answered) {
    isOpen.value = false;
    messages.value = [];
    streamingContent.value = '';
  }
});

// Auto-scroll
function scrollToBottom() {
  nextTick(() => {
    if (messagesContainer.value) {
      messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight;
    }
  });
}

watch([messages, streamingContent], () => {
  scrollToBottom();
}, { deep: true });

// Message Formatting
function formatMessage(text) {
  if (!text) return '';
  // Clean custom tags first (if any leftovers, though usually we handle clean text)
  const cleanText = text
    .replace(/\[RECOMMENDATION: DELETE\]/g, '')
    .replace(/\[CONFIRMED: DELETE\]/g, '')
    .replace(/\[REJECTED: KEEP\]/g, '');
    
  try {
    return marked.parse(cleanText);
  } catch (e) {
    return cleanText;
  }
}

// Input Handlers
function handleEnter(e) {
  if (isComposing.value) return;
  e.preventDefault();
  sendMessage();
}

function onCompositionEnd(e) {
  isComposing.value = false;
}

// Send Message
async function sendMessage() {
  if (!inputText.value.trim() || loading.value) return;
  if (!props.currentQuestion) return alert('当前没有可讨论的题目');
  
  const userMessage = inputText.value.trim();
  messages.value.push({ role: 'user', content: userMessage });
  inputText.value = '';
  loading.value = true;
  streamingContent.value = '';
  
  try {
    const questionData = {
      id: props.currentQuestion.id,
      topic: props.currentQuestion.topic,
      question_text: props.currentQuestion.question_text,
      options: props.currentQuestion.options,
      answer: props.currentQuestion.answer,
      explanation: props.currentQuestion.explanation,
      user_selected: props.userAnswer?.selected || null,
      user_correct: props.userAnswer?.correct ?? null
    };
    
    const config = questionApi.getChatStreamConfig(mode.value, messages.value, questionData, props.courseId);
    
    const response = await fetch(config.url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(config.data)
    });
    
    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let fullResponse = '';
    let recommendDelete = false;
    
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      const lines = decoder.decode(value).split('\n');
      for (const line of lines) {
        if (line.startsWith('data: ')) {
          try {
            const data = JSON.parse(line.slice(6));
            if (data.error) throw new Error(data.error);
            if (data.chunk) {
              fullResponse += data.chunk;
              streamingContent.value = fullResponse;
            }
            if (data.done) recommendDelete = data.recommend_delete || false;
          } catch (e) {
            // ignore JSON parse errors for partial chunks
          }
        }
      }
    }
    
    streamingContent.value = '';
    messages.value.push({
      role: 'assistant',
      content: fullResponse,
      recommendDelete
    });
    
  } catch (error) {
    console.error(error);
    streamingContent.value = '';
    messages.value.push({ role: 'assistant', content: '错误: ' + error.message });
  } finally {
    loading.value = false;
  }
}

// Request Deletion
async function requestDeletion() {
  if (!props.currentQuestion?.id) return;
  deleteLoading.value = true;
  try {
    const response = await questionApi.requestDelete(props.currentQuestion.id, messages.value);
    deleteResult.value = response.data;
    if (response.data.deleted) emit('question-deleted', props.currentQuestion.id);
  } catch (error) {
    deleteResult.value = { deleted: false, reasoning: error.message };
  } finally {
    deleteLoading.value = false;
  }
}
</script>

<style scoped>
/* --- Base Variables & Fonts --- */
.chat-wrapper {
  position: fixed;
  bottom: 24px;
  right: 24px;
  z-index: 9999;
  font-family: 'Inter', sans-serif;
  pointer-events: none; /* Allow clicks pass through wrapper area except children */
}
.chat-wrapper > * {
  pointer-events: auto;
}

/* --- Floating Toggle FAB --- */
.chat-toggle-fab {
  width: 56px;
  height: 56px;
  border-radius: 28px;
  background: #111827;
  color: white;
  border: none;
  cursor: pointer;
  box-shadow: 0 4px 12px rgba(0,0,0,0.15);
  transition: all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
  display: flex;
  align-items: center;
  justify-content: center;
  position: absolute;
  bottom: 0;
  right: 0;
}
.chat-toggle-fab:hover {
  transform: scale(1.1);
  box-shadow: 0 8px 16px rgba(0,0,0,0.2);
}
.fab-icon {
  font-size: 24px;
}

/* --- Chat Window --- */
.chat-window {
  position: absolute;
  bottom: 0;
  right: 0;
  /* width & height set by inline style */
  max-width: 90vw;
  max-height: calc(100vh - 40px);
  background: #FFFFFF;
  border-radius: 24px;
  box-shadow: 
    0 4px 6px -1px rgba(0, 0, 0, 0.05),
    0 10px 15px -3px rgba(0, 0, 0, 0.08), 
    0 0 0 1px rgba(0,0,0,0.05);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  transition: opacity 0.3s, transform 0.3s; /* Disable width/height transition during resize */
}

/* Resize Handle */
.resize-handle {
  position: absolute;
  top: 0;
  left: 0;
  width: 24px;
  height: 24px;
  cursor: nwse-resize;
  z-index: 50;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #9CA3AF;
  opacity: 0; /* Hidden by default, shown on hover */
  transition: opacity 0.2s;
  padding: 4px;
}

.chat-window:hover .resize-handle {
  opacity: 1;
}

.resize-handle:hover {
  color: #4F46E5;
}

/* Header */
.chat-header {
  padding: 16px 20px;
  background: white;
  border-bottom: 1px solid #F3F4F6;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.avatar-circle {
  width: 40px;
  height: 40px;
  border-radius: 12px;
  background: linear-gradient(135deg, #4F46E5, #818CF8);
  display: flex;
  align-items: center;
  justify-content: center;
}

.avatar-emoji {
  font-size: 20px;
}

.header-text {
  display: flex;
  flex-direction: column;
}

.header-title {
  font-weight: 700;
  color: #111827;
  font-size: 15px;
  line-height: 1.2;
}

.header-subtitle {
  font-size: 11px;
  color: #6B7280;
  font-weight: 500;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 8px;
}

.mode-switch {
  display: flex;
  background: #F3F4F6;
  padding: 2px;
  border-radius: 8px;
}

.switch-item {
  padding: 4px 10px;
  font-size: 12px;
  font-weight: 500;
  color: #6B7280;
  border-radius: 6px;
  border: none;
  background: transparent;
  cursor: pointer;
  transition: all 0.2s;
}

.switch-item:hover {
  color: #111827;
}

.switch-item.active {
  background: white;
  color: #4F46E5;
  box-shadow: 0 1px 2px rgba(0,0,0,0.05);
}

.close-btn {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: transparent;
  border: none;
  color: #9CA3AF;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s;
}
.close-btn:hover {
  background: #F3F4F6;
  color: #4B5563;
}

/* Status Bar */
.status-bar {
  padding: 6px 20px;
  font-size: 11px;
  color: #6B7280;
  background: #F9FAFB;
  display: flex;
  align-items: center;
  gap: 6px;
  border-bottom: 1px solid #F3F4F6;
}
.status-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #10B981;
}
.status-bar.review .status-dot { background: #F59E0B; }

/* Messages */
.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  background: white;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.message-row {
  display: flex;
  gap: 12px;
  max-width: 100%;
}
.message-row.user {
  flex-direction: row-reverse;
}

.message-avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: #F3F4F6;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
  flex-shrink: 0;
}
.message-row.user .message-avatar {
  background: #EEF2FF;
  color: #4F46E5;
}

.message-bubble-container {
  max-width: 80%;
  display: flex;
  flex-direction: column;
}

.message-bubble {
  padding: 10px 14px;
  border-radius: 16px;
  font-size: 14px;
  line-height: 1.5;
  word-wrap: break-word;
}

.message-row.assistant .message-bubble {
  background: #F9FAFB;
  color: #1F2937;
  border-top-left-radius: 4px;
  border: 1px solid #E5E7EB;
}

.message-row.user .message-bubble {
  background:linear-gradient(135deg, #4F46E5 0%, #4338CA 100%);
  color: white;
  border-top-right-radius: 4px;
  box-shadow: 0 2px 4px rgba(79, 70, 229, 0.2);
}

/* Footer Input */
.chat-footer {
  padding: 16px;
  border-top: 1px solid #F3F4F6;
  background: white;
}

.input-container {
  display: flex;
  align-items: flex-end;
  background: #F9FAFB;
  border: 1px solid #E5E7EB;
  border-radius: 20px;
  padding: 6px;
  transition: all 0.2s;
}

.input-container:focus-within {
  background: white;
  border-color: #4F46E5;
  box-shadow: 0 0 0 3px rgba(79, 70, 229, 0.1);
}

.chat-input {
  flex: 1;
  background: transparent;
  border: none;
  padding: 8px 12px;
  font-size: 14px;
  max-height: 100px;
  resize: none;
  outline: none;
  color: #111827;
}

.send-btn {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: #4F46E5;
  color: white;
  border: none;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s;
}

.send-btn:disabled {
  background: #E5E7EB;
  cursor: default;
}
.send-btn:hover:not(:disabled) {
  background: #4338CA;
  transform: scale(1.05);
}

/* Animations */
.scale-in-enter-active, .scale-in-leave-active {
  transition: all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
  transform-origin: bottom right;
}
.scale-in-enter-from, .scale-in-leave-to {
  opacity: 0;
  transform: scale(0.9) translateY(20px);
}

/* Typography Inside Bubble */
.message-bubble :deep(p) { margin-bottom: 8px; font-size: 14px; line-height: 1.6; }
.message-bubble :deep(p:last-child) { margin-bottom: 0; }

/* Headings */
.message-bubble :deep(h1),
.message-bubble :deep(h2), 
.message-bubble :deep(h3) {
  font-weight: 700;
  margin-top: 16px;
  margin-bottom: 8px;
  line-height: 1.3;
  color: #111827;
}
.message-bubble :deep(h1) { font-size: 1.25em; }
.message-bubble :deep(h2) { font-size: 1.1em; }
.message-bubble :deep(h3) { font-size: 1em; }

/* Lists */
.message-bubble :deep(ul), .message-bubble :deep(ol) {
  margin-bottom: 8px;
  padding-left: 20px;
}
.message-bubble :deep(li) {
  margin-bottom: 4px;
}
.message-bubble :deep(ul) { list-style-type: disc; }
.message-bubble :deep(ol) { list-style-type: decimal; }

/* Code Blocks & Inline Code */
.message-bubble :deep(code) { 
  font-family: 'Menlo', 'Monaco', 'Courier New', monospace; 
  font-size: 12px;
  padding: 2px 4px; 
  border-radius: 4px; 
}
.message-row.assistant .message-bubble :deep(code) { background: #E5E7EB; color: #DC2626; }
.message-row.user .message-bubble :deep(code) { background: rgba(255,255,255,0.2); color: white; }

.message-bubble :deep(pre) {
  background: #1E293B; /* Dark slate for code blocks */
  padding: 12px;
  border-radius: 8px;
  overflow-x: auto;
  margin: 10px 0;
}
.message-bubble :deep(pre code) {
  background: transparent !important;
  color: #E2E8F0 !important;
  padding: 0;
  border-radius: 0;
  display: block;
}

/* Links */
.message-bubble :deep(a) {
  color: #4F46E5;
  text-decoration: underline;
}
.message-row.user .message-bubble :deep(a) {
  color: white;
}
.message-bubble :deep(hr) {
  border: 0;
  border-top: 1px solid rgba(0,0,0,0.1);
  margin: 16px 0;
}

/* Empty State */
.empty-state {
  text-align: center;
  padding: 40px 20px;
  color: #9CA3AF;
}
.empty-icon { font-size: 48px; margin-bottom: 16px; opacity: 0.8; }
.empty-state h3 { color: #374151; font-weight: 600; margin-bottom: 8px; }
.empty-state p { font-size: 13px; line-height: 1.5; }

/* Action Card */
.action-card {
  margin-top: 8px;
  border: 1px solid #FECACA;
  background: #FEF2F2;
  border-radius: 12px;
  padding: 12px;
}
.action-header { display: flex; align-items: center; gap: 6px; font-size: 12px; font-weight: 600; color: #991B1B; margin-bottom: 8px; }
.action-btn { width: 100%; border: none; padding: 6px; border-radius: 6px; cursor: pointer; font-size: 12px; font-weight: 500; transition: all 0.2s; }
.action-btn.danger { background: #EF4444; color: white; }
.action-btn.danger:hover { background: #DC2626; }

/* Mobile */
@media (max-width: 640px) {
  .chat-wrapper { bottom: 0; right: 0; left: 0; width: 100%; height: 100%; pointer-events: none; }
  .chat-wrapper > .chat-toggle-fab { pointer-events: auto; position: fixed; bottom: 24px; right: 24px; }
  .chat-window { 
    pointer-events: auto; width: 100%; height: 100%; max-height: 100vh; border-radius: 0;
    position: fixed; top: 0; left: 0; 
  }
}
</style>
