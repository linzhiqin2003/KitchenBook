<template>
  <div class="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50 safe-area-bottom">
    <!-- Header: Premium Unified Command Bar -->
    <header class="sticky top-0 z-40 bg-white/80 backdrop-blur-xl border-b border-gray-100 transition-all">
      <div class="max-w-5xl mx-auto px-2 sm:px-4 h-16 flex items-center justify-between gap-2 sm:gap-4">
        
        <!-- Left: Back Button + Course Identity -->
        <div class="flex items-center gap-2 shrink-0">
          <!-- Back to Home -->
          <router-link 
            to="/" 
            class="w-9 h-9 rounded-lg bg-gray-100 hover:bg-indigo-100 flex items-center justify-center transition-all group"
            title="返回首页"
          >
            <svg class="w-4 h-4 text-gray-500 group-hover:text-indigo-600 group-hover:-translate-x-0.5 transition-all" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 19l-7-7m0 0l7-7m-7 7h18"/>
            </svg>
          </router-link>
          
          <!-- Course Identity -->
          <div class="relative">
          <button
            @click="showCourseDropdown = !showCourseDropdown"
            class="group flex items-center gap-3 hover:bg-gray-50 px-2 py-1.5 -ml-2 rounded-xl transition-all"
          >
            <div class="w-10 h-10 flex items-center justify-center bg-gradient-to-br from-indigo-500 to-blue-600 text-white rounded-lg shadow-sm group-hover:shadow-md transition-all">
              <span class="text-xl">{{ currentCourseIcon }}</span>
            </div>
            <div class="text-left hidden sm:block">
              <div class="text-xs font-medium text-gray-500">Current Course</div>
              <div class="text-sm font-bold text-gray-900 flex items-center gap-1">
                {{ currentCourseName }}
                <svg class="w-3 h-3 text-gray-400 group-hover:text-indigo-600 transition-colors" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"/></svg>
              </div>
            </div>
          </button>

          <!-- Course Dropdown -->
          <div v-if="showCourseDropdown" class="absolute top-full left-0 mt-2 bg-white rounded-2xl shadow-xl ring-1 ring-black/5 p-2 z-50 w-72 origin-top-left flex flex-col gap-1">
            <button
              v-for="(course, id) in availableCourses"
              :key="id"
              @click="selectCourse(id)"
              :class="currentCourseId === id ? 'bg-indigo-50 text-indigo-700' : 'text-gray-700 hover:bg-gray-50'"
              class="w-full px-3 py-3 text-left rounded-xl flex items-center gap-3 transition-all"
            >
              <span class="text-xl bg-white p-2 rounded-lg shadow-sm border border-gray-100">{{ course.icon }}</span>
              <div>
                <div class="font-bold text-sm">{{ course.name }}</div>
                <div class="text-xs opacity-70 mt-0.5 font-medium">{{ course.description }}</div>
              </div>
              <div v-if="currentCourseId === id" class="ml-auto text-indigo-600">
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/></svg>
              </div>
            </button>
          </div>
        </div>
        </div>

        <!-- Center: Unified Control Pill -->
        <div class="flex-1 flex justify-center max-w-2xl">
          <div class="flex items-center bg-gray-100/80 p-1 sm:p-1.5 rounded-2xl border border-gray-200/50 shadow-inner gap-1 sm:gap-2">
            
            <!-- Mode Segment -->
            <div class="flex bg-white rounded-xl shadow-sm border border-gray-100 divide-x divide-gray-100 overflow-hidden">
              <button
                @click="setMode('random')"
                :class="practiceMode === 'random' ? 'bg-indigo-50 text-indigo-700 font-bold' : 'text-gray-500 hover:bg-gray-50 font-medium'"
                class="px-3 sm:px-4 py-1.5 text-xs sm:text-sm transition-all flex items-center gap-2"
              >
                <span>🎲</span>
                <span class="hidden sm:inline">随机</span>
              </button>
              <button
                @click="setMode('topic')"
                :class="practiceMode === 'topic' ? 'bg-indigo-50 text-indigo-700 font-bold' : 'text-gray-500 hover:bg-gray-50 font-medium'"
                class="px-3 sm:px-4 py-1.5 text-xs sm:text-sm transition-all flex items-center gap-2"
              >
                <span>📚</span>
                <span class="hidden sm:inline">主题</span>
              </button>
            </div>

            <!-- VS Separator (Visual Only) -->
            <div class="w-px h-5 bg-gray-300 hidden sm:block"></div>

            <!-- Topic Selector (Conditional) -->
            <div v-if="practiceMode === 'topic'" class="relative">
              <button
                @click="showTopicDropdown = !showTopicDropdown"
                class="px-2 sm:px-3 py-1.5 bg-white border border-gray-200 rounded-xl text-xs sm:text-sm font-medium text-gray-700 hover:border-indigo-300 hover:text-indigo-600 transition-all flex items-center gap-2 min-w-[100px] sm:min-w-[120px] justify-between shadow-sm"
              >
                <span class="truncate max-w-[100px] sm:max-w-[150px]">{{ selectedTopic === 'all' ? '选择主题' : formatTopicName(selectedTopic) }}</span>
                <svg class="w-3 h-3 opacity-50" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"/></svg>
              </button>
               
               <!-- Topic Menu -->
               <div v-if="showTopicDropdown" class="absolute top-full left-0 mt-2 w-64 max-h-[300px] overflow-y-auto bg-white rounded-xl shadow-xl ring-1 ring-black/5 p-1 z-50">
                 <button
                   v-for="topic in availableTopics"
                   :key="topic"
                   @click="selectTopicFromDropdown(topic)"
                   :class="selectedTopic === topic ? 'bg-indigo-50 text-indigo-700' : 'text-gray-600 hover:bg-gray-50'"
                   class="w-full px-3 py-2 text-left text-sm rounded-lg flex justify-between items-center transition-colors mb-0.5"
                 >
                   <span class="truncate">{{ formatTopicName(topic) }}</span>
                   <span class="text-xs bg-gray-100 text-gray-500 px-1.5 py-0.5 rounded-full">{{ topicStats[topic] || 0 }}</span>
                 </button>
               </div>
            </div>
            
            <!-- Default Text when Random -->
            <div v-else class="hidden sm:flex items-center px-3 text-xs text-gray-400 font-medium select-none">
              全库随机 · {{ totalCachedQuestions }}题
            </div>

            <!-- VS Separator -->
            <div class="w-px h-5 bg-gray-300 hidden sm:block"></div>

            <!-- Difficulty Traffic Lights -->
            <div class="flex items-center gap-1 pl-1">
              <button
                 v-for="diff in difficultyOptions"
                 :key="diff.value"
                 @click="setDifficulty(diff.value)"
                 class="group relative w-6 h-6 rounded-full flex items-center justify-center transition-all hover:scale-110"
                 :title="diff.label"
              >
                <div 
                  class="w-3 h-3 rounded-full transition-all duration-300"
                  :class="[
                     selectedDifficulty === diff.value ? 'scale-125 ring-2 ring-offset-1 ring-gray-200 opacity-100' : 'opacity-20 group-hover:opacity-100',
                     diff.value === 'easy' ? 'bg-green-500' : diff.value === 'medium' ? 'bg-yellow-500' : 'bg-red-500'
                  ]"
                ></div>
              </button>
            </div>

          </div>
        </div>

        <!-- Right: Meta Actions -->
        <div class="flex items-center gap-3 shrink-0">
          <div class="hidden sm:flex flex-col items-end mr-2">
            <span class="text-[10px] uppercase font-bold text-gray-400 tracking-wider">Session</span>
            <div class="text-sm font-bold text-gray-700 font-mono">{{ correctCount }}<span class="text-gray-300">/</span>{{ historyQuestions.length }}</div>
          </div>
          
          <button 
             @click="showHistory = !showHistory" 
             class="w-10 h-10 rounded-full bg-white border border-gray-100 shadow-sm flex items-center justify-center text-gray-400 hover:text-indigo-600 hover:border-indigo-100 hover:shadow-md transition-all relative overflow-hidden group"
             title="历史记录"
          >
             <span class="relative z-10">📋</span>
             <div class="absolute inset-0 bg-indigo-50 transform scale-0 group-hover:scale-100 transition-transform origin-center rounded-full"></div>
          </button>
          
          <button 
             v-if="historyQuestions.length > 0" 
             @click="clearHistory" 
             class="w-10 h-10 rounded-full bg-white border border-gray-100 shadow-sm flex items-center justify-center text-gray-400 hover:text-red-500 hover:border-red-100 hover:shadow-md transition-all group relative overflow-hidden"
             title="清空"
          >
             <span class="relative z-10">🗑️</span>
             <div class="absolute inset-0 bg-red-50 transform scale-0 group-hover:scale-100 transition-transform origin-center rounded-full"></div>
          </button>
        </div>

      </div>
    </header>

    <!-- Click outside overlay - Must be BELOW header z-index but above main content -->
    <div 
      v-if="showCourseDropdown || showTopicDropdown" 
      class="fixed inset-0"
      style="z-index: 35;"
      @click="showCourseDropdown = false; showTopicDropdown = false"
    ></div>

    <!-- Main Content -->
    <main class="max-w-2xl mx-auto px-4 pt-6 pb-12">
      <!-- Loading State - Skeleton -->
      <div v-if="loading">
        <QuestionSkeleton />
        <p class="mt-4 text-center text-sm text-gray-400">{{ loadingMessage }}</p>
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

    <!-- AI Chat Window -->
    <AIChatWindow
      :current-question="currentQuestion"
      :course-id="currentCourseId"
      :question-answered="questionAnswered"
      :user-answer="userAnswer"
      @question-deleted="handleQuestionDeleted"
    />
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue';
import QuestionCard from '../components/QuestionCard.vue';
import QuestionSkeleton from '../components/QuestionSkeleton.vue';
import AIChatWindow from '../components/AIChatWindow.vue';
import { questionApi } from '../api';

// LocalStorage keys
const HISTORY_STORAGE_KEY = 'questiongen_history';
const SEEN_IDS_STORAGE_KEY = 'questiongen_seen_ids';
const SELECTED_TOPIC_KEY = 'questiongen_selected_topic';
const PRACTICE_MODE_KEY = 'questiongen_practice_mode';
const CURRENT_COURSE_KEY = 'questiongen_current_course';

// State
const currentQuestion = ref(null);
const prefetchedQuestion = ref(null);
const historyQuestions = ref([]);
const seenQuestionIds = ref([]); // Answered/Completed questions (Persisted)
const sessionSeenIds = ref([]);  // Temporary seen in this session
const loading = ref(true);
const isMobileMenuOpen = ref(false);
const prefetching = ref(false);
const loadingMessage = ref('正在加载题目...');
const showHistory = ref(false);
const historyDetailItem = ref(null);
const cardRef = ref(null);
const error = ref(null);
const questionSource = ref('');
const questionAnswered = ref(false);
const userAnswer = ref(null);  // { selected: 'A. xxx', correct: true/false }

// Course selection state
const currentCourseId = ref(null);
const availableCourses = ref({});
const showCourseDropdown = ref(false);

// Topic/Mode selection state
const practiceMode = ref('random');
const selectedTopic = ref('all');
const availableTopics = ref([]);
const topicsLoaded = ref(false);
const showTopicDropdown = ref(false);

// Stats
const totalCachedQuestions = ref(0);
const topicStats = ref({});

// Difficulty filter
const selectedDifficulty = ref(null);  // null = all, 'easy', 'medium', 'hard'
const difficultyOptions = [
  { value: 'easy', label: 'Easy', activeClass: 'bg-green-500 text-white shadow-sm' },
  { value: 'medium', label: 'Medium', activeClass: 'bg-yellow-500 text-white shadow-sm' },
  { value: 'hard', label: 'Hard', activeClass: 'bg-red-500 text-white shadow-sm' }
];

// Computed
const correctCount = computed(() => historyQuestions.value.filter(h => h.correct).length);

const currentCourse = computed(() => availableCourses.value[currentCourseId.value] || {});
const currentCourseName = computed(() => currentCourse.value.name || '选择课程');
const currentCourseDisplayName = computed(() => currentCourse.value.display_name || currentCourse.value.name || '刷题');
const currentCourseIcon = computed(() => currentCourse.value.icon || '📚');

// Load available courses
async function loadCourses() {
  try {
    const response = await questionApi.getCourses();
    const data = response.data;
    availableCourses.value = data.courses || {};
    
    // Set default course
    const storedCourse = localStorage.getItem(CURRENT_COURSE_KEY);
    if (storedCourse && availableCourses.value[storedCourse]) {
      currentCourseId.value = storedCourse;
    } else if (data.default) {
      currentCourseId.value = data.default;
    } else {
      currentCourseId.value = Object.keys(availableCourses.value)[0];
    }
  } catch (err) {
    console.error('Failed to load courses:', err);
  }
}

// Select course
async function selectCourse(courseId) {
  if (courseId === currentCourseId.value) {
    showCourseDropdown.value = false;
    return;
  }
  
  showCourseDropdown.value = false;
  currentCourseId.value = courseId;
  localStorage.setItem(CURRENT_COURSE_KEY, courseId);
  
  // Clear current state
  prefetchedQuestion.value = null;
  seenQuestionIds.value = [];
  selectedTopic.value = 'all';
  
  // Reload topics and questions for new course
  await loadTopics();
  await loadStats();
  
  loading.value = true;
  loadingMessage.value = `正在加载 ${currentCourseName.value} 题目...`;
  error.value = null;
  
  currentQuestion.value = await getSmartNextQuestion();
  loading.value = false;
  
  if (currentQuestion.value) {
    prefetchNextQuestion();
  }
}

// Load stats from server
async function loadStats() {
  try {
    const response = await questionApi.getStats(currentCourseId.value);
    const data = response.data;
    totalCachedQuestions.value = data.total_cached || 0;
    topicStats.value = data.by_topic || {};
  } catch (err) {
    console.error('Failed to load stats:', err);
  }
}

// Format topic name for display
function formatTopicName(topic) {
  if (!topic) return topic;
  const parts = topic.split('-');
  
  // Only remove the first part if it's a number prefix (e.g., "01-sysadmin" -> "sysadmin")
  let relevantParts = parts;
  if (parts.length > 1 && /^\d+$/.test(parts[0])) {
    relevantParts = parts.slice(1);
  }
  
  // Capitalize each word and join with spaces
  return relevantParts
    .map(part => {
      // Handle Roman numerals (i, ii, iii, iv, v, etc.)
      if (/^(i{1,3}|iv|v|vi{0,3})$/i.test(part)) {
        return part.toUpperCase();
      }
      // Handle common abbreviations
      if (['adts', 'sql', 'api', 'css', 'html', 'js', '1d', '2d', '3d'].includes(part.toLowerCase())) {
        return part.toUpperCase();
      }
      // Normal capitalization
      return part.charAt(0).toUpperCase() + part.slice(1);
    })
    .join(' ');
}

// Set difficulty filter
async function setDifficulty(difficulty) {
  // Toggle logic: if clicking the same difficulty, deselect it (set to null)
  if (selectedDifficulty.value === difficulty) {
    selectedDifficulty.value = null;
  } else {
    selectedDifficulty.value = difficulty;
  }
  // Reload question with new difficulty filter
  loading.value = true;
  loadingMessage.value = '切换难度中...';
  prefetchedQuestion.value = null;
  currentQuestion.value = await getSmartNextQuestion();
  loading.value = false;
  if (currentQuestion.value) {
    prefetchNextQuestion();
  }
}

// Load topics from server
async function loadTopics() {
  try {
    const response = await questionApi.getTopics(currentCourseId.value);
    const data = response.data;
    let topics = data.courseware_topics || data.topics || [];
    
    // Sort topics intelligently
    topics.sort((a, b) => {
      // Extract numbers from topic names for natural sorting
      // Handles patterns like "chapter-5", "01-topic", "a-topic"
      const extractNumber = (str) => {
        // Try to find chapter number (chapter-N or chapter_N)
        const chapterMatch = str.match(/chapter[-_](\d+)/i);
        if (chapterMatch) return parseInt(chapterMatch[1]);
        
        // Try leading number (01-topic, 02-topic)
        const leadingMatch = str.match(/^(\d+)/);
        if (leadingMatch) return parseInt(leadingMatch[1]);
        
        // Try single letter prefix (a-topic, b-topic)
        const letterMatch = str.match(/^([a-z])[-_]/i);
        if (letterMatch) return letterMatch[1].toLowerCase().charCodeAt(0) - 96; // a=1, b=2, etc.
        
        return 999; // No number found, put at end
      };
      
      const numA = extractNumber(a);
      const numB = extractNumber(b);
      
      if (numA !== numB) return numA - numB;
      return a.localeCompare(b); // Fall back to alphabetical
    });
    
    availableTopics.value = topics;
    topicsLoaded.value = true;
  } catch (err) {
    console.error('Failed to load topics:', err);
    topicsLoaded.value = true;
  }
}

// Set practice mode
async function setMode(mode) {
  if (mode === practiceMode.value) return;
  
  practiceMode.value = mode;
  localStorage.setItem(PRACTICE_MODE_KEY, mode);
  showTopicDropdown.value = false;
  isMobileMenuOpen.value = false;
  
  // Clear prefetched question
  prefetchedQuestion.value = null;
  loading.value = true;
  error.value = null;
  
  if (mode === 'random') {
    selectedTopic.value = 'all';
    localStorage.setItem(SELECTED_TOPIC_KEY, 'all');
    loadingMessage.value = '正在加载随机题目...';
  } else if (mode === 'topic') {
    // Load topics if not loaded
    if (!topicsLoaded.value) {
      await loadTopics();
    }
    // Keep current topic or use first available
    if (selectedTopic.value === 'all' && availableTopics.value.length > 0) {
      selectedTopic.value = availableTopics.value[0];
      localStorage.setItem(SELECTED_TOPIC_KEY, selectedTopic.value);
    }
    loadingMessage.value = `正在加载 ${formatTopicName(selectedTopic.value)} 题目...`;
  }
  
  currentQuestion.value = await getSmartNextQuestion();
  loading.value = false;
  
  if (currentQuestion.value) {
    prefetchNextQuestion();
  }
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
  
  prefetchedQuestion.value = null;
  
  loading.value = true;
  loadingMessage.value = `正在加载 ${topic === 'all' ? '随机' : formatTopicName(topic)} 题目...`;
  error.value = null;
  
  currentQuestion.value = await getSmartNextQuestion();
  loading.value = false;
  
  if (currentQuestion.value) {
    prefetchNextQuestion();
  }
}

// Load history from localStorage
function loadHistoryFromStorage() {
  try {
    const stored = localStorage.getItem(HISTORY_STORAGE_KEY);
    if (stored) {
      historyQuestions.value = JSON.parse(stored);
    }
    const seenStored = localStorage.getItem(SEEN_IDS_STORAGE_KEY);
    if (seenStored) {
      seenQuestionIds.value = JSON.parse(seenStored);
    }
    const modeStored = localStorage.getItem(PRACTICE_MODE_KEY);
    if (modeStored) {
      practiceMode.value = modeStored;
    }
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
    const toSave = historyQuestions.value.slice(-100);
    localStorage.setItem(HISTORY_STORAGE_KEY, JSON.stringify(toSave));
    const seenToSave = seenQuestionIds.value.slice(-500);
    localStorage.setItem(SEEN_IDS_STORAGE_KEY, JSON.stringify(seenToSave));
  } catch (e) {
    console.error('Failed to save history to localStorage:', e);
  }
}

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

// Get next question
async function getSmartNextQuestion() {
  try {
    error.value = null;
    // Cycle Logic: If we've viewed all available cached questions in this session, reset session history
    const currentPoolSize = selectedTopic.value === 'all' 
      ? totalCachedQuestions.value 
      : (topicStats.value[selectedTopic.value] || 0);
      
    const effectiveSessionSeenCount = sessionSeenIds.value.filter(id => !seenQuestionIds.value.includes(id)).length;
    
    // If we've seen (but not answered) nearly all cached questions, relax the session filter
    if (currentPoolSize > 0 && effectiveSessionSeenCount >= currentPoolSize) {
      // Keep only the most recent one to prevent immediate back-to-back, but allow cycling
      sessionSeenIds.value = sessionSeenIds.value.slice(-1);
    }

    // Combine persistent seen IDs (answered) and session seen IDs (viewed)
    const combinedSeenIds = [...new Set([...seenQuestionIds.value, ...sessionSeenIds.value])];

    const topicParam = selectedTopic.value === 'all' ? null : selectedTopic.value;
    const difficultyParam = selectedDifficulty.value;
    
    const response = await questionApi.smartNext(
      combinedSeenIds, 
      true, 
      topicParam, 
      difficultyParam,
      currentCourseId.value
    );
    const question = response.data;
    
    questionSource.value = question.source || 'unknown';
    
    // Mark as seen in this session (so we don't immediately repeat it if we skip)
    if (question.id && !sessionSeenIds.value.includes(question.id)) {
      sessionSeenIds.value.push(question.id);
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



// Prefetch next question
async function prefetchNextQuestion() {
  if (prefetching.value || prefetchedQuestion.value) return;
  
  prefetching.value = true;
  try {
    // Cycle Logic for prefetch
    const currentPoolSize = selectedTopic.value === 'all' 
      ? totalCachedQuestions.value 
      : (topicStats.value[selectedTopic.value] || 0);
      
    const effectiveSessionSeenCount = sessionSeenIds.value.filter(id => !seenQuestionIds.value.includes(id)).length;
    
    // Combine persistent and session seen IDs
    let idsToExclude = [...seenQuestionIds.value];
    
    // Only exclude session seen IDs if we haven't seen the whole pool yet
    if (currentPoolSize === 0 || effectiveSessionSeenCount < currentPoolSize) {
       idsToExclude = [...idsToExclude, ...sessionSeenIds.value];
    }
    
    const combinedSeenIds = [...new Set(idsToExclude)];
    
    // Also tentatively mark current question as seen for the purpose of prefetching next
    if (currentQuestion.value?.id && !combinedSeenIds.includes(currentQuestion.value.id)) {
      combinedSeenIds.push(currentQuestion.value.id);
    }
    
    const topicParam = selectedTopic.value === 'all' ? null : selectedTopic.value;
    // Fix: pass null for difficulty (4th arg) so courseId (5th arg) is correct
    const response = await questionApi.smartNext(combinedSeenIds, true, topicParam, null, currentCourseId.value);
    const question = response.data;
    
    // Add to session seen (not persistent yet)
    if (question.id && !sessionSeenIds.value.includes(question.id)) {
      sessionSeenIds.value.push(question.id);
    }
    
    prefetchedQuestion.value = question;
  } catch (err) {
    console.error('Failed to prefetch question:', err);
  } finally {
    prefetching.value = false;
  }
}

// Record answer in history
function onAnswered({ selected, correct }) {
  if (!currentQuestion.value) return;
  
  // Mark question as answered for chat window
  questionAnswered.value = true;
  
  // Save user's answer for AI context
  userAnswer.value = { selected, correct };
  
  // Mark as permanently seen/completed
  if (currentQuestion.value?.id && !seenQuestionIds.value.includes(currentQuestion.value.id)) {
    seenQuestionIds.value.push(currentQuestion.value.id);
  }
  
  historyQuestions.value.push({
    id: currentQuestion.value.id || Date.now(),
    question: currentQuestion.value,
    correct,
    answeredAt: new Date().toISOString()
  });
  
  prefetchNextQuestion();
}

// Move to next question
async function moveToNextQuestion() {
  loading.value = true;
  loadingMessage.value = '正在加载下一题...';
  error.value = null;
  questionAnswered.value = false;
  userAnswer.value = null;  // Reset user answer for new question
  
  const prefetchedTopic = prefetchedQuestion.value?.topic;
  const currentTopicMatches = selectedTopic.value === 'all' || 
    (prefetchedTopic && prefetchedTopic.toLowerCase().includes(selectedTopic.value.toLowerCase()));
  
  if (prefetchedQuestion.value && currentTopicMatches) {
    currentQuestion.value = prefetchedQuestion.value;
    prefetchedQuestion.value = null;
    loading.value = false;
    prefetchNextQuestion();
  } else {
    prefetchedQuestion.value = null;
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

// Handle question deleted from AI chat
async function handleQuestionDeleted(questionId) {
  console.log('Question deleted:', questionId);
  
  // Reset answer state - this will trigger AI chat to close
  questionAnswered.value = false;
  userAnswer.value = null;
  
  // Clear prefetched if it was the deleted question
  if (prefetchedQuestion.value?.id === questionId) {
    prefetchedQuestion.value = null;
  }
  
  // If current question was deleted, load next one
  if (currentQuestion.value?.id === questionId) {
    loading.value = true;
    loadingMessage.value = '题目已删除，正在加载下一题...';
    currentQuestion.value = await getSmartNextQuestion();
    loading.value = false;
    
    if (currentQuestion.value) {
      prefetchNextQuestion();
    }
  }
  
  // Update stats
  await loadStats();
}

// Initial load
onMounted(async () => {
  loadHistoryFromStorage();
  
  // Load courses first
  await loadCourses();
  
  // Then load topics and stats for the current course
  await loadTopics();
  await loadStats();
  
  loading.value = true;
  loadingMessage.value = '正在加载题目...';
  
  currentQuestion.value = await getSmartNextQuestion();
  loading.value = false;
  
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
  line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
</style>
