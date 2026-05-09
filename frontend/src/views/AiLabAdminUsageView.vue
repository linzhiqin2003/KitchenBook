<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import API_BASE_URL from '../config/api'
import AiLabUsageHeatmap from '../components/ailab/AiLabUsageHeatmap.vue'

const router = useRouter()
const me = ref(null)
const stats = ref(null)
const loading = ref(false)
const error = ref('')
const expanded = ref(new Set())
// per-visitor 详情面板状态：{uid: {tab: 'overview'|'models', range: 'all'|'30d'|'7d'}}
const detailState = ref({})

const detailFor = (uid) => {
  if (!detailState.value[uid]) {
    detailState.value[uid] = { tab: 'overview', range: 'all' }
  }
  return detailState.value[uid]
}
const setDetailTab = (uid, tab) => { detailFor(uid); detailState.value[uid].tab = tab }
const setDetailRange = (uid, range) => { detailFor(uid); detailState.value[uid].range = range }

// 按时间范围过滤 daily 数据 — 给 heatmap 显示用
const filterDaily = (daily, range) => {
  if (!Array.isArray(daily) || range === 'all') return daily || []
  const days = range === '7d' ? 6 : 29
  const today = new Date(); today.setHours(0,0,0,0)
  const start = new Date(today); start.setDate(start.getDate() - days)
  return daily.filter(d => new Date(d.date) >= start)
}

// 按时间范围算 stats 卡的衍生数字
const visitorWindowStats = (v, range) => {
  const list = filterDaily(v.daily, range)
  const tokens = list.reduce((a, d) => a + (d.tokens || 0), 0)
  const messages = list.reduce((a, d) => a + (d.messages || 0), 0)
  const sessions = list.reduce((a, d) => a + (d.sessions || 0), 0)
  const activeDays = list.filter(d => (d.tokens || 0) > 0).length
  return { tokens, messages, sessions, activeDays, days: list }
}

// 把 hour (0-23) 格式化成 "4 PM" / "2 AM"
const formatHour = (h) => {
  if (h === null || h === undefined) return '—'
  const n = Number(h)
  if (!isFinite(n)) return '—'
  if (n === 0) return '12 AM'
  if (n < 12)  return `${n} AM`
  if (n === 12) return '12 PM'
  return `${n - 12} PM`
}

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

const fetchStats = async ({ silent = false } = {}) => {
  if (!silent) loading.value = true
  error.value = ''
  try {
    const r = await fetch(`${API_BASE_URL}/api/ai/admin/visitor-stats/`, { headers: headers() })
    if (!r.ok) {
      const d = await r.json().catch(() => ({}))
      throw new Error(d.error || `HTTP ${r.status}`)
    }
    stats.value = await r.json()
  } catch (e) {
    error.value = e.message
  } finally {
    loading.value = false
  }
}

onMounted(async () => {
  try {
    await fetchMe()
    await fetchStats()
  } catch {
    router.replace('/ai-lab')
  }
})

const toggleExpand = (uid) => {
  const s = new Set(expanded.value)
  if (s.has(uid)) s.delete(uid)
  else s.add(uid)
  expanded.value = s
}

const isExpanded = (uid) => expanded.value.has(uid)

// ---- 格式化工具 ----
const formatNumber = (n) => {
  const v = Number(n) || 0
  if (v < 1000) return String(v)
  if (v < 1_000_000) return `${(v / 1000).toFixed(v < 10_000 ? 2 : 1)}K`
  if (v < 1_000_000_000) return `${(v / 1_000_000).toFixed(2)}M`
  return `${(v / 1_000_000_000).toFixed(2)}B`
}

const formatCost = (v) => {
  const n = Number(v)
  if (!isFinite(n) || n === 0) return '$0'
  if (n < 0.0001) return '< $0.0001'
  if (n < 0.01) return `$${n.toFixed(4)}`
  if (n < 1) return `$${n.toFixed(3)}`
  return `$${n.toFixed(2)}`
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

const formatDate = (iso) => {
  if (!iso) return '—'
  const d = new Date(iso)
  if (isNaN(d.getTime())) return '—'
  return `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')}`
}

const visitorDisplayName = (v) => v.nickname || v.username || v.email || `#${v.user_id}`

const visitorInitial = (v) => visitorDisplayName(v).trim().charAt(0).toUpperCase() || '?'

// 头像背景色：按 username hash 出一个稳定 hue，区分访客
const visitorHue = (v) => {
  const s = v.username || v.email || String(v.user_id)
  let h = 0
  for (let i = 0; i < s.length; i++) h = (h * 31 + s.charCodeAt(i)) % 360
  return h
}

const totals = computed(() => stats.value?.totals || null)
const visitors = computed(() => stats.value?.visitors || [])

// 用最大 total_tokens 作为各访客 bar 的归一基准
const maxVisitorTokens = computed(() => {
  const arr = visitors.value
  if (!arr.length) return 0
  return Math.max(...arr.map(v => v.total_tokens || 0))
})

// cache 命中率：cache / (cache + non_cache_input)
const cacheHitRatio = computed(() => {
  const t = totals.value
  if (!t) return 0
  const cache = Number(t.total_cache_tokens) || 0
  const prompt = Number(t.total_prompt_tokens) || 0
  if (!prompt) return 0
  return (Math.min(cache, prompt) / prompt) * 100
})

// 三段 token 占比（输入 / 缓存 / 输出），对应 input / cache / output 三种计费
const tokenSplit = computed(() => {
  const t = totals.value
  if (!t) return { input: 0, cache: 0, output: 0 }
  const inp = Number(t.non_cache_input_tokens) || 0
  const cache = Number(t.total_cache_tokens) || 0
  const out = Number(t.total_completion_tokens) || 0
  const sum = inp + cache + out
  if (!sum) return { input: 0, cache: 0, output: 0 }
  return {
    input: (inp / sum) * 100,
    cache: (cache / sum) * 100,
    output: (out / sum) * 100,
  }
})
</script>

<template>
  <div class="min-h-screen px-4 py-10" style="background: var(--theme-50, #f8f8f6);">
    <div class="max-w-5xl mx-auto">
      <!-- Header -->
      <header class="usage-header">
        <div class="usage-header__title">
          <router-link to="/ai-lab" class="usage-header__back" title="返回 MyAgent">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M19 12H5M12 19l-7-7 7-7"/>
            </svg>
          </router-link>
          <div class="usage-header__heading">
            <h1>访客用量</h1>
            <p>MyAgent 访客的使用情况与日活、token、cost 拆分。</p>
          </div>
        </div>
        <div class="usage-header__actions">
          <button
            @click="fetchStats({ silent: false })"
            :disabled="loading"
            class="usage-btn usage-btn--icon"
            :class="{ 'is-loading': loading }"
            title="刷新数据"
          >
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M3 12a9 9 0 0 1 15-6.7L21 8"/>
              <polyline points="21 3 21 8 16 8"/>
              <path d="M21 12a9 9 0 0 1-15 6.7L3 16"/>
              <polyline points="3 21 3 16 8 16"/>
            </svg>
            <span>{{ loading ? '刷新中' : '刷新' }}</span>
          </button>
          <router-link to="/ai-lab/admin/invites" class="usage-btn usage-btn--ghost">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
              <path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/>
              <circle cx="9" cy="7" r="4"/>
              <line x1="19" y1="8" x2="19" y2="14"/>
              <line x1="22" y1="11" x2="16" y2="11"/>
            </svg>
            <span>邀请码</span>
          </router-link>
        </div>
      </header>

      <div v-if="error" class="mb-4 px-4 py-3 rounded-lg text-[13px]" style="background: #fef2f2; color: #b91c1c; border: 1px solid #fecaca;">
        加载失败：{{ error }}
      </div>

      <!-- 总览卡片 -->
      <section v-if="totals" class="grid grid-cols-2 md:grid-cols-4 gap-3 mb-6">
        <div class="rounded-xl px-4 py-3.5" style="background: #fff; border: 1px solid var(--theme-200);">
          <div class="text-[11px] uppercase tracking-wide font-semibold" style="color: var(--theme-400);">访客</div>
          <div class="mt-1 flex items-baseline gap-1.5">
            <span class="text-[22px] font-semibold tabular-nums" style="color: var(--theme-700);">{{ totals.active_visitor_count }}</span>
            <span class="text-[13px]" style="color: var(--theme-400);">/ {{ totals.visitor_count }} 总数</span>
          </div>
          <div class="mt-1 text-[11px]" style="color: var(--theme-400);">活跃 / 已开通</div>
        </div>

        <div class="rounded-xl px-4 py-3.5" style="background: #fff; border: 1px solid var(--theme-200);">
          <div class="text-[11px] uppercase tracking-wide font-semibold" style="color: var(--theme-400);">会话</div>
          <div class="mt-1 flex items-baseline gap-1.5">
            <span class="text-[22px] font-semibold tabular-nums" style="color: var(--theme-700);">{{ totals.active_session_count }}</span>
            <span class="text-[13px]" style="color: var(--theme-400);">/ {{ totals.session_count }} 总数</span>
          </div>
          <div class="mt-1 text-[11px]" style="color: var(--theme-400);">活跃 / 创建</div>
        </div>

        <div class="rounded-xl px-4 py-3.5" style="background: #fff; border: 1px solid var(--theme-200);">
          <div class="text-[11px] uppercase tracking-wide font-semibold" style="color: var(--theme-400);">总 Tokens</div>
          <div class="mt-1 text-[22px] font-semibold tabular-nums" style="color: var(--theme-700);">
            {{ formatNumber(totals.total_tokens) }}
          </div>
          <div class="mt-2 h-1.5 rounded-full overflow-hidden flex" style="background: var(--theme-100);">
            <div :style="{ width: tokenSplit.input + '%', background: 'var(--theme-600)' }" class="h-full" title="按 input 价"></div>
            <div :style="{ width: tokenSplit.cache + '%', background: 'var(--theme-300)' }" class="h-full" title="按 cache 价"></div>
            <div :style="{ width: tokenSplit.output + '%', background: 'var(--theme-500)' }" class="h-full" title="按 output 价"></div>
          </div>
          <div class="mt-1 flex items-center justify-between text-[11px] gap-1" style="color: var(--theme-400);">
            <span title="按 input 价计费">输入 {{ formatNumber(totals.non_cache_input_tokens) }}</span>
            <span title="按 cache 价计费">缓存 {{ formatNumber(totals.total_cache_tokens) }}</span>
            <span title="按 output 价计费">输出 {{ formatNumber(totals.total_completion_tokens) }}</span>
          </div>
        </div>

        <div class="rounded-xl px-4 py-3.5" style="background: #fff; border: 1px solid var(--theme-200);">
          <div class="text-[11px] uppercase tracking-wide font-semibold" style="color: var(--theme-400);">总成本估算</div>
          <div class="mt-1 text-[22px] font-semibold tabular-nums" style="color: var(--theme-700);">
            {{ formatCost(totals.cost?.total) }}
          </div>
          <div class="mt-1 text-[11px] flex items-center gap-2" style="color: var(--theme-400);">
            <span>cache 命中 {{ cacheHitRatio.toFixed(1) }}%</span>
            <span>·</span>
            <span>{{ totals.last_active ? formatRelative(totals.last_active) + '活跃' : '尚无活动' }}</span>
          </div>
        </div>
      </section>

      <!-- 访客列表 -->
      <section class="rounded-xl overflow-hidden" style="background: #fff; border: 1px solid var(--theme-200);">
        <!-- Loading -->
        <div v-if="loading && !stats" class="px-5 py-12 text-center text-[13px]" style="color: var(--theme-400);">
          加载中…
        </div>
        <!-- Empty -->
        <div v-else-if="!loading && visitors.length === 0" class="px-5 py-16 text-center" style="color: var(--theme-400);">
          <div class="text-[14px]">尚无访客</div>
          <div class="mt-1 text-[12px]">在「邀请码管理」生成码并发出去，访客兑换后会出现在这里。</div>
        </div>
        <div v-else-if="visitors.length">
          <!-- Desktop header -->
          <div class="hidden md:grid grid-cols-12 gap-3 px-5 py-2.5 text-[11px] font-semibold uppercase tracking-wide" style="color: var(--theme-500); background: var(--theme-100); border-bottom: 1px solid var(--theme-200);">
            <div class="col-span-3">访客</div>
            <div class="col-span-2 text-right">会话 / 消息</div>
            <div class="col-span-3">用量</div>
            <div class="col-span-2 text-right">成本</div>
            <div class="col-span-2 text-right">最近活跃</div>
          </div>

          <div v-for="v in visitors" :key="v.user_id">
            <!-- Desktop row -->
            <div
              class="hidden md:grid grid-cols-12 gap-3 px-5 py-3.5 items-center text-[13px] transition-colors hover:bg-[var(--theme-50)] cursor-pointer"
              :class="{ 'bg-[var(--theme-50)]': isExpanded(v.user_id) }"
              :style="{ borderBottom: '1px solid var(--theme-100)' }"
              @click="toggleExpand(v.user_id)"
            >
              <!-- 访客标识 -->
              <div class="col-span-3 flex items-center gap-2.5 min-w-0">
                <div
                  class="w-8 h-8 rounded-full flex items-center justify-center text-[12px] font-semibold shrink-0"
                  :style="{ background: `hsl(${visitorHue(v)} 60% 92%)`, color: `hsl(${visitorHue(v)} 60% 35%)` }"
                >{{ visitorInitial(v) }}</div>
                <div class="min-w-0">
                  <div class="font-medium truncate" style="color: var(--theme-700);">{{ visitorDisplayName(v) }}</div>
                  <div class="text-[11px] truncate" style="color: var(--theme-400);">
                    <template v-if="v.invite_note">{{ v.invite_note }} · </template>
                    {{ v.username }}
                  </div>
                </div>
              </div>

              <!-- 会话/消息 -->
              <div class="col-span-2 text-right tabular-nums" style="color: var(--theme-600);">
                <div>{{ v.active_session_count }}<span class="text-[11px]" style="color: var(--theme-400);"> / {{ v.session_count }}</span></div>
                <div class="text-[11px]" style="color: var(--theme-400);">{{ v.user_message_count }} 提问 · {{ v.assistant_turn_count }} 回</div>
              </div>

              <!-- 用量 + 进度条 -->
              <div class="col-span-3 min-w-0">
                <div class="text-[12px] tabular-nums mb-1.5" style="color: var(--theme-600);">
                  {{ formatNumber(v.total_tokens) }} tok
                  <span class="text-[11px]" style="color: var(--theme-400);">
                    输入 {{ formatNumber(v.non_cache_input_tokens) }} · 缓存 {{ formatNumber(v.cache_tokens) }} · 输出 {{ formatNumber(v.completion_tokens) }}
                  </span>
                </div>
                <div class="h-1.5 rounded-full overflow-hidden" style="background: var(--theme-100);">
                  <div
                    class="h-full"
                    :style="{
                      width: maxVisitorTokens ? Math.max(2, (v.total_tokens / maxVisitorTokens) * 100) + '%' : '0%',
                      background: 'linear-gradient(90deg, var(--theme-500), var(--theme-300))'
                    }"
                  ></div>
                </div>
              </div>

              <!-- 成本 -->
              <div class="col-span-2 text-right tabular-nums">
                <div class="font-medium" style="color: var(--theme-700);">{{ formatCost(v.cost?.total) }}</div>
                <div class="text-[11px]" style="color: var(--theme-400);">{{ v.models.length }} 模型</div>
              </div>

              <!-- 最近活跃 -->
              <div class="col-span-2 text-right">
                <div class="text-[12px]" style="color: var(--theme-600);">{{ formatRelative(v.last_active) }}</div>
                <div class="text-[11px]" style="color: var(--theme-400);">激活 {{ formatDate(v.activated_at) }}</div>
              </div>
            </div>

            <!-- Expanded — analytics panel (responsive desktop + mobile) -->
            <div v-if="isExpanded(v.user_id)" class="analytics" :data-uid="v.user_id" @click.stop>
              <!-- Tabs + range -->
              <div class="analytics__toolbar">
                <div class="analytics__tabs">
                  <button
                    class="analytics__tab"
                    :class="{ 'is-active': detailFor(v.user_id).tab === 'overview' }"
                    @click="setDetailTab(v.user_id, 'overview')"
                  >Overview</button>
                  <button
                    class="analytics__tab"
                    :class="{ 'is-active': detailFor(v.user_id).tab === 'models' }"
                    @click="setDetailTab(v.user_id, 'models')"
                  >Models</button>
                </div>
                <div class="analytics__range">
                  <button
                    v-for="r in ['all','30d','7d']"
                    :key="r"
                    class="analytics__range-btn"
                    :class="{ 'is-active': detailFor(v.user_id).range === r }"
                    @click="setDetailRange(v.user_id, r)"
                  >{{ r === 'all' ? 'All' : r }}</button>
                </div>
              </div>

              <!-- Overview tab -->
              <template v-if="detailFor(v.user_id).tab === 'overview'">
                <!-- Stats grid -->
                <div class="analytics__stats">
                  <div class="stat">
                    <div class="stat__label">Sessions</div>
                    <div class="stat__value">{{ visitorWindowStats(v, detailFor(v.user_id).range).sessions }}</div>
                  </div>
                  <div class="stat">
                    <div class="stat__label">Messages</div>
                    <div class="stat__value">{{ visitorWindowStats(v, detailFor(v.user_id).range).messages.toLocaleString() }}</div>
                  </div>
                  <div class="stat">
                    <div class="stat__label">Total tokens</div>
                    <div class="stat__value">{{ formatNumber(visitorWindowStats(v, detailFor(v.user_id).range).tokens) }}</div>
                  </div>
                  <div class="stat">
                    <div class="stat__label">Active days</div>
                    <div class="stat__value">{{ visitorWindowStats(v, detailFor(v.user_id).range).activeDays }}</div>
                  </div>
                  <div class="stat">
                    <div class="stat__label">Current streak</div>
                    <div class="stat__value">{{ v.current_streak || 0 }}<span class="stat__unit">d</span></div>
                  </div>
                  <div class="stat">
                    <div class="stat__label">Longest streak</div>
                    <div class="stat__value">{{ v.longest_streak || 0 }}<span class="stat__unit">d</span></div>
                  </div>
                  <div class="stat">
                    <div class="stat__label">Peak hour</div>
                    <div class="stat__value">{{ formatHour(v.peak_hour) }}</div>
                  </div>
                  <div class="stat">
                    <div class="stat__label">Favorite model</div>
                    <div class="stat__value stat__value--text" :title="v.favorite_model || '—'">{{ v.favorite_model || '—' }}</div>
                  </div>
                </div>

                <!-- Heatmap -->
                <div class="analytics__heatmap">
                  <AiLabUsageHeatmap
                    :daily="v.daily || []"
                    :start-date="v.activated_at"
                    :range="detailFor(v.user_id).range"
                  />
                </div>
              </template>

              <!-- Models tab -->
              <template v-else>
                <div v-if="v.models.length === 0" class="analytics__empty">
                  该访客尚未产生计费 token。
                </div>
                <div v-else class="analytics__models">
                  <div
                    v-for="m in v.models"
                    :key="m.raw_model || m.model"
                    class="model-card"
                  >
                    <div class="model-card__head">
                      <div class="model-card__name">
                        <code>{{ m.raw_model || m.model }}</code>
                        <span v-if="!m.priced" class="model-card__badge" title="此模型不在价格表中，按默认模型估算">默认价</span>
                      </div>
                      <div class="model-card__cost">{{ formatCost(m.cost?.total) }}</div>
                    </div>
                    <div class="model-card__stats">
                      <div title="按 input 价计费"><span>输入</span> {{ formatNumber(m.non_cache_input_tokens) }}</div>
                      <div title="按 cache 价计费"><span>缓存</span> {{ formatNumber(m.cache_tokens) }}</div>
                      <div title="按 output 价计费"><span>输出</span> {{ formatNumber(m.completion_tokens) }}</div>
                      <div><span>轮数</span> {{ m.turns }}</div>
                    </div>
                  </div>
                </div>
              </template>
            </div>

            <!-- Mobile card -->
            <div
              class="md:hidden px-4 py-3.5 cursor-pointer"
              :class="{ 'bg-[var(--theme-50)]': isExpanded(v.user_id) }"
              :style="{ borderBottom: '1px solid var(--theme-100)' }"
              @click="toggleExpand(v.user_id)"
            >
              <div class="flex items-center gap-2.5 mb-2">
                <div
                  class="w-8 h-8 rounded-full flex items-center justify-center text-[12px] font-semibold shrink-0"
                  :style="{ background: `hsl(${visitorHue(v)} 60% 92%)`, color: `hsl(${visitorHue(v)} 60% 35%)` }"
                >{{ visitorInitial(v) }}</div>
                <div class="min-w-0 flex-1">
                  <div class="font-medium text-[13px] truncate" style="color: var(--theme-700);">{{ visitorDisplayName(v) }}</div>
                  <div class="text-[11px] truncate" style="color: var(--theme-400);">
                    <template v-if="v.invite_note">{{ v.invite_note }} · </template>{{ v.username }}
                  </div>
                </div>
                <div class="text-right shrink-0">
                  <div class="text-[13px] font-medium tabular-nums" style="color: var(--theme-700);">{{ formatCost(v.cost?.total) }}</div>
                  <div class="text-[11px]" style="color: var(--theme-400);">{{ formatRelative(v.last_active) }}</div>
                </div>
              </div>
              <div class="grid grid-cols-3 gap-2 text-[11px] tabular-nums" style="color: var(--theme-500);">
                <div><span style="color: var(--theme-400);">会话</span> {{ v.active_session_count }}/{{ v.session_count }}</div>
                <div><span style="color: var(--theme-400);">消息</span> {{ v.message_count }}</div>
                <div><span style="color: var(--theme-400);">tokens</span> {{ formatNumber(v.total_tokens) }}</div>
              </div>
              <div class="mt-2 h-1.5 rounded-full overflow-hidden" style="background: var(--theme-100);">
                <div
                  class="h-full"
                  :style="{
                    width: maxVisitorTokens ? Math.max(2, (v.total_tokens / maxVisitorTokens) * 100) + '%' : '0%',
                    background: 'linear-gradient(90deg, var(--theme-500), var(--theme-300))'
                  }"
                ></div>
              </div>
              <!-- 展开 analytics 由顶部统一渲染；mobile 此处不再重复列模型 -->
            </div>
          </div>
        </div>
      </section>
    </div>
  </div>
</template>

<style scoped>
/* === Header toolbar === */
.usage-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 28px;
  flex-wrap: wrap;
}
.usage-header__title {
  display: flex;
  align-items: center;
  gap: 14px;
  min-width: 0;
}
.usage-header__back {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  border-radius: 10px;
  background: #fff;
  border: 1px solid var(--theme-200, #e6e4dd);
  color: var(--theme-500, #888578);
  cursor: pointer;
  transition: background 0.12s ease, transform 0.12s ease, color 0.12s ease;
  flex-shrink: 0;
}
.usage-header__back:hover {
  background: var(--theme-100, #ececea);
  color: var(--theme-700, #2d2d28);
  transform: translateX(-1px);
}
.usage-header__heading h1 {
  font-size: 22px;
  font-weight: 600;
  letter-spacing: -0.01em;
  color: var(--theme-700, #2d2d28);
  margin: 0;
  line-height: 1.2;
}
.usage-header__heading p {
  font-size: 13px;
  color: var(--theme-500, #888578);
  margin: 4px 0 0;
}
.usage-header__actions {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 4px;
  background: var(--theme-100, #ececea);
  border: 1px solid var(--theme-200, #e6e4dd);
  border-radius: 12px;
}
.usage-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 7px 12px;
  border-radius: 8px;
  font-size: 13px;
  font-weight: 500;
  color: var(--theme-600, #6c6a5e);
  background: transparent;
  border: none;
  cursor: pointer;
  transition: background 0.12s ease, color 0.12s ease, box-shadow 0.12s ease;
  text-decoration: none;
}
.usage-btn:hover {
  background: #fff;
  color: var(--theme-700, #2d2d28);
  box-shadow: 0 1px 2px rgba(0,0,0,0.04);
}
.usage-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
.usage-btn--icon svg {
  transition: transform 0.4s ease;
}
.usage-btn--icon.is-loading svg {
  animation: usage-btn-spin 0.9s linear infinite;
}
@keyframes usage-btn-spin {
  to { transform: rotate(360deg); }
}

/* === Analytics panel inside expanded row === */
.analytics {
  background: var(--theme-50, #f8f8f6);
  border-bottom: 1px solid var(--theme-100, #ececea);
  padding: 18px 20px 22px;
}
.analytics__toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  flex-wrap: wrap;
  gap: 8px;
}
.analytics__tabs,
.analytics__range {
  display: inline-flex;
  align-items: center;
  background: #fff;
  border: 1px solid var(--theme-200, #e6e4dd);
  border-radius: 10px;
  padding: 3px;
  gap: 1px;
}
.analytics__tab,
.analytics__range-btn {
  padding: 5px 12px;
  border-radius: 7px;
  font-size: 12px;
  font-weight: 500;
  color: var(--theme-500, #888578);
  background: transparent;
  border: none;
  cursor: pointer;
  transition: background 0.12s ease, color 0.12s ease;
}
.analytics__tab:hover,
.analytics__range-btn:hover {
  color: var(--theme-700, #2d2d28);
}
.analytics__tab.is-active,
.analytics__range-btn.is-active {
  background: var(--theme-700, #2d2d28);
  color: var(--theme-50, #f8f8f6);
}
.analytics__range-btn {
  font-size: 11px;
  min-width: 38px;
  text-align: center;
}

/* Stats grid (8 cards) */
.analytics__stats {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 8px;
  margin-bottom: 16px;
}
@media (min-width: 640px) {
  .analytics__stats { grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 10px; }
}
@media (min-width: 1024px) {
  .analytics__stats { grid-template-columns: repeat(8, minmax(0, 1fr)); }
}
@media (max-width: 640px) {
  .analytics { padding: 14px 12px 16px; }
  .analytics__toolbar { gap: 6px; }
}
.stat {
  background: #fff;
  border: 1px solid var(--theme-200, #e6e4dd);
  border-radius: 10px;
  padding: 10px 12px;
}
.stat__label {
  font-size: 10px;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  font-weight: 600;
  color: var(--theme-400, #b3b1a6);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.stat__value {
  margin-top: 4px;
  font-size: 18px;
  font-weight: 600;
  color: var(--theme-700, #2d2d28);
  font-variant-numeric: tabular-nums;
  line-height: 1.2;
}
.stat__value--text {
  font-size: 13px;
  font-family: var(--ai-font-mono, ui-monospace, monospace);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.stat__unit {
  margin-left: 2px;
  font-size: 12px;
  font-weight: 500;
  color: var(--theme-400, #b3b1a6);
}

/* Heatmap container */
.analytics__heatmap {
  background: #fff;
  border: 1px solid var(--theme-200, #e6e4dd);
  border-radius: 10px;
  padding: 14px 14px 10px;
}

/* Models tab cards */
.analytics__empty {
  font-size: 12px;
  color: var(--theme-400, #b3b1a6);
  padding: 24px 0;
  text-align: center;
}
.analytics__models {
  display: grid;
  grid-template-columns: 1fr;
  gap: 8px;
}
@media (min-width: 1024px) {
  .analytics__models { grid-template-columns: 1fr 1fr; }
}
.model-card {
  background: #fff;
  border: 1px solid var(--theme-200, #e6e4dd);
  border-radius: 10px;
  padding: 10px 12px;
}
.model-card__head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 8px;
}
.model-card__name {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  min-width: 0;
}
.model-card__name code {
  font-size: 12px;
  font-family: var(--ai-font-mono, ui-monospace, monospace);
  color: var(--theme-700, #2d2d28);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.model-card__badge {
  font-size: 10px;
  padding: 2px 6px;
  border-radius: 4px;
  background: #fef9c3;
  color: #854d0e;
  flex-shrink: 0;
}
.model-card__cost {
  font-size: 12px;
  font-weight: 500;
  color: var(--theme-700, #2d2d28);
  font-variant-numeric: tabular-nums;
  flex-shrink: 0;
}
.model-card__stats {
  margin-top: 6px;
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 8px;
  font-size: 11px;
  color: var(--theme-500, #888578);
  font-variant-numeric: tabular-nums;
}
.model-card__stats span {
  color: var(--theme-400, #b3b1a6);
  margin-right: 3px;
}
</style>
