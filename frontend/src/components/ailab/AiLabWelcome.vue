<script setup>
import { ref, computed } from 'vue'

const props = defineProps({
  isLoading: {
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

// 示例提示词
const examplePrompts = [
  { icon: '🧮', title: '数学推理', prompt: '证明根号2是无理数' },
  { icon: '💻', title: '代码分析', prompt: '解释快速排序算法的时间复杂度' },
  { icon: '🧠', title: '深度思考', prompt: '从哲学角度分析人工智能的本质' },
  { icon: '📝', title: '写作助手', prompt: '帮我写一段关于科技发展的议论文' }
]

function handleEnter(e) {
  // 如果是 IME 输入法正在组合，不发送
  if (e.isComposing || e.keyCode === 229) return
  // Shift+Enter 换行
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
  <div class="flex-1 flex flex-col items-center justify-center px-4">
    <!-- 移动端菜单按钮 -->
    <button @click="emit('toggle-sidebar')" class="lg:hidden absolute top-4 left-4 text-gray-500 hover:text-gray-700 transition-colors cursor-pointer">
      <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16"/>
      </svg>
    </button>

    <!-- 居中标题 -->
    <h1 class="text-3xl font-medium text-gray-800 mb-10">有什么想法，说来听听？</h1>

    <!-- 居中输入框 -->
    <div class="w-full max-w-2xl">
      <div class="relative bg-gray-50 border border-gray-200 rounded-full shadow-sm transition-all hover:border-gray-300 hover:shadow-md">
        <textarea
          v-model="inputValue"
          @keydown.enter="handleEnter"
          placeholder="开始对话，探索无限可能..."
          class="w-full bg-transparent text-gray-800 placeholder-gray-400 py-3 pl-5 pr-14 min-h-[48px] max-h-32 resize-none scrollbar-hide outline-none border-none focus:ring-0 focus:outline-none"
          rows="1"
        ></textarea>

        <div class="absolute bottom-2.5 right-2.5 flex items-center gap-2">
          <button @click="submit" :disabled="!inputValue.trim() || isLoading"
             class="p-2 disabled:opacity-40 disabled:cursor-not-allowed rounded-full text-white transition-all shadow-lg cursor-pointer"
             style="background: var(--theme-gradient-btn); box-shadow: 0 4px 14px var(--theme-shadow);">
             <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
               <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 10l7-7m0 0l7 7m-7-7v18"/>
             </svg>
          </button>
        </div>
      </div>

      <!-- 示例标签 -->
      <div class="mt-5 flex flex-wrap justify-center gap-2">
        <button v-for="example in examplePrompts" :key="example.title"
             @click="setPrompt(example.prompt)"
             class="px-3 py-1.5 text-sm text-gray-500 bg-white rounded-full border border-gray-200 hover:border-purple-300 hover:text-purple-600 hover:bg-purple-50 transition-all cursor-pointer">
          {{ example.icon }} {{ example.title }}
        </button>
      </div>
    </div>

    <!-- 底部模型选择器 + 提示 -->
    <div class="absolute bottom-6 text-center text-xs text-gray-400">
      <div class="relative inline-flex items-center gap-1.5">
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
        <span>AI 可能产生不准确信息，请核实重要内容</span>
      </div>
      <div v-if="showModelMenu" class="fixed inset-0 z-40" @click="showModelMenu = false"></div>
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
