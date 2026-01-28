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

const handleKeydown = (e) => {
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
  <div class="bg-white border-t border-gray-200 px-4 py-3 safe-area-bottom">
    <div class="max-w-4xl mx-auto">
      <div class="flex items-end gap-2 p-2 bg-gray-50 rounded-2xl border border-gray-200 focus-within:border-violet-400 focus-within:ring-2 focus-within:ring-violet-100 transition-all">
        <!-- 左侧按钮组 -->
        <div class="flex items-center gap-1 pb-1">
          <!-- 图片按钮 -->
          <button
            @click="emit('image-click')"
            :disabled="isLoading || isOcrProcessing || isRecording"
            :class="[
              'w-9 h-9 rounded-xl flex items-center justify-center transition-all cursor-pointer',
              hasImage
                ? 'bg-violet-100 text-violet-600'
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
              'w-9 h-9 rounded-xl flex items-center justify-center transition-all cursor-pointer',
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
          <span v-if="isRecording" class="text-xs text-red-500 font-mono min-w-[40px] pb-0.5">
            {{ formatDuration(recordingDuration) }}
          </span>
        </div>

        <!-- 输入框 -->
        <textarea
          v-model="localValue"
          @keydown="handleKeydown"
          @paste="handlePaste"
          :disabled="isLoading || isRecording"
          :placeholder="isRecording ? '录音中...' : '输入消息...'"
          rows="1"
          class="flex-1 resize-none bg-transparent border-0 text-gray-800 placeholder-gray-400 focus:outline-none focus:ring-0 max-h-32 min-h-[36px] py-2 text-sm leading-relaxed"
          style="field-sizing: content;"
        ></textarea>

        <!-- 发送/停止按钮 -->
        <div class="pb-1">
          <button
            v-if="!isLoading"
            @click="emit('send')"
            :disabled="!localValue.trim() && !hasImage"
            :class="[
              'w-9 h-9 rounded-xl flex items-center justify-center transition-all cursor-pointer',
              localValue.trim() || hasImage
                ? 'bg-gradient-to-r from-violet-500 to-purple-600 text-white shadow-md shadow-violet-500/20 hover:shadow-lg hover:shadow-violet-500/30'
                : 'bg-gray-200 text-gray-400 cursor-not-allowed'
            ]"
          >
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8"/>
            </svg>
          </button>

          <button
            v-else
            @click="emit('stop')"
            class="w-9 h-9 rounded-xl bg-red-500 hover:bg-red-600 text-white flex items-center justify-center transition-colors cursor-pointer"
            title="停止生成"
          >
            <svg class="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
              <rect x="6" y="6" width="12" height="12" rx="1"/>
            </svg>
          </button>
        </div>
      </div>

      <!-- 底部提示 -->
      <div class="text-center mt-2 text-xs text-gray-400">
        DeepSeek Reasoner · 按 Enter 发送，Shift+Enter 换行
      </div>
    </div>
  </div>
</template>

<style scoped>
.safe-area-bottom {
  padding-bottom: max(12px, env(safe-area-inset-bottom));
}
</style>
