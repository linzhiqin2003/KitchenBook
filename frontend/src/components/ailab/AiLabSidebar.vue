<script setup>
import { computed } from 'vue'

const props = defineProps({
  conversations: {
    type: Array,
    default: () => []
  },
  currentId: {
    type: [Number, String],
    default: null
  },
  isCollapsed: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['select', 'new', 'delete', 'toggle-collapse'])

// 按日期分组会话
const groupedConversations = computed(() => {
  const today = new Date()
  today.setHours(0, 0, 0, 0)
  const yesterday = new Date(today)
  yesterday.setDate(yesterday.getDate() - 1)
  const lastWeek = new Date(today)
  lastWeek.setDate(lastWeek.getDate() - 7)

  const groups = {
    today: [],
    yesterday: [],
    lastWeek: [],
    older: []
  }

  props.conversations.forEach(conv => {
    const date = new Date(conv.updated_at)
    date.setHours(0, 0, 0, 0)

    if (date.getTime() >= today.getTime()) {
      groups.today.push(conv)
    } else if (date.getTime() >= yesterday.getTime()) {
      groups.yesterday.push(conv)
    } else if (date.getTime() >= lastWeek.getTime()) {
      groups.lastWeek.push(conv)
    } else {
      groups.older.push(conv)
    }
  })

  return groups
})

const formatTitle = (title) => {
  if (!title) return '新对话'
  return title.length > 20 ? title.slice(0, 20) + '...' : title
}
</script>

<template>
  <aside
    :class="[
      'h-full bg-gray-900 text-white flex flex-col transition-all duration-300 ease-in-out z-50',
      isCollapsed ? 'w-0 lg:w-16 overflow-hidden' : 'w-64',
      'fixed lg:relative left-0 top-0'
    ]"
  >
    <!-- 顶部区域 -->
    <div class="p-3 border-b border-gray-800">
      <div class="flex items-center justify-between">
        <!-- 折叠时只显示 Logo -->
        <div v-if="!isCollapsed" class="flex items-center gap-2">
          <div class="w-8 h-8 rounded-lg bg-gradient-to-br from-violet-500 to-purple-600 flex items-center justify-center">
            <span class="text-sm">✨</span>
          </div>
          <span class="font-semibold text-sm">AI Lab</span>
        </div>

        <!-- 折叠按钮 -->
        <button
          @click="emit('toggle-collapse')"
          class="w-8 h-8 rounded-lg hover:bg-gray-800 flex items-center justify-center transition-colors cursor-pointer"
          :class="{ 'mx-auto': isCollapsed }"
        >
          <svg
            class="w-5 h-5 transition-transform"
            :class="{ 'rotate-180': isCollapsed }"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 19l-7-7 7-7m8 14l-7-7 7-7"/>
          </svg>
        </button>
      </div>

      <!-- 新建对话按钮 -->
      <button
        @click="emit('new')"
        :class="[
          'mt-3 w-full flex items-center gap-2 px-3 py-2.5 rounded-lg bg-violet-600 hover:bg-violet-500 transition-colors cursor-pointer',
          isCollapsed && 'justify-center'
        ]"
      >
        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"/>
        </svg>
        <span v-if="!isCollapsed" class="text-sm font-medium">新对话</span>
      </button>
    </div>

    <!-- 会话列表 -->
    <div class="flex-1 overflow-y-auto px-2 py-3 space-y-4 custom-scrollbar">
      <!-- 折叠状态显示简化列表 -->
      <template v-if="isCollapsed">
        <button
          v-for="conv in conversations.slice(0, 10)"
          :key="conv.id"
          @click="emit('select', conv.id)"
          :class="[
            'w-full p-2 rounded-lg transition-colors cursor-pointer',
            currentId === conv.id ? 'bg-violet-600' : 'hover:bg-gray-800'
          ]"
          :title="conv.title"
        >
          <div class="w-8 h-8 rounded-full bg-gray-700 flex items-center justify-center text-xs">
            {{ conv.title?.charAt(0) || '新' }}
          </div>
        </button>
      </template>

      <!-- 展开状态显示分组列表 -->
      <template v-else>
        <!-- 今天 -->
        <div v-if="groupedConversations.today.length > 0">
          <div class="px-3 py-1.5 text-xs text-gray-500 font-medium">今天</div>
          <div class="space-y-1">
            <div
              v-for="conv in groupedConversations.today"
              :key="conv.id"
              :class="[
                'group flex items-center gap-2 px-3 py-2 rounded-lg transition-colors cursor-pointer',
                currentId === conv.id ? 'bg-violet-600/20 text-violet-300' : 'hover:bg-gray-800'
              ]"
              @click="emit('select', conv.id)"
            >
              <div class="flex-1 min-w-0">
                <div class="text-sm truncate">{{ formatTitle(conv.title) }}</div>
              </div>
              <button
                @click.stop="emit('delete', conv.id)"
                class="opacity-0 group-hover:opacity-100 w-6 h-6 rounded hover:bg-red-500/20 hover:text-red-400 flex items-center justify-center transition-all cursor-pointer"
              >
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/>
                </svg>
              </button>
            </div>
          </div>
        </div>

        <!-- 昨天 -->
        <div v-if="groupedConversations.yesterday.length > 0">
          <div class="px-3 py-1.5 text-xs text-gray-500 font-medium">昨天</div>
          <div class="space-y-1">
            <div
              v-for="conv in groupedConversations.yesterday"
              :key="conv.id"
              :class="[
                'group flex items-center gap-2 px-3 py-2 rounded-lg transition-colors cursor-pointer',
                currentId === conv.id ? 'bg-violet-600/20 text-violet-300' : 'hover:bg-gray-800'
              ]"
              @click="emit('select', conv.id)"
            >
              <div class="flex-1 min-w-0">
                <div class="text-sm truncate">{{ formatTitle(conv.title) }}</div>
              </div>
              <button
                @click.stop="emit('delete', conv.id)"
                class="opacity-0 group-hover:opacity-100 w-6 h-6 rounded hover:bg-red-500/20 hover:text-red-400 flex items-center justify-center transition-all cursor-pointer"
              >
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/>
                </svg>
              </button>
            </div>
          </div>
        </div>

        <!-- 过去7天 -->
        <div v-if="groupedConversations.lastWeek.length > 0">
          <div class="px-3 py-1.5 text-xs text-gray-500 font-medium">过去7天</div>
          <div class="space-y-1">
            <div
              v-for="conv in groupedConversations.lastWeek"
              :key="conv.id"
              :class="[
                'group flex items-center gap-2 px-3 py-2 rounded-lg transition-colors cursor-pointer',
                currentId === conv.id ? 'bg-violet-600/20 text-violet-300' : 'hover:bg-gray-800'
              ]"
              @click="emit('select', conv.id)"
            >
              <div class="flex-1 min-w-0">
                <div class="text-sm truncate">{{ formatTitle(conv.title) }}</div>
              </div>
              <button
                @click.stop="emit('delete', conv.id)"
                class="opacity-0 group-hover:opacity-100 w-6 h-6 rounded hover:bg-red-500/20 hover:text-red-400 flex items-center justify-center transition-all cursor-pointer"
              >
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/>
                </svg>
              </button>
            </div>
          </div>
        </div>

        <!-- 更早 -->
        <div v-if="groupedConversations.older.length > 0">
          <div class="px-3 py-1.5 text-xs text-gray-500 font-medium">更早</div>
          <div class="space-y-1">
            <div
              v-for="conv in groupedConversations.older"
              :key="conv.id"
              :class="[
                'group flex items-center gap-2 px-3 py-2 rounded-lg transition-colors cursor-pointer',
                currentId === conv.id ? 'bg-violet-600/20 text-violet-300' : 'hover:bg-gray-800'
              ]"
              @click="emit('select', conv.id)"
            >
              <div class="flex-1 min-w-0">
                <div class="text-sm truncate">{{ formatTitle(conv.title) }}</div>
              </div>
              <button
                @click.stop="emit('delete', conv.id)"
                class="opacity-0 group-hover:opacity-100 w-6 h-6 rounded hover:bg-red-500/20 hover:text-red-400 flex items-center justify-center transition-all cursor-pointer"
              >
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/>
                </svg>
              </button>
            </div>
          </div>
        </div>

        <!-- 空状态 -->
        <div v-if="conversations.length === 0" class="text-center py-8 text-gray-500 text-sm">
          还没有对话记录
        </div>
      </template>
    </div>

    <!-- 底部链接 -->
    <div class="p-3 border-t border-gray-800">
      <router-link
        to="/"
        :class="[
          'flex items-center gap-2 px-3 py-2 rounded-lg hover:bg-gray-800 transition-colors text-gray-400 hover:text-white',
          isCollapsed && 'justify-center'
        ]"
      >
        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6"/>
        </svg>
        <span v-if="!isCollapsed" class="text-sm">返回首页</span>
      </router-link>
    </div>
  </aside>
</template>

<style scoped>
.custom-scrollbar::-webkit-scrollbar {
  width: 6px;
}
.custom-scrollbar::-webkit-scrollbar-track {
  background: transparent;
}
.custom-scrollbar::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.1);
  border-radius: 3px;
}
.custom-scrollbar::-webkit-scrollbar-thumb:hover {
  background: rgba(255, 255, 255, 0.2);
}
</style>
