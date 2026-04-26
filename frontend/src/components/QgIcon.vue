<template>
  <svg
    :width="size"
    :height="size"
    :viewBox="viewBox"
    fill="none"
    stroke="currentColor"
    :stroke-width="strokeWidth"
    stroke-linecap="round"
    stroke-linejoin="round"
    aria-hidden="true"
    class="qg-icon"
  >
    <component :is="path" />
  </svg>
</template>

<script setup>
import { h, computed } from 'vue';

const props = defineProps({
  name: { type: String, required: true },
  size: { type: [Number, String], default: 16 },
  strokeWidth: { type: [Number, String], default: 1.6 },
});

const viewBox = '0 0 24 24';

/**
 * Inline-stroke SVG icons. Each entry returns the inner geometry.
 * Naming convention: lowercase noun, no abstractions — e.g. "target",
 * "doc", "pen", "wrench", "cpu". Add new icons here as the UI needs them.
 */
const ICONS = {
  // study modes
  target: () => [
    h('circle', { cx: 12, cy: 12, r: 9 }),
    h('circle', { cx: 12, cy: 12, r: 5 }),
    h('circle', { cx: 12, cy: 12, r: 1.6, fill: 'currentColor', stroke: 'none' }),
  ],
  note: () => [
    h('path', { d: 'M5 4h11l3 3v13H5z' }),
    h('path', { d: 'M16 4v3h3' }),
    h('path', { d: 'M8 11h8M8 15h8M8 19h5' }),
  ],
  doc: () => [
    h('path', { d: 'M7 3h7l4 4v14H7z' }),
    h('path', { d: 'M14 3v4h4' }),
    h('path', { d: 'M10 12h6M10 16h6' }),
  ],
  // question types — kept for future use (current TYPE segment uses text)
  mcq: () => [
    h('rect', { x: 3, y: 5, width: 18, height: 14, rx: 2 }),
    h('path', { d: 'M7 10l2 2 3-3' }),
    h('path', { d: 'M14 10h4M14 14h2' }),
  ],
  fill: () => [
    h('path', { d: 'M4 17h16' }),
    h('path', { d: 'M4 13h6m4 0h6' }),
  ],
  pen: () => [
    h('path', { d: 'M14 4l6 6L8 22H2v-6z' }),
    h('path', { d: 'M14 4l3-3 6 6-3 3' }),
  ],
  // courses
  wrench: () => [
    h('path', { d: 'M14.7 6.3a4 4 0 1 0 5 5L21 14a8 8 0 0 1-11 11l-1.7-1.3a4 4 0 0 0-5-5L2 17a8 8 0 0 1 11-11z' }),
  ],
  cpu: () => [
    h('rect', { x: 5, y: 5, width: 14, height: 14, rx: 2 }),
    h('rect', { x: 9, y: 9, width: 6, height: 6, rx: 1 }),
    h('path', { d: 'M9 1v3M15 1v3M9 20v3M15 20v3M1 9h3M1 15h3M20 9h3M20 15h3' }),
  ],
  monitor: () => [
    h('rect', { x: 3, y: 4, width: 18, height: 13, rx: 2 }),
    h('path', { d: 'M8 21h8M12 17v4' }),
  ],
  code: () => [
    h('path', { d: 'M9 18l-6-6 6-6M15 6l6 6-6 6' }),
  ],
  // misc
  check: () => [h('path', { d: 'M5 12l4 4L19 7' })],
  minus: () => [h('path', { d: 'M6 12h12' })],
  arrow_right: () => [h('path', { d: 'M5 12h14M13 6l6 6-6 6' })],
};

const path = computed(() => () => h('g', {}, (ICONS[props.name] || (() => []))()));
</script>

<style scoped>
.qg-icon {
  flex-shrink: 0;
  vertical-align: middle;
}
</style>
