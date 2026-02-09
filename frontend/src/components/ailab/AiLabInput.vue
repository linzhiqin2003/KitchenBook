<script setup>
import { ref, watch, computed } from 'vue'

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
  },
  selectedModel: {
    type: String,
    default: 'deepseek-reasoner'
  },
  modelOptions: {
    type: Array,
    default: () => []
  }
})

const emit = defineEmits([
  'update:modelValue',
  'send',
  'stop',
  'image-click',
  'voice-click',
  'paste',
  'update:selectedModel'
])

const localValue = ref(props.modelValue)
const showModelMenu = ref(false)

watch(() => props.modelValue, (val) => {
  localValue.value = val
})

watch(localValue, (val) => {
  emit('update:modelValue', val)
})

const currentModel = computed(() =>
  props.modelOptions.find(m => m.id === props.selectedModel) || props.modelOptions[0]
)

const selectModel = (id) => {
  emit('update:selectedModel', id)
  showModelMenu.value = false
}

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

const closeModelMenu = () => {
  showModelMenu.value = false
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

      <!-- 模型选择器 + 提示文字 -->
      <div class="flex items-center justify-center mt-2 gap-1.5 text-xs text-gray-400 relative">
        <div class="relative">
          <button
            @click="showModelMenu = !showModelMenu"
            class="inline-flex items-center gap-1 px-2 py-0.5 rounded-md hover:bg-gray-100 hover:text-gray-600 transition-colors cursor-pointer"
          >
            <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"/>
            </svg>
            <span>{{ currentModel?.name || 'Select Model' }}</span>
            <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"/>
            </svg>
          </button>

          <!-- 模型下拉菜单 -->
          <Transition name="popup">
            <div
              v-if="showModelMenu"
              class="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 w-56 bg-white rounded-xl shadow-xl border border-gray-200 py-1.5 z-50"
            >
              <button
                v-for="model in modelOptions"
                :key="model.id"
                @click="selectModel(model.id)"
                :class="[
                  'w-full text-left px-3 py-2 text-sm transition-colors cursor-pointer flex items-center gap-2',
                  model.id === selectedModel
                    ? 'bg-violet-50 text-violet-700'
                    : 'text-gray-600 hover:bg-gray-50'
                ]"
              >
                <span class="w-1.5 h-1.5 rounded-full shrink-0" :class="model.id === selectedModel ? 'bg-violet-500' : 'bg-gray-300'"></span>
                <span class="flex-1">
                  <span class="font-medium">{{ model.name }}</span>
                  <span v-if="model.desc" class="text-gray-400 ml-1">{{ model.desc }}</span>
                </span>
              </button>
            </div>
          </Transition>
        </div>
        <span class="text-gray-300">·</span>
        <span>Enter 发送，Shift+Enter 换行</span>
      </div>

      <!-- 点击外部关闭菜单 -->
      <div v-if="showModelMenu" class="fixed inset-0 z-40" @click="closeModelMenu"></div>
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

.popup-enter-active,
.popup-leave-active {
  transition: all 0.15s ease;
}
.popup-enter-from,
.popup-leave-to {
  opacity: 0;
  transform: translate(-50%, 4px);
}
</style>
