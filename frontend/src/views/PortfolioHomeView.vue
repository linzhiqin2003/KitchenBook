<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()

const currentTime = ref('')
const currentDate = ref('')

const updateTime = () => {
  const now = new Date()
  currentTime.value = now.toLocaleTimeString('zh-CN', {
    hour: '2-digit',
    minute: '2-digit',
    hour12: false,
  })
  currentDate.value = now.toLocaleDateString('zh-CN', {
    weekday: 'long',
    month: 'long',
    day: 'numeric',
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

const navigateTo = (path) => {
  router.push(path)
}
</script>

<template>
  <div class="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 text-white overflow-hidden">
    <!-- Dynamic background -->
    <div class="fixed inset-0 pointer-events-none overflow-hidden">
      <div class="orb orb-1"></div>
      <div class="orb orb-2"></div>
      <div class="orb orb-3"></div>
      <div class="orb orb-4"></div>
      <div class="particle particle-1"></div>
      <div class="particle particle-2"></div>
      <div class="particle particle-3"></div>
      <div class="particle particle-4"></div>
      <div class="particle particle-5"></div>
      <div class="particle particle-6"></div>
      <div class="absolute inset-0 bg-[linear-gradient(rgba(255,255,255,0.015)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,0.015)_1px,transparent_1px)] bg-[size:60px_60px]"></div>
      <div class="absolute inset-x-0 top-0 h-40 bg-gradient-to-b from-slate-900/50 to-transparent"></div>
      <div class="absolute inset-x-0 bottom-0 h-40 bg-gradient-to-t from-slate-900/50 to-transparent"></div>
    </div>

    <div class="relative min-h-screen flex flex-col">
      <!-- Top bar -->
      <header class="pt-safe px-5 sm:px-8 py-4 flex items-center justify-between">
        <div class="text-sm text-white/45 font-medium flex items-center gap-2.5">
          <span>{{ currentDate }}</span>
          <span class="text-white/20">|</span>
          <span class="tabular-nums text-white/35">{{ currentTime }}</span>
        </div>
        <div class="flex items-center gap-3">
          <router-link
            to="/blog"
            class="w-8 h-8 rounded-full bg-gradient-to-br from-violet-500/20 to-purple-500/20 backdrop-blur-sm flex items-center justify-center hover:from-violet-500/40 hover:to-purple-500/40 transition-all duration-300 group border border-white/10 hover:border-violet-400/50"
            title="技术博客"
          >
            <svg class="w-4 h-4 text-white/80 group-hover:text-violet-300 transition-colors" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"/>
            </svg>
          </router-link>
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

      <!-- Main content -->
      <main class="flex-1 px-4 sm:px-6 lg:px-8 pb-8">
        <div class="max-w-5xl mx-auto">

          <!-- Compact Hero -->
          <section class="hero-section text-center py-8 sm:py-10">
            <div class="relative inline-block mb-4">
              <div class="w-[72px] h-[72px] sm:w-20 sm:h-20 rounded-[1.25rem] bg-gradient-to-br from-violet-500 via-purple-500 to-fuchsia-500 p-[2.5px] shadow-xl shadow-purple-500/20">
                <div class="w-full h-full rounded-[1.1rem] bg-slate-800/90 backdrop-blur flex items-center justify-center">
                  <span class="text-[1.6rem] sm:text-[1.8rem] font-bold bg-clip-text text-transparent bg-gradient-to-br from-violet-300 to-fuchsia-300" style="font-family: 'Playfair Display', serif;">L</span>
                </div>
              </div>
              <div class="absolute -bottom-0.5 -right-0.5 w-4 h-4 rounded-full bg-emerald-500 border-[3px] border-slate-900"></div>
            </div>
            <h1 class="text-xl sm:text-2xl font-bold mb-1.5 text-white/95">
              LZQ 的个人空间
            </h1>
            <p class="text-sm text-white/40 max-w-xs mx-auto">
              探索代码世界，记录生活点滴
            </p>
          </section>

          <!-- Bento Grid -->
          <div class="bento-grid">

            <!-- Kitchen - Featured (spans 2 cols on lg) -->
            <button @click="navigateTo('/kitchen')" class="bento-card card-kitchen group">
              <div class="card-glow glow-kitchen"></div>
              <div class="absolute top-0 right-0 w-48 h-48 bg-gradient-to-br from-amber-500/[0.04] to-transparent rounded-bl-[4rem] pointer-events-none"></div>
              <div class="relative z-10">
                <div class="w-14 h-14 rounded-2xl bg-gradient-to-br from-amber-400 to-orange-500 flex items-center justify-center mb-5 shadow-lg shadow-amber-500/20 transition-transform duration-500 group-hover:scale-110 group-hover:rotate-3">
                  <svg class="w-7 h-7" viewBox="0 0 24 24" fill="white" fill-opacity="0.92">
                    <path d="M12 2C9 2 5 7.5 5 14c0 4.4 3.1 8 7 8s7-3.6 7-8c0-6.5-4-12-7-12zm0 17c-2.5 0-4.5-2.2-4.5-5.5C7.5 9 10 5 12 3.5 14 5 16.5 9 16.5 13.5c0 3.3-2 5.5-4.5 5.5z"/>
                    <ellipse cx="12" cy="15.5" rx="2" ry="2.5" fill-opacity="0.35"/>
                  </svg>
                </div>
                <h2 class="text-xl sm:text-2xl font-bold text-white mb-1">私人厨房</h2>
                <p class="text-[11px] font-medium text-white/30 uppercase tracking-[0.15em] mb-2.5">Kitchen Book</p>
                <p class="text-sm text-white/50 mb-5 leading-relaxed">私人菜谱收藏，记录美食制作方法</p>
                <div class="flex flex-wrap gap-2">
                  <span class="tag">拟物翻书</span>
                  <span class="tag">菜谱管理</span>
                  <span class="tag">订单系统</span>
                </div>
              </div>
            </button>

            <!-- AI Lab -->
            <button @click="navigateTo('/ai-lab')" class="bento-card card-ailab group">
              <div class="card-glow glow-ailab"></div>
              <div class="relative z-10">
                <div class="w-12 h-12 rounded-xl bg-gradient-to-br from-cyan-400 to-teal-500 flex items-center justify-center mb-4 shadow-lg shadow-cyan-500/20 transition-transform duration-500 group-hover:scale-110 group-hover:rotate-3">
                  <svg class="w-6 h-6" viewBox="0 0 24 24" fill="white">
                    <path fill-opacity="0.9" d="M8 2l1.5 4.5L14 8l-4.5 1.5L8 14l-1.5-4.5L2 8l4.5-1.5L8 2z"/>
                    <path fill-opacity="0.6" d="M18 12l.8 2.2L21 15l-2.2.8L18 18l-.8-2.2L15 15l2.2-.8L18 12z"/>
                  </svg>
                </div>
                <h2 class="text-lg sm:text-xl font-bold text-white mb-1">AI 实验室</h2>
                <p class="text-[11px] font-medium text-white/30 uppercase tracking-[0.15em] mb-2">AI Lab</p>
                <p class="text-sm text-white/50 leading-relaxed">DeepSeek 思考模型对话</p>
                <div class="flex flex-wrap gap-2 mt-4">
                  <span class="tag">思维链推理</span>
                  <span class="tag">语音输入</span>
                </div>
              </div>
            </button>

            <!-- QuestionGen -->
            <button @click="navigateTo('/questiongen')" class="bento-card card-qgen group">
              <div class="card-glow glow-qgen"></div>
              <div class="relative z-10">
                <div class="w-12 h-12 rounded-xl bg-gradient-to-br from-blue-400 to-indigo-500 flex items-center justify-center mb-4 shadow-lg shadow-blue-500/20 transition-transform duration-500 group-hover:scale-110 group-hover:rotate-3">
                  <svg class="w-6 h-6" viewBox="0 0 24 24" fill="white" fill-opacity="0.9">
                    <path d="M12 6.5C10 4.5 7 4 5 4v13c2 0 5 .5 7 2.5 2-2 5-2.5 7-2.5V4c-2 0-5 .5-7 2.5z"/>
                  </svg>
                </div>
                <h2 class="text-lg font-bold text-white mb-1">智能刷题</h2>
                <p class="text-[11px] font-medium text-white/30 uppercase tracking-[0.15em] mb-2">Question Gen</p>
                <p class="text-sm text-white/50">AI 驱动的智能学习工具</p>
              </div>
            </button>

            <!-- Tarot -->
            <button @click="navigateTo('/tarot')" class="bento-card card-tarot group">
              <div class="card-glow glow-tarot"></div>
              <div class="relative z-10">
                <div class="w-12 h-12 rounded-xl bg-gradient-to-br from-purple-400 to-indigo-600 flex items-center justify-center mb-4 shadow-lg shadow-purple-500/20 transition-transform duration-500 group-hover:scale-110 group-hover:rotate-3">
                  <svg class="w-6 h-6" viewBox="0 0 24 24" fill="white" fill-opacity="0.9">
                    <path d="M21 12.79A9 9 0 1111.21 3 7 7 0 0021 12.79z"/>
                  </svg>
                </div>
                <h2 class="text-lg font-bold text-white mb-1">塔罗秘仪</h2>
                <p class="text-[11px] font-medium text-white/30 uppercase tracking-[0.15em] mb-2">Tarot Sanctum</p>
                <p class="text-sm text-white/50">沉浸式占卜与神秘解读</p>
              </div>
            </button>

            <!-- Games -->
            <button @click="navigateTo('/games')" class="bento-card card-games group">
              <div class="card-glow glow-games"></div>
              <div class="relative z-10">
                <div class="w-12 h-12 rounded-xl bg-gradient-to-br from-emerald-400 to-teal-500 flex items-center justify-center mb-4 shadow-lg shadow-emerald-500/20 transition-transform duration-500 group-hover:scale-110 group-hover:rotate-3">
                  <svg class="w-6 h-6" viewBox="0 0 24 24" fill="none">
                    <rect x="2" y="7" width="20" height="10" rx="5" fill="white" fill-opacity="0.9"/>
                    <path d="M8.5 10v4M6.5 12h4" stroke="rgba(0,0,0,0.2)" stroke-width="1.5" stroke-linecap="round"/>
                    <circle cx="15.5" cy="10.5" r="1" fill="rgba(0,0,0,0.15)"/>
                    <circle cx="18" cy="12.5" r="1" fill="rgba(0,0,0,0.15)"/>
                  </svg>
                </div>
                <h2 class="text-lg font-bold text-white mb-1">联机游戏</h2>
                <p class="text-[11px] font-medium text-white/30 uppercase tracking-[0.15em] mb-2">Realtime Games</p>
                <p class="text-sm text-white/50">和朋友一起实时对战</p>
              </div>
            </button>

          </div>
        </div>
      </main>

      <!-- Footer -->
      <footer class="px-6 py-6 text-center">
        <div class="flex items-center justify-center gap-2 text-sm text-white/25">
          <span>Built with</span>
          <span class="text-red-400/80">&#10084;</span>
          <span>by LZQ</span>
        </div>
      </footer>
    </div>
  </div>
</template>

<style scoped>
/* ========== Hero entrance ========== */
.hero-section {
  animation: heroIn 0.7s ease-out;
}

@keyframes heroIn {
  from {
    opacity: 0;
    transform: translateY(12px);
  }
}

/* ========== Bento Grid ========== */
.bento-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  grid-template-rows: auto auto;
  gap: 1rem;
}

.card-kitchen {
  grid-column: span 2;
}

@media (max-width: 1024px) {
  .bento-grid {
    grid-template-columns: repeat(2, 1fr);
  }
  .card-kitchen {
    grid-column: span 2;
  }
}

@media (max-width: 640px) {
  .bento-grid {
    grid-template-columns: 1fr;
  }
  .card-kitchen {
    grid-column: span 1;
  }
}

/* ========== Bento Card ========== */
.bento-card {
  position: relative;
  overflow: hidden;
  border-radius: 1.25rem;
  backdrop-filter: blur(16px);
  border: 1px solid rgba(255, 255, 255, 0.07);
  padding: 1.5rem;
  text-align: left;
  cursor: pointer;
  transition: all 0.45s cubic-bezier(0.22, 1, 0.36, 1);
  animation: cardIn 0.6s ease-out backwards;
}

.bento-card:nth-child(1) { animation-delay: 0.08s; }
.bento-card:nth-child(2) { animation-delay: 0.16s; }
.bento-card:nth-child(3) { animation-delay: 0.24s; }
.bento-card:nth-child(4) { animation-delay: 0.32s; }
.bento-card:nth-child(5) { animation-delay: 0.40s; }

@keyframes cardIn {
  from {
    opacity: 0;
    transform: translateY(24px) scale(0.97);
  }
  to {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}

.bento-card:hover {
  transform: translateY(-4px);
  border-color: rgba(255, 255, 255, 0.14);
}

.bento-card:active {
  transform: translateY(-1px) scale(0.99);
}

/* Per-card background tints */
.card-kitchen {
  background: linear-gradient(145deg, rgba(245, 158, 11, 0.07) 0%, rgba(249, 115, 22, 0.025) 100%);
}
.card-kitchen:hover { background: linear-gradient(145deg, rgba(245, 158, 11, 0.11) 0%, rgba(249, 115, 22, 0.04) 100%); }

.card-ailab {
  background: linear-gradient(145deg, rgba(6, 182, 212, 0.07) 0%, rgba(20, 184, 166, 0.025) 100%);
}
.card-ailab:hover { background: linear-gradient(145deg, rgba(6, 182, 212, 0.11) 0%, rgba(20, 184, 166, 0.04) 100%); }

.card-qgen {
  background: linear-gradient(145deg, rgba(59, 130, 246, 0.07) 0%, rgba(99, 102, 241, 0.025) 100%);
}
.card-qgen:hover { background: linear-gradient(145deg, rgba(59, 130, 246, 0.11) 0%, rgba(99, 102, 241, 0.04) 100%); }

.card-tarot {
  background: linear-gradient(145deg, rgba(139, 92, 246, 0.07) 0%, rgba(99, 102, 241, 0.025) 100%);
}
.card-tarot:hover { background: linear-gradient(145deg, rgba(139, 92, 246, 0.11) 0%, rgba(99, 102, 241, 0.04) 100%); }

.card-games {
  background: linear-gradient(145deg, rgba(16, 185, 129, 0.07) 0%, rgba(20, 184, 166, 0.025) 100%);
}
.card-games:hover { background: linear-gradient(145deg, rgba(16, 185, 129, 0.11) 0%, rgba(20, 184, 166, 0.04) 100%); }

/* Hover glow (radial light effect) */
.card-glow {
  position: absolute;
  inset: 0;
  opacity: 0;
  transition: opacity 0.5s;
  pointer-events: none;
}
.bento-card:hover .card-glow { opacity: 1; }

.glow-kitchen { background: radial-gradient(ellipse at 25% 20%, rgba(245, 158, 11, 0.1), transparent 65%); }
.glow-ailab   { background: radial-gradient(ellipse at 25% 20%, rgba(6, 182, 212, 0.1), transparent 65%); }
.glow-qgen    { background: radial-gradient(ellipse at 25% 20%, rgba(59, 130, 246, 0.1), transparent 65%); }
.glow-tarot   { background: radial-gradient(ellipse at 25% 20%, rgba(139, 92, 246, 0.1), transparent 65%); }
.glow-games   { background: radial-gradient(ellipse at 25% 20%, rgba(16, 185, 129, 0.1), transparent 65%); }

/* Feature tags */
.tag {
  display: inline-block;
  padding: 0.2rem 0.6rem;
  font-size: 0.7rem;
  font-weight: 500;
  border-radius: 9999px;
  background: rgba(255, 255, 255, 0.06);
  color: rgba(255, 255, 255, 0.5);
  border: 1px solid rgba(255, 255, 255, 0.05);
}

/* ========== Dynamic background orbs ========== */
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

@keyframes float-1 {
  0%, 100% { transform: translate(0, 0) scale(1); }
  25% { transform: translate(50px, 30px) scale(1.05); }
  50% { transform: translate(20px, 60px) scale(0.95); }
  75% { transform: translate(-30px, 20px) scale(1.02); }
}

@keyframes float-2 {
  0%, 100% { transform: translate(0, 0) scale(1); }
  25% { transform: translate(-40px, -30px) scale(1.03); }
  50% { transform: translate(-70px, 20px) scale(0.97); }
  75% { transform: translate(20px, -40px) scale(1.05); }
}

@keyframes float-3 {
  0%, 100% { transform: translate(-50%, -50%) scale(1) rotate(0deg); }
  33% { transform: translate(-45%, -55%) scale(1.1) rotate(5deg); }
  66% { transform: translate(-55%, -45%) scale(0.9) rotate(-5deg); }
}

@keyframes float-4 {
  0%, 100% { transform: translate(0, 0) scale(1); }
  50% { transform: translate(-60px, 40px) scale(1.08); }
}

/* ========== Particles ========== */
.particle {
  position: absolute;
  border-radius: 50%;
  background: white;
  opacity: 0.4;
  will-change: transform, opacity;
}

.particle-1 { width: 4px; height: 4px; top: 20%; left: 30%; animation: twinkle 3s ease-in-out infinite, drift-1 15s ease-in-out infinite; }
.particle-2 { width: 3px; height: 3px; top: 60%; left: 15%; animation: twinkle 4s ease-in-out infinite 0.5s, drift-2 18s ease-in-out infinite; }
.particle-3 { width: 5px; height: 5px; top: 35%; right: 25%; animation: twinkle 3.5s ease-in-out infinite 1s, drift-3 20s ease-in-out infinite; }
.particle-4 { width: 3px; height: 3px; top: 75%; right: 35%; animation: twinkle 4.5s ease-in-out infinite 1.5s, drift-1 16s ease-in-out infinite reverse; }
.particle-5 { width: 4px; height: 4px; top: 45%; left: 70%; animation: twinkle 3s ease-in-out infinite 2s, drift-2 22s ease-in-out infinite; }
.particle-6 { width: 2px; height: 2px; top: 85%; left: 50%; animation: twinkle 5s ease-in-out infinite 0.8s, drift-3 17s ease-in-out infinite; }

@keyframes twinkle {
  0%, 100% { opacity: 0.2; transform: scale(1); }
  50% { opacity: 0.8; transform: scale(1.2); }
}

@keyframes drift-1 {
  0%, 100% { transform: translate(0, 0); }
  25% { transform: translate(30px, -20px); }
  50% { transform: translate(60px, 10px); }
  75% { transform: translate(20px, 30px); }
}

@keyframes drift-2 {
  0%, 100% { transform: translate(0, 0); }
  33% { transform: translate(-40px, 25px); }
  66% { transform: translate(20px, -35px); }
}

@keyframes drift-3 {
  0%, 100% { transform: translate(0, 0); }
  50% { transform: translate(-50px, -30px); }
}

/* ========== Utilities ========== */
.pt-safe {
  padding-top: max(1rem, env(safe-area-inset-top));
}

.tabular-nums {
  font-variant-numeric: tabular-nums;
}

@media (prefers-reduced-motion: reduce) {
  .orb, .particle { animation: none !important; }
  .bento-card { animation: none !important; }
  .hero-section { animation: none !important; }
}
</style>
