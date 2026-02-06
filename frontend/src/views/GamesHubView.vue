<script setup>
import { useRouter } from "vue-router"

const router = useRouter()

const playableGames = [
  {
    id: "gomoku",
    title: "联机五子棋",
    subtitle: "Gomoku 1v1",
    description: "双人实时对弈，支持房间号邀请好友。",
    icon: "⚫",
    path: "/games/gomoku",
    features: ["WebSocket 实时同步", "15x15 棋盘", "胜负自动判定"],
  },
]

const upcomingGames = [
  {
    id: "tic-tac-toe",
    title: "井字棋",
    status: "准备中",
  },
  {
    id: "battleship",
    title: "海战棋",
    status: "准备中",
  },
]

const enterGame = (path) => {
  router.push(path)
}
</script>

<template>
  <div class="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-emerald-950 text-white">
    <div class="max-w-6xl mx-auto px-4 py-12">
      <header class="mb-10 flex items-center justify-between gap-4">
        <div>
          <p class="text-emerald-300/80 text-sm tracking-[0.2em] uppercase">Realtime Games</p>
          <h1 class="text-3xl sm:text-4xl font-black mt-2">联机游戏集合</h1>
          <p class="text-slate-300 mt-3">先从简单可玩的开始，逐步扩展更多多人小游戏。</p>
        </div>
        <router-link
          to="/"
          class="shrink-0 px-4 py-2 rounded-xl border border-white/20 bg-white/5 hover:bg-white/10 transition-colors"
        >
          返回主页
        </router-link>
      </header>

      <section class="mb-10">
        <h2 class="text-xl font-bold mb-4">可立即体验</h2>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-5">
          <button
            v-for="game in playableGames"
            :key="game.id"
            @click="enterGame(game.path)"
            class="text-left p-6 rounded-2xl border border-emerald-300/30 bg-gradient-to-br from-emerald-500/10 to-cyan-500/5 hover:from-emerald-500/20 hover:to-cyan-500/10 hover:border-emerald-300/50 transition-all"
          >
            <div class="flex items-center gap-3 mb-4">
              <span class="text-3xl">{{ game.icon }}</span>
              <div>
                <h3 class="text-2xl font-bold">{{ game.title }}</h3>
                <p class="text-emerald-200/80 text-sm">{{ game.subtitle }}</p>
              </div>
            </div>
            <p class="text-slate-200/90 mb-4">{{ game.description }}</p>
            <div class="flex flex-wrap gap-2">
              <span
                v-for="feature in game.features"
                :key="feature"
                class="text-xs px-2.5 py-1 rounded-full bg-white/10 border border-white/10"
              >
                {{ feature }}
              </span>
            </div>
          </button>
        </div>
      </section>

      <section>
        <h2 class="text-xl font-bold mb-4">后续计划</h2>
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div
            v-for="game in upcomingGames"
            :key="game.id"
            class="p-5 rounded-2xl border border-white/10 bg-white/5"
          >
            <h3 class="text-lg font-semibold">{{ game.title }}</h3>
            <p class="text-sm text-slate-400 mt-2">{{ game.status }}</p>
          </div>
        </div>
      </section>
    </div>
  </div>
</template>

