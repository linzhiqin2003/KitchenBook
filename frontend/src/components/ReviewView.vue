<template>
  <article data-qg-surface class="rv">
    <header class="rv__head">
      <div class="rv__headLeft">
        <span class="qg-pill" data-tint="mcq">{{ activeChapterTitle }}</span>
        <span class="rv__count" data-mono>{{ displayQuestions.length }} QUESTIONS</span>
      </div>
      <div class="rv__headRight">
        <button class="rv__filterBtn" :data-active="starredOnly" @click="starredOnly = !starredOnly" title="只看标星">
          <svg viewBox="0 0 24 24" width="14" height="14" :fill="starredOnly ? 'currentColor' : 'none'" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/></svg>
          <span v-if="starredCount" data-mono>{{ starredCount }}</span>
        </button>
        <span class="rv__progress" data-mono>{{ reviewedCount }}/{{ displayQuestions.length }}</span>
      </div>
    </header>

    <div v-if="loading" class="rv__loading">
      <span class="rv__loadingDot"></span>
      <span data-mono>LOADING…</span>
    </div>

    <div v-else-if="error" class="qg-result rv__error" data-tone="danger">
      <p>{{ error }}</p>
      <button class="qg-btn qg-btn--ghost" @click="load">重试</button>
    </div>

    <div v-else-if="!chapters.length" class="rv__empty">
      <p class="rv__emptyTitle">No review data</p>
      <p class="rv__emptyBody">This course doesn't have review questions yet.</p>
    </div>

    <!-- Cards -->
    <div v-else class="rv__body">
      <div class="rv__deck">
        <transition :name="`rv-card-${slideDir}`" mode="out-in">
          <div
            class="rv__card"
            :key="cardIndex"
            :data-flipped="flipped"
            :data-starred="isStarred(currentQ)"
            @click="flipped = !flipped"
          >
            <!-- Star button -->
            <button class="rv__star" :data-on="isStarred(currentQ)" @click.stop="toggleStar(currentQ)" title="标记重要">
              <svg viewBox="0 0 24 24" width="18" height="18" :fill="isStarred(currentQ) ? 'currentColor' : 'none'" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/></svg>
            </button>

            <!-- Front: question -->
            <div v-show="!flipped" class="rv__cardFront">
              <div class="rv__cardMeta">
                <span class="rv__cardNum" data-mono>Q{{ currentQ.id }}</span>
                <span v-if="currentQ.mock" class="qg-pill" data-tint="essay">MOCK {{ currentQ.mock }}</span>
                <span class="rv__cardMarks" data-mono>{{ currentQ.marks }} marks</span>
              </div>
              <p class="rv__cardQuestion">{{ currentQ.question }}</p>
              <div class="rv__cardHint" data-mono>TAP TO REVEAL</div>
            </div>

            <!-- Back: answer -->
            <div v-show="flipped" class="rv__cardBack">
              <div class="rv__cardMeta">
                <span class="rv__cardNum" data-mono>Q{{ currentQ.id }}</span>
                <span class="rv__cardLabel" data-mono>ANSWER</span>
              </div>
              <ul class="rv__cardAnswer">
                <li v-for="(a, i) in currentQ.answer" :key="i">
                  <span>{{ a }}</span>
                  <span v-if="currentQ.answer_cn && currentQ.answer_cn[i]" class="rv__cn">{{ currentQ.answer_cn[i] }}</span>
                </li>
              </ul>
            </div>
          </div>
        </transition>
      </div>

      <!-- Nav -->
      <nav class="rv__nav">
        <button class="rv__navBtn" :disabled="cardIndex === 0" @click="go(-1)">
          <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M15 6l-6 6 6 6"/></svg>
        </button>

        <div class="rv__navCenter">
          <span class="rv__navPos" data-mono>{{ String(cardIndex + 1).padStart(2,'0') }} / {{ String(displayQuestions.length).padStart(2,'0') }}</span>
          <div class="rv__navBar">
            <div class="rv__navFill" :style="{ width: `${((cardIndex + 1) / (displayQuestions.length || 1)) * 100}%` }"></div>
          </div>
        </div>

        <button class="rv__navBtn" :disabled="cardIndex >= displayQuestions.length - 1" @click="go(1)">
          <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M9 6l6 6-6 6"/></svg>
        </button>
      </nav>
    </div>
  </article>
</template>

<script setup>
import { ref, computed, watch, onMounted, onBeforeUnmount } from 'vue';
import { questionApi } from '../api';

const props = defineProps({
  courseId: { type: String, required: true },
  topic: { type: String, default: null },
});

const chapters = ref([]);
const activeChapter = ref(null);
const cardIndex = ref(0);
const flipped = ref(false);
const slideDir = ref('next');
const loading = ref(false);
const error = ref('');
const reviewed = ref(new Set());
const starredOnly = ref(false);

const STARRED_KEY = 'rv_starred';
const starred = ref(new Set(JSON.parse(localStorage.getItem(STARRED_KEY) || '[]')));

function starKey(q) { return `${activeChapter.value}-${q.id}`; }
function isStarred(q) { return starred.value.has(starKey(q)); }
function toggleStar(q) {
  const k = starKey(q);
  const next = new Set(starred.value);
  if (next.has(k)) next.delete(k); else next.add(k);
  starred.value = next;
  localStorage.setItem(STARRED_KEY, JSON.stringify([...next]));
}

const currentQuestions = computed(() => {
  if (!activeChapter.value) return [];
  const ch = chapters.value.find(c => c.id === activeChapter.value);
  return ch ? ch.questions : [];
});

const displayQuestions = computed(() => {
  if (!starredOnly.value) return currentQuestions.value;
  return currentQuestions.value.filter(q => starred.value.has(`${activeChapter.value}-${q.id}`));
});

const currentQ = computed(() => displayQuestions.value[cardIndex.value] || { id: 0, question: '', marks: 0, answer: [] });
const activeChapterTitle = computed(() => {
  const ch = chapters.value.find(c => c.id === activeChapter.value);
  return ch ? ch.title : '—';
});
const starredCount = computed(() => {
  return currentQuestions.value.filter(q => starred.value.has(`${activeChapter.value}-${q.id}`)).length;
});
const reviewedCount = computed(() => {
  let count = 0;
  for (const q of displayQuestions.value) {
    if (reviewed.value.has(`${activeChapter.value}-${q.id}`)) count++;
  }
  return count;
});

function shortTitle(t) {
  return t.replace(/^(Introduction to |Object-Oriented )/, '').replace(/ Software Development$/, '');
}

function setChapter(id) {
  activeChapter.value = id;
  cardIndex.value = 0;
  flipped.value = false;
}

function go(delta) {
  if (flipped.value) {
    reviewed.value.add(`${activeChapter.value}-${currentQ.value.id}`);
  }
  slideDir.value = delta > 0 ? 'next' : 'prev';
  const next = cardIndex.value + delta;
  if (next < 0 || next >= displayQuestions.value.length) return;
  cardIndex.value = next;
  flipped.value = false;
}

// Reset card index when filter changes
watch(starredOnly, () => { cardIndex.value = 0; flipped.value = false; });

function onKey(e) {
  const tag = (e.target?.tagName || '').toLowerCase();
  if (tag === 'input' || tag === 'textarea' || e.target?.isContentEditable) return;
  if (e.key === 'ArrowLeft') { e.preventDefault(); go(-1); }
  else if (e.key === 'ArrowRight') { e.preventDefault(); go(1); }
  else if (e.key === ' ' || e.key === 'Enter') { e.preventDefault(); flipped.value = !flipped.value; }
}

onMounted(() => { load(); window.addEventListener('keydown', onKey); });
onBeforeUnmount(() => { window.removeEventListener('keydown', onKey); });

watch(() => props.courseId, load);

watch(() => props.topic, (t) => {
  if (!t || !chapters.value.length) return;
  const match = chapters.value.find(c => c.id === t || c.id.includes(t) || t.includes(c.id));
  if (match && match.id !== activeChapter.value) {
    setChapter(match.id);
  }
}, { immediate: true });

async function load() {
  loading.value = true;
  error.value = '';
  try {
    const r = await questionApi.getReviewData(props.courseId);
    chapters.value = r.data?.chapters || [];
    if (chapters.value.length) {
      if (props.topic) {
        const match = chapters.value.find(c => c.id === props.topic || c.id.includes(props.topic) || props.topic.includes(c.id));
        activeChapter.value = match ? match.id : chapters.value[0].id;
      } else if (!activeChapter.value) {
        activeChapter.value = chapters.value[0].id;
      }
    }
  } catch (e) {
    error.value = e?.response?.data?.error || e?.message || 'Failed to load';
    chapters.value = [];
  } finally {
    loading.value = false;
  }
}
</script>

<style scoped>
.rv { padding: clamp(16px, 3vw, 28px); }

/* ─── Header / chapter picker ─────────────────────────────────────── */
.rv__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding-bottom: 16px;
  margin-bottom: 20px;
  border-bottom: 1px solid var(--qg-border-default);
  flex-wrap: wrap;
}
.rv__headLeft {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}
.rv__chBtn {
  padding: 5px 12px;
  font-size: var(--qg-text-xs);
  font-weight: 500;
  color: var(--qg-text-tertiary);
  background: var(--qg-surface-sunken);
  border: 1px solid var(--qg-border-default);
  border-radius: var(--qg-radius-pill);
  cursor: pointer;
  transition: all var(--qg-dur-fast) var(--qg-ease);
  white-space: nowrap;
}
.rv__chBtn:hover { color: var(--qg-text-primary); border-color: var(--qg-border-strong); }
.rv__chBtn[data-active="true"] {
  background: var(--qg-accent-soft);
  color: var(--qg-accent);
  border-color: transparent;
}
.rv__count {
  font-size: 11px;
  letter-spacing: 0.12em;
  color: var(--qg-text-tertiary);
}
.rv__headRight {
  display: flex;
  align-items: center;
  gap: 10px;
}
.rv__filterBtn {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 4px 10px;
  background: transparent;
  border: 1px solid var(--qg-border-default);
  border-radius: var(--qg-radius-pill);
  cursor: pointer;
  color: var(--qg-text-muted);
  font-size: 11px;
  transition: all var(--qg-dur-fast) var(--qg-ease);
}
.rv__filterBtn:hover { color: var(--qg-type-fill); border-color: var(--qg-type-fill); }
.rv__filterBtn[data-active="true"] {
  color: var(--qg-type-fill);
  background: var(--qg-type-fill-soft);
  border-color: transparent;
}
.rv__progress {
  font-size: 11px;
  letter-spacing: 0.1em;
  color: var(--qg-text-tertiary);
}

/* ─── Loading / empty ─────────────────────────────────────────────── */
.rv__loading {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  padding: 60px 0;
  color: var(--qg-text-tertiary);
  font-size: 11px;
  letter-spacing: 0.12em;
}
.rv__loadingDot {
  width: 6px; height: 6px;
  border-radius: 50%;
  background: var(--qg-accent);
  animation: rvPulse 1.4s ease-in-out infinite;
}
@keyframes rvPulse {
  0%, 100% { opacity: 1; transform: scale(1); }
  50% { opacity: 0.4; transform: scale(0.8); }
}
.rv__empty {
  text-align: center;
  padding: 56px 24px;
}
.rv__emptyTitle {
  font-family: var(--qg-font-display);
  font-size: var(--qg-text-lg);
  color: var(--qg-text-primary);
  margin: 0 0 8px;
}
.rv__emptyBody {
  font-size: var(--qg-text-sm);
  color: var(--qg-text-tertiary);
  margin: 0;
}

/* ─── Card deck ───────────────────────────────────────────────────── */
.rv__body {
  display: flex;
  flex-direction: column;
  gap: 20px;
}
.rv__deck {
  position: relative;
  min-height: 280px;
  perspective: 1200px;
}

.rv__card {
  position: relative;
  width: 100%;
  cursor: pointer;
  border: 1px solid var(--qg-border-default);
  border-radius: var(--qg-radius-lg);
  background: var(--qg-surface-raised);
  box-shadow: var(--qg-shadow-1);
  transition: border-color var(--qg-dur-fast) var(--qg-ease), box-shadow var(--qg-dur-fast) var(--qg-ease);
  overflow: hidden;
}
.rv__card:hover { border-color: var(--qg-border-strong); }

/* Starred card highlight */
.rv__card[data-starred="true"] {
  border-color: var(--qg-type-fill);
  box-shadow: 0 0 0 1px color-mix(in oklch, var(--qg-type-fill) 25%, transparent), var(--qg-shadow-1);
}
.rv__card[data-starred="true"]::before {
  content: "";
  position: absolute;
  inset: 0;
  border-radius: inherit;
  background: color-mix(in oklch, var(--qg-type-fill) 6%, transparent);
  pointer-events: none;
}

/* Star button */
.rv__star {
  position: absolute;
  top: 12px;
  right: 12px;
  z-index: 2;
  width: 32px; height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  border: none;
  border-radius: 50%;
  cursor: pointer;
  color: var(--qg-text-muted);
  transition: color var(--qg-dur-fast) var(--qg-ease), transform var(--qg-dur-fast) var(--qg-ease);
}
.rv__star:hover { color: var(--qg-type-fill); transform: scale(1.15); }
.rv__star[data-on="true"] { color: var(--qg-type-fill); }

/* Front/Back toggle */
.rv__cardFront,
.rv__cardBack {
  padding: clamp(20px, 3vw, 28px);
}
.rv__card[data-flipped="true"] {
  background: var(--qg-surface-sunken);
  border-color: var(--qg-accent);
}

/* Meta row */
.rv__cardMeta {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 14px;
}
.rv__cardNum {
  font-size: 11px;
  color: var(--qg-text-tertiary);
  letter-spacing: 0.04em;
}
.rv__cardMarks {
  margin-left: auto;
  font-size: 11px;
  color: var(--qg-text-tertiary);
  letter-spacing: 0.04em;
}
.rv__cardLabel {
  font-size: 10px;
  letter-spacing: 0.12em;
  color: var(--qg-accent);
  font-weight: 600;
}

/* Question text */
.rv__cardQuestion {
  font-family: var(--qg-font-display);
  font-size: clamp(var(--qg-text-base), 2vw, var(--qg-text-lg));
  font-weight: 500;
  line-height: 1.6;
  color: var(--qg-text-primary);
  letter-spacing: -0.01em;
  margin: 0 0 20px;
  white-space: pre-line;
}

.rv__cardHint {
  font-size: 10px;
  letter-spacing: 0.14em;
  color: var(--qg-text-muted);
  text-align: center;
  padding-top: 12px;
  border-top: 1px dashed var(--qg-border-default);
}

/* Answer list */
.rv__cardAnswer {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.rv__cardAnswer li {
  position: relative;
  padding-left: 18px;
  font-size: var(--qg-text-sm);
  line-height: 1.65;
  color: var(--qg-text-primary);
}
.rv__cardAnswer li::before {
  content: "";
  position: absolute;
  left: 3px;
  top: 9px;
  width: 5px;
  height: 5px;
  border-radius: 50%;
  background: var(--qg-accent);
  opacity: 0.6;
}
.rv__cn {
  display: block;
  margin-top: 3px;
  font-size: var(--qg-text-xs);
  line-height: 1.5;
  color: var(--qg-text-tertiary);
  font-style: italic;
}

/* ─── Navigation ──────────────────────────────────────────────────── */
.rv__nav {
  display: flex;
  align-items: center;
  gap: 16px;
}
.rv__navBtn {
  flex-shrink: 0;
  width: 38px; height: 38px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: var(--qg-surface-raised);
  border: 1px solid var(--qg-border-default);
  border-radius: 50%;
  color: var(--qg-text-secondary);
  cursor: pointer;
  transition: all var(--qg-dur-fast) var(--qg-ease);
}
.rv__navBtn:hover:not(:disabled) { color: var(--qg-text-primary); border-color: var(--qg-border-strong); }
.rv__navBtn:disabled { opacity: 0.35; cursor: not-allowed; }
.rv__navCenter { flex: 1; display: flex; flex-direction: column; gap: 6px; }
.rv__navPos {
  font-size: 11px;
  letter-spacing: 0.14em;
  color: var(--qg-text-tertiary);
  text-align: center;
}
.rv__navBar {
  height: 3px;
  background: var(--qg-surface-sunken);
  border-radius: 999px;
  overflow: hidden;
}
.rv__navFill {
  height: 100%;
  background: var(--qg-accent);
  border-radius: inherit;
  transition: width var(--qg-dur-base) var(--qg-ease);
}

/* ─── Slide transitions ───────────────────────────────────────────── */
.rv-card-next-enter-active, .rv-card-prev-enter-active,
.rv-card-next-leave-active, .rv-card-prev-leave-active {
  transition: transform var(--qg-dur-base) var(--qg-ease), opacity var(--qg-dur-base) var(--qg-ease);
}
.rv-card-next-leave-active, .rv-card-prev-leave-active {
  position: absolute; inset: 0;
}
.rv-card-next-enter-from { opacity: 0; transform: translateX(28px); }
.rv-card-next-leave-to { opacity: 0; transform: translateX(-28px); }
.rv-card-prev-enter-from { opacity: 0; transform: translateX(-28px); }
.rv-card-prev-leave-to { opacity: 0; transform: translateX(28px); }

@media (max-width: 540px) {
  .rv__chBtn { font-size: 10px; padding: 4px 8px; }
}
</style>
