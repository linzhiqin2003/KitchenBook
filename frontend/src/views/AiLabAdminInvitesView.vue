<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import API_BASE_URL from '../config/api'

const router = useRouter()
const me = ref(null)
const invites = ref([])
const loading = ref(false)
const newNote = ref('')
const generating = ref(false)
const error = ref('')

const headers = () => {
  const t = localStorage.getItem('access_token') || ''
  const h = { 'Content-Type': 'application/json' }
  if (t) h['Authorization'] = `Bearer ${t}`
  return h
}

const fetchMe = async () => {
  const r = await fetch(`${API_BASE_URL}/api/ai/me/`, { headers: headers() })
  if (!r.ok) throw new Error('me')
  me.value = await r.json()
  if (!me.value.is_owner) router.replace('/ai-lab')
}

const fetchInvites = async () => {
  loading.value = true
  try {
    const r = await fetch(`${API_BASE_URL}/api/ai/invites/`, { headers: headers() })
    if (!r.ok) throw new Error(`HTTP ${r.status}`)
    const data = await r.json()
    invites.value = data.results || []
  } catch (e) {
    error.value = e.message
  } finally {
    loading.value = false
  }
}

const generate = async () => {
  generating.value = true
  error.value = ''
  try {
    const r = await fetch(`${API_BASE_URL}/api/ai/invites/`, {
      method: 'POST', headers: headers(),
      body: JSON.stringify({ note: newNote.value.trim() })
    })
    if (!r.ok) {
      const d = await r.json().catch(() => ({}))
      throw new Error(d.error || `HTTP ${r.status}`)
    }
    newNote.value = ''
    await fetchInvites()
  } catch (e) {
    error.value = e.message
  } finally {
    generating.value = false
  }
}

const copyCode = async (code) => {
  try {
    await navigator.clipboard.writeText(code)
  } catch { /* silent */ }
}

const fmtTime = (iso) => {
  if (!iso) return '—'
  const d = new Date(iso)
  return `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')} ${String(d.getHours()).padStart(2,'0')}:${String(d.getMinutes()).padStart(2,'0')}`
}

onMounted(async () => {
  try {
    await fetchMe()
    await fetchInvites()
  } catch {
    router.replace('/ai-lab')
  }
})
</script>

<template>
  <div class="min-h-screen px-4 py-10" style="background: var(--theme-50, #f8f8f6);">
    <div class="max-w-3xl mx-auto">
      <div class="flex items-center justify-between mb-6">
        <div>
          <h1 class="text-[22px] font-semibold tracking-tight" style="color: var(--theme-700);">邀请码管理</h1>
          <p class="text-[13px] mt-1" style="color: var(--theme-500);">生成邀请码分发给信任的访客，他们用码激活后才能使用 MyAgent。</p>
        </div>
        <router-link to="/ai-lab" class="text-[13px] cursor-pointer" style="color: var(--theme-500);">← 返回 MyAgent</router-link>
      </div>

      <!-- 生成新码 -->
      <div class="rounded-xl px-5 py-4 mb-6" style="background: #fff; border: 1px solid var(--theme-200);">
        <label class="block text-[12px] font-medium mb-2" style="color: var(--theme-500);">备注（给谁用，可选）</label>
        <div class="flex gap-2">
          <input
            v-model="newNote"
            type="text"
            placeholder="例如 给 Alice"
            @keyup.enter="generate"
            :disabled="generating"
            class="flex-1 px-3 py-2 rounded-lg outline-none"
            style="border: 1px solid var(--theme-200); background: var(--theme-50); font-size: 13px; color: var(--theme-700);"
          />
          <button
            @click="generate"
            :disabled="generating"
            class="px-4 py-2 rounded-lg text-[13px] font-medium cursor-pointer disabled:opacity-50"
            style="background: var(--theme-700); color: var(--theme-50);"
          >{{ generating ? '生成中…' : '生成新码' }}</button>
        </div>
        <div v-if="error" class="mt-2 text-[12px]" style="color: #b91c1c;">{{ error }}</div>
      </div>

      <!-- 列表 -->
      <div class="rounded-xl overflow-hidden" style="background: #fff; border: 1px solid var(--theme-200);">
        <div v-if="loading" class="px-5 py-12 text-center text-[13px]" style="color: var(--theme-400);">加载中…</div>
        <div v-else-if="invites.length === 0" class="px-5 py-12 text-center text-[13px]" style="color: var(--theme-400);">暂无邀请码</div>
        <div v-else>
          <div class="grid grid-cols-12 gap-3 px-5 py-2 text-[11px] font-semibold uppercase tracking-wide" style="color: var(--theme-500); background: var(--theme-100); border-bottom: 1px solid var(--theme-200);">
            <div class="col-span-4">Code</div>
            <div class="col-span-3">备注</div>
            <div class="col-span-2">状态</div>
            <div class="col-span-3">使用者 / 时间</div>
          </div>
          <div
            v-for="it in invites"
            :key="it.id"
            class="grid grid-cols-12 gap-3 px-5 py-3 items-center text-[13px] transition-colors hover:bg-[var(--theme-50)]"
            style="border-bottom: 1px solid var(--theme-100);"
          >
            <div class="col-span-4 flex items-center gap-1.5">
              <code class="text-[12px] truncate" style="color: var(--theme-700); font-family: var(--ai-font-mono, ui-monospace, monospace);">{{ it.code }}</code>
              <button @click="copyCode(it.code)" class="text-[11px] cursor-pointer hover:underline" style="color: var(--theme-400);" title="复制">📋</button>
            </div>
            <div class="col-span-3 truncate" style="color: var(--theme-600);">{{ it.note || '—' }}</div>
            <div class="col-span-2">
              <span v-if="it.is_used" class="text-[11px] font-medium px-2 py-0.5 rounded" style="background: var(--theme-100); color: var(--theme-500);">已用</span>
              <span v-else-if="it.is_expired" class="text-[11px] font-medium px-2 py-0.5 rounded" style="background: #fef2f2; color: #b91c1c;">过期</span>
              <span v-else class="text-[11px] font-medium px-2 py-0.5 rounded" style="background: #ecfdf5; color: #047857;">未用</span>
            </div>
            <div class="col-span-3 text-[12px]" style="color: var(--theme-500);">
              <span v-if="it.used_by">{{ it.used_by }}<br/></span>
              <span class="text-[11px]" style="color: var(--theme-400);">{{ fmtTime(it.used_at || it.created_at) }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
