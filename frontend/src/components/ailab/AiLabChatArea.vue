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
// 记录已经"思维链结束→自动折叠"过的消息 index，避免在用户重新展开后被再次折叠
const autoCollapsedOnce = new Set()
const isNearBottom = ref(true)

// 用户主动上滑后停止自动跟随。流式更新到达时不再硬把视图拽回底部，
// 避免"用户滑一下、新 chunk 把它拉回去"的来回抖动。
// 一旦用户重新滚回底部 100px 范围内，自动跟随恢复。
const userScrolledUp = ref(false)
let suppressNextScrollEvent = false

// 跟踪用户滚动位置
const handleScroll = () => {
  if (!messagesContainer.value) return
  // 我们刚执行的 programmatic scroll 也会触发 scroll 事件 —— 跳过它，
  // 否则下一次窗口判断会因为 scrollTop 还在终态而误判为"用户在底部"。
  if (suppressNextScrollEvent) {
    suppressNextScrollEvent = false
    return
  }
  const { scrollTop, scrollHeight, clientHeight } = messagesContainer.value
  const near = scrollHeight - scrollTop - clientHeight < 100
  isNearBottom.value = near
  if (near) {
    // 用户自己滑回了底部 → 重新启用自动跟随
    userScrolledUp.value = false
  } else {
    // 用户向上滑离了底部 → 锁住自动跟随
    userScrolledUp.value = true
  }
}

// 防抖滚动：force=true 强制滚动，否则仅在用户跟随状态下滚动
let scrollPending = false
const scrollToBottom = (force = false) => {
  if (!force && (userScrolledUp.value || !isNearBottom.value)) return
  if (scrollPending) return
  scrollPending = true
  nextTick(() => {
    requestAnimationFrame(() => {
      scrollPending = false
      if (messagesContainer.value) {
        suppressNextScrollEvent = true
        messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
        isNearBottom.value = true
        if (force) userScrolledUp.value = false
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

// 思维链阶段结束（reasoning → answering）时自动折叠当前流式消息的思维链，
// 给最终答案让出视觉焦点。每条消息只自动折叠一次，用户后续展开后不再干预。
watch(
  () => props.isReasoningPhase,
  (now, prev) => {
    if (prev !== true || now !== false) return
    const idx = props.currentStreamingIndex
    if (idx == null) return
    if (autoCollapsedOnce.has(idx)) return
    autoCollapsedOnce.add(idx)
    reasoningCollapsed.value[idx] = true
  }
)

// 暴露方法给父组件
defineExpose({
  scrollToBottom
})
</script>

<template>
  <div class="flex-1 flex flex-col overflow-hidden relative">
    <!-- 会话标题栏 -->
    <div v-if="conversationTitle" class="shrink-0 h-11 flex items-center px-5" style="border-bottom: 1px solid var(--theme-200, #e4e4df);">
      <h2 class="truncate" style="font-size: 14px; font-weight: 500; color: var(--theme-500, #6b6b63);">{{ conversationTitle }}</h2>
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
        class="scroll-bottom-btn absolute bottom-1 left-1/2 -translate-x-1/2 px-2 py-1 cursor-pointer flex items-center gap-1 z-10"
        style="font-size: 12px; color: var(--theme-400, #8a8a82); background: transparent; border: none;"
      >
        <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
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

.scroll-bottom-btn {
  transition: color 0.15s ease, transform 0.15s ease;
}
.scroll-bottom-btn:hover {
  color: var(--theme-600, #5a5a52);
  transform: translate(-50%, -1px);
}
</style>
