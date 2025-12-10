<template>
  <div class="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50">
    <!-- Header -->
    <header class="sticky top-0 z-10 bg-white/80 backdrop-blur-xl border-b border-gray-200/50 shadow-sm">
      <div class="max-w-2xl mx-auto px-4 py-4">
        <div class="flex items-center justify-between">
          <div class="flex items-center gap-3">
            <router-link to="/" class="p-2 hover:bg-gray-100 rounded-lg transition-colors" title="返回首页">
              <svg class="w-5 h-5 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 19l-7-7m0 0l7-7m-7 7h18"/>
              </svg>
            </router-link>
            <h1 class="text-xl font-bold text-gray-900">📚 Software Tools 刷题</h1>
          </div>
          <div class="flex items-center gap-3">
            <span class="text-sm text-gray-500 bg-gray-100 px-3 py-1 rounded-full">
              {{ correctCount }} / {{ historyQuestions.length }} 正确
            </span>
            <button
              @click="showHistory = !showHistory"
              class="px-3 py-2 text-sm font-medium text-gray-600 hover:bg-gray-100 rounded-lg transition-colors cursor-pointer"
            >
              📋 历史
            </button>
            <button
              v-if="historyQuestions.length > 0"
              @click="clearHistory"
              class="px-3 py-2 text-sm font-medium text-red-500 hover:bg-red-50 rounded-lg transition-colors cursor-pointer"
              title="清空历史"
            >
              🗑️
            </button>
          </div>
        </div>
      </div>
    </header>

    <!-- Main Content -->
    <main class="max-w-2xl mx-auto px-4 pt-6 pb-12">
      <!-- Loading State (Initial or Generating) -->
      <div v-if="loading" class="flex flex-col items-center justify-center py-20">
        <div class="w-12 h-12 border-4 border-blue-200 border-t-blue-600 rounded-full animate-spin"></div>
        <p class="mt-4 text-gray-500">{{ loadingMessage }}</p>
      </div>

      <!-- Error State -->
      <div v-else-if="error" class="bg-white rounded-2xl shadow-lg p-8 text-center">
        <div class="text-6xl mb-4">⚠️</div>
        <h2 class="text-xl font-semibold text-gray-900 mb-2">出错了</h2>
        <p class="text-gray-500 mb-6">{{ error }}</p>
        <button 
          @click="retryGenerate" 
          class="px-6 py-3 bg-blue-600 text-white rounded-xl font-semibold hover:bg-blue-700 transition-colors cursor-pointer"
        >
          重试
        </button>
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
      <div v-else class="bg-white rounded-2xl shadow-lg p-8 text-center">
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
          <div class="p-4 border-b border-gray-100 flex items-center justify-between bg-gradient-to-r from-blue-50 to-indigo-50">
            <h2 class="text-lg font-bold text-gray-800">📋 答题历史</h2>
            <button @click="showHistory = false" class="p-2 hover:bg-white/50 rounded-full cursor-pointer transition-colors">
              ✕
            </button>
          </div>
          <div class="flex-1 overflow-y-auto p-4 space-y-3">
            <div 
              v-for="(item, index) in [...historyQuestions].reverse()" 
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
                <span class="text-xs text-gray-400">#{{ historyQuestions.length - index }}</span>
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
      <div v-if="historyDetailItem" class="fixed inset-0 z-[60] flex items-center justify-center p-4">
        <div class="absolute inset-0 bg-black/50" @click="historyDetailItem = null"></div>
        <div class="relative max-w-2xl w-full max-h-[80vh] overflow-y-auto bg-white rounded-2xl shadow-2xl p-6">
          <button @click="historyDetailItem = null" class="absolute top-4 right-4 p-2 hover:bg-gray-100 rounded-full cursor-pointer">
            ✕
          </button>
          <QuestionCard
            :question="historyDetailItem.question"
            :question-number="historyDetailItem.index + 1"
            :loading="false"
            class="pointer-events-none shadow-none"
          />
        </div>
      </div>
    </transition>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue';
import QuestionCard from '../components/QuestionCard.vue';
import { questionApi } from '../api/questiongen';

// LocalStorage key for history persistence
const HISTORY_STORAGE_KEY = 'questiongen_history';

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
const error = ref(null);

const correctCount = computed(() => historyQuestions.value.filter(h => h.correct).length);

// Load history from localStorage on mount
function loadHistoryFromStorage() {
  try {
    const stored = localStorage.getItem(HISTORY_STORAGE_KEY);
    if (stored) {
      historyQuestions.value = JSON.parse(stored);
    }
  } catch (e) {
    console.error('Failed to load history from localStorage:', e);
  }
}

// Save history to localStorage
function saveHistoryToStorage() {
  try {
    // Keep only last 50 questions to avoid storage limits
    const toSave = historyQuestions.value.slice(-50);
    localStorage.setItem(HISTORY_STORAGE_KEY, JSON.stringify(toSave));
  } catch (e) {
    console.error('Failed to save history to localStorage:', e);
  }
}

// Watch history changes and persist
watch(historyQuestions, () => {
  saveHistoryToStorage();
}, { deep: true });

// Clear history
function clearHistory() {
  if (confirm('确定要清空所有答题历史吗？')) {
    historyQuestions.value = [];
    localStorage.removeItem(HISTORY_STORAGE_KEY);
  }
}

// Generate a single new question
async function generateSingleQuestion() {
  try {
    error.value = null;
    const response = await questionApi.generateQuestion();
    return response.data;
  } catch (err) {
    console.error('Failed to generate question:', err);
    error.value = err.response?.data?.error || err.message || '生成题目失败，请检查网络连接';
    return null;
  }
}

// Retry after error
async function retryGenerate() {
  loading.value = true;
  loadingMessage.value = '正在重新生成题目...';
  error.value = null;
  currentQuestion.value = await generateSingleQuestion();
  loading.value = false;
  if (currentQuestion.value) {
    prefetchNextQuestion();
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
    id: currentQuestion.value.id || Date.now(),
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
  error.value = null;
  
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
    if (currentQuestion.value) {
      prefetchNextQuestion();
    }
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
  // Load history from localStorage
  loadHistoryFromStorage();
  
  loading.value = true;
  loadingMessage.value = '正在生成第一道题目...';
  
  // Generate first question
  currentQuestion.value = await generateSingleQuestion();
  loading.value = false;
  
  // Start prefetching second question
  if (currentQuestion.value) {
    prefetchNextQuestion();
  }
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
