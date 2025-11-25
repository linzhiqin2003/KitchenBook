<script setup>
import { onMounted, ref, nextTick, onBeforeUnmount, watch } from 'vue'
import { PageFlip } from 'page-flip'
import { cart } from '../store/cart'

const props = defineProps({
  recipes: {
    type: Array,
    required: true
  }
})

const bookEl = ref(null)
const isReady = ref(false) // New state to track if book is ready
let pageFlip = null

const initBook = async () => {
    if (!bookEl.value || props.recipes.length === 0) return

    isReady.value = false // Hide book during init

    // Destroy existing instance if any (re-initialization safety)
    if (pageFlip) {
        pageFlip.destroy()
    }

    await nextTick()
    
    // Small delay to ensure DOM is fully rendered
    setTimeout(() => {
        if (!bookEl.value) return
        
        // Force fixed size optimized for dual-page view
        const bookHeight = 700
        const bookWidth = 500

        pageFlip = new PageFlip(bookEl.value, {
            width: bookWidth,
            height: bookHeight,
            size: "fixed",
            minWidth: 300,
            maxWidth: 800,
            minHeight: 400,
            maxHeight: 1200,
            maxShadowOpacity: 0.5,
            showCover: false,
            mobileScrollSupport: false,
            useMouseEvents: true,
            flippingTime: 800,
            startPage: 0,
            usePortrait: false,  // Force dual-page (landscape) mode
            drawShadow: true
        })
        
        const pages = bookEl.value.querySelectorAll('.page')
        if (pages.length > 0) {
            pageFlip.loadFromHTML(pages)
        }

        // Show book after init
        setTimeout(() => {
            isReady.value = true
        }, 100)
    }, 200)
}


onMounted(() => {
    initBook()
})

// Re-init if recipes change (e.g. async load)
watch(() => props.recipes, () => {
    initBook()
}, { deep: true })

onBeforeUnmount(() => {
    if (pageFlip) {
        pageFlip.destroy()
    }
})
</script>

<template>
  <div class="book-stage min-h-[90vh] flex items-center justify-center py-10 select-none relative overflow-visible">
    <!-- Loading State -->
    <div v-if="!isReady" class="absolute inset-0 flex items-center justify-center text-emerald-800/50 animate-pulse">
        <span class="text-4xl">📖</span>
    </div>

    <div ref="bookEl" class="shadow-2xl transition-opacity duration-500" :class="isReady ? 'opacity-100' : 'opacity-0'">
        <!-- Cover -->
        <div class="page" data-density="hard">
            <div class="page-content bg-paper-hard h-full p-8 border-r border-stone-900/20 flex flex-col items-center justify-center text-center relative overflow-hidden">
                <div class="paper-texture absolute inset-0 opacity-50 pointer-events-none"></div>
                
                <div class="border-4 border-double border-stone-800/20 p-12 relative z-10 bg-white/40 backdrop-blur-sm w-full h-full flex flex-col items-center justify-center">
                    <div class="text-6xl mb-6 animate-bounce-slow">👨‍🍳</div>
                    <h1 class="text-5xl font-display font-bold text-emerald-900 mb-6 drop-shadow-sm">今日菜单</h1>
                    <h2 class="text-2xl font-serif italic text-stone-600 mb-8">Today's Special</h2>
                    
                    <div class="w-24 h-1.5 bg-amber-400 mb-10 rounded-full"></div>
                    
                    <p class="font-serif text-stone-700 text-lg max-w-xs leading-relaxed">
                        "精选当季食材，用心烹饪每一道佳肴。"
                    </p>
                    
                    <div class="mt-auto text-xs text-stone-400 tracking-widest uppercase">
                        KitchenBook Collection
                    </div>
                </div>
            </div>
        </div>

        <!-- Recipe Pages -->
        <div v-for="(recipe, index) in recipes" :key="recipe.id" class="page" data-density="soft">
            <div class="page-content bg-paper-soft h-full p-6 border-r border-stone-300/20 flex flex-col relative overflow-hidden">
                <div class="paper-texture absolute inset-0 opacity-30 pointer-events-none"></div>

                <!-- Header/Number -->
                <div class="flex justify-between items-center mb-4 text-stone-400 font-serif text-sm border-b border-stone-200 pb-2">
                    <span>{{ recipe.category || 'Main Course' }}</span>
                    <span>{{ index + 1 }}</span>
                </div>

                <!-- Image Area -->
                <div class="relative h-[45%] mb-4 group cursor-pointer flex-shrink-0 w-full">
                    <div class="absolute inset-0 bg-stone-900/10 transform rotate-2 rounded transition-transform group-hover:rotate-3"></div>
                    <div class="relative h-full bg-white p-2 shadow-md transform -rotate-1 transition-transform group-hover:-rotate-2 hover:scale-[1.02] duration-500">
                        <img v-if="recipe.cover_image" :src="recipe.cover_image" class="w-full h-full object-cover filter contrast-[1.05]" />
                        <div v-else class="w-full h-full flex items-center justify-center bg-stone-100 text-4xl text-stone-300">🍳</div>
                    </div>
                    
                    <!-- Cooking Time Badge -->
                    <div class="absolute -top-2 -right-2 bg-amber-100 text-amber-800 px-3 py-1 rounded-full text-xs font-bold shadow-sm border border-amber-200 z-20 flex items-center gap-1">
                        <span>⏱️</span> {{ recipe.cooking_time }} min
                    </div>
                </div>

                <!-- Content Area -->
                <div class="flex-1 flex flex-col items-center text-center px-2 w-full overflow-hidden min-h-0">
                    <h3 class="text-xl font-display font-bold text-stone-800 mb-2 truncate w-full flex-shrink-0">{{ recipe.title }}</h3>
                    
                    <div class="w-12 h-px bg-stone-300 mb-3 shrink-0"></div>
                    
                    <div class="flex-1 overflow-y-auto custom-scrollbar mb-4 w-full">
                        <p class="text-stone-600 font-serif text-sm leading-relaxed px-2">
                            {{ recipe.description }}
                        </p>
                    </div>

                    <!-- Action -->
                    <button @click.stop="cart.addItem(recipe)" 
                        class="mt-auto mb-8 group relative px-6 py-2.5 bg-emerald-800 text-amber-50 font-serif font-bold overflow-hidden rounded shadow-md hover:shadow-xl hover:-translate-y-0.5 transition-all duration-300 w-full max-w-[180px] shrink-0">
                        <div class="absolute inset-0 w-full h-full bg-gradient-to-r from-transparent via-white/20 to-transparent -translate-x-[150%] group-hover:translate-x-[150%] transition-transform duration-700 ease-in-out"></div>
                        <span class="flex items-center justify-center gap-2 relative z-10">
                            <span>Add to Cart</span>
                            <span class="text-lg group-hover:rotate-90 transition-transform duration-300">✛</span>
                        </span>
                    </button>
                </div>
                
                <!-- Footer decoration -->
                <div class="absolute bottom-3 left-1/2 transform -translate-x-1/2 opacity-20">
                    <span class="text-2xl">❦</span>
                </div>
            </div>
        </div>

        <!-- Back Cover -->
        <div class="page" data-density="hard">
             <div class="page-content bg-paper-hard h-full p-10 flex flex-col items-center justify-center border-8 border-amber-900/5 relative">
                <div class="paper-texture absolute inset-0 opacity-50 pointer-events-none"></div>
                
                <div class="text-center relative z-10">
                    <h3 class="text-3xl font-display font-bold text-stone-800 mb-2">Bon Appétit</h3>
                    <p class="text-stone-500 font-serif italic mb-8">Enjoy your meal</p>
                    <div class="flex justify-center gap-4 text-stone-300 text-2xl">
                        <span>★</span><span>★</span><span>★</span>
                    </div>
                </div>
                
                <div class="absolute bottom-8 text-xs text-stone-400">
                    &copy; KitchenBook
                </div>
             </div>
        </div>
    </div>
  </div>
</template>

<style scoped>
.bg-paper-hard {
    background-color: #fdfbf7;
    background-image: linear-gradient(to right, rgba(0,0,0,0.05), transparent 20%);
}

.bg-paper-soft {
    background-color: #fffefb;
    background-image: linear-gradient(to right, rgba(0,0,0,0.03), transparent 10%);
}

.paper-texture {
    background-image: url("data:image/svg+xml,%3Csvg width='100' height='100' viewBox='0 0 100 100' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noise'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.8' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100' height='100' filter='url(%23noise)' opacity='0.08'/%3E%3C/svg%3E");
}

.page-content {
    box-shadow: inset 0 0 30px rgba(0,0,0,0.02);
}

.book-stage {
    perspective: 2000px;
    /* Ensure enough space for book shadow/transforms */
    overflow: hidden; 
}

.animate-bounce-slow {
    animation: bounce 2s infinite;
}

@keyframes bounce {
  0%, 100% {
    transform: translateY(-5%);
    animation-timing-function: cubic-bezier(0.8, 0, 1, 1);
  }
  50% {
    transform: translateY(0);
    animation-timing-function: cubic-bezier(0, 0, 0.2, 1);
  }
}
</style>

