<template>
  <div data-qg-surface class="qg-shell" :class="{ 'qg-shell--sidebar': showSidebar }" :style="showSidebar ? { marginRight: sidebarWidth + 'px' } : {}">
    <!-- ─── Top bar: minimal hairline. Course + theme toggle live here. ─── -->
    <header class="qg-topbar">
      <div class="qg-topbar__inner">
        <div class="qg-topbar__left">
          <router-link to="/" class="qg-back" title="返回">
            <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M15 18l-6-6 6-6"/></svg>
          </router-link>
          <div class="qg-wordmark">
            <span class="qg-wordmark__brand">LZQ</span>
            <span class="qg-wordmark__sep">/</span>
            <span class="qg-wordmark__page">Practice</span>
          </div>
        </div>

        <div class="qg-topbar__right">
          <div class="qg-session" v-if="historyQuestions.length > 0">
            <span class="qg-session__label">Session</span>
            <span class="qg-num qg-session__count">{{ correctCount }}<span class="qg-session__sep">/</span>{{ historyQuestions.length }}</span>
          </div>
          <button class="qg-iconbtn" @click="showSidebar = !showSidebar" :data-active="showSidebar" title="AI 助手">
            <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>
          </button>
          <button class="qg-iconbtn" @click="showHistory = !showHistory" title="答题历史">
            <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M3 8a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2v10a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8z"/><path d="M3 8l9 7 9-7"/></svg>
          </button>
          <QgThemeToggle />
        </div>
      </div>
    </header>

    <!-- ─── Editorial title block: course + topic foregrounded as content. ─── -->
    <section class="qg-hero">
      <div class="qg-hero__inner">
        <div class="qg-eyebrow" data-mono>{{ currentCourseDisplayName || currentCourseName }}</div>

        <div class="qg-courseswitch">
          <button class="qg-courseswitch__trigger" @click="showCourseDropdown = !showCourseDropdown" :aria-expanded="showCourseDropdown">
            <h1 class="qg-display qg-hero__title">{{ currentCourseName }}</h1>
            <svg class="qg-courseswitch__chev" :class="{ 'qg-courseswitch__chev--open': showCourseDropdown }" viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M6 9l6 6 6-6"/></svg>
          </button>
          <div v-if="showCourseDropdown" class="qg-menu qg-menu--course">
            <button
              v-for="(course, id) in availableCourses"
              :key="id"
              class="qg-menu__row"
              :data-active="currentCourseId === id"
              @click="selectCourse(id)"
            >
              <span class="qg-menu__title">{{ course.name }}</span>
              <span class="qg-menu__sub">{{ course.description }}</span>
            </button>
          </div>
        </div>

        <p class="qg-hero__meta">
          <span>{{ totalCachedQuestions }} questions in library</span>
          <span class="qg-hero__dot">·</span>
          <span>{{ availableTopics.length }} topics</span>
        </p>

        <!-- Page-level mode tabs — switches the whole stage paradigm -->
        <nav class="qg-modetabs" role="tablist" aria-label="模式">
          <button
            v-for="sm in STUDY_MODES"
            :key="sm.value"
            role="tab"
            :aria-selected="studyMode === sm.value"
            class="qg-modetabs__btn"
            @click="setStudyMode(sm.value)"
          >
            <QgIcon :name="sm.icon" :size="15" class="qg-modetabs__icon" />
            <span class="qg-modetabs__label">{{ sm.label }}</span>
          </button>
        </nav>
      </div>
    </section>

    <!-- ─── Practice console — only shows controls relevant to the active mode ─── -->
    <section class="qg-console">
      <div class="qg-console__inner">
        <!-- Question type: questions only -->
        <div v-if="studyMode === 'answer'" class="qg-console__group">
          <div class="qg-console__label" data-mono>Type</div>
          <div class="qg-segment" role="tablist" aria-label="题型">
            <button
              v-for="qt in availableQuestionTypes"
              :key="qt.value"
              role="tab"
              :aria-selected="selectedQuestionType === qt.value"
              class="qg-segment__btn"
              @click="setQuestionType(qt.value)"
            >
              <span data-mono class="qg-segment__icon">{{ qt.icon }}</span>
              <span class="qg-segment__txt">{{ qt.label }}</span>
            </button>
          </div>
        </div>

        <!-- Source / Topic — Random+Topic toggle for questions, just the chapter picker for notes -->
        <div class="qg-console__group">
          <div class="qg-console__label" data-mono>{{ studyMode === 'answer' ? 'Source' : 'Chapter' }}</div>
          <div class="qg-source">
            <div v-if="studyMode === 'answer'" class="qg-segment" role="tablist" aria-label="出题源">
              <button role="tab" :aria-selected="practiceMode === 'random'" class="qg-segment__btn" @click="setMode('random')">Random</button>
              <button role="tab" :aria-selected="practiceMode === 'topic'" class="qg-segment__btn" @click="setMode('topic')">Topic</button>
            </div>
            <div v-if="studyMode !== 'answer' || practiceMode === 'topic'" class="qg-topicpick">
              <button class="qg-topicpick__btn" @click="showTopicDropdown = !showTopicDropdown">
                <span class="qg-topicpick__name">{{ selectedTopic === 'all' ? '选择章节' : formatTopicName(selectedTopic) }}</span>
                <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M6 9l6 6 6-6"/></svg>
              </button>
              <div v-if="showTopicDropdown" class="qg-menu qg-menu--topic">
                <button
                  v-for="topic in availableTopics"
                  :key="topic"
                  class="qg-menu__row qg-menu__row--compact"
                  :data-active="selectedTopic === topic"
                  @click="selectTopicFromDropdown(topic)"
                >
                  <span>{{ formatTopicName(topic) }}</span>
                  <span v-if="studyMode !== 'raw'" class="qg-num qg-menu__count">{{ topicCount(topic) }}</span>
                </button>
              </div>
            </div>
          </div>
        </div>

        <!-- Difficulty: questions only -->
        <div v-if="studyMode === 'answer'" class="qg-console__group qg-console__group--right">
          <div class="qg-console__label" data-mono>Difficulty</div>
          <div class="qg-difficulty">
            <button
              v-for="diff in difficultyOptions"
              :key="diff.value"
              class="qg-difficulty__btn"
              :data-active="selectedDifficulty === diff.value"
              :data-level="diff.value"
              @click="setDifficulty(diff.value)"
            >
              <span class="qg-difficulty__dot"></span>
              <span class="qg-difficulty__label">{{ diff.value }}</span>
            </button>
          </div>
        </div>
      </div>
    </section>

    <!-- Outside-click overlay -->
    <div
      v-if="showCourseDropdown || showTopicDropdown"
      class="qg-veil"
      @click="showCourseDropdown = false; showTopicDropdown = false"
    ></div>

    <!-- ─── Stage ─── -->
    <main class="qg-stage" @mouseup="onStageMouseUp">
      <!-- Notes mode: structured knowledge points -->
      <div v-if="studyMode === 'notes'" class="qg-stage__inner">
        <NotesView
          :course-id="currentCourseId"
          :topic="selectedTopic === 'all' ? null : selectedTopic"
        />
      </div>

      <!-- Raw courseware mode: source markdown for the chapter -->
      <div v-else-if="studyMode === 'raw'" class="qg-stage__inner">
        <CoursewareView
          :course-id="currentCourseId"
          :topic="selectedTopic === 'all' ? null : selectedTopic"
        />
      </div>

      <div v-else-if="loading" class="qg-stage__inner">
        <QuestionSkeleton />
        <p class="qg-stage__loading">{{ loadingMessage }}</p>
      </div>

      <div v-else-if="error" class="qg-stage__inner">
        <div class="qg-card qg-empty">
          <div class="qg-empty__heading">出错了</div>
          <p class="qg-empty__body">{{ error }}</p>
          <button class="qg-btn qg-btn--primary" @click="retryGenerate">重试</button>
        </div>
      </div>

      <div v-else-if="currentQuestion" class="qg-stage__inner">
        <QuestionCard
          ref="cardRef"
          :key="`${currentQuestion.id}-${studyMode}`"
          :question="currentQuestion"
          :question-number="historyQuestions.length + 1"
          :mode="studyMode"
          @next="moveToNextQuestion"
          @answered="onAnswered"
        />
        <div v-if="prefetching" class="qg-prefetch">
          <span class="qg-prefetch__dot"></span>
          <span data-mono>Pre-generating next…</span>
        </div>
      </div>

      <div v-else class="qg-stage__inner">
        <div class="qg-card qg-empty">
          <div class="qg-empty__heading">准备开始</div>
          <p class="qg-empty__body">正在加载第一道题目…</p>
        </div>
      </div>
    </main>

    <!-- ─── History drawer ─── -->
    <transition name="qg-drawer">
      <div v-if="showHistory" class="qg-drawer">
        <div class="qg-drawer__veil" @click="showHistory = false"></div>
        <aside class="qg-drawer__panel">
          <header class="qg-drawer__head">
            <div>
              <div class="qg-eyebrow" data-mono>History</div>
              <h2 class="qg-drawer__title">答题历史</h2>
            </div>
            <button class="qg-iconbtn" @click="showHistory = false" title="关闭">
              <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round"><path d="M6 6l12 12M18 6L6 18"/></svg>
            </button>
          </header>
          <div class="qg-drawer__body">
            <div
              v-for="(item, index) in [...historyQuestions].reverse()"
              :key="item.id"
              class="qg-history__item"
              :data-correct="item.correct"
              @click="viewHistoryItem(item)"
            >
              <div class="qg-history__head">
                <span class="qg-pill" :data-tint="item.correct ? 'success' : 'danger'">{{ item.correct ? 'Correct' : 'Incorrect' }}</span>
                <span class="qg-num qg-history__index">#{{ historyQuestions.length - index }}</span>
              </div>
              <p class="qg-history__preview">{{ item.question.question_text }}</p>
            </div>
            <div v-if="historyQuestions.length === 0" class="qg-history__empty">
              暂无答题记录
            </div>
          </div>
          <footer v-if="historyQuestions.length > 0" class="qg-drawer__foot">
            <button class="qg-btn qg-btn--quiet" @click="clearHistory">清空记录</button>
          </footer>
        </aside>
      </div>
    </transition>

    <!-- History detail — floating card with left/right pagination -->
    <transition name="qg-modal-pop">
      <div v-if="historyIndex !== null" class="qg-history-modal">
        <div class="qg-history-modal__veil" @click="closeHistoryDetail"></div>

        <!-- Side-flanking nav buttons (desktop) -->
        <button
          class="qg-history-modal__navside qg-history-modal__navside--prev"
          :disabled="historyIndex === 0"
          @click="stepHistory(-1)"
          aria-label="上一题"
        >
          <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M15 18l-6-6 6-6"/></svg>
        </button>
        <button
          class="qg-history-modal__navside qg-history-modal__navside--next"
          :disabled="historyIndex >= historyQuestions.length - 1"
          @click="stepHistory(1)"
          aria-label="下一题"
        >
          <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M9 18l6-6-6-6"/></svg>
        </button>

        <div class="qg-history-modal__panel">
          <header class="qg-history-modal__head">
            <div class="qg-history-modal__crumb">
              <span class="qg-pill" :data-tint="currentHistoryItem?.correct ? 'success' : 'danger'">
                {{ currentHistoryItem?.correct ? 'Correct' : 'Incorrect' }}
              </span>
              <span class="qg-num qg-history-modal__pos">
                {{ String(historyIndex + 1).padStart(2, '0') }}
                <span class="qg-history-modal__posSep">/</span>
                {{ String(historyQuestions.length).padStart(2, '0') }}
              </span>
            </div>
            <div class="qg-history-modal__nav">
              <button class="qg-iconbtn" :disabled="historyIndex === 0" @click="stepHistory(-1)" aria-label="上一题">
                <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><path d="M15 18l-6-6 6-6"/></svg>
              </button>
              <button class="qg-iconbtn" :disabled="historyIndex >= historyQuestions.length - 1" @click="stepHistory(1)" aria-label="下一题">
                <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><path d="M9 18l6-6-6-6"/></svg>
              </button>
              <button class="qg-iconbtn" @click="closeHistoryDetail" aria-label="关闭">
                <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round"><path d="M6 6l12 12M18 6L6 18"/></svg>
              </button>
            </div>
          </header>

          <div class="qg-history-modal__body">
            <QuestionCard
              v-if="currentHistoryItem"
              :key="`hist-${historyIndex}-${currentHistoryItem.id}`"
              :question="currentHistoryItem.question"
              :question-number="historyIndex + 1"
              :loading="false"
              mode="memorize"
            />
          </div>

          <footer class="qg-history-modal__foot" data-mono>
            <span>← →  导航</span>
            <span class="qg-history-modal__footSep">·</span>
            <span>ESC  关闭</span>
          </footer>
        </div>
      </div>
    </transition>

    <!-- ─── AI Sidebar ─── -->
    <QgChatSidebar
      :open="showSidebar"
      :study-mode="studyMode"
      :course-id="currentCourseId"
      :topic="selectedTopic === 'all' ? null : selectedTopic"
      :current-question="currentQuestion"
      :question-answered="questionAnswered"
      :user-answer="userAnswer"
      :quoted-text="quotedText"
      @close="showSidebar = false"
      @clear-quote="quotedText = ''"
      @question-deleted="handleQuestionDeleted"
      @width-change="sidebarWidth = $event"
    />

    <!-- ─── Floating quote button ─── -->
    <teleport to="body">
      <transition name="qg-fade">
        <button
          v-if="showQuoteBtn"
          class="qg-quote-fab"
          :style="quoteBtnStyle"
          @mousedown.prevent.stop="quoteSelection"
        >
          <svg viewBox="0 0 24 24" width="13" height="13" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>
          Quote
        </button>
      </transition>
    </teleport>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount, watch } from 'vue';
import QuestionCard from '../components/QuestionCard.vue';
import QuestionSkeleton from '../components/QuestionSkeleton.vue';
import QgChatSidebar from '../components/QgChatSidebar.vue';
import QgThemeToggle from '../components/QgThemeToggle.vue';
import NotesView from '../components/NotesView.vue';
import CoursewareView from '../components/CoursewareView.vue';
import QgIcon from '../components/QgIcon.vue';
import { questionApi } from '../api';

// LocalStorage keys
const HISTORY_STORAGE_KEY = 'questiongen_history';
const SEEN_IDS_STORAGE_KEY = 'questiongen_seen_ids';
const SELECTED_TOPIC_KEY = 'questiongen_selected_topic';
const PRACTICE_MODE_KEY = 'questiongen_practice_mode';
const CURRENT_COURSE_KEY = 'questiongen_current_course';
const QUESTION_TYPE_KEY = 'questiongen_question_type';
const STUDY_MODE_KEY = 'questiongen_study_mode';

// Question type + study mode (背题/答题)
const QUESTION_TYPES = [
  { value: 'mcq', label: '选择题', icon: 'A·B' },
  { value: 'fill', label: '填空题', icon: '___' },
  { value: 'essay', label: '论述题', icon: '✍︎' },
];
const STUDY_MODES = [
  { value: 'answer', label: '答题', icon: 'target' },
  { value: 'notes',  label: '知识点', icon: 'note' },
  { value: 'raw',    label: '原文', icon: 'doc' },
];

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
// History detail — track an index into historyQuestions so the modal can
// page through them with ← / → keys or the side nav buttons.
const historyIndex = ref(null);
const currentHistoryItem = computed(() =>
  historyIndex.value !== null ? historyQuestions.value[historyIndex.value] || null : null
);
const cardRef = ref(null);
const error = ref(null);
const questionSource = ref('');
const questionAnswered = ref(false);
const userAnswer = ref(null);  // { selected: 'A. xxx', correct: true/false }

// Sidebar + text selection quoting
const showSidebar = ref(false);
const sidebarWidth = ref(380);
const quotedText = ref('');
const showQuoteBtn = ref(false);
const quoteBtnPos = ref({ x: 0, y: 0 });
const pendingQuoteText = ref('');

const quoteBtnStyle = computed(() => ({
  position: 'fixed',
  top: `${quoteBtnPos.value.y}px`,
  left: `${quoteBtnPos.value.x}px`,
  transform: 'translate(-50%, -100%)',
  zIndex: 9999,
}));

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
const notesTopicStats = ref({});  // chapter → knowledge-point count

// Topic dropdown count: switches between question count and notes count
// based on the active study mode.
function topicCount(topic) {
  if (studyMode.value === 'notes') return notesTopicStats.value[topic] || 0;
  return topicStats.value[topic] || 0;
}

// Question type + study mode
const selectedQuestionType = ref('mcq');
const studyMode = ref('answer');

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

// Question types this course supports — backend returns in course config.
// Default to ['mcq'] for any course that doesn't opt into fill/essay.
const courseSupportedTypes = computed(() =>
  Array.isArray(currentCourse.value.question_types) && currentCourse.value.question_types.length
    ? currentCourse.value.question_types
    : ['mcq']
);
const availableQuestionTypes = computed(() =>
  QUESTION_TYPES.filter(t => courseSupportedTypes.value.includes(t.value))
);

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

  // Snap selected question type back to mcq if the new course doesn't support
  // the previously chosen type (e.g. switching from software-engineering to
  // c-programming while on 'essay').
  if (!courseSupportedTypes.value.includes(selectedQuestionType.value)) {
    selectedQuestionType.value = 'mcq';
    localStorage.setItem(QUESTION_TYPE_KEY, 'mcq');
  }

  // Clear current state
  prefetchedQuestion.value = null;
  seenQuestionIds.value = [];
  selectedTopic.value = 'all';

  // Reload topics and questions for new course
  await loadTopics();
  await loadStats();
  await loadNotesStats();

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

// Load knowledge-point counts per chapter (used by Topic dropdown in notes mode)
async function loadNotesStats() {
  try {
    const r = await questionApi.getNotesTopics(currentCourseId.value);
    const map = {};
    for (const t of (r.data?.topics || [])) {
      map[t.topic] = t.count || 0;
    }
    notesTopicStats.value = map;
  } catch (err) {
    console.error('Failed to load notes stats:', err);
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

        // L1, L2 ... L11 style — letter prefix + multi-digit lecture number
        const lectureMatch = str.match(/^[a-z](\d+)[-_]/i);
        if (lectureMatch) return parseInt(lectureMatch[1]);

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
    const qtypeStored = localStorage.getItem(QUESTION_TYPE_KEY);
    if (qtypeStored && QUESTION_TYPES.some(t => t.value === qtypeStored)) {
      selectedQuestionType.value = qtypeStored;
    }
    const studyStored = localStorage.getItem(STUDY_MODE_KEY);
    if (studyStored === 'memorize') {
      // 背题 mode was retired in favour of 知识点; migrate the stored value.
      studyMode.value = 'answer';
      localStorage.setItem(STUDY_MODE_KEY, 'answer');
    } else if (studyStored && STUDY_MODES.some(m => m.value === studyStored)) {
      studyMode.value = studyStored;
    }
  } catch (e) {
    console.error('Failed to load history from localStorage:', e);
  }
}

// Set question type and reload
async function setQuestionType(qtype) {
  if (qtype === selectedQuestionType.value) return;
  selectedQuestionType.value = qtype;
  localStorage.setItem(QUESTION_TYPE_KEY, qtype);
  prefetchedQuestion.value = null;
  loading.value = true;
  loadingMessage.value = `正在加载${QUESTION_TYPES.find(t => t.value === qtype)?.label || ''}...`;
  error.value = null;
  currentQuestion.value = await getSmartNextQuestion();
  loading.value = false;
  if (currentQuestion.value) prefetchNextQuestion();
}

// Set study mode (背题/答题) — no API call needed; just toggles UI
function setStudyMode(mode) {
  if (mode === studyMode.value) return;
  studyMode.value = mode;
  localStorage.setItem(STUDY_MODE_KEY, mode);
  // Reset answered state on mode swap so the card re-renders cleanly
  questionAnswered.value = false;
  userAnswer.value = null;
  cardRef.value?.reset?.();
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
      currentCourseId.value,
      selectedQuestionType.value
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
    const response = await questionApi.smartNext(combinedSeenIds, true, topicParam, null, currentCourseId.value, selectedQuestionType.value);
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

// View historical question detail — opens the paginated overlay
function viewHistoryItem(item) {
  const idx = historyQuestions.value.indexOf(item);
  if (idx >= 0) historyIndex.value = idx;
}
function stepHistory(delta) {
  if (historyIndex.value === null) return;
  const next = historyIndex.value + delta;
  if (next < 0 || next >= historyQuestions.value.length) return;
  historyIndex.value = next;
}
function closeHistoryDetail() {
  historyIndex.value = null;
}
function onHistoryKey(e) {
  if (historyIndex.value === null) return;
  if (e.key === 'Escape')      { e.preventDefault(); closeHistoryDetail(); }
  else if (e.key === 'ArrowLeft')  { e.preventDefault(); stepHistory(-1); }
  else if (e.key === 'ArrowRight') { e.preventDefault(); stepHistory(1);  }
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
  await loadNotesStats();
}

// ─── Text selection → quote ─────────────────────────────────────────
function onStageMouseUp(e) {
  if (e.target.closest('.qg-quote-fab')) return;
  const sel = window.getSelection();
  const text = sel?.toString().trim();
  if (text && text.length > 3) {
    const range = sel.getRangeAt(0);
    const rect = range.getBoundingClientRect();
    quoteBtnPos.value = {
      x: rect.left + rect.width / 2,
      y: rect.top - 6,
    };
    pendingQuoteText.value = text;
    showQuoteBtn.value = true;
  } else {
    showQuoteBtn.value = false;
  }
}

function quoteSelection() {
  quotedText.value = pendingQuoteText.value;
  pendingQuoteText.value = '';
  showQuoteBtn.value = false;
  showSidebar.value = true;
  window.getSelection()?.removeAllRanges();
}

function onDocMouseDown(e) {
  if (!e.target.closest('.qg-quote-fab')) {
    showQuoteBtn.value = false;
  }
}

function onWindowScroll() {
  if (showQuoteBtn.value) showQuoteBtn.value = false;
}

// Initial load
onMounted(async () => {
  loadHistoryFromStorage();
  window.addEventListener('keydown', onHistoryKey);
  document.addEventListener('mousedown', onDocMouseDown);
  window.addEventListener('scroll', onWindowScroll, true);

  // Load courses first
  await loadCourses();

  // If the persisted type isn't supported by the current course (e.g. a stale
  // 'essay' from a prior course), snap to mcq before fetching the first question.
  if (!courseSupportedTypes.value.includes(selectedQuestionType.value)) {
    selectedQuestionType.value = 'mcq';
    localStorage.setItem(QUESTION_TYPE_KEY, 'mcq');
  }

  // Then load topics and stats for the current course
  await loadTopics();
  await loadStats();
  await loadNotesStats();
  
  loading.value = true;
  loadingMessage.value = '正在加载题目...';
  
  currentQuestion.value = await getSmartNextQuestion();
  loading.value = false;
  
  if (currentQuestion.value) {
    prefetchNextQuestion();
  }
});

onBeforeUnmount(() => {
  window.removeEventListener('keydown', onHistoryKey);
  document.removeEventListener('mousedown', onDocMouseDown);
  window.removeEventListener('scroll', onWindowScroll, true);
});
</script>

<style scoped>
/* ─── Shell ─────────────────────────────────────────────────────────── */
.qg-shell {
  min-height: 100dvh;
  background: var(--qg-surface-base);
  color: var(--qg-text-primary);
  padding-bottom: env(safe-area-inset-bottom);
  transition: margin-right var(--qg-dur-slow) var(--qg-ease);
}
@media (max-width: 768px) {
  .qg-shell--sidebar { margin-right: 0 !important; }
}

/* ─── Topbar ────────────────────────────────────────────────────────── */
.qg-topbar {
  position: sticky;
  top: 0;
  z-index: 40;
  background: color-mix(in oklch, var(--qg-surface-base) 88%, transparent);
  backdrop-filter: saturate(160%) blur(12px);
  -webkit-backdrop-filter: saturate(160%) blur(12px);
  border-bottom: 1px solid var(--qg-border-default);
}
.qg-topbar__inner {
  max-width: 1080px;
  margin: 0 auto;
  padding: 12px clamp(16px, 4vw, 32px);
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}
.qg-topbar__left,
.qg-topbar__right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.qg-back {
  width: 32px;
  height: 32px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  color: var(--qg-text-secondary);
  border: 1px solid var(--qg-border-default);
  border-radius: var(--qg-radius-md);
  background: transparent;
  transition: color var(--qg-dur-fast) var(--qg-ease),
              border-color var(--qg-dur-fast) var(--qg-ease);
}
.qg-back:hover { color: var(--qg-text-primary); border-color: var(--qg-border-strong); }

.qg-wordmark {
  display: inline-flex;
  align-items: baseline;
  gap: 8px;
  font-family: var(--qg-font-mono);
  font-size: 12px;
  letter-spacing: 0.04em;
  color: var(--qg-text-secondary);
}
.qg-wordmark__brand { color: var(--qg-text-primary); font-weight: 500; }
.qg-wordmark__sep { color: var(--qg-text-muted); }
.qg-wordmark__page { text-transform: uppercase; }

.qg-session {
  display: inline-flex;
  flex-direction: column;
  align-items: flex-end;
  margin-right: 4px;
}
.qg-session__label {
  font-family: var(--qg-font-mono);
  font-size: 10px;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--qg-text-muted);
  line-height: 1;
  margin-bottom: 2px;
}
.qg-session__count {
  font-size: 13px;
  color: var(--qg-text-primary);
  font-weight: 500;
}
.qg-session__sep { color: var(--qg-text-muted); margin: 0 1px; }

.qg-iconbtn {
  width: 32px;
  height: 32px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  color: var(--qg-text-secondary);
  border: 1px solid var(--qg-border-default);
  border-radius: var(--qg-radius-md);
  cursor: pointer;
  transition: color var(--qg-dur-fast) var(--qg-ease),
              border-color var(--qg-dur-fast) var(--qg-ease),
              background var(--qg-dur-fast) var(--qg-ease);
}
.qg-iconbtn:hover {
  color: var(--qg-text-primary);
  border-color: var(--qg-border-strong);
  background: var(--qg-surface-sunken);
}
.qg-iconbtn[data-active="true"] {
  color: var(--qg-accent);
  border-color: var(--qg-accent);
  background: var(--qg-accent-soft);
}

/* ─── Hero ──────────────────────────────────────────────────────────── */
.qg-hero {
  border-bottom: 1px solid var(--qg-border-default);
}
.qg-hero__inner {
  max-width: 1080px;
  margin: 0 auto;
  padding: clamp(28px, 5vw, 56px) clamp(16px, 4vw, 32px) clamp(20px, 4vw, 36px);
}
.qg-eyebrow {
  font-size: 11px;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: var(--qg-text-tertiary);
  margin-bottom: 8px;
}

.qg-courseswitch { position: relative; }
.qg-courseswitch__trigger {
  display: inline-flex;
  align-items: baseline;
  gap: 12px;
  padding: 0;
  background: transparent;
  border: none;
  color: var(--qg-text-primary);
  cursor: pointer;
  text-align: left;
}
.qg-hero__title {
  font-size: var(--qg-text-display);
  font-weight: 500;
  font-family: var(--qg-font-display);
  line-height: 1.05;
  letter-spacing: -0.025em;
  margin: 0;
  color: var(--qg-text-primary);
  /* opsz axis (Bricolage Grotesque variable) — display optical size */
  font-variation-settings: 'opsz' 72;
}
.qg-courseswitch__chev {
  color: var(--qg-text-tertiary);
  transition: transform var(--qg-dur-base) var(--qg-ease),
              color var(--qg-dur-fast) var(--qg-ease);
  transform: translateY(-3px);
}
.qg-courseswitch__chev--open {
  transform: translateY(-3px) rotate(180deg);
  color: var(--qg-text-primary);
}
.qg-courseswitch__trigger:hover .qg-courseswitch__chev { color: var(--qg-text-primary); }

.qg-hero__meta {
  margin: 14px 0 0;
  font-size: var(--qg-text-sm);
  color: var(--qg-text-tertiary);
  display: flex;
  align-items: center;
  gap: 8px;
}
.qg-hero__dot { color: var(--qg-text-muted); }

/* Page-level mode tabs — primary navigation, sits in the hero */
.qg-modetabs {
  margin-top: 28px;
  display: inline-flex;
  gap: 0;
  border-bottom: 1px solid var(--qg-border-default);
}
.qg-modetabs__btn {
  position: relative;
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 12px 18px 14px;
  background: transparent;
  border: none;
  cursor: pointer;
  color: var(--qg-text-tertiary);
  font-size: var(--qg-text-base);
  font-weight: 500;
  letter-spacing: -0.005em;
  transition: color var(--qg-dur-fast) var(--qg-ease);
}
.qg-modetabs__btn:hover { color: var(--qg-text-secondary); }
.qg-modetabs__btn[aria-selected="true"] {
  color: var(--qg-text-primary);
}
.qg-modetabs__btn[aria-selected="true"]::after {
  content: "";
  position: absolute;
  left: 0;
  right: 0;
  bottom: -1px;
  height: 2px;
  background: var(--qg-accent);
  border-radius: 2px 2px 0 0;
}
.qg-modetabs__icon {
  opacity: 0.7;
  transition: opacity var(--qg-dur-fast) var(--qg-ease);
}
.qg-modetabs__btn[aria-selected="true"] .qg-modetabs__icon { opacity: 1; }
@media (max-width: 540px) {
  .qg-modetabs { margin-top: 22px; }
  .qg-modetabs__btn { padding: 10px 14px 12px; font-size: var(--qg-text-sm); }
}

.qg-menu {
  position: absolute;
  z-index: 50;
  background: var(--qg-surface-raised);
  border: 1px solid var(--qg-border-default);
  border-radius: var(--qg-radius-lg);
  box-shadow: var(--qg-shadow-2);
  padding: 6px;
  min-width: 280px;
  display: flex;
  flex-direction: column;
  gap: 2px;
  margin-top: 12px;
  animation: qg-menu-in var(--qg-dur-base) var(--qg-ease);
}
.qg-menu--course { left: 0; top: 100%; }
.qg-menu--topic { right: 0; top: 100%; max-height: 320px; overflow-y: auto; }

@keyframes qg-menu-in {
  from { opacity: 0; transform: translateY(-4px); }
  to   { opacity: 1; transform: translateY(0); }
}

.qg-menu__row {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  text-align: left;
  padding: 10px 12px;
  background: transparent;
  border: none;
  border-radius: var(--qg-radius-md);
  cursor: pointer;
  color: var(--qg-text-secondary);
  transition: background var(--qg-dur-fast) var(--qg-ease),
              color var(--qg-dur-fast) var(--qg-ease);
}
.qg-menu__row:hover {
  background: var(--qg-surface-sunken);
  color: var(--qg-text-primary);
}
.qg-menu__row[data-active="true"] {
  background: var(--qg-accent-soft);
  color: var(--qg-accent);
}
.qg-menu__title {
  font-size: var(--qg-text-base);
  font-weight: 500;
  letter-spacing: -0.005em;
}
.qg-menu__sub {
  font-size: var(--qg-text-xs);
  color: var(--qg-text-tertiary);
  margin-top: 2px;
  font-weight: 400;
}
.qg-menu__row--compact {
  flex-direction: row;
  justify-content: space-between;
  align-items: center;
  padding: 8px 10px;
  font-size: var(--qg-text-sm);
}
.qg-menu__count {
  font-size: 11px;
  color: var(--qg-text-tertiary);
  background: var(--qg-surface-sunken);
  padding: 2px 8px;
  border-radius: var(--qg-radius-pill);
}
.qg-menu__row[data-active="true"] .qg-menu__count {
  background: color-mix(in oklch, var(--qg-accent) 18%, transparent);
  color: var(--qg-accent);
}

/* ─── Console ───────────────────────────────────────────────────────── */
.qg-console {
  border-bottom: 1px solid var(--qg-border-default);
  background: var(--qg-surface-sunken);
}
.qg-console__inner {
  max-width: 1080px;
  margin: 0 auto;
  padding: 18px clamp(16px, 4vw, 32px);
  display: flex;
  flex-wrap: wrap;
  align-items: flex-end;
  gap: 24px 28px;
}
.qg-console__group {
  display: flex;
  flex-direction: column;
  gap: 7px;
  min-width: 0;
}
.qg-console__group--right { margin-left: auto; }
.qg-console__label {
  font-size: 10px;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: var(--qg-text-tertiary);
  line-height: 1;
}

/* Segmented controls already styled by qg-design-tokens; refine icon font */
.qg-segment__icon {
  font-size: 11px;
  letter-spacing: 0.05em;
  color: var(--qg-text-tertiary);
}
.qg-segment__btn[aria-selected="true"] .qg-segment__icon {
  color: var(--qg-text-primary);
}

.qg-source {
  display: flex;
  align-items: center;
  gap: 10px;
}
.qg-topicpick { position: relative; }
.qg-topicpick__btn {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 7px 12px 7px 14px;
  background: var(--qg-surface-raised);
  color: var(--qg-text-primary);
  border: 1px solid var(--qg-border-default);
  border-radius: var(--qg-radius-md);
  font-size: var(--qg-text-sm);
  font-weight: 500;
  cursor: pointer;
  letter-spacing: -0.005em;
  transition: border-color var(--qg-dur-fast) var(--qg-ease),
              color var(--qg-dur-fast) var(--qg-ease);
}
.qg-topicpick__btn:hover { border-color: var(--qg-border-strong); }
.qg-topicpick__name { max-width: 200px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }

/* Difficulty selector — replaces the traffic-light dots */
.qg-difficulty {
  display: inline-flex;
  gap: 4px;
}
.qg-difficulty__btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 10px;
  background: transparent;
  border: 1px solid transparent;
  border-radius: var(--qg-radius-md);
  cursor: pointer;
  color: var(--qg-text-tertiary);
  transition: color var(--qg-dur-fast) var(--qg-ease),
              background var(--qg-dur-fast) var(--qg-ease),
              border-color var(--qg-dur-fast) var(--qg-ease);
}
.qg-difficulty__btn:hover { color: var(--qg-text-primary); }
.qg-difficulty__dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: currentColor;
  opacity: 0.5;
  transition: opacity var(--qg-dur-fast) var(--qg-ease);
}
.qg-difficulty__label {
  font-family: var(--qg-font-mono);
  font-size: 11px;
  letter-spacing: 0.04em;
  text-transform: uppercase;
}
.qg-difficulty__btn[data-level="easy"] { color: var(--qg-diff-easy); }
.qg-difficulty__btn[data-level="medium"] { color: var(--qg-diff-medium); }
.qg-difficulty__btn[data-level="hard"] { color: var(--qg-diff-hard); }
.qg-difficulty__btn[data-active="true"] {
  background: color-mix(in oklch, currentColor 12%, transparent);
  border-color: color-mix(in oklch, currentColor 30%, transparent);
}
.qg-difficulty__btn[data-active="true"] .qg-difficulty__dot { opacity: 1; }

/* ─── Stage ─────────────────────────────────────────────────────────── */
.qg-stage {
  padding: clamp(28px, 5vw, 56px) clamp(16px, 4vw, 32px) 96px;
}
.qg-stage__inner {
  max-width: 720px;
  margin: 0 auto;
}
.qg-stage__loading {
  margin-top: 20px;
  text-align: center;
  font-size: var(--qg-text-sm);
  color: var(--qg-text-tertiary);
  font-family: var(--qg-font-mono);
  letter-spacing: 0.04em;
}

.qg-empty {
  padding: clamp(32px, 5vw, 56px);
  text-align: center;
}
.qg-empty__heading {
  font-family: var(--qg-font-display);
  font-size: var(--qg-text-xl);
  letter-spacing: -0.015em;
  color: var(--qg-text-primary);
  margin-bottom: 8px;
}
.qg-empty__body {
  color: var(--qg-text-secondary);
  font-size: var(--qg-text-base);
  margin-bottom: 24px;
}

.qg-prefetch {
  margin-top: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  font-size: 11px;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: var(--qg-text-tertiary);
}
.qg-prefetch__dot {
  width: 6px; height: 6px;
  border-radius: 50%;
  background: var(--qg-success);
  animation: qg-pulse 1.6s var(--qg-ease) infinite;
}
@keyframes qg-pulse {
  0%, 100% { opacity: 1; transform: scale(1); }
  50% { opacity: 0.4; transform: scale(0.85); }
}

/* ─── Veil for outside-click ────────────────────────────────────────── */
.qg-veil {
  position: fixed;
  inset: 0;
  z-index: 35;
}

/* ─── Drawer (history) ─────────────────────────────────────────────── */
.qg-drawer {
  position: fixed;
  inset: 0;
  z-index: 60;
  display: flex;
  justify-content: flex-end;
}
.qg-drawer__veil {
  position: absolute;
  inset: 0;
  background: var(--qg-surface-overlay);
  backdrop-filter: blur(2px);
}
.qg-drawer__panel {
  position: relative;
  width: 100%;
  max-width: 420px;
  background: var(--qg-surface-raised);
  border-left: 1px solid var(--qg-border-default);
  display: flex;
  flex-direction: column;
}
.qg-drawer__head {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  padding: 24px 24px 18px;
  border-bottom: 1px solid var(--qg-border-default);
}
.qg-drawer__title {
  font-family: var(--qg-font-display);
  font-size: var(--qg-text-xl);
  font-weight: 500;
  margin: 0;
  letter-spacing: -0.02em;
  color: var(--qg-text-primary);
}
.qg-drawer__body {
  flex: 1;
  overflow-y: auto;
  padding: 16px 24px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.qg-drawer__foot {
  border-top: 1px solid var(--qg-border-default);
  padding: 12px 24px;
  display: flex;
  justify-content: flex-end;
}

.qg-history__item {
  padding: 12px 14px;
  background: var(--qg-surface-sunken);
  border: 1px solid var(--qg-border-default);
  border-radius: var(--qg-radius-md);
  cursor: pointer;
  transition: background var(--qg-dur-fast) var(--qg-ease),
              border-color var(--qg-dur-fast) var(--qg-ease);
}
.qg-history__item:hover {
  background: var(--qg-surface-raised);
  border-color: var(--qg-border-strong);
}
.qg-history__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 6px;
}
.qg-history__index {
  font-size: 11px;
  color: var(--qg-text-tertiary);
}
.qg-history__preview {
  font-size: var(--qg-text-sm);
  color: var(--qg-text-secondary);
  line-height: 1.5;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  margin: 0;
}
.qg-history__empty {
  text-align: center;
  padding: 40px 0;
  color: var(--qg-text-tertiary);
  font-size: var(--qg-text-sm);
}

/* Drawer transition */
.qg-drawer-enter-active .qg-drawer__panel,
.qg-drawer-leave-active .qg-drawer__panel {
  transition: transform var(--qg-dur-slow) var(--qg-ease);
}
.qg-drawer-enter-from .qg-drawer__panel,
.qg-drawer-leave-to .qg-drawer__panel {
  transform: translateX(100%);
}
.qg-drawer-enter-active .qg-drawer__veil,
.qg-drawer-leave-active .qg-drawer__veil {
  transition: opacity var(--qg-dur-slow) var(--qg-ease);
}
.qg-drawer-enter-from .qg-drawer__veil,
.qg-drawer-leave-to .qg-drawer__veil {
  opacity: 0;
}

/* ─── History detail modal (paginated floating card) ───────────────── */
.qg-history-modal {
  position: fixed;
  inset: 0;
  z-index: 70;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: clamp(12px, 3vw, 28px);
}
.qg-history-modal__veil {
  position: absolute;
  inset: 0;
  background: var(--qg-surface-overlay);
  backdrop-filter: blur(6px);
  -webkit-backdrop-filter: blur(6px);
}

/* Side-flanking large nav buttons (desktop only) */
.qg-history-modal__navside {
  position: absolute;
  top: 50%;
  transform: translateY(-50%);
  width: 44px;
  height: 44px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: var(--qg-surface-raised);
  color: var(--qg-text-secondary);
  border: 1px solid var(--qg-border-default);
  border-radius: 50%;
  cursor: pointer;
  z-index: 2;
  box-shadow: var(--qg-shadow-1);
  transition: color var(--qg-dur-fast) var(--qg-ease),
              border-color var(--qg-dur-fast) var(--qg-ease),
              transform var(--qg-dur-fast) var(--qg-ease),
              opacity var(--qg-dur-fast) var(--qg-ease);
}
.qg-history-modal__navside:hover:not(:disabled) {
  color: var(--qg-text-primary);
  border-color: var(--qg-border-strong);
  transform: translateY(-50%) scale(1.06);
}
.qg-history-modal__navside:disabled {
  opacity: 0.3;
  cursor: not-allowed;
}
.qg-history-modal__navside--prev { left: clamp(8px, 4vw, 40px); }
.qg-history-modal__navside--next { right: clamp(8px, 4vw, 40px); }
@media (max-width: 720px) {
  .qg-history-modal__navside { display: none; }
}

/* The card itself */
.qg-history-modal__panel {
  position: relative;
  width: 100%;
  max-width: 720px;
  max-height: 86vh;
  background: var(--qg-surface-raised);
  border: 1px solid var(--qg-border-default);
  border-radius: var(--qg-radius-xl);
  box-shadow: var(--qg-shadow-2);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}
.qg-history-modal__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 14px 18px;
  border-bottom: 1px solid var(--qg-border-default);
  background: var(--qg-surface-base);
}
.qg-history-modal__crumb {
  display: inline-flex;
  align-items: center;
  gap: 12px;
}
.qg-history-modal__pos {
  font-size: 12px;
  color: var(--qg-text-secondary);
  letter-spacing: 0.04em;
  font-variant-numeric: tabular-nums;
}
.qg-history-modal__posSep {
  color: var(--qg-text-muted);
  margin: 0 2px;
}
.qg-history-modal__nav {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}
.qg-history-modal__nav .qg-iconbtn:disabled {
  opacity: 0.35;
  cursor: not-allowed;
  pointer-events: none;
}

.qg-history-modal__body {
  flex: 1;
  overflow-y: auto;
  padding: 18px clamp(14px, 3vw, 28px);
}
/* Strip the inner question card border so it sits flat inside the modal */
.qg-history-modal__body :deep(.qg-card) {
  border: none;
  box-shadow: none;
  background: transparent;
  padding: 0;
}

.qg-history-modal__foot {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 10px 16px;
  border-top: 1px solid var(--qg-border-default);
  background: var(--qg-surface-base);
  font-size: 10.5px;
  letter-spacing: 0.12em;
  color: var(--qg-text-tertiary);
}
.qg-history-modal__footSep { color: var(--qg-text-muted); }
@media (max-width: 540px) {
  .qg-history-modal__foot { display: none; }
}

/* Pop-in transition */
.qg-modal-pop-enter-active,
.qg-modal-pop-leave-active {
  transition: opacity var(--qg-dur-base) var(--qg-ease);
}
.qg-modal-pop-enter-active .qg-history-modal__panel,
.qg-modal-pop-leave-active .qg-history-modal__panel {
  transition: transform var(--qg-dur-base) var(--qg-ease),
              opacity var(--qg-dur-base) var(--qg-ease);
}
.qg-modal-pop-enter-from,
.qg-modal-pop-leave-to { opacity: 0; }
.qg-modal-pop-enter-from .qg-history-modal__panel,
.qg-modal-pop-leave-to .qg-history-modal__panel {
  transform: scale(0.96) translateY(8px);
  opacity: 0;
}

.qg-fade-enter-active,
.qg-fade-leave-active { transition: opacity var(--qg-dur-base) var(--qg-ease); }
.qg-fade-enter-from,
.qg-fade-leave-to { opacity: 0; }

/* ─── Responsive trims ──────────────────────────────────────────────── */
@media (max-width: 720px) {
  .qg-console__group--right { margin-left: 0; }
  .qg-session { display: none; }
  /* Topic dropdown: anchor to button's left edge so it doesn't overflow
     the viewport on narrow screens (button is near the left side). */
  .qg-menu--topic {
    left: 0;
    right: auto;
    min-width: 0;
    width: max-content;
    max-width: calc(100vw - 32px);
  }
  .qg-menu--course {
    min-width: 0;
    width: max-content;
    max-width: calc(100vw - 32px);
  }
}

/* Below 540px: TYPE segment falls back to icons only (still legible);
   MODE keeps Chinese label since 答/背 is the meaning, no icon to fall back on.  */
@media (max-width: 540px) {
  .qg-console__inner { gap: 18px 20px; }
  /* Only TYPE segment's text label hides — its 'A·B / ___ / ✍︎' icons remain */
  .qg-console__group:nth-child(1) .qg-segment__txt { display: none; }
  .qg-console__group:nth-child(1) .qg-segment__btn { padding: 6px 10px; }
  /* Difficulty: shorten labels via uppercase initials (handled by CSS pseudo) */
  .qg-difficulty__label { display: none; }
  .qg-difficulty__btn { padding: 6px 8px; }
  .qg-difficulty__btn::after {
    font-family: var(--qg-font-mono);
    font-size: 11px;
    letter-spacing: 0.04em;
    text-transform: uppercase;
  }
  .qg-difficulty__btn[data-level="easy"]::after   { content: "E"; }
  .qg-difficulty__btn[data-level="medium"]::after { content: "M"; }
  .qg-difficulty__btn[data-level="hard"]::after   { content: "H"; }
  .qg-wordmark__page { display: none; }
}

@media (max-width: 380px) {
  .qg-console__inner { flex-direction: column; align-items: stretch; gap: 14px; }
  .qg-console__group--right { margin-left: 0; align-items: flex-start; }
  .qg-source { flex-direction: column; align-items: flex-start; gap: 8px; }
}

/* ─── Floating quote button ────────────────────────────────────────────── */
.qg-quote-fab {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 6px 12px;
  background: var(--qg-accent, oklch(0.46 0.13 252));
  color: var(--qg-accent-on, #fff);
  border: none;
  border-radius: 999px;
  font-family: var(--qg-font-mono, monospace);
  font-size: 11px;
  font-weight: 500;
  letter-spacing: 0.04em;
  cursor: pointer;
  box-shadow: 0 4px 12px rgba(0,0,0,0.15);
  user-select: none;
  -webkit-user-select: none;
  transition: transform 0.15s ease, box-shadow 0.15s ease;
  pointer-events: auto;
}
.qg-quote-fab:hover {
  transform: translate(-50%, -100%) scale(1.06);
  box-shadow: 0 6px 16px rgba(0,0,0,0.2);
}
</style>
