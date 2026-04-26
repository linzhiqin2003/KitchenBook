<template>
  <article data-qg-surface class="qg-card mcq" :class="{ 'is-loading': loading }">
    <header class="mcq__header">
      <div class="mcq__meta">
        <span class="qg-pill" data-tint="mcq">{{ formattedTopic }}</span>
        <span class="qg-pill">选择题</span>
        <span class="qg-diff" :data-level="(question.difficulty || 'medium')">{{ question.difficulty || 'medium' }}</span>
      </div>
      <span class="qg-num mcq__index">№ {{ String(questionNumber).padStart(2, '0') }}</span>
    </header>

    <div class="mcq__question qg-prose" v-html="renderedQuestion"></div>

    <div class="mcq__options">
      <button
        v-for="(option, index) in question.options"
        :key="index"
        class="qg-option"
        :data-state="optionState(option)"
        :disabled="submitted || mode === 'memorize'"
        @click="selectOption(option)"
      >
        <span class="qg-option__letter">{{ letters[index] }}</span>
        <span class="qg-option__text" v-html="renderOption(option, index)"></span>
      </button>
    </div>

    <footer class="mcq__footer">
      <template v-if="mode === 'memorize'">
        <button class="qg-btn qg-btn--primary mcq__cta" @click="$emit('next')">
          下一题
          <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12h14M13 6l6 6-6 6"/></svg>
        </button>
      </template>
      <template v-else>
        <button
          v-if="!submitted"
          class="qg-btn qg-btn--primary mcq__cta"
          :disabled="!selectedOption"
          @click="submit"
        >提交答案</button>
        <button v-else class="qg-btn qg-btn--primary mcq__cta" @click="$emit('next')">
          下一题
          <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12h14M13 6l6 6-6 6"/></svg>
        </button>
      </template>
    </footer>

    <transition name="qg-reveal">
      <section
        v-if="showExplanation"
        class="qg-result mcq__result"
        :data-tone="resultTone"
      >
        <div class="mcq__resultHead">
          <span class="qg-pill" :data-tint="resultPillTint">{{ resultLabel }}</span>
          <span class="mcq__resultAnswer">
            <span class="mcq__resultAnswerLabel">答案</span>
            <span data-mono>{{ question.answer }}</span>
          </span>
        </div>
        <div class="qg-prose mcq__explanation" v-html="renderedExplanation"></div>

        <footer v-if="question.source_excerpt || question.source_chapter" class="mcq__source">
          <span class="mcq__sourceLabel" data-mono>
            出处<span v-if="question.source_chapter"> · {{ question.source_chapter }}</span>
          </span>
          <span v-if="question.source_excerpt" class="mcq__sourceExcerpt">「{{ question.source_excerpt }}」</span>
        </footer>
      </section>
    </transition>
  </article>
</template>

<script setup>
import { ref, computed, watch } from 'vue';
import { marked } from 'marked';

const props = defineProps({
  question: { type: Object, required: true },
  questionNumber: { type: Number, default: 1 },
  loading: { type: Boolean, default: false },
  mode: { type: String, default: 'answer' },
});

const emit = defineEmits(['next', 'answered']);

const letters = ['A', 'B', 'C', 'D'];
const selectedOption = ref(null);
const submitted = ref(false);

const isCorrect = computed(() => {
  if (!selectedOption.value || !props.question.answer) return false;
  return isAnswer(selectedOption.value);
});

const showExplanation = computed(() => props.mode === 'memorize' || submitted.value);

const resultTone = computed(() => {
  if (props.mode === 'memorize') return 'info';
  return isCorrect.value ? 'success' : 'danger';
});
const resultPillTint = computed(() => {
  if (props.mode === 'memorize') return 'mcq';
  return isCorrect.value ? 'success' : 'danger';
});
const resultLabel = computed(() => {
  if (props.mode === 'memorize') return '参考解析';
  return isCorrect.value ? '回答正确' : '回答错误';
});

const renderedQuestion = computed(() => marked.parse(props.question.question_text || ''));
const renderedExplanation = computed(() => marked.parse(props.question.explanation || ''));

const formattedTopic = computed(() => {
  const t = props.question.topic || 'general';
  // strip leading number prefix e.g. "01-" or letter prefix "A-"
  const stripped = t.replace(/^[a-z]?\d*[-_]/i, '');
  return stripped.replace(/-/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
});

function renderOption(text, index) {
  if (!text) return '';
  if (typeof index === 'number') {
    const expectedLetter = letters[index];
    const re = new RegExp(`^${expectedLetter}\\.\\s*`);
    text = text.replace(re, '');
  }
  // Stricter code detection: only treat as <pre> when there's a strong
  // signal — explicit newlines, paired braces, or a code keyword
  // adjacent to a brace/paren. Plain English with "for" / ";" no longer
  // misfires (was: "purpose for it." → mono <pre>).
  const isCode = (
    text.includes('\n') ||
    (text.includes('{') && text.includes('}')) ||
    /^\s*(SELECT|INSERT|UPDATE|DELETE|grep|awk|sed|cat|ls|cd|sudo|npm|pip|git)\b/i.test(text) ||
    /\b(int|void|char|return|class|def|function)\b\s*[(){=]/.test(text) ||
    /=>\s*[{(]/.test(text)
  );
  if (isCode && !text.trim().startsWith('`')) {
    const escaped = text.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
    return `<pre><code>${escaped}</code></pre>`;
  }
  return marked.parseInline(text);
}

function isAnswer(option) {
  const a = props.question.answer || '';
  return option === a || a.includes(option) || option.includes(a);
}

function optionState(option) {
  if (props.mode === 'memorize') {
    return isAnswer(option) ? 'correct' : 'dim';
  }
  if (!submitted.value) {
    return selectedOption.value === option ? 'selected' : null;
  }
  if (isAnswer(option)) return 'correct';
  if (selectedOption.value === option) return 'wrong';
  return 'dim';
}

function selectOption(option) {
  if (!submitted.value && props.mode === 'answer') {
    selectedOption.value = option;
  }
}

function submit() {
  if (!selectedOption.value) return;
  submitted.value = true;
  emit('answered', { selected: selectedOption.value, correct: isCorrect.value });
}

watch(() => props.question?.id, () => {
  selectedOption.value = null;
  submitted.value = false;
});

defineExpose({
  reset() { selectedOption.value = null; submitted.value = false; },
});
</script>

<style scoped>
.mcq {
  padding: clamp(28px, 4vw, 40px);
}
.mcq.is-loading { opacity: 0.5; }

.mcq__header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 24px;
}
.mcq__meta {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
}
.mcq__index {
  font-size: 12px;
  color: var(--qg-text-tertiary);
  letter-spacing: 0.04em;
  flex-shrink: 0;
}

.mcq__question {
  font-size: var(--qg-text-md);
  line-height: 1.7;
  color: var(--qg-text-primary);
  margin-bottom: 28px;
}

.mcq__options {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-bottom: 28px;
}
.qg-option__text {
  /* Belt + suspenders: any text or pre inside an option must wrap, never overflow */
  min-width: 0;
  overflow-wrap: anywhere;
  word-break: break-word;
}
.qg-option__text :deep(pre) {
  margin: 4px 0 0;
  padding: 0;
  background: transparent;
  border: none;
  font-size: 0.875em;
  white-space: pre-wrap;
  overflow-wrap: anywhere;
  word-break: break-word;
  max-width: 100%;
}
.qg-option__text :deep(pre code) {
  background: transparent;
  padding: 0;
  white-space: pre-wrap;
  overflow-wrap: anywhere;
  word-break: break-word;
}
.qg-option__text :deep(code) {
  font-family: var(--qg-font-mono);
  font-size: 0.875em;
  background: color-mix(in oklch, currentColor 6%, transparent);
  padding: 1px 6px;
  border-radius: 4px;
  overflow-wrap: anywhere;
  word-break: break-word;
}

.mcq__footer {
  padding-top: 20px;
  border-top: 1px solid var(--qg-border-default);
  display: flex;
}
.mcq__cta {
  flex: 1;
  padding: 14px 20px;
  font-size: var(--qg-text-base);
}

.mcq__result {
  margin-top: 24px;
}
.mcq__resultHead {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 12px;
}
.mcq__resultAnswer {
  display: inline-flex;
  align-items: baseline;
  gap: 8px;
  font-size: var(--qg-text-sm);
  color: var(--qg-text-secondary);
}
.mcq__resultAnswerLabel {
  font-family: var(--qg-font-mono);
  font-size: 11px;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: var(--qg-text-tertiary);
}
.mcq__explanation {
  font-size: var(--qg-text-base);
  color: var(--qg-text-secondary);
  line-height: 1.7;
}
.mcq__explanation :deep(strong) { color: var(--qg-text-primary); }

.mcq__source {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding-top: 12px;
  margin-top: 14px;
  border-top: 1px dashed var(--qg-border-default);
}
.mcq__sourceLabel {
  font-size: 10px;
  letter-spacing: 0.14em;
  color: var(--qg-text-tertiary);
}
.mcq__sourceExcerpt {
  font-size: var(--qg-text-sm);
  line-height: 1.55;
  color: var(--qg-text-tertiary);
  font-style: italic;
}

/* Reveal transition for the explanation */
.qg-reveal-enter-active,
.qg-reveal-leave-active {
  transition: opacity var(--qg-dur-slow) var(--qg-ease),
              transform var(--qg-dur-slow) var(--qg-ease);
  overflow: hidden;
}
.qg-reveal-enter-from {
  opacity: 0;
  transform: translateY(6px);
}
.qg-reveal-leave-to {
  opacity: 0;
  transform: translateY(-4px);
}
</style>
