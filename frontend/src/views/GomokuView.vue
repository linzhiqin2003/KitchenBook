<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from "vue"
import { useRoute, useRouter } from "vue-router"

import { getWsBaseUrl } from "../config/ws"

const BOARD_SIZE = 15

const route = useRoute()
const router = useRouter()

const ws = ref(null)
const connecting = ref(false)
const connected = ref(false)

const roomInput = ref("")
const roomId = ref("")
const nickname = ref("")

const role = ref("spectator")
const playerColor = ref("")
const status = ref("waiting")
const turn = ref("black")
const winner = ref(null)
const players = ref({ black: null, white: null })
const spectators = ref([])
const online = ref({
  room: { players: 0, spectators: 0, total: 0 },
  global: { totalConnections: 0, rooms: 0 },
})
const lastMove = ref(null)
const board = ref(createEmptyBoard())

const errorMessage = ref("")
const noticeMessage = ref("")

function createEmptyBoard() {
  return Array.from({ length: BOARD_SIZE }, () => Array(BOARD_SIZE).fill(0))
}

function sanitizeRoomId(value) {
  if (!value) return ""
  return String(value).toUpperCase().replace(/[^A-Z0-9_-]/g, "").slice(0, 20)
}

function sanitizeNickname(value) {
  if (!value) return ""
  return String(value).trim().slice(0, 20)
}

function createRandomRoomId() {
  const chars = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
  let id = ""
  for (let i = 0; i < 6; i += 1) {
    id += chars[Math.floor(Math.random() * chars.length)]
  }
  return id
}

function buildWsUrl(room, name) {
  const encodedRoom = encodeURIComponent(room)
  const encodedName = encodeURIComponent(name || "Guest")
  return `${getWsBaseUrl()}/ws/games/gomoku/${encodedRoom}/?name=${encodedName}`
}

function resetGameState() {
  board.value = createEmptyBoard()
  players.value = { black: null, white: null }
  spectators.value = []
  online.value = {
    room: { players: 0, spectators: 0, total: 0 },
    global: { totalConnections: 0, rooms: 0 },
  }
  status.value = "waiting"
  turn.value = "black"
  winner.value = null
  lastMove.value = null
}

const isSpectator = computed(() => role.value === "spectator")

const playerColorLabel = computed(() => {
  if (isSpectator.value) return "观战"
  if (playerColor.value === "black") return "黑子"
  if (playerColor.value === "white") return "白子"
  return "未分配"
})

const winnerLabel = computed(() => {
  if (winner.value === "black") return "黑子胜"
  if (winner.value === "white") return "白子胜"
  if (winner.value === "draw") return "平局"
  return ""
})

const turnLabel = computed(() => (turn.value === "black" ? "黑子" : "白子"))

const statusText = computed(() => {
  if (!connected.value && connecting.value) return "正在建立连接..."
  if (!connected.value) return "未连接房间"
  if (status.value === "waiting") return isSpectator.value ? "观战中：等待玩家到齐" : "等待另一位玩家加入"
  if (status.value === "finished") return `对局结束：${winnerLabel.value}`
  if (isSpectator.value) return `观战中：${turnLabel.value}落子`
  return `进行中：${turnLabel.value}落子`
})

const canPlaceStone = computed(
  () =>
    connected.value &&
    !isSpectator.value &&
    status.value === "playing" &&
    playerColor.value &&
    playerColor.value === turn.value
)

const canRestart = computed(
  () => connected.value && !isSpectator.value && online.value.room.players === 2
)

const flatCells = computed(() => {
  const cells = []
  for (let y = 0; y < BOARD_SIZE; y += 1) {
    for (let x = 0; x < BOARD_SIZE; x += 1) {
      cells.push({ x, y, key: `${x}-${y}` })
    }
  }
  return cells
})

const shareLink = computed(() => {
  if (!roomId.value) return ""
  return `${window.location.origin}/games/gomoku/${roomId.value}`
})

function updateRoomFromRoute() {
  const presetRoom = sanitizeRoomId(route.params.roomId)
  const presetName = sanitizeNickname(typeof route.query.name === "string" ? route.query.name : "")
  if (presetRoom) {
    roomInput.value = presetRoom
  }
  if (presetName) {
    nickname.value = presetName
  }
}

function closeSocket(silent = false) {
  const socket = ws.value
  ws.value = null
  connected.value = false
  connecting.value = false
  role.value = "spectator"
  playerColor.value = ""

  if (socket && (socket.readyState === WebSocket.OPEN || socket.readyState === WebSocket.CONNECTING)) {
    socket.close()
  }

  if (!silent) {
    noticeMessage.value = "已离开房间。"
  }
}

function connectRoom() {
  const nextRoomId = sanitizeRoomId(roomInput.value)
  const nextNickname = sanitizeNickname(nickname.value)

  if (!nextRoomId) {
    errorMessage.value = "请输入房间号（3-20位，仅字母数字-_）。"
    return
  }

  if (nextRoomId.length < 3) {
    errorMessage.value = "房间号至少 3 位。"
    return
  }

  if (!nextNickname) {
    errorMessage.value = "请输入昵称。"
    return
  }

  roomInput.value = nextRoomId
  nickname.value = nextNickname
  errorMessage.value = ""
  noticeMessage.value = ""
  resetGameState()
  closeSocket(true)

  connecting.value = true
  const socket = new WebSocket(buildWsUrl(nextRoomId, nextNickname))
  ws.value = socket

  socket.onopen = () => {
    connected.value = true
    connecting.value = false
    roomId.value = nextRoomId
    noticeMessage.value = "连接成功，等待服务器分配座位..."
    router.replace({ path: `/games/gomoku/${nextRoomId}`, query: { name: nextNickname } })
  }

  socket.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data)
      handleServerMessage(data)
    } catch (error) {
      errorMessage.value = "收到无法解析的服务器消息。"
    }
  }

  socket.onerror = () => {
    errorMessage.value = "WebSocket 连接异常，请稍后重试。"
  }

  socket.onclose = () => {
    if (ws.value === socket) {
      ws.value = null
    }
    connected.value = false
    connecting.value = false
  }
}

function handleServerMessage(data) {
  if (data.type === "joined") {
    role.value = data.role || (data.playerColor ? "player" : "spectator")
    playerColor.value = data.playerColor || ""
    roomId.value = data.roomId || roomId.value
    if (role.value === "spectator") {
      noticeMessage.value = `已加入房间 ${roomId.value}，你当前为观战模式。`
    } else {
      noticeMessage.value = `已加入房间 ${roomId.value}，你执 ${playerColorLabel.value}。`
    }
    return
  }

  if (data.type === "room_state") {
    if (Array.isArray(data.board) && data.board.length === BOARD_SIZE) {
      board.value = data.board
    }
    players.value = data.players || { black: null, white: null }
    status.value = data.status || "waiting"
    turn.value = data.turn || "black"
    winner.value = data.winner ?? null
    lastMove.value = data.lastMove || null
    spectators.value = Array.isArray(data.spectators) ? data.spectators : []
    if (data.online && data.online.room && data.online.global) {
      online.value = data.online
    }
    return
  }

  if (data.type === "error") {
    errorMessage.value = data.message || "服务器返回错误。"
    return
  }

  if (data.type === "pong") {
    return
  }
}

function sendMessage(payload) {
  if (!ws.value || ws.value.readyState !== WebSocket.OPEN) {
    return
  }
  ws.value.send(JSON.stringify(payload))
}

function placeStone(x, y) {
  if (!canPlaceStone.value) return
  if (board.value[y][x] !== 0) return
  sendMessage({ type: "move", x, y })
}

function restartGame() {
  sendMessage({ type: "restart" })
}

function leaveRoom() {
  closeSocket(false)
}

function randomRoomAndConnect() {
  if (!nickname.value.trim()) {
    nickname.value = "Guest"
  }
  roomInput.value = createRandomRoomId()
  connectRoom()
}

async function copyShareLink() {
  if (!shareLink.value) return
  try {
    await navigator.clipboard.writeText(shareLink.value)
    noticeMessage.value = "邀请链接已复制。"
  } catch (error) {
    errorMessage.value = "复制失败，请手动复制链接。"
  }
}

function isLastMove(x, y) {
  return lastMove.value && lastMove.value.x === x && lastMove.value.y === y
}

function stoneClass(value) {
  if (value === 1) return "stone stone-black"
  if (value === 2) return "stone stone-white"
  return ""
}

function cellValue(x, y) {
  return board.value[y]?.[x] ?? 0
}

onMounted(() => {
  updateRoomFromRoute()
  if (roomInput.value && nickname.value) {
    connectRoom()
  }
})

onBeforeUnmount(() => {
  closeSocket(true)
})
</script>

<template>
  <div class="min-h-screen bg-gradient-to-br from-stone-950 via-slate-900 to-amber-950 text-white">
    <div class="max-w-7xl mx-auto px-4 py-8">
      <header class="mb-6 flex flex-wrap items-center justify-between gap-3">
        <div>
          <p class="text-amber-300/80 text-sm tracking-[0.2em] uppercase">Gomoku Online</p>
          <h1 class="text-3xl sm:text-4xl font-black mt-2">五子棋联机对弈</h1>
        </div>
        <div class="flex items-center gap-2">
          <router-link
            to="/games"
            class="px-4 py-2 rounded-xl bg-white/10 border border-white/20 hover:bg-white/20 transition-colors"
          >
            返回游戏集合
          </router-link>
          <router-link
            to="/"
            class="px-4 py-2 rounded-xl bg-white/10 border border-white/20 hover:bg-white/20 transition-colors"
          >
            回到主页
          </router-link>
        </div>
      </header>

      <section class="grid grid-cols-1 xl:grid-cols-[1fr_360px] gap-6">
        <div class="rounded-3xl bg-black/20 border border-white/10 p-4 sm:p-6">
          <div class="gomoku-board">
            <button
              v-for="cell in flatCells"
              :key="cell.key"
              class="gomoku-cell"
              :class="{
                'gomoku-cell-playable': canPlaceStone && cellValue(cell.x, cell.y) === 0,
                'gomoku-cell-last': isLastMove(cell.x, cell.y),
              }"
              :disabled="cellValue(cell.x, cell.y) !== 0 || !canPlaceStone"
              @click="placeStone(cell.x, cell.y)"
            >
              <span
                v-if="cellValue(cell.x, cell.y) !== 0"
                :class="stoneClass(cellValue(cell.x, cell.y))"
              ></span>
            </button>
          </div>
        </div>

        <aside class="rounded-3xl bg-black/20 border border-white/10 p-5 sm:p-6 space-y-5">
          <div class="space-y-3">
            <label class="block text-sm text-slate-300">
              昵称
              <input
                v-model="nickname"
                type="text"
                maxlength="20"
                placeholder="输入昵称"
                class="mt-1 w-full rounded-xl bg-white/10 border border-white/20 px-3 py-2 outline-none focus:border-amber-400"
              />
            </label>

            <label class="block text-sm text-slate-300">
              房间号
              <input
                v-model="roomInput"
                type="text"
                maxlength="20"
                placeholder="例如 A1B2C3"
                class="mt-1 w-full rounded-xl bg-white/10 border border-white/20 px-3 py-2 outline-none focus:border-amber-400 uppercase"
              />
            </label>

            <div class="grid grid-cols-1 sm:grid-cols-2 gap-2">
              <button
                @click="connectRoom"
                :disabled="connecting"
                class="px-4 py-2 rounded-xl bg-amber-500 text-black font-semibold hover:bg-amber-400 disabled:opacity-60 transition-colors"
              >
                {{ connecting ? "连接中..." : "加入房间" }}
              </button>
              <button
                @click="randomRoomAndConnect"
                :disabled="connecting"
                class="px-4 py-2 rounded-xl bg-cyan-500/90 text-black font-semibold hover:bg-cyan-400 disabled:opacity-60 transition-colors"
              >
                随机房间
              </button>
            </div>

            <div class="grid grid-cols-1 sm:grid-cols-2 gap-2">
              <button
                @click="leaveRoom"
                class="px-4 py-2 rounded-xl bg-white/10 border border-white/20 hover:bg-white/20 transition-colors"
              >
                离开房间
              </button>
              <button
                @click="copyShareLink"
                :disabled="!shareLink"
                class="px-4 py-2 rounded-xl bg-white/10 border border-white/20 hover:bg-white/20 disabled:opacity-50 transition-colors"
              >
                复制邀请链接
              </button>
            </div>

            <p class="text-xs text-slate-400">
              提示：同一房间前两位为对弈玩家，后续加入会自动进入观战模式。
            </p>
          </div>

          <div class="rounded-2xl bg-white/5 border border-white/10 p-4 space-y-2">
            <h3 class="font-semibold text-lg">对局状态</h3>
            <p class="text-slate-200">{{ statusText }}</p>
            <p class="text-slate-300 text-sm">房间号：{{ roomId || "-" }}</p>
            <p class="text-slate-300 text-sm">当前身份：{{ isSpectator ? "观战者" : "玩家" }}</p>
            <p class="text-slate-300 text-sm">你当前执子：{{ playerColorLabel }}</p>
          </div>

          <div class="rounded-2xl bg-white/5 border border-white/10 p-4 space-y-2">
            <h3 class="font-semibold text-lg">玩家列表</h3>
            <p class="text-sm">
              黑子：<span class="text-slate-200">{{ players.black?.nickname || "等待加入" }}</span>
            </p>
            <p class="text-sm">
              白子：<span class="text-slate-200">{{ players.white?.nickname || "等待加入" }}</span>
            </p>
            <button
              @click="restartGame"
              :disabled="!canRestart"
              class="mt-2 px-4 py-2 rounded-xl bg-emerald-500 text-black font-semibold hover:bg-emerald-400 transition-colors"
              :class="{ 'opacity-50 cursor-not-allowed hover:bg-emerald-500': !canRestart }"
            >
              重开一局
            </button>
          </div>

          <div class="rounded-2xl bg-white/5 border border-white/10 p-4 space-y-2">
            <h3 class="font-semibold text-lg">在线人数</h3>
            <p class="text-sm">
              房间在线：
              <span class="text-slate-200">{{ online.room.total }}</span>
              （玩家 {{ online.room.players }} / 观战 {{ online.room.spectators }}）
            </p>
            <p class="text-sm">
              全局在线：
              <span class="text-slate-200">{{ online.global.totalConnections }}</span>
              （活跃房间 {{ online.global.rooms }}）
            </p>
          </div>

          <div class="rounded-2xl bg-white/5 border border-white/10 p-4 space-y-2">
            <h3 class="font-semibold text-lg">观战列表</h3>
            <p class="text-sm text-slate-300">共 {{ spectators.length }} 人观战</p>
            <div v-if="spectators.length === 0" class="text-sm text-slate-400">暂无观战者</div>
            <ul v-else class="max-h-32 overflow-auto space-y-1 pr-1">
              <li
                v-for="(item, index) in spectators"
                :key="`${item.nickname}-${index}`"
                class="text-sm text-slate-200"
              >
                {{ item.nickname }}
              </li>
            </ul>
          </div>

          <div v-if="noticeMessage" class="rounded-xl border border-emerald-300/40 bg-emerald-500/10 px-3 py-2 text-sm text-emerald-100">
            {{ noticeMessage }}
          </div>
          <div v-if="errorMessage" class="rounded-xl border border-red-300/40 bg-red-500/10 px-3 py-2 text-sm text-red-100">
            {{ errorMessage }}
          </div>
        </aside>
      </section>
    </div>
  </div>
</template>

<style scoped>
.gomoku-board {
  width: min(92vw, 720px);
  max-width: 100%;
  aspect-ratio: 1 / 1;
  margin: 0 auto;
  display: grid;
  grid-template-columns: repeat(15, minmax(0, 1fr));
  grid-template-rows: repeat(15, minmax(0, 1fr));
  border: 2px solid rgba(0, 0, 0, 0.45);
  border-radius: 18px;
  overflow: hidden;
  background: linear-gradient(145deg, #d8a15f, #c7883c);
  box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.15), 0 18px 40px rgba(0, 0, 0, 0.35);
}

.gomoku-cell {
  position: relative;
  border: 1px solid rgba(71, 36, 7, 0.3);
  background: rgba(255, 255, 255, 0.06);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0;
}

.gomoku-cell-playable:hover {
  background: rgba(255, 255, 255, 0.2);
}

.gomoku-cell-last {
  box-shadow: inset 0 0 0 2px rgba(239, 68, 68, 0.9);
}

.stone {
  width: 74%;
  height: 74%;
  border-radius: 9999px;
  display: block;
}

.stone-black {
  background: radial-gradient(circle at 30% 30%, #5b5b5b 0%, #151515 55%, #020202 100%);
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.45);
}

.stone-white {
  background: radial-gradient(circle at 30% 30%, #ffffff 0%, #f2f2f2 55%, #d8d8d8 100%);
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.3);
}
</style>
