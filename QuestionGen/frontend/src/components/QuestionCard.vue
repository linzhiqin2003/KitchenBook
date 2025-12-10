<template>
  <div class="ios-card p-6 md:p-8 animate-slide-up" :class="{ 'opacity-50': loading }">
    <!-- Question Header -->
    <div class="flex items-center justify-between mb-6">
      <span class="px-3 py-1 text-xs font-semibold tracking-wide uppercase rounded-full bg-blue-50 text-blue-600">
        {{ question.topic || 'General' }}
      </span>
      <span class="text-sm font-medium text-gray-400 font-mono">
        #{{ questionNumber }}
      </span>
    </div>

    <!-- Question Text (Markdown Rendered) -->
    <div 
      class="prose prose-sm md:prose-base max-w-none mb-8 text-gray-800 leading-relaxed font-sans"
      v-html="renderedQuestion"
    ></div>

    <!-- Options -->
    <div class="space-y-4 mb-8">
      <button
        v-for="(option, index) in question.options"
        :key="index"
        @click="selectOption(option)"
        :disabled="submitted"
        :class="getOptionClass(option)"
        class="option-btn group relative"
      >
        <div class="flex items-start">
           <span 
             class="flex-shrink-0 w-6 h-6 rounded-full border-2 mr-3 flex items-center justify-center text-xs font-bold transition-colors duration-200"
             :class="getOptionIndicatorClass(option)"
           >
             {{ ['A', 'B', 'C', 'D'][index] }}
           </span>
           <span class="text-base font-medium pt-0.5">{{ option }}</span>
        </div>
      </button>
    </div>

    <!-- Submit / Next Actions -->
    <div class="flex gap-4 pt-4 border-t border-gray-100/50">
      <button
        v-if="!submitted"
        @click="submit"
        :disabled="!selectedOption"
        class="btn-primary flex-1 py-3.5 text-lg"
        :class="{ 'opacity-50 cursor-not-allowed': !selectedOption }"
      >
        提交答案
      </button>
      <button
        v-else
        @click="$emit('next')"
        class="btn-primary flex-1 py-3.5 text-lg"
      >
        下一题 →
      </button>
    </div>

    <!-- Explanation (shows after submit) -->
    <transition name="fade">
      <div 
        v-if="submitted" 
        class="mt-8 p-5 rounded-2xl animate-fade-in text-left overflow-hidden relative"
        :class="isCorrect ? 'bg-green-50/50 border border-green-100' : 'bg-red-50/50 border border-red-100'"
      >
        <div class="flex items-center gap-2 mb-3">
          <div class="p-1 rounded-full" :class="isCorrect ? 'bg-green-100 text-green-600' : 'bg-red-100 text-red-600'">
             <svg v-if="isCorrect" class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path></svg>
             <svg v-else class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path></svg>
          </div>
          <span class="font-bold text-base" :class="isCorrect ? 'text-green-700' : 'text-red-700'">
            {{ isCorrect ? '回答正确!' : '回答错误' }}
          </span>
        </div>
        
        <div class="prose prose-sm max-w-none text-gray-600">
           <p class="mb-2"><strong class="text-gray-900">正确答案:</strong> {{ question.answer }}</p>
           <div class="markdown-body" v-html="renderedExplanation"></div>
        </div>
      </div>
    </transition>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue';
import { marked } from 'marked';

const props = defineProps({
  question: {
    type: Object,
    required: true,
  },
  questionNumber: {
    type: Number,
    default: 1,
  },
  loading: {
    type: Boolean,
    default: false,
  },
});

const emit = defineEmits(['next', 'answered']);

const selectedOption = ref(null);
const submitted = ref(false);

const isCorrect = computed(() => {
  if (!selectedOption.value || !props.question.answer) return false;
  return selectedOption.value === props.question.answer || 
         props.question.answer.includes(selectedOption.value) ||
         selectedOption.value.includes(props.question.answer);
});

const renderedQuestion = computed(() => {
  return marked(props.question.question_text || '');
});

const renderedExplanation = computed(() => {
  return marked(props.question.explanation || '');
});

function selectOption(option) {
  if (!submitted.value) {
    selectedOption.value = option;
  }
}

function submit() {
  if (selectedOption.value) {
    submitted.value = true;
    emit('answered', {
      selected: selectedOption.value,
      correct: isCorrect.value,
    });
  }
}

function getOptionClass(option) {
  if (!submitted.value) {
    return selectedOption.value === option 
      ? 'border-blue-500 bg-blue-50/50 shadow-sm' 
      : 'border-transparent hover:bg-white/60 hover:shadow-sm';
  }
  
  const isAnswer = option === props.question.answer || 
                   props.question.answer.includes(option) ||
                   option.includes(props.question.answer);
  
  if (isAnswer) return 'border-green-500 bg-green-50/50 shadow-sm';
  if (selectedOption.value === option && !isAnswer) return 'border-red-500 bg-red-50/50 shadow-sm';
  return 'border-transparent opacity-60';
}

function getOptionIndicatorClass(option) {
    if (!submitted.value) {
        return selectedOption.value === option ? 'border-blue-500 text-blue-600 bg-blue-100' : 'border-gray-300 text-gray-400';
    }
    const isAnswer = option === props.question.answer || 
                     props.question.answer.includes(option) ||
                     option.includes(props.question.answer);
                     
    if (isAnswer) return 'border-green-500 text-green-600 bg-green-100';
    if (selectedOption.value === option && !isAnswer) return 'border-red-500 text-red-600 bg-red-100';
    return 'border-gray-200 text-gray-300';
}

defineExpose({
  reset() {
    selectedOption.value = null;
    submitted.value = false;
  }
});
</script>



