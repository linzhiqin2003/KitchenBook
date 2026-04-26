<template>
  <article data-qg-surface class="notes">
    <!-- Topic switcher / header -->
    <header class="notes__head">
      <div class="notes__headLeft">
        <span class="qg-pill" data-tint="essay">{{ formattedTopic(currentTopic) }}</span>
        <span v-if="currentCount" class="notes__count" data-mono>{{ currentCount }} POINTS</span>
        <span v-else-if="!loading" class="notes__count notes__count--muted" data-mono>EMPTY</span>
      </div>
      <div class="notes__headRight">
        <button class="qg-btn qg-btn--ghost notes__regen" :disabled="generating" @click="onRegenerate">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">
            <path d="M3 12a9 9 0 1 1 3 6.7"/>
            <path d="M3 21v-6h6"/>
          </svg>
          {{ generating ? '生成中…' : (currentCount ? '重新生成' : '生成笔记') }}
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

    <div v-else-if="!points.length && !generating" class="notes__empty">
      <p class="notes__emptyTitle">这一章还没有笔记</p>
      <p class="notes__emptyBody">点击右上角「生成笔记」让 AI 把课件拆成结构化要点。</p>
    </div>

    <div v-else class="notes__body">
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
  </article>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue';
import { marked } from 'marked';
import { questionApi } from '../api';

const props = defineProps({
  courseId: { type: String, required: true },
  topic: { type: String, default: null }, // null = use first available courseware topic
});

const points = ref([]);
const loading = ref(false);
const generating = ref(false);
const error = ref('');
const currentTopic = ref(props.topic || null);
const allCoursewareTopics = ref([]);

const currentCount = computed(() => points.value.length);

watch(() => [props.courseId, props.topic], () => {
  currentTopic.value = props.topic || null;
  reload();
});

onMounted(reload);

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
</style>
