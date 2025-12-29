<script setup>
defineProps({
  isRecording: Boolean,
  disabled: Boolean,
})

defineEmits(['click'])
</script>

<template>
  <button
    @click="$emit('click')"
    :disabled="disabled"
    class="relative flex items-center justify-center transition-all duration-300 focus:outline-none disabled:opacity-50 disabled:cursor-not-allowed"
  >
    <!-- Outer Ring (Border) -->
    <div 
      class="w-20 h-20 rounded-full border-[3px] transition-colors duration-300 flex items-center justify-center"
      :class="isRecording ? 'border-ios-red' : 'border-white/20 group-hover:border-white/40'"
    >
      <!-- Core Button -->
      <div
        class="rounded-full transition-all duration-300 shadow-lg"
        :class="[
          isRecording 
            ? 'w-10 h-10 bg-ios-red rounded-[6px]' /* Square when recording */
            : 'w-16 h-16 bg-ios-red hover:bg-red-500 rounded-full' /* Circle when idle */
        ]"
      ></div>
    </div>
    
    <!-- Ripple Effect when recording -->
    <div 
      v-if="isRecording"
      class="absolute inset-0 rounded-full border border-ios-red opacity-50 animate-ping"
    ></div>
  </button>
</template>
