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
  { title: '数学推理', prompt: '证明根号2是无理数' },
  { title: '代码分析', prompt: '解释快速排序算法的时间复杂度' },
  { title: '深度思考', prompt: '从哲学角度分析人工智能的本质' },
  { title: '写作助手', prompt: '帮我写一段关于科技发展的议论文' }
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

      <div class="mt-4 flex flex-wrap justify-center gap-2">
        <button v-for="example in examplePrompts" :key="example.title"
             @click="!isLoading && emit('ask', example.prompt)"
             :disabled="isLoading"
             class="px-3 py-1 transition-all cursor-pointer rounded-md"
             style="font-size: 13px; color: var(--theme-500); border: 1px solid var(--theme-200); background: transparent;">
          {{ example.title }}
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
</style>
