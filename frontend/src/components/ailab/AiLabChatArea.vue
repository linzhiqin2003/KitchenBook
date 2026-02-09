<script setup>
import { ref, watch, nextTick } from 'vue'
import AiLabMessageItem from './AiLabMessageItem.vue'

const props = defineProps({
  messages: {
    type: Array,
    default: () => []
  },
  currentStreamingIndex: {
    type: Number,
    default: null
  },
  isReasoningPhase: {
    type: Boolean,
    default: false
  },
  conversationTitle: {
    type: String,
    default: ''
  }
})

const emit = defineEmits(['edit', 'regenerate'])

const messagesContainer = ref(null)
const reasoningCollapsed = ref({})
const isNearBottom = ref(true)

// 跟踪用户滚动位置
const handleScroll = () => {
  if (!messagesContainer.value) return
  const { scrollTop, scrollHeight, clientHeight } = messagesContainer.value
  isNearBottom.value = scrollHeight - scrollTop - clientHeight < 100
}

// 防抖滚动：force=true 强制滚动，否则仅在用户位于底部时滚动
let scrollPending = false
const scrollToBottom = (force = false) => {
  if (!force && !isNearBottom.value) return
  if (scrollPending) return
  scrollPending = true
  nextTick(() => {
    requestAnimationFrame(() => {
      scrollPending = false
      if (messagesContainer.value) {
        messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
        isNearBottom.value = true
      }
    })
  })
}

// 新消息到达时强制滚动到底部
watch(
  () => props.messages.length,
  () => { scrollToBottom(true) }
)

// 流式内容更新时，仅在用户已在底部附近时滚动
watch(
  () => {
    const idx = props.currentStreamingIndex
    const msg = idx != null ? props.messages[idx] : null
    return [
      msg?.content,
      msg?.reasoning,
      msg?.subTurns?.length,
      msg?.currentReasoning,
      msg?.currentToolCall?.argumentsText,
      msg?.currentToolCall?.status,
    ]
  },
  () => { scrollToBottom() },
  { deep: false }
)

// 切换思维链折叠
const toggleReasoning = (index) => {
  reasoningCollapsed.value[index] = !reasoningCollapsed.value[index]
}

// 暴露方法给父组件
defineExpose({
  scrollToBottom
})
</script>

<template>
  <div class="flex-1 flex flex-col overflow-hidden relative">
    <!-- 会话标题栏 -->
    <div v-if="conversationTitle" class="shrink-0 h-12 border-b border-gray-200 flex items-center px-4 bg-white/80 backdrop-blur-sm">
      <h2 class="text-sm font-medium text-gray-700 truncate">{{ conversationTitle }}</h2>
    </div>

    <!-- 消息列表 -->
    <div
      ref="messagesContainer"
      @scroll="handleScroll"
      class="flex-1 overflow-y-auto px-4 pt-6 pb-40"
    >
      <div class="max-w-4xl mx-auto space-y-6">
        <AiLabMessageItem
          v-for="(msg, index) in messages"
          :key="msg.id || index"
          :message="msg"
          :index="index"
          :is-streaming="index === currentStreamingIndex"
          :is-reasoning-phase="index === currentStreamingIndex && isReasoningPhase"
          :reasoning-collapsed="reasoningCollapsed[index]"
          @edit="(id, content) => emit('edit', id, content, index)"
          @regenerate="(id) => emit('regenerate', id, index)"
          @toggle-reasoning="toggleReasoning"
        />
      </div>
    </div>

    <!-- 回到底部按钮 -->
    <Transition name="fade-up">
      <button
        v-if="!isNearBottom"
        @click="scrollToBottom(true)"
        class="absolute bottom-4 left-1/2 -translate-x-1/2 px-3 py-1.5 bg-white/90 backdrop-blur border border-gray-200 rounded-full shadow-lg text-xs text-gray-500 hover:text-gray-700 hover:bg-white transition-all cursor-pointer flex items-center gap-1 z-10"
      >
        <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 14l-7 7m0 0l-7-7m7 7V3"/>
        </svg>
        回到底部
      </button>
    </Transition>
  </div>
</template>

<style scoped>
/* 滚动条样式 */
.overflow-y-auto::-webkit-scrollbar {
  width: 8px;
}
.overflow-y-auto::-webkit-scrollbar-track {
  background: transparent;
}
.overflow-y-auto::-webkit-scrollbar-thumb {
  background: rgba(150, 150, 170, 0.3);
  border-radius: 4px;
}
.overflow-y-auto::-webkit-scrollbar-thumb:hover {
  background: rgba(150, 150, 170, 0.5);
}

.fade-up-enter-active,
.fade-up-leave-active {
  transition: all 0.2s ease;
}
.fade-up-enter-from,
.fade-up-leave-to {
  opacity: 0;
  transform: translate(-50%, 8px);
}
</style>
