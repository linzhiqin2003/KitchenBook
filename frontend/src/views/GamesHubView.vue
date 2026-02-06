<script setup>
import { onMounted, onBeforeUnmount, ref } from "vue"
import { useRouter } from "vue-router"

const router = useRouter()

const playableGames = [
  {
    id: "gomoku",
    title: "五子棋",
    subtitle: "实时联机对弈",
    description: "双人实时对弈，支持房间号邀请好友。",
    path: "/games/gomoku",
    features: ["实时同步", "15x15 棋盘", "自动判定"],
    // pixel art colors for the gomoku icon
    iconType: "gomoku",
  },
]

const upcomingGames = [
  {
    id: "tic-tac-toe",
    title: "井字棋",
    subtitle: "经典三连珠",
    iconType: "tictactoe",
  },
  {
    id: "battleship",
    title: "海战棋",
    subtitle: "策略猜位对战",
    iconType: "battleship",
  },
]

const enterGame = (path) => {
  router.push(path)
}

// Starfield animation
const starsSmall = ref("")
const starsMed = ref("")
const starsLarge = ref("")

function generateStars(count, maxSize) {
  const shadows = []
  for (let i = 0; i < count; i++) {
    const x = Math.floor(Math.random() * 2000)
    const y = Math.floor(Math.random() * 2000)
    shadows.push(`${x}px ${y}px 0 ${maxSize}px rgba(255,255,255,${0.3 + Math.random() * 0.7})`)
  }
  return shadows.join(",")
}

let cursorInterval = null
const cursorVisible = ref(true)

onMounted(() => {
  starsSmall.value = generateStars(80, 0)
  starsMed.value = generateStars(30, 0.5)
  starsLarge.value = generateStars(10, 1)
  cursorInterval = setInterval(() => {
    cursorVisible.value = !cursorVisible.value
  }, 530)
})

onBeforeUnmount(() => {
  if (cursorInterval) clearInterval(cursorInterval)
})
</script>

<template>
  <div class="arcade-root">
    <!-- Starfield layers -->
    <div class="stars stars-small" :style="{ boxShadow: starsSmall }"></div>
    <div class="stars stars-med" :style="{ boxShadow: starsMed }"></div>
    <div class="stars stars-large" :style="{ boxShadow: starsLarge }"></div>

    <!-- CRT scanline overlay -->
    <div class="scanlines"></div>

    <div class="arcade-content">
      <!-- Header -->
      <header class="arcade-header">
        <div class="header-top">
          <router-link to="/" class="pixel-btn pixel-btn-ghost">
            <span class="pixel-btn-text">&lt; 主页</span>
          </router-link>
        </div>

        <div class="title-block">
          <p class="subtitle-tag">投币开始</p>
          <h1 class="arcade-title">
            <span class="title-glow">游戏厅</span>
            <span class="cursor-block" :class="{ 'cursor-on': cursorVisible }"></span>
          </h1>
          <p class="subtitle-desc">选择你的游戏</p>
        </div>

        <div class="pixel-divider"></div>
      </header>

      <!-- Playable games -->
      <section class="games-section">
        <h2 class="section-label">
          <span class="label-dot"></span>
          可以游玩
        </h2>
        <div class="games-grid">
          <button
            v-for="game in playableGames"
            :key="game.id"
            @click="enterGame(game.path)"
            class="game-card game-card-active"
          >
            <div class="card-icon-area">
              <!-- Gomoku pixel art icon -->
              <div v-if="game.iconType === 'gomoku'" class="pixel-icon pixel-icon-gomoku">
                <div class="pi-row">
                  <span class="pi-b"></span><span class="pi-e"></span><span class="pi-w"></span>
                </div>
                <div class="pi-row">
                  <span class="pi-e"></span><span class="pi-w"></span><span class="pi-b"></span>
                </div>
                <div class="pi-row">
                  <span class="pi-w"></span><span class="pi-b"></span><span class="pi-e"></span>
                </div>
              </div>
            </div>
            <div class="card-info">
              <h3 class="card-title">{{ game.title }}</h3>
              <p class="card-subtitle">{{ game.subtitle }}</p>
              <p class="card-desc">{{ game.description }}</p>
              <div class="card-tags">
                <span v-for="f in game.features" :key="f" class="pixel-tag">{{ f }}</span>
              </div>
            </div>
            <div class="card-arrow">
              <span class="arrow-text">&gt;&gt;</span>
            </div>
          </button>
        </div>
      </section>

      <!-- Coming soon -->
      <section class="games-section">
        <h2 class="section-label">
          <span class="label-dot label-dot-yellow"></span>
          即将推出
        </h2>
        <div class="upcoming-grid">
          <div
            v-for="game in upcomingGames"
            :key="game.id"
            class="game-card game-card-locked"
          >
            <div class="card-icon-area">
              <!-- Tic-tac-toe pixel art -->
              <div v-if="game.iconType === 'tictactoe'" class="pixel-icon pixel-icon-ttt">
                <div class="pi-row">
                  <span class="pi-x"></span><span class="pi-l"></span><span class="pi-o"></span>
                </div>
                <div class="pi-row pi-row-line">
                  <span class="pi-o"></span><span class="pi-l"></span><span class="pi-x"></span>
                </div>
                <div class="pi-row">
                  <span class="pi-e2"></span><span class="pi-l"></span><span class="pi-e2"></span>
                </div>
              </div>
              <!-- Battleship pixel art -->
              <div v-if="game.iconType === 'battleship'" class="pixel-icon pixel-icon-ship">
                <div class="pi-row">
                  <span class="pi-e2"></span><span class="pi-s"></span><span class="pi-e2"></span>
                </div>
                <div class="pi-row">
                  <span class="pi-s"></span><span class="pi-s"></span><span class="pi-s"></span>
                </div>
                <div class="pi-row">
                  <span class="pi-wave"></span><span class="pi-wave"></span><span class="pi-wave"></span>
                </div>
              </div>
            </div>
            <div class="card-info">
              <h3 class="card-title card-title-locked">{{ game.title }}</h3>
              <p class="card-subtitle">{{ game.subtitle }}</p>
            </div>
            <div class="lock-badge">未开放</div>
          </div>
        </div>
      </section>

      <!-- Footer decoration -->
      <footer class="arcade-footer">
        <div class="pixel-divider"></div>
        <p class="footer-text">按下开始键继续</p>
      </footer>
    </div>
  </div>
</template>

<style scoped>
/* ===== Root & Background ===== */
.arcade-root {
  min-height: 100vh;
  background: #0a0a0a;
  position: relative;
  overflow: hidden;
  font-family: 'Press Start 2P', monospace;
  color: #b0b0b0;
}

/* ===== Starfield ===== */
.stars {
  position: fixed;
  top: 0;
  left: 0;
  width: 2px;
  height: 2px;
  background: transparent;
  pointer-events: none;
}

.stars-small {
  animation: starScroll 120s linear infinite;
}

.stars-med {
  animation: starScroll 80s linear infinite;
}

.stars-large {
  animation: starScroll 50s linear infinite;
}

@keyframes starScroll {
  from { transform: translateY(0); }
  to { transform: translateY(-2000px); }
}

/* ===== Scanlines ===== */
.scanlines {
  position: fixed;
  inset: 0;
  pointer-events: none;
  z-index: 100;
  background: repeating-linear-gradient(
    0deg,
    transparent,
    transparent 2px,
    rgba(0, 0, 0, 0.08) 2px,
    rgba(0, 0, 0, 0.08) 4px
  );
}

/* ===== Content ===== */
.arcade-content {
  position: relative;
  z-index: 10;
  max-width: 900px;
  margin: 0 auto;
  padding: 2rem 1rem 3rem;
}

/* ===== Header ===== */
.arcade-header {
  margin-bottom: 2.5rem;
}

.header-top {
  display: flex;
  justify-content: flex-end;
  margin-bottom: 1.5rem;
}

.title-block {
  text-align: center;
  margin-bottom: 1.5rem;
}

.subtitle-tag {
  font-size: 0.55rem;
  color: #00e5ff;
  letter-spacing: 0.25em;
  margin-bottom: 0.75rem;
  animation: subtitleBlink 3s ease-in-out infinite;
}

@keyframes subtitleBlink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.4; }
}

.arcade-title {
  font-size: 2.5rem;
  line-height: 1.2;
  display: inline-flex;
  align-items: center;
  gap: 0.3em;
}

@media (max-width: 640px) {
  .arcade-title { font-size: 1.6rem; }
}

.title-glow {
  color: #00ff41;
  text-shadow:
    0 0 4px #00ff41,
    0 0 12px rgba(0, 255, 65, 0.5),
    0 0 30px rgba(0, 255, 65, 0.25);
  animation: neonPulse 2.5s ease-in-out infinite;
}

@keyframes neonPulse {
  0%, 100% {
    text-shadow:
      0 0 4px #00ff41,
      0 0 12px rgba(0, 255, 65, 0.5),
      0 0 30px rgba(0, 255, 65, 0.25);
  }
  50% {
    text-shadow:
      0 0 6px #00ff41,
      0 0 20px rgba(0, 255, 65, 0.7),
      0 0 50px rgba(0, 255, 65, 0.4);
  }
}

.cursor-block {
  display: inline-block;
  width: 0.55em;
  height: 1em;
  background: #00ff41;
  vertical-align: middle;
  opacity: 0;
  transition: opacity 0.05s;
}

.cursor-on {
  opacity: 1;
}

.subtitle-desc {
  font-size: 0.6rem;
  color: #666;
  margin-top: 0.75rem;
  letter-spacing: 0.15em;
}

/* ===== Pixel Divider ===== */
.pixel-divider {
  height: 4px;
  background: repeating-linear-gradient(
    90deg,
    #00ff41 0px,
    #00ff41 8px,
    transparent 8px,
    transparent 12px
  );
  opacity: 0.35;
}

/* ===== Section ===== */
.games-section {
  margin-bottom: 2.5rem;
}

.section-label {
  font-size: 0.65rem;
  color: #00ff41;
  letter-spacing: 0.15em;
  margin-bottom: 1rem;
  display: flex;
  align-items: center;
  gap: 0.6em;
}

.label-dot {
  display: inline-block;
  width: 8px;
  height: 8px;
  background: #00ff41;
  box-shadow: 0 0 6px #00ff41;
  animation: dotPulse 1.5s ease-in-out infinite;
}

.label-dot-yellow {
  background: #ffff00;
  box-shadow: 0 0 6px #ffff00;
}

@keyframes dotPulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.3; }
}

/* ===== Games Grid ===== */
.games-grid {
  display: grid;
  gap: 1rem;
}

.upcoming-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 1rem;
}

@media (max-width: 640px) {
  .upcoming-grid { grid-template-columns: 1fr; }
}

/* ===== Game Card ===== */
.game-card {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 1.25rem;
  background: rgba(0, 255, 65, 0.03);
  border: 2px solid rgba(0, 255, 65, 0.15);
  cursor: default;
  text-align: left;
  position: relative;
  transition: all 0.2s;
  /* Pixel border effect via clip-path */
  clip-path: polygon(
    0 8px, 8px 8px, 8px 0,
    calc(100% - 8px) 0, calc(100% - 8px) 8px, 100% 8px,
    100% calc(100% - 8px), calc(100% - 8px) calc(100% - 8px), calc(100% - 8px) 100%,
    8px 100%, 8px calc(100% - 8px), 0 calc(100% - 8px)
  );
}

.game-card-active {
  cursor: pointer;
}

.game-card-active:hover {
  background: rgba(0, 255, 65, 0.08);
  border-color: rgba(0, 255, 65, 0.5);
  box-shadow: 0 0 20px rgba(0, 255, 65, 0.1);
  animation: cardShake 0.3s ease-in-out;
}

@keyframes cardShake {
  0%, 100% { transform: translate(0); }
  25% { transform: translate(-1px, 1px); }
  50% { transform: translate(1px, -1px); }
  75% { transform: translate(-1px, -1px); }
}

.game-card-locked {
  opacity: 0.5;
  border-color: rgba(255, 255, 0, 0.1);
  background: rgba(255, 255, 0, 0.02);
}

/* ===== Card Inner ===== */
.card-icon-area {
  flex-shrink: 0;
  width: 60px;
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.card-info {
  flex: 1;
  min-width: 0;
}

.card-title {
  font-size: 0.85rem;
  color: #00ff41;
  margin-bottom: 0.25rem;
}

.card-title-locked {
  color: #ffff00;
}

.card-subtitle {
  font-size: 0.5rem;
  color: #888;
  margin-bottom: 0.5rem;
}

.card-desc {
  font-size: 0.5rem;
  color: #999;
  line-height: 1.8;
  margin-bottom: 0.6rem;
}

.card-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 0.4rem;
}

.pixel-tag {
  font-size: 0.4rem;
  padding: 0.25em 0.6em;
  background: rgba(0, 229, 255, 0.1);
  border: 1px solid rgba(0, 229, 255, 0.25);
  color: #00e5ff;
  font-family: 'Press Start 2P', monospace;
}

.card-arrow {
  flex-shrink: 0;
  color: #00ff41;
  font-size: 0.75rem;
  animation: arrowBlink 1s step-end infinite;
}

@keyframes arrowBlink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.2; }
}

.lock-badge {
  position: absolute;
  top: 0.6rem;
  right: 0.8rem;
  font-size: 0.4rem;
  color: #ffff00;
  border: 1px solid rgba(255, 255, 0, 0.3);
  padding: 0.2em 0.5em;
  letter-spacing: 0.1em;
}

/* ===== Pixel Art Icons ===== */
.pixel-icon {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.pi-row {
  display: flex;
  gap: 4px;
}

.pi-row-line {
  border-top: 1px solid rgba(255, 0, 255, 0.3);
  border-bottom: 1px solid rgba(255, 0, 255, 0.3);
  padding: 2px 0;
}

/* Gomoku pieces */
.pi-b {
  display: block;
  width: 14px;
  height: 14px;
  border-radius: 50%;
  background: radial-gradient(circle at 35% 35%, #555, #111);
  box-shadow: 0 0 4px rgba(0, 255, 65, 0.3);
}

.pi-w {
  display: block;
  width: 14px;
  height: 14px;
  border-radius: 50%;
  background: radial-gradient(circle at 35% 35%, #fff, #ccc);
  box-shadow: 0 0 4px rgba(255, 255, 255, 0.3);
}

.pi-e {
  display: block;
  width: 14px;
  height: 14px;
  border: 1px solid rgba(0, 255, 65, 0.15);
  background: rgba(0, 255, 65, 0.03);
}

/* Tic-tac-toe */
.pi-x {
  display: block;
  width: 14px;
  height: 14px;
  position: relative;
}

.pi-x::before,
.pi-x::after {
  content: "";
  position: absolute;
  top: 50%;
  left: 50%;
  width: 12px;
  height: 2px;
  background: #ff00ff;
}

.pi-x::before { transform: translate(-50%, -50%) rotate(45deg); }
.pi-x::after { transform: translate(-50%, -50%) rotate(-45deg); }

.pi-o {
  display: block;
  width: 14px;
  height: 14px;
  border-radius: 50%;
  border: 2px solid #00e5ff;
  box-sizing: border-box;
}

.pi-l {
  display: block;
  width: 2px;
  height: 14px;
  background: rgba(255, 0, 255, 0.25);
}

.pi-e2 {
  display: block;
  width: 14px;
  height: 14px;
}

/* Battleship */
.pi-s {
  display: block;
  width: 14px;
  height: 14px;
  background: #666;
  clip-path: polygon(50% 0%, 100% 100%, 0% 100%);
}

.pi-wave {
  display: block;
  width: 14px;
  height: 14px;
  position: relative;
  overflow: hidden;
}

.pi-wave::after {
  content: "";
  position: absolute;
  bottom: 2px;
  left: 0;
  width: 100%;
  height: 3px;
  background: repeating-linear-gradient(
    90deg,
    #00e5ff 0px,
    #00e5ff 4px,
    transparent 4px,
    transparent 6px
  );
  opacity: 0.6;
}

/* ===== Pixel Button ===== */
.pixel-btn {
  font-family: 'Press Start 2P', monospace;
  font-size: 0.5rem;
  padding: 0.6em 1.2em;
  border: 2px solid rgba(0, 255, 65, 0.3);
  background: rgba(0, 255, 65, 0.05);
  color: #00ff41;
  cursor: pointer;
  position: relative;
  transition: all 0.15s;
  text-decoration: none;
  display: inline-block;
  clip-path: polygon(
    0 4px, 4px 4px, 4px 0,
    calc(100% - 4px) 0, calc(100% - 4px) 4px, 100% 4px,
    100% calc(100% - 4px), calc(100% - 4px) calc(100% - 4px), calc(100% - 4px) 100%,
    4px 100%, 4px calc(100% - 4px), 0 calc(100% - 4px)
  );
}

.pixel-btn:hover {
  background: rgba(0, 255, 65, 0.15);
  border-color: #00ff41;
  box-shadow: 0 0 10px rgba(0, 255, 65, 0.2);
}

.pixel-btn:active {
  transform: translateY(2px);
}

.pixel-btn-text {
  letter-spacing: 0.1em;
}

/* ===== Footer ===== */
.arcade-footer {
  margin-top: 1rem;
  text-align: center;
}

.footer-text {
  font-size: 0.5rem;
  color: #444;
  margin-top: 1rem;
  letter-spacing: 0.15em;
  animation: subtitleBlink 3s ease-in-out infinite;
}

/* ===== Responsive ===== */
@media (max-width: 480px) {
  .arcade-content {
    padding: 1rem 0.75rem 2rem;
  }

  .arcade-title {
    font-size: 1.3rem;
  }

  .game-card {
    flex-direction: column;
    align-items: flex-start;
    gap: 0.75rem;
    padding: 1rem;
  }

  .card-icon-area {
    width: 48px;
    height: 48px;
  }

  .card-arrow {
    display: none;
  }

  .card-title {
    font-size: 0.7rem;
  }

  .subtitle-tag, .subtitle-desc {
    font-size: 0.45rem;
  }
}
</style>
