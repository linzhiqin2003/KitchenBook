<template>
  <component
    :is="cardComponent"
    ref="innerRef"
    :question="question"
    :question-number="questionNumber"
    :loading="loading"
    :mode="mode"
    @next="$emit('next')"
    @answered="$emit('answered', $event)"
  />
</template>

<script setup>
import { computed, ref } from 'vue';
import MCQQuestionCard from './MCQQuestionCard.vue';
import FillQuestionCard from './FillQuestionCard.vue';
import EssayQuestionCard from './EssayQuestionCard.vue';

const props = defineProps({
  question: { type: Object, required: true },
  questionNumber: { type: Number, default: 1 },
  loading: { type: Boolean, default: false },
  mode: { type: String, default: 'answer' }, // 'answer' | 'memorize'
});

defineEmits(['next', 'answered']);

const innerRef = ref(null);

const cardComponent = computed(() => {
  switch (props.question?.question_type) {
    case 'fill': return FillQuestionCard;
    case 'essay': return EssayQuestionCard;
    case 'mcq':
    default: return MCQQuestionCard;
  }
});

defineExpose({
  reset() {
    innerRef.value?.reset?.();
  },
});
</script>
