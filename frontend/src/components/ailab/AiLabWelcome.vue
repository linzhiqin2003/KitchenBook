<script setup>
import { ref, computed } from 'vue'

const props = defineProps({
  isLoading: {
    type: Boolean,
    default: false
  },
  selectedModel: {
    type: String,
    default: 'deepseek-v4-flash'
  },
  modelOptions: {
    type: Array,
    default: () => []
  }
})

const emit = defineEmits(['ask', 'toggle-sidebar', 'update:selectedModel'])

const showModelMenu = ref(false)
const currentModel = computed(() =>
  props.modelOptions.find(m => m.id === props.selectedModel) || props.modelOptions[0]
)
const selectModel = (id) => {
  emit('update:selectedModel', id)
  showModelMenu.value = false
}

const inputValue = ref('')

const examplePrompts = [
  { title: '数学推理', prompt: '证明根号2是无理数' },
  { title: '代码分析', prompt: '解释快速排序算法的时间复杂度' },
  { title: '深度思考', prompt: '从哲学角度分析人工智能的本质' },
  { title: '写作助手', prompt: '帮我写一段关于科技发展的议论文' }
]

function handleEnter(e) {
  if (e.isComposing || e.keyCode === 229) return
  if (e.shiftKey) return
  e.preventDefault()
  submit()
}

function submit() {
  if (!inputValue.value.trim() || props.isLoading) return
  emit('ask', inputValue.value)
  inputValue.value = ''
}

function setPrompt(prompt) {
  inputValue.value = prompt
}
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
      <div class="relative transition-all" style="background: var(--theme-50); border: 1px solid var(--theme-200); border-radius: 12px;">
        <textarea
          v-model="inputValue"
          @keydown.enter="handleEnter"
          placeholder="开始对话…"
          class="w-full bg-transparent resize-none scrollbar-hide outline-none border-none focus:ring-0 focus:outline-none"
          style="color: var(--theme-700); padding: 14px 52px 14px 16px; min-height: 48px; max-height: 8rem; font-size: 14px; line-height: 1.5;"
          rows="1"
        ></textarea>

        <div class="absolute bottom-2.5 right-2.5">
          <button @click="submit" :disabled="!inputValue.trim() || isLoading"
             class="w-8 h-8 rounded-lg flex items-center justify-center disabled:opacity-30 disabled:cursor-not-allowed transition-all cursor-pointer"
             style="background: var(--theme-700); color: var(--theme-50);">
             <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
               <path stroke-linecap="round" stroke-linejoin="round" d="M4.5 10.5L12 3m0 0l7.5 7.5M12 3v18"/>
             </svg>
          </button>
        </div>
      </div>

      <div class="mt-4 flex flex-wrap justify-center gap-2">
        <button v-for="example in examplePrompts" :key="example.title"
             @click="setPrompt(example.prompt)"
             class="px-3 py-1 transition-all cursor-pointer rounded-md"
             style="font-size: 13px; color: var(--theme-500); border: 1px solid var(--theme-200); background: transparent;">
          {{ example.title }}
        </button>
      </div>
    </div>

    <div class="absolute bottom-5 text-center" style="font-size: 12px; color: var(--theme-400);">
      <div class="relative inline-flex items-center gap-1.5">
        <div class="relative">
          <button
            @click="showModelMenu = !showModelMenu"
            class="inline-flex items-center gap-1 px-1.5 py-0.5 rounded-md transition-colors cursor-pointer"
          >
            <span>{{ currentModel?.name || 'Model' }}</span>
            <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M19.5 8.25l-7.5 7.5-7.5-7.5"/>
            </svg>
          </button>
          <Transition name="popup">
            <div
              v-if="showModelMenu"
              class="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 w-48 py-1 z-50"
              style="background: var(--theme-50); border: 1px solid var(--theme-200); border-radius: 10px; box-shadow: 0 4px 16px rgba(0,0,0,0.06);"
            >
              <button
                v-for="model in modelOptions"
                :key="model.id"
                @click="selectModel(model.id)"
                class="w-full text-left px-3 py-1.5 transition-colors cursor-pointer flex items-center gap-2"
                :style="model.id === selectedModel
                  ? 'background: var(--ai-accent-soft); color: var(--ai-accent); font-size: 13px;'
                  : 'color: var(--theme-600); font-size: 13px;'"
              >
                <svg v-if="model.icon === 'bolt'" class="w-3.5 h-3.5 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="1.5">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M3.75 13.5l10.5-11.25L12 10.5h8.25L9.75 21.75 12 13.5H3.75z"/>
                </svg>
                <svg v-else-if="model.icon === 'sparkle'" class="w-3.5 h-3.5 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="1.5">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09z"/>
                </svg>
                <span class="flex-1">
                  <span class="font-medium">{{ model.name }}</span>
                  <span v-if="model.desc" style="color: var(--theme-400); margin-left: 4px;">{{ model.desc }}</span>
                </span>
              </button>
            </div>
          </Transition>
        </div>
        <span style="color: var(--theme-300);">·</span>
        <span>AI 可能产生不准确信息，请核实重要内容</span>
      </div>
      <div v-if="showModelMenu" class="fixed inset-0 z-40" @click="showModelMenu = false"></div>
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
