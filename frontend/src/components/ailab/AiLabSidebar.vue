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
  <div class="flex flex-col transition-all duration-300"
       style="background: #f7f7f8; border-right: 1px solid #ebebed; font-family: var(--ai-font-body); height: 100vh; height: 100dvh;"
       :class="[
         isCollapsed ? 'w-0 lg:w-16 overflow-hidden' : 'w-60',
         'fixed z-50 lg:relative lg:z-auto'
       ]">
    <!-- Header -->
    <div class="px-4 py-3 flex items-center" :class="isCollapsed ? 'justify-center' : 'justify-between'">
      <div v-if="!isCollapsed" class="flex items-center gap-2">
        <span class="text-[13px] font-semibold tracking-tight" style="color: var(--theme-700);">AI Lab</span>
      </div>
      <button @click="emit('toggle-collapse')"
              class="p-1 rounded-md transition-all cursor-pointer"
              style="color: var(--theme-400);"
              :title="isCollapsed ? '展开侧边栏' : '折叠侧边栏'">
        <svg v-if="!isCollapsed" class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="1.5">
          <path stroke-linecap="round" stroke-linejoin="round" d="M15.75 19.5L8.25 12l7.5-7.5"/>
        </svg>
        <svg v-else class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="1.5">
          <path stroke-linecap="round" stroke-linejoin="round" d="M8.25 4.5l7.5 7.5-7.5 7.5"/>
        </svg>
      </button>
    </div>

    <!-- New Chat Button -->
    <div class="px-3 pb-2">
      <button @click="emit('new')"
              class="w-full flex items-center justify-center gap-1.5 px-3 py-2 rounded-lg transition-colors cursor-pointer text-[13px] font-medium"
              style="background: #fff; border: 1px solid #e0e0e3; color: #4a4a4f;">
        <svg class="w-3.5 h-3.5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="1.5">
          <path stroke-linecap="round" stroke-linejoin="round" d="M12 4.5v15m7.5-7.5h-15"/>
        </svg>
        <span v-if="!isCollapsed">新对话</span>
      </button>
    </div>

    <!-- 会话列表 -->
    <div class="flex-1 min-h-0 overflow-y-auto px-2 py-1 custom-scrollbar">
      <div v-if="conversations.length === 0 && !isCollapsed" class="text-center mt-10 px-4" style="color: var(--theme-400); font-size: 13px;">
        暂无历史记录
      </div>

      <template v-for="(group, groupName) in groupedConversations" :key="groupName">
        <div v-if="!isCollapsed" class="px-2 py-1.5 mt-3 first:mt-0" style="font-size: 11px; font-weight: 500; color: #9a9aa0; letter-spacing: 0.02em;">
          {{ groupName }}
        </div>
        <div v-for="chat in group" :key="chat.id"
             @click="editingChatId !== chat.id && emit('select', chat.id)"
             class="group flex items-center justify-between px-2 py-1.5 rounded-md cursor-pointer transition-colors relative"
             :class="[
               isCollapsed ? 'justify-center' : ''
             ]"
             :style="currentId === chat.id ? 'background: #eeeef0; color: #2c2c30;' : 'color: #6e6e76;'"
             :title="isCollapsed ? chat.title : ''">

          <div class="flex items-center gap-2 flex-1 min-w-0">
            <svg v-if="isCollapsed" class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="1.5" style="color: var(--theme-400);">
              <path stroke-linecap="round" stroke-linejoin="round" d="M7.5 8.25h9m-9 3H12m-9.75 1.51c0 1.6 1.123 2.994 2.707 3.227 1.129.166 2.27.293 3.423.379.35.026.67.21.865.501L12 21l2.755-4.133a1.14 1.14 0 01.865-.501 48.172 48.172 0 003.423-.379c1.584-.233 2.707-1.626 2.707-3.228V6.741c0-1.602-1.123-2.995-2.707-3.228A48.394 48.394 0 0012 3c-2.392 0-4.744.175-7.043.513C3.373 3.746 2.25 5.14 2.25 6.741v6.018z"/>
            </svg>
            <input v-else-if="editingChatId === chat.id"
                   ref="inlineEditRef"
                   v-model="editingTitle"
                   @click.stop
                   @keyup.enter="saveInlineEdit(chat)"
                   @keyup.esc="cancelInlineEdit"
                   @blur="saveInlineEdit(chat)"
                   type="text"
                   class="flex-1 px-2 py-0.5 text-[13px] rounded-md bg-white focus:outline-none"
                   style="border: 1px solid var(--ai-accent); color: var(--theme-700);" />
            <span v-else class="truncate text-[13px]">
              {{ formatTitle(chat.title) }}
            </span>
          </div>

          <div v-if="!isCollapsed && editingChatId !== chat.id" class="relative">
            <button
              :ref="el => menuButtonRefs[chat.id] = el"
              @click.stop="toggleMenu(chat.id)"
              class="opacity-0 group-hover:opacity-100 p-1 rounded-md transition-all flex-shrink-0 cursor-pointer"
              :class="{ 'opacity-100': activeMenuId === chat.id }"
              style="color: var(--theme-400);">
              <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M6.75 12a.75.75 0 11-1.5 0 .75.75 0 011.5 0zM12.75 12a.75.75 0 11-1.5 0 .75.75 0 011.5 0zM18.75 12a.75.75 0 11-1.5 0 .75.75 0 011.5 0z"/>
              </svg>
            </button>
          </div>
        </div>
      </template>
    </div>

    <!-- 底部导航 -->
    <div class="px-2 pt-2 pb-8 space-y-0.5 shrink-0" style="border-top: 1px solid #ebebed;">
      <router-link
        to="/ai-lab/studio"
        :class="['flex items-center gap-2 px-2.5 py-1.5 rounded-md transition-colors hover:bg-black/[0.04]', isCollapsed && 'justify-center']"
        style="color: #8a8a90; font-size: 13px;"
        :title="isCollapsed ? 'Studio' : ''"
      >
        <svg class="w-4 h-4 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="1.5">
          <path stroke-linecap="round" stroke-linejoin="round" d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09zM18.259 8.715L18 9.75l-.259-1.035a3.375 3.375 0 00-2.455-2.456L14.25 6l1.036-.259a3.375 3.375 0 002.455-2.456L18 2.25l.259 1.035a3.375 3.375 0 002.455 2.456L21.75 6l-1.036.259a3.375 3.375 0 00-2.455 2.456zM16.894 20.567L16.5 21.75l-.394-1.183a2.25 2.25 0 00-1.423-1.423L13.5 18.75l1.183-.394a2.25 2.25 0 001.423-1.423l.394-1.183.394 1.183a2.25 2.25 0 001.423 1.423l1.183.394-1.183.394a2.25 2.25 0 00-1.423 1.423z"/>
        </svg>
        <span v-if="!isCollapsed">Studio</span>
      </router-link>
      <router-link
        to="/"
        :class="['flex items-center gap-2 px-2.5 py-1.5 rounded-md transition-colors hover:bg-black/[0.04]', isCollapsed && 'justify-center']"
        style="color: #8a8a90; font-size: 13px;"
      >
        <svg class="w-4 h-4 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="1.5">
          <path stroke-linecap="round" stroke-linejoin="round" d="M2.25 12l8.954-8.955c.44-.439 1.152-.439 1.591 0L21.75 12M4.5 9.75v10.125c0 .621.504 1.125 1.125 1.125H9.75v-4.875c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125V21h4.125c.621 0 1.125-.504 1.125-1.125V9.75M8.25 21h8.25"/>
        </svg>
        <span v-if="!isCollapsed">首页</span>
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
