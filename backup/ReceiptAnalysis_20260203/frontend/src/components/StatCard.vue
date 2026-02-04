<template>
  <div class="stat-card">
    <div class="stat-header">
      <div class="label">{{ label }}</div>
      <div v-if="$slots.icon" class="stat-icon">
        <slot name="icon" />
      </div>
    </div>
    <div class="value">{{ value }}</div>
    <div v-if="subtitle" class="subtitle">{{ subtitle }}</div>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  label: string;
  value: string | number;
  subtitle?: string;
}>();
</script>

<style scoped>
.subtitle {
  color: var(--muted);
  font-size: 12px;
  margin-top: 6px;
}
</style>
