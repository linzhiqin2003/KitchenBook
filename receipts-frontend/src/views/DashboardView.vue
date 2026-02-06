<template>
  <!-- 时间范围选择栏 -->
  <div class="date-range-bar">
    <div class="range-presets">
      <button v-for="p in presets" :key="p.key"
              :class="{ active: activePreset === p.key }"
              @click="applyPreset(p.key)">
        {{ p.label }}
      </button>
    </div>
    <div v-if="activePreset === 'custom'" class="custom-dates">
      <input type="date" :value="dateRange.start" @change="onCustomStart" />
      <span class="date-sep">至</span>
      <input type="date" :value="dateRange.end" @change="onCustomEnd" />
    </div>
    <div v-if="exchangeRate" class="exchange-rate-badge">
      实时汇率：£1 = ¥{{ exchangeRate.toFixed(2) }}
    </div>
  </div>

  <div class="card-grid">
    <StatCard label="总支出" :value="formatGBP(stats.total_spend)" :secondary-value="convertCNY(stats.total_spend)" :subtitle="rangeLabel">
      <template #icon><Wallet :size="20" /></template>
    </StatCard>
    <StatCard label="收据数量" :value="stats.receipt_count" :subtitle="rangeLabel">
      <template #icon><Receipt :size="20" /></template>
    </StatCard>
    <StatCard label="最大类目" :value="topCategory" subtitle="消费最高">
      <template #icon><FolderOpen :size="20" /></template>
    </StatCard>
  </div>

  <div class="card-grid" style="margin-top: 8px;">
    <ChartCard :options="categoryChart" @chart-click="onCategoryClick" />
    <div class="panel chart-panel trend-panel">
      <div class="trend-header">
        <h2>{{ trendMode === 'month' ? '月度趋势' : '日度趋势' }}</h2>
        <div class="trend-toggle">
          <button :class="{ active: trendMode === 'month' }" @click="trendMode = 'month'">月度</button>
          <button :class="{ active: trendMode === 'day' }" @click="trendMode = 'day'">日度</button>
        </div>
      </div>
      <ChartCard :options="trendChart" class="trend-chart-inner" @chart-click="onTrendClick" />
    </div>
  </div>

  <div v-if="authStore.isOrgMode && stats.by_payer?.length" class="card-grid" style="margin-top: 8px;">
    <ChartCard :options="merchantChart" @chart-click="onMerchantClick" />
    <ChartCard :options="payerChart" @chart-click="onPayerClick" />
  </div>
  <div v-else class="card-grid card-grid--single" style="margin-top: 8px;">
    <ChartCard :options="merchantChart" @chart-click="onMerchantClick" />
  </div>

  <div class="panel">
    <div class="recent-header">
      <h2>最近购买</h2>
      <button v-if="selectedCategory" class="filter-tag" @click="selectedCategory = null">
        {{ selectedCategory }} <span class="filter-tag__x">&times;</span>
      </button>
      <button v-if="selectedMerchant" class="filter-tag" @click="selectedMerchant = null">
        {{ selectedMerchant }} <span class="filter-tag__x">&times;</span>
      </button>
      <button v-if="selectedPeriod" class="filter-tag" @click="selectedPeriod = null">
        {{ selectedPeriod.label }} <span class="filter-tag__x">&times;</span>
      </button>
      <button v-if="selectedPayer" class="filter-tag" @click="selectedPayer = null">
        {{ selectedPayer }} <span class="filter-tag__x">&times;</span>
      </button>
    </div>
    <table class="table">
      <thead>
        <tr>
          <th>商品</th>
          <th>品牌</th>
          <th>数量</th>
          <th>单位</th>
          <th class="sortable-th" :class="{ 'sorted': sortKey === 'total_spent' }" @click="toggleSort('total_spent')">
            总花费
            <span class="sort-arrow">{{ sortKey === 'total_spent' ? (sortDir === 'asc' ? '↑' : '↓') : '↕' }}</span>
          </th>
          <th class="sortable-th" :class="{ 'sorted': sortKey === 'last_purchased' }" @click="toggleSort('last_purchased')">
            购买日期
            <span class="sort-arrow">{{ sortKey === 'last_purchased' ? (sortDir === 'asc' ? '↑' : '↓') : '↕' }}</span>
          </th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="(item, idx) in paginatedItems" :key="idx" class="recent-row">
          <td data-label="商品">{{ item.name }}</td>
          <td data-label="品牌">{{ item.brand || "-" }}</td>
          <td data-label="数量">{{ formatQuantity(item.total_quantity) }}</td>
          <td data-label="单位">{{ item.unit || "-" }}</td>
          <td data-label="总花费">
            {{ formatGBP(item.total_spent) }}
            <span v-if="convertCNY(item.total_spent)" class="cny-hint">{{ convertCNY(item.total_spent) }}</span>
          </td>
          <td data-label="购买日期">{{ formatDate(item.last_purchased) }}</td>
        </tr>
      </tbody>
    </table>
    <div v-if="!filteredItems.length" class="empty-state">
      <Inbox :size="40" class="empty-state__icon" />
      <div class="empty-state__text">{{ (selectedCategory || selectedMerchant) ? '该筛选条件下暂无记录' : '暂无购买记录' }}</div>
    </div>
    <div v-if="totalPages > 1" class="pagination">
      <span class="pagination__info">共 {{ filteredItems.length }} 条，第 {{ currentPage }}/{{ totalPages }} 页</span>
      <div class="pagination__controls">
        <button :disabled="currentPage <= 1" @click="currentPage = 1" title="首页">&laquo;</button>
        <button :disabled="currentPage <= 1" @click="currentPage--" title="上一页">&lsaquo;</button>
        <button v-for="p in visiblePages" :key="p"
                :class="{ active: p === currentPage }"
                @click="currentPage = p">{{ p }}</button>
        <button :disabled="currentPage >= totalPages" @click="currentPage++" title="下一页">&rsaquo;</button>
        <button :disabled="currentPage >= totalPages" @click="currentPage = totalPages" title="末页">&raquo;</button>
      </div>
      <select v-model.number="pageSize" class="pagination__size">
        <option :value="10">10 条/页</option>
        <option :value="20">20 条/页</option>
        <option :value="50">50 条/页</option>
      </select>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";
import { Wallet, Receipt, FolderOpen, Inbox } from "lucide-vue-next";
import ChartCard from "../components/ChartCard.vue";
import StatCard from "../components/StatCard.vue";
import { fetchStats, getExchangeRate } from "../api/receipts";
import { useAuthStore } from "../stores/auth";

const authStore = useAuthStore();

const exchangeRate = ref<number | null>(null);

const convertCNY = (value: number | string | null): string => {
  const num = Number(value || 0);
  if (!exchangeRate.value || num === 0) return "";
  const cny = num * exchangeRate.value;
  return `≈ ¥${cny.toFixed(2)}`;
};

const stats = ref({
  total_spend: 0,
  receipt_count: 0,
  by_category: [],
  by_month: [],
  by_day: [],
  by_merchant: [],
  by_payer: [],
  recent_items: []
} as any);

// 同色系深浅渐变调色板
const palette = [
  "rgba(82,132,240,0.82)",
  "rgba(100,148,244,0.78)",
  "rgba(120,164,246,0.74)",
  "rgba(140,178,248,0.7)",
  "rgba(160,192,250,0.66)",
  "rgba(178,204,251,0.62)",
  "rgba(194,214,252,0.58)",
  "rgba(210,224,253,0.54)",
  "rgba(222,232,254,0.5)",
  "rgba(232,240,255,0.46)",
];

const trendMode = ref<"month" | "day">("day");
const selectedCategory = ref<string | null>(null);
const selectedMerchant = ref<string | null>(null);
const selectedPayer = ref<string | null>(null);
const selectedPeriod = ref<{ type: "day" | "month"; label: string } | null>(null);
const sortKey = ref<"total_spent" | "last_purchased">("last_purchased");
const sortDir = ref<"asc" | "desc">("desc");

// ── 分页 ──
const currentPage = ref(1);
const pageSize = ref(10);

function toggleSort(key: "total_spent" | "last_purchased") {
  if (sortKey.value === key) {
    sortDir.value = sortDir.value === "asc" ? "desc" : "asc";
  } else {
    sortKey.value = key;
    sortDir.value = "desc";
  }
}

// ── 时间范围 ──
type PresetKey = "7d" | "30d" | "3m" | "1y" | "all" | "custom";
const presets: { key: PresetKey; label: string }[] = [
  { key: "7d", label: "近 7 天" },
  { key: "30d", label: "近 30 天" },
  { key: "3m", label: "近 3 个月" },
  { key: "1y", label: "近 1 年" },
  { key: "all", label: "全部" },
  { key: "custom", label: "自定义" },
];

const activePreset = ref<PresetKey>("30d");
const dateRange = ref<{ start: string; end: string }>({ start: "", end: "" });

function toISO(d: Date) {
  return d.toISOString().slice(0, 10);
}

function calcPresetRange(key: PresetKey): { start: string; end: string } {
  const now = new Date();
  const end = toISO(now);
  switch (key) {
    case "7d": return { start: toISO(new Date(now.getTime() - 7 * 86400000)), end };
    case "30d": return { start: toISO(new Date(now.getTime() - 30 * 86400000)), end };
    case "3m": {
      const d = new Date(now); d.setMonth(d.getMonth() - 3);
      return { start: toISO(d), end };
    }
    case "1y": {
      const d = new Date(now); d.setFullYear(d.getFullYear() - 1);
      return { start: toISO(d), end };
    }
    default: return { start: "", end: "" };
  }
}

const rangeLabel = computed(() => {
  const p = presets.find((x) => x.key === activePreset.value);
  if (p && activePreset.value !== "custom") return p.label;
  const s = dateRange.value.start;
  const e = dateRange.value.end;
  if (s && e) return `${s} ~ ${e}`;
  if (s) return `${s} 起`;
  if (e) return `至 ${e}`;
  return "全部";
});

async function loadStats() {
  try {
    const { start, end } = dateRange.value;
    const filters: { category?: string; merchant?: string; payer?: string } = {};
    if (selectedCategory.value) filters.category = selectedCategory.value;
    if (selectedMerchant.value) filters.merchant = selectedMerchant.value;
    if (selectedPayer.value) filters.payer = selectedPayer.value;
    stats.value = await fetchStats(start || undefined, end || undefined, filters);
  } catch (err: any) {
    if (err?.response?.status === 401) return;
    console.error("Failed to load stats:", err);
  }
}

function applyPreset(key: PresetKey) {
  activePreset.value = key;
  if (key === "custom") return; // 等用户选日期
  dateRange.value = calcPresetRange(key);
  loadStats();
}

function onCustomStart(e: Event) {
  dateRange.value.start = (e.target as HTMLInputElement).value;
  loadStats();
}

function onCustomEnd(e: Event) {
  dateRange.value.end = (e.target as HTMLInputElement).value;
  loadStats();
}

const filteredItems = computed(() => {
  const items = stats.value.recent_items || [];

  // 1. Filter (category/merchant/payer already filtered by backend)
  const filtered = items.filter((item: any) => {
    if (selectedPeriod.value && item.purchased_at) {
      const d = new Date(item.purchased_at);
      if (isNaN(d.getTime())) return false;
      const mm = String(d.getMonth() + 1).padStart(2, "0");
      const dd = String(d.getDate()).padStart(2, "0");
      const yyyy = d.getFullYear();
      if (selectedPeriod.value.type === "day") {
        if (`${mm}-${dd}` !== selectedPeriod.value.label) return false;
      } else {
        if (`${yyyy}-${mm}` !== selectedPeriod.value.label) return false;
      }
    } else if (selectedPeriod.value && !item.purchased_at) {
      return false;
    }
    return true;
  });

  // 2. Aggregate by name+brand+unit
  const map = new Map<string, any>();
  for (const item of filtered) {
    const key = `${item.name}||${item.brand}||${item.unit}`;
    if (map.has(key)) {
      const ex = map.get(key);
      ex.total_quantity += Number(item.quantity || 0);
      ex.total_spent += Number(item.total_price || 0);
      if (item.purchased_at && (!ex.last_purchased || item.purchased_at > ex.last_purchased)) {
        ex.last_purchased = item.purchased_at;
      }
    } else {
      map.set(key, {
        name: item.name,
        brand: item.brand,
        unit: item.unit,
        total_quantity: Number(item.quantity || 0),
        total_spent: Number(item.total_price || 0),
        last_purchased: item.purchased_at,
      });
    }
  }

  const arr = Array.from(map.values());
  const dir = sortDir.value === "asc" ? 1 : -1;
  if (sortKey.value === "total_spent") {
    arr.sort((a, b) => (a.total_spent - b.total_spent) * dir);
  } else {
    arr.sort((a, b) => ((a.last_purchased || "").localeCompare(b.last_purchased || "")) * dir);
  }
  return arr;
});

const totalPages = computed(() => Math.max(1, Math.ceil(filteredItems.value.length / pageSize.value)));

const paginatedItems = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value;
  return filteredItems.value.slice(start, start + pageSize.value);
});

const visiblePages = computed(() => {
  const total = totalPages.value;
  const cur = currentPage.value;
  const pages: number[] = [];
  let start = Math.max(1, cur - 2);
  let end = Math.min(total, start + 4);
  start = Math.max(1, end - 4);
  for (let i = start; i <= end; i++) pages.push(i);
  return pages;
});

// 筛选/排序/每页条数变化时回到第一页
// 维度筛选变化 → 重新请求后端数据
watch([selectedCategory, selectedMerchant, selectedPayer], () => {
  currentPage.value = 1;
  loadStats();
});

// 排序/分页/时间段筛选 → 仅前端重置页码
watch([selectedPeriod, sortKey, sortDir, pageSize], () => {
  currentPage.value = 1;
});

const onCategoryClick = (params: any) => {
  if (params.name && params.seriesType === "treemap") {
    selectedCategory.value = selectedCategory.value === params.name ? null : params.name;
  }
};

const onMerchantClick = (params: any) => {
  if (params.name && params.seriesType === "bar") {
    selectedMerchant.value = selectedMerchant.value === params.name ? null : params.name;
  }
};

const onTrendClick = (params: any) => {
  if (!params.name) return;
  const type = trendMode.value;
  if (selectedPeriod.value?.type === type && selectedPeriod.value?.label === params.name) {
    selectedPeriod.value = null;
  } else {
    selectedPeriod.value = { type, label: params.name };
  }
};

const onPayerClick = (params: any) => {
  if (params.name && params.seriesType === "bar") {
    selectedPayer.value = selectedPayer.value === params.name ? null : params.name;
  }
};

const formatGBP = (value: number | string | null) => {
  const num = Number(value || 0);
  return new Intl.NumberFormat("en-GB", { style: "currency", currency: "GBP" }).format(num);
};

const formatQuantity = (value: number | string | null) => {
  const num = Number(value || 0);
  return num % 1 === 0 ? num.toString() : num.toFixed(1);
};

const formatDate = (value: string | null) => {
  if (!value) return "-";
  const d = new Date(value);
  if (isNaN(d.getTime())) return value;
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, "0");
  const day = String(d.getDate()).padStart(2, "0");
  return `${y}/${m}/${day}`;
};

const topCategory = computed(() => {
  if (!stats.value.by_category?.length) return "-";
  return stats.value.by_category[0].category_main__name || "-";
});

const categoryChart = computed(() => {
  const data = stats.value.by_category || [];
  return {
    title: { text: "主类消费分布", left: "left" },
    tooltip: {
      backgroundColor: "rgba(255,255,255,0.9)",
      borderColor: "rgba(0,0,0,0.08)",
      textStyle: { color: "#1c1c1e" },
      formatter: (info: any) => {
        const val = Number(info.value || 0);
        const cny = convertCNY(val);
        return `<b>${info.name}</b><br/>£${val.toFixed(2)}${cny ? `（${cny}）` : ''}`;
      }
    },
    series: [
      {
        type: "treemap",
        width: "100%",
        height: "80%",
        top: 36,
        roam: false,
        nodeClick: "link",
        breadcrumb: { show: false },
        label: {
          show: true,
          formatter: "{b}",
          fontSize: 13,
          fontWeight: 600,
          color: "#1c1c1e"
        },
        itemStyle: {
          borderColor: "#fff",
          borderWidth: 2,
          gapWidth: 2
        },
        data: data.map((item: any, i: number) => ({
          name: item.category_main__name || "未分类",
          value: Number(item.total || 0),
          itemStyle: { color: palette[i % palette.length] }
        }))
      }
    ]
  };
});

const trendChart = computed(() => {
  const isDay = trendMode.value === "day";
  const data = isDay ? (stats.value.by_day || []) : (stats.value.by_month || []);

  const xLabels = data.map((item: any) => {
    if (isDay) {
      return item.day ? item.day.slice(5, 10) : "";
    }
    return item.month ? item.month.slice(0, 7) : "";
  });

  return {
    tooltip: { trigger: "axis", backgroundColor: "rgba(255,255,255,0.9)", borderColor: "rgba(0,0,0,0.08)", textStyle: { color: "#1c1c1e" } },
    grid: { top: 16, right: 16, bottom: 28, left: 48 },
    xAxis: {
      type: "category",
      data: xLabels,
      axisLabel: { rotate: isDay ? 45 : 0, fontSize: isDay ? 10 : 11 }
    },
    yAxis: { type: "value" },
    series: [
      isDay
        ? {
            type: "line",
            smooth: true,
            data: data.map((item: any) => item.total),
            areaStyle: {
              color: {
                type: "linear", x: 0, y: 0, x2: 0, y2: 1,
                colorStops: [
                  { offset: 0, color: "rgba(100,148,244,0.3)" },
                  { offset: 1, color: "rgba(100,148,244,0.02)" }
                ]
              }
            },
            lineStyle: { width: 2.5, color: "rgba(82,132,240,0.8)" },
            itemStyle: { color: "rgba(82,132,240,0.8)" },
            symbol: "circle",
            symbolSize: 6
          }
        : {
            type: "bar",
            data: data.map((item: any) => item.total),
            itemStyle: {
              borderRadius: [6, 6, 0, 0],
              color: "rgba(120,164,246,0.6)"
            }
          }
    ]
  };
});

const merchantChart = computed(() => {
  const data = (stats.value.by_merchant || []).slice(0, 10);
  // 倒序排列使最大值在顶部
  const sorted = [...data].reverse();
  return {
    title: { text: "店铺消费排名（Top 10）", left: "left" },
    tooltip: {
      backgroundColor: "rgba(255,255,255,0.9)",
      borderColor: "rgba(0,0,0,0.08)",
      textStyle: { color: "#1c1c1e" },
      formatter: (info: any) => {
        const val = Number(info.value || 0);
        const cny = convertCNY(val);
        return `<b>${info.name}</b><br/>£${val.toFixed(2)}${cny ? `（${cny}）` : ''}`;
      },
    },
    grid: { top: 36, right: 60, bottom: 8, left: 140 },
    xAxis: { type: "value" },
    yAxis: {
      type: "category",
      data: sorted.map((item: any) => item.merchant_name || "未知店铺"),
      axisLabel: { fontSize: 12 },
    },
    series: [
      {
        type: "bar",
        data: sorted.map((item: any, i: number) => ({
          value: Number(item.total || 0),
          itemStyle: {
            color: palette[i % palette.length],
            borderRadius: [0, 6, 6, 0],
          },
        })),
        label: {
          show: true,
          position: "right",
          formatter: (p: any) => `£${Number(p.value).toFixed(2)}`,
          fontSize: 11,
          color: "#666",
        },
      },
    ],
  };
});

const payerChart = computed(() => {
  const data = stats.value.by_payer || [];
  return {
    title: { text: "成员付款分布", left: "left" },
    tooltip: {
      backgroundColor: "rgba(255,255,255,0.9)",
      borderColor: "rgba(0,0,0,0.08)",
      textStyle: { color: "#1c1c1e" },
      formatter: (info: any) => {
        const val = Number(info.value || 0);
        const cny = convertCNY(val);
        return `<b>${info.name}</b><br/>£${val.toFixed(2)}${cny ? `（${cny}）` : ''}`;
      },
    },
    grid: { top: 36, right: 16, bottom: 28, left: 48 },
    xAxis: {
      type: "category",
      data: data.map((item: any) => item.payer_name || "未指定"),
      axisLabel: { fontSize: 12 },
    },
    yAxis: { type: "value" },
    series: [
      {
        type: "bar",
        data: data.map((item: any, i: number) => ({
          value: Number(item.total || 0),
          itemStyle: {
            color: palette[i % palette.length],
            borderRadius: [6, 6, 0, 0],
          },
        })),
        label: {
          show: true,
          position: "top",
          formatter: (p: any) => `£${Number(p.value).toFixed(2)}`,
          fontSize: 11,
          color: "#666",
        },
      },
    ],
  };
});

onMounted(() => {
  dateRange.value = calcPresetRange("30d");
  loadStats();
  getExchangeRate()
    .then((res) => { if (res.rate) exchangeRate.value = res.rate; })
    .catch(() => {});
});
</script>

<style scoped>
.cny-hint {
  color: var(--muted);
  font-size: 11px;
  margin-left: 4px;
}

.date-range-bar {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
  flex-wrap: wrap;
}

.exchange-rate-badge {
  margin-left: auto;
  font-size: 12px;
  font-weight: 600;
  color: var(--muted);
  background: rgba(0, 0, 0, 0.03);
  padding: 4px 10px;
  border-radius: 6px;
  white-space: nowrap;
}

.range-presets {
  display: inline-flex;
  background: rgba(0, 0, 0, 0.04);
  border-radius: 8px;
  padding: 2px;
}

.range-presets button {
  border: none;
  background: transparent;
  padding: 5px 14px;
  font-size: 12px;
  font-weight: 600;
  font-family: inherit;
  color: var(--muted);
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.range-presets button.active {
  background: #fff;
  color: var(--accent);
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08);
}

.custom-dates {
  display: inline-flex;
  align-items: center;
  gap: 8px;
}

.custom-dates input[type="date"] {
  padding: 4px 10px;
  border: 1px solid var(--border);
  border-radius: 6px;
  font-size: 12px;
  font-family: inherit;
  background: #fff;
  color: var(--text);
}

.date-sep {
  font-size: 12px;
  color: var(--muted);
}

.empty-state {
  text-align: center;
  padding: 36px 0;
  animation: fadeIn 0.4s ease;
}

.empty-state__icon {
  color: var(--muted);
  margin-bottom: 10px;
}

.empty-state__text {
  color: var(--muted);
  font-size: 14px;
}

.trend-panel {
  display: flex;
  flex-direction: column;
}

.trend-panel h2 {
  margin: 0;
}

.trend-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}

.trend-toggle {
  display: inline-flex;
  background: rgba(0, 0, 0, 0.04);
  border-radius: 8px;
  padding: 2px;
}

.trend-toggle button {
  border: none;
  background: transparent;
  padding: 5px 14px;
  font-size: 12px;
  font-weight: 600;
  font-family: inherit;
  color: var(--muted);
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.trend-toggle button.active {
  background: #fff;
  color: var(--accent);
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08);
}

.trend-chart-inner {
  flex: 1;
  border: none;
  box-shadow: none;
  padding: 0;
  background: transparent;
  backdrop-filter: none;
  -webkit-backdrop-filter: none;
  animation: none;
  border-radius: 0;
  min-height: 260px;
}

.recent-header {
  display: flex;
  align-items: center;
  gap: 10px;
}

.recent-header h2 {
  margin: 0;
}

.filter-tag {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 4px 12px;
  font-size: 12px;
  font-weight: 600;
  font-family: inherit;
  color: rgba(59,130,246,1);
  background: rgba(59,130,246,0.08);
  border: 1px solid rgba(59,130,246,0.15);
  border-radius: 20px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.filter-tag:hover {
  background: rgba(59,130,246,0.14);
}

.filter-tag__x {
  font-size: 15px;
  line-height: 1;
  margin-left: 2px;
}

.card-grid--single {
  display: grid;
  grid-template-columns: 1fr;
}

.sortable-th {
  cursor: pointer;
  user-select: none;
  transition: color 0.2s ease;
}

.sortable-th:hover {
  color: var(--accent);
}

.sortable-th.sorted {
  color: var(--accent);
}

.sort-arrow {
  font-size: 12px;
  margin-left: 4px;
  opacity: 0.5;
}

.sortable-th.sorted .sort-arrow {
  opacity: 1;
}

.pagination {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  margin-top: 16px;
  padding-top: 14px;
  border-top: 1px solid var(--border);
  flex-wrap: wrap;
}

.pagination__info {
  font-size: 12px;
  color: var(--muted);
  white-space: nowrap;
}

.pagination__controls {
  display: inline-flex;
  gap: 4px;
}

.pagination__controls button {
  min-width: 32px;
  height: 32px;
  border: 1px solid var(--border);
  background: #fff;
  border-radius: 6px;
  font-size: 13px;
  font-weight: 600;
  font-family: inherit;
  color: var(--text);
  cursor: pointer;
  transition: all 0.2s ease;
}

.pagination__controls button:hover:not(:disabled):not(.active) {
  background: rgba(0, 0, 0, 0.04);
  border-color: var(--accent);
  color: var(--accent);
}

.pagination__controls button.active {
  background: var(--accent);
  border-color: var(--accent);
  color: #fff;
}

.pagination__controls button:disabled {
  opacity: 0.35;
  cursor: not-allowed;
}

.pagination__size {
  padding: 4px 8px;
  border: 1px solid var(--border);
  border-radius: 6px;
  font-size: 12px;
  font-family: inherit;
  background: #fff;
  color: var(--text);
  cursor: pointer;
}

@media (max-width: 640px) {
  .date-range-bar {
    gap: 8px;
  }

  .range-presets {
    flex-wrap: wrap;
    gap: 2px;
  }

  .range-presets button {
    padding: 5px 10px;
    font-size: 11px;
  }

  .recent-header {
    flex-wrap: wrap;
    gap: 6px;
  }

  .table thead {
    display: none;
  }

  .recent-row {
    display: flex;
    flex-wrap: wrap;
    gap: 6px 12px;
    padding: 12px 0;
    border-bottom: 1px solid var(--border);
  }

  .recent-row td {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 0;
    border-bottom: none;
    font-size: 13px;
  }

  .recent-row td::before {
    content: attr(data-label);
    font-size: 11px;
    font-weight: 600;
    color: var(--muted);
  }

  .pagination {
    gap: 8px;
  }

  .pagination__controls button {
    min-width: 28px;
    height: 28px;
    font-size: 12px;
  }

  .pagination__info {
    font-size: 11px;
    width: 100%;
    text-align: center;
    order: -1;
  }
}
</style>
