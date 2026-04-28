<script setup>
import AiLabInput from './AiLabInput.vue'

const props = defineProps({
  modelValue: { type: String, default: '' },
  isLoading: { type: Boolean, default: false },
  isRecording: { type: Boolean, default: false },
  isTranscribing: { type: Boolean, default: false },
  isOcrProcessing: { type: Boolean, default: false },
  recordingDuration: { type: Number, default: 0 },
  hasImage: { type: Boolean, default: false },
  fileAttachment: { type: Object, default: null },
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
  'update:modelValue', 'ask', 'send', 'stop', 'image-click', 'voice-click', 'paste', 'remove-file', 'toggle-sidebar'
])

const examplePrompts = [
  { title: '数学推理', subtitle: '证明、推导、计算', icon: 'math', prompt: '证明根号2是无理数' },
  { title: '代码分析', subtitle: '算法、复杂度、调试', icon: 'code', prompt: '解释快速排序算法的时间复杂度' },
  { title: '深度思考', subtitle: '哲学、辩证、本质', icon: 'spark', prompt: '从哲学角度分析人工智能的本质' },
  { title: '写作助手', subtitle: '议论、记叙、润色', icon: 'pen',   prompt: '帮我写一段关于科技发展的议论文' }
]
</script>

<template>
  <div class="flex-1 flex flex-col items-center justify-center px-4" style="font-family: var(--ai-font-body);">
    <button @click="emit('toggle-sidebar')" class="lg:hidden absolute top-4 left-4 transition-colors cursor-pointer" style="color: var(--theme-400);">
      <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="1.5">
        <path stroke-linecap="round" stroke-linejoin="round" d="M3.75 6.75h16.5M3.75 12h16.5M3.75 17.25h16.5"/>
      </svg>
    </button>

    <h1 class="mb-8" style="font-family: var(--ai-font-display); font-size: clamp(1.5rem, 3vw, 2rem); font-weight: 600; letter-spacing: -0.02em; color: var(--theme-700);">
      有什么想法，说来听听？
    </h1>

    <div class="w-full" style="max-width: 38rem;">
      <AiLabInput
        :model-value="modelValue"
        :floating="false"
        :is-loading="isLoading"
        :is-recording="isRecording"
        :is-transcribing="isTranscribing"
        :is-ocr-processing="isOcrProcessing"
        :recording-duration="recordingDuration"
        :has-image="hasImage"
        :file-attachment="fileAttachment"
        :session-tokens="sessionTokens"
        :context-limit="contextLimit"
        @update:model-value="emit('update:modelValue', $event)"
        @send="emit('send')"
        @stop="emit('stop')"
        @image-click="emit('image-click')"
        @voice-click="emit('voice-click')"
        @paste="emit('paste', $event)"
        @remove-file="emit('remove-file')"
      />

      <div class="mt-5 grid grid-cols-2 sm:grid-cols-4 gap-2.5">
        <button v-for="example in examplePrompts" :key="example.title"
             @click="!isLoading && emit('ask', example.prompt)"
             :disabled="isLoading"
             class="example-card">
          <span class="example-icon">
            <svg v-if="example.icon === 'math'" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">
              <path d="M5 5h11l-7 14h9"/>
              <path d="M14 11h6"/>
            </svg>
            <svg v-else-if="example.icon === 'code'" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">
              <path d="M8 7l-5 5 5 5"/>
              <path d="M16 7l5 5-5 5"/>
              <path d="M14 4l-4 16"/>
            </svg>
            <svg v-else-if="example.icon === 'spark'" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">
              <path d="M12 3v4M12 17v4M3 12h4M17 12h4M5.6 5.6l2.8 2.8M15.6 15.6l2.8 2.8M5.6 18.4l2.8-2.8M15.6 8.4l2.8-2.8"/>
            </svg>
            <svg v-else-if="example.icon === 'pen'" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">
              <path d="M4 20l3.5-1 11-11-2.5-2.5-11 11L4 20z"/>
              <path d="M14.5 6.5l3 3"/>
            </svg>
          </span>
          <span class="example-text">
            <span class="example-title">{{ example.title }}</span>
            <span class="example-subtitle">{{ example.subtitle }}</span>
          </span>
        </button>
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

.example-card {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  padding: 0.65rem 0.8rem;
  border-radius: 12px;
  border: 1px solid var(--theme-200);
  background: rgba(255, 255, 255, 0.55);
  text-align: left;
  cursor: pointer;
  transition: border-color 0.18s ease, background 0.18s ease,
              transform 0.18s ease, box-shadow 0.18s ease;
}
.example-card:hover:not(:disabled) {
  border-color: var(--theme-300);
  background: #ffffff;
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(45, 45, 40, 0.05);
}
.example-card:active:not(:disabled) {
  transform: translateY(0);
}
.example-card:disabled {
  opacity: 0.55;
  cursor: not-allowed;
}

.example-icon {
  flex-shrink: 0;
  width: 28px;
  height: 28px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 8px;
  background: var(--theme-100);
  color: var(--theme-500);
  transition: background 0.18s ease, color 0.18s ease;
}
.example-icon svg {
  width: 16px;
  height: 16px;
}
.example-card:hover:not(:disabled) .example-icon {
  background: var(--ai-accent-soft);
  color: var(--ai-accent);
}

.example-text {
  display: flex;
  flex-direction: column;
  gap: 1px;
  min-width: 0;
  flex: 1;
}
.example-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--theme-700);
  line-height: 1.3;
  letter-spacing: -0.005em;
}
.example-subtitle {
  font-size: 12px;
  color: var(--theme-400);
  line-height: 1.3;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
</style>
