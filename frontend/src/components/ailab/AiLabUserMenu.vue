<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../../store/auth'
import API_BASE_URL from '../../config/api'

const router = useRouter()
const authStore = useAuthStore()

const open = ref(false)
const me = ref(null)
const wrapperRef = ref(null)
// 'menu' | 'stats' — 控制面板内显示哪个视图
const view = ref('menu')

const stats = ref(null)
const statsLoading = ref(false)
let statsTimer = null

const headers = () => {
  const t = localStorage.getItem('access_token') || ''
  const h = { 'Content-Type': 'application/json' }
  if (t) h['Authorization'] = `Bearer ${t}`
  return h
}

const fetchMe = async () => {
  try {
    const r = await fetch(`${API_BASE_URL}/api/ai/me/`, { headers: headers() })
    if (r.ok) me.value = await r.json()
  } catch { /* silent */ }
}

const fetchStats = async ({ silent = false } = {}) => {
  if (!silent) statsLoading.value = true
  try {
    const r = await fetch(`${API_BASE_URL}/api/ai/conversations/stats/`, { headers: headers() })
    if (r.ok) stats.value = await r.json()
  } catch { /* silent */ } finally {
    statsLoading.value = false
  }
}

const startStatsAutoRefresh = () => {
  stopStatsAutoRefresh()
  statsTimer = setInterval(() => fetchStats({ silent: true }), 5000)
}
const stopStatsAutoRefresh = () => {
  if (statsTimer) {
    clearInterval(statsTimer)
    statsTimer = null
  }
}

watch(view, (v) => {
  if (v === 'stats') {
    fetchStats()
    startStatsAutoRefresh()
  } else {
    stopStatsAutoRefresh()
  }
})

watch(open, (v) => {
  if (!v) {
    view.value = 'menu'
    stopStatsAutoRefresh()
  }
})

const formatNumber = (n) => {
  const v = Number(n) || 0
  if (v < 1000) return String(v)
  if (v < 1_000_000) return `${(v / 1000).toFixed(v < 10_000 ? 2 : 1)}K`
  if (v < 1_000_000_000) return `${(v / 1_000_000).toFixed(2)}M`
  return `${(v / 1_000_000_000).toFixed(2)}B`
}

const formatRelative = (iso) => {
  if (!iso) return '—'
  const t = new Date(iso).getTime()
  if (isNaN(t)) return '—'
  const diff = Math.max(0, Date.now() - t)
  const sec = Math.floor(diff / 1000)
  if (sec < 60) return '刚刚'
  const min = Math.floor(sec / 60)
  if (min < 60) return `${min} 分钟前`
  const hr = Math.floor(min / 60)
  if (hr < 24) return `${hr} 小时前`
  const day = Math.floor(hr / 24)
  if (day < 30) return `${day} 天前`
  return new Date(iso).toLocaleDateString('zh-CN')
}

const totalTokensLabel = computed(() => formatNumber(stats.value?.total_tokens))
const promptTokensLabel = computed(() => formatNumber(stats.value?.total_prompt_tokens))
const completionTokensLabel = computed(() => formatNumber(stats.value?.total_completion_tokens))
const promptCompletionRatio = computed(() => {
  const p = Number(stats.value?.total_prompt_tokens) || 0
  const c = Number(stats.value?.total_completion_tokens) || 0
  const sum = p + c
  if (!sum) return { p: 0, c: 0 }
  return { p: (p / sum) * 100, c: (c / sum) * 100 }
})

const initials = computed(() => {
  const name = me.value?.nickname || me.value?.username || me.value?.email || '?'
  // 中文取第一个字、英文取首字母
  const ch = name.trim().charAt(0)
  return ch.toUpperCase()
})

const displayName = computed(() => me.value?.nickname || me.value?.email || me.value?.username || '')

const handleLogout = () => {
  authStore.logout()
  router.push('/login')
}

const goInvites = () => {
  open.value = false
  router.push('/ai-lab/admin/invites')
}

const goStats = () => {
  view.value = 'stats'
}

const backToMenu = () => {
  view.value = 'menu'
}

const handleOutsideClick = (e) => {
  if (!wrapperRef.value) return
  if (!wrapperRef.value.contains(e.target)) open.value = false
}

defineExpose({ refresh: fetchMe, me, refreshStats: () => fetchStats({ silent: true }) })

onMounted(() => {
  fetchMe()
  document.addEventListener('click', handleOutsideClick)
})
onUnmounted(() => {
  document.removeEventListener('click', handleOutsideClick)
  stopStatsAutoRefresh()
})
</script>

<template>
  <div ref="wrapperRef" class="relative inline-block">
    <button
      @click.stop="open = !open"
      class="w-8 h-8 rounded-full flex items-center justify-center transition-all cursor-pointer relative overflow-hidden"
      :style="open
        ? 'background: var(--theme-700); color: var(--theme-50); border: 1px solid var(--theme-700);'
        : 'background: #fff; color: var(--theme-700); border: 1px solid var(--theme-300);'"
      :title="displayName"
    >
      <img v-if="me?.avatar_url" :src="me.avatar_url" class="w-full h-full object-cover" />
      <span v-else class="text-[12px] font-semibold tracking-tight">{{ initials }}</span>
      <span
        v-if="me?.is_owner"
        class="absolute -bottom-0.5 -right-0.5 w-2.5 h-2.5 rounded-full"
        style="background: var(--ai-accent, #3d7cc9); border: 1.5px solid #fff;"
        title="Owner"
      ></span>
    </button>

    <Transition name="panel">
      <div
        v-if="open"
        class="absolute right-0 top-full mt-1.5 w-[280px] rounded-xl shadow-lg overflow-hidden z-50"
        style="background: var(--theme-50); border: 1px solid var(--theme-200);"
        @click.stop
      >
        <!-- ===== 视图：菜单（默认） ===== -->
        <template v-if="view === 'menu'">
          <!-- 身份头部 -->
          <div class="px-4 pt-3 pb-2.5" style="border-bottom: 1px solid var(--theme-100);">
            <div class="flex items-center gap-2.5">
              <div
                class="w-9 h-9 rounded-full flex items-center justify-center overflow-hidden shrink-0"
                style="background: var(--theme-100);"
              >
                <img v-if="me?.avatar_url" :src="me.avatar_url" class="w-full h-full object-cover" />
                <span v-else class="text-[14px] font-semibold" style="color: var(--theme-600);">{{ initials }}</span>
              </div>
              <div class="min-w-0">
                <div class="text-[14px] font-semibold truncate" style="color: var(--theme-700);">
                  {{ displayName }}
                </div>
                <div class="flex items-center gap-1.5 mt-0.5">
                  <span
                    v-if="me?.is_owner"
                    class="text-[10px] font-semibold px-1.5 py-0.5 rounded uppercase tracking-wide"
                    style="background: var(--ai-accent, #3d7cc9); color: #fff;"
                  >Owner</span>
                  <span
                    v-else-if="me?.ai_lab_enabled"
                    class="text-[10px] font-medium px-1.5 py-0.5 rounded"
                    style="background: var(--theme-100); color: var(--theme-500);"
                  >已开通</span>
                  <span
                    v-else
                    class="text-[10px] font-medium px-1.5 py-0.5 rounded"
                    style="background: #fff4e0; color: #b45309;"
                  >未开通</span>
                </div>
              </div>
            </div>
          </div>

          <!-- 菜单项 -->
          <div class="py-1">
            <button
              @click="goStats"
              class="w-full px-4 py-2 flex items-center gap-2 text-left text-[13px] cursor-pointer transition-colors hover:bg-[var(--theme-100)]"
              style="color: var(--theme-600);"
            >
              <svg class="w-4 h-4 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="1.6">
                <path stroke-linecap="round" stroke-linejoin="round" d="M3 13.125C3 12.504 3.504 12 4.125 12h2.25c.621 0 1.125.504 1.125 1.125v6.75C7.5 20.496 6.996 21 6.375 21h-2.25A1.125 1.125 0 013 19.875v-6.75zM9.75 8.625c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125v11.25c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V8.625zM16.5 4.125c0-.621.504-1.125 1.125-1.125h2.25C20.496 3 21 3.504 21 4.125v15.75c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V4.125z"/>
              </svg>
              <span class="flex-1">用量统计</span>
              <svg class="w-3.5 h-3.5 opacity-60" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M8.25 4.5l7.5 7.5-7.5 7.5"/>
              </svg>
            </button>
            <button
              v-if="me?.is_owner"
              @click="goInvites"
              class="w-full px-4 py-2 flex items-center gap-2 text-left text-[13px] cursor-pointer transition-colors hover:bg-[var(--theme-100)]"
              style="color: var(--theme-600);"
            >
              <svg class="w-4 h-4 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="1.6">
                <path stroke-linecap="round" stroke-linejoin="round" d="M15 19.128a9.38 9.38 0 002.625.372 9.337 9.337 0 004.121-.952 4.125 4.125 0 00-7.533-2.493M15 19.128v-.003c0-1.113-.285-2.16-.786-3.07M15 19.128v.106A12.318 12.318 0 018.624 21c-2.331 0-4.512-.645-6.374-1.766l-.001-.109a6.375 6.375 0 0111.964-3.07M12 6.375a3.375 3.375 0 11-6.75 0 3.375 3.375 0 016.75 0zm8.25 2.25a2.625 2.625 0 11-5.25 0 2.625 2.625 0 015.25 0z"/>
              </svg>
              邀请码管理
            </button>
            <button
              @click="handleLogout"
              class="w-full px-4 py-2 flex items-center gap-2 text-left text-[13px] cursor-pointer transition-colors hover:bg-[var(--theme-100)]"
              style="color: var(--theme-600);"
            >
              <svg class="w-4 h-4 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="1.6">
                <path stroke-linecap="round" stroke-linejoin="round" d="M15.75 9V5.25A2.25 2.25 0 0013.5 3h-6a2.25 2.25 0 00-2.25 2.25v13.5A2.25 2.25 0 007.5 21h6a2.25 2.25 0 002.25-2.25V15m3 0l3-3m0 0l-3-3m3 3H9"/>
              </svg>
              退出登录
            </button>
          </div>
        </template>

        <!-- ===== 视图：用量统计卡片 ===== -->
        <template v-else-if="view === 'stats'">
          <!-- 卡片头：返回按钮 + 标题 + 状态 -->
          <div class="px-3 pt-2.5 pb-2 flex items-center gap-1.5" style="border-bottom: 1px solid var(--theme-100);">
            <button
              @click="backToMenu"
              class="w-6 h-6 rounded-md flex items-center justify-center cursor-pointer transition-colors hover:bg-[var(--theme-100)]"
              style="color: var(--theme-500);"
              title="返回"
            >
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M15.75 19.5L8.25 12l7.5-7.5"/>
              </svg>
            </button>
            <span class="text-[13px] font-semibold flex-1" style="color: var(--theme-700);">用量统计</span>
            <span
              class="flex items-center gap-1 text-[10px]"
              style="color: var(--theme-400);"
              :title="statsLoading ? '加载中…' : '每 5 秒刷新'"
            >
              <span
                class="w-1.5 h-1.5 rounded-full"
                :style="{ background: statsLoading ? '#f59e0b' : '#10b981' }"
              ></span>
              {{ statsLoading ? '加载中' : '实时' }}
            </span>
          </div>

          <!-- 总 Tokens 大数字 + 输入/输出占比条 -->
          <div class="px-4 pt-3 pb-3">
            <div class="text-[10px] font-semibold tracking-wide uppercase" style="color: var(--theme-400);">
              累计 Tokens
            </div>
            <div class="flex items-baseline gap-1.5 mt-0.5">
              <span class="text-[24px] font-semibold font-mono leading-none" style="color: var(--theme-700);">
                {{ totalTokensLabel }}
              </span>
              <span class="text-[11px]" style="color: var(--theme-400);">
                跨 {{ stats?.session_count || 0 }} 个会话
              </span>
            </div>

            <!-- 输入/输出占比堆叠条 -->
            <div class="mt-2.5 h-1.5 rounded-full overflow-hidden flex" style="background: var(--theme-200);">
              <div
                class="h-full transition-all duration-500"
                :style="{ width: `${promptCompletionRatio.p}%`, background: 'var(--ai-accent, #3d7cc9)' }"
                title="输入"
              ></div>
              <div
                class="h-full transition-all duration-500"
                :style="{ width: `${promptCompletionRatio.c}%`, background: '#16a34a' }"
                title="输出"
              ></div>
            </div>
            <div class="flex items-center justify-between mt-1.5 text-[11px]">
              <span class="flex items-center gap-1" style="color: var(--theme-500);">
                <span class="w-1.5 h-1.5 rounded-full" style="background: var(--ai-accent, #3d7cc9);"></span>
                输入 <span class="font-mono" style="color: var(--theme-700);">{{ promptTokensLabel }}</span>
              </span>
              <span class="flex items-center gap-1" style="color: var(--theme-500);">
                <span class="w-1.5 h-1.5 rounded-full" style="background: #16a34a;"></span>
                输出 <span class="font-mono" style="color: var(--theme-700);">{{ completionTokensLabel }}</span>
              </span>
            </div>
          </div>

          <!-- 明细 -->
          <div class="px-4 py-2.5 space-y-1" style="border-top: 1px solid var(--theme-100); background: var(--theme-100);">
            <div class="flex items-center justify-between text-[12px]">
              <span style="color: var(--theme-500);">总轮次</span>
              <span class="font-mono" style="color: var(--theme-700);">{{ stats?.total_turns || 0 }}</span>
            </div>
            <div class="flex items-center justify-between text-[12px]">
              <span style="color: var(--theme-500);">活跃会话</span>
              <span class="font-mono" style="color: var(--theme-700);">
                {{ stats?.active_session_count || 0 }} / {{ stats?.session_count || 0 }}
              </span>
            </div>
            <div class="flex items-center justify-between text-[12px]">
              <span style="color: var(--theme-500);">最近活跃</span>
              <span class="font-mono" style="color: var(--theme-700);">{{ formatRelative(stats?.last_active) }}</span>
            </div>
          </div>
        </template>
      </div>
    </Transition>
  </div>
</template>

<style scoped>
.panel-enter-active, .panel-leave-active { transition: opacity 0.15s ease, transform 0.15s ease; }
.panel-enter-from, .panel-leave-to { opacity: 0; transform: translateY(-4px); }
.panel-enter-to, .panel-leave-from { opacity: 1; transform: translateY(0); }
</style>
