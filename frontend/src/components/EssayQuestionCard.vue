<template>
  <article data-qg-surface class="qg-card essay" :class="{ 'is-loading': loading }">
    <header class="essay__header">
      <div class="essay__meta">
        <span class="qg-pill" data-tint="essay">{{ formattedTopic }}</span>
        <span class="qg-pill">论述题</span>
        <span class="qg-diff" :data-level="(question.difficulty || 'medium')">{{ question.difficulty || 'medium' }}</span>
      </div>
      <span class="qg-num essay__index">№ {{ String(questionNumber).padStart(2, '0') }}</span>
    </header>

    <div class="essay__prompt qg-prose" v-html="renderedQuestion"></div>

    <!-- Memorize: reveal model answer + rubric directly -->
    <template v-if="mode === 'memorize'">
      <section class="qg-result essay__reveal" data-tone="info">
        <div class="essay__revealHead">
          <span class="qg-pill" data-tint="essay">参考答案</span>
        </div>
        <div class="qg-prose essay__model" v-html="renderedAnswer"></div>
      </section>

      <section class="essay__rubric">
        <header class="essay__rubricHead">
          <span class="qg-pill">评分要点</span>
          <span class="qg-num essay__rubricMax">满分 10</span>
        </header>
        <div class="qg-prose essay__rubricBody" v-html="renderedRubric"></div>
        <div v-if="question.source_excerpt || question.source_chapter" class="essay__source">
          <span class="essay__sourceLabel" data-mono>
            出处<span v-if="question.source_chapter"> · {{ question.source_chapter }}</span>
          </span>
          <span v-if="question.source_excerpt" class="essay__sourceExcerpt">「{{ question.source_excerpt }}」</span>
        </div>
      </section>

      <footer class="essay__footer">
        <button class="qg-btn qg-btn--primary essay__cta" @click="$emit('next')">
          下一题
          <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12h14M13 6l6 6-6 6"/></svg>
        </button>
      </footer>
    </template>

    <!-- Answer mode -->
    <template v-else>
      <div class="essay__compose">
        <textarea
          v-model="studentAnswer"
          :disabled="submitted || grading"
          rows="9"
          class="qg-textarea essay__textarea"
          placeholder="在此作答（建议 200–500 字，论据清晰，结构完整）…"
        ></textarea>
        <div class="essay__counter" data-mono>{{ studentAnswer.length }} / 500</div>
      </div>

      <footer class="essay__footer">
        <button
          v-if="!submitted"
          class="qg-btn qg-btn--primary essay__cta"
          :disabled="!canSubmit || grading"
          @click="submit"
        >{{ grading ? 'AI 评分中…' : '提交评分' }}</button>
        <button v-else class="qg-btn qg-btn--primary essay__cta" @click="$emit('next')">
          下一题
          <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12h14M13 6l6 6-6 6"/></svg>
        </button>
      </footer>

      <transition name="qg-reveal">
        <section v-if="submitted && gradeResult" class="essay__feedback">
          <!-- Score banner — large numeric, editorial -->
          <div class="essay__score" :data-tone="scoreTone">
            <div class="essay__scoreNumeric">
              <span class="qg-num essay__scoreValue">{{ gradeResult.score }}</span>
              <span class="essay__scoreMax">/ {{ gradeResult.max_score || 10 }}</span>
            </div>
            <div class="essay__scoreCopy">
              <div class="essay__scoreLabel">{{ scoreLabel }}</div>
              <p class="essay__scoreFeedback">{{ gradeResult.feedback }}</p>
            </div>
          </div>

          <!-- Matched / Missing — symmetric two-column at md+ -->
          <div class="essay__points">
            <div class="essay__pointGroup" data-kind="matched">
              <header class="essay__pointHead">
                <span class="essay__pointBullet">✓</span>
                <span class="essay__pointTitle">已得分要点</span>
                <span class="qg-num essay__pointCount">{{ (gradeResult.matched_points || []).length }}</span>
              </header>
              <ul class="essay__pointList">
                <li v-for="(pt, i) in gradeResult.matched_points || []" :key="i">{{ pt }}</li>
                <li v-if="!(gradeResult.matched_points || []).length" class="essay__pointEmpty">无</li>
              </ul>
            </div>

            <div class="essay__pointGroup" data-kind="missing">
              <header class="essay__pointHead">
                <span class="essay__pointBullet">−</span>
                <span class="essay__pointTitle">未覆盖要点</span>
                <span class="qg-num essay__pointCount">{{ (gradeResult.missing_points || []).length }}</span>
              </header>
              <ul class="essay__pointList">
                <li v-for="(pt, i) in gradeResult.missing_points || []" :key="i">{{ pt }}</li>
                <li v-if="!(gradeResult.missing_points || []).length" class="essay__pointEmpty">全部覆盖</li>
              </ul>
            </div>
          </div>

          <!-- Reference (collapsed) -->
          <details class="essay__reference">
            <summary>
              <span>查看参考答案 & 评分标准</span>
              <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M6 9l6 6 6-6"/></svg>
            </summary>
            <div class="qg-prose essay__referenceBody" v-html="renderedAnswer"></div>
            <hr class="essay__referenceDivider" />
            <div class="qg-prose essay__referenceBody" v-html="renderedRubric"></div>
            <div v-if="question.source_excerpt || question.source_chapter" class="essay__source">
              <span class="essay__sourceLabel" data-mono>
                出处<span v-if="question.source_chapter"> · {{ question.source_chapter }}</span>
              </span>
              <span v-if="question.source_excerpt" class="essay__sourceExcerpt">「{{ question.source_excerpt }}」</span>
            </div>
          </details>
        </section>
      </transition>
    </template>
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

const studentAnswer = ref('');
const submitted = ref(false);
const grading = ref(false);
const gradeResult = ref(null);

const canSubmit = computed(() => studentAnswer.value.trim().length >= 30);

const renderedQuestion = computed(() => marked.parse(props.question.question_text || ''));
const renderedAnswer = computed(() => marked.parse(props.question.answer || ''));
const renderedRubric = computed(() => marked.parse(props.question.explanation || ''));

const formattedTopic = computed(() => {
  const t = props.question.topic || 'general';
  const stripped = t.replace(/^[a-z]?\d*[-_]/i, '');
  return stripped.replace(/-/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
});

const scoreTone = computed(() => {
  const s = gradeResult.value?.score ?? 0;
  if (s >= 7) return 'success';
  if (s >= 5) return 'warning';
  return 'danger';
});
const scoreLabel = computed(() => {
  const s = gradeResult.value?.score ?? 0;
  if (s >= 9) return 'Outstanding';
  if (s >= 7) return 'Strong response';
  if (s >= 5) return 'Passing — room to grow';
  return 'Needs more work';
});

async function submit() {
  if (!canSubmit.value || grading.value) return;
  grading.value = true;
  try {
    const r = await questionApi.gradeAnswer(props.question.id, studentAnswer.value);
    gradeResult.value = r.data;
    submitted.value = true;
    emit('answered', { selected: studentAnswer.value, correct: (gradeResult.value?.score ?? 0) >= 7 });
  } catch {
    gradeResult.value = { score: 0, max_score: 10, matched_points: [], missing_points: [], feedback: '评分服务暂时不可用，请稍后重试。' };
    submitted.value = true;
  } finally {
    grading.value = false;
  }
}

watch(() => props.question?.id, () => {
  studentAnswer.value = '';
  submitted.value = false;
  gradeResult.value = null;
});

defineExpose({
  reset() { studentAnswer.value = ''; submitted.value = false; gradeResult.value = null; },
});
</script>

<style scoped>
.essay { padding: clamp(28px, 4vw, 40px); }
.essay.is-loading { opacity: 0.5; }

.essay__header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 24px;
}
.essay__meta {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
}
.essay__index {
  font-size: 12px;
  color: var(--qg-text-tertiary);
  letter-spacing: 0.04em;
  flex-shrink: 0;
}

.essay__prompt {
  font-size: var(--qg-text-md);
  line-height: 1.75;
  color: var(--qg-text-primary);
  margin-bottom: 28px;
  /* No max-width — essay prompt should breathe with the card */
  max-width: none;
}

/* Compose textarea */
.essay__compose { position: relative; margin-bottom: 24px; }
.essay__textarea {
  font-family: var(--qg-font-body);
  font-size: var(--qg-text-md);
  line-height: 1.7;
  min-height: 220px;
}
.essay__counter {
  position: absolute;
  right: 12px;
  bottom: 10px;
  font-size: 11px;
  color: var(--qg-text-tertiary);
  letter-spacing: 0.04em;
}

.essay__footer {
  padding-top: 20px;
  border-top: 1px solid var(--qg-border-default);
  display: flex;
}
.essay__cta {
  flex: 1;
  padding: 14px 20px;
  font-size: var(--qg-text-base);
}

/* Memorize-mode reference reveal */
.essay__reveal { margin-top: 0; margin-bottom: 20px; }
.essay__revealHead { margin-bottom: 12px; }
.essay__model {
  font-size: var(--qg-text-base);
  color: var(--qg-text-primary);
  line-height: 1.75;
}

.essay__rubric {
  margin-bottom: 24px;
  padding: 18px 20px;
  border: 1px solid var(--qg-border-default);
  border-radius: var(--qg-radius-md);
  background: var(--qg-surface-sunken);
}
.essay__rubricHead {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}
.essay__rubricMax {
  font-size: 11px;
  color: var(--qg-text-tertiary);
  letter-spacing: 0.04em;
}
.essay__rubricBody {
  font-size: var(--qg-text-sm);
  color: var(--qg-text-secondary);
  line-height: 1.65;
  max-width: none;
}

.essay__source {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding-top: 12px;
  margin-top: 14px;
  border-top: 1px dashed var(--qg-border-default);
}
.essay__sourceLabel {
  font-size: 10px;
  letter-spacing: 0.14em;
  color: var(--qg-text-tertiary);
}
.essay__sourceExcerpt {
  font-size: var(--qg-text-sm);
  line-height: 1.55;
  color: var(--qg-text-tertiary);
  font-style: italic;
}

/* Score feedback after submit */
.essay__feedback {
  margin-top: 28px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.essay__score {
  display: flex;
  gap: 24px;
  align-items: center;
  padding: 24px;
  border: 1px solid var(--qg-border-default);
  border-radius: var(--qg-radius-lg);
  background: var(--qg-surface-sunken);
}
.essay__score[data-tone="success"] {
  background: var(--qg-success-soft);
  border-color: color-mix(in oklch, var(--qg-success) 30%, transparent);
}
.essay__score[data-tone="warning"] {
  background: var(--qg-warning-soft);
  border-color: color-mix(in oklch, var(--qg-warning) 30%, transparent);
}
.essay__score[data-tone="danger"] {
  background: var(--qg-danger-soft);
  border-color: color-mix(in oklch, var(--qg-danger) 30%, transparent);
}
.essay__scoreNumeric {
  display: flex;
  align-items: baseline;
  gap: 4px;
  flex-shrink: 0;
}
.essay__scoreValue {
  font-family: var(--qg-font-display);
  font-size: clamp(2.75rem, 1.5rem + 4vw, 4rem);
  font-weight: 400;
  line-height: 1;
  letter-spacing: -0.04em;
  font-variation-settings: 'opsz' 96;
  color: var(--qg-text-primary);
}
.essay__scoreMax {
  font-family: var(--qg-font-mono);
  font-size: var(--qg-text-md);
  color: var(--qg-text-tertiary);
  letter-spacing: 0.02em;
}
.essay__scoreCopy { min-width: 0; }
.essay__scoreLabel {
  font-family: var(--qg-font-display);
  font-size: var(--qg-text-lg);
  color: var(--qg-text-primary);
  letter-spacing: -0.015em;
  margin-bottom: 4px;
}
.essay__scoreFeedback {
  font-size: var(--qg-text-sm);
  line-height: 1.6;
  color: var(--qg-text-secondary);
  margin: 0;
}

.essay__points {
  display: grid;
  grid-template-columns: 1fr;
  gap: 12px;
}
@container (min-width: 520px) { .essay__points { grid-template-columns: 1fr 1fr; } }
@media (min-width: 720px) { .essay__points { grid-template-columns: 1fr 1fr; } }

.essay__pointGroup {
  border: 1px solid var(--qg-border-default);
  border-radius: var(--qg-radius-md);
  background: var(--qg-surface-sunken);
  padding: 14px 16px;
}
.essay__pointHead {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 10px;
}
.essay__pointBullet {
  width: 18px;
  height: 18px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-family: var(--qg-font-mono);
  font-size: 12px;
  border-radius: 50%;
  flex-shrink: 0;
}
.essay__pointGroup[data-kind="matched"] .essay__pointBullet {
  background: color-mix(in oklch, var(--qg-success) 18%, transparent);
  color: var(--qg-success);
}
.essay__pointGroup[data-kind="missing"] .essay__pointBullet {
  background: color-mix(in oklch, var(--qg-danger) 18%, transparent);
  color: var(--qg-danger);
}
.essay__pointTitle {
  font-size: var(--qg-text-sm);
  font-weight: 500;
  color: var(--qg-text-primary);
  letter-spacing: -0.005em;
  flex: 1;
}
.essay__pointCount {
  font-size: 11px;
  color: var(--qg-text-tertiary);
  letter-spacing: 0.04em;
}

.essay__pointList {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.essay__pointList li {
  font-size: var(--qg-text-sm);
  line-height: 1.55;
  color: var(--qg-text-secondary);
  padding-left: 16px;
  position: relative;
}
.essay__pointList li::before {
  content: "·";
  position: absolute;
  left: 4px;
  color: var(--qg-text-tertiary);
}
.essay__pointEmpty {
  color: var(--qg-text-tertiary);
  font-style: italic;
}

.essay__reference {
  margin-top: 4px;
  border: 1px solid var(--qg-border-default);
  border-radius: var(--qg-radius-md);
  background: var(--qg-surface-sunken);
  padding: 14px 18px;
}
.essay__reference summary {
  display: flex;
  align-items: center;
  justify-content: space-between;
  cursor: pointer;
  font-size: var(--qg-text-sm);
  font-weight: 500;
  color: var(--qg-text-primary);
  list-style: none;
  user-select: none;
}
.essay__reference summary::-webkit-details-marker { display: none; }
.essay__reference summary svg {
  color: var(--qg-text-tertiary);
  transition: transform var(--qg-dur-base) var(--qg-ease);
}
.essay__reference[open] summary svg { transform: rotate(180deg); }
.essay__referenceBody {
  margin-top: 14px;
  font-size: var(--qg-text-sm);
  color: var(--qg-text-secondary);
  line-height: 1.7;
  max-width: none;
}
.essay__referenceDivider {
  margin: 14px 0;
  border: none;
  border-top: 1px solid var(--qg-border-default);
}

.qg-reveal-enter-active,
.qg-reveal-leave-active {
  transition: opacity var(--qg-dur-slow) var(--qg-ease),
              transform var(--qg-dur-slow) var(--qg-ease);
}
.qg-reveal-enter-from { opacity: 0; transform: translateY(6px); }
.qg-reveal-leave-to { opacity: 0; transform: translateY(-4px); }
</style>
