<template>
  <article data-qg-surface class="cw">
    <header class="cw__head">
      <span class="qg-pill" data-tint="mcq">{{ formattedTopic(topic) }}</span>
      <span v-if="meta" class="cw__meta" data-mono>
        {{ meta.char_count }} CHARS · {{ meta.line_count }} LINES
      </span>
      <span v-else-if="!loading && !error" class="cw__meta cw__meta--muted" data-mono>EMPTY</span>

      <div v-if="hasAnyView" class="cw__viewSwitch" role="tablist" aria-label="View">
        <button
          v-for="v in availableViews"
          :key="v.id"
          role="tab"
          :aria-selected="currentView === v.id"
          class="cw__viewBtn"
          :data-active="currentView === v.id"
          @click="setView(v.id)"
        >{{ v.label }}</button>
      </div>
    </header>

    <div v-if="loading" class="cw__loading">
      <span class="cw__loadingDot"></span>
      <span data-mono>LOADING…</span>
    </div>

    <div v-else-if="error" class="qg-result cw__error" data-tone="danger">
      <p>{{ error }}</p>
      <button class="qg-btn qg-btn--ghost" @click="reload">重试</button>
    </div>

    <div v-else-if="!content" class="cw__empty">
      <p class="cw__emptyTitle">这一章没有原文</p>
      <p class="cw__emptyBody">课件库里没有 <span data-mono>{{ topic }}</span> 章节的内容。</p>
    </div>

    <div v-else class="qg-prose cw__body" v-html="rendered"></div>
  </article>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue';
import { marked } from 'marked';
import { questionApi } from '../api';

const props = defineProps({
  courseId: { type: String, required: true },
  topic: { type: String, default: null },
});

const content = ref('');
const meta = ref(null);
const loading = ref(false);
const error = ref('');

// View state: 'summary-en', 'summary-zh', 'raw'
const currentView = ref('summary-en');
// Languages available for the current topic. Populated from /summary-index/.
const availableLangs = ref([]);

const VIEW_OPTIONS = [
  { id: 'summary-en', label: '整理 EN', requiresLang: 'en' },
  { id: 'summary-zh', label: '整理 中', requiresLang: 'zh' },
  { id: 'raw', label: '原文', requiresLang: null },
];
const availableViews = computed(() => VIEW_OPTIONS.filter(
  v => !v.requiresLang || availableLangs.value.includes(v.requiresLang)
));
const hasAnyView = computed(() => availableViews.value.length >= 2);

const rendered = computed(() => marked.parse(content.value || ''));

watch(() => [props.courseId, props.topic], async () => {
  await refreshIndex();
  await reload();
});

onMounted(async () => {
  await refreshIndex();
  await reload();
});

async function refreshIndex() {
  if (!props.courseId || !props.topic) {
    availableLangs.value = [];
    return;
  }
  try {
    const r = await questionApi.getCoursewareSummaryIndex(props.courseId);
    const summaries = r.data?.summaries || {};
    availableLangs.value = summaries[props.topic] || [];
  } catch {
    availableLangs.value = [];
  }
  // Pick a sensible default view: prefer EN summary, then ZH, else fall back to raw.
  if (availableLangs.value.includes('en')) currentView.value = 'summary-en';
  else if (availableLangs.value.includes('zh')) currentView.value = 'summary-zh';
  else currentView.value = 'raw';
}

function setView(id) {
  if (id === currentView.value) return;
  currentView.value = id;
  reload();
}

async function reload() {
  if (!props.courseId || !props.topic) return;
  error.value = '';
  loading.value = true;
  content.value = '';
  meta.value = null;
  try {
    let r;
    if (currentView.value === 'summary-en') {
      r = await questionApi.getCoursewareSummary(props.courseId, props.topic, 'en');
    } else if (currentView.value === 'summary-zh') {
      r = await questionApi.getCoursewareSummary(props.courseId, props.topic, 'zh');
    } else {
      r = await questionApi.getCoursewareChapter(props.courseId, props.topic);
    }
    content.value = r.data?.content || '';
    meta.value = {
      char_count: r.data?.char_count || 0,
      line_count: r.data?.line_count || 0,
    };
  } catch (e) {
    error.value = e?.response?.data?.error || e?.message || '加载失败';
  } finally {
    loading.value = false;
  }
}

function formattedTopic(t) {
  if (!t) return '—';
  return t.replace(/^[a-z]?\d*[-_]/i, '').replace(/-/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
}
</script>

<style scoped>
.cw {
  padding: clamp(20px, 3vw, 32px);
}
.cw__head {
  display: flex;
  align-items: center;
  gap: 12px;
  padding-bottom: 18px;
  margin-bottom: 24px;
  border-bottom: 1px solid var(--qg-border-default);
  flex-wrap: wrap;
}
.cw__meta {
  font-size: 11px;
  letter-spacing: 0.12em;
  color: var(--qg-text-tertiary);
}
.cw__meta--muted { color: var(--qg-text-muted); }

.cw__viewSwitch {
  margin-left: auto;
  display: inline-flex;
  gap: 2px;
  padding: 2px;
  background: var(--qg-surface-sunken);
  border: 1px solid var(--qg-border-default);
  border-radius: var(--qg-radius-sm, 6px);
}
.cw__viewBtn {
  appearance: none;
  border: 0;
  background: transparent;
  font: inherit;
  font-size: 11px;
  letter-spacing: 0.06em;
  color: var(--qg-text-tertiary);
  padding: 4px 10px;
  border-radius: 4px;
  cursor: pointer;
  transition: background 120ms ease, color 120ms ease;
}
.cw__viewBtn:hover { color: var(--qg-text-secondary); }
.cw__viewBtn[data-active="true"] {
  background: var(--qg-surface-elevated, var(--qg-surface-default));
  color: var(--qg-text-primary);
  box-shadow: 0 1px 2px rgba(0,0,0,0.06);
}

.cw__loading {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  padding: 60px 0;
  color: var(--qg-text-tertiary);
  font-size: 11px;
  letter-spacing: 0.12em;
}
.cw__loadingDot {
  width: 6px; height: 6px;
  border-radius: 50%;
  background: var(--qg-accent);
  animation: cwPulse 1.4s ease-in-out infinite;
}
@keyframes cwPulse {
  0%, 100% { opacity: 1; transform: scale(1); }
  50% { opacity: 0.4; transform: scale(0.8); }
}

.cw__error {
  display: flex;
  flex-direction: column;
  gap: 12px;
  align-items: flex-start;
}
.cw__empty {
  text-align: center;
  padding: 56px 24px;
  color: var(--qg-text-secondary);
}
.cw__emptyTitle {
  font-family: var(--qg-font-display);
  font-size: var(--qg-text-lg);
  color: var(--qg-text-primary);
  margin: 0 0 8px;
}
.cw__emptyBody {
  font-size: var(--qg-text-sm);
  color: var(--qg-text-tertiary);
  margin: 0;
}

/* Document body — long-form prose, generous line height */
.cw__body {
  font-size: var(--qg-text-md);
  line-height: 1.8;
  color: var(--qg-text-primary);
  max-width: 72ch;
  letter-spacing: -0.005em;
}
.cw__body :deep(h1) {
  font-family: var(--qg-font-display);
  font-size: clamp(1.75rem, 1rem + 1.6vw, 2.25rem);
  font-weight: 500;
  letter-spacing: -0.025em;
  color: var(--qg-text-primary);
  margin: 0 0 24px;
  padding-bottom: 12px;
  border-bottom: 1px solid var(--qg-border-default);
  font-variation-settings: 'opsz' 60;
}
.cw__body :deep(h2) {
  font-family: var(--qg-font-display);
  font-size: 1.375rem;
  font-weight: 500;
  letter-spacing: -0.018em;
  color: var(--qg-text-primary);
  margin: 36px 0 12px;
}
.cw__body :deep(h3) {
  font-family: var(--qg-font-display);
  font-size: 1.125rem;
  font-weight: 500;
  letter-spacing: -0.012em;
  color: var(--qg-text-primary);
  margin: 28px 0 10px;
}
.cw__body :deep(p) {
  margin: 0 0 14px;
  color: var(--qg-text-secondary);
}
.cw__body :deep(strong) { color: var(--qg-text-primary); font-weight: 600; }
.cw__body :deep(em) { color: var(--qg-text-primary); font-style: italic; }
.cw__body :deep(ul),
.cw__body :deep(ol) {
  padding-left: 1.4rem;
  margin: 4px 0 14px;
  color: var(--qg-text-secondary);
}
.cw__body :deep(li) { margin: 4px 0; }
.cw__body :deep(li > ul),
.cw__body :deep(li > ol) { margin: 6px 0 4px; }
.cw__body :deep(code) {
  font-family: var(--qg-font-mono);
  font-size: 0.875em;
  background: var(--qg-surface-sunken);
  border: 1px solid var(--qg-border-default);
  padding: 1px 6px;
  border-radius: 4px;
  color: var(--qg-text-primary);
}
.cw__body :deep(pre) {
  font-family: var(--qg-font-mono);
  background: var(--qg-surface-sunken);
  border: 1px solid var(--qg-border-default);
  border-radius: var(--qg-radius-md);
  padding: 14px 16px;
  margin: 16px 0;
  overflow-x: auto;
  font-size: 0.875rem;
  line-height: 1.6;
}
.cw__body :deep(pre code) { background: transparent; border: none; padding: 0; }
.cw__body :deep(blockquote) {
  margin: 16px 0;
  padding: 4px 14px;
  color: var(--qg-text-secondary);
  border-left: 1px solid var(--qg-border-strong);
  font-style: italic;
}
.cw__body :deep(hr) {
  border: none;
  border-top: 1px solid var(--qg-border-default);
  margin: 32px 0;
}
.cw__body :deep(a) {
  color: var(--qg-accent);
  text-decoration: none;
  border-bottom: 1px solid color-mix(in oklch, var(--qg-accent) 35%, transparent);
}
.cw__body :deep(a:hover) { border-bottom-color: var(--qg-accent); }
.cw__body :deep(table) {
  border-collapse: collapse;
  margin: 16px 0;
  font-size: var(--qg-text-sm);
  width: 100%;
}
.cw__body :deep(th),
.cw__body :deep(td) {
  text-align: left;
  padding: 8px 10px;
  border-bottom: 1px solid var(--qg-border-default);
}
.cw__body :deep(th) { color: var(--qg-text-primary); font-weight: 600; }
</style>
