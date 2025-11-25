<script setup>
import { ref } from 'vue'
import { cart } from '../store/cart'

// 控制哪个菜品正在编辑备注
const editingNoteId = ref(null)

const toggleNoteEdit = (recipeId) => {
  if (editingNoteId.value === recipeId) {
    editingNoteId.value = null
  } else {
    editingNoteId.value = recipeId
  }
}
</script>

<template>
  <div v-if="cart.isOpen" class="fixed inset-0 z-40">
    <!-- Backdrop -->
    <div class="absolute inset-0 bg-black/30 backdrop-blur-sm" @click="cart.isOpen = false"></div>
    
    <!-- 移动端：底部弹出面板 -->
    <div class="sm:hidden absolute inset-x-0 bottom-0 bg-white rounded-t-3xl shadow-2xl flex flex-col animate-slide-up max-h-[85vh]">
        <!-- 拖动条 -->
        <div class="flex justify-center pt-3 pb-2">
            <div class="w-12 h-1.5 bg-stone-200 rounded-full"></div>
        </div>
        
        <div class="px-4 pb-3 flex justify-between items-center border-b border-stone-100">
            <div>
              <h2 class="text-lg font-bold text-emerald-900">您的点单</h2>
              <p class="text-xs text-stone-400">{{ cart.items.length }} 道菜</p>
            </div>
            <button @click="cart.isOpen = false" class="w-8 h-8 flex items-center justify-center rounded-full bg-stone-100 text-stone-400 hover:bg-stone-200 hover:text-stone-600 transition-colors">✕</button>
        </div>
        
        <div class="flex-1 overflow-y-auto px-4 py-3 min-h-0">
            <div v-if="cart.items.length === 0" class="text-center text-stone-400 py-12">
                <span class="text-5xl block mb-3">🍽️</span>
                <p class="text-sm">还没点菜呢</p>
                <p class="text-xs text-stone-300 mt-1">去挑选您喜欢的美食吧</p>
            </div>
            <div v-else class="space-y-4">
                <div v-for="item in cart.items" :key="item.recipe.id" class="bg-stone-50 rounded-xl p-3 transition-all">
                    <div class="flex gap-3 items-start">
                        <img v-if="item.recipe.cover_image" :src="item.recipe.cover_image" class="w-16 h-16 object-cover rounded-lg flex-shrink-0 shadow-sm" />
                        <div v-else class="w-16 h-16 bg-stone-200 rounded-lg flex items-center justify-center flex-shrink-0 text-2xl">🍳</div>
                        
                        <div class="flex-1 min-w-0">
                            <h4 class="font-bold text-stone-800 text-sm truncate">{{ item.recipe.title }}</h4>
                            
                            <!-- 数量控制 -->
                            <div class="flex items-center gap-2 mt-2">
                                <button @click="item.quantity > 1 ? item.quantity-- : cart.removeItem(item.recipe.id)" class="w-7 h-7 bg-white rounded-full text-stone-500 flex items-center justify-center shadow-sm active:bg-stone-100 border border-stone-200">−</button>
                                <span class="text-sm font-bold w-6 text-center text-stone-700">{{ item.quantity }}</span>
                                <button @click="item.quantity++" class="w-7 h-7 bg-emerald-500 rounded-full text-white flex items-center justify-center shadow-sm active:bg-emerald-600">+</button>
                            </div>
                        </div>
                        
                        <button @click="cart.removeItem(item.recipe.id)" class="text-stone-300 hover:text-red-400 transition-colors p-1">
                          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/></svg>
                        </button>
                    </div>
                    
                    <!-- 备注区域 -->
                    <div class="mt-2.5 pt-2.5 border-t border-stone-200/50">
                      <button 
                        @click="toggleNoteEdit(item.recipe.id)"
                        class="text-xs flex items-center gap-1.5 text-stone-400 hover:text-stone-600 transition-colors w-full text-left"
                      >
                        <span v-if="!item.note" class="flex items-center gap-1">
                          <span class="text-[10px]">✎</span>
                          <span>添加备注</span>
                        </span>
                        <span v-else class="text-stone-500 italic truncate">「{{ item.note }}」</span>
                      </button>
                      
                      <!-- 备注输入框 -->
                      <Transition name="note-expand">
                        <div v-if="editingNoteId === item.recipe.id" class="mt-2">
                          <input 
                            v-model="item.note"
                            type="text"
                            placeholder="例如：少辣、不要香菜、多放葱..."
                            class="w-full text-xs border border-stone-200 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent bg-white"
                            maxlength="100"
                            @keyup.enter="editingNoteId = null"
                          />
                          <div class="flex justify-between items-center mt-1">
                            <span class="text-[10px] text-stone-300">{{ item.note?.length || 0 }}/100</span>
                            <button @click="editingNoteId = null" class="text-xs text-emerald-600 font-medium">完成</button>
                          </div>
                        </div>
                      </Transition>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- 底部固定区域 -->
        <div class="p-4 border-t border-stone-100 bg-white pb-safe">
            <div class="mb-3">
                <label class="block text-xs font-bold text-stone-600 mb-1.5">您的称呼</label>
                <input v-model="cart.customerName" type="text" placeholder="例如：张先生 / 2号桌" class="w-full border border-stone-200 rounded-xl p-3 text-stone-800 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent text-sm bg-stone-50" />
            </div>
            <button 
                @click="cart.submitOrder" 
                :disabled="cart.items.length === 0"
                class="w-full bg-gradient-to-r from-emerald-600 to-emerald-500 text-white py-3.5 rounded-xl font-bold hover:from-emerald-500 hover:to-emerald-400 disabled:from-stone-300 disabled:to-stone-300 disabled:cursor-not-allowed transition-all shadow-lg shadow-emerald-500/25 active:scale-[0.98] text-sm">
                🍽️ 提交点餐单
            </button>
        </div>
    </div>

    <!-- 桌面端：右侧滑入侧边栏 -->
    <div class="hidden sm:flex absolute inset-y-0 right-0 w-full max-w-md bg-white shadow-2xl flex-col animate-slide-in">
        <div class="p-5 border-b border-stone-100 flex justify-between items-center bg-gradient-to-r from-emerald-50 to-white">
            <div>
              <h2 class="text-xl font-bold text-emerald-900">您的点单</h2>
              <p class="text-xs text-stone-400 mt-0.5">{{ cart.items.length }} 道菜已选择</p>
            </div>
            <button @click="cart.isOpen = false" class="w-9 h-9 flex items-center justify-center rounded-full bg-white text-stone-400 hover:bg-stone-100 hover:text-stone-600 transition-colors shadow-sm border border-stone-100">✕</button>
        </div>
        
        <div class="flex-1 overflow-y-auto p-4">
            <div v-if="cart.items.length === 0" class="text-center text-stone-400 mt-16">
                <span class="text-6xl block mb-4">🍽️</span>
                <p class="text-lg">还没点菜呢</p>
                <p class="text-sm text-stone-300 mt-1">去挑选您喜欢的美食吧</p>
            </div>
            <div v-else class="space-y-4">
                <div v-for="item in cart.items" :key="item.recipe.id" class="bg-stone-50 rounded-2xl p-4 transition-all hover:shadow-md">
                    <div class="flex gap-4 items-start">
                        <img v-if="item.recipe.cover_image" :src="item.recipe.cover_image" class="w-20 h-20 object-cover rounded-xl flex-shrink-0 shadow-sm" />
                        <div v-else class="w-20 h-20 bg-stone-200 rounded-xl flex items-center justify-center flex-shrink-0 text-3xl">🍳</div>
                        
                        <div class="flex-1 min-w-0">
                            <h4 class="font-bold text-stone-800 truncate">{{ item.recipe.title }}</h4>
                            <p class="text-xs text-stone-400 mt-0.5">{{ item.recipe.category || '私房菜' }}</p>
                            
                            <!-- 数量控制 -->
                            <div class="flex items-center gap-3 mt-3">
                                <button @click="item.quantity > 1 ? item.quantity-- : cart.removeItem(item.recipe.id)" class="w-8 h-8 bg-white rounded-full text-stone-500 flex items-center justify-center shadow-sm hover:bg-stone-100 border border-stone-200 transition-colors">−</button>
                                <span class="font-bold w-8 text-center text-stone-700">{{ item.quantity }}</span>
                                <button @click="item.quantity++" class="w-8 h-8 bg-emerald-500 rounded-full text-white flex items-center justify-center shadow-sm hover:bg-emerald-600 transition-colors">+</button>
                            </div>
                        </div>
                        
                        <button @click="cart.removeItem(item.recipe.id)" class="text-stone-300 hover:text-red-400 transition-colors p-1">
                          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/></svg>
                        </button>
                    </div>
                    
                    <!-- 备注区域 -->
                    <div class="mt-3 pt-3 border-t border-stone-200/50">
                      <button 
                        @click="toggleNoteEdit(item.recipe.id)"
                        class="text-sm flex items-center gap-1.5 text-stone-400 hover:text-stone-600 transition-colors w-full text-left"
                      >
                        <span v-if="!item.note" class="flex items-center gap-1.5">
                          <span class="text-xs">✎</span>
                          <span>添加备注</span>
                        </span>
                        <span v-else class="text-stone-500 italic truncate">「{{ item.note }}」</span>
                      </button>
                      
                      <!-- 备注输入框 -->
                      <Transition name="note-expand">
                        <div v-if="editingNoteId === item.recipe.id" class="mt-3">
                          <div class="relative">
                            <input 
                              v-model="item.note"
                              type="text"
                              placeholder="例如：少辣、不要香菜、多放葱花..."
                              class="w-full text-sm border border-stone-200 rounded-xl px-4 py-2.5 pr-16 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent bg-white"
                              maxlength="100"
                              @keyup.enter="editingNoteId = null"
                            />
                            <button 
                              @click="editingNoteId = null" 
                              class="absolute right-2 top-1/2 -translate-y-1/2 text-xs bg-emerald-500 text-white px-3 py-1 rounded-full font-medium hover:bg-emerald-600 transition-colors"
                            >
                              完成
                            </button>
                          </div>
                          <p class="text-[11px] text-stone-300 mt-1.5 ml-1">{{ item.note?.length || 0 }}/100 字符</p>
                        </div>
                      </Transition>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="p-5 border-t border-stone-100 bg-gradient-to-t from-stone-50 to-white">
            <div class="mb-4">
                <label class="block text-sm font-bold text-stone-600 mb-2">您的称呼</label>
                <input v-model="cart.customerName" type="text" placeholder="例如：张先生 / 2号桌" class="w-full border border-stone-200 rounded-xl p-3 text-stone-800 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent bg-white" />
            </div>
            <button 
                @click="cart.submitOrder" 
                :disabled="cart.items.length === 0"
                class="w-full bg-gradient-to-r from-emerald-600 to-emerald-500 text-white py-4 rounded-xl font-bold hover:from-emerald-500 hover:to-emerald-400 disabled:from-stone-300 disabled:to-stone-300 disabled:cursor-not-allowed transition-all shadow-lg shadow-emerald-500/25 active:scale-[0.98]">
                🍽️ 提交点餐单
            </button>
        </div>
    </div>
  </div>
</template>

<style scoped>
/* 桌面端 - 从右侧滑入 */
.animate-slide-in {
    animation: slideIn 0.3s ease-out;
}
@keyframes slideIn {
    from { transform: translateX(100%); }
    to { transform: translateX(0); }
}

/* 移动端 - 从底部弹出 */
.animate-slide-up {
    animation: slideUp 0.3s ease-out;
}
@keyframes slideUp {
    from { transform: translateY(100%); }
    to { transform: translateY(0); }
}

/* 备注展开动画 */
.note-expand-enter-active,
.note-expand-leave-active {
  transition: all 0.2s ease;
}
.note-expand-enter-from,
.note-expand-leave-to {
  opacity: 0;
  transform: translateY(-10px);
}
</style>
