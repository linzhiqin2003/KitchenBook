<template>
  <div class="min-h-screen bg-mystic-dark text-mystic-gold flex flex-col items-center justify-center p-8 text-center relative overflow-hidden font-mystic">
    <!-- Animated Starfield Background -->
    <StarField />
    
    <div class="relative z-10">
      <h1 class="text-6xl mb-4 tracking-widest uppercase drop-shadow-xl glow-text">Tarot Sanctum</h1>
      <p class="text-xl text-gray-400 mb-12 max-w-md">Enter the void. Ask the universe. Receive your truth.</p>
      
      <router-link 
          to="/tarot/ritual" 
          class="group relative inline-flex items-center justify-center px-8 py-3 overflow-hidden font-medium transition duration-300 ease-out border-2 border-mystic-gold rounded-full shadow-md group border-opacity-50 hover:border-opacity-100 hover:shadow-mystic-gold/50"
      >
          <span class="absolute inset-0 w-full h-full bg-gradient-to-br from-mystic-purple to-black opacity-0 group-hover:opacity-100 transition duration-300 ease-out"></span>
          <span class="relative group-hover:text-white transition duration-300">Enter Sanctum</span>
      </router-link>
    </div>
  </div>
</template>

<script setup>
import StarField from '../../components/tarot/StarField.vue';
</script>

<style scoped>
.glow-text {
  text-shadow: 0 0 10px rgba(255, 215, 0, 0.5), 0 0 20px rgba(255, 215, 0, 0.3), 0 0 40px rgba(255, 215, 0, 0.2);
  animation: glow 3s ease-in-out infinite alternate;
}

@keyframes glow {
  from {
    text-shadow: 0 0 10px rgba(255, 215, 0, 0.5), 0 0 20px rgba(255, 215, 0, 0.3);
  }
  to {
    text-shadow: 0 0 20px rgba(255, 215, 0, 0.8), 0 0 40px rgba(255, 215, 0, 0.5), 0 0 60px rgba(168, 85, 247, 0.3);
  }
}
</style>
