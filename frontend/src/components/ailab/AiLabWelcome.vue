<script setup>
defineProps({
  isLoading: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['ask'])

const quickActions = [
  { icon: '🧮', label: '数学推理', prompt: '证明根号2是无理数' },
  { icon: '💻', label: '代码分析', prompt: '用动态规划解决背包问题' },
  { icon: '🧠', label: '深度思考', prompt: '分析人工智能对社会的影响' },
]
</script>

<template>
  <div class="flex-1 flex flex-col items-center justify-center px-4 py-12">
    <!-- Logo 和标题 -->
    <div class="text-center mb-8">
      <div class="w-16 h-16 mx-auto mb-4 rounded-2xl bg-gradient-to-br from-violet-500 to-purple-600 flex items-center justify-center shadow-lg shadow-violet-500/20">
        <span class="text-3xl">✨</span>
      </div>
      <h1 class="text-2xl font-semibold text-gray-800 mb-2">有什么想法，说来听听？</h1>
      <p class="text-gray-500 text-sm">DeepSeek Reasoner 擅长深度推理和复杂问题分析</p>
    </div>

    <!-- 快捷操作 -->
    <div class="flex flex-wrap justify-center gap-3 mb-6">
      <button
        v-for="action in quickActions"
        :key="action.label"
        @click="emit('ask', action.prompt)"
        :disabled="isLoading"
        class="flex items-center gap-2 px-4 py-2.5 bg-white hover:bg-gray-50 border border-gray-200 hover:border-violet-300 rounded-xl text-sm text-gray-600 hover:text-violet-600 transition-all disabled:opacity-50 cursor-pointer shadow-sm hover:shadow"
      >
        <span>{{ action.icon }}</span>
        <span>{{ action.label }}</span>
      </button>
    </div>

    <!-- 提示 -->
    <p class="text-xs text-gray-400 text-center max-w-md">
      DeepSeek Reasoner 可能产生不准确的信息，请核实重要内容
    </p>
  </div>
</template>
