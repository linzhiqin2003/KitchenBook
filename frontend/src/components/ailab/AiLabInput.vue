<script setup>
import { ref, watch, computed } from 'vue'

const props = defineProps({
  modelValue: { type: String, default: '' },
  isLoading: { type: Boolean, default: false },
  isRecording: { type: Boolean, default: false },
  isTranscribing: { type: Boolean, default: false },
  isOcrProcessing: { type: Boolean, default: false },
  recordingDuration: { type: Number, default: 0 },
  hasImage: { type: Boolean, default: false },
  selectedModel: { type: String, default: 'deepseek-v4-flash' },
  modelOptions: { type: Array, default: () => [] },
  thinkingLevel: { type: String, default: 'low' },
  thinkingLevels: { type: Array, default: () => ['none', 'low', 'medium', 'high', 'max'] }
})

const emit = defineEmits([
  'update:modelValue', 'send', 'stop', 'image-click', 'voice-click', 'paste',
  'update:selectedModel', 'update:thinkingLevel'
])

const localValue = ref(props.modelValue)
const showMenu = ref(false)

watch(() => props.modelValue, (val) => { localValue.value = val })
watch(localValue, (val) => { emit('update:modelValue', val) })

const currentModel = computed(() =>
  props.modelOptions.find(m => m.id === props.selectedModel) || props.modelOptions[0]
)

const selectModel = (id) => { emit('update:selectedModel', id) }
const selectThinking = (level) => { emit('update:thinkingLevel', level) }

const thinkingLabel = computed(() => {
  const l = props.thinkingLevel
  return l.charAt(0).toUpperCase() + l.slice(1)
})

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

const formatDuration = (seconds) => {
  const mins = Math.floor(seconds / 60)
  const secs = seconds % 60
  return `${mins}:${secs.toString().padStart(2, '0')}`
}
</script>

<template>
  <div class="absolute bottom-0 left-0 right-0 pt-4 pb-3 px-4" style="background: linear-gradient(to top, var(--theme-50) 70%, transparent); font-family: var(--ai-font-body);">
    <div class="max-w-3xl mx-auto relative">
      <!-- 输入框容器 -->
      <div class="flex items-end gap-2 transition-all" style="background: var(--theme-50); border: 1px solid var(--theme-200); border-radius: 10px; padding: 6px;">
        <!-- 左侧工具按钮 -->
        <div class="flex items-center gap-0.5 shrink-0 pb-px">
          <button
            @click="emit('image-click')"
            :disabled="isLoading || isOcrProcessing || isRecording"
            class="p-1.5 rounded-md transition-all cursor-pointer disabled:opacity-40 disabled:cursor-not-allowed"
            :style="hasImage ? 'color: var(--ai-accent); background: var(--ai-accent-soft);' : 'color: var(--theme-400);'"
            title="上传图片"
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
            <svg v-if="isTranscribing" class="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
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
          :disabled="isLoading || isRecording"
          :placeholder="isRecording ? '录音中…' : '继续对话…'"
          class="flex-1 bg-transparent resize-none scrollbar-hide outline-none border-none focus:ring-0 focus:outline-none self-center"
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
          <button v-else @click="emit('send')" :disabled="!localValue.trim() && !hasImage"
             class="w-7 h-7 rounded-lg flex items-center justify-center disabled:opacity-30 disabled:cursor-not-allowed transition-all cursor-pointer"
             style="background: var(--theme-700); color: var(--theme-50);">
             <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
               <path stroke-linecap="round" stroke-linejoin="round" d="M4.5 10.5L12 3m0 0l7.5 7.5M12 3v18"/>
             </svg>
          </button>
        </div>
      </div>

      <!-- 底部状态栏 -->
      <div class="flex items-center justify-center mt-1.5 relative" style="font-size: 12px; color: var(--theme-400);">
        <div class="relative">
          <button @click="showMenu = !showMenu"
            class="inline-flex items-center gap-1 px-1.5 py-0.5 rounded-md transition-colors cursor-pointer">
            <span>{{ currentModel?.name || 'Flash' }} · {{ thinkingLabel }}</span>
            <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M19.5 8.25l-7.5 7.5-7.5-7.5"/>
            </svg>
          </button>

          <!-- 合并菜单 -->
          <Transition name="popup">
            <div v-if="showMenu"
              class="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 w-52 z-50"
              style="background: var(--theme-50); border: 1px solid var(--theme-200); border-radius: 10px; box-shadow: 0 4px 16px rgba(0,0,0,0.06);">

              <!-- Models -->
              <div class="px-3 pt-2 pb-1" style="font-size: 11px; font-weight: 600; color: var(--theme-400); letter-spacing: 0.03em;">Models</div>
              <button
                v-for="model in modelOptions"
                :key="model.id"
                @click="selectModel(model.id)"
                class="w-full text-left px-3 py-1.5 transition-colors cursor-pointer flex items-center gap-2"
                :style="'color: var(--theme-600); font-size: 13px;'">
                <svg v-if="model.icon === 'bolt'" class="w-3.5 h-3.5 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="1.5">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M3.75 13.5l10.5-11.25L12 10.5h8.25L9.75 21.75 12 13.5H3.75z"/>
                </svg>
                <svg v-else-if="model.icon === 'sparkle'" class="w-3.5 h-3.5 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="1.5">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09z"/>
                </svg>
                <span class="flex-1 font-medium">{{ model.name }}</span>
                <svg v-if="model.id === selectedModel" class="w-3.5 h-3.5 shrink-0" style="color: var(--theme-500);" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M4.5 12.75l6 6 9-13.5"/>
                </svg>
              </button>

              <!-- Divider -->
              <div class="mx-3 my-1" style="border-top: 1px solid var(--theme-200);"></div>

              <!-- Effort -->
              <div class="px-3 pt-1 pb-1" style="font-size: 11px; font-weight: 600; color: var(--theme-400); letter-spacing: 0.03em;">Effort</div>
              <button
                v-for="level in thinkingLevels"
                :key="level"
                @click="selectThinking(level)"
                class="w-full text-left px-3 py-1.5 transition-colors cursor-pointer flex items-center"
                :style="'color: var(--theme-600); font-size: 13px;'">
                <span class="flex-1" style="text-transform: capitalize;">{{ level }}</span>
                <svg v-if="level === thinkingLevel" class="w-3.5 h-3.5 shrink-0" style="color: var(--theme-500);" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M4.5 12.75l6 6 9-13.5"/>
                </svg>
              </button>

              <div class="h-1"></div>
            </div>
          </Transition>
        </div>
      </div>

      <div v-if="showMenu" class="fixed inset-0 z-40" @click="showMenu = false"></div>
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
