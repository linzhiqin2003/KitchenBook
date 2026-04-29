<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import API_BASE_URL from '../../config/api'

const open = ref(false)
const list = ref([])
const unreadCount = ref(0)
const loading = ref(false)
const error = ref('')

let pollHandle = null
let outsideHandler = null
const wrapperRef = ref(null)

const headers = () => {
  const t = localStorage.getItem('access_token') || ''
  const h = { 'Content-Type': 'application/json' }
  if (t) h['Authorization'] = `Bearer ${t}`
  return h
}

const fetchList = async () => {
  loading.value = true
  error.value = ''
  try {
    const r = await fetch(`${API_BASE_URL}/api/ai/notifications/?limit=50`, { headers: headers() })
    if (!r.ok) throw new Error(`HTTP ${r.status}`)
    const data = await r.json()
    list.value = data.results || []
    unreadCount.value = Number(data.unread_count) || 0
  } catch (e) {
    error.value = e.message
  } finally {
    loading.value = false
  }
}

// 仅拉未读计数 —— 轮询用，不要每 30s 把整列表带回来
const pollUnread = async () => {
  try {
    const r = await fetch(`${API_BASE_URL}/api/ai/notifications/?unread=1&limit=1`, { headers: headers() })
    if (!r.ok) return
    const data = await r.json()
    unreadCount.value = Number(data.unread_count) || 0
  } catch { /* silent */ }
}

const markRead = async (ids) => {
  try {
    const body = ids === 'all' ? { all: true } : { ids: Array.isArray(ids) ? ids : [ids] }
    await fetch(`${API_BASE_URL}/api/ai/notifications/mark-read/`, {
      method: 'POST', headers: headers(), body: JSON.stringify(body)
    })
    if (ids === 'all') {
      list.value.forEach(n => n.is_read = true)
      unreadCount.value = 0
    } else {
      const set = new Set(Array.isArray(ids) ? ids : [ids])
      list.value.forEach(n => { if (set.has(n.id)) n.is_read = true })
      unreadCount.value = list.value.filter(n => !n.is_read).length
    }
  } catch { /* silent */ }
}

const togglePanel = () => {
  open.value = !open.value
  if (open.value) fetchList()
}

const handleNotificationClick = (notif) => {
  if (!notif.is_read) markRead(notif.id)
}

const formatTime = (iso) => {
  if (!iso) return ''
  const d = new Date(iso)
  const now = new Date()
  const diffMs = now - d
  const min = Math.floor(diffMs / 60000)
  if (min < 1) return '刚刚'
  if (min < 60) return `${min} 分钟前`
  const hr = Math.floor(min / 60)
  if (hr < 24) return `${hr} 小时前`
  const day = Math.floor(hr / 24)
  if (day < 7) return `${day} 天前`
  return d.toLocaleDateString('zh-CN')
}

const sourceLabel = (s) => ({
  cron: 'Cron',
  hook: 'Hook',
  manual: '手动',
  agent: 'Agent',
}[s] || s)

const handleOutsideClick = (e) => {
  if (!wrapperRef.value) return
  if (!wrapperRef.value.contains(e.target)) open.value = false
}

onMounted(() => {
  pollUnread()
  pollHandle = setInterval(pollUnread, 30000)
  outsideHandler = handleOutsideClick
  document.addEventListener('click', outsideHandler)
})
onUnmounted(() => {
  if (pollHandle) clearInterval(pollHandle)
  if (outsideHandler) document.removeEventListener('click', outsideHandler)
})
</script>

<template>
  <div ref="wrapperRef" class="relative inline-block">
    <button
      @click.stop="togglePanel"
      class="w-8 h-8 rounded-md flex items-center justify-center transition-colors cursor-pointer relative"
      :style="open ? 'color: var(--theme-700); background: var(--theme-100);' : 'color: var(--theme-400);'"
      title="通知"
    >
      <svg class="w-[18px] h-[18px]" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="1.5">
        <path stroke-linecap="round" stroke-linejoin="round" d="M14.857 17.082a23.848 23.848 0 005.454-1.31A8.967 8.967 0 0118 9.75v-.7V9A6 6 0 006 9v.75a8.967 8.967 0 01-2.312 6.022c1.733.64 3.56 1.085 5.455 1.31m5.714 0a24.255 24.255 0 01-5.714 0m5.714 0a3 3 0 11-5.714 0"/>
      </svg>
      <span
        v-if="unreadCount > 0"
        class="absolute top-0.5 right-0.5 min-w-[14px] h-[14px] rounded-full text-[10px] font-semibold flex items-center justify-center px-1"
        style="background: #ef4444; color: #fff;"
      >{{ unreadCount > 99 ? '99+' : unreadCount }}</span>
    </button>

    <Transition name="panel">
      <div
        v-if="open"
        class="absolute right-0 top-full mt-1.5 w-[360px] max-h-[480px] rounded-xl shadow-lg overflow-hidden z-50 flex flex-col"
        style="background: var(--theme-50); border: 1px solid var(--theme-200);"
        @click.stop
      >
        <div class="px-4 py-2.5 flex items-center justify-between" style="border-bottom: 1px solid var(--theme-100);">
          <span class="text-[13px] font-semibold tracking-wide uppercase" style="color: var(--theme-700);">通知</span>
          <button
            v-if="unreadCount > 0"
            @click="markRead('all')"
            class="text-[12px] cursor-pointer hover:underline"
            style="color: var(--theme-500);"
          >全部已读</button>
        </div>

        <div class="flex-1 overflow-y-auto" style="scrollbar-width: thin;">
          <div v-if="loading && list.length === 0" class="px-4 py-8 text-center text-[12px]" style="color: var(--theme-400);">
            加载中…
          </div>
          <div v-else-if="error" class="px-4 py-8 text-center text-[12px]" style="color: #b42318;">
            {{ error }}
          </div>
          <div v-else-if="list.length === 0" class="px-4 py-12 text-center text-[12px]" style="color: var(--theme-400);">
            暂无通知
          </div>
          <div v-else>
            <div
              v-for="n in list"
              :key="n.id"
              @click="handleNotificationClick(n)"
              class="px-4 py-2.5 cursor-pointer transition-colors"
              :class="n.is_read ? '' : 'notif-unread'"
              :style="n.is_read ? 'border-bottom: 1px solid var(--theme-100);' : 'background: rgba(61, 124, 201, 0.06); border-bottom: 1px solid var(--theme-100);'"
            >
              <div class="flex items-center gap-1.5 mb-0.5">
                <span class="text-[10px] font-medium px-1.5 py-0.5 rounded" style="background: var(--theme-100); color: var(--theme-600);">
                  {{ sourceLabel(n.source) }}
                </span>
                <span v-if="n.title" class="text-[13px] font-semibold truncate" :style="n.is_read ? 'color: var(--theme-600);' : 'color: var(--theme-700);'">
                  {{ n.title }}
                </span>
                <span class="ml-auto text-[11px] shrink-0" style="color: var(--theme-400);">
                  {{ formatTime(n.created_at) }}
                </span>
              </div>
              <div class="text-[13px] leading-relaxed whitespace-pre-wrap break-words" :style="n.is_read ? 'color: var(--theme-500);' : 'color: var(--theme-700);'">
                {{ n.content }}
              </div>
            </div>
          </div>
        </div>
      </div>
    </Transition>
  </div>
</template>

<style scoped>
.panel-enter-active, .panel-leave-active { transition: opacity 0.15s ease, transform 0.15s ease; }
.panel-enter-from, .panel-leave-to { opacity: 0; transform: translateY(-4px); }
.panel-enter-to, .panel-leave-from { opacity: 1; transform: translateY(0); }

.notif-unread:hover { background: rgba(61, 124, 201, 0.10) !important; }

div::-webkit-scrollbar { width: 4px; }
div::-webkit-scrollbar-track { background: transparent; }
div::-webkit-scrollbar-thumb { background: rgba(15, 23, 42, 0.18); border-radius: 2px; }
</style>
