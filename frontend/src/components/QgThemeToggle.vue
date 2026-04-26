<template>
  <button
    type="button"
    class="qg-theme-toggle"
    :aria-label="`主题：${labels[mode]}（点击切换）`"
    :title="`主题：${labels[mode]}`"
    @click="cycle"
  >
    <!-- Sun -->
    <svg v-if="resolved === 'light'" viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">
      <circle cx="12" cy="12" r="4"/>
      <path d="M12 3v1.5M12 19.5V21M4.22 4.22l1.06 1.06M18.72 18.72l1.06 1.06M3 12h1.5M19.5 12H21M4.22 19.78l1.06-1.06M18.72 5.28l1.06-1.06"/>
    </svg>
    <!-- Moon -->
    <svg v-else viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">
      <path d="M21 12.5A8.5 8.5 0 1 1 11.5 3a6.5 6.5 0 0 0 9.5 9.5z"/>
    </svg>
    <span class="qg-theme-toggle__mode" :data-mode="mode">{{ labels[mode] }}</span>
  </button>
</template>

<script setup>
import { useQgTheme } from '../composables/useQgTheme';

const { mode, resolved, cycle } = useQgTheme();

const labels = {
  light: 'Light',
  dark:  'Dark',
  system: 'Auto',
};
</script>

<style scoped>
.qg-theme-toggle {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 6px 10px 6px 8px;
  background: transparent;
  color: var(--qg-text-secondary);
  border: 1px solid var(--qg-border-default);
  border-radius: var(--qg-radius-md);
  font-family: var(--qg-font-mono);
  font-size: 11px;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  cursor: pointer;
  transition: background var(--qg-dur-fast) var(--qg-ease),
              color var(--qg-dur-fast) var(--qg-ease),
              border-color var(--qg-dur-fast) var(--qg-ease);
}
.qg-theme-toggle:hover {
  color: var(--qg-text-primary);
  background: var(--qg-surface-sunken);
  border-color: var(--qg-border-strong);
}
.qg-theme-toggle:focus-visible {
  outline: none;
  box-shadow: var(--qg-shadow-focus);
}
.qg-theme-toggle__mode {
  font-weight: 500;
}
</style>
