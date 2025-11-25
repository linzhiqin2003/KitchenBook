<script setup>
import { cart } from '../store/cart'

defineProps({
  recipe: Object
})
</script>

<template>
  <div class="bg-white rounded-xl shadow-sm overflow-hidden hover:shadow-xl hover:-translate-y-1 transition-all duration-300 cursor-pointer border border-stone-100 group relative flex flex-col h-full">
    <!-- Image Container -->
    <div class="h-56 bg-stone-200 overflow-hidden relative">
      <img v-if="recipe.cover_image" :src="recipe.cover_image" :alt="recipe.title" class="w-full h-full object-cover group-hover:scale-110 transition-transform duration-700" />
      <div v-else class="w-full h-full flex items-center justify-center text-stone-400 bg-stone-100">
        <span class="text-5xl opacity-50">🍳</span>
      </div>
      <!-- Category Badge -->
      <div class="absolute top-3 right-3 bg-white/90 backdrop-blur-sm px-3 py-1 rounded-full text-xs font-bold text-emerald-800 shadow-sm uppercase tracking-wider border border-emerald-100">
        {{ recipe.category || '家常菜' }}
      </div>
      <!-- Overlay for better text readability if needed, or hover effect -->
      <div class="absolute inset-0 bg-black/0 group-hover:bg-black/5 transition-colors duration-300"></div>
    </div>

    <!-- Content -->
    <div class="p-5 flex flex-col flex-1">
      <h3 class="text-xl font-bold mb-2 text-stone-800 font-display group-hover:text-emerald-800 transition-colors">{{ recipe.title }}</h3>
      <p class="text-stone-600 text-sm mb-6 line-clamp-2 flex-1 leading-relaxed">{{ recipe.description }}</p>
      
      <div class="flex items-center justify-between pt-4 border-t border-stone-100 mt-auto">
        <span class="flex items-center gap-1.5 text-stone-500 text-xs font-bold uppercase tracking-wide">
            <span class="text-base">⏱️</span> {{ recipe.cooking_time }} 分钟
        </span>
        
        <button @click.stop.prevent="cart.addItem(recipe)" class="z-20 bg-emerald-50 text-emerald-700 pl-3 pr-4 py-1.5 rounded-full hover:bg-emerald-600 hover:text-white flex items-center gap-2 transition-all duration-300 font-bold text-xs shadow-sm hover:shadow-md active:scale-95 group/btn border border-emerald-200 hover:border-emerald-600 cursor-pointer">
            <span class="text-lg leading-none mb-0.5 group-hover/btn:rotate-90 transition-transform">+</span> 点这道菜
        </button>
      </div>
    </div>

    <!-- Removed full card link to reader for guests -->
  </div>
</template>
