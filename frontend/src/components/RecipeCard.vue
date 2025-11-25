<script setup>
import { cart } from '../store/cart'

defineProps({
  recipe: Object
})
</script>

<template>
  <div class="bg-white rounded-xl shadow-sm overflow-hidden hover:shadow-xl hover:-translate-y-1 transition-all duration-300 cursor-pointer border border-stone-100 group relative flex flex-col h-full">
    <!-- Image Container -->
    <div class="h-40 sm:h-48 md:h-56 bg-stone-200 overflow-hidden relative">
      <img v-if="recipe.cover_image" :src="recipe.cover_image" :alt="recipe.title" class="w-full h-full object-cover group-hover:scale-110 transition-transform duration-700" />
      <div v-else class="w-full h-full flex items-center justify-center text-stone-400 bg-stone-100">
        <span class="text-4xl md:text-5xl opacity-50">🍳</span>
      </div>
      <!-- Category Badge -->
      <div class="absolute top-2 right-2 md:top-3 md:right-3 bg-white/90 backdrop-blur-sm px-2 md:px-3 py-0.5 md:py-1 rounded-full text-[10px] md:text-xs font-bold text-emerald-800 shadow-sm uppercase tracking-wider border border-emerald-100">
        {{ recipe.category || '家常菜' }}
      </div>
      <!-- Overlay for better text readability if needed, or hover effect -->
      <div class="absolute inset-0 bg-black/0 group-hover:bg-black/5 transition-colors duration-300"></div>
    </div>

    <!-- Content -->
    <div class="p-3 md:p-5 flex flex-col flex-1">
      <h3 class="text-base md:text-xl font-bold mb-1 md:mb-2 text-stone-800 font-display group-hover:text-emerald-800 transition-colors truncate">{{ recipe.title }}</h3>
      <p class="text-stone-600 text-xs md:text-sm mb-3 md:mb-6 line-clamp-2 flex-1 leading-relaxed">{{ recipe.description }}</p>
      
      <div class="flex items-center justify-between pt-3 md:pt-4 border-t border-stone-100 mt-auto gap-2">
        <span class="flex items-center gap-1 md:gap-1.5 text-stone-500 text-[10px] md:text-xs font-bold uppercase tracking-wide flex-shrink-0">
            <span class="text-sm md:text-base">⏱️</span> {{ recipe.cooking_time }}分钟
        </span>
        
        <button @click.stop.prevent="cart.addItem(recipe)" class="z-20 bg-emerald-50 text-emerald-700 px-2.5 md:pl-3 md:pr-4 py-1 md:py-1.5 rounded-full hover:bg-emerald-600 hover:text-white flex items-center gap-1 md:gap-2 transition-all duration-300 font-bold text-[10px] md:text-xs shadow-sm hover:shadow-md active:scale-95 group/btn border border-emerald-200 hover:border-emerald-600 cursor-pointer">
            <span class="text-sm md:text-lg leading-none group-hover/btn:rotate-90 transition-transform">+</span> 
            <span class="hidden xs:inline">点这道菜</span>
            <span class="xs:hidden">点菜</span>
        </button>
      </div>
    </div>

    <!-- Removed full card link to reader for guests -->
  </div>
</template>
