<script setup>
import { computed, ref } from 'vue'

const props = defineProps({
  // [{date: 'YYYY-MM-DD', tokens, messages, sessions, ...}, ...]  — 已按日期升序
  daily: { type: Array, default: () => [] },
  // 数据起始锚点（访客激活日，用作 All 模式起点）
  startDate: { type: String, default: '' },
  // 'all' | '30d' | '7d'
  range: { type: String, default: 'all' },
})

const _today = () => {
  const d = new Date()
  d.setHours(0, 0, 0, 0)
  return d
}
const _addDays = (d, n) => {
  const r = new Date(d)
  r.setDate(r.getDate() + n)
  return r
}
const _isoDate = (d) => {
  const yyyy = d.getFullYear()
  const mm = String(d.getMonth() + 1).padStart(2, '0')
  const dd = String(d.getDate()).padStart(2, '0')
  return `${yyyy}-${mm}-${dd}`
}

// 时间窗口起点
const windowStart = computed(() => {
  const today = _today()
  if (props.range === '7d')  return _addDays(today, -6)
  if (props.range === '30d') return _addDays(today, -29)
  // all: 取访客激活日 vs 90 天前 较早的；不存在就 90 天前。最少 8 周显示
  const fallback = _addDays(today, -89)
  if (props.startDate) {
    const sd = new Date(props.startDate)
    if (!isNaN(sd.getTime())) {
      sd.setHours(0, 0, 0, 0)
      return sd < fallback ? sd : fallback
    }
  }
  return fallback
})

// 起点对齐到周日（让网格按完整周排列）— 前面的那几天显示空白 placeholder
const gridStart = computed(() => {
  const s = new Date(windowStart.value)
  const dayOfWeek = s.getDay() // 0 = 周日
  return _addDays(s, -dayOfWeek)
})

// 数据查找表
const dailyMap = computed(() => {
  const m = new Map()
  for (const row of props.daily || []) {
    if (row && row.date) m.set(row.date, row)
  }
  return m
})

// 颜色梯度阈值（用窗口期内最大值动态划分 — 让稀少访客也有颜色对比）
const maxTokens = computed(() => {
  let m = 0
  for (const row of props.daily || []) {
    const t = Number(row.tokens) || 0
    if (t > m) m = t
  }
  return m
})

const cellLevel = (row) => {
  if (!row) return 0
  const t = Number(row.tokens) || 0
  if (t <= 0) return 0
  const m = maxTokens.value
  if (m <= 0) return 0
  const r = t / m
  if (r > 0.66) return 4
  if (r > 0.33) return 3
  if (r > 0.10) return 2
  return 1
}

// 生成网格：每列 = 一周（周日→周六），列数 = 覆盖窗口的周数
const weeks = computed(() => {
  const start = gridStart.value
  const today = _today()
  const totalDays = Math.floor((today - start) / 86400000) + 1
  const totalWeeks = Math.ceil(totalDays / 7)

  const result = []
  for (let w = 0; w < totalWeeks; w++) {
    const days = []
    for (let d = 0; d < 7; d++) {
      const cellDate = _addDays(start, w * 7 + d)
      // 超出今天的格子 → null（显示为空白）
      if (cellDate > today) {
        days.push(null)
        continue
      }
      // 早于 windowStart 的格子（用来对齐到周首）→ ghost
      const beforeWindow = cellDate < windowStart.value
      const iso = _isoDate(cellDate)
      const data = dailyMap.value.get(iso)
      days.push({
        date: iso,
        ghost: beforeWindow,
        level: beforeWindow ? -1 : cellLevel(data),
        tokens: data?.tokens || 0,
        messages: data?.messages || 0,
        sessions: data?.sessions || 0,
      })
    }
    result.push(days)
  }
  return result
})

// 月份标签（每个月在它第一周列上方显示）
const monthLabels = computed(() => {
  const labels = []
  let lastMonth = -1
  weeks.value.forEach((wk, idx) => {
    // 用该列第一个非 null 单元格的月份
    const firstCell = wk.find(c => c)
    if (!firstCell) return
    const m = new Date(firstCell.date).getMonth()
    if (m !== lastMonth) {
      labels.push({ idx, label: `${m + 1}月` })
      lastMonth = m
    }
  })
  return labels
})

const dayLabels = ['', '一', '', '三', '', '五', '']

const formatNumber = (n) => {
  const v = Number(n) || 0
  if (v < 1000) return String(v)
  if (v < 1_000_000) return `${(v / 1000).toFixed(v < 10_000 ? 2 : 1)}K`
  if (v < 1_000_000_000) return `${(v / 1_000_000).toFixed(2)}M`
  return `${(v / 1_000_000_000).toFixed(2)}B`
}

const hover = ref(null)
const hoverPos = ref({ x: 0, y: 0 })
const onCellEnter = (cell, ev) => {
  if (!cell || cell.ghost || cell.level < 0) {
    hover.value = null
    return
  }
  hover.value = cell
  const rect = ev.currentTarget.getBoundingClientRect()
  const wrapRect = ev.currentTarget.closest('.heatmap')?.getBoundingClientRect()
  hoverPos.value = {
    x: rect.left + rect.width / 2 - (wrapRect?.left || 0),
    y: rect.top - (wrapRect?.top || 0) - 4,
  }
}
const onCellLeave = () => { hover.value = null }
</script>

<template>
  <div class="heatmap">
    <!-- 月份行 -->
    <div class="heatmap__months" :style="{ '--cols': weeks.length }">
      <div
        v-for="m in monthLabels"
        :key="m.idx"
        class="heatmap__month-label"
        :style="{ gridColumn: `${m.idx + 2} / span 1` }"
      >{{ m.label }}</div>
    </div>

    <!-- 网格 + 周次标签 -->
    <div class="heatmap__grid-wrap">
      <div class="heatmap__day-axis">
        <div v-for="(d, i) in dayLabels" :key="i" class="heatmap__day-label">{{ d }}</div>
      </div>

      <div class="heatmap__grid" :style="{ '--cols': weeks.length }">
        <div
          v-for="(wk, wi) in weeks"
          :key="wi"
          class="heatmap__week"
        >
          <div
            v-for="(cell, di) in wk"
            :key="di"
            class="heatmap__cell"
            :class="cell ? `lvl-${cell.level >= 0 ? cell.level : 'ghost'}` : 'lvl-empty'"
            @mouseenter="onCellEnter(cell, $event)"
            @mouseleave="onCellLeave"
          ></div>
        </div>
      </div>
    </div>

    <!-- 图例 -->
    <div class="heatmap__legend">
      <span class="heatmap__legend-label">少</span>
      <div class="heatmap__cell lvl-0"></div>
      <div class="heatmap__cell lvl-1"></div>
      <div class="heatmap__cell lvl-2"></div>
      <div class="heatmap__cell lvl-3"></div>
      <div class="heatmap__cell lvl-4"></div>
      <span class="heatmap__legend-label">多</span>
    </div>

    <!-- Tooltip -->
    <div
      v-if="hover"
      class="heatmap__tooltip"
      :style="{ left: hoverPos.x + 'px', top: hoverPos.y + 'px' }"
    >
      <div class="heatmap__tooltip-date">{{ hover.date }}</div>
      <div class="heatmap__tooltip-row">tokens <b>{{ formatNumber(hover.tokens) }}</b></div>
      <div class="heatmap__tooltip-row">messages <b>{{ hover.messages }}</b></div>
      <div class="heatmap__tooltip-row">sessions <b>{{ hover.sessions }}</b></div>
    </div>
  </div>
</template>

<style scoped>
.heatmap {
  position: relative;
  font-family: var(--ai-font-body, system-ui);
}

.heatmap__months {
  display: grid;
  grid-template-columns: 18px repeat(var(--cols), 12px);
  column-gap: 3px;
  margin-bottom: 4px;
  height: 14px;
}
.heatmap__month-label {
  font-size: 10px;
  color: var(--theme-400, #b3b1a6);
  white-space: nowrap;
  align-self: center;
}

.heatmap__grid-wrap {
  display: flex;
  align-items: flex-start;
  gap: 3px;
}
.heatmap__day-axis {
  display: grid;
  grid-template-rows: repeat(7, 12px);
  gap: 3px;
  width: 18px;
  flex-shrink: 0;
}
.heatmap__day-label {
  font-size: 9px;
  line-height: 12px;
  color: var(--theme-400, #b3b1a6);
}

.heatmap__grid {
  display: grid;
  grid-template-columns: repeat(var(--cols), 12px);
  gap: 3px;
  flex: 1;
  min-width: 0;
  overflow-x: auto;
}
.heatmap__week {
  display: grid;
  grid-template-rows: repeat(7, 12px);
  gap: 3px;
}
.heatmap__cell {
  width: 12px;
  height: 12px;
  border-radius: 2px;
  background: var(--theme-100, #ececea);
  transition: transform 0.08s ease, box-shadow 0.08s ease;
}
.heatmap__cell:hover {
  transform: scale(1.15);
  box-shadow: 0 0 0 1px rgba(0,0,0,0.1);
}
.heatmap__cell.lvl-empty,
.heatmap__cell.lvl-ghost {
  background: transparent;
  pointer-events: none;
}
.heatmap__cell.lvl-0 { background: var(--theme-100, #ececea); }
.heatmap__cell.lvl-1 { background: #c8e6f8; }
.heatmap__cell.lvl-2 { background: #79bbe6; }
.heatmap__cell.lvl-3 { background: #4d8fc4; }
.heatmap__cell.lvl-4 { background: #1f5fa0; }

.heatmap__legend {
  display: flex;
  align-items: center;
  gap: 3px;
  margin-top: 8px;
  font-size: 10px;
  justify-content: flex-end;
}
.heatmap__legend-label {
  color: var(--theme-400, #b3b1a6);
  margin: 0 4px;
}
.heatmap__legend .heatmap__cell {
  width: 10px;
  height: 10px;
}

.heatmap__tooltip {
  position: absolute;
  transform: translate(-50%, -100%);
  background: rgba(0, 0, 0, 0.85);
  color: #fff;
  border-radius: 6px;
  padding: 6px 8px;
  font-size: 11px;
  pointer-events: none;
  z-index: 10;
  white-space: nowrap;
  box-shadow: 0 2px 8px rgba(0,0,0,0.15);
}
.heatmap__tooltip-date {
  font-weight: 600;
  margin-bottom: 2px;
  font-family: var(--ai-font-mono, ui-monospace, monospace);
}
.heatmap__tooltip-row {
  display: flex;
  justify-content: space-between;
  gap: 8px;
  font-size: 10px;
  color: rgba(255,255,255,0.8);
}
.heatmap__tooltip-row b {
  color: #fff;
  font-weight: 500;
  margin-left: 6px;
}
</style>
