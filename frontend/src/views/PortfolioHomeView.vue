<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()

// 当前时间（拆分 时:分 用于冒号闪烁）
const timeHour = ref('')
const timeMinute = ref('')
const currentDate = ref('')

const updateTime = () => {
  const now = new Date()
  timeHour.value = String(now.getHours()).padStart(2, '0')
  timeMinute.value = String(now.getMinutes()).padStart(2, '0')
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
    path: '/kitchen',
    gradient: 'from-orange-400 via-amber-500 to-yellow-500',
    shadowColor: 'shadow-amber-500/30',
    features: ['拟物翻书', '菜谱管理', '订单系统'],
    featured: true
  },
  {
    id: 'ai-lab',
    title: 'AI 实验室',
    subtitle: 'AI Lab',
    description: 'DeepSeek Reasoner 思考模型对话',
    path: '/ai-lab',
    gradient: 'from-emerald-400 via-teal-500 to-cyan-500',
    shadowColor: 'shadow-teal-500/30',
    features: ['思维链推理', '语音输入']
  },
  {
    id: 'questiongen',
    title: '智能刷题',
    subtitle: 'Question Gen',
    description: 'AI驱动的智能学习工具',
    path: '/questiongen',
    gradient: 'from-cyan-500 via-blue-500 to-indigo-500',
    shadowColor: 'shadow-blue-500/30',
    features: ['AI出题', '知识巩固']
  },
  {
    id: 'tarot',
    title: '塔罗秘仪',
    subtitle: 'Tarot Sanctum',
    description: '沉浸式占卜与神秘解读体验',
    path: '/tarot',
    gradient: 'from-violet-500 via-purple-500 to-indigo-500',
    shadowColor: 'shadow-purple-500/30',
    features: ['互动牌阵', 'AI解读']
  },
  {
    id: 'games',
    title: '联机游戏',
    subtitle: 'Realtime Games',
    description: '和朋友一起实时对战',
    path: '/games',
    gradient: 'from-emerald-500 via-teal-500 to-cyan-500',
    shadowColor: 'shadow-teal-500/30',
    features: ['WebSocket对战', '房间邀请']
  }
]

const navigateTo = (path) => {
  router.push(path)
}
</script>

<template>
  <div class="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 text-white overflow-hidden">
    <!-- 动态背景 -->
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
      <!-- 顶部状态栏 -->
      <header class="pt-safe px-6 py-4 flex items-center justify-between">
        <div class="text-base text-white/60 font-medium">
          {{ currentDate }}
        </div>
        <div class="flex items-center gap-3.5">
          <router-link
            to="/blog"
            class="w-10 h-10 rounded-full bg-gradient-to-br from-violet-500/20 to-purple-500/20 backdrop-blur-sm flex items-center justify-center hover:from-violet-500/40 hover:to-purple-500/40 transition-all duration-300 group border border-white/10 hover:border-violet-400/50"
            title="技术博客"
          >
            <svg class="w-5 h-5 text-white/80 group-hover:text-violet-300 transition-colors" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"/>
            </svg>
          </router-link>
          <a
            href="https://github.com/linzhiqin2003"
            target="_blank"
            class="w-10 h-10 rounded-full bg-white/10 backdrop-blur-sm flex items-center justify-center hover:bg-white/20 transition-colors border border-white/10 hover:border-white/30"
            title="GitHub"
          >
            <svg class="w-5 h-5 text-white/80" fill="currentColor" viewBox="0 0 24 24">
              <path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"/>
            </svg>
          </a>
        </div>
      </header>

      <!-- 主内容 -->
      <main class="flex-1 px-4 sm:px-6 lg:px-8 pb-8">
        <div class="max-w-5xl mx-auto">
          <!-- Hero区域 -->
          <div class="hero-section text-center pt-8 sm:pt-12 pb-10 sm:pb-14">
            <!-- 头像（呼吸光环） -->
            <div class="relative inline-block mb-5">
              <div class="avatar-glow"></div>
              <div class="w-24 h-24 sm:w-28 sm:h-28 rounded-[1.75rem] bg-gradient-to-br from-violet-500 via-purple-500 to-fuchsia-500 p-[3px] shadow-2xl shadow-purple-500/25 relative z-10">
                <div class="w-full h-full rounded-[1.55rem] bg-slate-800 flex items-center justify-center">
                  <span class="text-4xl sm:text-5xl">&#x1F468;&#x200D;&#x1F4BB;</span>
                </div>
              </div>
              <div class="absolute bottom-0.5 right-0.5 w-5 h-5 rounded-full bg-emerald-500 border-[3px] border-slate-900 z-20"></div>
            </div>

            <!-- 时间（冒号闪烁） -->
            <div class="mb-4">
              <div class="text-5xl sm:text-6xl lg:text-7xl font-extralight tracking-tight text-white/90 mb-1 tabular-nums">
                <span>{{ timeHour }}</span><span class="colon-blink">:</span><span>{{ timeMinute }}</span>
              </div>
            </div>

            <!-- 名称和标语 -->
            <h1 class="text-2xl sm:text-3xl lg:text-4xl font-bold mb-3 bg-clip-text text-transparent bg-gradient-to-r from-white via-white to-white/80">
              LZQ 的个人空间
            </h1>
            <p class="text-base sm:text-lg text-white/45 max-w-sm mx-auto leading-relaxed">
              猛猛干 就是玩
            </p>
          </div>

          <!-- Bento 网格 -->
          <div class="bento-grid max-w-4xl mx-auto">
            <button
              v-for="(block, idx) in navBlocks"
              :key="block.id"
              @click="navigateTo(block.path)"
              class="group relative overflow-hidden rounded-3xl backdrop-blur-xl border border-white/10 text-left transition-all duration-500 hover:scale-[1.02] hover:border-white/20 focus:outline-none focus:ring-2 focus:ring-white/20 bento-card"
              :class="[block.featured ? 'card-featured p-6 sm:p-8' : 'p-5 sm:p-6']"
              :style="{ animationDelay: (idx * 0.08 + 0.1) + 's' }"
            >
              <!-- Hover 渐变背景 -->
              <div
                class="absolute inset-0 bg-gradient-to-br opacity-[0.05] group-hover:opacity-[0.12] transition-opacity duration-500"
                :class="block.gradient"
              ></div>

              <!-- Hover 角落光效 -->
              <div class="absolute top-0 right-0 w-40 h-40 bg-gradient-to-br from-white/[0.03] to-transparent rounded-bl-full opacity-0 group-hover:opacity-100 transition-opacity duration-500"></div>

              <!-- 厨房卡片装饰图案 -->
              <div v-if="block.featured" class="kitchen-decor-pattern"></div>

              <!-- 右下角装饰 SVG -->
              <div class="decor-icon" :class="block.featured ? 'decor-lg' : 'decor-sm'">
                <!-- Kitchen: 叉勺交叉 -->
                <svg v-if="block.id === 'kitchen'" viewBox="0 0 48 48" fill="currentColor"><path d="M14 4v14c0 2.2 1.8 4 4 4h1v22h2V22h1c2.2 0 4-1.8 4-4V4h-3v12h-2V4h-2v12h-2V4h-3zm20 0c-2 8-4 12-4 18 0 2.2 1.8 4 4 4v18h2V26c2.2 0 4-1.8 4-4 0-6-2-10-4-18h-2z"/></svg>
                <!-- AI Lab: 原子轨道 -->
                <svg v-else-if="block.id === 'ai-lab'" viewBox="0 0 48 48" fill="none" stroke="currentColor" stroke-width="2"><ellipse cx="24" cy="24" rx="20" ry="8" transform="rotate(0 24 24)"/><ellipse cx="24" cy="24" rx="20" ry="8" transform="rotate(60 24 24)"/><ellipse cx="24" cy="24" rx="20" ry="8" transform="rotate(120 24 24)"/><circle cx="24" cy="24" r="3" fill="currentColor"/></svg>
                <!-- QuestionGen: 灯泡 -->
                <svg v-else-if="block.id === 'questiongen'" viewBox="0 0 48 48" fill="currentColor"><path d="M24 4C16.3 4 10 10.3 10 18c0 4.8 2.4 9 6 11.6V34a4 4 0 004 4h8a4 4 0 004-4v-4.4c3.6-2.6 6-6.8 6-11.6 0-7.7-6.3-14-14-14zm4 36h-8a2 2 0 010-4h8a2 2 0 010 4z"/></svg>
                <!-- Tarot: 月亮与星 -->
                <svg v-else-if="block.id === 'tarot'" viewBox="0 0 48 48" fill="currentColor"><path d="M36 28.6A16 16 0 1119.4 12 12.5 12.5 0 0036 28.6z"/><path d="M38 8l1.2 3.6L43 13l-3.8 1.4L38 18l-1.2-3.6L33 13l3.8-1.4z" opacity="0.7"/></svg>
                <!-- Games: 骰子 -->
                <svg v-else-if="block.id === 'games'" viewBox="0 0 48 48" fill="currentColor"><rect x="6" y="6" width="36" height="36" rx="6"/><circle cx="16" cy="16" r="3" fill="rgba(0,0,0,0.3)"/><circle cx="32" cy="16" r="3" fill="rgba(0,0,0,0.3)"/><circle cx="24" cy="24" r="3" fill="rgba(0,0,0,0.3)"/><circle cx="16" cy="32" r="3" fill="rgba(0,0,0,0.3)"/><circle cx="32" cy="32" r="3" fill="rgba(0,0,0,0.3)"/></svg>
              </div>

              <div class="relative z-10">
                <!-- 图标 -->
                <div
                  class="rounded-2xl bg-gradient-to-br flex items-center justify-center mb-4 shadow-lg transition-transform duration-500 group-hover:scale-110 group-hover:rotate-3"
                  :class="[
                    block.gradient,
                    block.shadowColor,
                    block.featured ? 'w-14 h-14 sm:w-16 sm:h-16' : 'w-12 h-12 sm:w-14 sm:h-14'
                  ]"
                >
                  <!-- Kitchen: emoji -->
                  <span v-if="block.id === 'kitchen'" :class="block.featured ? 'text-3xl sm:text-4xl' : 'text-2xl sm:text-3xl'">🍳</span>
                  <!-- AI Lab: 多角星火花 -->
                  <svg v-else-if="block.id === 'ai-lab'" :class="block.featured ? 'w-7 h-7 sm:w-8 sm:h-8' : 'w-6 h-6 sm:w-7 sm:h-7'" viewBox="0 0 24 24" fill="white">
                    <path d="M12 1.5l2 5.5 5.5 2-5.5 2-2 5.5-2-5.5L4.5 9l5.5-2 2-5.5z" fill-opacity="0.92"/>
                    <path d="M20 12l.8 2.2 2.2.8-2.2.8-.8 2.2-.8-2.2-2.2-.8 2.2-.8.8-2.2z" fill-opacity="0.5"/>
                    <path d="M4 17l.5 1.5 1.5.5-1.5.5-.5 1.5-.5-1.5L2 19l1.5-.5.5-1.5z" fill-opacity="0.35"/>
                  </svg>
                  <!-- QuestionGen: 灯泡 -->
                  <svg v-else-if="block.id === 'questiongen'" :class="block.featured ? 'w-7 h-7 sm:w-8 sm:h-8' : 'w-6 h-6 sm:w-7 sm:h-7'" viewBox="0 0 24 24" fill="none">
                    <path d="M9 21h6m-5-1.5h4M12 3a6 6 0 00-3.5 10.9c.5.5.8 1.2.9 1.8.05.25.2.3.6.3h4c.4 0 .55-.05.6-.3.1-.6.4-1.3.9-1.8A6 6 0 0012 3z" stroke="white" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"/>
                    <path d="M12 3v1.5m6 .5l-1 1M21 10.5h-1.5m-13 0H5m2.5-5l-1-1" stroke="white" stroke-width="1.2" stroke-linecap="round" opacity="0.45"/>
                  </svg>
                  <!-- Tarot: 全视之眼 -->
                  <svg v-else-if="block.id === 'tarot'" :class="block.featured ? 'w-7 h-7 sm:w-8 sm:h-8' : 'w-6 h-6 sm:w-7 sm:h-7'" viewBox="0 0 24 24" fill="white">
                    <path d="M12 5C6 5 1.5 12 1.5 12S6 19 12 19s10.5-7 10.5-7S18 5 12 5z" fill-opacity="0.2"/>
                    <path d="M12 5C6 5 1.5 12 1.5 12S6 19 12 19s10.5-7 10.5-7S18 5 12 5zm0 11a4 4 0 110-8 4 4 0 010 8z" fill-opacity="0.85"/>
                    <circle cx="12" cy="12" r="1.8" fill-opacity="0.95"/>
                  </svg>
                  <!-- Games: 手柄 -->
                  <svg v-else-if="block.id === 'games'" :class="block.featured ? 'w-7 h-7 sm:w-8 sm:h-8' : 'w-6 h-6 sm:w-7 sm:h-7'" viewBox="0 0 24 24" fill="white">
                    <rect x="2" y="7.5" width="20" height="9" rx="4.5" fill-opacity="0.9"/>
                    <path d="M8.5 10v4m-2-2h4" stroke="rgba(0,0,0,0.2)" stroke-width="1.6" stroke-linecap="round"/>
                    <circle cx="15.5" cy="10.5" r="1" fill="rgba(0,0,0,0.15)"/>
                    <circle cx="18" cy="12.5" r="1" fill="rgba(0,0,0,0.15)"/>
                  </svg>
                </div>

                <!-- 标题 -->
                <div class="mb-2">
                  <h2
                    class="font-bold text-white mb-0.5"
                    :class="block.featured ? 'text-xl sm:text-2xl' : 'text-lg sm:text-xl'"
                  >
                    {{ block.title }}
                  </h2>
                  <p class="text-[11px] font-medium text-white/35 uppercase tracking-wider">
                    {{ block.subtitle }}
                  </p>
                </div>

                <!-- 描述 -->
                <p class="text-sm text-white/55 mb-4 leading-relaxed">
                  {{ block.description }}
                </p>

                <!-- 特性标签 -->
                <div class="flex flex-wrap gap-2">
                  <span
                    v-for="feature in block.features"
                    :key="feature"
                    class="px-2.5 py-1 text-xs font-medium rounded-full bg-white/[0.08] text-white/60 border border-white/[0.06]"
                  >
                    {{ feature }}
                  </span>
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
          <span class="text-red-400">&#10084;&#65039;</span>
          <span>by LZQ</span>
          <span class="mx-2">&middot;</span>
          <span>&copy; 2025</span>
        </div>
      </footer>
    </div>
  </div>
</template>

<style scoped>
/* ========== Hero ========== */
.hero-section {
  animation: heroIn 0.7s ease-out;
}

@keyframes heroIn {
  from { opacity: 0; transform: translateY(16px); }
}

/* 头像呼吸光环 */
.avatar-glow {
  position: absolute;
  inset: -6px;
  border-radius: 2rem;
  background: linear-gradient(135deg, #a855f7, #7c3aed, #d946ef);
  opacity: 0.35;
  filter: blur(14px);
  z-index: 0;
  animation: breatheGlow 3s ease-in-out infinite;
}

@keyframes breatheGlow {
  0%, 100% { opacity: 0.25; transform: scale(1); }
  50% { opacity: 0.55; transform: scale(1.08); }
}

/* 冒号闪烁 */
.colon-blink {
  animation: blinkColon 1s step-end infinite;
}

@keyframes blinkColon {
  0%, 100% { opacity: 1; }
  50% { opacity: 0; }
}

.tabular-nums {
  font-variant-numeric: tabular-nums;
}

/* ========== Bento Grid ========== */
.bento-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 1rem;
}

.card-featured {
  grid-column: span 2;
}

@media (max-width: 1024px) {
  .bento-grid {
    grid-template-columns: repeat(2, 1fr);
  }
  .card-featured {
    grid-column: span 2;
  }
}

@media (max-width: 640px) {
  .bento-grid {
    grid-template-columns: 1fr;
  }
  .card-featured {
    grid-column: span 1;
  }
}

/* ========== Bento Card ========== */
.bento-card {
  background: rgba(255, 255, 255, 0.04);
  animation: cardIn 0.55s ease-out backwards;
}

@keyframes cardIn {
  from {
    opacity: 0;
    transform: translateY(20px) scale(0.97);
  }
  to {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}

.bento-card:hover {
  background: rgba(255, 255, 255, 0.08);
}

.bento-card:active {
  transform: scale(0.99) !important;
}

/* 右下角装饰 SVG */
.decor-icon {
  position: absolute;
  bottom: -8%;
  right: -2%;
  pointer-events: none;
  z-index: 1;
  color: white;
  opacity: 0.04;
  transition: opacity 0.5s, transform 0.5s;
  transform: rotate(-8deg);
}

.decor-lg { width: 120px; height: 120px; }
.decor-sm { width: 90px; height: 90px; }

@media (min-width: 640px) {
  .decor-lg { width: 160px; height: 160px; }
  .decor-sm { width: 110px; height: 110px; }
}

.decor-icon svg {
  width: 100%;
  height: 100%;
}

.bento-card:hover .decor-icon {
  opacity: 0.07;
  transform: rotate(-4deg) scale(1.06);
}

/* 厨房卡片装饰线条图案 */
.kitchen-decor-pattern {
  position: absolute;
  inset: 0;
  pointer-events: none;
  z-index: 1;
  opacity: 0.025;
  background-image:
    radial-gradient(circle at 75% 25%, rgba(245, 158, 11, 0.5) 0%, transparent 50%),
    repeating-linear-gradient(
      -45deg,
      transparent,
      transparent 20px,
      rgba(245, 158, 11, 0.15) 20px,
      rgba(245, 158, 11, 0.15) 21px
    );
  transition: opacity 0.5s;
}

.bento-card:hover .kitchen-decor-pattern {
  opacity: 0.06;
}

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

/* ========== 小光点粒子 ========== */
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

/* ========== 其他样式 ========== */
.pt-safe {
  padding-top: max(1rem, env(safe-area-inset-top));
}

.line-clamp-2 {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

@media (prefers-reduced-motion: reduce) {
  .orb, .particle { animation: none !important; }
  .bento-card { animation: none !important; }
  .hero-section { animation: none !important; }
}
</style>
