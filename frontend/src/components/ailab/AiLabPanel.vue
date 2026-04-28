<script setup>
import { ref, computed, onMounted } from 'vue'
import { HERMES_API_URL, HERMES_API_KEY } from '../../config/api'

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

const headers = { 'Authorization': `Bearer ${HERMES_API_KEY}`, 'Content-Type': 'application/json' }

const fetchTools = async () => {
  loadingTools.value = true
  try {
    const r = await fetch(`${HERMES_API_URL}/api/tools`, { headers })
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
      method: 'POST', headers,
      body: JSON.stringify({ name: tool.name, enable: !tool.enabled })
    })
    tool.enabled = !tool.enabled
  } catch (e) { console.error('Failed to toggle tool:', e) }
}

const fetchSkills = async () => {
  loadingSkills.value = true
  try {
    const r = await fetch(`${HERMES_API_URL}/api/skills`, { headers })
    if (r.ok) {
      const data = await r.json()
      skills.value = data.skills || []
    }
  } catch (e) { console.error('Failed to fetch skills:', e) }
  finally { loadingSkills.value = false }
}

const fetchMemory = async () => {
  loadingMemory.value = true
  try {
    const r = await fetch(`${HERMES_API_URL}/api/memory`, { headers })
    if (r.ok) {
      const data = await r.json()
      memory.value = data.memory || ''
      userProfile.value = data.user_profile || ''
    }
  } catch (e) { console.error('Failed to fetch memory:', e) }
  finally { loadingMemory.value = false }
}

const startEditMemory = () => {
  memoryDraft.value = memory.value
  editingMemory.value = true
}

const saveMemory = async () => {
  try {
    await fetch(`${HERMES_API_URL}/api/memory`, {
      method: 'POST', headers,
      body: JSON.stringify({ memory: memoryDraft.value })
    })
    memory.value = memoryDraft.value
    editingMemory.value = false
  } catch (e) { console.error('Failed to save memory:', e) }
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

const loadTab = (tab) => {
  activeTab.value = tab
  if (tab === 'tools' && tools.value.length === 0) fetchTools()
  if (tab === 'skills' && skills.value.length === 0) fetchSkills()
  if (tab === 'memory') fetchMemory()
}

onMounted(() => { if (props.visible) fetchTools() })

defineExpose({ refreshMemory: fetchMemory })
</script>

<template>
  <Transition name="slide">
    <div v-if="visible" class="flex flex-col" style="width: 320px; min-width: 320px; height: 100dvh; background: #f7f7f8; border-left: 1px solid #ebebed; font-family: var(--ai-font-body);">
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
        <button v-for="tab in ['tools', 'skills', 'memory']" :key="tab"
          @click="loadTab(tab)"
          class="px-3 py-1 rounded-md text-[12px] font-medium transition-colors cursor-pointer"
          :style="activeTab === tab ? 'background: #fff; color: #2c2c30; box-shadow: 0 1px 2px rgba(0,0,0,0.05);' : 'color: #9a9aa0;'">
          {{ tab === 'tools' ? 'Tools' : tab === 'skills' ? 'Skills' : 'Memory' }}
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
                    <span class="text-[13px] truncate" :style="tool.enabled ? 'color: #2c2c30;' : 'color: #b0b0b6;'">{{ tool.name }}</span>
                  </div>
                  <button @click="toggleTool(tool)" class="shrink-0 ml-2 cursor-pointer px-2 py-0.5 rounded text-[11px] transition-colors"
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
                <span class="text-[13px]" style="color: #2c2c30;">{{ tool.name }}</span>
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
                  <span class="text-[13px] truncate" :style="skill.enabled ? 'color: #2c2c30;' : 'color: #b0b0b6;'">{{ skill.name }}</span>
                  <span class="text-[11px] shrink-0" :style="skill.enabled ? 'color: #9a9aa0;' : 'color: #d1d1d6;'">
                    {{ skill.enabled ? 'on' : 'off' }}
                  </span>
                </div>
              </div>
            </div>
          </template>
        </template>

        <!-- Memory Tab -->
        <template v-if="activeTab === 'memory'">
          <div v-if="loadingMemory" class="text-center py-8" style="color: #9a9aa0; font-size: 13px;">加载中…</div>
          <template v-else>
            <!-- MEMORY.md -->
            <div class="mb-4">
              <div class="flex items-center justify-between mb-2">
                <span class="text-[12px] font-semibold" style="color: #6e6e76;">MEMORY.md</span>
                <button v-if="!editingMemory" @click="startEditMemory"
                  class="text-[11px] px-2 py-0.5 rounded-md cursor-pointer transition-colors"
                  style="color: var(--ai-accent); border: 1px solid var(--ai-accent-soft);">编辑</button>
                <div v-else class="flex gap-1">
                  <button @click="saveMemory" class="text-[11px] px-2 py-0.5 rounded-md cursor-pointer" style="background: var(--theme-700); color: #fff;">保存</button>
                  <button @click="editingMemory = false" class="text-[11px] px-2 py-0.5 rounded-md cursor-pointer" style="color: #9a9aa0;">取消</button>
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
                <span class="text-[12px] font-semibold" style="color: #6e6e76;">USER.md</span>
                <span class="text-[10px] ml-2" style="color: #b0b0b6;">agent 自动维护</span>
              </div>
              <pre class="rounded-lg p-3 whitespace-pre-wrap break-words"
                style="background: #fff; color: #2c2c30; font-size: 12px; line-height: 1.6; min-height: 60px; font-family: var(--ai-font-mono);">{{ userProfile || '(空)' }}</pre>
            </div>
          </template>
        </template>
      </div>
    </div>
  </Transition>
</template>

<style scoped>
.slide-enter-active, .slide-leave-active {
  transition: all 0.25s ease;
}
.slide-enter-from, .slide-leave-to {
  transform: translateX(100%);
  opacity: 0;
}
</style>
