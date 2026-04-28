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
    <div class="max-w-3xl mx-auto relative">
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
            <div class="truncate text-[13px] leading-4" style="color: var(--theme-700);">{{ fileAttachment.name }}</div>
            <div class="text-[11px] leading-4" style="color: var(--theme-400);">{{ fileAttachment.type === 'image' ? '图片' : 'PDF' }}<span v-if="fileSizeLabel"> · {{ fileSizeLabel }}</span></div>
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

        <div class="flex items-end gap-2">
          <!-- 左侧工具按钮 -->
          <div class="flex items-center gap-0.5 shrink-0 pb-px">
            <button
              @click="emit('image-click')"
              :disabled="isLoading || isOcrProcessing || isRecording"
              class="p-1.5 rounded-md transition-all cursor-pointer disabled:opacity-40 disabled:cursor-not-allowed"
              :style="hasAttachment ? 'color: var(--ai-accent); background: var(--ai-accent-soft);' : 'color: var(--theme-400);'"
              title="上传图片或 PDF"
            >
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="1.5">
                <path stroke-linecap="round" stroke-linejoin="round" d="M2.25 15.75l5.159-5.159a2.25 2.25 0 013.182 0l5.159 5.159m-1.5-1.5l1.409-1.409a2.25 2.25 0 013.182 0l2.909 2.909M18 3.75H6A2.25 2.25 0 003.75 6v12A2.25 2.25 0 006 20.25h12A2.25 2.25 0 0020.25 18V6A2.25 2.25 0 0018 3.75zM15.75 9a.75.75 0 11-1.5 0 .75.75 0 011.5 0z"/>
              </svg>
            </button>
            <button
              @click="emit('voice-click')"
              :disabled="isLoading || isOcrProcessing || isTranscribing"
              class="p-1.5 rounded-md transition-all cursor-pointer disabled:opacity-40 disabled:cursor-not-allowed"
              :style="isRecording ? 'color: #c53030; background: #fff5f5;' : 'color: var(--theme-400);'"
              :title="isRecording ? '停止录音' : '语音输入'"
            >
              <svg v-if="isTranscribing || isOcrProcessing" class="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="3"></circle>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"></path>
              </svg>
              <svg v-else-if="isRecording" class="w-4 h-4" fill="currentColor" viewBox="0 0 24 24">
                <rect x="7" y="7" width="10" height="10" rx="1.5"/>
              </svg>
              <svg v-else class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="1.5">
                <path stroke-linecap="round" stroke-linejoin="round" d="M12 18.75a6 6 0 006-6v-1.5m-6 7.5a6 6 0 01-6-6v-1.5m6 7.5v3.75m-3.75 0h7.5M12 15.75a3 3 0 01-3-3V4.5a3 3 0 116 0v8.25a3 3 0 01-3 3z"/>
              </svg>
            </button>
            <span v-if="isRecording" class="text-xs font-mono min-w-[36px]" style="color: #c53030;">
              {{ formatDuration(recordingDuration) }}
            </span>
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
            class="flex-1 min-w-0 bg-transparent resize-none scrollbar-hide outline-none border-none focus:ring-0 focus:outline-none self-center"
            style="color: var(--theme-700); font-size: 14px; line-height: 20px; padding: 4px 0; min-height: 28px; max-height: 8rem;"
            rows="1"
          ></textarea>

          <!-- 发送/停止按钮 -->
          <div class="shrink-0 pb-px">
            <button v-if="isLoading" @click="emit('stop')"
              class="w-7 h-7 rounded-lg flex items-center justify-center transition-colors cursor-pointer"
              style="background: var(--theme-200); color: var(--theme-600);">
              <svg class="w-3 h-3 fill-current" viewBox="0 0 24 24">
                <rect x="6" y="6" width="12" height="12" rx="2"/>
              </svg>
            </button>
            <button v-else @click="emit('send')" :disabled="(!localValue.trim() && !hasAttachment) || isOcrProcessing"
               class="w-7 h-7 rounded-lg flex items-center justify-center disabled:opacity-30 disabled:cursor-not-allowed transition-all cursor-pointer"
               style="background: var(--theme-700); color: var(--theme-50);">
               <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
                 <path stroke-linecap="round" stroke-linejoin="round" d="M4.5 10.5L12 3m0 0l7.5 7.5M12 3v18"/>
               </svg>
            </button>
          </div>
        </div>
      </div>

      <!-- 底部状态栏：模型标识 + token 用量 -->
      <div v-if="floating" class="flex items-center justify-center gap-3 mt-1.5" style="font-size: 12px; color: var(--theme-400);">
        <span>Hermes Agent</span>
        <span style="color: var(--theme-300);">·</span>
        <AiLabTokenUsage
          :prompt-tokens="sessionTokens.promptTokens"
          :completion-tokens="sessionTokens.completionTokens"
          :total-prompt-tokens="sessionTokens.totalPromptTokens"
          :total-completion-tokens="sessionTokens.totalCompletionTokens"
          :turn-count="sessionTokens.turnCount"
          :context-limit="contextLimit"
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
  background: var(--theme-50);
  border: 1px solid var(--theme-200);
  border-radius: 10px;
  padding: 6px;
}
.attachment-row {
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 0;
  margin-bottom: 6px;
  padding: 6px 8px;
  border-radius: 8px;
  background: var(--theme-100);
  border: 1px solid var(--theme-200);
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
