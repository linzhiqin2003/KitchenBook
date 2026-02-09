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

// 防抖滚动：等 Vue DOM 更新后再滚动，合并高频调用
let scrollPending = false
const scrollToBottom = () => {
  if (scrollPending) return
  scrollPending = true
  nextTick(() => {
    requestAnimationFrame(() => {
      scrollPending = false
      if (messagesContainer.value) {
        messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
      }
    })
  })
}

// 监听消息变化，自动滚动（合并为单个 watcher）
watch(
  () => {
    const idx = props.currentStreamingIndex
    const msg = idx != null ? props.messages[idx] : null
    return [
      props.messages.length,
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
  <div class="flex-1 flex flex-col overflow-hidden">
    <!-- 会话标题栏 -->
    <div v-if="conversationTitle" class="shrink-0 h-12 border-b border-gray-200 flex items-center px-4 bg-white/80 backdrop-blur-sm">
      <h2 class="text-sm font-medium text-gray-700 truncate">{{ conversationTitle }}</h2>
    </div>

    <!-- 消息列表 -->
    <div
      ref="messagesContainer"
      class="flex-1 overflow-y-auto px-4 py-6"
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
</style>
