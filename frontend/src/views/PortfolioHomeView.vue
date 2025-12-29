<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()

// 当前时间
const currentTime = ref('')
const currentDate = ref('')

const updateTime = () => {
  const now = new Date()
  currentTime.value = now.toLocaleTimeString('zh-CN', { 
    hour: '2-digit', 
    minute: '2-digit',
    hour12: false 
  })
  currentDate.value = now.toLocaleDateString('zh-CN', { 
    weekday: 'long',
    month: 'long', 
    day: 'numeric' 
  })
}

let timer = null
onMounted(() => {
  updateTime()
  timer = setInterval(updateTime, 1000)
})

onUnmounted(() => {
  if (timer) clearInterval(timer)
})

// 导航区块配置
const navBlocks = [
  {
    id: 'kitchen',
    title: '私人厨房',
    subtitle: 'Kitchen Book',
    description: '私人菜谱收藏，记录美食制作方法',
    icon: '🍳',
    path: '/kitchen',
    gradient: 'from-orange-400 via-amber-500 to-yellow-500',
    shadowColor: 'shadow-amber-500/30',
    features: ['拟物翻书效果', '菜谱管理', '订单系统']
  },
  {
    id: 'questiongen',
    title: '智能刷题',
    subtitle: 'Question Gen',
    description: 'AI驱动的智能学习工具',
    icon: '📚',
    path: '/questiongen',
    gradient: 'from-cyan-500 via-blue-500 to-indigo-500',
    shadowColor: 'shadow-blue-500/30',
    features: ['AI出题', '知识巩固', '自适应学习']
  },
  {
    id: 'tarot',
    title: '塔罗秘仪',
    subtitle: 'Tarot Sanctum',
    description: '沉浸式占卜与神秘解读体验',
    icon: '🃏',
    path: '/tarot',
    gradient: 'from-indigo-500 via-slate-700 to-slate-900',
    shadowColor: 'shadow-indigo-500/30',
    features: ['互动牌阵', 'AI解读', '仪式体验']
  },
  {
    id: 'ai-lab',
    title: 'AI 实验室',
    subtitle: 'AI Lab',
    description: 'DeepSeek Reasoner 思考模型对话',
    icon: '🧠',
    path: '/ai-lab',
    gradient: 'from-emerald-400 via-teal-500 to-cyan-500',
    shadowColor: 'shadow-teal-500/30',
    features: ['思维链推理', '语音输入', '图片OCR']
  }
]

const navigateTo = (path) => {
  router.push(path)
}

// 社交链接
const socialLinks = [
  { name: 'GitHub', icon: 'github', url: 'https://github.com/linzhiqin2003' }
]
</script>

<template>
  <div class="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 text-white overflow-hidden">
    <!-- 动态背景 -->
    <div class="fixed inset-0 pointer-events-none overflow-hidden">
      <!-- 主渐变光球 - 缓慢移动 -->
      <div class="orb orb-1"></div>
      <div class="orb orb-2"></div>
      <div class="orb orb-3"></div>
      <div class="orb orb-4"></div>
      
      <!-- 小光点粒子 -->
      <div class="particle particle-1"></div>
      <div class="particle particle-2"></div>
      <div class="particle particle-3"></div>
      <div class="particle particle-4"></div>
      <div class="particle particle-5"></div>
      <div class="particle particle-6"></div>
      
      <!-- 细微网格纹理 -->
      <div class="absolute inset-0 bg-[linear-gradient(rgba(255,255,255,0.015)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,0.015)_1px,transparent_1px)] bg-[size:60px_60px]"></div>
      
      <!-- 顶部和底部渐变遮罩 -->
      <div class="absolute inset-x-0 top-0 h-40 bg-gradient-to-b from-slate-900/50 to-transparent"></div>
      <div class="absolute inset-x-0 bottom-0 h-40 bg-gradient-to-t from-slate-900/50 to-transparent"></div>
    </div>
    
    <div class="relative min-h-screen flex flex-col">
      <!-- 顶部状态栏 (iOS风格) -->
      <header class="pt-safe px-6 py-4 flex items-center justify-between">
        <div class="text-sm text-white/60 font-medium">
          {{ currentDate }}
        </div>
        <div class="flex items-center gap-3">
          <!-- 技术博客入口 -->
          <router-link 
            to="/blog"
            class="w-8 h-8 rounded-full bg-gradient-to-br from-violet-500/20 to-purple-500/20 backdrop-blur-sm flex items-center justify-center hover:from-violet-500/40 hover:to-purple-500/40 transition-all duration-300 group border border-white/10 hover:border-violet-400/50"
            title="技术博客"
          >
            <svg class="w-4 h-4 text-white/80 group-hover:text-violet-300 transition-colors" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"/>
            </svg>
          </router-link>
          
          <!-- GitHub -->
          <a 
            href="https://github.com/linzhiqin2003" 
            target="_blank"
            class="w-8 h-8 rounded-full bg-white/10 backdrop-blur-sm flex items-center justify-center hover:bg-white/20 transition-colors border border-white/10 hover:border-white/30"
            title="GitHub"
          >
            <svg class="w-4 h-4 text-white/80" fill="currentColor" viewBox="0 0 24 24">
              <path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"/>
            </svg>
          </a>
        </div>
      </header>
      
      <!-- 主内容区域 -->
      <main class="flex-1 px-4 sm:px-6 lg:px-8 pb-8">
        <div class="max-w-6xl mx-auto">
          <!-- 个人简介区域 -->
          <div class="text-center py-12 sm:py-16 lg:py-20">
            <!-- 头像 -->
            <div class="relative inline-block mb-6">
              <div class="w-28 h-28 sm:w-32 sm:h-32 rounded-[2rem] bg-gradient-to-br from-violet-500 via-purple-500 to-fuchsia-500 p-1 shadow-2xl shadow-purple-500/30">
                <div class="w-full h-full rounded-[1.75rem] bg-slate-800 flex items-center justify-center">
                  <span class="text-5xl sm:text-6xl">👨‍💻</span>
                </div>
              </div>
              <!-- 在线状态指示器 -->
              <div class="absolute bottom-1 right-1 w-5 h-5 rounded-full bg-emerald-500 border-4 border-slate-900"></div>
            </div>
            
            <!-- 时间显示 (iOS锁屏风格) -->
            <div class="mb-6">
              <div class="text-6xl sm:text-7xl lg:text-8xl font-extralight tracking-tight text-white/90 mb-2">
                {{ currentTime }}
              </div>
            </div>
            
            <!-- 名称和标语 -->
            <h1 class="text-3xl sm:text-4xl lg:text-5xl font-bold mb-4 bg-clip-text text-transparent bg-gradient-to-r from-white via-white to-white/80">
              LZQ 的个人空间
            </h1>
            <p class="text-lg sm:text-xl text-white/50 max-w-md mx-auto leading-relaxed">
              探索代码世界，记录生活点滴
            </p>
          </div>
          
          <!-- 导航卡片网格 -->
          <div class="grid grid-cols-1 sm:grid-cols-2 gap-4 sm:gap-6 max-w-4xl mx-auto">
            <button
              v-for="block in navBlocks"
              :key="block.id"
              @click="navigateTo(block.path)"
              class="group relative overflow-hidden rounded-3xl bg-white/5 backdrop-blur-xl border border-white/10 p-6 sm:p-8 text-left transition-all duration-500 hover:scale-[1.02] hover:bg-white/10 hover:border-white/20 focus:outline-none focus:ring-2 focus:ring-white/20"
            >
              <!-- 悬停渐变背景 -->
              <div 
                class="absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity duration-500 bg-gradient-to-br"
                :class="block.gradient"
                style="opacity: 0.08;"
              ></div>
              
              <!-- 装饰性光效 -->
              <div class="absolute top-0 right-0 w-32 h-32 bg-gradient-to-br from-white/5 to-transparent rounded-bl-full opacity-0 group-hover:opacity-100 transition-opacity duration-500"></div>
              
              <div class="relative z-10">
                <!-- 图标 -->
                <div 
                  class="w-14 h-14 sm:w-16 sm:h-16 rounded-2xl bg-gradient-to-br flex items-center justify-center text-3xl sm:text-4xl mb-4 shadow-lg transition-transform duration-500 group-hover:scale-110 group-hover:rotate-3"
                  :class="[block.gradient, block.shadowColor]"
                >
                  {{ block.icon }}
                </div>
                
                <!-- 标题 -->
                <div class="mb-3">
                  <h2 class="text-xl sm:text-2xl font-bold text-white mb-1 group-hover:text-white transition-colors">
                    {{ block.title }}
                  </h2>
                  <p class="text-xs sm:text-sm font-medium text-white/40 uppercase tracking-wider">
                    {{ block.subtitle }}
                  </p>
                </div>
                
                <!-- 描述 -->
                <p class="text-sm text-white/60 mb-4 line-clamp-2">
                  {{ block.description }}
                </p>
                
                <!-- 特性标签 -->
                <div class="flex flex-wrap gap-2">
                  <span 
                    v-for="feature in block.features" 
                    :key="feature"
                    class="px-2.5 py-1 text-xs font-medium rounded-full bg-white/10 text-white/70 border border-white/5"
                  >
                    {{ feature }}
                  </span>
                </div>
                
                <!-- 箭头指示器 -->
                <div class="absolute bottom-6 right-6 sm:bottom-8 sm:right-8 w-10 h-10 rounded-full bg-white/10 flex items-center justify-center opacity-0 group-hover:opacity-100 translate-x-4 group-hover:translate-x-0 transition-all duration-500">
                  <svg class="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"/>
                  </svg>
                </div>
              </div>
            </button>
          </div>
        </div>
      </main>
      
      <!-- 底部 -->
      <footer class="px-6 py-6 text-center">
        <div class="flex items-center justify-center gap-2 text-sm text-white/30">
          <span>Built with</span>
          <span class="text-red-400">❤️</span>
          <span>by LZQ</span>
          <span class="mx-2">·</span>
          <span>© 2025</span>
        </div>
      </footer>
    </div>
  </div>
</template>

<style scoped>
/* ========== 动态背景光球 ========== */
.orb {
  position: absolute;
  border-radius: 50%;
  filter: blur(80px);
  opacity: 0.4;
  will-change: transform;
}

.orb-1 {
  width: 600px;
  height: 600px;
  background: linear-gradient(135deg, #a855f7 0%, #7c3aed 50%, #4f46e5 100%);
  top: -15%;
  left: -10%;
  animation: float-1 20s ease-in-out infinite;
}

.orb-2 {
  width: 500px;
  height: 500px;
  background: linear-gradient(135deg, #06b6d4 0%, #0ea5e9 50%, #3b82f6 100%);
  bottom: -15%;
  right: -10%;
  animation: float-2 25s ease-in-out infinite;
}

.orb-3 {
  width: 400px;
  height: 400px;
  background: linear-gradient(135deg, #f59e0b 0%, #f97316 50%, #ef4444 100%);
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  animation: float-3 18s ease-in-out infinite;
  opacity: 0.25;
}

.orb-4 {
  width: 350px;
  height: 350px;
  background: linear-gradient(135deg, #10b981 0%, #14b8a6 50%, #06b6d4 100%);
  top: 20%;
  right: 20%;
  animation: float-4 22s ease-in-out infinite;
  opacity: 0.3;
}

/* 光球浮动动画 */
@keyframes float-1 {
  0%, 100% {
    transform: translate(0, 0) scale(1);
  }
  25% {
    transform: translate(50px, 30px) scale(1.05);
  }
  50% {
    transform: translate(20px, 60px) scale(0.95);
  }
  75% {
    transform: translate(-30px, 20px) scale(1.02);
  }
}

@keyframes float-2 {
  0%, 100% {
    transform: translate(0, 0) scale(1);
  }
  25% {
    transform: translate(-40px, -30px) scale(1.03);
  }
  50% {
    transform: translate(-70px, 20px) scale(0.97);
  }
  75% {
    transform: translate(20px, -40px) scale(1.05);
  }
}

@keyframes float-3 {
  0%, 100% {
    transform: translate(-50%, -50%) scale(1) rotate(0deg);
  }
  33% {
    transform: translate(-45%, -55%) scale(1.1) rotate(5deg);
  }
  66% {
    transform: translate(-55%, -45%) scale(0.9) rotate(-5deg);
  }
}

@keyframes float-4 {
  0%, 100% {
    transform: translate(0, 0) scale(1);
  }
  50% {
    transform: translate(-60px, 40px) scale(1.08);
  }
}

/* ========== 小光点粒子 ========== */
.particle {
  position: absolute;
  border-radius: 50%;
  background: white;
  opacity: 0.4;
  will-change: transform, opacity;
}

.particle-1 {
  width: 4px;
  height: 4px;
  top: 20%;
  left: 30%;
  animation: twinkle 3s ease-in-out infinite, drift-1 15s ease-in-out infinite;
}

.particle-2 {
  width: 3px;
  height: 3px;
  top: 60%;
  left: 15%;
  animation: twinkle 4s ease-in-out infinite 0.5s, drift-2 18s ease-in-out infinite;
}

.particle-3 {
  width: 5px;
  height: 5px;
  top: 35%;
  right: 25%;
  animation: twinkle 3.5s ease-in-out infinite 1s, drift-3 20s ease-in-out infinite;
}

.particle-4 {
  width: 3px;
  height: 3px;
  top: 75%;
  right: 35%;
  animation: twinkle 4.5s ease-in-out infinite 1.5s, drift-1 16s ease-in-out infinite reverse;
}

.particle-5 {
  width: 4px;
  height: 4px;
  top: 45%;
  left: 70%;
  animation: twinkle 3s ease-in-out infinite 2s, drift-2 22s ease-in-out infinite;
}

.particle-6 {
  width: 2px;
  height: 2px;
  top: 85%;
  left: 50%;
  animation: twinkle 5s ease-in-out infinite 0.8s, drift-3 17s ease-in-out infinite;
}

/* 闪烁动画 */
@keyframes twinkle {
  0%, 100% {
    opacity: 0.2;
    transform: scale(1);
  }
  50% {
    opacity: 0.8;
    transform: scale(1.2);
  }
}

/* 漂移动画 */
@keyframes drift-1 {
  0%, 100% {
    transform: translate(0, 0);
  }
  25% {
    transform: translate(30px, -20px);
  }
  50% {
    transform: translate(60px, 10px);
  }
  75% {
    transform: translate(20px, 30px);
  }
}

@keyframes drift-2 {
  0%, 100% {
    transform: translate(0, 0);
  }
  33% {
    transform: translate(-40px, 25px);
  }
  66% {
    transform: translate(20px, -35px);
  }
}

@keyframes drift-3 {
  0%, 100% {
    transform: translate(0, 0);
  }
  50% {
    transform: translate(-50px, -30px);
  }
}

/* ========== 其他样式 ========== */
/* iOS 安全区域 */
.pt-safe {
  padding-top: max(1rem, env(safe-area-inset-top));
}

/* 文本截断 */
.line-clamp-2 {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

/* 减少动画对性能的影响 */
@media (prefers-reduced-motion: reduce) {
  .orb, .particle {
    animation: none !important;
  }
}
</style>
