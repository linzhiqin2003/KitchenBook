<script setup>
import { onMounted, ref, nextTick, onBeforeUnmount } from 'vue'
import { PageFlip } from 'page-flip'

const props = defineProps({
  recipe: Object
})

const bookEl = ref(null)
let pageFlip = null

onMounted(async () => {
    await nextTick()
    setTimeout(() => {
        if (bookEl.value) {
            pageFlip = new PageFlip(bookEl.value, {
                width: 500,
                height: 650,
                size: "stretch",
                minWidth: 350,
                maxWidth: 1000,
                minHeight: 400,
                maxHeight: 1350,
                maxShadowOpacity: 0.5,
                showCover: true,
                mobileScrollSupport: false,
                useMouseEvents: true,
                flippingTime: 800 
            })
            
            const pages = bookEl.value.querySelectorAll('.page')
            if (pages.length > 0) {
                pageFlip.loadFromHTML(pages)
            }
        }
    }, 100)
})

onBeforeUnmount(() => {
    if (pageFlip) {
        pageFlip.destroy()
    }
})
</script>

<template>
  <div class="book-stage h-[85vh] flex items-center justify-center py-10">
    <div ref="bookEl" class="shadow-2xl bg-transparent">
        <!-- Cover -->
        <div class="page" data-density="hard">
            <div class="page-content bg-paper-hard h-full p-10 border-r border-stone-400/30 flex flex-col text-center border-8 border-amber-900/10 relative overflow-hidden">
                <!-- Texture Overlay -->
                <div class="paper-texture absolute inset-0 opacity-50 pointer-events-none"></div>
                
                <div class="relative z-10 flex flex-col h-full items-center justify-center border-double border-4 border-stone-800/20 p-8">
                    <span class="text-emerald-800 tracking-[0.3em] text-xs font-bold uppercase mb-8 border-b border-emerald-800/30 pb-2">The Kitchen Collection</span>
                    
                    <h1 class="text-5xl font-display font-bold text-stone-900 mb-8 leading-tight drop-shadow-sm">{{ recipe.title }}</h1>
                    
                    <div class="my-8 relative">
                        <div class="absolute inset-0 bg-stone-900/10 transform translate-x-2 translate-y-2 rounded rotate-2"></div>
                        <div class="relative bg-white p-2 rounded shadow-lg transform -rotate-2">
                             <img v-if="recipe.cover_image" :src="recipe.cover_image" class="max-h-60 w-auto object-cover filter sepia-[.15]" />
                             <div v-else class="h-48 w-32 flex items-center justify-center bg-stone-100 text-6xl">🍳</div>
                        </div>
                    </div>

                    <p class="text-stone-700 italic font-serif text-lg mb-8 max-w-xs leading-relaxed">"{{ recipe.description || '一道充满爱意的料理' }}"</p>
                    
                    <div class="mt-auto text-sm text-stone-500 font-serif flex items-center gap-2">
                        <span class="w-8 h-[1px] bg-stone-400"></span>
                        <span>Volume 1</span>
                        <span class="w-8 h-[1px] bg-stone-400"></span>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- Ingredients Page -->
        <div class="page" data-density="soft">
            <div class="page-content bg-paper-soft h-full p-10 border-r border-stone-300/20 relative">
                 <div class="paper-texture absolute inset-0 opacity-30 pointer-events-none"></div>
                 
                 <div class="relative z-10">
                    <h2 class="text-3xl font-display font-bold text-emerald-900 border-b-2 border-emerald-900/10 pb-4 mb-8 flex items-center gap-3">
                        <span class="text-2xl opacity-50">01.</span> 准备食材
                    </h2>
                    
                    <div class="space-y-5 font-serif">
                        <div v-for="(ing, idx) in recipe.ingredients" :key="ing.id" class="flex items-baseline justify-between group">
                            <div class="flex items-center gap-3">
                                <span class="w-4 h-4 rounded-full border border-stone-400 flex items-center justify-center text-[10px] text-stone-400 group-hover:bg-emerald-100 group-hover:text-emerald-600 transition-colors">{{ idx + 1 }}</span>
                                <span class="text-xl text-stone-800 border-b border-transparent group-hover:border-stone-300 transition-all">{{ ing.ingredient_name }}</span>
                            </div>
                            <span class="font-bold text-emerald-700 font-mono text-lg bg-emerald-50 px-2 py-0.5 rounded">{{ ing.quantity }}</span>
                        </div>
                    </div>
                    
                    <div class="mt-12 p-6 bg-amber-50/80 rounded-lg border border-amber-100/50 shadow-sm relative">
                        <span class="absolute -top-3 -left-2 text-3xl">📌</span>
                        <h4 class="font-bold text-amber-900/80 text-sm uppercase tracking-wide mb-2">Chef's Note</h4>
                        <p class="text-stone-700 italic text-sm leading-relaxed">确保所有食材新鲜，并在烹饪前清洗干净。好的准备是成功的一半。</p>
                    </div>
                </div>
                
                <span class="absolute bottom-6 left-1/2 transform -translate-x-1/2 text-stone-400 font-serif text-sm">- 2 -</span>
            </div>
        </div>

        <!-- Steps Pages -->
        <div class="page" v-for="(step, index) in recipe.steps" :key="step.id" data-density="soft">
            <div class="page-content bg-paper-soft h-full p-10 border-r border-stone-300/20 relative flex flex-col">
                <div class="paper-texture absolute inset-0 opacity-30 pointer-events-none"></div>
                
                <div class="relative z-10 flex-1">
                    <div class="flex justify-between items-end mb-8 border-b border-stone-200 pb-4">
                         <h2 class="text-xl font-display font-bold text-emerald-900">烹饪步骤</h2>
                         <span class="text-4xl font-display font-bold text-stone-200 leading-none -mb-1">{{ String(step.step_number).padStart(2, '0') }}</span>
                    </div>

                    <div v-if="step.image" class="mb-8 relative group cursor-pointer">
                         <div class="absolute inset-0 bg-stone-800/5 transform translate-x-2 translate-y-2 transition-transform group-hover:translate-x-3 group-hover:translate-y-3"></div>
                         <div class="relative bg-white p-1 border border-stone-200 shadow-sm">
                             <img :src="step.image" class="w-full h-56 object-cover filter contrast-[1.05]" />
                         </div>
                    </div>
                    
                    <div class="prose prose-stone">
                        <p class="text-xl leading-loose text-stone-800 font-serif first-letter:text-4xl first-letter:font-bold first-letter:text-emerald-800 first-letter:mr-1 first-letter:float-left">
                            {{ step.description }}
                        </p>
                    </div>
                </div>
                
                <span class="absolute bottom-6 left-1/2 transform -translate-x-1/2 text-stone-400 font-serif text-sm">- {{ index + 3 }} -</span>
            </div>
        </div>

        <!-- Back Cover -->
         <div class="page" data-density="hard">
            <div class="page-content bg-paper-hard h-full p-10 flex items-center justify-center border-8 border-amber-900/10 relative">
                <div class="paper-texture absolute inset-0 opacity-50 pointer-events-none"></div>
                
                <div class="text-center z-10 border-4 border-double border-stone-800/20 p-12 bg-white/30 backdrop-blur-sm">
                    <div class="text-emerald-700 text-6xl mb-6">👨‍🍳</div>
                    <h3 class="text-4xl font-display font-bold text-stone-800 mb-4">Bon Appétit</h3>
                    <p class="text-stone-600 text-xl italic font-serif mb-8">唯有爱与美食不可辜负</p>
                    <div class="w-16 h-1 bg-emerald-700 mx-auto mb-8"></div>
                    <p class="text-xs text-stone-400 uppercase tracking-widest">KitchenBook · 2024</p>
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
}
</style>
