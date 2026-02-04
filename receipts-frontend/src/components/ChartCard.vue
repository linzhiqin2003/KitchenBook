<template>
  <div class="panel chart-panel" ref="chartEl"></div>
</template>

<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref, watch } from "vue";
import * as echarts from "echarts";

const props = defineProps<{ options: echarts.EChartsOption }>();
const emit = defineEmits<{ (e: "chartClick", params: any): void }>();
const chartEl = ref<HTMLDivElement | null>(null);
let chart: echarts.ECharts | null = null;

const appleTheme = {
  color: ["#007aff", "#5ac8fa", "#34c759", "#ff9f0a", "#ff3b30", "#af52de", "#ff2d55", "#5856d6"],
  backgroundColor: "transparent",
  textStyle: { fontFamily: "DM Sans, -apple-system, sans-serif" },
  title: {
    textStyle: { fontSize: 15, fontWeight: 600, fontFamily: "Space Grotesk, sans-serif", color: "#1c1c1e" }
  },
  categoryAxis: {
    axisLine: { lineStyle: { color: "rgba(0,0,0,0.08)" } },
    axisLabel: { color: "#8e8e93", fontSize: 11 },
    splitLine: { lineStyle: { color: "rgba(0,0,0,0.04)" } }
  },
  valueAxis: {
    axisLine: { show: false },
    axisLabel: { color: "#8e8e93", fontSize: 11 },
    splitLine: { lineStyle: { color: "rgba(0,0,0,0.06)" } }
  }
};

const initChart = () => {
  if (!chart && chartEl.value) {
    echarts.registerTheme("apple", appleTheme);
    chart = echarts.init(chartEl.value, "apple");
  }
};

const render = () => {
  initChart();
  if (chart) {
    chart.setOption(props.options, true);
  }
};

const handleResize = () => {
  chart?.resize();
};

onMounted(() => {
  render();
  if (chart) {
    chart.on("click", (params: any) => emit("chartClick", params));
  }
  window.addEventListener("resize", handleResize);
});

watch(
  () => props.options,
  () => render(),
  { deep: true }
);

onBeforeUnmount(() => {
  window.removeEventListener("resize", handleResize);
  chart?.dispose();
});
</script>
