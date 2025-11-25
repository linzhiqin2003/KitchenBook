<script setup>
import { onMounted, ref, nextTick, onBeforeUnmount, watch, computed } from 'vue'
import { PageFlip } from 'page-flip'
import { cart } from '../store/cart'

const props = defineProps({
  recipes: {
    type: Array,
    required: true
  }
})

const bookEl = ref(null)
const isReady = ref(false)
const isMobile = ref(false)
let pageFlip = null

// 检测是否移动端
const checkMobile = () => {
    isMobile.value = window.innerWidth < 768
}

const initBook = async () => {
    if (!bookEl.value || props.recipes.length === 0) return

    isReady.value = false

    if (pageFlip) {
        pageFlip.destroy()
    }

    await nextTick()
    
    setTimeout(() => {
        if (!bookEl.value) return
        
        // 根据屏幕尺寸动态调整
        const screenWidth = window.innerWidth
        const screenHeight = window.innerHeight
        
        let bookWidth, bookHeight
        
        if (screenWidth < 480) {
            // 手机竖屏 - 更小的尺寸
            bookWidth = Math.min(screenWidth - 40, 280)
            bookHeight = Math.min(screenHeight - 200, 420)
        } else if (screenWidth < 768) {
            // 平板/大手机
            bookWidth = Math.min(screenWidth - 60, 350)
            bookHeight = Math.min(screenHeight - 200, 500)
        } else {
            // 桌面端
            bookWidth = 500
            bookHeight = 700
        }

        pageFlip = new PageFlip(bookEl.value, {
            width: bookWidth,
            height: bookHeight,
            size: "fixed",
            minWidth: 200,
            maxWidth: 800,
            minHeight: 300,
            maxHeight: 1200,
            maxShadowOpacity: isMobile.value ? 0.3 : 0.5,
            showCover: false,
            mobileScrollSupport: true,  // 启用移动端触摸支持
            useMouseEvents: true,
            flippingTime: isMobile.value ? 600 : 800,
            startPage: 0,
            usePortrait: isMobile.value,  // 移动端使用单页模式
            drawShadow: true,
            swipeDistance: 30  // 更短的滑动距离触发翻页
        })
        
        const pages = bookEl.value.querySelectorAll('.page')
        if (pages.length > 0) {
            pageFlip.loadFromHTML(pages)
        }

        setTimeout(() => {
            isReady.value = true
        }, 100)
    }, 200)
}


onMounted(() => {
    checkMobile()
    window.addEventListener('resize', handleResize)
    initBook()
})

let resizeTimeout = null
const handleResize = () => {
    checkMobile()
    // 防抖处理
    if (resizeTimeout) clearTimeout(resizeTimeout)
    resizeTimeout = setTimeout(() => {
        initBook()
    }, 300)
}

watch(() => props.recipes, () => {
    initBook()
}, { deep: true })

onBeforeUnmount(() => {
    if (pageFlip) {
        pageFlip.destroy()
    }
    window.removeEventListener('resize', handleResize)
    if (resizeTimeout) clearTimeout(resizeTimeout)
})
</script>

<template>
  <div class="book-stage min-h-[60vh] md:min-h-[90vh] flex items-center justify-center py-4 md:py-10 select-none relative overflow-visible px-2">
    <!-- Loading State -->
    <div v-if="!isReady" class="absolute inset-0 flex items-center justify-center text-emerald-800/50 animate-pulse">
        <span class="text-4xl">📖</span>
    </div>

    <!-- 移动端提示 -->
    <div v-if="isMobile && isReady" class="absolute top-0 left-1/2 -translate-x-1/2 text-xs text-stone-400 bg-white/80 px-3 py-1 rounded-full shadow-sm">
      👆 左右滑动翻页
    </div>

    <div ref="bookEl" class="shadow-xl md:shadow-2xl transition-opacity duration-500" :class="isReady ? 'opacity-100' : 'opacity-0'">
        <!-- Cover -->
        <div class="page" data-density="hard">
            <div class="page-content bg-paper-hard h-full p-4 md:p-8 border-r border-stone-900/20 flex flex-col items-center justify-center text-center relative overflow-hidden">
                <div class="paper-texture absolute inset-0 opacity-50 pointer-events-none"></div>
                
                <div class="border-2 md:border-4 border-double border-stone-800/20 p-4 md:p-12 relative z-10 bg-white/40 backdrop-blur-sm w-full h-full flex flex-col items-center justify-center">
                    <div class="text-4xl md:text-6xl mb-3 md:mb-6 animate-bounce-slow">👨‍🍳</div>
                    <h1 class="text-2xl md:text-5xl font-display font-bold text-emerald-900 mb-2 md:mb-6 drop-shadow-sm">今日菜单</h1>
                    <h2 class="text-base md:text-2xl font-serif italic text-stone-600 mb-4 md:mb-8">Today's Special</h2>
                    
                    <div class="w-16 md:w-24 h-1 md:h-1.5 bg-amber-400 mb-4 md:mb-10 rounded-full"></div>
                    
                    <p class="font-serif text-stone-700 text-sm md:text-lg max-w-xs leading-relaxed hidden md:block">
                        "精选当季食材，用心烹饪每一道佳肴。"
                    </p>
                    
                    <div class="mt-auto text-[10px] md:text-xs text-stone-400 tracking-widest uppercase">
                        KitchenBook
                    </div>
                </div>
            </div>
        </div>

        <!-- Recipe Pages -->
        <div v-for="(recipe, index) in recipes" :key="recipe.id" class="page" data-density="soft">
            <div class="page-content bg-paper-soft h-full p-3 md:p-6 border-r border-stone-300/20 flex flex-col relative overflow-hidden">
                <div class="paper-texture absolute inset-0 opacity-30 pointer-events-none"></div>

                <!-- Header/Number -->
                <div class="flex justify-between items-center mb-2 md:mb-4 text-stone-400 font-serif text-xs md:text-sm border-b border-stone-200 pb-1 md:pb-2">
                    <span class="truncate max-w-[60%]">{{ recipe.category || 'Main Course' }}</span>
                    <span>{{ index + 1 }}</span>
                </div>

                <!-- Image Area -->
                <div class="relative h-[40%] md:h-[45%] mb-2 md:mb-4 group cursor-pointer flex-shrink-0 w-full">
                    <div class="absolute inset-0 bg-stone-900/10 transform rotate-1 md:rotate-2 rounded transition-transform"></div>
                    <div class="relative h-full bg-white p-1 md:p-2 shadow-md transform -rotate-0.5 md:-rotate-1 transition-transform duration-500">
                        <img v-if="recipe.cover_image" :src="recipe.cover_image" class="w-full h-full object-cover filter contrast-[1.05]" />
                        <div v-else class="w-full h-full flex items-center justify-center bg-stone-100 text-2xl md:text-4xl text-stone-300">🍳</div>
                    </div>
                    
                    <!-- Cooking Time Badge -->
                    <div class="absolute -top-1 -right-1 md:-top-2 md:-right-2 bg-amber-100 text-amber-800 px-2 py-0.5 md:px-3 md:py-1 rounded-full text-[10px] md:text-xs font-bold shadow-sm border border-amber-200 z-20 flex items-center gap-0.5 md:gap-1">
                        <span>⏱️</span> {{ recipe.cooking_time }}m
                    </div>
                </div>

                <!-- Content Area -->
                <div class="flex-1 flex flex-col items-center text-center px-1 md:px-2 w-full overflow-hidden min-h-0">
                    <h3 class="text-base md:text-xl font-display font-bold text-stone-800 mb-1 md:mb-2 truncate w-full flex-shrink-0">{{ recipe.title }}</h3>
                    
                    <div class="w-8 md:w-12 h-px bg-stone-300 mb-2 md:mb-3 shrink-0"></div>
                    
                    <div class="flex-1 overflow-y-auto custom-scrollbar mb-2 md:mb-4 w-full">
                        <p class="text-stone-600 font-serif text-xs md:text-sm leading-relaxed px-1 md:px-2 line-clamp-4 md:line-clamp-none">
                            {{ recipe.description }}
                        </p>
                    </div>

                    <!-- Action -->
                    <button @click.stop="cart.addItem(recipe)" 
                        class="mt-auto mb-4 md:mb-8 group relative px-4 md:px-6 py-2 md:py-2.5 bg-emerald-800 text-amber-50 font-serif font-bold overflow-hidden rounded shadow-md hover:shadow-xl hover:-translate-y-0.5 transition-all duration-300 w-full max-w-[160px] md:max-w-[180px] shrink-0 text-sm md:text-base">
                        <div class="absolute inset-0 w-full h-full bg-gradient-to-r from-transparent via-white/20 to-transparent -translate-x-[150%] group-hover:translate-x-[150%] transition-transform duration-700 ease-in-out"></div>
                        <span class="flex items-center justify-center gap-1 md:gap-2 relative z-10">
                            <span>加入点单</span>
                            <span class="text-base md:text-lg group-hover:rotate-90 transition-transform duration-300">✛</span>
                        </span>
                    </button>
                </div>
                
                <!-- Footer decoration -->
                <div class="absolute bottom-2 md:bottom-3 left-1/2 transform -translate-x-1/2 opacity-20">
                    <span class="text-lg md:text-2xl">❦</span>
                </div>
            </div>
        </div>

        <!-- Back Cover -->
        <div class="page" data-density="hard">
             <div class="page-content bg-paper-hard h-full p-4 md:p-10 flex flex-col items-center justify-center border-4 md:border-8 border-amber-900/5 relative">
                <div class="paper-texture absolute inset-0 opacity-50 pointer-events-none"></div>
                
                <div class="text-center relative z-10">
                    <h3 class="text-xl md:text-3xl font-display font-bold text-stone-800 mb-2">Bon Appétit</h3>
                    <p class="text-stone-500 font-serif italic mb-4 md:mb-8 text-sm md:text-base">Enjoy your meal</p>
                    <div class="flex justify-center gap-2 md:gap-4 text-stone-300 text-lg md:text-2xl">
                        <span>★</span><span>★</span><span>★</span>
                    </div>
                </div>
                
                <div class="absolute bottom-4 md:bottom-8 text-[10px] md:text-xs text-stone-400">
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

