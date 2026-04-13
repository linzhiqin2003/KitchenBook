<script setup>
import { ref, onMounted, onUnmounted, watch, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import * as d3 from 'd3'

const props = defineProps({
  nodes: { type: Array, default: () => [] },
  edges: { type: Array, default: () => [] },
  isDarkTheme: { type: Boolean, default: true }
})

const router = useRouter()
const container = ref(null)
const tooltip = ref({ show: false, x: 0, y: 0, node: null })
let simulation = null
let svg = null
let resizeObserver = null

const theme = {
  dark: {
    bg: 'transparent',
    nodeFill: '#1e1e2e',
    nodeStroke: '#6366f1',
    nodeStrokeHover: '#a78bfa',
    text: '#e2e8f0',
    textMuted: '#94a3b8',
    link: '#334155',
    linkHover: '#6366f1',
    glow: 'rgba(99, 102, 241, 0.3)',
  },
  light: {
    bg: 'transparent',
    nodeFill: '#ffffff',
    nodeStroke: '#cbd5e1',
    nodeStrokeHover: '#475569',
    text: '#1e293b',
    textMuted: '#64748b',
    link: '#e2e8f0',
    linkHover: '#475569',
    glow: 'rgba(0, 0, 0, 0.08)',
  }
}

const getTheme = () => props.isDarkTheme ? theme.dark : theme.light

// 截断文字
const truncate = (text, maxLen) => text.length > maxLen ? text.slice(0, maxLen) + '...' : text

const buildGraph = () => {
  if (!container.value || !props.nodes.length) return

  // 清除旧图
  d3.select(container.value).selectAll('*').remove()

  const rect = container.value.getBoundingClientRect()
  const width = rect.width
  const height = rect.height || 500
  const t = getTheme()

  // 节点显示名（取冒号前的短标题，否则完整标题）
  const displayName = (title) => {
    const short = title.split(/[：:]/)[0].trim()
    return short.length > 12 ? short.slice(0, 12) + '…' : short
  }

  // 节点大小：按显示文字长度自适应
  const nodeRadius = (n) => {
    const name = displayName(n.title)
    return Math.max(32, name.length * 7 + 16)
  }

  // 复制数据（D3 会修改原数据）
  const nodes = props.nodes.map(n => ({ ...n }))
  const edges = props.edges.map(e => ({ ...e }))

  svg = d3.select(container.value)
    .append('svg')
    .attr('width', width)
    .attr('height', height)

  // 缩放 + 拖拽画布
  const g = svg.append('g')
  const zoom = d3.zoom()
    .scaleExtent([0.3, 3])
    .on('zoom', (event) => g.attr('transform', event.transform))
  svg.call(zoom)

  // 箭头标记
  svg.append('defs').append('marker')
    .attr('id', 'arrowhead')
    .attr('viewBox', '0 -5 10 10')
    .attr('refX', 8)
    .attr('refY', 0)
    .attr('markerWidth', 6)
    .attr('markerHeight', 6)
    .attr('orient', 'auto')
    .append('path')
    .attr('d', 'M0,-4L8,0L0,4')
    .attr('fill', t.link)

  // 力模拟
  simulation = d3.forceSimulation(nodes)
    .force('link', d3.forceLink(edges).id(d => d.id).distance(140).strength(0.5))
    .force('charge', d3.forceManyBody().strength(-600))
    .force('center', d3.forceCenter(width / 2, height / 2))
    .force('collision', d3.forceCollide().radius(d => nodeRadius(d) + 15))

  // 连线
  const link = g.append('g')
    .selectAll('line')
    .data(edges)
    .join('line')
    .attr('stroke', t.link)
    .attr('stroke-width', 1.5)
    .attr('marker-end', 'url(#arrowhead)')

  // 节点组
  const node = g.append('g')
    .selectAll('g')
    .data(nodes)
    .join('g')
    .style('cursor', 'pointer')
    .call(d3.drag()
      .on('start', dragStarted)
      .on('drag', dragged)
      .on('end', dragEnded)
    )

  // 节点圆形
  node.append('circle')
    .attr('r', d => nodeRadius(d))
    .attr('fill', t.nodeFill)
    .attr('stroke', t.nodeStroke)
    .attr('stroke-width', 2)
    .style('filter', `drop-shadow(0 2px 8px ${t.glow})`)
    .style('transition', 'stroke 0.2s, filter 0.2s')

  // 节点文字
  node.append('text')
    .text(d => displayName(d.title))
    .attr('text-anchor', 'middle')
    .attr('dy', '0.35em')
    .attr('fill', t.text)
    .attr('font-size', '11px')
    .attr('font-weight', '600')
    .style('pointer-events', 'none')
    .style('user-select', 'none')

  // 交互
  node.on('mouseenter', (event, d) => {
    // 高亮节点
    d3.select(event.currentTarget).select('circle')
      .attr('stroke', t.nodeStrokeHover)
      .attr('stroke-width', 3)
      .style('filter', `drop-shadow(0 4px 16px ${t.glow})`)

    // 高亮关联边
    link.attr('stroke', l =>
      l.source.id === d.id || l.target.id === d.id ? t.linkHover : t.link
    ).attr('stroke-width', l =>
      l.source.id === d.id || l.target.id === d.id ? 2.5 : 1.5
    )

    // Tooltip
    const svgRect = container.value.getBoundingClientRect()
    tooltip.value = {
      show: true,
      x: event.clientX - svgRect.left,
      y: event.clientY - svgRect.top - 10,
      node: d
    }
  })
  .on('mouseleave', (event) => {
    d3.select(event.currentTarget).select('circle')
      .attr('stroke', t.nodeStroke)
      .attr('stroke-width', 2)
      .style('filter', `drop-shadow(0 2px 8px ${t.glow})`)

    link.attr('stroke', t.link).attr('stroke-width', 1.5)
    tooltip.value.show = false
  })
  .on('click', (event, d) => {
    event.stopPropagation()
    router.push(`/blog/${d.slug}`)
  })

  // Tick — 连线端点缩短到圆圈边缘
  simulation.on('tick', () => {
    link.each(function(d) {
      const dx = d.target.x - d.source.x
      const dy = d.target.y - d.source.y
      const dist = Math.sqrt(dx * dx + dy * dy) || 1
      const sr = nodeRadius(d.source) + 2
      const tr = nodeRadius(d.target) + 10 // 留出箭头空间
      d3.select(this)
        .attr('x1', d.source.x + dx / dist * sr)
        .attr('y1', d.source.y + dy / dist * sr)
        .attr('x2', d.target.x - dx / dist * tr)
        .attr('y2', d.target.y - dy / dist * tr)
    })

    node.attr('transform', d => `translate(${d.x},${d.y})`)
  })

  // 初始缩放适应
  simulation.on('end', () => {
    const bounds = g.node().getBBox()
    const padding = 60
    const scale = Math.min(
      width / (bounds.width + padding * 2),
      height / (bounds.height + padding * 2),
      1.2
    )
    const tx = width / 2 - (bounds.x + bounds.width / 2) * scale
    const ty = height / 2 - (bounds.y + bounds.height / 2) * scale
    svg.transition().duration(500).call(
      zoom.transform,
      d3.zoomIdentity.translate(tx, ty).scale(scale)
    )
  })

  function dragStarted(event, d) {
    if (!event.active) simulation.alphaTarget(0.3).restart()
    d.fx = d.x
    d.fy = d.y
  }
  function dragged(event, d) {
    d.fx = event.x
    d.fy = event.y
    tooltip.value.show = false
  }
  function dragEnded(event, d) {
    if (!event.active) simulation.alphaTarget(0)
    d.fx = null
    d.fy = null
  }
}

onMounted(() => {
  nextTick(buildGraph)
  resizeObserver = new ResizeObserver(() => {
    if (simulation) {
      simulation.stop()
      simulation = null
    }
    buildGraph()
  })
  if (container.value) resizeObserver.observe(container.value)
})

onUnmounted(() => {
  if (simulation) simulation.stop()
  if (resizeObserver) resizeObserver.disconnect()
})

watch(() => [props.nodes, props.edges, props.isDarkTheme], () => {
  if (simulation) {
    simulation.stop()
    simulation = null
  }
  nextTick(buildGraph)
}, { deep: true })
</script>

<template>
  <div ref="container" class="w-full h-[500px] md:h-[600px] relative rounded-xl overflow-hidden">
    <!-- Tooltip -->
    <Transition name="fade">
      <div
        v-if="tooltip.show && tooltip.node"
        class="absolute z-50 pointer-events-none"
        :style="{ left: tooltip.x + 'px', top: tooltip.y + 'px', transform: 'translate(-50%, -100%)' }"
      >
        <div :class="[
          'px-4 py-3 rounded-xl shadow-xl border max-w-[240px]',
          isDarkTheme ? 'bg-[#1e1e2e] border-white/10 text-white' : 'bg-white border-slate-200 text-slate-800'
        ]">
          <div class="font-bold text-sm mb-1">{{ tooltip.node.title }}</div>
          <div :class="['text-xs leading-relaxed', isDarkTheme ? 'text-slate-400' : 'text-slate-500']">
            {{ tooltip.node.summary || '暂无摘要' }}
          </div>
          <div :class="['text-xs mt-2 flex items-center gap-3', isDarkTheme ? 'text-slate-500' : 'text-slate-400']">
            <span>{{ tooltip.node.reading_time }} min</span>
            <span>{{ tooltip.node.view_count }} 次阅读</span>
          </div>
        </div>
      </div>
    </Transition>
  </div>
</template>

<style scoped>
.fade-enter-active, .fade-leave-active {
  transition: opacity 0.15s;
}
.fade-enter-from, .fade-leave-to {
  opacity: 0;
}
</style>
