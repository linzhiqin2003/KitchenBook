<template>
  <article data-qg-surface class="notes">
    <!-- Topic header (read-only — regeneration handled by backend command) -->
    <header class="notes__head">
      <div class="notes__headLeft">
        <span class="qg-pill" data-tint="essay">{{ formattedTopic(currentTopic) }}</span>
        <span v-if="currentCount" class="notes__count" data-mono>{{ currentCount }} POINTS</span>
        <span v-else-if="!loading" class="notes__count notes__count--muted" data-mono>EMPTY</span>
      </div>
      <div v-if="points.length" class="notes__viewToggle" role="tablist" aria-label="视图模式">
        <button
          role="tab"
          :aria-selected="viewMode === 'list'"
          class="notes__viewBtn"
          @click="setViewMode('list')"
        >
          <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">
            <path d="M4 6h16M4 12h16M4 18h16"/>
          </svg>
          <span>列表</span>
        </button>
        <button
          role="tab"
          :aria-selected="viewMode === 'card'"
          class="notes__viewBtn"
          @click="setViewMode('card')"
        >
          <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">
            <rect x="4" y="5" width="16" height="14" rx="2"/>
            <path d="M9 5v14"/>
          </svg>
          <span>卡片</span>
        </button>
      </div>
    </header>

    <!-- Body -->
    <div v-if="loading" class="notes__loading">
      <span class="notes__loadingDot"></span>
      <span data-mono>LOADING…</span>
    </div>

    <div v-else-if="error" class="qg-result notes__error" data-tone="danger">
      <p>{{ error }}</p>
      <button class="qg-btn qg-btn--ghost" @click="reload">重试</button>
    </div>

    <div v-else-if="!points.length" class="notes__empty">
      <p class="notes__emptyTitle">这一章还没有笔记</p>
      <p class="notes__emptyBody">联系管理员从后台生成（`manage.py` batch-generate）。</p>
    </div>

    <div v-else-if="viewMode === 'list'" class="notes__body">
      <ol class="notes__list">
        <li
          v-for="(p, idx) in points"
          :key="p.id"
          class="notes__item"
          :data-importance="p.importance"
        >
          <header class="notes__itemHead">
            <span class="notes__index" data-mono>{{ String(idx + 1).padStart(2, '0') }}</span>
            <h3 class="notes__title">{{ p.title }}</h3>
            <span class="qg-pill notes__importance" :data-tint="p.importance === 'core' ? 'fill' : null">
              {{ p.importance === 'core' ? '核心' : '辅助' }}
            </span>
          </header>

          <p class="notes__definition">{{ p.definition }}</p>

          <ul v-if="p.details && p.details.length" class="notes__details">
            <li v-for="(d, di) in p.details" :key="di" class="notes__detail" v-html="renderInline(d)"></li>
          </ul>

          <footer v-if="p.source_excerpt || p.source_chapter" class="notes__source">
            <span class="notes__sourceLabel" data-mono>
              出处
              <span v-if="p.source_chapter" class="notes__sourceChapter">· {{ p.source_chapter }}</span>
            </span>
            <span v-if="p.source_excerpt" class="notes__sourceExcerpt">「{{ p.source_excerpt }}」</span>
          </footer>
        </li>
      </ol>
    </div>

    <!-- Card / flashcard mode -->
    <div v-else class="notes__cards">
      <div class="notes__deck" ref="deckRef" @touchstart.passive="onTouchStart" @touchend.passive="onTouchEnd">
        <transition :name="`notes-card-${slideDir}`" mode="out-in" @before-leave="lockDeckHeight" @after-enter="releaseDeckHeight">
          <article
            :key="currentPoint.id"
            class="notes__card notes__item"
            :data-importance="currentPoint.importance"
            tabindex="0"
            ref="cardRef"
          >
            <header class="notes__itemHead">
              <span class="notes__index" data-mono>{{ String(cardIndex + 1).padStart(2, '0') }}</span>
              <h3 class="notes__title">{{ currentPoint.title }}</h3>
              <span class="qg-pill notes__importance" :data-tint="currentPoint.importance === 'core' ? 'fill' : null">
                {{ currentPoint.importance === 'core' ? '核心' : '辅助' }}
              </span>
            </header>

            <p class="notes__definition">{{ currentPoint.definition }}</p>

            <ul v-if="currentPoint.details && currentPoint.details.length" class="notes__details">
              <li v-for="(d, di) in currentPoint.details" :key="di" class="notes__detail" v-html="renderInline(d)"></li>
            </ul>

            <footer v-if="currentPoint.source_excerpt || currentPoint.source_chapter" class="notes__source">
              <span class="notes__sourceLabel" data-mono>
                出处
                <span v-if="currentPoint.source_chapter" class="notes__sourceChapter">· {{ currentPoint.source_chapter }}</span>
              </span>
              <span v-if="currentPoint.source_excerpt" class="notes__sourceExcerpt">「{{ currentPoint.source_excerpt }}」</span>
            </footer>
          </article>
        </transition>
      </div>

      <nav class="notes__cardNav" aria-label="卡片导航">
        <button
          class="notes__navBtn"
          :disabled="cardIndex === 0"
          @click="goPrev"
          aria-label="上一张"
        >
          <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M15 6l-6 6 6 6"/></svg>
        </button>

        <div class="notes__progress">
          <span class="notes__progressText" data-mono>
            {{ String(cardIndex + 1).padStart(2, '0') }} / {{ String(points.length).padStart(2, '0') }}
          </span>
          <div class="notes__progressBar" role="progressbar" :aria-valuenow="cardIndex + 1" :aria-valuemin="1" :aria-valuemax="points.length">
            <div class="notes__progressFill" :style="{ width: `${((cardIndex + 1) / points.length) * 100}%` }"></div>
          </div>
        </div>

        <button
          class="notes__navBtn"
          :disabled="cardIndex >= points.length - 1"
          @click="goNext"
          aria-label="下一张"
        >
          <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M9 6l6 6-6 6"/></svg>
        </button>
      </nav>
    </div>
  </article>
</template>

<script setup>
import { ref, computed, watch, onMounted, onBeforeUnmount, nextTick } from 'vue';
import { marked } from 'marked';
import { questionApi } from '../api';

const props = defineProps({
  courseId: { type: String, required: true },
  topic: { type: String, default: null }, // null = use first available courseware topic
});

const VIEW_MODE_KEY = 'notesview_view_mode';

const points = ref([]);
const loading = ref(false);
const error = ref('');
const currentTopic = ref(props.topic || null);
const allCoursewareTopics = ref([]);

const viewMode = ref(localStorage.getItem(VIEW_MODE_KEY) === 'card' ? 'card' : 'list');
const cardIndex = ref(0);
const slideDir = ref('next'); // 'next' | 'prev' — drives transition direction
const cardRef = ref(null);
const deckRef = ref(null);

function lockDeckHeight() {
  if (deckRef.value) {
    deckRef.value.style.height = `${deckRef.value.scrollHeight}px`;
  }
}
function releaseDeckHeight() {
  if (deckRef.value) {
    deckRef.value.style.height = '';
  }
}

const currentCount = computed(() => points.value.length);
const currentPoint = computed(() => points.value[cardIndex.value] || points.value[0]);

watch(() => [props.courseId, props.topic], () => {
  currentTopic.value = props.topic || null;
  cardIndex.value = 0;
  reload();
});

function setViewMode(mode) {
  if (viewMode.value === mode) return;
  viewMode.value = mode;
  localStorage.setItem(VIEW_MODE_KEY, mode);
  if (mode === 'card') {
    cardIndex.value = Math.min(cardIndex.value, Math.max(0, points.value.length - 1));
    nextTick(() => cardRef.value?.focus?.());
  }
}

function goPrev() {
  if (cardIndex.value <= 0) return;
  slideDir.value = 'prev';
  cardIndex.value -= 1;
}

function goNext() {
  if (cardIndex.value >= points.value.length - 1) return;
  slideDir.value = 'next';
  cardIndex.value += 1;
}

function onKey(e) {
  if (viewMode.value !== 'card' || !points.value.length) return;
  // Skip when typing in inputs
  const tag = (e.target?.tagName || '').toLowerCase();
  if (tag === 'input' || tag === 'textarea' || e.target?.isContentEditable) return;
  if (e.key === 'ArrowLeft') { e.preventDefault(); goPrev(); }
  else if (e.key === 'ArrowRight' || e.key === ' ') { e.preventDefault(); goNext(); }
}

let touchStartX = 0;
let touchStartY = 0;
function onTouchStart(e) {
  const t = e.touches?.[0];
  if (!t) return;
  touchStartX = t.clientX;
  touchStartY = t.clientY;
}
function onTouchEnd(e) {
  const t = e.changedTouches?.[0];
  if (!t) return;
  const dx = t.clientX - touchStartX;
  const dy = t.clientY - touchStartY;
  // Treat as swipe only when horizontal motion clearly dominates
  if (Math.abs(dx) < 48 || Math.abs(dx) < Math.abs(dy) * 1.5) return;
  if (dx < 0) goNext(); else goPrev();
}

onMounted(() => {
  reload();
  window.addEventListener('keydown', onKey);
});
onBeforeUnmount(() => {
  window.removeEventListener('keydown', onKey);
});

async function reload() {
  error.value = '';
  loading.value = true;
  try {
    if (!currentTopic.value) {
      // Fall back to the first courseware topic if caller didn't pin one
      const tr = await questionApi.getNotesTopics(props.courseId);
      const topics = tr.data?.topics || [];
      allCoursewareTopics.value = topics;
      currentTopic.value = topics[0]?.topic || null;
      if (!currentTopic.value) {
        points.value = [];
        return;
      }
    }
    const r = await questionApi.getNotes(props.courseId, currentTopic.value);
    const data = r.data?.results || r.data || [];
    points.value = Array.isArray(data) ? data : (data.results || []);
    cardIndex.value = 0;
  } catch (e) {
    error.value = e?.response?.data?.error || e?.message || '加载失败';
  } finally {
    loading.value = false;
  }
}

async function onRegenerate() {
  if (!currentTopic.value || generating.value) return;
  generating.value = true;
  error.value = '';
  try {
    const r = await questionApi.generateNotes(props.courseId, currentTopic.value, true);
    points.value = r.data?.points || [];
  } catch (e) {
    error.value = e?.response?.data?.error || e?.message || '生成失败';
  } finally {
    generating.value = false;
  }
}

function formattedTopic(t) {
  if (!t) return '—';
  return t.replace(/^[a-z]?\d*[-_]/i, '').replace(/-/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
}
function renderInline(text) {
  return marked.parseInline(text || '');
}

defineExpose({ reload, regenerate: onRegenerate });
</script>

<style scoped>
.notes {
  padding: clamp(20px, 3vw, 32px);
}

.notes__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding-bottom: 18px;
  margin-bottom: 24px;
  border-bottom: 1px solid var(--qg-border-default);
  flex-wrap: wrap;
}
.notes__headLeft {
  display: inline-flex;
  align-items: center;
  gap: 12px;
}
.notes__count {
  font-size: 11px;
  letter-spacing: 0.12em;
  color: var(--qg-text-tertiary);
}
.notes__count--muted { color: var(--qg-text-muted); }

.notes__regen {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: var(--qg-text-sm);
  padding: 8px 14px;
}

.notes__loading {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  padding: 60px 0;
  color: var(--qg-text-tertiary);
  font-size: 11px;
  letter-spacing: 0.12em;
}
.notes__loadingDot {
  width: 6px; height: 6px;
  border-radius: 50%;
  background: var(--qg-accent);
  animation: notesPulse 1.4s ease-in-out infinite;
}
@keyframes notesPulse {
  0%, 100% { opacity: 1; transform: scale(1); }
  50% { opacity: 0.4; transform: scale(0.8); }
}

.notes__error {
  display: flex;
  flex-direction: column;
  gap: 12px;
  align-items: flex-start;
}

.notes__empty {
  text-align: center;
  padding: 56px 24px;
  color: var(--qg-text-secondary);
}
.notes__emptyTitle {
  font-family: var(--qg-font-display);
  font-size: var(--qg-text-lg);
  color: var(--qg-text-primary);
  margin: 0 0 8px;
  letter-spacing: -0.01em;
}
.notes__emptyBody {
  font-size: var(--qg-text-sm);
  color: var(--qg-text-tertiary);
  margin: 0;
}

/* List */
.notes__list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 28px;
}
.notes__item {
  position: relative;
  padding: 20px 22px 18px 22px;
  border: 1px solid var(--qg-border-default);
  border-radius: var(--qg-radius-lg);
  background: var(--qg-surface-raised);
  transition: border-color var(--qg-dur-fast) var(--qg-ease);
}
.notes__item:hover {
  border-color: var(--qg-border-strong);
}
.notes__item[data-importance="supporting"] {
  background: var(--qg-surface-base);
}
.notes__item[data-importance="supporting"] .notes__title {
  color: var(--qg-text-secondary);
}

.notes__itemHead {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 10px;
}
.notes__index {
  font-size: 11px;
  color: var(--qg-text-tertiary);
  flex-shrink: 0;
  font-variant-numeric: tabular-nums;
}
.notes__title {
  font-family: var(--qg-font-display);
  font-size: var(--qg-text-lg);
  font-weight: 500;
  letter-spacing: -0.018em;
  color: var(--qg-text-primary);
  margin: 0;
  flex: 1;
  font-variation-settings: 'opsz' 36;
}
.notes__importance { flex-shrink: 0; font-size: 10px; }

.notes__definition {
  font-size: var(--qg-text-base);
  line-height: 1.65;
  color: var(--qg-text-primary);
  margin: 0 0 12px;
  letter-spacing: -0.005em;
  font-weight: 500;
}

.notes__details {
  list-style: none;
  margin: 0 0 14px;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.notes__detail {
  position: relative;
  padding-left: 18px;
  font-size: var(--qg-text-sm);
  line-height: 1.6;
  color: var(--qg-text-secondary);
}
.notes__detail::before {
  content: "";
  position: absolute;
  left: 4px;
  top: 9px;
  width: 4px;
  height: 4px;
  border-radius: 50%;
  background: var(--qg-text-tertiary);
}
.notes__detail :deep(code) {
  font-family: var(--qg-font-mono);
  font-size: 0.875em;
  background: var(--qg-surface-sunken);
  padding: 1px 6px;
  border-radius: 4px;
  border: 1px solid var(--qg-border-default);
}
.notes__detail :deep(strong) { color: var(--qg-text-primary); font-weight: 600; }

.notes__source {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding-top: 12px;
  border-top: 1px dashed var(--qg-border-default);
  margin-top: 4px;
}
.notes__sourceLabel {
  font-size: 10px;
  letter-spacing: 0.14em;
  color: var(--qg-text-tertiary);
}
.notes__sourceChapter {
  margin-left: 2px;
  color: var(--qg-text-secondary);
}
.notes__sourceExcerpt {
  font-size: var(--qg-text-sm);
  line-height: 1.55;
  color: var(--qg-text-tertiary);
  font-style: italic;
}

/* ─── View toggle (列表 / 卡片) ───────────────────────────────────────── */
.notes__viewToggle {
  display: inline-flex;
  gap: 2px;
  padding: 3px;
  background: var(--qg-surface-sunken);
  border: 1px solid var(--qg-border-default);
  border-radius: var(--qg-radius-pill);
}
.notes__viewBtn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 5px 12px;
  background: transparent;
  border: none;
  border-radius: var(--qg-radius-pill);
  font-size: var(--qg-text-xs);
  font-weight: 500;
  letter-spacing: -0.005em;
  color: var(--qg-text-tertiary);
  cursor: pointer;
  transition: background var(--qg-dur-fast) var(--qg-ease),
              color var(--qg-dur-fast) var(--qg-ease);
}
.notes__viewBtn:hover { color: var(--qg-text-primary); }
.notes__viewBtn[aria-selected="true"] {
  background: var(--qg-surface-raised);
  color: var(--qg-text-primary);
  box-shadow: 0 1px 2px rgba(0,0,0,0.06);
}
.notes__viewBtn svg { flex-shrink: 0; }

/* ─── Card mode ───────────────────────────────────────────────────────── */
.notes__cards {
  display: flex;
  flex-direction: column;
  gap: 24px;
  min-height: 360px;
}
.notes__deck {
  position: relative;
  display: flex;
  align-items: stretch;
  min-height: 320px;
  perspective: 1200px;
  user-select: none;
  -webkit-user-select: none;
  touch-action: pan-y;
}
.notes__card {
  width: 100%;
  padding: clamp(22px, 3.5vw, 32px);
}
.notes__card:focus { outline: none; }
.notes__card:focus-visible {
  outline: 2px solid var(--qg-accent);
  outline-offset: 2px;
}
.notes__card .notes__title {
  font-size: clamp(var(--qg-text-lg), 2.4vw, var(--qg-text-xl));
}
.notes__card .notes__definition {
  font-size: clamp(var(--qg-text-base), 1.8vw, var(--qg-text-lg));
  line-height: 1.7;
}

/* Navigation footer */
.notes__cardNav {
  display: flex;
  align-items: center;
  gap: 16px;
}
.notes__navBtn {
  flex-shrink: 0;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 38px;
  height: 38px;
  background: var(--qg-surface-raised);
  border: 1px solid var(--qg-border-default);
  border-radius: 50%;
  color: var(--qg-text-secondary);
  cursor: pointer;
  transition: border-color var(--qg-dur-fast) var(--qg-ease),
              color var(--qg-dur-fast) var(--qg-ease),
              transform var(--qg-dur-fast) var(--qg-ease),
              opacity var(--qg-dur-fast) var(--qg-ease);
}
.notes__navBtn:hover:not(:disabled) {
  color: var(--qg-text-primary);
  border-color: var(--qg-border-strong);
}
.notes__navBtn:active:not(:disabled) { transform: scale(0.94); }
.notes__navBtn:disabled {
  opacity: 0.35;
  cursor: not-allowed;
}

.notes__progress {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.notes__progressText {
  font-size: 11px;
  letter-spacing: 0.14em;
  color: var(--qg-text-tertiary);
  text-align: center;
}
.notes__progressBar {
  position: relative;
  height: 3px;
  background: var(--qg-surface-sunken);
  border-radius: 999px;
  overflow: hidden;
}
.notes__progressFill {
  height: 100%;
  background: var(--qg-accent);
  border-radius: inherit;
  transition: width var(--qg-dur-base) var(--qg-ease);
}

/* ─── Card slide transitions ──────────────────────────────────────────── */
.notes-card-next-enter-active,
.notes-card-prev-enter-active {
  transition: transform var(--qg-dur-base) var(--qg-ease),
              opacity var(--qg-dur-base) var(--qg-ease);
}
.notes-card-next-leave-active,
.notes-card-prev-leave-active {
  transition: transform var(--qg-dur-base) var(--qg-ease),
              opacity var(--qg-dur-base) var(--qg-ease);
  position: absolute;
  inset: 0;
}
.notes-card-next-enter-from {
  opacity: 0;
  transform: translateX(28px);
}
.notes-card-next-leave-to {
  opacity: 0;
  transform: translateX(-28px);
}
.notes-card-prev-enter-from {
  opacity: 0;
  transform: translateX(-28px);
}
.notes-card-prev-leave-to {
  opacity: 0;
  transform: translateX(28px);
}

@media (max-width: 540px) {
  .notes__viewBtn span { display: none; }
  .notes__viewBtn { padding: 6px 10px; }
}
</style>
