<script setup>
// 简化版铃铛：只展示未读 badge + 点击事件交给父组件（通常是打开右侧 panel 切到 Inbox tab）
defineProps({
  unreadCount: { type: Number, default: 0 },
})
const emit = defineEmits(['click'])
</script>

<template>
  <button
    @click.stop="emit('click')"
    class="w-8 h-8 rounded-md flex items-center justify-center transition-colors cursor-pointer relative"
    style="color: var(--theme-400);"
    title="通知"
    @mouseenter="$event.currentTarget.style.color = 'var(--theme-700)'"
    @mouseleave="$event.currentTarget.style.color = 'var(--theme-400)'"
  >
    <svg class="w-[18px] h-[18px]" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="1.5">
      <path stroke-linecap="round" stroke-linejoin="round" d="M14.857 17.082a23.848 23.848 0 005.454-1.31A8.967 8.967 0 0118 9.75v-.7V9A6 6 0 006 9v.75a8.967 8.967 0 01-2.312 6.022c1.733.64 3.56 1.085 5.455 1.31m5.714 0a24.255 24.255 0 01-5.714 0m5.714 0a3 3 0 11-5.714 0"/>
    </svg>
    <span
      v-if="unreadCount > 0"
      class="absolute top-0.5 right-0.5 min-w-[14px] h-[14px] rounded-full text-[10px] font-semibold flex items-center justify-center px-1"
      style="background: #ef4444; color: #fff;"
    >{{ unreadCount > 99 ? '99+' : unreadCount }}</span>
  </button>
</template>
