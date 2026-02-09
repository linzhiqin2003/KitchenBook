<script setup>
import { ref, watch } from 'vue'

const props = defineProps({
  modelValue: {
    type: String,
    default: ''
  },
  isLoading: {
    type: Boolean,
    default: false
  },
  isRecording: {
    type: Boolean,
    default: false
  },
  isTranscribing: {
    type: Boolean,
    default: false
  },
  isOcrProcessing: {
    type: Boolean,
    default: false
  },
  recordingDuration: {
    type: Number,
    default: 0
  },
  hasImage: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits([
  'update:modelValue',
  'send',
  'stop',
  'image-click',
  'voice-click',
  'paste'
])

const localValue = ref(props.modelValue)

watch(() => props.modelValue, (val) => {
  localValue.value = val
})

watch(localValue, (val) => {
  emit('update:modelValue', val)
})

// IME 组合状态跟踪（解决 Chrome 在 compositionend 后 isComposing 已为 false 的问题）
const composing = ref(false)
const onCompositionStart = () => { composing.value = true }
const onCompositionEnd = () => {
  // 延迟一帧清除，确保紧随其后的 keydown Enter 仍被拦截
  requestAnimationFrame(() => { composing.value = false })
}

const handleKeydown = (e) => {
  if (composing.value || e.isComposing || e.keyCode === 229) return
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault()
    emit('send')
  }
}

const handlePaste = (e) => {
  emit('paste', e)
}

const formatDuration = (seconds) => {
  const mins = Math.floor(seconds / 60)
  const secs = seconds % 60
  return `${mins}:${secs.toString().padStart(2, '0')}`
}
</script>

<template>
  <div class="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-white via-white to-transparent pt-10 pb-6 px-4">
    <div class="max-w-3xl mx-auto relative">
      <div class="relative bg-gray-50 border border-gray-200 rounded-full shadow-sm transition-all hover:border-gray-300 hover:shadow-md">
        <!-- 左侧按钮组 -->
        <div class="absolute bottom-2.5 left-3 flex items-center gap-1">
          <!-- 图片按钮 -->
          <button
            @click="emit('image-click')"
            :disabled="isLoading || isOcrProcessing || isRecording"
            :class="[
              'p-2 rounded-full transition-all cursor-pointer',
              hasImage
                ? 'bg-purple-100 text-purple-600'
                : 'hover:bg-gray-200 text-gray-400 hover:text-gray-600',
              (isLoading || isOcrProcessing || isRecording) && 'opacity-50 cursor-not-allowed'
            ]"
            title="上传图片 (支持粘贴)"
          >
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"/>
            </svg>
          </button>

          <!-- 语音按钮 -->
          <button
            @click="emit('voice-click')"
            :disabled="isLoading || isOcrProcessing || isTranscribing"
            :class="[
              'p-2 rounded-full transition-all cursor-pointer',
              isRecording
                ? 'bg-red-500 text-white animate-pulse'
                : 'hover:bg-gray-200 text-gray-400 hover:text-gray-600',
              (isLoading || isOcrProcessing || isTranscribing) && 'opacity-50 cursor-not-allowed'
            ]"
            :title="isRecording ? '停止录音' : '语音输入'"
          >
            <svg v-if="isTranscribing" class="w-5 h-5 animate-spin" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"></path>
            </svg>
            <svg v-else-if="isRecording" class="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
              <rect x="6" y="6" width="12" height="12" rx="1"/>
            </svg>
            <svg v-else class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z"/>
            </svg>
          </button>

          <!-- 录音时长 -->
          <span v-if="isRecording" class="text-xs text-red-500 font-mono min-w-[40px]">
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
          :disabled="isLoading || isRecording"
          :placeholder="isRecording ? '录音中...' : '继续对话...'"
          class="w-full bg-transparent text-gray-800 placeholder-gray-400 py-3 pl-24 pr-14 min-h-[48px] max-h-32 resize-none scrollbar-hide outline-none border-none focus:ring-0 focus:outline-none"
          rows="1"
        ></textarea>

        <!-- 发送/停止按钮 -->
        <div class="absolute bottom-2.5 right-2.5 flex items-center gap-2">
          <button v-if="isLoading" @click="emit('stop')" class="p-2 bg-gray-200 hover:bg-gray-300 rounded-full text-gray-600 transition-colors cursor-pointer">
            <svg class="w-4 h-4 fill-current" viewBox="0 0 24 24">
              <rect x="6" y="6" width="12" height="12" rx="1"/>
            </svg>
          </button>
          <button v-else @click="emit('send')" :disabled="!localValue.trim() && !hasImage"
             class="p-2 disabled:opacity-40 disabled:cursor-not-allowed rounded-full text-white transition-all shadow-lg cursor-pointer"
             style="background: var(--theme-gradient-btn); box-shadow: 0 4px 14px var(--theme-shadow);">
             <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
               <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 10l7-7m0 0l7 7m-7-7v18"/>
             </svg>
          </button>
        </div>
      </div>
      <div class="text-center mt-2 text-xs text-gray-400">
        DeepSeek Reasoner + Tool Calling · Enter 发送，Shift+Enter 换行
      </div>
    </div>
  </div>
</template>

<style scoped>
/* 隐藏滚动条但保持功能 */
.scrollbar-hide {
  -ms-overflow-style: none;
  scrollbar-width: none;
}

.scrollbar-hide::-webkit-scrollbar {
  display: none;
}
</style>
