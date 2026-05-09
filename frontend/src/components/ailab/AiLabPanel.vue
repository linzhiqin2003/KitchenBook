<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { getHermesApiUrl, HERMES_API_KEY } from '../../config/api'
import { useAuthStore } from '../../store/auth'
import api from '../../api/client'
import EntryIcon from './EntryIcon.vue'

const authStore = useAuthStore()

const props = defineProps({
  visible: { type: Boolean, default: false }
})

const emit = defineEmits(['close'])

const activeTab = ref('tools')
const tabs = ['tools', 'skills', 'memory', 'files', 'notifications']
const TAB_META = {
  tools: { label: 'Tools', icon: 'wrench' },
  skills: { label: 'Skills', icon: 'sparkles' },
  memory: { label: 'Memory', icon: 'memory' },
  files: { label: 'Files', icon: 'folder' },
  notifications: { label: 'Inbox', icon: 'bell' },
}
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
const isMobile = ref(window.innerWidth < 1024)

const checkMobile = () => { isMobile.value = window.innerWidth < 1024 }
let mobileResizeHandler = null

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
    const r = await fetch(`${getHermesApiUrl()}/api/tools`, { headers: headers.value })
    if (r.ok) {
      const data = await r.json()
      tools.value = data.tools || []
    }
  } catch (e) { console.error('Failed to fetch tools:', e) }
  finally { loadingTools.value = false }
}

const toggleTool = async (tool) => {
  try {
    await fetch(`${getHermesApiUrl()}/api/tools/toggle`, {
      method: 'POST', headers: headers.value,
      body: JSON.stringify({ name: tool.name, enable: !tool.enabled })
    })
    tool.enabled = !tool.enabled
  } catch (e) { console.error('Failed to toggle tool:', e) }
}

const fetchSkills = async () => {
  loadingSkills.value = true
  try {
    const r = await fetch(`${getHermesApiUrl()}/api/skills`, { headers: headers.value })
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
    const r = await fetch(`${getHermesApiUrl()}/api/skills/toggle`, {
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
  mobileResizeHandler = () => checkMobile()
  window.addEventListener('resize', mobileResizeHandler)
})

onUnmounted(() => {
  stopResize()
  if (notifPollHandle) clearInterval(notifPollHandle)
  if (mobileResizeHandler) window.removeEventListener('resize', mobileResizeHandler)
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

// 双击：直接预览该 skill 的 SKILL.md。需要看完整目录用 folder 按钮入口。
const openSkillReadme = async (skill) => {
  if (!skill?.name) return
  selectedSkillName.value = skill.name
  await previewSkillEntry({ name: 'SKILL.md', path: 'SKILL.md' })
}

// folder 按钮：弹浮窗展示该 skill 的目录结构。切换 skill 时重置路径。
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
      :class="{ resizing: isResizing, 'panel-mobile': isMobile }"
      :style="isMobile ? {} : { width: `${panelWidth}px`, minWidth: `${panelWidth}px` }"
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

      <div class="flex items-center justify-between px-4 pt-3.5 pb-2.5">
        <div class="flex items-center gap-2">
          <span class="text-[13.5px] font-semibold tracking-tight" style="color: var(--theme-700);">Agent Panel</span>
        </div>
        <div class="flex items-center gap-0.5">
          <button
            v-if="activeTab !== 'notifications'"
            @click="loadTab(activeTab)"
            class="w-7 h-7 rounded-md cursor-pointer transition-colors hover:bg-black/[0.04] flex items-center justify-center"
            :class="{ 'is-refreshing': isCurrentTabLoading }"
            :title="`刷新 ${activeTab}`"
            style="color: var(--theme-400);"
          >
            <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="1.8">
              <path stroke-linecap="round" stroke-linejoin="round" d="M16.023 9.348h4.992v-.001M2.985 19.644v-4.992m0 0h4.992m-4.993 0l3.181 3.183a8.25 8.25 0 0013.803-3.7M4.031 9.865a8.25 8.25 0 0113.803-3.7l3.181 3.182m0-4.991v4.99"/>
            </svg>
          </button>
          <button @click="emit('close')" class="w-7 h-7 rounded-md cursor-pointer hover:bg-black/[0.04] flex items-center justify-center transition-colors" style="color: var(--theme-400);" title="关闭">
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="1.6">
              <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12"/>
            </svg>
          </button>
        </div>
      </div>

      <div class="px-3 pb-2.5">
        <div class="tab-bar flex items-center gap-0.5 p-1 rounded-lg" style="background: rgba(0,0,0,0.035);">
          <button v-for="tab in tabs" :key="tab"
            @click="loadTab(tab)"
            class="tab-btn flex-1 flex items-center justify-center gap-1.5 px-2 py-1.5 rounded-md text-[12px] font-medium transition-all cursor-pointer relative"
            :class="{ 'tab-active': activeTab === tab }"
            :title="TAB_META[tab].label">
            <svg v-if="TAB_META[tab].icon === 'wrench'" class="w-3.5 h-3.5 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="1.7">
              <path stroke-linecap="round" stroke-linejoin="round" d="M11.42 15.17L17.25 21A2.652 2.652 0 0021 17.25l-5.877-5.877M11.42 15.17l2.496-3.03c.317-.384.74-.626 1.208-.766M11.42 15.17l-4.655 5.653a2.548 2.548 0 11-3.586-3.586l6.837-5.63m5.108-.233c.55-.164 1.163-.188 1.743-.14a4.5 4.5 0 004.486-6.336l-3.276 3.277a3.004 3.004 0 01-2.25-2.25l3.276-3.276a4.5 4.5 0 00-6.336 4.486c.091 1.076-.071 2.264-.904 2.95l-.102.085m-1.745 1.437L5.909 7.5H4.5L2.25 3.75l1.5-1.5L7.5 4.5v1.409l4.26 4.26m-1.745 1.437l1.745-1.437m6.615 8.206L15.75 15.75M4.867 19.125h.008v.008h-.008v-.008z"/>
            </svg>
            <svg v-else-if="TAB_META[tab].icon === 'sparkles'" class="w-3.5 h-3.5 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="1.7">
              <path stroke-linecap="round" stroke-linejoin="round" d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09zM18.259 8.715L18 9.75l-.259-1.035a3.375 3.375 0 00-2.455-2.456L14.25 6l1.036-.259a3.375 3.375 0 002.455-2.456L18 2.25l.259 1.035a3.375 3.375 0 002.455 2.456L21.75 6l-1.036.259a3.375 3.375 0 00-2.455 2.456z"/>
            </svg>
            <svg v-else-if="TAB_META[tab].icon === 'memory'" class="w-3.5 h-3.5 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="1.7">
              <path stroke-linecap="round" stroke-linejoin="round" d="M20.25 6.375c0 2.278-3.694 4.125-8.25 4.125S3.75 8.653 3.75 6.375m16.5 0c0-2.278-3.694-4.125-8.25-4.125S3.75 4.097 3.75 6.375m16.5 0v11.25c0 2.278-3.694 4.125-8.25 4.125s-8.25-1.847-8.25-4.125V6.375m16.5 0v3.75m-16.5-3.75v3.75m16.5 0v3.75C20.25 16.153 16.556 18 12 18s-8.25-1.847-8.25-4.125v-3.75m16.5 0c0 2.278-3.694 4.125-8.25 4.125s-8.25-1.847-8.25-4.125"/>
            </svg>
            <svg v-else-if="TAB_META[tab].icon === 'folder'" class="w-3.5 h-3.5 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="1.7">
              <path stroke-linecap="round" stroke-linejoin="round" d="M2.25 12.75V12A2.25 2.25 0 014.5 9.75h15A2.25 2.25 0 0121.75 12v.75m-8.69-6.44l-2.12-2.12a1.5 1.5 0 00-1.061-.44H4.5A2.25 2.25 0 002.25 6v12a2.25 2.25 0 002.25 2.25h15A2.25 2.25 0 0021.75 18V9a2.25 2.25 0 00-2.25-2.25h-5.379a1.5 1.5 0 01-1.06-.44z"/>
            </svg>
            <svg v-else-if="TAB_META[tab].icon === 'bell'" class="w-3.5 h-3.5 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="1.7">
              <path stroke-linecap="round" stroke-linejoin="round" d="M14.857 17.082a23.848 23.848 0 005.454-1.31A8.967 8.967 0 0118 9.75v-.7V9A6 6 0 006 9v.75a8.967 8.967 0 01-2.312 6.022c1.733.64 3.56 1.085 5.455 1.31m5.714 0a24.255 24.255 0 01-5.714 0m5.714 0a3 3 0 11-5.714 0"/>
            </svg>
            <span class="tab-label">{{ TAB_META[tab].label }}</span>
            <span
              v-if="tab === 'notifications' && notificationsUnread > 0"
              class="absolute -top-0.5 -right-0.5 min-w-[14px] h-[14px] rounded-full text-[9px] font-semibold flex items-center justify-center px-1 ring-2 ring-[var(--theme-50,var(--theme-50))]"
              style="background: #ef4444; color: #fff;"
            >{{ notificationsUnread > 99 ? '99+' : notificationsUnread }}</span>
          </button>
        </div>
      </div>

      <div class="flex-1 overflow-y-auto px-3 pb-4 panel-body">
        <template v-if="activeTab === 'tools'">
          <div v-if="loadingTools" class="space-y-2 pt-1">
            <div v-for="n in 5" :key="`tools-skel-${n}`" class="skeleton-row" />
          </div>
          <template v-else-if="tools.length === 0">
            <div class="empty-state">
              <svg class="w-10 h-10 mb-2.5" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="1.4" style="color: var(--theme-300);">
                <path stroke-linecap="round" stroke-linejoin="round" d="M11.42 15.17L17.25 21A2.652 2.652 0 0021 17.25l-5.877-5.877M11.42 15.17l2.496-3.03c.317-.384.74-.626 1.208-.766M11.42 15.17l-4.655 5.653a2.548 2.548 0 11-3.586-3.586l6.837-5.63m5.108-.233c.55-.164 1.163-.188 1.743-.14a4.5 4.5 0 004.486-6.336l-3.276 3.277a3.004 3.004 0 01-2.25-2.25l3.276-3.276a4.5 4.5 0 00-6.336 4.486c.091 1.076-.071 2.264-.904 2.95l-.102.085"/>
              </svg>
              <div class="empty-title">暂无可用工具</div>
              <div class="empty-hint">登录或连接 Hermes 后可启用</div>
            </div>
          </template>
          <template v-else>
            <div class="space-y-0.5">
              <template v-for="tool in tools.filter(t => t.type === 'builtin')" :key="tool.name">
                <div class="row-item flex items-center justify-between px-3 py-2 rounded-lg">
                  <div class="flex items-center gap-2 flex-1 min-w-0">
                    <span class="w-1.5 h-1.5 rounded-full shrink-0 transition-colors" :style="tool.enabled ? 'background: var(--ai-accent);' : 'background: var(--theme-300);'"></span>
                    <span class="text-[14px] truncate" :style="tool.enabled ? 'color: var(--theme-700);' : 'color: var(--theme-300);'">{{ tool.name }}</span>
                  </div>
                  <button @click="toggleTool(tool)" class="toggle-pill shrink-0 ml-2 cursor-pointer text-[10.5px] font-semibold uppercase tracking-wider transition-all"
                    :class="{ 'is-on': tool.enabled }">
                    {{ tool.enabled ? 'on' : 'off' }}
                  </button>
                </div>
              </template>
            </div>
            <div v-if="tools.some(t => t.type === 'mcp')" class="mt-4">
              <div class="section-label">MCP Servers</div>
              <div v-for="tool in tools.filter(t => t.type === 'mcp')" :key="'mcp-' + tool.name"
                class="row-item flex items-center gap-2 px-3 py-2 rounded-lg">
                <span class="w-1.5 h-1.5 rounded-full shrink-0" style="background: var(--ai-accent);"></span>
                <span class="text-[14px]" style="color: var(--theme-700);">{{ tool.name }}</span>
              </div>
            </div>
          </template>
        </template>

        <template v-if="activeTab === 'skills'">
          <div v-if="loadingSkills" class="space-y-2 pt-1">
            <div v-for="n in 4" :key="`skills-skel-${n}`" class="skeleton-card" />
          </div>
          <div v-else-if="skills.length === 0" class="empty-state">
            <svg class="w-10 h-10 mb-2.5" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="1.4" style="color: var(--theme-300);">
              <path stroke-linecap="round" stroke-linejoin="round" d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09zM18.259 8.715L18 9.75l-.259-1.035a3.375 3.375 0 00-2.455-2.456L14.25 6l1.036-.259a3.375 3.375 0 002.455-2.456L18 2.25l.259 1.035a3.375 3.375 0 002.455 2.456L21.75 6l-1.036.259a3.375 3.375 0 00-2.455 2.456z"/>
            </svg>
            <div class="empty-title">暂无已安装的技能</div>
            <div class="empty-hint">在 Hermes 配置中安装 skill 后即可启用</div>
          </div>
          <template v-else>
            <div v-for="(group, category) in skillsByCategoryWithSelected" :key="category" class="mb-3">
              <div v-if="category" class="section-label">{{ category || 'Other' }}</div>
              <div class="space-y-1">
                <div v-for="skill in group" :key="skill.name"
                  class="card-item flex items-start justify-between gap-2 px-3 py-2 rounded-lg cursor-pointer relative"
                  :class="{ 'is-selected': skill.isSelected }"
                  @click="selectSkill(skill)"
                  @dblclick="openSkillReadme(skill)">
                  <div class="min-w-0 flex-1">
                    <div class="flex items-center gap-1.5">
                      <span class="text-[13.5px] truncate font-medium" :style="skill.enabled ? 'color: var(--theme-700);' : 'color: var(--theme-300);'">{{ skill.name }}</span>
                    </div>
                    <div v-if="skill.description" class="text-[11px] mt-0.5 line-clamp-2 leading-snug" style="color: var(--theme-400);">{{ skill.description }}</div>
                  </div>
                  <div class="shrink-0 ml-2 flex items-center gap-1">
                    <button @click.stop="openSkillBrowser(skill)"
                      class="icon-btn cursor-pointer transition-all"
                      title="查看文件目录">
                      <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="1.7">
                        <path stroke-linecap="round" stroke-linejoin="round" d="M3.75 9.776c.112-.017.227-.026.344-.026h15.812c.117 0 .232.009.344.026m-16.5 0a2.25 2.25 0 00-1.883 2.542l.857 6a2.25 2.25 0 002.227 1.932H19.05a2.25 2.25 0 002.227-1.932l.857-6a2.25 2.25 0 00-1.883-2.542m-16.5 0V6A2.25 2.25 0 016 3.75h3.879a1.5 1.5 0 011.06.44l2.122 2.12a1.5 1.5 0 001.06.44H18A2.25 2.25 0 0120.25 9v.776"/>
                      </svg>
                    </button>
                    <button @click.stop="toggleSkill(skill)"
                      class="toggle-pill cursor-pointer text-[10.5px] font-semibold uppercase tracking-wider transition-all"
                      :class="{ 'is-on': skill.enabled }">
                      {{ skill.enabled ? 'on' : 'off' }}
                    </button>
                  </div>
                </div>
              </div>
            </div>
            <div class="text-[10.5px] text-center mt-2" style="color: var(--theme-300);">
              单击选中 · 双击查看文件
            </div>
          </template>
        </template>

        <template v-if="activeTab === 'memory'">
          <div v-if="loadingMemory" class="space-y-2 pt-1">
            <div v-for="n in 4" :key="`mem-skel-${n}`" class="skeleton-card" />
          </div>
          <template v-else>
            <div v-if="memoryError" class="error-banner">
              <svg class="w-4 h-4 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="1.7"><path stroke-linecap="round" stroke-linejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z"/></svg>
              <span>{{ memoryError }}</span>
            </div>

            <div v-if="visibleMemoryEntries.length === 0" class="empty-state">
              <svg class="w-10 h-10 mb-2.5" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="1.3" style="color: var(--theme-300);">
                <path stroke-linecap="round" stroke-linejoin="round" d="M20.25 6.375c0 2.278-3.694 4.125-8.25 4.125S3.75 8.653 3.75 6.375m16.5 0c0-2.278-3.694-4.125-8.25-4.125S3.75 4.097 3.75 6.375m16.5 0v11.25c0 2.278-3.694 4.125-8.25 4.125s-8.25-1.847-8.25-4.125V6.375m16.5 0v3.75m-16.5-3.75v3.75m16.5 0v3.75C20.25 16.153 16.556 18 12 18s-8.25-1.847-8.25-4.125v-3.75m16.5 0c0 2.278-3.694 4.125-8.25 4.125s-8.25-1.847-8.25-4.125"/>
              </svg>
              <div class="empty-title">尚无记忆条目</div>
              <div class="empty-hint">Agent 会自动把跨会话的事实存到这里</div>
            </div>
            <div v-else class="space-y-1">
              <button
                v-for="entry in visibleMemoryEntries"
                :key="entry.path"
                class="card-item w-full flex items-start gap-2.5 px-3 py-2 rounded-lg text-left cursor-pointer relative"
                :class="{ 'is-selected': memorySelectedPath === entry.path }"
                @click="selectMemoryEntry(entry)"
                @dblclick="openMemoryEntry(entry)"
              >
                <EntryIcon :entry="entry" class="mt-0.5" />

                <div class="min-w-0 flex-1">
                  <div class="flex items-center gap-2 min-w-0">
                    <span class="text-[13px] truncate font-medium" style="color: var(--theme-700);">{{ entry.name }}</span>
                                      </div>
                  <div class="text-[11px] mt-0.5" style="color: var(--theme-300);">
                    <span>{{ formatWorkspaceTime(entry.modified_at) }}</span>
                    <span v-if="entry.target"> · {{ entry.target }}</span>
                  </div>
                </div>
              </button>
            </div>
          </template>
        </template>

        <template v-if="activeTab === 'files'">
          <div class="files-header rounded-xl mb-3 overflow-hidden">
            <div class="files-toolbar px-2 py-1.5 flex items-center gap-1 flex-wrap">
              <button
                class="w-6 h-6 rounded-md flex items-center justify-center cursor-pointer transition-colors hover:bg-black/[0.04]"
                :disabled="!workspaceCanGoUp"
                :style="workspaceCanGoUp ? 'color: var(--theme-500);' : 'color: var(--theme-300);'"
                title="返回上一级"
                @click="openWorkspaceBreadcrumb(workspaceParentPath)"
              >
                <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="1.8">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M15.75 19.5L8.25 12l7.5-7.5"/>
                </svg>
              </button>
              <template v-for="(crumb, ci) in workspaceBreadcrumbs" :key="`${workspaceActiveRoot}-${crumb.path || 'root'}`">
                <span v-if="ci > 0" class="text-[11px] select-none" style="color: var(--theme-300);">/</span>
                <button
                  class="px-1.5 py-0.5 rounded-md text-[11px] cursor-pointer transition-colors hover:bg-black/[0.04]"
                  style="color: var(--theme-500);"
                  @click="openWorkspaceBreadcrumb(crumb.path)"
                >
                  {{ crumb.name }}
                </button>
              </template>
            </div>
          </div>

          <div v-if="loadingWorkspace" class="space-y-2 pt-1">
            <div v-for="n in 5" :key="`ws-skel-${n}`" class="skeleton-card" />
          </div>
          <div v-else-if="workspaceError" class="error-banner">
            <svg class="w-4 h-4 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="1.7"><path stroke-linecap="round" stroke-linejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z"/></svg>
            <span>{{ workspaceError }}</span>
          </div>
          <div v-else-if="workspaceEntries.length === 0" class="empty-state">
            <svg class="w-10 h-10 mb-2.5" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="1.4" style="color: var(--theme-300);">
              <path stroke-linecap="round" stroke-linejoin="round" d="M3.75 9.776c.112-.017.227-.026.344-.026h15.812c.117 0 .232.009.344.026m-16.5 0a2.25 2.25 0 00-1.883 2.542l.857 6a2.25 2.25 0 002.227 1.932H19.05a2.25 2.25 0 002.227-1.932l.857-6a2.25 2.25 0 00-1.883-2.542m-16.5 0V6A2.25 2.25 0 016 3.75h3.879a1.5 1.5 0 011.06.44l2.122 2.12a1.5 1.5 0 001.06.44H18A2.25 2.25 0 0120.25 9v.776"/>
            </svg>
            <div class="empty-title">当前目录是空的</div>
            <div class="empty-hint">这里会列出 workspace 下的文件与子目录</div>
          </div>
          <div v-else class="space-y-1">
            <button
              v-for="entry in workspaceEntries"
              :key="entry.path"
              class="card-item w-full flex items-start gap-2.5 px-3 py-2 rounded-lg text-left cursor-pointer relative"
              :class="{ 'is-selected': workspaceSelectedPath === entry.path }"
              @click="selectWorkspaceEntry(entry)"
              @dblclick="openWorkspaceEntry(entry)"
            >
              <EntryIcon :entry="entry" class="mt-0.5" />

              <div class="min-w-0 flex-1">
                <div class="flex items-center gap-2 min-w-0">
                  <span class="text-[13px] truncate font-medium" style="color: var(--theme-700);">{{ entry.name }}</span>
                                  </div>
                <div class="text-[11px] mt-0.5" style="color: var(--theme-300);">
                  <span>{{ formatWorkspaceTime(entry.modified_at) }}</span>
                  <span v-if="entry.target"> · {{ entry.target }}</span>
                </div>
              </div>
            </button>
          </div>
          <div v-if="workspaceEntries.length > 0" class="mt-3 text-[10.5px] text-center" style="color: var(--theme-300);">
            单击选中 · 双击打开
          </div>
        </template>

        <template v-if="activeTab === 'notifications'">
          <div v-if="notifications.length > 0" class="flex items-center justify-between mb-2.5 px-1">
            <span class="text-[12px] flex items-center gap-1.5" style="color: var(--theme-500);">
              <span class="text-[13px] font-medium" style="color: var(--theme-700);">{{ notifications.length }}</span>
              <span>条通知</span>
              <span v-if="notificationsUnread > 0" class="px-1.5 py-px rounded text-[10px] font-semibold" style="background: rgba(239,68,68,0.1); color: #ef4444;">{{ notificationsUnread }} 未读</span>
            </span>
            <div class="flex items-center gap-2.5">
              <button
                v-if="notificationsUnread > 0"
                @click="markNotificationRead('all')"
                class="text-[11.5px] cursor-pointer transition-colors"
                style="color: var(--ai-accent);"
              >全部已读</button>
              <button
                v-if="notifications.length > 0"
                @click="clearAllNotifications"
                class="text-[11.5px] cursor-pointer transition-colors hover:text-red-500"
                style="color: var(--theme-400);"
              >清空</button>
            </div>
          </div>
          <div v-if="notificationsLoading && notifications.length === 0" class="space-y-2 pt-1">
            <div v-for="n in 3" :key="`notif-skel-${n}`" class="skeleton-card" />
          </div>
          <div v-else-if="notificationsError" class="error-banner">
            <svg class="w-4 h-4 shrink-0 mt-px" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="1.7"><path stroke-linecap="round" stroke-linejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z"/></svg>
            <div class="flex-1 min-w-0">
              <div>{{ notificationsError }}</div>
              <button @click="fetchNotifications" class="text-[11px] mt-1 underline cursor-pointer" style="color: #b42318;">重试</button>
            </div>
          </div>
          <div v-else-if="notifications.length === 0" class="empty-state">
            <svg class="w-10 h-10 mb-2.5" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="1.4" style="color: var(--theme-300);">
              <path stroke-linecap="round" stroke-linejoin="round" d="M14.857 17.082a23.848 23.848 0 005.454-1.31A8.967 8.967 0 0118 9.75v-.7V9A6 6 0 006 9v.75a8.967 8.967 0 01-2.312 6.022c1.733.64 3.56 1.085 5.455 1.31m5.714 0a24.255 24.255 0 01-5.714 0m5.714 0a3 3 0 11-5.714 0"/>
            </svg>
            <div class="empty-title">收件箱是空的</div>
            <div class="empty-hint">Cron / Hook / Agent 异步通知会出现在这里</div>
          </div>
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
        style="background: var(--theme-50); border-color: rgba(255,255,255,0.24);"
        @click.stop
      >
        <div class="flex items-center justify-between gap-3 px-4 py-3 border-b" style="border-color: var(--theme-200);">
          <div class="min-w-0">
            <div class="text-[14px] font-semibold truncate" style="color: var(--theme-700);">
              {{ selectedSkillName || 'Skill' }}
            </div>
            <div v-if="selectedSkillMeta?.description" class="text-[11px] truncate mt-0.5" style="color: var(--theme-400);">
              {{ selectedSkillMeta.description }}
            </div>
          </div>
          <button
            class="w-8 h-8 rounded-md flex items-center justify-center cursor-pointer transition-colors hover:bg-black/[0.05] shrink-0"
            style="color: var(--theme-400);"
            title="关闭"
            @click="closeSkillBrowser"
          >
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="1.8">
              <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12"/>
            </svg>
          </button>
        </div>

        <div class="flex-1 overflow-auto p-4">
          <div class="rounded-xl border p-2 mb-3" style="border-color: var(--theme-200); background: rgba(255,255,255,0.88);">
            <div class="flex items-center gap-1.5 flex-wrap">
              <button
                class="w-7 h-7 rounded-md flex items-center justify-center cursor-pointer transition-colors hover:bg-black/[0.04]"
                :disabled="!skillBrowserCanGoUp"
                :style="skillBrowserCanGoUp ? 'color: var(--theme-500);' : 'color: var(--theme-300);'"
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
                style="color: var(--theme-500);"
                @click="openSkillBrowserBreadcrumb(crumb.path)"
              >
                {{ crumb.name }}
              </button>
            </div>
          </div>

          <div v-if="loadingSkillBrowser" class="text-center py-8 text-[12px]" style="color: var(--theme-300);">
            加载中…
          </div>
          <div
            v-else-if="skillBrowserError"
            class="rounded-lg px-3 py-2 text-[13px]"
            style="background: #fff4f4; color: #b42318; border: 1px solid #ffd7d7;"
          >
            {{ skillBrowserError }}
          </div>
          <div v-else-if="skillBrowserEntries.length === 0" class="text-center py-10 text-[12px]" style="color: var(--theme-300);">
            当前目录是空的
          </div>
          <div v-else class="space-y-1">
            <button
              v-for="entry in skillBrowserEntries"
              :key="`${selectedSkillName}-${entry.path}`"
              class="card-item w-full flex items-start gap-2.5 px-3 py-2 rounded-lg text-left cursor-pointer relative"
              :class="{ 'is-selected': skillBrowserSelectedPath === entry.path }"
              @click="selectSkillBrowserEntry(entry)"
              @dblclick="openSkillBrowserEntry(entry)"
            >
              <EntryIcon :entry="entry" class="mt-0.5" />

              <div class="min-w-0 flex-1">
                <div class="flex items-center gap-2 min-w-0">
                  <span class="text-[13px] truncate font-medium" style="color: var(--theme-700);">{{ entry.name }}</span>
                                  </div>
                <div class="text-[11px] mt-0.5" style="color: var(--theme-300);">
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
        style="background: var(--theme-50); border-color: rgba(255,255,255,0.24);"
        @click.stop
      >
        <div class="flex items-center justify-between gap-3 px-4 py-3 border-b" style="border-color: var(--theme-200);">
          <div class="min-w-0">
            <div class="text-[14px] font-semibold truncate" style="color: var(--theme-700);">
              {{ workspacePreview?.name || 'Preview' }}
            </div>
            <div class="text-[11px] truncate mt-0.5" style="color: var(--theme-400);">
              {{ workspacePreview?.display_path }}
            </div>
          </div>
          <div class="flex items-center gap-3 shrink-0">
            <span v-if="workspacePreviewMeta" class="text-[11px]" style="color: var(--theme-400);">
              {{ workspacePreviewMeta }}
            </span>
            <button
              class="w-8 h-8 rounded-md flex items-center justify-center cursor-pointer transition-colors hover:bg-black/[0.05]"
              style="color: var(--theme-400);"
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
          <div v-if="loadingWorkspacePreview" class="text-center py-10 text-[13px]" style="color: var(--theme-400);">加载预览…</div>
          <div v-else-if="workspacePreviewError" class="rounded-lg px-3 py-2 text-[13px]" style="background: #fff4f4; color: #b42318; border: 1px solid #ffd7d7;">
            {{ workspacePreviewError }}
          </div>
          <template v-else-if="workspacePreview">
            <pre
              v-if="workspacePreview.preview_type === 'text'"
              class="rounded-xl p-4 whitespace-pre-wrap break-words min-h-[240px]"
              style="background: #fff; color: var(--theme-700); font-size: 12px; line-height: 1.6; font-family: var(--ai-font-mono);"
            >{{ workspacePreview.content }}</pre>
            <img
              v-else-if="workspacePreview.preview_type === 'image'"
              :src="workspacePreview.data_url"
              :alt="workspacePreview.name"
              class="max-w-full max-h-[75vh] mx-auto rounded-xl border bg-white"
              style="border-color: var(--theme-200);"
            />
            <iframe
              v-else-if="workspacePreview.preview_type === 'pdf'"
              :src="workspacePreview.data_url"
              class="w-full h-[75vh] rounded-xl border bg-white"
              style="border-color: var(--theme-200);"
            ></iframe>
            <div v-else class="rounded-xl p-4 text-[13px]" style="background: #fff; color: var(--theme-500); border: 1px solid var(--theme-200);">
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

  <!-- Mobile backdrop for panel -->
  <Transition name="fade">
    <div
      v-if="visible && isMobile"
      class="fixed inset-0 bg-black/40 z-[35] lg:hidden"
      @click="emit('close')"
    ></div>
  </Transition>
</template>

<style scoped>
.panel-shell {
  position: relative;
  height: 100dvh;
  background: var(--theme-50);
  border-left: 1px solid var(--theme-200);
  font-family: var(--ai-font-body);
  container-type: inline-size;
}
.tab-label {
  display: inline;
}
/* Panel 自身宽度 < 360px 时收起 tab 文字，只剩图标 —— 不依赖 viewport */
@container (max-width: 359px) {
  .tab-label { display: none; }
  .tab-btn { padding-left: 6px; padding-right: 6px; }
}
@media (max-width: 1023px) {
  .panel-shell.panel-mobile {
    position: fixed;
    top: 0;
    right: 0;
    width: 85vw !important;
    min-width: 280px !important;
    max-width: 400px;
    z-index: 40;
    box-shadow: -8px 0 32px rgba(0,0,0,0.12);
  }
}
.is-refreshing svg {
  animation: refresh-spin 0.8s linear infinite;
}
@keyframes refresh-spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}
.tab-bar {
  border: 1px solid rgba(0, 0, 0, 0.04);
}
.tab-btn {
  color: var(--theme-400);
}
.tab-btn:hover:not(.tab-active) {
  color: var(--theme-500);
  background: rgba(255, 255, 255, 0.55);
}
.tab-btn.tab-active {
  background: #fff;
  color: var(--theme-700);
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.06), 0 0 0 0.5px rgba(0, 0, 0, 0.04);
}
.tab-btn.tab-active svg {
  color: var(--ai-accent);
}

/* List items */
.row-item {
  transition: background-color 0.15s ease;
}
.row-item:hover {
  background: rgba(0, 0, 0, 0.025);
}
.card-item {
  background: #fff;
  border: 1px solid var(--theme-200);
  transition: background-color 0.15s ease, border-color 0.15s ease, box-shadow 0.15s ease, transform 0.15s ease;
}
.card-item:hover {
  border-color: rgba(0, 0, 0, 0.09);
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
}
.card-item.is-selected {
  background: rgba(61, 124, 201, 0.06);
  border-color: rgba(61, 124, 201, 0.28);
  box-shadow: 0 1px 3px rgba(61, 124, 201, 0.08);
}
.card-item.is-selected::before {
  content: '';
  position: absolute;
  left: -1px;
  top: 8px;
  bottom: 8px;
  width: 2px;
  border-radius: 2px;
  background: var(--ai-accent);
}

/* Toggle pill */
.toggle-pill {
  padding: 3px 8px;
  border-radius: 999px;
  background: rgba(0, 0, 0, 0.04);
  color: var(--theme-300);
  border: 1px solid transparent;
}
.toggle-pill:hover {
  background: rgba(0, 0, 0, 0.06);
}
.toggle-pill.is-on {
  background: rgba(61, 124, 201, 0.1);
  color: var(--ai-accent);
  border-color: rgba(61, 124, 201, 0.18);
}

/* Section label */
.section-label {
  padding: 8px 12px 4px;
  font-size: 10.5px;
  font-weight: 600;
  color: var(--theme-400);
  letter-spacing: 0.04em;
  text-transform: uppercase;
}

/* Empty state */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 36px 16px 28px;
  text-align: center;
}
.empty-title {
  font-size: 13px;
  font-weight: 500;
  color: var(--theme-500);
  margin-bottom: 4px;
}
.empty-hint {
  font-size: 11.5px;
  color: var(--theme-400);
  line-height: 1.5;
  max-width: 220px;
}

/* Skeleton */
.skeleton-row,
.skeleton-card {
  border-radius: 10px;
  background: linear-gradient(
    90deg,
    rgba(0, 0, 0, 0.035) 0%,
    rgba(0, 0, 0, 0.06) 50%,
    rgba(0, 0, 0, 0.035) 100%
  );
  background-size: 200% 100%;
  animation: skeleton-shimmer 1.6s ease-in-out infinite;
}
.skeleton-row { height: 32px; }
.skeleton-card { height: 48px; }
@keyframes skeleton-shimmer {
  0% { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}

/* Error banner */
.error-banner {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  margin-bottom: 12px;
  padding: 10px 12px;
  border-radius: 10px;
  background: #fff4f4;
  color: #b42318;
  border: 1px solid #ffd7d7;
  font-size: 12.5px;
  line-height: 1.5;
}

/* Icon button (e.g. folder shortcut on skill cards) */
.icon-btn {
  width: 24px;
  height: 24px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 6px;
  color: var(--theme-400);
  background: transparent;
}
.icon-btn:hover {
  background: rgba(0, 0, 0, 0.05);
  color: var(--ai-accent);
}

/* Files header */
.files-header {
  background: rgba(255, 255, 255, 0.92);
  border: 1px solid var(--theme-200);
}
.root-chip {
  background: transparent;
  color: var(--theme-500);
  border: 1px solid transparent;
}
.root-chip:hover {
  background: rgba(0, 0, 0, 0.035);
}
.root-chip.is-active {
  background: var(--theme-700, #1a1a1a);
  color: var(--theme-50, #fafafa);
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
}

/* Resize handle grip */
.resize-handle::before {
  content: '';
  position: absolute;
  top: 50%;
  left: 1.5px;
  width: 4px;
  height: 36px;
  margin-top: -18px;
  border-radius: 4px;
  background: rgba(0, 0, 0, 0.08);
  opacity: 0;
  transition: opacity 0.18s ease;
}
.resize-handle:hover::before,
.resizing .resize-handle::before {
  opacity: 1;
}

/* Custom scrollbar for panel body */
.panel-body::-webkit-scrollbar {
  width: 6px;
}
.panel-body::-webkit-scrollbar-track {
  background: transparent;
}
.panel-body::-webkit-scrollbar-thumb {
  background: rgba(0, 0, 0, 0.1);
  border-radius: 3px;
}
.panel-body::-webkit-scrollbar-thumb:hover {
  background: rgba(0, 0, 0, 0.2);
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
.fade-enter-active, .fade-leave-active {
  transition: opacity 0.2s ease;
}
.fade-enter-from, .fade-leave-to {
  opacity: 0;
}
</style>
