<template>
  <div class="min-h-screen bg-[#F2F2F7] pb-8">
    <!-- Header -->
    <header class="sticky top-0 z-10 bg-white/80 backdrop-blur-xl border-b border-gray-200/50">
      <div class="max-w-2xl mx-auto px-4 py-4">
        <div class="flex items-center justify-between">
          <h1 class="text-xl font-bold text-gray-900">Software Tools 刷题</h1>
          <div class="flex items-center gap-3">
            <span class="text-sm text-gray-500">
              {{ correctCount }} / {{ historyQuestions.length }} 正确
            </span>
            <button
              @click="showHistory = !showHistory"
              class="px-3 py-2 text-sm font-medium text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
            >
              📋 历史
            </button>
          </div>
        </div>
      </div>
    </header>

    <!-- Main Content -->
    <main class="max-w-2xl mx-auto px-4 pt-6">
      <!-- Loading State (Initial or Generating) -->
      <div v-if="loading" class="flex flex-col items-center justify-center py-20">
        <div class="w-12 h-12 border-4 border-blue-200 border-t-blue-600 rounded-full animate-spin"></div>
        <p class="mt-4 text-gray-500">{{ loadingMessage }}</p>
      </div>

      <!-- Current Question Card -->
      <div v-else-if="currentQuestion">
        <QuestionCard
          ref="cardRef"
          :key="currentQuestion.id"
          :question="currentQuestion"
          :question-number="historyQuestions.length + 1"
          @next="moveToNextQuestion"
          @answered="onAnswered"
        />
        
        <!-- Prefetch Indicator -->
        <div v-if="prefetching" class="mt-4 text-center text-sm text-gray-400">
          <span class="inline-flex items-center gap-2">
            <span class="w-2 h-2 bg-green-400 rounded-full animate-pulse"></span>
            正在预生成下一题...
          </span>
        </div>
      </div>

      <!-- Empty State (Shouldn't normally show) -->
      <div v-else class="ios-card p-8 text-center">
        <div class="text-6xl mb-4">📚</div>
        <h2 class="text-xl font-semibold text-gray-900 mb-2">准备开始</h2>
        <p class="text-gray-500 mb-6">正在加载第一道题目...</p>
      </div>
    </main>

    <!-- History Sidebar -->
    <transition name="slide">
      <div v-if="showHistory" class="fixed inset-0 z-50 flex justify-end">
        <div class="absolute inset-0 bg-black/30" @click="showHistory = false"></div>
        <div class="relative w-full max-w-md bg-white shadow-2xl overflow-hidden flex flex-col">
          <div class="p-4 border-b border-gray-100 flex items-center justify-between">
            <h2 class="text-lg font-bold">答题历史</h2>
            <button @click="showHistory = false" class="p-2 hover:bg-gray-100 rounded-full">
              ✕
            </button>
          </div>
          <div class="flex-1 overflow-y-auto p-4 space-y-3">
            <div 
              v-for="(item, index) in historyQuestions" 
              :key="item.id"
              class="p-4 rounded-xl border cursor-pointer transition-all hover:shadow-md"
              :class="item.correct ? 'border-green-200 bg-green-50/50' : 'border-red-200 bg-red-50/50'"
              @click="viewHistoryItem(item)"
            >
              <div class="flex items-center justify-between mb-2">
                <span class="text-xs font-medium px-2 py-0.5 rounded-full"
                      :class="item.correct ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'">
                  {{ item.correct ? '✓ 正确' : '✗ 错误' }}
                </span>
                <span class="text-xs text-gray-400">#{{ index + 1 }}</span>
              </div>
              <p class="text-sm text-gray-800 line-clamp-2">{{ item.question.question_text }}</p>
            </div>
            <div v-if="historyQuestions.length === 0" class="text-center text-gray-400 py-8">
              暂无答题记录
            </div>
          </div>
        </div>
      </div>
    </transition>

    <!-- History Detail Modal -->
    <transition name="fade">
      <div v-if="historyDetailItem" class="fixed inset-0 z-60 flex items-center justify-center p-4">
        <div class="absolute inset-0 bg-black/50" @click="historyDetailItem = null"></div>
        <div class="relative max-w-2xl w-full max-h-[80vh] overflow-y-auto bg-white rounded-2xl shadow-2xl p-6">
          <button @click="historyDetailItem = null" class="absolute top-4 right-4 p-2 hover:bg-gray-100 rounded-full">
            ✕
          </button>
          <QuestionCard
            :question="historyDetailItem.question"
            :question-number="historyDetailItem.index + 1"
            :loading="false"
            class="pointer-events-none"
          />
        </div>
      </div>
    </transition>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue';
import QuestionCard from '../components/QuestionCard.vue';
import { questionApi } from '../api';

// State
const currentQuestion = ref(null);
const prefetchedQuestion = ref(null);
const historyQuestions = ref([]);
const loading = ref(true);
const prefetching = ref(false);
const loadingMessage = ref('正在生成第一道题目...');
const showHistory = ref(false);
const historyDetailItem = ref(null);
const cardRef = ref(null);

const correctCount = computed(() => historyQuestions.value.filter(h => h.correct).length);

// Generate a single new question
async function generateSingleQuestion() {
  try {
    const response = await questionApi.generateQuestion();
    return response.data;
  } catch (error) {
    console.error('Failed to generate question:', error);
    return null;
  }
}

// Prefetch next question in background
async function prefetchNextQuestion() {
  if (prefetching.value || prefetchedQuestion.value) return;
  
  prefetching.value = true;
  try {
    prefetchedQuestion.value = await generateSingleQuestion();
  } finally {
    prefetching.value = false;
  }
}

// Called when user submits answer
function onAnswered({ correct }) {
  if (!currentQuestion.value) return;
  
  // Add to history
  historyQuestions.value.push({
    id: currentQuestion.value.id,
    question: currentQuestion.value,
    correct,
    answeredAt: new Date().toISOString()
  });
  
  // Start prefetching if not already
  prefetchNextQuestion();
}

// Move to next question
async function moveToNextQuestion() {
  loading.value = true;
  loadingMessage.value = '正在加载下一题...';
  
  // Use prefetched question if available
  if (prefetchedQuestion.value) {
    currentQuestion.value = prefetchedQuestion.value;
    prefetchedQuestion.value = null;
    loading.value = false;
    // Start prefetching the next one
    prefetchNextQuestion();
  } else {
    // Generate new question (shouldn't happen often if prefetch works)
    currentQuestion.value = await generateSingleQuestion();
    loading.value = false;
    prefetchNextQuestion();
  }
  
  cardRef.value?.reset();
}

// View historical question detail
function viewHistoryItem(item) {
  historyDetailItem.value = {
    ...item,
    index: historyQuestions.value.indexOf(item)
  };
}

// Initial load
onMounted(async () => {
  loading.value = true;
  loadingMessage.value = '正在生成第一道题目...';
  
  // Generate first question
  currentQuestion.value = await generateSingleQuestion();
  loading.value = false;
  
  // Start prefetching second question
  prefetchNextQuestion();
});
</script>

<style scoped>
.slide-enter-active,
.slide-leave-active {
  transition: transform 0.3s ease;
}
.slide-enter-from,
.slide-leave-to {
  transform: translateX(100%);
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

.line-clamp-2 {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
</style>
