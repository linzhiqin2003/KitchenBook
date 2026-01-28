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

// 滚动到底部
const scrollToBottom = async () => {
  await nextTick()
  if (messagesContainer.value) {
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
  }
}

// 监听消息变化，自动滚动
watch(() => props.messages.length, () => {
  scrollToBottom()
})

watch(() => props.messages[props.currentStreamingIndex]?.content, () => {
  scrollToBottom()
}, { deep: true })

watch(() => props.messages[props.currentStreamingIndex]?.reasoning, () => {
  scrollToBottom()
}, { deep: true })

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
      class="flex-1 overflow-y-auto px-4 py-6 scroll-smooth"
    >
      <div class="max-w-4xl mx-auto space-y-6">
        <TransitionGroup name="message">
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
        </TransitionGroup>
      </div>
    </div>
  </div>
</template>

<style scoped>
/* 消息动画 */
.message-enter-active {
  animation: message-in 0.3s ease-out;
}

@keyframes message-in {
  0% {
    opacity: 0;
    transform: translateY(10px);
  }
  100% {
    opacity: 1;
    transform: translateY(0);
  }
}

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
