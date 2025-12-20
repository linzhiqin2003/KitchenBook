<template>
  <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8 max-w-6xl w-full px-4">
    <div 
      v-for="spread in spreads" 
      :key="spread.id"
      @click="$emit('select', spread)"
      class="relative group cursor-pointer bg-gradient-to-br from-gray-900 to-black border border-gray-800 rounded-2xl p-8 hover:border-mystic-gold transition-all duration-300 hover:shadow-xl hover:shadow-mystic-gold/20 hover:-translate-y-1"
    >
      <!-- Card Count Badge -->
      <div class="absolute -top-3 -right-3 bg-mystic-gold text-black text-sm font-bold px-3 py-1.5 rounded-full shadow-lg font-chinese-body">
        {{ spread.card_count }}牌
      </div>
      
      <!-- Spread Info -->
      <h3 class="text-2xl text-mystic-gold mb-3 font-chinese-title">{{ spread.name_cn }}</h3>
      <p class="text-base text-gray-400 mb-5 line-clamp-2 font-chinese-body">{{ spread.description }}</p>
      
      <!-- Positions Preview -->
      <div class="flex flex-wrap gap-1">
        <span 
          v-for="(pos, idx) in spread.positions.slice(0, 3)" 
          :key="idx"
          class="text-xs bg-gray-800 text-gray-300 px-2 py-1 rounded"
        >
          {{ pos }}
        </span>
        <span v-if="spread.positions.length > 3" class="text-xs text-gray-500">
          +{{ spread.positions.length - 3 }} more
        </span>
      </div>
      
      <!-- Hover Glow -->
      <div class="absolute inset-0 rounded-xl bg-gradient-to-br from-mystic-gold/0 to-mystic-purple/0 group-hover:from-mystic-gold/5 group-hover:to-mystic-purple/10 transition-all duration-300 pointer-events-none"></div>
    </div>
  </div>
</template>

<script setup>
defineProps({
  spreads: {
    type: Array,
    required: true
  }
});

defineEmits(['select']);
</script>
