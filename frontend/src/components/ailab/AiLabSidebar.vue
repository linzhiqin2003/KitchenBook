<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'

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

const emit = defineEmits(['select', 'new', 'delete', 'toggle-collapse', 'rename'])

// 下拉菜单状态
const activeMenuId = ref(null)
const menuButtonRefs = ref({})
const menuPosition = ref(null)

// 删除确认状态
const deleteTarget = ref(null)

// 内联编辑状态
const editingChatId = ref(null)
const editingTitle = ref('')
const inlineEditRef = ref(null)

// 按日期分组会话
const groupedConversations = computed(() => {
  const today = new Date()
  today.setHours(0, 0, 0, 0)
  const yesterday = new Date(today)
  yesterday.setDate(yesterday.getDate() - 1)
  const lastWeek = new Date(today)
  lastWeek.setDate(lastWeek.getDate() - 7)

  const groups = {}

  props.conversations.forEach(conv => {
    const date = new Date(conv.updated_at)
    date.setHours(0, 0, 0, 0)

    let groupName
    if (date.getTime() >= today.getTime()) {
      groupName = '今天'
    } else if (date.getTime() >= yesterday.getTime()) {
      groupName = '昨天'
    } else if (date.getTime() >= lastWeek.getTime()) {
      groupName = '7天内'
    } else {
      groupName = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}`
    }

    if (!groups[groupName]) {
      groups[groupName] = []
    }
    groups[groupName].push(conv)
  })

  return groups
})

const formatTitle = (title) => {
  if (!title) return '新对话'
  return title.length > 20 ? title.slice(0, 20) + '...' : title
}

// 切换下拉菜单
function toggleMenu(chatId) {
  if (activeMenuId.value === chatId) {
    activeMenuId.value = null
    menuPosition.value = null
  } else {
    activeMenuId.value = chatId
    const button = menuButtonRefs.value[chatId]
    if (button) {
      const rect = button.getBoundingClientRect()
      menuPosition.value = {
        left: rect.right + 4,
        top: rect.top
      }
    }
  }
}

// 获取当前活动的会话
const activeChat = computed(() => {
  if (!activeMenuId.value || !props.conversations) return null
  return props.conversations.find(c => c.id === activeMenuId.value)
})

// 处理重命名
function handleRename(chat) {
  activeMenuId.value = null
  menuPosition.value = null
  editingChatId.value = chat.id
  editingTitle.value = chat.title || ''
  nextTick(() => {
    const input = inlineEditRef.value
    if (Array.isArray(input)) {
      input[0]?.focus()
      input[0]?.select()
    } else if (input) {
      input.focus()
      input.select()
    }
  })
}

function saveInlineEdit(chat) {
  if (editingChatId.value === chat.id && editingTitle.value.trim()) {
    emit('rename', { chat, newTitle: editingTitle.value.trim() })
  }
  editingChatId.value = null
  editingTitle.value = ''
}

function cancelInlineEdit() {
  editingChatId.value = null
  editingTitle.value = ''
}

// 处理删除
function handleDelete(chat) {
  activeMenuId.value = null
  menuPosition.value = null
  deleteTarget.value = chat
}

function executeDelete() {
  if (deleteTarget.value) {
    emit('delete', deleteTarget.value.id)
    deleteTarget.value = null
  }
}

// 点击外部关闭菜单
function handleClickOutside(e) {
  if (activeMenuId.value) {
    const clickedMenuButton = Object.values(menuButtonRefs.value).some(
      btn => btn && btn.contains(e.target)
    )
    if (!clickedMenuButton) {
      activeMenuId.value = null
      menuPosition.value = null
    }
  }
}

onMounted(() => {
  document.addEventListener('click', handleClickOutside)
})

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
})
</script>

<template>
  <div class="flex flex-col h-full bg-gray-50 transition-all duration-300 border-r border-gray-200"
       :class="[
         isCollapsed ? 'w-0 lg:w-16 overflow-hidden' : 'w-64',
         'fixed z-50 lg:relative lg:z-auto'
       ]">
    <!-- Header -->
    <div class="px-4 py-4 flex items-center" :class="isCollapsed ? 'justify-center' : 'justify-between'">
      <!-- Logo (only when expanded) -->
      <div v-if="!isCollapsed" class="flex items-center gap-2.5">
        <div class="w-9 h-9 rounded-xl flex items-center justify-center shadow-lg flex-shrink-0"
             style="background: var(--theme-gradient); box-shadow: 0 4px 14px var(--theme-shadow);">
          <span class="text-white text-sm">✨</span>
        </div>
        <span class="text-base font-semibold text-gray-800">AI Lab</span>
      </div>

      <!-- Collapse Toggle -->
      <button @click="emit('toggle-collapse')"
              class="p-1.5 rounded-lg text-gray-400 hover:text-gray-600 hover:bg-gray-200 transition-all cursor-pointer"
              :title="isCollapsed ? '展开侧边栏' : '折叠侧边栏'">
        <svg v-if="!isCollapsed" class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 19l-7-7 7-7m8 14l-7-7 7-7"/>
        </svg>
        <svg v-else class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 5l7 7-7 7M5 5l7 7-7 7"/>
        </svg>
      </button>
    </div>

    <!-- New Chat Button -->
    <div class="px-3 pb-3">
      <button @click="emit('new')"
              class="w-full flex items-center justify-center gap-2 px-4 py-2.5 bg-white hover:bg-gray-100 text-gray-700 rounded-full transition-colors border border-gray-200 hover:border-gray-300 shadow-sm cursor-pointer">
        <svg class="w-4 h-4 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"/>
        </svg>
        <span v-if="!isCollapsed" class="text-sm font-medium">新对话</span>
      </button>
    </div>

    <!-- 会话列表 -->
    <div class="flex-1 overflow-y-auto px-3 py-2 custom-scrollbar">
      <div v-if="conversations.length === 0 && !isCollapsed" class="text-center text-gray-400 text-sm mt-10 px-4">
        <div class="w-12 h-12 mx-auto mb-3 rounded-full bg-gray-100 flex items-center justify-center">
          <svg class="w-5 h-5 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"/>
          </svg>
        </div>
        暂无历史记录
      </div>

      <!-- 按日期分组 -->
      <template v-for="(group, groupName) in groupedConversations" :key="groupName">
        <div v-if="!isCollapsed" class="text-xs text-gray-400 px-2 py-2 mt-2 first:mt-0">
          {{ groupName }}
        </div>
        <div v-for="chat in group" :key="chat.id"
             @click="editingChatId !== chat.id && emit('select', chat.id)"
             class="group flex items-center justify-between px-2 py-2 rounded-lg cursor-pointer transition-colors relative"
             :class="[
               currentId === chat.id ? 'bg-purple-50' : 'hover:bg-gray-100',
               isCollapsed ? 'justify-center' : ''
             ]"
             :title="isCollapsed ? chat.title : ''">

          <div class="flex items-center gap-2 flex-1 min-w-0">
            <svg v-if="isCollapsed" class="w-4 h-4 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"/>
            </svg>
            <!-- 内联编辑 -->
            <input v-else-if="editingChatId === chat.id"
                   ref="inlineEditRef"
                   v-model="editingTitle"
                   @click.stop
                   @keyup.enter="saveInlineEdit(chat)"
                   @keyup.esc="cancelInlineEdit"
                   @blur="saveInlineEdit(chat)"
                   type="text"
                   class="flex-1 px-2 py-1 text-sm border border-purple-300 rounded-lg bg-white focus:outline-none focus:ring-2 focus:ring-purple-500/30" />
            <!-- 正常显示 -->
            <span v-else class="truncate text-sm" :class="currentId === chat.id ? 'text-gray-800' : 'text-gray-600'">
              {{ formatTitle(chat.title) }}
            </span>
          </div>

          <!-- 更多按钮 -->
          <div v-if="!isCollapsed && editingChatId !== chat.id" class="relative">
            <button
              :ref="el => menuButtonRefs[chat.id] = el"
              @click.stop="toggleMenu(chat.id)"
              class="opacity-0 group-hover:opacity-100 px-2.5 py-1 rounded-full bg-gray-100 hover:bg-gray-200 text-gray-400 hover:text-gray-600 transition-all flex-shrink-0 cursor-pointer"
              :class="{ 'opacity-100 bg-gray-200': activeMenuId === chat.id }">
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 12h.01M12 12h.01M19 12h.01"/>
              </svg>
            </button>
          </div>
        </div>
      </template>
    </div>

    <!-- 底部返回首页 -->
    <div class="p-3 border-t border-gray-200">
      <router-link
        to="/"
        :class="[
          'flex items-center gap-2 px-3 py-2 rounded-lg hover:bg-gray-100 transition-colors text-gray-600 hover:text-gray-800',
          isCollapsed && 'justify-center'
        ]"
      >
        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6"/>
        </svg>
        <span v-if="!isCollapsed" class="text-sm">返回首页</span>
      </router-link>
    </div>
  </div>

  <!-- Teleport 下拉菜单 -->
  <Teleport to="body">
    <Transition name="dropdown">
      <div v-if="activeMenuId && menuPosition"
           @click.stop
           :style="{ left: menuPosition.left + 'px', top: menuPosition.top + 'px' }"
           class="fixed w-28 bg-white rounded-lg shadow-lg border border-gray-200 py-1 z-[200]">
        <button @click.stop="handleRename(activeChat)" class="w-full flex items-center gap-2 px-3 py-2 text-sm text-gray-700 hover:bg-gray-50 transition-colors cursor-pointer">
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"/>
          </svg>
          重命名
        </button>
        <div class="border-t border-gray-100 my-1"></div>
        <button @click.stop="handleDelete(activeChat)" class="w-full flex items-center gap-2 px-3 py-2 text-sm text-red-500 hover:bg-red-50 transition-colors cursor-pointer">
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/>
          </svg>
          删除
        </button>
      </div>
    </Transition>
  </Teleport>

  <!-- 删除确认弹窗 -->
  <Teleport to="body">
    <Transition name="modal">
      <div v-if="deleteTarget"
           class="fixed inset-0 z-[100] flex items-center justify-center p-4"
           @click.self="deleteTarget = null">
        <!-- 遮罩 -->
        <div class="absolute inset-0 bg-black/20 backdrop-blur-[2px]" @click="deleteTarget = null"></div>

        <!-- 弹窗 -->
        <div class="relative bg-white rounded-2xl p-6 max-w-sm w-full shadow-xl transform transition-all">
          <h3 class="text-base font-semibold text-gray-900 mb-2">删除对话</h3>
          <p class="text-sm text-gray-500 mb-6">
            删除后，该对话将不可恢复。确认删除吗？
          </p>
          <div class="flex justify-end gap-3">
            <button @click="deleteTarget = null"
                    class="px-5 py-2 border border-gray-300 hover:bg-gray-50 text-gray-700 rounded-full transition-all text-sm font-medium cursor-pointer">
              取消
            </button>
            <button @click="executeDelete"
                    class="px-5 py-2 border border-red-400 hover:bg-red-50 text-red-500 rounded-full transition-all text-sm font-medium cursor-pointer">
              删除
            </button>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>

  <!-- 移动端遮罩 -->
  <div v-if="!isCollapsed" @click="emit('toggle-collapse')"
       class="fixed inset-0 bg-black/30 z-40 lg:hidden backdrop-blur-sm"></div>
</template>

<style scoped>
.custom-scrollbar::-webkit-scrollbar {
  width: 6px;
}
.custom-scrollbar::-webkit-scrollbar-track {
  background: transparent;
}
.custom-scrollbar::-webkit-scrollbar-thumb {
  background: #d1d5db;
  border-radius: 3px;
}
.custom-scrollbar::-webkit-scrollbar-thumb:hover {
  background: #9ca3af;
}

/* Modal transition */
.modal-enter-active,
.modal-leave-active {
  transition: all 0.25s ease-out;
}

.modal-enter-from,
.modal-leave-to {
  opacity: 0;
}

.modal-enter-from > div:last-child,
.modal-leave-to > div:last-child {
  transform: scale(0.95);
  opacity: 0;
}

.modal-enter-active > div:last-child,
.modal-leave-active > div:last-child {
  transition: all 0.2s ease-out;
}

/* Dropdown transition */
.dropdown-enter-active,
.dropdown-leave-active {
  transition: all 0.15s ease-out;
}

.dropdown-enter-from,
.dropdown-leave-to {
  opacity: 0;
  transform: translateY(-4px);
}
</style>
