<script setup>
import { ref, watch, onUnmounted } from 'vue'

const props = defineProps({
  isActive: Boolean,
  analyser: Object,
})

const bars = ref(Array(24).fill(4)) // Increased resolution
let animationId = null

function visualize() {
  if (!props.isActive || !props.analyser) {
    bars.value = Array(24).fill(4)
    return
  }
  
  const bufferLength = props.analyser.frequencyBinCount
  const dataArray = new Uint8Array(bufferLength)
  props.analyser.getByteFrequencyData(dataArray)
  
  // Sample spread across the spectrum
  const step = Math.floor(bufferLength / 24)
  const newBars = []
  
  for (let i = 0; i < 24; i++) {
    const value = dataArray[i * step]
    // Smoother scaling
    const height = Math.max(4, (value / 255) * 100)
    newBars.push(height)
  }
  
  bars.value = newBars
  animationId = requestAnimationFrame(visualize)
}

watch(() => props.isActive, (active) => {
  if (active) {
    visualize()
  } else {
    if (animationId) {
      cancelAnimationFrame(animationId)
      animationId = null
    }
    bars.value = Array(24).fill(4)
  }
})

onUnmounted(() => {
  if (animationId) {
    cancelAnimationFrame(animationId)
  }
})
</script>

<template>
  <div class="flex items-center justify-center gap-[2px] h-12 w-full">
    <div
      v-for="(height, index) in bars"
      :key="index"
      class="w-1 rounded-full transition-all duration-75"
      :class="isActive ? 'bg-ios-red' : 'bg-ios-gray/30'"
      :style="{ height: `${height}%` }"
    ></div>
  </div>
</template>
