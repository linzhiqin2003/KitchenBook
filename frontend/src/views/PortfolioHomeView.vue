<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import QgThemeToggle from '../components/QgThemeToggle.vue'

const router = useRouter()

// Time/date — quiet mono indicator in the top bar
const timeStr = ref('')
const dateStr = ref('')
const updateTime = () => {
  const now = new Date()
  timeStr.value =
    String(now.getHours()).padStart(2, '0') + ':' + String(now.getMinutes()).padStart(2, '0')
  dateStr.value = now
    .toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' })
    .toUpperCase()
}
let timer = null
onMounted(() => { updateTime(); timer = setInterval(updateTime, 30_000) })
onUnmounted(() => { if (timer) clearInterval(timer) })

// The 6 destinations — restrained, no gradient theming. Each has:
//   monogram (mono uppercase, ~2 chars), display name + sub, description, accent hue (subtle)
const destinations = [
  {
    id: 'kitchen',
    monogram: 'KB',
    title: '私人厨房',
    sub: 'Kitchen Book',
    desc: '私人菜谱收藏与点单系统，记录与复现每一道菜。',
    path: '/kitchen',
    accent: 'ochre',
    featured: true,
  },
  {
    id: 'questiongen',
    monogram: 'QG',
    title: '智能刷题',
    sub: 'Practice',
    desc: '选择 / 填空 / 论述三种题型，按主题分级演练。',
    path: '/questiongen',
    accent: 'inky',
  },
  {
    id: 'ai-lab',
    monogram: 'AI',
    title: 'AI 实验室',
    sub: 'AI Lab',
    desc: '推理对话、即时翻译、表情包视频生成。',
    path: '/ai-lab',
    accent: 'teal',
  },
  {
    id: 'tarot',
    monogram: 'TR',
    title: '塔罗秘仪',
    sub: 'Tarot',
    desc: '互动牌阵 + AI 解读，沉浸式占卜。',
    path: '/tarot',
    accent: 'plum',
  },
  {
    id: 'games',
    monogram: 'GM',
    title: '联机游戏',
    sub: 'Realtime',
    desc: '与朋友实时对战，房间制 WebSocket 通信。',
    path: '/games',
    accent: 'forest',
  },
  {
    id: 'blog',
    monogram: 'BL',
    title: '技术博客',
    sub: 'Notes',
    desc: '随笔与读书笔记，附知识图谱视图。',
    path: '/blog',
    accent: 'graphite',
  },
]

const go = (path) => router.push(path)
</script>

<template>
  <div data-qg-surface class="home">
    <!-- Top utility bar -->
    <header class="home__top">
      <div class="home__topLeft" data-mono>
        <span class="home__date">{{ dateStr }}</span>
        <span class="home__sep">·</span>
        <span class="home__time">{{ timeStr }}</span>
      </div>
      <div class="home__topRight">
        <a href="https://github.com/linzhiqin2003" target="_blank" rel="noopener" class="home__icon" title="GitHub">
          <svg viewBox="0 0 24 24" width="14" height="14" fill="currentColor"><path d="M12 .5C5.4.5 0 5.9 0 12.5c0 5.3 3.4 9.8 8.2 11.4.6.1.8-.3.8-.6v-2.1c-3.3.7-4-1.4-4-1.4-.6-1.4-1.4-1.8-1.4-1.8-1.1-.7.1-.7.1-.7 1.2.1 1.8 1.2 1.8 1.2 1.1 1.8 2.8 1.3 3.5 1 .1-.8.4-1.3.8-1.6-2.7-.3-5.5-1.3-5.5-5.9 0-1.3.5-2.4 1.2-3.2-.1-.3-.5-1.5.1-3.2 0 0 1-.3 3.3 1.2.9-.3 2-.4 3-.4s2.1.1 3 .4c2.3-1.5 3.3-1.2 3.3-1.2.7 1.7.2 2.9.1 3.2.8.8 1.2 1.9 1.2 3.2 0 4.6-2.8 5.6-5.5 5.9.4.4.8 1.1.8 2.2v3.3c0 .3.2.7.8.6C20.6 22.3 24 17.8 24 12.5 24 5.9 18.6.5 12 .5z"/></svg>
        </a>
        <QgThemeToggle />
      </div>
    </header>

    <!-- Hero -->
    <section class="home__hero">
      <div class="home__heroInner">
        <div class="home__avatar">
          <img src="/avatar.jpg" alt="LZQ" />
        </div>
        <div class="home__eyebrow" data-mono>Personal · Established 2024</div>
        <h1 class="home__wordmark">LZQ Space</h1>
        <p class="home__tagline">
          一个人的工作室——<br />
          收纳习题、菜谱、随笔、占卜与日常账本。
        </p>
      </div>
    </section>

    <!-- Sections grid -->
    <main class="home__main">
      <div class="home__sectionLabel" data-mono>
        <span class="home__sectionDot"></span>
        <span>Sections</span>
        <span class="home__sectionCount">{{ destinations.length }}</span>
      </div>

      <div class="home__grid">
        <button
          v-for="d in destinations"
          :key="d.id"
          class="home__card"
          :class="{ 'home__card--featured': d.featured }"
          :data-accent="d.accent"
          @click="go(d.path)"
        >
          <header class="home__cardHead">
            <span class="home__monogram" data-mono>{{ d.monogram }}</span>
            <span class="home__cardSub" data-mono>{{ d.sub }}</span>
          </header>

          <div class="home__cardBody">
            <h2 class="home__cardTitle">{{ d.title }}</h2>
            <p class="home__cardDesc">{{ d.desc }}</p>
          </div>

          <footer class="home__cardFoot">
            <span data-mono class="home__cardOpen">Open</span>
            <svg class="home__cardArrow" viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round">
              <path d="M5 12h14M13 6l6 6-6 6"/>
            </svg>
          </footer>
        </button>
      </div>
    </main>

    <!-- Footer -->
    <footer class="home__foot" data-mono>
      <span>www.lzqqq.org</span>
      <span class="home__footSep">·</span>
      <span>v 0.4</span>
      <span class="home__footSep">·</span>
      <span>© LZQ 2025</span>
    </footer>
  </div>
</template>

<style scoped>
.home {
  min-height: 100dvh;
  background: var(--qg-surface-base);
  color: var(--qg-text-primary);
  font-family: var(--qg-font-body);
  display: flex;
  flex-direction: column;
}

/* ─── Top bar ─────────────────────────────────────────────────────── */
.home__top {
  position: sticky;
  top: 0;
  z-index: 30;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px clamp(20px, 4vw, 40px);
  border-bottom: 1px solid var(--qg-border-default);
  background: color-mix(in oklch, var(--qg-surface-base) 88%, transparent);
  backdrop-filter: saturate(160%) blur(8px);
}
.home__topLeft {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  font-size: 11px;
  letter-spacing: 0.08em;
  color: var(--qg-text-secondary);
}
.home__sep, .home__footSep { color: var(--qg-text-muted); }
.home__time { color: var(--qg-text-primary); font-feature-settings: 'tnum'; }

.home__topRight {
  display: inline-flex;
  align-items: center;
  gap: 10px;
}
.home__icon {
  width: 32px;
  height: 32px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  color: var(--qg-text-secondary);
  border: 1px solid var(--qg-border-default);
  border-radius: var(--qg-radius-md);
  text-decoration: none;
  transition: color var(--qg-dur-fast) var(--qg-ease),
              border-color var(--qg-dur-fast) var(--qg-ease),
              background var(--qg-dur-fast) var(--qg-ease);
}
.home__icon:hover {
  color: var(--qg-text-primary);
  border-color: var(--qg-border-strong);
  background: var(--qg-surface-sunken);
}

/* ─── Hero ────────────────────────────────────────────────────────── */
.home__hero {
  border-bottom: 1px solid var(--qg-border-default);
}
.home__heroInner {
  max-width: 980px;
  margin: 0 auto;
  padding: clamp(56px, 8vw, 120px) clamp(24px, 5vw, 48px) clamp(40px, 6vw, 80px);
}

.home__avatar {
  width: 56px;
  height: 56px;
  border-radius: 50%;
  overflow: hidden;
  border: 1px solid var(--qg-border-default);
  background: var(--qg-surface-sunken);
  margin-bottom: 24px;
}
.home__avatar img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

.home__eyebrow {
  font-size: 11px;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  color: var(--qg-text-tertiary);
  margin-bottom: 12px;
}
.home__wordmark {
  font-family: var(--qg-font-display);
  font-weight: 500;
  font-size: clamp(3.25rem, 4vw + 2rem, 6rem);
  line-height: 0.95;
  letter-spacing: -0.035em;
  margin: 0 0 20px;
  color: var(--qg-text-primary);
  font-variation-settings: 'opsz' 96;
}
.home__tagline {
  font-size: var(--qg-text-md);
  line-height: 1.65;
  color: var(--qg-text-secondary);
  max-width: 42ch;
  margin: 0;
}

/* ─── Section grid ────────────────────────────────────────────────── */
.home__main {
  flex: 1;
  max-width: 980px;
  width: 100%;
  margin: 0 auto;
  padding: clamp(32px, 5vw, 56px) clamp(24px, 5vw, 48px) clamp(48px, 6vw, 80px);
}
.home__sectionLabel {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  font-size: 11px;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  color: var(--qg-text-tertiary);
  margin-bottom: 24px;
}
.home__sectionDot {
  width: 6px; height: 6px;
  border-radius: 50%;
  background: var(--qg-text-tertiary);
}
.home__sectionCount {
  margin-left: 4px;
  color: var(--qg-text-muted);
}

.home__grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 14px;
}
@media (min-width: 720px) {
  .home__grid { grid-template-columns: repeat(3, 1fr); }
}
@media (max-width: 480px) {
  .home__grid { grid-template-columns: 1fr; }
}

/* Featured card spans full width — reads like the main entry */
.home__card--featured {
  grid-column: 1 / -1;
}

/* ─── Card ────────────────────────────────────────────────────────── */
.home__card {
  --card-accent: var(--qg-text-primary);
  position: relative;
  display: flex;
  flex-direction: column;
  gap: 18px;
  padding: clamp(20px, 2.4vw, 28px);
  text-align: left;
  background: var(--qg-surface-raised);
  border: 1px solid var(--qg-border-default);
  border-radius: var(--qg-radius-lg);
  cursor: pointer;
  font: inherit;
  color: inherit;
  transition: border-color var(--qg-dur-base) var(--qg-ease),
              transform var(--qg-dur-base) var(--qg-ease),
              box-shadow var(--qg-dur-base) var(--qg-ease);
  overflow: hidden;
}
.home__card::before {
  /* A near-invisible accent corner — only visible on hover */
  content: "";
  position: absolute;
  inset: -1px -1px auto auto;
  width: 64px;
  height: 64px;
  background: radial-gradient(circle at top right,
              color-mix(in oklch, var(--card-accent) 22%, transparent) 0%,
              transparent 70%);
  opacity: 0;
  transition: opacity var(--qg-dur-base) var(--qg-ease);
  pointer-events: none;
}
.home__card:hover {
  border-color: var(--qg-border-strong);
  box-shadow: var(--qg-shadow-2);
  transform: translateY(-2px);
}
.home__card:hover::before { opacity: 1; }
.home__card:focus-visible {
  outline: none;
  box-shadow: var(--qg-shadow-focus);
}
.home__card:active { transform: translateY(0); }

/* Per-accent — keep extremely restrained, only an oklch hue tweak */
.home__card[data-accent="ochre"]    { --card-accent: oklch(0.60 0.13 65); }
.home__card[data-accent="inky"]     { --card-accent: oklch(0.50 0.13 252); }
.home__card[data-accent="teal"]     { --card-accent: oklch(0.55 0.10 200); }
.home__card[data-accent="plum"]     { --card-accent: oklch(0.50 0.10 320); }
.home__card[data-accent="forest"]   { --card-accent: oklch(0.50 0.09 155); }
.home__card[data-accent="graphite"] { --card-accent: oklch(0.45 0.02 80); }

.home__cardHead {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}
.home__monogram {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 28px;
  height: 22px;
  padding: 0 7px;
  font-size: 10.5px;
  font-weight: 500;
  letter-spacing: 0.08em;
  color: var(--card-accent);
  background: color-mix(in oklch, var(--card-accent) 10%, transparent);
  border: 1px solid color-mix(in oklch, var(--card-accent) 22%, transparent);
  border-radius: var(--qg-radius-sm);
}
.home__cardSub {
  font-size: 10.5px;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: var(--qg-text-tertiary);
}

.home__cardBody { display: flex; flex-direction: column; gap: 6px; }
.home__cardTitle {
  font-family: var(--qg-font-display);
  font-size: clamp(1.25rem, 0.9rem + 0.6vw, 1.625rem);
  font-weight: 500;
  letter-spacing: -0.02em;
  line-height: 1.15;
  margin: 0;
  color: var(--qg-text-primary);
  font-variation-settings: 'opsz' 36;
}
.home__cardDesc {
  font-size: var(--qg-text-sm);
  line-height: 1.55;
  color: var(--qg-text-secondary);
  margin: 0;
  /* keep two-line max for visual rhythm */
  display: -webkit-box;
  -webkit-line-clamp: 2;
  line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.home__cardFoot {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-top: auto;
  padding-top: 8px;
  border-top: 1px dashed var(--qg-border-default);
  font-size: 10px;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  color: var(--qg-text-tertiary);
  transition: color var(--qg-dur-fast) var(--qg-ease);
}
.home__cardArrow {
  margin-left: auto;
  color: var(--qg-text-tertiary);
  transition: color var(--qg-dur-fast) var(--qg-ease),
              transform var(--qg-dur-fast) var(--qg-ease);
}
.home__card:hover .home__cardFoot { color: var(--card-accent); }
.home__card:hover .home__cardArrow {
  color: var(--card-accent);
  transform: translateX(3px);
}

/* Featured card gets a slightly larger title and extra body padding */
.home__card--featured .home__cardTitle {
  font-size: clamp(1.625rem, 1.1rem + 1.2vw, 2.125rem);
}
.home__card--featured .home__cardDesc {
  font-size: var(--qg-text-base);
  -webkit-line-clamp: 3;
  line-clamp: 3;
}
.home__card--featured {
  padding: clamp(28px, 3.5vw, 40px);
  gap: 24px;
}

/* ─── Footer ──────────────────────────────────────────────────────── */
.home__foot {
  border-top: 1px solid var(--qg-border-default);
  padding: 18px clamp(20px, 4vw, 40px);
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  font-size: 11px;
  letter-spacing: 0.05em;
  color: var(--qg-text-muted);
}

@media (prefers-reduced-motion: reduce) {
  .home__card,
  .home__cardArrow { transition: none !important; }
  .home__card:hover { transform: none; }
}
</style>
