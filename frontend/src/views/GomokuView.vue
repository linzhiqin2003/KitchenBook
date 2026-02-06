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
  if (!connected.value && connecting.value) return "CONNECTING..."
  if (!connected.value) return "NOT CONNECTED"
  if (status.value === "waiting") return isSpectator.value ? "SPECTATING - WAITING" : "WAITING FOR OPPONENT"
  if (status.value === "finished") return `GAME OVER: ${winnerLabel.value}`
  if (isSpectator.value) return `SPECTATING: ${turnLabel.value}`
  return `YOUR TURN: ${turnLabel.value}`
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

// Blinking cursor for overlay
let cursorInterval = null
const cursorVisible = ref(true)

onMounted(() => {
  updateRoomFromRoute()
  if (roomInput.value && nickname.value) {
    connectRoom()
  }
  cursorInterval = setInterval(() => {
    cursorVisible.value = !cursorVisible.value
  }, 530)
})

onBeforeUnmount(() => {
  closeSocket(true)
  if (cursorInterval) clearInterval(cursorInterval)
})
</script>

<template>
  <div class="gomoku-root">
    <!-- Scanlines -->
    <div class="scanlines"></div>

    <div class="gomoku-content">
      <!-- Header -->
      <header class="gomoku-header">
        <div class="header-left">
          <p class="header-tag">GOMOKU ONLINE</p>
          <h1 class="header-title">
            <span class="title-glow">五子棋</span>
          </h1>
        </div>
        <div class="header-nav">
          <router-link to="/games" class="pixel-btn">
            &lt; ARCADE
          </router-link>
          <router-link to="/" class="pixel-btn">
            HOME
          </router-link>
        </div>
      </header>

      <!-- Status bar (only when connected) -->
      <div v-if="connected" class="status-bar">
        <span class="status-dot dot-on"></span>
        <span class="status-text">{{ statusText }}</span>
      </div>

      <!-- Main layout -->
      <section class="main-layout" :class="{ 'layout-full': !connected }">
        <!-- Board area with overlay -->
        <div class="board-area">
          <div class="board-wrapper">
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

          <!-- Board overlay when not connected -->
          <Transition name="overlay-fade">
            <div v-if="!connected" class="board-overlay">
              <div class="overlay-content">
                <div class="overlay-title">
                  <span class="ov-text">INSERT COIN</span>
                  <span class="ov-cursor" :class="{ 'cursor-on': cursorVisible }"></span>
                </div>
                <p class="overlay-sub">输入信息加入对局</p>

                <div class="overlay-form">
                  <label class="field-label">
                    NICKNAME
                    <input
                      v-model="nickname"
                      type="text"
                      maxlength="20"
                      placeholder="YOUR NAME"
                      class="pixel-input"
                      @keyup.enter="connectRoom"
                    />
                  </label>

                  <label class="field-label">
                    ROOM ID
                    <input
                      v-model="roomInput"
                      type="text"
                      maxlength="20"
                      placeholder="e.g. A1B2C3"
                      class="pixel-input uppercase"
                      @keyup.enter="connectRoom"
                    />
                  </label>

                  <div class="btn-row">
                    <button
                      @click="connectRoom"
                      :disabled="connecting"
                      class="pixel-btn pixel-btn-primary"
                    >
                      {{ connecting ? "CONNECTING..." : "JOIN ROOM" }}
                    </button>
                    <button
                      @click="randomRoomAndConnect"
                      :disabled="connecting"
                      class="pixel-btn pixel-btn-cyan"
                    >
                      RANDOM
                    </button>
                  </div>

                  <p class="overlay-hint">前两位进入为对弈玩家，后续自动观战</p>

                  <!-- Error on overlay -->
                  <div v-if="errorMessage" class="msg msg-error">
                    {{ errorMessage }}
                  </div>
                </div>
              </div>
            </div>
          </Transition>
        </div>

        <!-- Sidebar (only when connected) -->
        <aside v-if="connected" class="sidebar">
          <!-- Room & identity -->
          <div class="panel">
            <h3 class="panel-title">
              ROOM: {{ roomId }}
              <span class="panel-badge">{{ isSpectator ? "SPECTATOR" : playerColorLabel }}</span>
            </h3>
            <div class="panel-body">
              <div class="btn-row">
                <button @click="leaveRoom" class="pixel-btn pixel-btn-small">
                  LEAVE
                </button>
                <button
                  @click="copyShareLink"
                  :disabled="!shareLink"
                  class="pixel-btn pixel-btn-small"
                >
                  INVITE
                </button>
              </div>
            </div>
          </div>

          <!-- Players -->
          <div class="panel">
            <h3 class="panel-title">PLAYERS</h3>
            <div class="panel-body info-list">
              <p>
                <span class="stone-indicator stone-indicator-b"></span>
                <span :class="{ 'player-turn': turn === 'black' && status === 'playing' }">
                  {{ players.black?.nickname || "WAITING..." }}
                </span>
                <span v-if="turn === 'black' && status === 'playing'" class="turn-arrow">&lt;</span>
              </p>
              <p>
                <span class="stone-indicator stone-indicator-w"></span>
                <span :class="{ 'player-turn': turn === 'white' && status === 'playing' }">
                  {{ players.white?.nickname || "WAITING..." }}
                </span>
                <span v-if="turn === 'white' && status === 'playing'" class="turn-arrow">&lt;</span>
              </p>
              <button
                v-if="canRestart || status === 'finished'"
                @click="restartGame"
                :disabled="!canRestart"
                class="pixel-btn pixel-btn-green pixel-btn-small mt-2"
                :class="{ 'pixel-btn-disabled': !canRestart }"
              >
                RESTART
              </button>
            </div>
          </div>

          <!-- Online + Spectators combined -->
          <div class="panel">
            <h3 class="panel-title">
              ONLINE
              <span class="panel-count">{{ online.room.total }}</span>
            </h3>
            <div class="panel-body info-list">
              <p>
                <span class="info-key">ROOM:</span>
                P:{{ online.room.players }} / S:{{ online.room.spectators }}
              </p>
              <p>
                <span class="info-key">GLOBAL:</span>
                {{ online.global.totalConnections }} ({{ online.global.rooms }} rooms)
              </p>
              <div v-if="spectators.length > 0" class="spectator-section">
                <p class="spectator-label">SPECTATORS:</p>
                <span
                  v-for="(item, index) in spectators"
                  :key="`${item.nickname}-${index}`"
                  class="spectator-name"
                >{{ item.nickname }}<span v-if="index < spectators.length - 1">, </span></span>
              </div>
            </div>
          </div>

          <!-- Messages -->
          <div v-if="noticeMessage" class="msg msg-notice">
            {{ noticeMessage }}
          </div>
          <div v-if="errorMessage" class="msg msg-error">
            {{ errorMessage }}
          </div>
        </aside>
      </section>
    </div>
  </div>
</template>

<style scoped>
/* ===== Root ===== */
.gomoku-root {
  min-height: 100vh;
  background: #0a0a0a;
  position: relative;
  font-family: 'Press Start 2P', monospace;
  color: #b0b0b0;
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
    rgba(0, 0, 0, 0.06) 2px,
    rgba(0, 0, 0, 0.06) 4px
  );
}

/* ===== Content ===== */
.gomoku-content {
  position: relative;
  z-index: 10;
  max-width: 1200px;
  margin: 0 auto;
  padding: 1.5rem 1rem 3rem;
}

/* ===== Header ===== */
.gomoku-header {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  margin-bottom: 1rem;
}

.header-left {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.header-tag {
  font-size: 0.45rem;
  color: #00e5ff;
  letter-spacing: 0.2em;
}

.header-title {
  font-size: 1.5rem;
}

@media (max-width: 640px) {
  .header-title { font-size: 1.1rem; }
}

.title-glow {
  color: #00ff41;
  text-shadow:
    0 0 4px #00ff41,
    0 0 10px rgba(0, 255, 65, 0.4);
}

.header-nav {
  display: flex;
  gap: 0.5rem;
}

/* ===== Status Bar ===== */
.status-bar {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 0.75rem;
  margin-bottom: 1rem;
  border: 1px solid rgba(0, 255, 65, 0.15);
  background: rgba(0, 255, 65, 0.03);
  clip-path: polygon(
    0 4px, 4px 4px, 4px 0,
    calc(100% - 4px) 0, calc(100% - 4px) 4px, 100% 4px,
    100% calc(100% - 4px), calc(100% - 4px) calc(100% - 4px), calc(100% - 4px) 100%,
    4px 100%, 4px calc(100% - 4px), 0 calc(100% - 4px)
  );
}

.status-dot {
  width: 8px;
  height: 8px;
  flex-shrink: 0;
}

.dot-on {
  background: #00ff41;
  box-shadow: 0 0 6px #00ff41;
  animation: dotPulse 1.5s ease-in-out infinite;
}

@keyframes dotPulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.3; }
}

.status-text {
  font-size: 0.5rem;
  color: #00ff41;
  letter-spacing: 0.1em;
}

/* ===== Main Layout ===== */
.main-layout {
  display: grid;
  grid-template-columns: 1fr 300px;
  gap: 1.25rem;
  align-items: start;
}

.layout-full {
  grid-template-columns: 1fr;
  max-width: 800px;
  margin: 0 auto;
}

@media (max-width: 1024px) {
  .main-layout {
    grid-template-columns: 1fr;
  }
}

/* ===== Board Area (with overlay support) ===== */
.board-area {
  position: relative;
}

.board-wrapper {
  border: 2px solid rgba(0, 255, 65, 0.15);
  padding: 0.75rem;
  background: rgba(0, 0, 0, 0.3);
  clip-path: polygon(
    0 8px, 8px 8px, 8px 0,
    calc(100% - 8px) 0, calc(100% - 8px) 8px, 100% 8px,
    100% calc(100% - 8px), calc(100% - 8px) calc(100% - 8px), calc(100% - 8px) 100%,
    8px 100%, 8px calc(100% - 8px), 0 calc(100% - 8px)
  );
}

.gomoku-board {
  width: 100%;
  max-width: 100%;
  aspect-ratio: 1 / 1;
  margin: 0 auto;
  display: grid;
  grid-template-columns: repeat(15, minmax(0, 1fr));
  grid-template-rows: repeat(15, minmax(0, 1fr));
  border: 2px solid rgba(0, 0, 0, 0.45);
  border-radius: 4px;
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

/* ===== Board Overlay ===== */
.board-overlay {
  position: absolute;
  inset: 0;
  background: rgba(0, 0, 0, 0.82);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 20;
  backdrop-filter: blur(2px);
}

.overlay-content {
  text-align: center;
  padding: 2rem;
  max-width: 380px;
  width: 100%;
}

.overlay-title {
  display: inline-flex;
  align-items: center;
  gap: 0.3em;
  margin-bottom: 0.6rem;
}

.ov-text {
  font-size: 1.4rem;
  color: #00ff41;
  text-shadow:
    0 0 6px #00ff41,
    0 0 16px rgba(0, 255, 65, 0.5),
    0 0 40px rgba(0, 255, 65, 0.2);
  animation: neonPulse 2.5s ease-in-out infinite;
}

@media (max-width: 480px) {
  .ov-text { font-size: 1rem; }
}

@keyframes neonPulse {
  0%, 100% {
    text-shadow:
      0 0 6px #00ff41,
      0 0 16px rgba(0, 255, 65, 0.5),
      0 0 40px rgba(0, 255, 65, 0.2);
  }
  50% {
    text-shadow:
      0 0 8px #00ff41,
      0 0 24px rgba(0, 255, 65, 0.7),
      0 0 60px rgba(0, 255, 65, 0.35);
  }
}

.ov-cursor {
  display: inline-block;
  width: 0.5em;
  height: 1em;
  background: #00ff41;
  opacity: 0;
  transition: opacity 0.05s;
}

.cursor-on {
  opacity: 1;
}

.overlay-sub {
  font-size: 0.45rem;
  color: #666;
  margin-bottom: 1.5rem;
  letter-spacing: 0.1em;
  font-family: 'Noto Sans SC', 'Press Start 2P', sans-serif;
}

.overlay-form {
  text-align: left;
}

.overlay-hint {
  font-size: 0.35rem;
  color: #444;
  text-align: center;
  margin-top: 0.25rem;
  font-family: 'Noto Sans SC', 'Press Start 2P', sans-serif;
}

/* Overlay transition */
.overlay-fade-enter-active,
.overlay-fade-leave-active {
  transition: opacity 0.4s ease;
}

.overlay-fade-enter-from,
.overlay-fade-leave-to {
  opacity: 0;
}

/* ===== Sidebar ===== */
.sidebar {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

/* ===== Panel ===== */
.panel {
  border: 1px solid rgba(0, 255, 65, 0.12);
  background: rgba(0, 255, 65, 0.02);
  clip-path: polygon(
    0 6px, 6px 6px, 6px 0,
    calc(100% - 6px) 0, calc(100% - 6px) 6px, 100% 6px,
    100% calc(100% - 6px), calc(100% - 6px) calc(100% - 6px), calc(100% - 6px) 100%,
    6px 100%, 6px calc(100% - 6px), 0 calc(100% - 6px)
  );
}

.panel-title {
  font-size: 0.45rem;
  color: #00ff41;
  padding: 0.5rem 0.75rem;
  border-bottom: 1px solid rgba(0, 255, 65, 0.1);
  letter-spacing: 0.1em;
  display: flex;
  align-items: center;
  gap: 0.5em;
}

.panel-badge {
  font-size: 0.35rem;
  color: #00e5ff;
  border: 1px solid rgba(0, 229, 255, 0.3);
  padding: 0.15em 0.4em;
  margin-left: auto;
}

.panel-count {
  font-size: 0.4rem;
  color: #ffc800;
  margin-left: auto;
}

.panel-body {
  padding: 0.5rem 0.75rem;
}

/* ===== Form Fields ===== */
.field-label {
  display: block;
  font-size: 0.4rem;
  color: #888;
  margin-bottom: 0.6rem;
  letter-spacing: 0.1em;
}

.pixel-input {
  display: block;
  width: 100%;
  margin-top: 0.3rem;
  padding: 0.5rem 0.6rem;
  background: rgba(0, 0, 0, 0.5);
  border: 1px solid rgba(0, 255, 65, 0.2);
  color: #ccc;
  font-family: 'Press Start 2P', monospace;
  font-size: 0.45rem;
  outline: none;
  transition: border-color 0.2s;
}

.pixel-input:focus {
  border-color: #00ff41;
  box-shadow: 0 0 8px rgba(0, 255, 65, 0.2);
}

.pixel-input.uppercase {
  text-transform: uppercase;
}

/* ===== Buttons ===== */
.btn-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0.4rem;
  margin-bottom: 0.5rem;
}

.pixel-btn {
  font-family: 'Press Start 2P', monospace;
  font-size: 0.45rem;
  padding: 0.55rem 0.6rem;
  border: 2px solid rgba(0, 255, 65, 0.25);
  background: rgba(0, 255, 65, 0.05);
  color: #00ff41;
  cursor: pointer;
  text-decoration: none;
  text-align: center;
  transition: all 0.15s;
  letter-spacing: 0.05em;
  clip-path: polygon(
    0 3px, 3px 3px, 3px 0,
    calc(100% - 3px) 0, calc(100% - 3px) 3px, 100% 3px,
    100% calc(100% - 3px), calc(100% - 3px) calc(100% - 3px), calc(100% - 3px) 100%,
    3px 100%, 3px calc(100% - 3px), 0 calc(100% - 3px)
  );
}

.pixel-btn:hover {
  background: rgba(0, 255, 65, 0.12);
  border-color: #00ff41;
}

.pixel-btn:active {
  transform: translateY(2px);
}

.pixel-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.pixel-btn-small {
  font-size: 0.38rem;
  padding: 0.4rem 0.5rem;
}

.pixel-btn-primary {
  background: rgba(255, 200, 0, 0.15);
  border-color: rgba(255, 200, 0, 0.4);
  color: #ffc800;
}

.pixel-btn-primary:hover {
  background: rgba(255, 200, 0, 0.25);
  border-color: #ffc800;
}

.pixel-btn-cyan {
  background: rgba(0, 229, 255, 0.1);
  border-color: rgba(0, 229, 255, 0.3);
  color: #00e5ff;
}

.pixel-btn-cyan:hover {
  background: rgba(0, 229, 255, 0.2);
  border-color: #00e5ff;
}

.pixel-btn-green {
  background: rgba(0, 255, 65, 0.1);
  border-color: rgba(0, 255, 65, 0.3);
  color: #00ff41;
}

.pixel-btn-green:hover {
  background: rgba(0, 255, 65, 0.2);
  border-color: #00ff41;
}

.pixel-btn-disabled {
  opacity: 0.35;
  cursor: not-allowed;
}

.mt-2 {
  margin-top: 0.5rem;
}

/* ===== Info List ===== */
.info-list p {
  font-size: 0.42rem;
  line-height: 2.2;
  display: flex;
  align-items: center;
  gap: 0.4em;
}

.info-key {
  color: #555;
}

/* ===== Player turn indicator ===== */
.player-turn {
  color: #00ff41;
}

.turn-arrow {
  color: #00ff41;
  font-size: 0.5rem;
  margin-left: auto;
  animation: arrowBlink 0.8s step-end infinite;
}

@keyframes arrowBlink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0; }
}

/* ===== Stone Indicator ===== */
.stone-indicator {
  display: inline-block;
  width: 10px;
  height: 10px;
  border-radius: 50%;
  flex-shrink: 0;
}

.stone-indicator-b {
  background: radial-gradient(circle at 35% 35%, #555, #111);
  box-shadow: 0 0 3px rgba(0, 0, 0, 0.5);
}

.stone-indicator-w {
  background: radial-gradient(circle at 35% 35%, #fff, #ccc);
  box-shadow: 0 0 3px rgba(255, 255, 255, 0.3);
}

/* ===== Spectator section (inline) ===== */
.spectator-section {
  margin-top: 0.3rem;
  padding-top: 0.3rem;
  border-top: 1px solid rgba(0, 255, 65, 0.08);
}

.spectator-label {
  font-size: 0.35rem;
  color: #555;
  margin-bottom: 0.2rem;
}

.spectator-name {
  font-size: 0.35rem;
  color: #888;
}

/* ===== Messages ===== */
.msg {
  font-size: 0.4rem;
  padding: 0.5rem 0.6rem;
  line-height: 1.8;
  border: 1px solid;
  font-family: 'Noto Sans SC', 'Press Start 2P', sans-serif;
}

.msg-notice {
  border-color: rgba(0, 255, 65, 0.25);
  background: rgba(0, 255, 65, 0.05);
  color: #7dff7d;
}

.msg-error {
  border-color: rgba(255, 80, 80, 0.3);
  background: rgba(255, 0, 0, 0.05);
  color: #ff8888;
}

/* ===== Responsive ===== */
@media (max-width: 480px) {
  .gomoku-content {
    padding: 0.75rem 0.5rem 2rem;
  }

  .board-wrapper {
    padding: 0.4rem;
  }

  .overlay-content {
    padding: 1.25rem;
  }

  .panel-title {
    font-size: 0.38rem;
  }

  .pixel-btn {
    font-size: 0.38rem;
    padding: 0.4rem 0.5rem;
  }

  .info-list p {
    font-size: 0.38rem;
  }
}
</style>
