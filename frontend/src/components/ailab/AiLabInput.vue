<script setup>
import { ref, computed, watch } from 'vue'
import AiLabTokenUsage from './AiLabTokenUsage.vue'

const props = defineProps({
  modelValue: { type: String, default: '' },
  isLoading: { type: Boolean, default: false },
  isRecording: { type: Boolean, default: false },
  isTranscribing: { type: Boolean, default: false },
  isOcrProcessing: { type: Boolean, default: false },
  recordingDuration: { type: Number, default: 0 },
  hasImage: { type: Boolean, default: false },
  fileAttachment: { type: Object, default: null },
  floating: { type: Boolean, default: true },
  sessionTokens: {
    type: Object,
    default: () => ({
      promptTokens: 0,
      completionTokens: 0,
      totalPromptTokens: 0,
      totalCompletionTokens: 0,
      turnCount: 0,
    }),
  },
  contextLimit: { type: Number, default: 1_000_000 },
})

const emit = defineEmits([
  'update:modelValue', 'send', 'stop', 'image-click', 'voice-click', 'paste', 'remove-file'
])

const localValue = ref(props.modelValue)

watch(() => props.modelValue, (val) => { localValue.value = val })
watch(localValue, (val) => { emit('update:modelValue', val) })

const composing = ref(false)
const onCompositionStart = () => { composing.value = true }
const onCompositionEnd = () => {
  requestAnimationFrame(() => { composing.value = false })
}

const handleKeydown = (e) => {
  if (composing.value || e.isComposing || e.keyCode === 229) return
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault()
    emit('send')
  }
}

const handlePaste = (e) => { emit('paste', e) }

const hasAttachment = computed(() => !!props.fileAttachment)

const fileSizeLabel = computed(() => {
  const size = props.fileAttachment?.size || 0
  if (!size) return ''
  if (size >= 1024 * 1024) return `${(size / 1024 / 1024).toFixed(1)} MB`
  return `${Math.max(1, Math.round(size / 1024))} KB`
})

const formatDuration = (seconds) => {
  const mins = Math.floor(seconds / 60)
  const secs = seconds % 60
  return `${mins}:${secs.toString().padStart(2, '0')}`
}
</script>

<template>
  <div
    :class="floating ? 'absolute bottom-0 left-0 right-0 pt-4 pb-3 px-4' : 'relative w-full'"
    :style="floating ? 'background: linear-gradient(to top, var(--theme-50) 70%, transparent); font-family: var(--ai-font-body);' : 'font-family: var(--ai-font-body);'"
  >
    <div class="max-w-4xl mx-auto relative">
      <div class="input-shell transition-all">
        <div v-if="hasAttachment" class="attachment-row">
          <img
            v-if="fileAttachment.type === 'image' && fileAttachment.preview"
            :src="fileAttachment.preview"
            class="attachment-thumb"
            alt=""
          />
          <div v-else class="attachment-icon">
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="1.5">
              <path stroke-linecap="round" stroke-linejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m2.25 0H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z"/>
            </svg>
          </div>
          <div class="min-w-0 flex-1">
            <div class="truncate text-[14px] leading-5" style="color: var(--theme-700);">{{ fileAttachment.name }}</div>
            <div class="text-[12px] leading-4" style="color: var(--theme-400);">{{ fileAttachment.type === 'image' ? '图片' : 'PDF' }}<span v-if="fileSizeLabel"> · {{ fileSizeLabel }}</span></div>
          </div>
          <button
            @click="emit('remove-file')"
            :disabled="isLoading || isOcrProcessing"
            class="shrink-0 p-1.5 rounded-md cursor-pointer disabled:opacity-40 disabled:cursor-not-allowed hover:bg-black/[0.04]"
            style="color: var(--theme-400);"
            title="移除文件"
          >
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="1.5">
              <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12"/>
            </svg>
          </button>
        </div>

        <div class="input-main-row">
          <!-- 左侧工具按钮 -->
          <div class="flex items-center gap-1 shrink-0">
            <button
              @click="emit('image-click')"
              :disabled="isLoading || isOcrProcessing || isRecording"
              class="input-icon-button input-add-button"
              :class="{ active: hasAttachment }"
              title="上传图片或 PDF"
            >
              <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="1.8">
                <path stroke-linecap="round" stroke-linejoin="round" d="M12 5v14M5 12h14"/>
              </svg>
            </button>
            <span v-if="hasAttachment" class="attachment-count">1</span>
          </div>

          <!-- 输入框 -->
          <textarea
            v-model="localValue"
            @keydown="handleKeydown"
            @compositionstart="onCompositionStart"
            @compositionend="onCompositionEnd"
            @paste="handlePaste"
            :disabled="isLoading || isRecording || isOcrProcessing"
            :placeholder="isOcrProcessing ? '正在处理文件…' : isRecording ? '录音中…' : '继续对话…'"
            class="input-textarea scrollbar-hide"
            rows="1"
          ></textarea>

          <!-- 右侧操作 -->
          <div class="input-actions">
            <button
              @click="emit('voice-click')"
              :disabled="isLoading || isOcrProcessing || isTranscribing"
              class="input-icon-button input-voice-button"
              :class="{ recording: isRecording }"
              :title="isRecording ? '停止录音' : '语音输入'"
            >
              <svg v-if="isTranscribing || isOcrProcessing" class="w-5 h-5 animate-spin" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="3"></circle>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"></path>
              </svg>
              <svg v-else-if="isRecording" class="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                <rect x="7" y="7" width="10" height="10" rx="1.5"/>
              </svg>
              <svg v-else class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="1.8">
                <path stroke-linecap="round" stroke-linejoin="round" d="M12 18.75a6 6 0 006-6v-1.5m-6 7.5a6 6 0 01-6-6v-1.5m6 7.5v3.75m-3.75 0h7.5M12 15.75a3 3 0 01-3-3V4.5a3 3 0 116 0v8.25a3 3 0 01-3 3z"/>
              </svg>
            </button>
            <span v-if="isRecording" class="recording-time">
              {{ formatDuration(recordingDuration) }}
            </span>

            <button v-if="isLoading" @click="emit('stop')"
              class="input-send-button input-stop-button"
              title="停止生成">
              <svg class="w-3.5 h-3.5 fill-current" viewBox="0 0 24 24">
                <rect x="6" y="6" width="12" height="12" rx="2"/>
              </svg>
            </button>
            <button v-else @click="emit('send')" :disabled="(!localValue.trim() && !hasAttachment) || isOcrProcessing"
               class="input-send-button"
               title="发送">
               <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2.2">
                 <path stroke-linecap="round" stroke-linejoin="round" d="M4.5 10.5L12 3m0 0l7.5 7.5M12 3v18"/>
               </svg>
            </button>
          </div>
        </div>
      </div>

      <!-- 底部状态栏：模型标识 + token 用量 -->
      <div v-if="floating" class="flex items-center justify-center gap-3 mt-1.5" style="font-size: 13px; color: var(--theme-400);">
        <span>Hermes Agent</span>
        <span style="color: var(--theme-300);">·</span>
        <AiLabTokenUsage
          :prompt-tokens="sessionTokens.promptTokens"
          :completion-tokens="sessionTokens.completionTokens"
          :total-prompt-tokens="sessionTokens.totalPromptTokens"
          :total-completion-tokens="sessionTokens.totalCompletionTokens"
          :turn-count="sessionTokens.turnCount"
          :context-limit="contextLimit"
          :breakdown="sessionTokens.breakdown"
        />
      </div>
    </div>
  </div>
</template>

<style scoped>
.scrollbar-hide {
  -ms-overflow-style: none;
  scrollbar-width: none;
}
.scrollbar-hide::-webkit-scrollbar {
  display: none;
}
.input-shell {
  background: rgba(255, 255, 255, 0.94);
  border: 1px solid rgba(15, 23, 42, 0.11);
  border-radius: 28px;
  padding: 6px;
  box-shadow:
    0 18px 42px rgba(15, 23, 42, 0.08),
    0 2px 7px rgba(15, 23, 42, 0.08),
    inset 0 1px 0 rgba(255, 255, 255, 0.96);
}
.input-shell:focus-within {
  border-color: rgba(45, 45, 40, 0.22);
  box-shadow:
    0 18px 42px rgba(15, 23, 42, 0.08),
    0 2px 7px rgba(15, 23, 42, 0.08),
    0 0 0 3px rgba(45, 45, 40, 0.06),
    inset 0 1px 0 rgba(255, 255, 255, 0.96);
}
.input-main-row {
  display: flex;
  align-items: center;
  gap: 8px;
  min-height: 44px;
  padding: 0 4px 0 8px;
}
.input-textarea {
  flex: 1;
  min-width: 0;
  align-self: center;
  resize: none;
  border: 0;
  outline: none;
  background: transparent;
  color: #111827;
  font-size: 16px;
  line-height: 24px;
  min-height: 26px;
  max-height: 8rem;
  padding: 1px 0;
}
.input-textarea::placeholder {
  color: #9ca3af;
}
.input-textarea:disabled {
  opacity: 0.62;
  cursor: not-allowed;
}
.input-actions {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
}
.input-icon-button {
  width: 32px;
  height: 32px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  border-radius: 999px;
  color: #111827;
  background: transparent;
  transition: background 0.16s ease, color 0.16s ease, transform 0.16s ease;
  cursor: pointer;
}
.input-icon-button:hover:not(:disabled) {
  background: rgba(15, 23, 42, 0.06);
}
.input-icon-button:active:not(:disabled) {
  transform: scale(0.94);
}
.input-icon-button:disabled {
  opacity: 0.38;
  cursor: not-allowed;
}
.input-add-button.active {
  color: var(--theme-700);
  background: var(--theme-100);
}
.input-voice-button.recording {
  color: #c53030;
  background: #fff5f5;
}
.attachment-count {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 16px;
  height: 16px;
  margin-left: -10px;
  margin-right: 2px;
  border-radius: 999px;
  background: var(--theme-700);
  color: white;
  font-size: 10px;
  font-weight: 700;
  line-height: 1;
}
.recording-time {
  min-width: 36px;
  color: #c53030;
  font-family: var(--ai-font-mono);
  font-size: 12px;
  font-variant-numeric: tabular-nums;
}
.input-send-button {
  width: 36px;
  height: 36px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  border-radius: 999px;
  background: var(--theme-700);
  color: white;
  box-shadow: 0 6px 14px rgba(45, 45, 40, 0.18);
  transition: transform 0.16s ease, background 0.16s ease, opacity 0.16s ease;
  cursor: pointer;
}
.input-send-button:hover:not(:disabled) {
  background: var(--theme-600);
  transform: translateY(-1px);
}
.input-send-button:active:not(:disabled) {
  transform: scale(0.94);
}
.input-send-button:disabled {
  opacity: 0.42;
  cursor: not-allowed;
  box-shadow: none;
}
.input-stop-button {
  background: #e5e7eb;
  color: #374151;
  box-shadow: none;
}
.attachment-row {
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 0;
  margin: 2px 2px 6px;
  padding: 7px 9px;
  border-radius: 18px;
  background: #f8fafc;
  border: 1px solid #e5e7eb;
}
.attachment-thumb,
.attachment-icon {
  width: 36px;
  height: 36px;
  flex: 0 0 36px;
  border-radius: 7px;
}
.attachment-thumb {
  object-fit: cover;
}
.attachment-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--theme-400);
  background: var(--theme-50);
}
</style>
