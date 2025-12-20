<template>
  <div 
    class="relative w-48 h-80 perspective-1000 cursor-pointer group"
    @click="flip"
  >
    <div 
      class="relative w-full h-full transition-transform duration-700 transform-style-3d shadow-xl rounded-xl"
      :class="{ 'rotate-y-180': isFlipped }"
    >
      <!-- Card Back -->
      <div class="absolute w-full h-full backface-hidden rounded-xl border-2 border-mystic-gold bg-mystic-dark flex items-center justify-center overflow-hidden">
        <div class="absolute inset-0 bg-opacity-20 bg-pattern-mystic"></div>
        <div class="text-mystic-gold text-4xl opacity-50">✧</div>
      </div>

      <!-- Card Front -->
      <div class="absolute w-full h-full backface-hidden rotate-y-180 rounded-xl overflow-hidden border-2 border-mystic-gold bg-black">
        <img 
          :src="imageSrc" 
          :alt="card.name" 
          class="w-full h-full object-cover"
        />
        <div class="absolute bottom-0 w-full bg-black bg-opacity-70 text-center py-2">
            <span class="text-mystic-gold font-mystic text-sm">{{ card.name }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue';

const props = defineProps({
  card: {
    type: Object,
    required: true
  },
  revealed: {
      type: Boolean,
      default: false
  }
});

const isInternalFlipped = ref(false);

const isFlipped = computed(() => props.revealed || isInternalFlipped.value);

const imageSrc = computed(() => {
    // Assuming images are in public/cards/
    return `/cards/${props.card.img}`;
});

function flip() {
    if (!props.revealed) {
        isInternalFlipped.value = !isInternalFlipped.value;
    }
}
</script>

<style scoped>
.perspective-1000 {
  perspective: 1000px;
}
.transform-style-3d {
  transform-style: preserve-3d;
}
.backface-hidden {
  backface-visibility: hidden;
}
.rotate-y-180 {
  transform: rotateY(180deg);
}
</style>
