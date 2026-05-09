<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import API_BASE_URL from '../config/api'

const router = useRouter()
const me = ref(null)
const stats = ref(null)
const loading = ref(false)
const error = ref('')
const expanded = ref(new Set())

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

// prompt 段内 cache vs 非 cache 占比 — 计算 totals 区段
const promptCacheRatio = computed(() => {
  const t = totals.value
  if (!t) return { cache: 0, nonCache: 0 }
  const p = Number(t.total_prompt_tokens) || 0
  if (!p) return { cache: 0, nonCache: 0 }
  const cache = Math.min(Number(t.total_cache_tokens) || 0, p)
  return { cache: (cache / p) * 100, nonCache: ((p - cache) / p) * 100 }
})

const promptVsCompletion = computed(() => {
  const t = totals.value
  if (!t) return { p: 0, c: 0 }
  const p = Number(t.total_prompt_tokens) || 0
  const c = Number(t.total_completion_tokens) || 0
  const sum = p + c
  if (!sum) return { p: 0, c: 0 }
  return { p: (p / sum) * 100, c: (c / sum) * 100 }
})
</script>

<template>
  <div class="min-h-screen px-4 py-10" style="background: var(--theme-50, #f8f8f6);">
    <div class="max-w-5xl mx-auto">
      <!-- Header -->
      <div class="flex items-center justify-between mb-6 flex-wrap gap-3">
        <div>
          <h1 class="text-[22px] font-semibold tracking-tight" style="color: var(--theme-700);">访客用量</h1>
          <p class="text-[13px] mt-1" style="color: var(--theme-500);">所有兑换过邀请码、开通了 MyAgent 的访客的使用情况。</p>
        </div>
        <div class="flex items-center gap-3 text-[13px]">
          <router-link
            to="/ai-lab/admin/invites"
            class="cursor-pointer hover:underline"
            style="color: var(--theme-500);"
          >邀请码管理 →</router-link>
          <button
            @click="fetchStats({ silent: false })"
            :disabled="loading"
            class="px-3 py-1.5 rounded-lg cursor-pointer disabled:opacity-50"
            style="border: 1px solid var(--theme-200); background: #fff; color: var(--theme-600);"
          >{{ loading ? '刷新中…' : '刷新' }}</button>
          <router-link to="/ai-lab" class="cursor-pointer" style="color: var(--theme-500);">← 返回 MyAgent</router-link>
        </div>
      </div>

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
            <div :style="{ width: promptVsCompletion.p + '%', background: 'var(--theme-500)' }" class="h-full"></div>
            <div :style="{ width: promptVsCompletion.c + '%', background: 'var(--theme-300)' }" class="h-full"></div>
          </div>
          <div class="mt-1 flex items-center justify-between text-[11px]" style="color: var(--theme-400);">
            <span>P {{ formatNumber(totals.total_prompt_tokens) }}</span>
            <span>C {{ formatNumber(totals.total_completion_tokens) }}</span>
          </div>
        </div>

        <div class="rounded-xl px-4 py-3.5" style="background: #fff; border: 1px solid var(--theme-200);">
          <div class="text-[11px] uppercase tracking-wide font-semibold" style="color: var(--theme-400);">总成本估算</div>
          <div class="mt-1 text-[22px] font-semibold tabular-nums" style="color: var(--theme-700);">
            {{ formatCost(totals.cost?.total) }}
          </div>
          <div class="mt-1 text-[11px] flex items-center gap-2" style="color: var(--theme-400);">
            <span>cache 命中 {{ promptCacheRatio.cache.toFixed(0) }}%</span>
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
                    P {{ formatNumber(v.prompt_tokens) }} · C {{ formatNumber(v.completion_tokens) }}
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

            <!-- Desktop expanded -->
            <div v-if="isExpanded(v.user_id)" class="hidden md:block px-5 py-4" style="background: var(--theme-50); border-bottom: 1px solid var(--theme-100);">
              <div v-if="v.models.length === 0" class="text-[12px]" style="color: var(--theme-400);">
                该访客尚未产生计费 token。
              </div>
              <div v-else>
                <div class="text-[11px] font-semibold uppercase tracking-wide mb-2" style="color: var(--theme-500);">模型分布</div>
                <div class="grid grid-cols-1 lg:grid-cols-2 gap-2">
                  <div
                    v-for="m in v.models"
                    :key="m.raw_model || m.model"
                    class="rounded-lg px-3 py-2.5"
                    style="background: #fff; border: 1px solid var(--theme-200);"
                  >
                    <div class="flex items-center justify-between gap-2">
                      <div class="min-w-0 flex items-center gap-1.5">
                        <code class="text-[12px] truncate" style="color: var(--theme-700); font-family: var(--ai-font-mono, ui-monospace, monospace);">{{ m.raw_model || m.model }}</code>
                        <span v-if="!m.priced" class="text-[10px] px-1.5 py-0.5 rounded shrink-0" style="background: #fef9c3; color: #854d0e;" title="此模型不在价格表中，按默认模型估算">默认价</span>
                      </div>
                      <div class="text-[12px] font-medium tabular-nums shrink-0" style="color: var(--theme-700);">{{ formatCost(m.cost?.total) }}</div>
                    </div>
                    <div class="mt-1.5 grid grid-cols-4 gap-2 text-[11px] tabular-nums" style="color: var(--theme-500);">
                      <div><span style="color: var(--theme-400);">prompt</span> {{ formatNumber(m.prompt_tokens) }}</div>
                      <div><span style="color: var(--theme-400);">cache</span> {{ formatNumber(m.cache_tokens) }}</div>
                      <div><span style="color: var(--theme-400);">输出</span> {{ formatNumber(m.completion_tokens) }}</div>
                      <div><span style="color: var(--theme-400);">轮数</span> {{ m.turns }}</div>
                    </div>
                  </div>
                </div>
              </div>
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
              <div v-if="isExpanded(v.user_id) && v.models.length" class="mt-3 space-y-2">
                <div
                  v-for="m in v.models"
                  :key="m.raw_model || m.model"
                  class="rounded-lg px-3 py-2"
                  style="background: #fff; border: 1px solid var(--theme-200);"
                >
                  <div class="flex items-center justify-between gap-2 mb-1">
                    <code class="text-[11px] truncate" style="color: var(--theme-700); font-family: var(--ai-font-mono, ui-monospace, monospace);">{{ m.raw_model || m.model }}</code>
                    <span class="text-[12px] font-medium tabular-nums" style="color: var(--theme-700);">{{ formatCost(m.cost?.total) }}</span>
                  </div>
                  <div class="grid grid-cols-4 gap-1 text-[10px] tabular-nums" style="color: var(--theme-500);">
                    <div>P {{ formatNumber(m.prompt_tokens) }}</div>
                    <div>K {{ formatNumber(m.cache_tokens) }}</div>
                    <div>O {{ formatNumber(m.completion_tokens) }}</div>
                    <div>{{ m.turns }} 轮</div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>
    </div>
  </div>
</template>
