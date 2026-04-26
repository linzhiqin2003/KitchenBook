<template>
  <article data-qg-surface class="qg-card fill" :class="{ 'is-loading': loading }">
    <header class="fill__header">
      <div class="fill__meta">
        <span class="qg-pill" data-tint="fill">{{ formattedTopic }}</span>
        <span class="qg-pill">填空题</span>
        <span class="qg-diff" :data-level="(question.difficulty || 'medium')">{{ question.difficulty || 'medium' }}</span>
      </div>
      <span class="qg-num fill__index">№ {{ String(questionNumber).padStart(2, '0') }}</span>
    </header>

    <div class="fill__question">
      <template v-for="(part, idx) in questionParts" :key="idx">
        <span v-if="part.type === 'text'" class="fill__text" v-html="renderInline(part.value)"></span><input
          v-else
          type="text"
          v-model="userInputs[part.blankIndex]"
          :disabled="submitted || mode === 'memorize'"
          :placeholder="`#${part.blankIndex + 1}`"
          class="qg-blank fill__input"
          :data-state="blankState(part.blankIndex)"
          @keyup.enter="onEnter"
        />
      </template>
    </div>

    <footer class="fill__footer">
      <template v-if="mode === 'memorize'">
        <button class="qg-btn qg-btn--primary fill__cta" @click="$emit('next')">
          下一题
          <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12h14M13 6l6 6-6 6"/></svg>
        </button>
      </template>
      <template v-else>
        <button
          v-if="!submitted"
          class="qg-btn qg-btn--primary fill__cta"
          :disabled="!canSubmit || grading"
          @click="submit"
        >{{ grading ? '判分中…' : '提交答案' }}</button>
        <button v-else class="qg-btn qg-btn--primary fill__cta" @click="$emit('next')">
          下一题
          <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12h14M13 6l6 6-6 6"/></svg>
        </button>
      </template>
    </footer>

    <transition name="qg-reveal">
      <section
        v-if="showExplanation"
        class="qg-result fill__result"
        :data-tone="resultTone"
      >
        <div class="fill__resultHead">
          <span class="qg-pill" :data-tint="resultPillTint">{{ resultLabel }}</span>
        </div>

        <div class="fill__answers">
          <div v-for="(exp, i) in expectedAnswers" :key="i" class="fill__answerRow">
            <span class="fill__answerSlot" data-mono>#{{ i + 1 }}</span>
            <span class="fill__answerCorrect" data-mono>{{ exp }}</span>
            <span
              v-if="mode === 'answer' && perBlank[i] === false"
              class="fill__answerYours"
              data-mono
            >你的: {{ userInputs[i] || '∅' }}</span>
          </div>
        </div>

        <div class="qg-prose fill__explanation" v-html="renderedExplanation"></div>
      </section>
    </transition>
  </article>
</template>

<script setup>
import { ref, computed, watch } from 'vue';
import { marked } from 'marked';
import { questionApi } from '../api';

const props = defineProps({
  question: { type: Object, required: true },
  questionNumber: { type: Number, default: 1 },
  loading: { type: Boolean, default: false },
  mode: { type: String, default: 'answer' },
});

const emit = defineEmits(['next', 'answered']);

const userInputs = ref([]);
const submitted = ref(false);
const grading = ref(false);
const gradeResult = ref(null);

const questionParts = computed(() => {
  const text = props.question.question_text || '';
  const parts = [];
  const re = /_{4,}/g;
  let lastIndex = 0;
  let blankIndex = 0;
  let m;
  while ((m = re.exec(text)) !== null) {
    if (m.index > lastIndex) parts.push({ type: 'text', value: text.slice(lastIndex, m.index) });
    parts.push({ type: 'blank', blankIndex: blankIndex++ });
    lastIndex = m.index + m[0].length;
  }
  if (lastIndex < text.length) parts.push({ type: 'text', value: text.slice(lastIndex) });
  return parts;
});
const numBlanks = computed(() => questionParts.value.filter(p => p.type === 'blank').length);
const expectedAnswers = computed(() => (props.question.answer || '').split('|||').map(s => s.trim()));

const canSubmit = computed(() =>
  numBlanks.value > 0 && userInputs.value.slice(0, numBlanks.value).every(v => v && v.trim().length > 0)
);
const perBlank = computed(() => gradeResult.value?.per_blank || []);
const isCorrect = computed(() => gradeResult.value?.correct === true);
const allWrong = computed(() => perBlank.value.length > 0 && perBlank.value.every(b => b === false));

const showExplanation = computed(() => props.mode === 'memorize' || submitted.value);

const resultTone = computed(() => {
  if (props.mode === 'memorize') return 'info';
  if (isCorrect.value) return 'success';
  if (allWrong.value) return 'danger';
  return 'warning';
});
const resultPillTint = computed(() => {
  if (props.mode === 'memorize') return 'fill';
  if (isCorrect.value) return 'success';
  if (allWrong.value) return 'danger';
  return 'warning';
});
const resultLabel = computed(() => {
  if (props.mode === 'memorize') return '参考答案';
  if (isCorrect.value) return '全部正确';
  if (allWrong.value) return '需要再练';
  return '部分正确';
});

const renderedExplanation = computed(() => marked.parse(props.question.explanation || ''));

const formattedTopic = computed(() => {
  const t = props.question.topic || 'general';
  const stripped = t.replace(/^[a-z]?\d*[-_]/i, '');
  return stripped.replace(/-/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
});

function renderInline(text) {
  return marked.parseInline(text || '');
}

function blankState(idx) {
  if (props.mode === 'memorize') return null;
  if (!submitted.value) return null;
  return perBlank.value[idx] ? 'correct' : 'wrong';
}

function onEnter() {
  if (canSubmit.value && !submitted.value) submit();
}

async function submit() {
  if (!canSubmit.value || grading.value) return;
  grading.value = true;
  const joined = userInputs.value.slice(0, numBlanks.value).map(s => s.trim()).join('|||');
  try {
    const r = await questionApi.gradeAnswer(props.question.id, joined);
    gradeResult.value = r.data;
  } catch {
    gradeResult.value = localGrade(joined, expectedAnswers.value);
  } finally {
    submitted.value = true;
    grading.value = false;
    emit('answered', { selected: joined, correct: gradeResult.value?.correct === true });
  }
}

function localGrade(joined, expected) {
  const given = joined.split('|||').map(s => s.trim().toLowerCase());
  const exp = expected.map(s => s.trim().toLowerCase());
  while (given.length < exp.length) given.push('');
  const per_blank = exp.map((e, i) => e !== '' && given[i] === e);
  return { correct: per_blank.every(Boolean) && per_blank.length > 0, per_blank, expected };
}

watch(() => props.question?.id, () => {
  userInputs.value = Array(numBlanks.value).fill('');
  submitted.value = false;
  gradeResult.value = null;
}, { immediate: true });

defineExpose({
  reset() {
    userInputs.value = Array(numBlanks.value).fill('');
    submitted.value = false;
    gradeResult.value = null;
  },
});
</script>

<style scoped>
.fill { padding: clamp(28px, 4vw, 40px); }
.fill.is-loading { opacity: 0.5; }

.fill__header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 24px;
}
.fill__meta {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
}
.fill__index {
  font-size: 12px;
  color: var(--qg-text-tertiary);
  letter-spacing: 0.04em;
  flex-shrink: 0;
}

.fill__question {
  font-size: var(--qg-text-md);
  line-height: 2.1;
  color: var(--qg-text-primary);
  letter-spacing: -0.005em;
  margin-bottom: 28px;
  /* Slightly looser leading so the inline inputs sit naturally in text flow */
}
.fill__text :deep(strong) { color: var(--qg-text-primary); font-weight: 600; }
.fill__input {
  margin: 0 4px;
  font-size: 0.95em;
}

.fill__footer {
  padding-top: 20px;
  border-top: 1px solid var(--qg-border-default);
  display: flex;
}
.fill__cta {
  flex: 1;
  padding: 14px 20px;
  font-size: var(--qg-text-base);
}

.fill__result { margin-top: 24px; }
.fill__resultHead { margin-bottom: 16px; }

.fill__answers {
  display: flex;
  flex-direction: column;
  gap: 6px;
  margin-bottom: 16px;
}
.fill__answerRow {
  display: flex;
  align-items: baseline;
  gap: 12px;
  font-size: var(--qg-text-sm);
}
.fill__answerSlot {
  flex-shrink: 0;
  font-size: 11px;
  color: var(--qg-text-tertiary);
  letter-spacing: 0.04em;
  width: 28px;
}
.fill__answerCorrect {
  color: var(--qg-success);
  font-weight: 500;
}
.fill__answerYours {
  margin-left: auto;
  color: var(--qg-text-tertiary);
  text-decoration: line-through;
  font-size: 12px;
}

.fill__explanation {
  font-size: var(--qg-text-base);
  color: var(--qg-text-secondary);
  line-height: 1.7;
  border-top: 1px solid var(--qg-border-default);
  padding-top: 16px;
}

.qg-reveal-enter-active,
.qg-reveal-leave-active {
  transition: opacity var(--qg-dur-slow) var(--qg-ease),
              transform var(--qg-dur-slow) var(--qg-ease);
}
.qg-reveal-enter-from { opacity: 0; transform: translateY(6px); }
.qg-reveal-leave-to { opacity: 0; transform: translateY(-4px); }
</style>
