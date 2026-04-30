<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { HERMES_API_URL, HERMES_API_KEY } from '../../config/api'
import { useAuthStore } from '../../store/auth'
import api from '../../api/client'

const authStore = useAuthStore()

const props = defineProps({
  visible: { type: Boolean, default: false }
})

const emit = defineEmits(['close'])

const activeTab = ref('tools')
const tabs = ['tools', 'skills', 'memory', 'files', 'notifications']
const tools = ref([])
const skills = ref([])
const selectedSkillName = ref('')
const selectedSkillMeta = ref(null)
const skillBrowserEntries = ref([])
const skillBrowserBreadcrumbs = ref([])
const skillBrowserCurrentPath = ref('')
const skillBrowserSelectedPath = ref('')
const memoryEntries = ref([])
const memoryBreadcrumbs = ref([])
const memoryCurrentPath = ref('memories')
const memorySelectedPath = ref('')
const workspaceRoots = ref([])
const workspaceActiveRoot = ref('')
const workspaceRootLabel = ref('')
const workspaceRootDisplay = ref('')
const workspaceCurrentPath = ref('')
const workspaceCurrentDisplay = ref('')
const workspaceEntries = ref([])
const workspaceBreadcrumbs = ref([])
const workspaceEntryCount = ref(0)
const workspaceTruncated = ref(false)
const workspaceListLimit = ref(0)
const workspaceSelectedPath = ref('')
const workspacePreview = ref(null)
const workspacePreviewOpen = ref(false)
const skillBrowserOpen = ref(false)
const loadingTools = ref(false)
const loadingSkills = ref(false)
const loadingSkillBrowser = ref(false)
const loadingMemory = ref(false)
const loadingWorkspace = ref(false)
const loadingWorkspacePreview = ref(false)
const memoryError = ref('')
const skillBrowserError = ref('')
const workspaceError = ref('')
const workspacePreviewError = ref('')
const MIN_PANEL_WIDTH = 280
const MAX_PANEL_WIDTH = 560
const DEFAULT_PANEL_WIDTH = 360
const panelWidth = ref(DEFAULT_PANEL_WIDTH)
const isResizing = ref(false)

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
      if (skills.value.length === 0) {
        selectedSkillName.value = ''
        selectedSkillMeta.value = null
        skillBrowserEntries.value = []
        skillBrowserBreadcrumbs.value = []
        skillBrowserCurrentPath.value = ''
        skillBrowserSelectedPath.value = ''
      } else {
        const nextSkill = skills.value.find(item => item.name === selectedSkillName.value) || skills.value[0]
        await fetchSkillBrowser({ skillName: nextSkill.name, path: nextSkill.name === selectedSkillName.value ? skillBrowserCurrentPath.value : '' })
      }
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

const fetchSkillBrowser = async ({ skillName = selectedSkillName.value || '', path = '' } = {}) => {
  if (!skillName) return
  loadingSkillBrowser.value = true
  skillBrowserError.value = ''
  try {
    const { data } = await api.get('/ai/skills/browser/', {
      params: { skill: skillName, path }
    })
    selectedSkillName.value = data.skill || skillName
    selectedSkillMeta.value = {
      name: data.skill || skillName,
      category: data.category || '',
      description: data.description || '',
      rootDisplay: data.root_display || '',
    }
    skillBrowserCurrentPath.value = data.current_path || path || ''
    skillBrowserBreadcrumbs.value = Array.isArray(data.breadcrumbs) ? data.breadcrumbs : []
    skillBrowserEntries.value = Array.isArray(data.entries) ? data.entries : []
    skillBrowserSelectedPath.value = ''
  } catch (e) {
    console.error('Failed to fetch skill browser:', e)
    skillBrowserError.value = e?.response?.data?.error || e?.message || '无法读取 skill 目录'
  } finally {
    loadingSkillBrowser.value = false
  }
}

const fetchMemory = async ({ path = memoryCurrentPath.value || 'memories' } = {}) => {
  loadingMemory.value = true
  memoryError.value = ''
  try {
    const { data } = await api.get('/ai/workspace/', {
      params: { root: 'user', path }
    })
    memoryCurrentPath.value = data.current_path || path
    memoryBreadcrumbs.value = Array.isArray(data.breadcrumbs) ? data.breadcrumbs : []
    memoryEntries.value = Array.isArray(data.entries) ? data.entries : []
  } catch (e) {
    console.error('Failed to fetch memory directory:', e)
    memoryError.value = e?.response?.data?.error || e?.message || '无法读取 memories 目录'
  } finally { loadingMemory.value = false }
}

const previewSkillEntry = async (entry) => {
  workspacePreviewError.value = ''
  loadingWorkspacePreview.value = true
  try {
    const { data } = await api.get('/ai/skills/preview/', {
      params: {
        skill: selectedSkillName.value,
        path: entry.path,
      }
    })
    if (data.preview_type === 'image' || data.preview_type === 'pdf') {
      data.data_url = `data:${data.mime_type};base64,${data.content_base64}`
    }
    workspacePreview.value = data
    workspacePreviewOpen.value = true
  } catch (e) {
    workspacePreviewError.value = e?.response?.data?.error || e?.message || '预览失败'
  } finally {
    loadingWorkspacePreview.value = false
  }
}

const clearWorkspacePreview = () => {
  workspacePreview.value = null
  workspacePreviewOpen.value = false
  workspacePreviewError.value = ''
  loadingWorkspacePreview.value = false
}

const fetchWorkspace = async ({ root = workspaceActiveRoot.value || '', path = workspaceCurrentPath.value || '' } = {}) => {
  loadingWorkspace.value = true
  workspaceError.value = ''
  try {
    const { data } = await api.get('/ai/workspace/', {
      params: { root, path }
    })
    workspaceRoots.value = Array.isArray(data.roots) ? data.roots : []
    workspaceActiveRoot.value = data.active_root || workspaceRoots.value[0]?.key || ''
    workspaceRootLabel.value = data.active_root_label || workspaceRoots.value.find(item => item.key === workspaceActiveRoot.value)?.label || ''
    workspaceRootDisplay.value = data.root_display || ''
    workspaceCurrentPath.value = data.current_path || ''
    workspaceCurrentDisplay.value = data.current_display || ''
    workspaceBreadcrumbs.value = Array.isArray(data.breadcrumbs) ? data.breadcrumbs : []
    workspaceEntries.value = Array.isArray(data.entries) ? data.entries : []
    workspaceEntryCount.value = Number(data.entry_count) || workspaceEntries.value.length
    workspaceTruncated.value = Boolean(data.truncated)
    workspaceListLimit.value = Number(data.list_limit) || 0
  } catch (e) {
    workspaceError.value = e?.response?.data?.error || e?.message || '加载失败'
  } finally {
    loadingWorkspace.value = false
  }
}

const openWorkspaceRoot = async (rootKey) => {
  if (!rootKey) return
  if (rootKey === workspaceActiveRoot.value && !workspaceCurrentPath.value) return
  workspaceActiveRoot.value = rootKey
  workspaceCurrentPath.value = ''
  workspaceSelectedPath.value = ''
  clearWorkspacePreview()
  await fetchWorkspace({ root: rootKey, path: '' })
}

const openWorkspaceBreadcrumb = async (path) => {
  workspaceCurrentPath.value = path || ''
  workspaceSelectedPath.value = ''
  clearWorkspacePreview()
  await fetchWorkspace({ root: workspaceActiveRoot.value, path: workspaceCurrentPath.value })
}

const previewWorkspaceEntry = async (entry) => {
  workspacePreviewError.value = ''
  loadingWorkspacePreview.value = true
  try {
    const { data } = await api.get('/ai/workspace/preview/', {
      params: {
        root: entry.root || workspaceActiveRoot.value,
        path: entry.path,
      }
    })
    if (data.preview_type === 'image' || data.preview_type === 'pdf') {
      data.data_url = `data:${data.mime_type};base64,${data.content_base64}`
    }
    workspacePreview.value = data
    workspacePreviewOpen.value = true
  } catch (e) {
    workspacePreviewError.value = e?.response?.data?.error || e?.message || '预览失败'
  } finally {
    loadingWorkspacePreview.value = false
  }
}

const selectWorkspaceEntry = (entry) => {
  workspaceSelectedPath.value = entry.path
}

const openWorkspaceEntry = async (entry) => {
  if (entry.type === 'dir') {
    workspaceCurrentPath.value = entry.path
    workspaceSelectedPath.value = ''
    clearWorkspacePreview()
    await fetchWorkspace({ root: workspaceActiveRoot.value, path: entry.path })
    return
  }
  await previewWorkspaceEntry(entry)
}

const closeWorkspacePreview = () => {
  workspacePreviewOpen.value = false
}

const isCurrentTabLoading = computed(() => {
  if (activeTab.value === 'tools') return loadingTools.value
  if (activeTab.value === 'skills') return loadingSkills.value
  if (activeTab.value === 'memory') return loadingMemory.value
  if (activeTab.value === 'files') return loadingWorkspace.value
  return false
})

const skillsByCategory = computed(() => {
  const groups = {}
  for (const s of skills.value) {
    const cat = s.category || ''
    if (!groups[cat]) groups[cat] = []
    groups[cat].push(s)
  }
  return groups
})

const visibleMemoryEntries = computed(() => (
  memoryEntries.value.filter(entry => !entry.name.endsWith('.lock'))
))

const skillBrowserCanGoUp = computed(() => skillBrowserBreadcrumbs.value.length > 1)

const skillBrowserParentPath = computed(() => {
  if (skillBrowserBreadcrumbs.value.length <= 1) return ''
  return skillBrowserBreadcrumbs.value[skillBrowserBreadcrumbs.value.length - 2]?.path || ''
})

const notifications = ref([])
const notificationsLoading = ref(false)
const notificationsError = ref('')
const notificationsUnread = ref(0)

const fetchNotifications = async () => {
  notificationsLoading.value = true
  notificationsError.value = ''
  try {
    const { data } = await api.get('/ai/notifications/', { params: { limit: 100 } })
    notifications.value = data.results || []
    notificationsUnread.value = Number(data.unread_count) || 0
  } catch (e) {
    notificationsError.value = e?.response ? `HTTP ${e.response.status}` : (e.message || '加载失败')
  } finally {
    notificationsLoading.value = false
  }
}

const pollNotificationsUnread = async () => {
  try {
    const { data } = await api.get('/ai/notifications/', { params: { unread: 1, limit: 1 } })
    notificationsUnread.value = Number(data.unread_count) || 0
  } catch { /* silent */ }
}

const markNotificationRead = async (ids) => {
  try {
    const body = ids === 'all' ? { all: true } : { ids: Array.isArray(ids) ? ids : [ids] }
    await api.post('/ai/notifications/mark-read/', body)
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

const deleteNotification = async (id) => {
  try {
    await api.delete(`/ai/notifications/${id}/`)
    notifications.value = notifications.value.filter(n => n.id !== id)
    notificationsUnread.value = notifications.value.filter(n => !n.is_read).length
  } catch { /* silent */ }
}

const clearAllNotifications = async () => {
  if (!confirm('清空所有通知？此操作不可撤销。')) return
  try {
    await api.post('/ai/notifications/clear-all/')
    notifications.value = []
    notificationsUnread.value = 0
  } catch { /* silent */ }
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
  if (tab === 'tools') fetchTools()
  if (tab === 'skills') fetchSkills()
  if (tab === 'memory') fetchMemory()
  if (tab === 'files') fetchWorkspace()
  if (tab === 'notifications') fetchNotifications()
}

watch(
  () => props.visible,
  (visible) => {
    if (visible) loadTab(activeTab.value)
  }
)

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

const handleKeydown = (event) => {
  if (event.key !== 'Escape') return
  // 文件预览叠在 skill 浏览器之上，先关上层
  if (workspacePreviewOpen.value) {
    closeWorkspacePreview()
    return
  }
  if (skillBrowserOpen.value) {
    closeSkillBrowser()
  }
}

onMounted(() => {
  window.addEventListener('keydown', handleKeydown)
})

onUnmounted(() => {
  window.removeEventListener('keydown', handleKeydown)
})

const openNotifications = () => {
  loadTab('notifications')
}

const formatWorkspaceSize = (size) => {
  const value = Number(size) || 0
  if (value < 1024) return `${value} B`
  if (value < 1024 * 1024) return `${(value / 1024).toFixed(1)} KB`
  return `${(value / (1024 * 1024)).toFixed(1)} MB`
}

const formatWorkspaceTime = (iso) => {
  if (!iso) return ''
  const date = new Date(iso)
  if (Number.isNaN(date.getTime())) return ''
  return date.toLocaleString('zh-CN', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  })
}

const workspaceCanGoUp = computed(() => workspaceBreadcrumbs.value.length > 1)
const memoryCanGoUp = computed(() => memoryBreadcrumbs.value.length > 1)

const workspaceParentPath = computed(() => {
  if (workspaceBreadcrumbs.value.length <= 1) return ''
  return workspaceBreadcrumbs.value[workspaceBreadcrumbs.value.length - 2]?.path || ''
})

const memoryParentPath = computed(() => {
  if (memoryBreadcrumbs.value.length <= 1) return 'memories'
  return memoryBreadcrumbs.value[memoryBreadcrumbs.value.length - 2]?.path || 'memories'
})

const workspacePreviewMeta = computed(() => {
  if (!workspacePreview.value) return ''
  return [
    workspacePreview.value.mime_type,
    formatWorkspaceSize(workspacePreview.value.size),
  ].filter(Boolean).join(' · ')
})

const workspaceRootHint = computed(() => (
  workspaceCurrentDisplay.value || workspaceRootDisplay.value || '~/.hermes/users/<uid>'
))

const memoryBreadcrumbItems = computed(() => (
  memoryBreadcrumbs.value.map((crumb, index) => ({
    ...crumb,
    name: index === 0 ? 'Memory' : crumb.name,
  }))
))

const skillsByCategoryWithSelected = computed(() => {
  const groups = {}
  for (const skill of skills.value) {
    const cat = skill.category || ''
    if (!groups[cat]) groups[cat] = []
    groups[cat].push({
      ...skill,
      isSelected: skill.name === selectedSkillName.value,
    })
  }
  return groups
})

const openMemoryBreadcrumb = async (path) => {
  memoryCurrentPath.value = path || 'memories'
  memorySelectedPath.value = ''
  await fetchMemory({ path: memoryCurrentPath.value })
}

const selectMemoryEntry = (entry) => {
  memorySelectedPath.value = entry.path
}

const openMemoryEntry = async (entry) => {
  // Memory tab 锁在 memories/ 根目录：dir 不进入，仅文件能预览
  if (entry.type === 'dir') return
  await previewWorkspaceEntry({ ...entry, root: 'user' })
}

const openSkillBrowserBreadcrumb = async (path) => {
  skillBrowserCurrentPath.value = path || ''
  skillBrowserSelectedPath.value = ''
  await fetchSkillBrowser({ skillName: selectedSkillName.value, path: skillBrowserCurrentPath.value })
}

// 单击只高亮（不发请求、不展开任何浏览器）。
const selectSkill = (skill) => {
  if (!skill?.name) return
  selectedSkillName.value = skill.name
}

// 双击：弹浮窗，展示该 skill 的文件浏览器；切换 skill 时重置路径。
const openSkillBrowser = async (skill) => {
  if (!skill?.name) return
  if (selectedSkillName.value !== skill.name) {
    skillBrowserCurrentPath.value = ''
    skillBrowserSelectedPath.value = ''
  }
  selectedSkillName.value = skill.name
  skillBrowserOpen.value = true
  await fetchSkillBrowser({ skillName: skill.name, path: skillBrowserCurrentPath.value || '' })
}

const closeSkillBrowser = () => {
  skillBrowserOpen.value = false
}

const selectSkillBrowserEntry = (entry) => {
  skillBrowserSelectedPath.value = entry.path
}

const openSkillBrowserEntry = async (entry) => {
  if (entry.type === 'dir') {
    skillBrowserCurrentPath.value = entry.path
    skillBrowserSelectedPath.value = ''
    await fetchSkillBrowser({ skillName: selectedSkillName.value, path: entry.path })
    return
  }
  await previewSkillEntry(entry)
}

defineExpose({
  refreshMemory: fetchMemory,
  openNotifications,
  notificationsUnread,
  openTab: loadTab,
  activeTab,
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

      <div class="flex items-center justify-between px-4 pt-3 pb-2">
        <span class="text-[14px] font-semibold" style="color: #2c2c30;">Agent Panel</span>
        <button @click="emit('close')" class="p-1 rounded-md cursor-pointer hover:bg-black/[0.04]" style="color: #9a9aa0;">
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="1.5">
            <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12"/>
          </svg>
        </button>
      </div>

      <div class="flex items-center px-3 pb-2 gap-1">
        <button v-for="tab in tabs" :key="tab"
          @click="loadTab(tab)"
          class="px-3 py-1 rounded-md text-[13px] font-medium transition-colors cursor-pointer relative"
          :style="activeTab === tab ? 'background: #fff; color: #2c2c30; box-shadow: 0 1px 2px rgba(0,0,0,0.05);' : 'color: #9a9aa0;'">
          {{ tab === 'tools' ? 'Tools' : tab === 'skills' ? 'Skills' : tab === 'memory' ? 'Memory' : tab === 'files' ? 'Files' : 'Inbox' }}
          <span
            v-if="tab === 'notifications' && notificationsUnread > 0"
            class="absolute -top-0.5 -right-0.5 min-w-[14px] h-[14px] rounded-full text-[9px] font-semibold flex items-center justify-center px-1"
            style="background: #ef4444; color: #fff;"
          >{{ notificationsUnread > 99 ? '99+' : notificationsUnread }}</span>
        </button>
        <button
          v-if="activeTab !== 'notifications'"
          @click="loadTab(activeTab)"
          class="ml-auto p-1 rounded-md cursor-pointer transition-colors hover:bg-black/[0.04]"
          :class="{ 'is-refreshing': isCurrentTabLoading }"
          :title="`刷新 ${activeTab}`"
          style="color: #9a9aa0;"
        >
          <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="1.8">
            <path stroke-linecap="round" stroke-linejoin="round" d="M16.023 9.348h4.992v-.001M2.985 19.644v-4.992m0 0h4.992m-4.993 0l3.181 3.183a8.25 8.25 0 0013.803-3.7M4.031 9.865a8.25 8.25 0 0113.803-3.7l3.181 3.182m0-4.991v4.99"/>
          </svg>
        </button>
      </div>

      <div class="flex-1 overflow-y-auto px-3 pb-4">
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

        <template v-if="activeTab === 'skills'">
          <div v-if="loadingSkills" class="text-center py-8" style="color: #b0b0b6; font-size: 13px;">加载中…</div>
          <div v-else-if="skills.length === 0" class="text-center py-8" style="color: #b0b0b6; font-size: 13px;">暂无已安装的技能</div>
          <template v-else>
            <div v-for="(group, category) in skillsByCategoryWithSelected" :key="category" class="mb-3">
              <div v-if="category" class="px-3 pb-1 pt-2" style="font-size: 11px; font-weight: 600; color: #9a9aa0; letter-spacing: 0.03em;">{{ category || 'Other' }}</div>
              <div class="space-y-0.5">
                <div v-for="skill in group" :key="skill.name"
                  class="flex items-start justify-between gap-2 px-3 py-2 rounded-lg transition-colors cursor-pointer"
                  :style="skill.isSelected
                    ? 'background: rgba(61, 124, 201, 0.08); border: 1px solid rgba(61, 124, 201, 0.18);'
                    : 'background: #fff; border: 1px solid #ececef;'"
                  @click="selectSkill(skill)"
                  @dblclick="openSkillBrowser(skill)">
                  <div class="min-w-0 flex-1">
                    <div class="text-[14px] truncate" :style="skill.enabled ? 'color: #2c2c30;' : 'color: #b0b0b6;'">{{ skill.name }}</div>
                    <div v-if="skill.description" class="text-[11px] mt-0.5 line-clamp-2" style="color: #9a9aa0;">{{ skill.description }}</div>
                  </div>
                  <button @click.stop="toggleSkill(skill)"
                    class="shrink-0 ml-2 cursor-pointer px-2 py-0.5 rounded text-[12px] transition-colors"
                    :style="skill.enabled ? 'color: #2c2c30;' : 'color: #b0b0b6;'">
                    {{ skill.enabled ? 'on' : 'off' }}
                  </button>
                </div>
              </div>
            </div>

          </template>
        </template>

        <template v-if="activeTab === 'memory'">
          <div v-if="loadingMemory" class="text-center py-8" style="color: #9a9aa0; font-size: 13px;">加载中…</div>
          <template v-else>
            <div v-if="memoryError" class="mb-3 rounded-lg px-3 py-2 text-[13px]" style="background: #fff4f4; color: #b42318; border: 1px solid #ffd7d7;">
              {{ memoryError }}
            </div>

            <div v-if="visibleMemoryEntries.length === 0" class="text-center py-10 text-[12px]" style="color: #b0b0b6;">
              当前目录是空的
            </div>
            <div v-else class="space-y-1">
              <button
                v-for="entry in visibleMemoryEntries"
                :key="entry.path"
                class="w-full flex items-start gap-2 px-3 py-2 rounded-lg text-left cursor-pointer transition-colors"
                :style="memorySelectedPath === entry.path
                  ? 'background: rgba(61, 124, 201, 0.08); border: 1px solid rgba(61, 124, 201, 0.18);'
                  : 'background: #fff; border: 1px solid #ececef;'"
                @click="selectMemoryEntry(entry)"
                @dblclick="openMemoryEntry(entry)"
              >
                <span class="w-4 h-4 shrink-0 mt-0.5" :style="entry.type === 'dir' ? 'color: #d97706;' : entry.type === 'symlink' ? 'color: #8b5cf6;' : 'color: #64748b;'">
                  <svg v-if="entry.type === 'dir'" class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="1.6">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M2.25 6.75A2.25 2.25 0 014.5 4.5h4.19a2.25 2.25 0 011.59.659l1.06 1.06a2.25 2.25 0 001.59.659h6.56a2.25 2.25 0 012.25 2.25v8.25a2.25 2.25 0 01-2.25 2.25H4.5a2.25 2.25 0 01-2.25-2.25V6.75z" />
                  </svg>
                  <svg v-else-if="entry.type === 'symlink'" class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="1.8">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M13.19 8.688a4.5 4.5 0 016.364 6.364l-1.757 1.757a4.5 4.5 0 01-6.364 0m-1.414-9.9a4.5 4.5 0 00-6.364 0L2.44 8.666a4.5 4.5 0 006.364 6.364l1.757-1.757" />
                  </svg>
                  <svg v-else class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="1.6">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M19.5 14.25v-8.625a1.125 1.125 0 00-1.125-1.125H8.25m11.25 9.75h-2.625a1.125 1.125 0 00-1.125 1.125V18m4.875-3.75l-3.375 3.375a2.25 2.25 0 01-1.59.659H6.375A1.125 1.125 0 015.25 17.16V5.625A1.125 1.125 0 016.375 4.5H8.25m0 0l2.25 2.25m-2.25-2.25V6.75m0-2.25h6.75" />
                  </svg>
                </span>

                <div class="min-w-0 flex-1">
                  <div class="flex items-center gap-2 min-w-0">
                    <span class="text-[13px] truncate" style="color: #2c2c30;">{{ entry.name }}</span>
                    <span v-if="entry.type === 'dir' && entry.has_children" class="text-[10px] shrink-0" style="color: #b0b0b6;">folder</span>
                    <span v-else-if="entry.type !== 'dir'" class="text-[11px] shrink-0" style="color: #9a9aa0;">{{ formatWorkspaceSize(entry.size) }}</span>
                  </div>
                  <div class="text-[11px] mt-0.5" style="color: #b0b0b6;">
                    <span>{{ formatWorkspaceTime(entry.modified_at) }}</span>
                    <span v-if="entry.target"> · {{ entry.target }}</span>
                  </div>
                </div>
              </button>
            </div>
          </template>
        </template>

        <template v-if="activeTab === 'files'">
          <div class="rounded-xl border px-3 py-3 mb-3" style="border-color: #ececef; background: rgba(255,255,255,0.88);">
            <div class="text-[12px] font-semibold mb-2" style="color: #6e6e76;">{{ workspaceRootLabel || 'Workspace' }}</div>
            <div class="flex flex-wrap gap-1.5 mb-2">
              <button
                v-for="root in workspaceRoots"
                :key="root.key"
                @click="openWorkspaceRoot(root.key)"
                class="px-2.5 py-1 rounded-md text-[12px] cursor-pointer transition-colors"
                :style="workspaceActiveRoot === root.key
                  ? 'background: var(--theme-700); color: #fff;'
                  : 'background: #fff; color: #6e6e76; border: 1px solid #ececef;'"
              >
                {{ root.label }}
              </button>
            </div>
            <div class="text-[11px] break-all" style="color: #9a9aa0; font-family: var(--ai-font-mono);">
              {{ workspaceRootHint }}
            </div>
            <div class="text-[11px] mt-2 flex flex-wrap gap-x-3 gap-y-1" style="color: #9a9aa0;">
              <span>{{ workspaceEntryCount }} 项</span>
              <span v-if="workspaceListLimit > 0">单目录上限 {{ workspaceListLimit }}</span>
            </div>
            <div
              v-if="workspaceTruncated"
              class="text-[11px] mt-2"
              style="color: #b45309;"
            >当前目录条目过多，只展示前 {{ workspaceListLimit }} 项</div>
          </div>

          <div class="rounded-xl border p-2 mb-3" style="border-color: #ececef; background: rgba(255,255,255,0.88);">
            <div class="flex items-center gap-1.5 flex-wrap">
              <button
                class="w-7 h-7 rounded-md flex items-center justify-center cursor-pointer transition-colors hover:bg-black/[0.04]"
                :disabled="!workspaceCanGoUp"
                :style="workspaceCanGoUp ? 'color: #6e6e76;' : 'color: #d1d1d6;'"
                title="返回上一级"
                @click="openWorkspaceBreadcrumb(workspaceParentPath)"
              >
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="1.8">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M15.75 19.5L8.25 12l7.5-7.5"/>
                </svg>
              </button>
              <button
                v-for="crumb in workspaceBreadcrumbs"
                :key="`${workspaceActiveRoot}-${crumb.path || 'root'}`"
                class="px-2 py-1 rounded-md text-[11px] cursor-pointer transition-colors hover:bg-black/[0.04]"
                style="color: #6e6e76;"
                @click="openWorkspaceBreadcrumb(crumb.path)"
              >
                {{ crumb.name }}
              </button>
            </div>
          </div>

          <div v-if="loadingWorkspace" class="text-center py-8" style="color: #9a9aa0; font-size: 13px;">加载中…</div>
          <div
            v-else-if="workspaceError"
            class="rounded-lg px-3 py-2 text-[13px]"
            style="background: #fff4f4; color: #b42318; border: 1px solid #ffd7d7;"
          >
            {{ workspaceError }}
          </div>
          <div v-else-if="workspaceEntries.length === 0" class="text-center py-10 text-[12px]" style="color: #b0b0b6;">
            当前目录是空的
          </div>
          <div v-else class="space-y-1">
            <button
              v-for="entry in workspaceEntries"
              :key="entry.path"
              class="w-full flex items-start gap-2 px-3 py-2 rounded-lg text-left cursor-pointer transition-colors"
              :style="workspaceSelectedPath === entry.path
                ? 'background: rgba(61, 124, 201, 0.08); border: 1px solid rgba(61, 124, 201, 0.18);'
                : 'background: #fff; border: 1px solid #ececef;'"
              @click="selectWorkspaceEntry(entry)"
              @dblclick="openWorkspaceEntry(entry)"
            >
              <span class="w-4 h-4 shrink-0 mt-0.5" :style="entry.type === 'dir' ? 'color: #d97706;' : entry.type === 'symlink' ? 'color: #8b5cf6;' : 'color: #64748b;'">
                <svg v-if="entry.type === 'dir'" class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="1.6">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M2.25 6.75A2.25 2.25 0 014.5 4.5h4.19a2.25 2.25 0 011.59.659l1.06 1.06a2.25 2.25 0 001.59.659h6.56a2.25 2.25 0 012.25 2.25v8.25a2.25 2.25 0 01-2.25 2.25H4.5a2.25 2.25 0 01-2.25-2.25V6.75z" />
                </svg>
                <svg v-else-if="entry.type === 'symlink'" class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="1.8">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M13.19 8.688a4.5 4.5 0 016.364 6.364l-1.757 1.757a4.5 4.5 0 01-6.364 0m-1.414-9.9a4.5 4.5 0 00-6.364 0L2.44 8.666a4.5 4.5 0 006.364 6.364l1.757-1.757" />
                </svg>
                <svg v-else class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="1.6">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M19.5 14.25v-8.625a1.125 1.125 0 00-1.125-1.125H8.25m11.25 9.75h-2.625a1.125 1.125 0 00-1.125 1.125V18m4.875-3.75l-3.375 3.375a2.25 2.25 0 01-1.59.659H6.375A1.125 1.125 0 015.25 17.16V5.625A1.125 1.125 0 016.375 4.5H8.25m0 0l2.25 2.25m-2.25-2.25V6.75m0-2.25h6.75" />
                </svg>
              </span>

              <div class="min-w-0 flex-1">
                <div class="flex items-center gap-2 min-w-0">
                  <span class="text-[13px] truncate" style="color: #2c2c30;">{{ entry.name }}</span>
                  <span v-if="entry.type === 'dir' && entry.has_children" class="text-[10px] shrink-0" style="color: #b0b0b6;">folder</span>
                  <span v-else-if="entry.type !== 'dir'" class="text-[11px] shrink-0" style="color: #9a9aa0;">{{ formatWorkspaceSize(entry.size) }}</span>
                </div>
                <div class="text-[11px] mt-0.5" style="color: #b0b0b6;">
                  <span>{{ formatWorkspaceTime(entry.modified_at) }}</span>
                  <span v-if="entry.target"> · {{ entry.target }}</span>
                </div>
              </div>
            </button>
          </div>
          <div class="mt-3 text-[11px] text-center" style="color: #b0b0b6;">
            单击选择，双击打开
          </div>
        </template>

        <template v-if="activeTab === 'notifications'">
          <div class="flex items-center justify-between mb-2 px-1">
            <span class="text-[13px]" style="color: #6e6e76;">
              {{ notifications.length === 0 ? '暂无通知' : `共 ${notifications.length} 条` }}
            </span>
            <div class="flex items-center gap-3">
              <button
                v-if="notificationsUnread > 0"
                @click="markNotificationRead('all')"
                class="text-[12px] cursor-pointer hover:underline"
                style="color: var(--theme-500);"
              >全部已读</button>
              <button
                v-if="notifications.length > 0"
                @click="clearAllNotifications"
                class="text-[12px] cursor-pointer hover:underline"
                style="color: var(--theme-500);"
              >清空</button>
            </div>
          </div>
          <div v-if="notificationsLoading && notifications.length === 0" class="text-center py-8 text-[12px]" style="color: #b0b0b6;">加载中…</div>
          <div v-else-if="notificationsError" class="text-center py-8 text-[12px]" style="color: #b91c1c;">{{ notificationsError }}</div>
          <div v-else-if="notifications.length === 0" class="text-center py-12 text-[12px]" style="color: #b0b0b6;">收件箱是空的</div>
          <div v-else class="space-y-2">
            <div
              v-for="n in notifications"
              :key="n.id"
              @click="handleNotifClick(n)"
              class="rounded-lg px-3 py-2.5 cursor-pointer transition-colors group/notif relative"
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
                <button
                  @click.stop="deleteNotification(n.id)"
                  class="opacity-0 group-hover/notif:opacity-100 transition-opacity p-0.5 rounded cursor-pointer hover:bg-black/[0.06] shrink-0"
                  style="color: var(--theme-400);"
                  title="删除"
                >
                  <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="1.6">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M14.74 9l-.346 9m-4.788 0L9.26 9m9.968-3.21c.342.052.682.107 1.022.166m-1.022-.165L18.16 19.673a2.25 2.25 0 01-2.244 2.077H8.084a2.25 2.25 0 01-2.244-2.077L4.772 5.79m14.456 0a48.108 48.108 0 00-3.478-.397m-12 .562c.34-.059.68-.114 1.022-.165m0 0a48.11 48.11 0 013.478-.397m7.5 0v-.916c0-1.18-.91-2.164-2.09-2.201a51.964 51.964 0 00-3.32 0c-1.18.037-2.09 1.022-2.09 2.201v.916m7.5 0a48.667 48.667 0 00-7.5 0"/>
                  </svg>
                </button>
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

  <Transition name="workspace-preview">
    <div
      v-if="skillBrowserOpen"
      class="fixed inset-0 z-[80] flex items-center justify-center bg-black/45 px-6 py-8"
      @click="closeSkillBrowser"
    >
      <div
        class="w-full max-w-2xl max-h-full rounded-2xl border shadow-2xl overflow-hidden flex flex-col"
        style="background: #f7f7f8; border-color: rgba(255,255,255,0.24);"
        @click.stop
      >
        <div class="flex items-center justify-between gap-3 px-4 py-3 border-b" style="border-color: #e8e8ec;">
          <div class="min-w-0">
            <div class="text-[14px] font-semibold truncate" style="color: #2c2c30;">
              {{ selectedSkillName || 'Skill' }}
            </div>
            <div v-if="selectedSkillMeta?.description" class="text-[11px] truncate mt-0.5" style="color: #9a9aa0;">
              {{ selectedSkillMeta.description }}
            </div>
          </div>
          <button
            class="w-8 h-8 rounded-md flex items-center justify-center cursor-pointer transition-colors hover:bg-black/[0.05] shrink-0"
            style="color: #9a9aa0;"
            title="关闭"
            @click="closeSkillBrowser"
          >
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="1.8">
              <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12"/>
            </svg>
          </button>
        </div>

        <div class="flex-1 overflow-auto p-4">
          <div class="rounded-xl border p-2 mb-3" style="border-color: #ececef; background: rgba(255,255,255,0.88);">
            <div class="flex items-center gap-1.5 flex-wrap">
              <button
                class="w-7 h-7 rounded-md flex items-center justify-center cursor-pointer transition-colors hover:bg-black/[0.04]"
                :disabled="!skillBrowserCanGoUp"
                :style="skillBrowserCanGoUp ? 'color: #6e6e76;' : 'color: #d1d1d6;'"
                title="返回上一级"
                @click="openSkillBrowserBreadcrumb(skillBrowserParentPath)"
              >
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="1.8">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M15.75 19.5L8.25 12l7.5-7.5"/>
                </svg>
              </button>
              <button
                v-for="crumb in skillBrowserBreadcrumbs"
                :key="`skill-${selectedSkillName}-${crumb.path || 'root'}`"
                class="px-2 py-1 rounded-md text-[11px] cursor-pointer transition-colors hover:bg-black/[0.04]"
                style="color: #6e6e76;"
                @click="openSkillBrowserBreadcrumb(crumb.path)"
              >
                {{ crumb.name }}
              </button>
            </div>
          </div>

          <div v-if="loadingSkillBrowser" class="text-center py-8 text-[12px]" style="color: #b0b0b6;">
            加载中…
          </div>
          <div
            v-else-if="skillBrowserError"
            class="rounded-lg px-3 py-2 text-[13px]"
            style="background: #fff4f4; color: #b42318; border: 1px solid #ffd7d7;"
          >
            {{ skillBrowserError }}
          </div>
          <div v-else-if="skillBrowserEntries.length === 0" class="text-center py-10 text-[12px]" style="color: #b0b0b6;">
            当前目录是空的
          </div>
          <div v-else class="space-y-1">
            <button
              v-for="entry in skillBrowserEntries"
              :key="`${selectedSkillName}-${entry.path}`"
              class="w-full flex items-start gap-2 px-3 py-2 rounded-lg text-left cursor-pointer transition-colors"
              :style="skillBrowserSelectedPath === entry.path
                ? 'background: rgba(61, 124, 201, 0.08); border: 1px solid rgba(61, 124, 201, 0.18);'
                : 'background: #fff; border: 1px solid #ececef;'"
              @click="selectSkillBrowserEntry(entry)"
              @dblclick="openSkillBrowserEntry(entry)"
            >
              <span class="w-4 h-4 shrink-0 mt-0.5" :style="entry.type === 'dir' ? 'color: #d97706;' : entry.type === 'symlink' ? 'color: #8b5cf6;' : 'color: #64748b;'">
                <svg v-if="entry.type === 'dir'" class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="1.6">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M2.25 6.75A2.25 2.25 0 014.5 4.5h4.19a2.25 2.25 0 011.59.659l1.06 1.06a2.25 2.25 0 001.59.659h6.56a2.25 2.25 0 012.25 2.25v8.25a2.25 2.25 0 01-2.25 2.25H4.5a2.25 2.25 0 01-2.25-2.25V6.75z" />
                </svg>
                <svg v-else-if="entry.type === 'symlink'" class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="1.8">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M13.19 8.688a4.5 4.5 0 016.364 6.364l-1.757 1.757a4.5 4.5 0 01-6.364 0m-1.414-9.9a4.5 4.5 0 00-6.364 0L2.44 8.666a4.5 4.5 0 006.364 6.364l1.757-1.757" />
                </svg>
                <svg v-else class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="1.6">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M19.5 14.25v-8.625a1.125 1.125 0 00-1.125-1.125H8.25m11.25 9.75h-2.625a1.125 1.125 0 00-1.125 1.125V18m4.875-3.75l-3.375 3.375a2.25 2.25 0 01-1.59.659H6.375A1.125 1.125 0 015.25 17.16V5.625A1.125 1.125 0 016.375 4.5H8.25m0 0l2.25 2.25m-2.25-2.25V6.75m0-2.25h6.75" />
                </svg>
              </span>

              <div class="min-w-0 flex-1">
                <div class="flex items-center gap-2 min-w-0">
                  <span class="text-[13px] truncate" style="color: #2c2c30;">{{ entry.name }}</span>
                  <span v-if="entry.type === 'dir' && entry.has_children" class="text-[10px] shrink-0" style="color: #b0b0b6;">folder</span>
                  <span v-else-if="entry.type !== 'dir'" class="text-[11px] shrink-0" style="color: #9a9aa0;">{{ formatWorkspaceSize(entry.size) }}</span>
                </div>
                <div class="text-[11px] mt-0.5" style="color: #b0b0b6;">
                  <span>{{ formatWorkspaceTime(entry.modified_at) }}</span>
                  <span v-if="entry.target"> · {{ entry.target }}</span>
                </div>
              </div>
            </button>
          </div>
        </div>
      </div>
    </div>
  </Transition>

  <Transition name="workspace-preview">
    <div
      v-if="workspacePreviewOpen"
      class="fixed inset-0 z-[90] flex items-center justify-center bg-black/45 px-6 py-8"
      @click="closeWorkspacePreview"
    >
      <div
        class="w-full max-w-4xl max-h-full rounded-2xl border shadow-2xl overflow-hidden flex flex-col"
        style="background: #f7f7f8; border-color: rgba(255,255,255,0.24);"
        @click.stop
      >
        <div class="flex items-center justify-between gap-3 px-4 py-3 border-b" style="border-color: #e8e8ec;">
          <div class="min-w-0">
            <div class="text-[14px] font-semibold truncate" style="color: #2c2c30;">
              {{ workspacePreview?.name || 'Preview' }}
            </div>
            <div class="text-[11px] truncate mt-0.5" style="color: #9a9aa0;">
              {{ workspacePreview?.display_path }}
            </div>
          </div>
          <div class="flex items-center gap-3 shrink-0">
            <span v-if="workspacePreviewMeta" class="text-[11px]" style="color: #9a9aa0;">
              {{ workspacePreviewMeta }}
            </span>
            <button
              class="w-8 h-8 rounded-md flex items-center justify-center cursor-pointer transition-colors hover:bg-black/[0.05]"
              style="color: #9a9aa0;"
              title="关闭"
              @click="closeWorkspacePreview"
            >
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="1.8">
                <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12"/>
              </svg>
            </button>
          </div>
        </div>

        <div class="flex-1 overflow-auto p-4">
          <div v-if="loadingWorkspacePreview" class="text-center py-10 text-[13px]" style="color: #9a9aa0;">加载预览…</div>
          <div v-else-if="workspacePreviewError" class="rounded-lg px-3 py-2 text-[13px]" style="background: #fff4f4; color: #b42318; border: 1px solid #ffd7d7;">
            {{ workspacePreviewError }}
          </div>
          <template v-else-if="workspacePreview">
            <pre
              v-if="workspacePreview.preview_type === 'text'"
              class="rounded-xl p-4 whitespace-pre-wrap break-words min-h-[240px]"
              style="background: #fff; color: #2c2c30; font-size: 12px; line-height: 1.6; font-family: var(--ai-font-mono);"
            >{{ workspacePreview.content }}</pre>
            <img
              v-else-if="workspacePreview.preview_type === 'image'"
              :src="workspacePreview.data_url"
              :alt="workspacePreview.name"
              class="max-w-full max-h-[75vh] mx-auto rounded-xl border bg-white"
              style="border-color: #ececef;"
            />
            <iframe
              v-else-if="workspacePreview.preview_type === 'pdf'"
              :src="workspacePreview.data_url"
              class="w-full h-[75vh] rounded-xl border bg-white"
              style="border-color: #ececef;"
            ></iframe>
            <div v-else class="rounded-xl p-4 text-[13px]" style="background: #fff; color: #6e6e76; border: 1px solid #ececef;">
              这个文件类型暂不支持内联预览。
            </div>
            <div v-if="workspacePreview.truncated" class="text-[11px] mt-3" style="color: #b45309;">
              文件较大，当前只展示前 256 KB 文本内容
            </div>
          </template>
        </div>
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
.is-refreshing svg {
  animation: refresh-spin 0.8s linear infinite;
}
@keyframes refresh-spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
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
.workspace-preview-enter-active, .workspace-preview-leave-active {
  transition: opacity 0.18s ease;
}
.workspace-preview-enter-from, .workspace-preview-leave-to {
  opacity: 0;
}
</style>
