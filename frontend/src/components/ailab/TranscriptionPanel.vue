<script setup>
import { computed, nextTick, watch, ref } from 'vue'

const props = defineProps({
  currentTranscription: String,
  history: Array,
  totalChars: Number,
  isTranslating: Boolean,  // Show "translating..." when waiting for translation
})

const emit = defineEmits(['clear', 'copy', 'download'])

const containerRef = ref(null)
const showClearConfirm = ref(false)

// Auto-scroll to bottom
watch(() => props.history.length, () => {
  nextTick(() => {
    if (containerRef.value) {
      containerRef.value.scrollTop = containerRef.value.scrollHeight
    }
  })
})

function handleClearClick() {
  showClearConfirm.value = true
}

function confirmClear() {
  showClearConfirm.value = false
  emit('clear')
}

function cancelClear() {
  showClearConfirm.value = false
}
</script>

<template>
  <div class="ios-glass h-full rounded-[32px] p-8 flex flex-col border border-white/5 relative overflow-hidden shadow-2xl ring-1 ring-white/10">
    <!-- Header -->
    <div class="flex justify-between items-center pb-6 z-10 border-b border-white/5">
      <div class="flex items-center gap-3">
         <h2 class="text-[20px] font-semibold text-white tracking-tight">Transcript</h2>
         <span v-if="history.length > 0" class="px-2 py-0.5 rounded-full bg-white/10 text-[11px] font-medium text-white/50">{{ history.length }}</span>
      </div>
      
      <!-- iOS Action Menu (Refined) -->
      <div class="flex gap-2">
        <button
          @click="emit('copy')"
          class="w-9 h-9 rounded-full bg-white/5 flex items-center justify-center text-white/60 hover:bg-white/10 hover:text-white transition-all duration-200"
          title="复制"
        >
          <svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
            <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
          </svg>
        </button>
        <button
          @click="emit('download')"
          class="w-9 h-9 rounded-full bg-white/5 flex items-center justify-center text-white/60 hover:bg-white/10 hover:text-white transition-all duration-200"
          title="下载"
        >
          <svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path><polyline points="7 10 12 15 17 10"></polyline><line x1="12" y1="15" x2="12" y2="3"></line></svg>
        </button>
        <button
          @click="handleClearClick"
          class="w-9 h-9 rounded-full bg-white/5 flex items-center justify-center text-white/60 hover:bg-red-500/20 hover:text-red-400 transition-all duration-200"
          title="清空"
        >
          <svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M3 6h18"></path>
            <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
          </svg>
        </button>
      </div>
    </div>
    
    <!-- Content List -->
    <div ref="containerRef" class="flex-1 overflow-y-auto custom-scrollbar space-y-4 py-6 scroll-smooth">
      <div v-if="history.length === 0 && !currentTranscription" class="h-full flex flex-col items-center justify-center text-ios-gray/30">
        <div class="w-20 h-20 rounded-[20px] bg-white/5 flex items-center justify-center mb-6">
           <svg class="w-10 h-10 opacity-50" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
             <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"></path>
             <path d="M19 10v2a7 7 0 0 1-14 0v-2"></path>
             <line x1="12" y1="19" x2="12" y2="23"></line>
             <line x1="8" y1="23" x2="16" y2="23"></line>
           </svg>
        </div>
        <p class="text-[17px] font-medium tracking-wide">Ready to translate</p>
      </div>

      <!-- History Items -->
      <div 
        v-for="item in history" 
        :key="item.id"
        class="group relative bg-white/5 hover:bg-white/10 p-5 rounded-[20px] transition-all duration-300 border border-transparent hover:border-white/5"
      >
        <div class="space-y-3">
          <!-- Text Content -->
          <div class="space-y-1.5">
             <!-- Original -->
             <div class="flex items-start gap-3">
                <span class="mt-1.5 w-1.5 h-1.5 rounded-full bg-white/20 shrink-0"></span>
                <p class="text-[15px] text-ios-gray leading-relaxed font-light">{{ item.original }}</p>
             </div>
             
             <!-- Translated (only show if translation exists) -->
             <div v-if="item.translated" class="flex items-start gap-3">
                <span class="mt-1.5 w-1.5 h-1.5 rounded-full bg-blue-500 shrink-0 shadow-[0_0_8px_rgba(59,130,246,0.5)]"></span>
                <p class="text-[17px] text-white font-normal leading-relaxed tracking-wide">{{ item.translated }}</p>
             </div>
          </div>
          
          <!-- Metadata -->
          <div class="flex items-center justify-end pt-1 opacity-0 group-hover:opacity-100 transition-opacity duration-300">
            <span class="text-[11px] text-ios-gray/40 font-medium">{{ item.timestamp }}</span>
          </div>
        </div>
      </div>

      <!-- Current Processing Item -->
      <div 
        v-if="currentTranscription"
        class="relative bg-gradient-to-r from-blue-500/5 to-purple-500/5 p-5 rounded-[20px] overflow-hidden transition-all duration-500"
        :class="isTranslating ? 'from-blue-500/10 to-purple-500/10' : ''"
      >
        <!-- Animated gradient border -->
        <div class="absolute inset-0 rounded-[20px] border border-blue-500/30"></div>
        
        <!-- Typing indicator bar -->
        <div 
          class="absolute bottom-0 left-0 h-[2px] bg-gradient-to-r from-blue-500 via-purple-500 to-blue-500" 
          :class="isTranslating ? 'animate-shimmer bg-size-200' : ''"
          style="width: 100%; background-size: 200% 100%;"
        ></div>
        
        <div class="space-y-2">
          <!-- Original text -->
          <div class="flex items-start gap-3">
            <!-- Subtle breathing dot -->
            <span 
              class="mt-2 w-2 h-2 rounded-full shrink-0" 
              :class="isTranslating ? 'bg-purple-400' : 'bg-blue-400'"
              style="animation: breathing 2s ease-in-out infinite;"
            ></span>
            <p class="text-[17px] text-white/90 leading-relaxed">{{ currentTranscription }}</p>
          </div>
          
          <!-- Translating indicator -->
          <div v-if="isTranslating" class="flex items-center gap-2 pl-5">
            <div class="flex gap-1">
              <span class="w-1.5 h-1.5 bg-purple-400 rounded-full animate-bounce" style="animation-delay: 0ms;"></span>
              <span class="w-1.5 h-1.5 bg-purple-400 rounded-full animate-bounce" style="animation-delay: 150ms;"></span>
              <span class="w-1.5 h-1.5 bg-purple-400 rounded-full animate-bounce" style="animation-delay: 300ms;"></span>
            </div>
            <span class="text-[13px] text-purple-400/70 font-medium">翻译中...</span>
          </div>
        </div>
      </div>
    </div>
    
    <!-- Custom Clear Confirmation Modal -->
    <Transition name="fade">
      <div v-if="showClearConfirm" class="absolute inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm rounded-[32px]">
        <div class="bg-[#1c1c1e] rounded-2xl p-6 shadow-2xl border border-white/10 max-w-[280px] mx-4">
          <div class="text-center mb-5">
            <div class="w-12 h-12 rounded-full bg-red-500/20 flex items-center justify-center mx-auto mb-3">
              <svg class="w-6 h-6 text-red-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M3 6h18"></path>
                <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
              </svg>
            </div>
            <h3 class="text-white font-semibold text-[17px] mb-1">清空记录</h3>
            <p class="text-white/50 text-[14px]">确定要清空所有翻译记录吗？此操作无法撤销。</p>
          </div>
          <div class="flex gap-3">
            <button
              @click="cancelClear"
              class="flex-1 py-2.5 px-4 rounded-xl bg-white/10 text-white font-medium text-[15px] hover:bg-white/20 transition-colors"
            >
              取消
            </button>
            <button
              @click="confirmClear"
              class="flex-1 py-2.5 px-4 rounded-xl bg-red-500 text-white font-medium text-[15px] hover:bg-red-600 transition-colors"
            >
              清空
            </button>
          </div>
        </div>
      </div>
    </Transition>
  </div>
</template>

<style scoped>
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
