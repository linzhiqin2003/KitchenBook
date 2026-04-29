<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import API_BASE_URL, { HERMES_API_URL, HERMES_API_KEY } from '../../config/api'
import { useAuthStore } from '../../store/auth'

const authStore = useAuthStore()

const props = defineProps({
  visible: { type: Boolean, default: false }
})

const emit = defineEmits(['close'])

const activeTab = ref('tools')
const tools = ref([])
const skills = ref([])
const memory = ref('')
const userProfile = ref('')
const loadingTools = ref(false)
const loadingSkills = ref(false)
const loadingMemory = ref(false)
const editingMemory = ref(false)
const memoryDraft = ref('')
const memoryError = ref('')
const MIN_PANEL_WIDTH = 280
const MAX_PANEL_WIDTH = 560
const DEFAULT_PANEL_WIDTH = 320
const panelWidth = ref(DEFAULT_PANEL_WIDTH)
const isResizing = ref(false)

// 把当前登录用户的 id 透传给 Hermes，让服务端 scope memory / config 路径
const headers = computed(() => {
  const uid = authStore.user?.id
  const h = {
    'Authorization': `Bearer ${HERMES_API_KEY}`,
    'Content-Type': 'application/json',
  }
  if (uid) {
    h['X-Hermes-User-Id'] = String(uid)
    h['X-Hermes-Session-Id'] = `ailab-user-${uid}`
  }
  return h
})

const clampPanelWidth = (width) => Math.min(MAX_PANEL_WIDTH, Math.max(MIN_PANEL_WIDTH, width))

const handleResizeMove = (event) => {
  if (!isResizing.value) return
  panelWidth.value = clampPanelWidth(window.innerWidth - event.clientX)
}

const stopResize = () => {
  if (!isResizing.value) return
  isResizing.value = false
  document.body.style.userSelect = ''
  window.removeEventListener('pointermove', handleResizeMove)
  window.removeEventListener('pointerup', stopResize)
}

const startResize = (event) => {
  event.preventDefault()
  isResizing.value = true
  document.body.style.userSelect = 'none'
  window.addEventListener('pointermove', handleResizeMove)
  window.addEventListener('pointerup', stopResize)
}

const responseErrorMessage = (data, fallback) => {
  if (typeof data?.error === 'string') return data.error
  if (typeof data?.error?.message === 'string') return data.error.message
  if (typeof data?.detail === 'string') return data.detail
  return fallback
}

const fetchTools = async () => {
  loadingTools.value = true
  try {
    const r = await fetch(`${HERMES_API_URL}/api/tools`, { headers: headers.value })
    if (r.ok) {
      const data = await r.json()
      tools.value = data.tools || []
    }
  } catch (e) { console.error('Failed to fetch tools:', e) }
  finally { loadingTools.value = false }
}

const toggleTool = async (tool) => {
  try {
    await fetch(`${HERMES_API_URL}/api/tools/toggle`, {
      method: 'POST', headers: headers.value,
      body: JSON.stringify({ name: tool.name, enable: !tool.enabled })
    })
    tool.enabled = !tool.enabled
  } catch (e) { console.error('Failed to toggle tool:', e) }
}

const fetchSkills = async () => {
  loadingSkills.value = true
  try {
    const r = await fetch(`${HERMES_API_URL}/api/skills`, { headers: headers.value })
    if (r.ok) {
      const data = await r.json()
      skills.value = data.skills || []
    }
  } catch (e) { console.error('Failed to fetch skills:', e) }
  finally { loadingSkills.value = false }
}

const toggleSkill = async (skill) => {
  const next = !skill.enabled
  try {
    const r = await fetch(`${HERMES_API_URL}/api/skills/toggle`, {
      method: 'POST', headers: headers.value,
      body: JSON.stringify({ name: skill.name, enable: next })
    })
    if (!r.ok) throw new Error(`toggle failed (${r.status})`)
    skill.enabled = next
  } catch (e) { console.error('Failed to toggle skill:', e) }
}

const fetchMemory = async () => {
  loadingMemory.value = true
  memoryError.value = ''
  try {
    const r = await fetch(`${HERMES_API_URL}/api/memory`, { headers: headers.value })
    const data = await r.json().catch(() => ({}))
    if (!r.ok) {
      throw new Error(responseErrorMessage(data, `Memory 接口请求失败 (${r.status})`))
    }
    memory.value = data.memory || ''
    userProfile.value = data.user_profile || ''
    return true
  } catch (e) {
    console.error('Failed to fetch memory:', e)
    memoryError.value = e.message || '无法读取 Memory，请检查 Hermes /api/memory 接口和服务状态。'
  } finally { loadingMemory.value = false }
  return false
}

const startEditMemory = () => {
  memoryDraft.value = memory.value
  editingMemory.value = true
}

const saveMemory = async () => {
  memoryError.value = ''
  try {
    const r = await fetch(`${HERMES_API_URL}/api/memory`, {
      method: 'POST', headers: headers.value,
      body: JSON.stringify({ memory: memoryDraft.value })
    })
    const data = await r.json().catch(() => ({}))
    if (!r.ok) {
      throw new Error(responseErrorMessage(data, `Memory 保存失败 (${r.status})`))
    }
    memory.value = memoryDraft.value
    editingMemory.value = false
  } catch (e) {
    console.error('Failed to save memory:', e)
    memoryError.value = e.message || 'Memory 保存失败'
  }
}

const skillsByCategory = computed(() => {
  const groups = {}
  for (const s of skills.value) {
    const cat = s.category || ''
    if (!groups[cat]) groups[cat] = []
    groups[cat].push(s)
  }
  return groups
})

// === 通知 (从 Django 拉，用 JWT) ===
const notifications = ref([])
const notificationsLoading = ref(false)
const notificationsError = ref('')
const notificationsUnread = ref(0)

const djangoHeaders = () => {
  const t = localStorage.getItem('access_token') || ''
  const h = { 'Content-Type': 'application/json' }
  if (t) h['Authorization'] = `Bearer ${t}`
  return h
}

const fetchNotifications = async () => {
  notificationsLoading.value = true
  notificationsError.value = ''
  try {
    const r = await fetch(`${API_BASE_URL}/api/ai/notifications/?limit=100`, { headers: djangoHeaders() })
    if (!r.ok) throw new Error(`HTTP ${r.status}`)
    const data = await r.json()
    notifications.value = data.results || []
    notificationsUnread.value = Number(data.unread_count) || 0
  } catch (e) {
    notificationsError.value = e.message
  } finally {
    notificationsLoading.value = false
  }
}

// 单独的轻量轮询：只拿未读数，用于铃铛 badge
const pollNotificationsUnread = async () => {
  try {
    const r = await fetch(`${API_BASE_URL}/api/ai/notifications/?unread=1&limit=1`, { headers: djangoHeaders() })
    if (!r.ok) return
    const data = await r.json()
    notificationsUnread.value = Number(data.unread_count) || 0
  } catch { /* silent */ }
}

const markNotificationRead = async (ids) => {
  try {
    const body = ids === 'all' ? { all: true } : { ids: Array.isArray(ids) ? ids : [ids] }
    await fetch(`${API_BASE_URL}/api/ai/notifications/mark-read/`, {
      method: 'POST', headers: djangoHeaders(), body: JSON.stringify(body)
    })
    if (ids === 'all') {
      notifications.value.forEach(n => n.is_read = true)
      notificationsUnread.value = 0
    } else {
      const set = new Set(Array.isArray(ids) ? ids : [ids])
      notifications.value.forEach(n => { if (set.has(n.id)) n.is_read = true })
      notificationsUnread.value = notifications.value.filter(n => !n.is_read).length
    }
  } catch { /* silent */ }
}

const handleNotifClick = (n) => {
  if (!n.is_read) markNotificationRead(n.id)
}

const formatNotifTime = (iso) => {
  if (!iso) return ''
  const d = new Date(iso)
  const min = Math.floor((Date.now() - d) / 60000)
  if (min < 1) return '刚刚'
  if (min < 60) return `${min} 分钟前`
  const hr = Math.floor(min / 60)
  if (hr < 24) return `${hr} 小时前`
  const day = Math.floor(hr / 24)
  if (day < 7) return `${day} 天前`
  return d.toLocaleDateString('zh-CN')
}

const sourceLabel = (s) => ({
  cron: 'Cron', hook: 'Hook', manual: '手动', agent: 'Agent',
}[s] || s)

const loadTab = (tab) => {
  activeTab.value = tab
  if (tab === 'tools' && tools.value.length === 0) fetchTools()
  if (tab === 'skills' && skills.value.length === 0) fetchSkills()
  if (tab === 'memory') fetchMemory()
  if (tab === 'notifications') fetchNotifications()
}

watch(
  () => props.visible,
  (visible) => {
    if (visible) loadTab(activeTab.value)
  }
)

// 通知未读数轮询：30s 一次，独立于 panel 是否打开
let notifPollHandle = null
onMounted(() => {
  if (props.visible) loadTab(activeTab.value)
  pollNotificationsUnread()
  notifPollHandle = setInterval(pollNotificationsUnread, 30000)
})

onUnmounted(() => {
  stopResize()
  if (notifPollHandle) clearInterval(notifPollHandle)
})

// 暴露给父组件：让铃铛能切到通知 tab、读取未读数
const openNotifications = () => {
  loadTab('notifications')
}

defineExpose({
  refreshMemory: fetchMemory,
  openNotifications,
  notificationsUnread,
})
</script>

<template>
  <Transition name="slide">
    <div
      v-if="visible"
      class="panel-shell flex flex-col"
      :class="{ resizing: isResizing }"
      :style="{ width: `${panelWidth}px`, minWidth: `${panelWidth}px` }"
    >
      <div
        class="resize-handle"
        role="separator"
        aria-orientation="vertical"
        :aria-valuemin="MIN_PANEL_WIDTH"
        :aria-valuemax="MAX_PANEL_WIDTH"
        :aria-valuenow="panelWidth"
        title="拖动调整宽度"
        @pointerdown="startResize"
      ></div>
      <!-- Header -->
      <div class="flex items-center justify-between px-4 pt-3 pb-2">
        <span class="text-[14px] font-semibold" style="color: #2c2c30;">Agent Panel</span>
        <button @click="emit('close')" class="p-1 rounded-md cursor-pointer hover:bg-black/[0.04]" style="color: #9a9aa0;">
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="1.5">
            <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12"/>
          </svg>
        </button>
      </div>

      <!-- Tabs -->
      <div class="flex px-3 pb-2 gap-1">
        <button v-for="tab in ['tools', 'skills', 'memory', 'notifications']" :key="tab"
          @click="loadTab(tab)"
          class="px-3 py-1 rounded-md text-[13px] font-medium transition-colors cursor-pointer relative"
          :style="activeTab === tab ? 'background: #fff; color: #2c2c30; box-shadow: 0 1px 2px rgba(0,0,0,0.05);' : 'color: #9a9aa0;'">
          {{ tab === 'tools' ? 'Tools' : tab === 'skills' ? 'Skills' : tab === 'memory' ? 'Memory' : 'Inbox' }}
          <span
            v-if="tab === 'notifications' && notificationsUnread > 0"
            class="absolute -top-0.5 -right-0.5 min-w-[14px] h-[14px] rounded-full text-[9px] font-semibold flex items-center justify-center px-1"
            style="background: #ef4444; color: #fff;"
          >{{ notificationsUnread > 99 ? '99+' : notificationsUnread }}</span>
        </button>
      </div>

      <!-- Content -->
      <div class="flex-1 overflow-y-auto px-3 pb-4">

        <!-- Tools Tab -->
        <template v-if="activeTab === 'tools'">
          <div v-if="loadingTools" class="text-center py-8" style="color: #b0b0b6; font-size: 13px;">加载中…</div>
          <template v-else>
            <div class="space-y-0.5">
              <template v-for="tool in tools.filter(t => t.type === 'builtin')" :key="tool.name">
                <div class="flex items-center justify-between px-3 py-2 rounded-lg hover:bg-white/60 transition-colors">
                  <div class="flex items-center gap-2 flex-1 min-w-0">
                    <span class="w-1.5 h-1.5 rounded-full shrink-0" :style="tool.enabled ? 'background: #2c2c30;' : 'background: #d1d1d6;'"></span>
                    <span class="text-[14px] truncate" :style="tool.enabled ? 'color: #2c2c30;' : 'color: #b0b0b6;'">{{ tool.name }}</span>
                  </div>
                  <button @click="toggleTool(tool)" class="shrink-0 ml-2 cursor-pointer px-2 py-0.5 rounded text-[12px] transition-colors"
                    :style="tool.enabled ? 'color: #2c2c30;' : 'color: #b0b0b6;'">
                    {{ tool.enabled ? 'on' : 'off' }}
                  </button>
                </div>
              </template>
            </div>
            <!-- MCP section -->
            <div v-if="tools.some(t => t.type === 'mcp')" class="mt-4">
              <div class="px-3 pb-1.5" style="font-size: 11px; font-weight: 600; color: #9a9aa0; letter-spacing: 0.03em;">MCP Servers</div>
              <div v-for="tool in tools.filter(t => t.type === 'mcp')" :key="'mcp-' + tool.name"
                class="flex items-center gap-2 px-3 py-2 rounded-lg hover:bg-white/60 transition-colors">
                <span class="w-1.5 h-1.5 rounded-full shrink-0" style="background: var(--ai-accent);"></span>
                <span class="text-[14px]" style="color: #2c2c30;">{{ tool.name }}</span>
              </div>
            </div>
          </template>
        </template>

        <!-- Skills Tab -->
        <template v-if="activeTab === 'skills'">
          <div v-if="loadingSkills" class="text-center py-8" style="color: #b0b0b6; font-size: 13px;">加载中…</div>
          <div v-else-if="skills.length === 0" class="text-center py-8" style="color: #b0b0b6; font-size: 13px;">暂无已安装的技能</div>
          <template v-else>
            <div v-for="(group, category) in skillsByCategory" :key="category" class="mb-3">
              <div v-if="category" class="px-3 pb-1 pt-2" style="font-size: 11px; font-weight: 600; color: #9a9aa0; letter-spacing: 0.03em;">{{ category || 'Other' }}</div>
              <div class="space-y-0.5">
                <div v-for="skill in group" :key="skill.name"
                  class="flex items-center justify-between px-3 py-1.5 rounded-lg hover:bg-white/60 transition-colors">
                  <span class="text-[14px] truncate" :style="skill.enabled ? 'color: #2c2c30;' : 'color: #b0b0b6;'">{{ skill.name }}</span>
                  <button @click="toggleSkill(skill)"
                    class="shrink-0 ml-2 cursor-pointer px-2 py-0.5 rounded text-[12px] transition-colors"
                    :style="skill.enabled ? 'color: #2c2c30;' : 'color: #b0b0b6;'">
                    {{ skill.enabled ? 'on' : 'off' }}
                  </button>
                </div>
              </div>
            </div>
          </template>
        </template>

        <!-- Memory Tab -->
        <template v-if="activeTab === 'memory'">
          <div v-if="loadingMemory" class="text-center py-8" style="color: #9a9aa0; font-size: 13px;">加载中…</div>
          <template v-else>
            <div v-if="memoryError" class="mb-3 rounded-lg px-3 py-2 text-[13px]" style="background: #fff4f4; color: #b42318; border: 1px solid #ffd7d7;">
              {{ memoryError }}
            </div>

            <!-- MEMORY.md -->
            <div class="mb-4">
              <div class="flex items-center justify-between mb-2">
                <span class="text-[13px] font-semibold" style="color: #6e6e76;">MEMORY.md</span>
                <button v-if="!editingMemory" @click="startEditMemory"
                  class="text-[12px] px-2 py-0.5 rounded-md cursor-pointer transition-colors"
                  style="color: var(--ai-accent); border: 1px solid var(--ai-accent-soft);">编辑</button>
                <div v-else class="flex gap-1">
                  <button @click="saveMemory" class="text-[12px] px-2 py-0.5 rounded-md cursor-pointer" style="background: var(--theme-700); color: #fff;">保存</button>
                  <button @click="editingMemory = false" class="text-[12px] px-2 py-0.5 rounded-md cursor-pointer" style="color: #9a9aa0;">取消</button>
                </div>
              </div>
              <textarea v-if="editingMemory" v-model="memoryDraft"
                class="w-full rounded-lg p-3 outline-none resize-none"
                style="background: #fff; border: 1px solid var(--ai-accent); color: #2c2c30; font-size: 12px; line-height: 1.6; min-height: 200px; font-family: var(--ai-font-mono);"></textarea>
              <pre v-else class="rounded-lg p-3 whitespace-pre-wrap break-words"
                style="background: #fff; color: #2c2c30; font-size: 12px; line-height: 1.6; min-height: 60px; font-family: var(--ai-font-mono);">{{ memory || '(空)' }}</pre>
            </div>

            <!-- USER.md -->
            <div>
              <div class="flex items-center mb-2">
                <span class="text-[13px] font-semibold" style="color: #6e6e76;">USER.md</span>
                <span class="text-[11px] ml-2" style="color: #b0b0b6;">agent 自动维护</span>
              </div>
              <pre class="rounded-lg p-3 whitespace-pre-wrap break-words"
                style="background: #fff; color: #2c2c30; font-size: 12px; line-height: 1.6; min-height: 60px; font-family: var(--ai-font-mono);">{{ userProfile || '(空)' }}</pre>
            </div>
          </template>
        </template>

        <!-- Notifications Tab -->
        <template v-if="activeTab === 'notifications'">
          <div class="flex items-center justify-between mb-2 px-1">
            <span class="text-[13px]" style="color: #6e6e76;">
              {{ notifications.length === 0 ? '暂无通知' : `共 ${notifications.length} 条` }}
            </span>
            <button
              v-if="notificationsUnread > 0"
              @click="markNotificationRead('all')"
              class="text-[12px] cursor-pointer hover:underline"
              style="color: var(--theme-500);"
            >全部已读</button>
          </div>
          <div v-if="notificationsLoading && notifications.length === 0" class="text-center py-8 text-[12px]" style="color: #b0b0b6;">加载中…</div>
          <div v-else-if="notificationsError" class="text-center py-8 text-[12px]" style="color: #b91c1c;">{{ notificationsError }}</div>
          <div v-else-if="notifications.length === 0" class="text-center py-12 text-[12px]" style="color: #b0b0b6;">收件箱是空的</div>
          <div v-else class="space-y-2">
            <div
              v-for="n in notifications"
              :key="n.id"
              @click="handleNotifClick(n)"
              class="rounded-lg px-3 py-2.5 cursor-pointer transition-colors"
              :style="n.is_read
                ? 'background: #fff; border: 1px solid var(--theme-200);'
                : 'background: rgba(61, 124, 201, 0.06); border: 1px solid rgba(61, 124, 201, 0.25);'"
            >
              <div class="flex items-center gap-1.5 mb-1">
                <span class="text-[10px] font-medium px-1.5 py-0.5 rounded" style="background: var(--theme-100); color: var(--theme-600);">
                  {{ sourceLabel(n.source) }}
                </span>
                <span v-if="n.title" class="text-[13px] font-semibold truncate" :style="n.is_read ? 'color: var(--theme-600);' : 'color: var(--theme-700);'">
                  {{ n.title }}
                </span>
                <span class="ml-auto text-[11px] shrink-0" style="color: var(--theme-400);">
                  {{ formatNotifTime(n.created_at) }}
                </span>
              </div>
              <div
                class="text-[13px] leading-relaxed whitespace-pre-wrap break-words"
                :style="n.is_read ? 'color: var(--theme-500);' : 'color: var(--theme-700);'"
              >{{ n.content }}</div>
            </div>
          </div>
        </template>
      </div>
    </div>
  </Transition>
</template>

<style scoped>
.panel-shell {
  position: relative;
  height: 100dvh;
  background: #f7f7f8;
  border-left: 1px solid #ebebed;
  font-family: var(--ai-font-body);
}
.resize-handle {
  position: absolute;
  top: 0;
  left: -4px;
  width: 8px;
  height: 100%;
  cursor: col-resize;
  touch-action: none;
  z-index: 2;
}
.resize-handle::after {
  content: '';
  position: absolute;
  top: 0;
  left: 3px;
  width: 1px;
  height: 100%;
  background: transparent;
  transition: background 0.15s ease;
}
.resize-handle:hover::after,
.resizing .resize-handle::after {
  background: var(--ai-accent);
}
.slide-enter-active, .slide-leave-active {
  transition: all 0.25s ease;
}
.slide-enter-from, .slide-leave-to {
  transform: translateX(100%);
  opacity: 0;
}
</style>
