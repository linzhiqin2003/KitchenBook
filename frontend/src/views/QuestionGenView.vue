<template>
  <div class="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50">
    <!-- Header -->
    <header class="sticky top-0 z-10 bg-white/95 backdrop-blur-xl border-b border-gray-200/50 shadow-sm">
      <div class="max-w-2xl mx-auto px-3 sm:px-4 py-3">
        <!-- Top Row: Title and Actions -->
        <div class="flex items-center justify-between">
          <div class="flex items-center gap-2 sm:gap-3">
            <router-link to="/" class="p-1.5 sm:p-2 hover:bg-gray-100 rounded-lg transition-colors" title="返回首页">
              <svg class="w-5 h-5 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 19l-7-7m0 0l7-7m-7 7h18"/>
              </svg>
            </router-link>
            <h1 class="text-sm sm:text-xl font-bold text-gray-900">📚 Software Tools 刷题</h1>
          </div>
          <div class="flex items-center gap-1.5 sm:gap-3">
            <span class="text-xs sm:text-sm text-gray-500 bg-gray-100 px-2 sm:px-3 py-1 rounded-full">
              {{ correctCount }}/{{ historyQuestions.length }}
            </span>
            <button
              @click="showHistory = !showHistory"
              class="p-2 text-sm font-medium text-gray-600 hover:bg-gray-100 rounded-lg transition-colors cursor-pointer"
              title="历史记录"
            >
              📋
            </button>
            <button
              v-if="historyQuestions.length > 0"
              @click="clearHistory"
              class="p-2 text-sm font-medium text-red-500 hover:bg-red-50 rounded-lg transition-colors cursor-pointer"
              title="清空历史"
            >
              🗑️
            </button>
          </div>
        </div>
        
        <!-- Mode Toggle Row -->
        <div class="mt-3 flex items-center gap-3">
          <!-- Mode Switch -->
          <div class="flex items-center bg-gray-100 rounded-full p-1">
            <button
              @click="setMode('random')"
              :class="practiceMode === 'random' 
                ? 'bg-white text-blue-600 shadow-sm' 
                : 'text-gray-500 hover:text-gray-700'"
              class="px-3 sm:px-4 py-1.5 text-xs sm:text-sm font-medium rounded-full transition-all cursor-pointer"
            >
              🎲 随机
            </button>
            <button
              @click="setMode('topic')"
              :class="practiceMode === 'topic' 
                ? 'bg-white text-blue-600 shadow-sm' 
                : 'text-gray-500 hover:text-gray-700'"
              class="px-3 sm:px-4 py-1.5 text-xs sm:text-sm font-medium rounded-full transition-all cursor-pointer"
            >
              📚 主题
            </button>
          </div>
          
          <!-- Topic Dropdown (only show when in topic mode) -->
          <div v-if="practiceMode === 'topic'" class="relative flex-1">
            <button
              @click="showTopicDropdown = !showTopicDropdown"
              class="w-full flex items-center justify-between gap-2 px-3 sm:px-4 py-2 bg-blue-50 border border-blue-200 rounded-xl text-sm text-blue-700 font-medium cursor-pointer hover:bg-blue-100 transition-colors"
            >
              <span class="truncate">{{ selectedTopic === 'all' ? '选择主题' : formatTopicName(selectedTopic) }}</span>
              <svg 
                class="w-4 h-4 flex-shrink-0 transition-transform" 
                :class="showTopicDropdown ? 'rotate-180' : ''"
                fill="none" stroke="currentColor" viewBox="0 0 24 24"
              >
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"/>
              </svg>
            </button>
            
            <!-- Dropdown Menu -->
            <transition name="dropdown">
              <div 
                v-if="showTopicDropdown" 
                class="absolute top-full left-0 right-0 mt-2 bg-white rounded-xl shadow-lg border border-gray-200 overflow-hidden z-20 max-h-64 overflow-y-auto"
              >
                <button
                  v-for="topic in availableTopics"
                  :key="topic"
                  @click="selectTopicFromDropdown(topic)"
                  :class="selectedTopic === topic ? 'bg-blue-50 text-blue-700' : 'text-gray-700 hover:bg-gray-50'"
                  class="w-full px-4 py-3 text-left text-sm font-medium border-b border-gray-100 last:border-b-0 cursor-pointer transition-colors"
                >
                  {{ formatTopicName(topic) }}
                </button>
                <div v-if="!topicsLoaded" class="px-4 py-3 text-sm text-gray-400 text-center">
                  加载中...
                </div>
              </div>
            </transition>
          </div>
          
          <!-- Current Topic Badge (random mode) -->
          <div v-else class="flex-1 text-xs sm:text-sm text-gray-500">
            全部主题随机出题
          </div>
        </div>
      </div>
    </header>

    <!-- Click outside to close dropdown -->
    <div 
      v-if="showTopicDropdown" 
      class="fixed inset-0 z-[5]" 
      @click="showTopicDropdown = false"
    ></div>



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

// LocalStorage keys
const HISTORY_STORAGE_KEY = 'questiongen_history';
const SEEN_IDS_STORAGE_KEY = 'questiongen_seen_ids';
const SELECTED_TOPIC_KEY = 'questiongen_selected_topic';
const PRACTICE_MODE_KEY = 'questiongen_practice_mode';

// State
const currentQuestion = ref(null);
const prefetchedQuestion = ref(null);
const historyQuestions = ref([]);
const seenQuestionIds = ref([]); // Track all seen question IDs (for server-side filtering)
const loading = ref(true);
const prefetching = ref(false);
const loadingMessage = ref('正在加载题目...');
const showHistory = ref(false);
const historyDetailItem = ref(null);
const cardRef = ref(null);
const error = ref(null);
const questionSource = ref(''); // 'cached' or 'generated'

// Topic/Mode selection state
const practiceMode = ref('random'); // 'random' or 'topic'
const selectedTopic = ref('all');
const availableTopics = ref([]);
const topicsLoaded = ref(false);
const showTopicDropdown = ref(false);

const correctCount = computed(() => historyQuestions.value.filter(h => h.correct).length);

// Format topic name for display
function formatTopicName(topic) {
  if (!topic) return topic;
  // Extract meaningful part from topic names like "01-sysadmin" -> "Sysadmin"
  const parts = topic.split('-');
  if (parts.length > 1) {
    return parts.slice(1).join('-').replace(/^\w/, c => c.toUpperCase());
  }
  return topic.replace(/^\w/, c => c.toUpperCase());
}

// Load topics from server
async function loadTopics() {
  try {
    const response = await questionApi.getTopics();
    const data = response.data;
    // Use courseware topics as they are more organized
    availableTopics.value = data.courseware_topics || data.topics || [];
    topicsLoaded.value = true;
  } catch (err) {
    console.error('Failed to load topics:', err);
    topicsLoaded.value = true;
  }
}

// Set practice mode (random or topic)
async function setMode(mode) {
  if (mode === practiceMode.value) return;
  
  practiceMode.value = mode;
  localStorage.setItem(PRACTICE_MODE_KEY, mode);
  showTopicDropdown.value = false;
  
  if (mode === 'random') {
    // Switch to random mode
    selectedTopic.value = 'all';
    localStorage.setItem(SELECTED_TOPIC_KEY, 'all');
    
    // Clear prefetched question and load new random question
    prefetchedQuestion.value = null;
    loading.value = true;
    loadingMessage.value = '正在加载随机题目...';
    error.value = null;
    
    currentQuestion.value = await getSmartNextQuestion();
    loading.value = false;
    
    if (currentQuestion.value) {
      prefetchNextQuestion();
    }
  }
  // For topic mode, wait for user to select a topic
}

// Select topic from dropdown
async function selectTopicFromDropdown(topic) {
  showTopicDropdown.value = false;
  await selectTopic(topic);
}

// Select topic and reload question
async function selectTopic(topic) {
  if (topic === selectedTopic.value && practiceMode.value === 'topic') return;
  
  selectedTopic.value = topic;
  localStorage.setItem(SELECTED_TOPIC_KEY, topic);
  
  // Clear prefetched question as it may be for a different topic
  prefetchedQuestion.value = null;
  
  // Load new question for this topic
  loading.value = true;
  loadingMessage.value = `正在加载 ${topic === 'all' ? '随机' : formatTopicName(topic)} 题目...`;
  error.value = null;
  
  currentQuestion.value = await getSmartNextQuestion();
  loading.value = false;
  
  if (currentQuestion.value) {
    prefetchNextQuestion();
  }
}

// Load history from localStorage on mount
function loadHistoryFromStorage() {
  try {
    const stored = localStorage.getItem(HISTORY_STORAGE_KEY);
    if (stored) {
      historyQuestions.value = JSON.parse(stored);
    }
    // Also load seen IDs
    const seenStored = localStorage.getItem(SEEN_IDS_STORAGE_KEY);
    if (seenStored) {
      seenQuestionIds.value = JSON.parse(seenStored);
    }
    // Load practice mode
    const modeStored = localStorage.getItem(PRACTICE_MODE_KEY);
    if (modeStored) {
      practiceMode.value = modeStored;
    }
    // Load selected topic
    const topicStored = localStorage.getItem(SELECTED_TOPIC_KEY);
    if (topicStored) {
      selectedTopic.value = topicStored;
    }
  } catch (e) {
    console.error('Failed to load history from localStorage:', e);
  }
}

// Save history to localStorage
function saveHistoryToStorage() {
  try {
    // Keep only last 100 questions to avoid storage limits
    const toSave = historyQuestions.value.slice(-100);
    localStorage.setItem(HISTORY_STORAGE_KEY, JSON.stringify(toSave));
    // Also save seen IDs (keep last 500)
    const seenToSave = seenQuestionIds.value.slice(-500);
    localStorage.setItem(SEEN_IDS_STORAGE_KEY, JSON.stringify(seenToSave));
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
    seenQuestionIds.value = [];
    localStorage.removeItem(HISTORY_STORAGE_KEY);
    localStorage.removeItem(SEEN_IDS_STORAGE_KEY);
  }
}

// Get next question using smart endpoint (prioritizes cached)
async function getSmartNextQuestion() {
  try {
    error.value = null;
    // Pass topic to API (null or 'all' means random)
    const topicParam = selectedTopic.value === 'all' ? null : selectedTopic.value;
    const response = await questionApi.smartNext(seenQuestionIds.value, true, topicParam);
    const question = response.data;
    
    // Track the source (cached vs generated)
    questionSource.value = question.source || 'unknown';
    
    // Add to seen IDs
    if (question.id && !seenQuestionIds.value.includes(question.id)) {
      seenQuestionIds.value.push(question.id);
    }
    
    return question;
  } catch (err) {
    console.error('Failed to get question:', err);
    error.value = err.response?.data?.error || err.message || '获取题目失败，请检查网络连接';
    return null;
  }
}

// Retry after error
async function retryGenerate() {
  loading.value = true;
  loadingMessage.value = '正在重新加载题目...';
  error.value = null;
  currentQuestion.value = await getSmartNextQuestion();
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
    // Include the current question ID in seen list for prefetch
    const allSeenIds = [...seenQuestionIds.value];
    if (currentQuestion.value?.id && !allSeenIds.includes(currentQuestion.value.id)) {
      allSeenIds.push(currentQuestion.value.id);
    }
    
    // Pass topic to API
    const topicParam = selectedTopic.value === 'all' ? null : selectedTopic.value;
    const response = await questionApi.smartNext(allSeenIds, true, topicParam);
    const question = response.data;
    
    // Add to seen IDs
    if (question.id && !seenQuestionIds.value.includes(question.id)) {
      seenQuestionIds.value.push(question.id);
    }
    
    prefetchedQuestion.value = question;
  } catch (err) {
    console.error('Failed to prefetch question:', err);
    // Don't set error - prefetch failure shouldn't block user
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
  
  // Use prefetched question if available AND matches current topic
  const prefetchedTopic = prefetchedQuestion.value?.topic;
  const currentTopicMatches = selectedTopic.value === 'all' || 
    (prefetchedTopic && prefetchedTopic.toLowerCase().includes(selectedTopic.value.toLowerCase()));
  
  if (prefetchedQuestion.value && currentTopicMatches) {
    currentQuestion.value = prefetchedQuestion.value;
    prefetchedQuestion.value = null;
    loading.value = false;
    // Start prefetching the next one
    prefetchNextQuestion();
  } else {
    // Clear mismatched prefetch
    prefetchedQuestion.value = null;
    // Get new question
    currentQuestion.value = await getSmartNextQuestion();
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
  
  // Load available topics
  loadTopics();
  
  loading.value = true;
  loadingMessage.value = '正在加载题目...';
  
  // Get first question (smart endpoint will return cached if available)
  currentQuestion.value = await getSmartNextQuestion();
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

.dropdown-enter-active,
.dropdown-leave-active {
  transition: all 0.2s ease;
}
.dropdown-enter-from,
.dropdown-leave-to {
  opacity: 0;
  transform: translateY(-8px);
}

.line-clamp-2 {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
</style>
