<template>
  <transition name="qg-sidebar-slide">
    <aside v-if="open" data-qg-surface class="qg-sidebar" :style="{ width: sidebarWidth + 'px' }">
      <!-- Resize handle -->
      <div class="qg-sidebar__resize" @mousedown.prevent="startResize"></div>

      <!-- Header -->
      <header class="qg-sidebar__head">
        <div class="qg-sidebar__headLeft">
          <svg class="qg-sidebar__headIcon" viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">
            <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
          </svg>
          <span class="qg-sidebar__headTitle">AI Assistant</span>
        </div>
        <div class="qg-sidebar__headRight">
          <button
            v-if="activeTab === 'chat' && messages.length > 0"
            class="qg-iconbtn qg-sidebar__archiveBtn"
            :disabled="archiveSaving"
            @click="archiveSession"
            title="存档会话"
          >
            <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"/><polyline points="17 21 17 13 7 13 7 21"/><polyline points="7 3 7 8 15 8"/></svg>
          </button>
          <button class="qg-iconbtn" @click="$emit('close')" title="关闭">
            <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round"><path d="M6 6l12 12M18 6L6 18"/></svg>
          </button>
        </div>
      </header>

      <!-- Tabs -->
      <nav class="qg-sidebar__tabs" role="tablist">
        <button
          role="tab"
          :aria-selected="activeTab === 'chat'"
          class="qg-sidebar__tab"
          @click="activeTab = 'chat'"
        >对话</button>
        <button
          role="tab"
          :aria-selected="activeTab === 'archive'"
          class="qg-sidebar__tab"
          @click="switchToArchive"
        >
          存档
          <span v-if="archiveNotes.length" class="qg-sidebar__tabBadge" data-mono>{{ archiveNotes.length }}</span>
        </button>
      </nav>

      <!-- ═══ Chat tab ═══ -->
      <template v-if="activeTab === 'chat'">
        <!-- Status -->
        <div class="qg-sidebar__status" :data-mode="effectiveMode">
          <span class="qg-sidebar__statusDot"></span>
          <span data-mono>{{ statusText }}</span>
          <div v-if="effectiveMode !== 'study'" class="qg-segment qg-sidebar__modeSeg">
            <button class="qg-segment__btn" :aria-selected="chatMode === 'qa'" @click="setChatMode('qa')">答疑</button>
            <button class="qg-segment__btn" :aria-selected="chatMode === 'review'" @click="setChatMode('review')">审核</button>
          </div>
        </div>

        <!-- Messages -->
        <div class="qg-sidebar__messages" ref="messagesRef" @scroll="onMessagesScroll">
          <div v-if="!messages.length && !streamingContent && !loading" class="qg-sidebar__empty">
            <svg class="qg-sidebar__emptyIcon" viewBox="0 0 24 24" width="28" height="28" fill="none" stroke="currentColor" stroke-width="1.2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
            </svg>
            <p class="qg-sidebar__emptyTitle">{{ emptyTitle }}</p>
            <p class="qg-sidebar__emptyBody">{{ emptyBody }}</p>
          </div>

          <div v-for="(msg, i) in messages" :key="i" class="qg-sidebar__msg" :data-role="msg.role">
            <div class="qg-sidebar__bubble" v-html="formatMessage(msg.content)"></div>
            <div v-if="msg.recommendDelete" class="qg-sidebar__deleteCard">
              <span>建议删除此题</span>
              <button class="qg-btn qg-btn--ghost qg-sidebar__deleteBtn" :disabled="deleteLoading" @click="requestDeletion">{{ deleteLoading ? '确认中...' : '确认删除' }}</button>
            </div>
          </div>

          <div v-if="streamingContent" class="qg-sidebar__msg" data-role="assistant">
            <div class="qg-sidebar__bubble">
              <span v-html="formatMessage(streamingContent)"></span>
              <span class="qg-sidebar__cursor"></span>
            </div>
          </div>

          <div v-if="loading && !streamingContent" class="qg-sidebar__msg" data-role="assistant">
            <div class="qg-sidebar__bubble">
              <span class="qg-sidebar__dots"><span></span><span></span><span></span></span>
            </div>
          </div>

          <div v-if="deleteResult" class="qg-sidebar__notice" :data-tone="deleteResult.deleted ? 'success' : 'danger'">
            <span>{{ deleteResult.deleted ? 'Question deleted' : 'Deletion rejected' }}</span>
            <button class="qg-sidebar__noticeDismiss" @click="deleteResult = null">&times;</button>
          </div>
        </div>

        <!-- Scroll-to-bottom indicator -->
        <transition name="qg-fade">
          <button v-if="userScrolledUp && (streamingContent || loading)" class="qg-sidebar__scrollDown" @click="forceScrollBottom">
            <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M6 9l6 6 6-6"/></svg>
          </button>
        </transition>

        <!-- Quote preview -->
        <transition name="qg-quote-slide">
          <div v-if="quotedText" class="qg-sidebar__quote">
            <div class="qg-sidebar__quoteHead">
              <span class="qg-sidebar__quoteLabel" data-mono>QUOTED</span>
              <button class="qg-sidebar__quoteDismiss" @click="$emit('clear-quote')">&times;</button>
            </div>
            <p class="qg-sidebar__quoteText">{{ truncatedQuote }}</p>
          </div>
        </transition>

        <!-- Archive saved toast -->
        <transition name="qg-fade">
          <div v-if="archiveToast" class="qg-sidebar__toast">Saved to archive</div>
        </transition>

        <!-- Input -->
        <footer class="qg-sidebar__foot">
          <div class="qg-sidebar__inputWrap" :class="{ 'qg-sidebar__inputWrap--focus': inputFocused }">
            <textarea
              ref="inputRef"
              v-model="inputText"
              @focus="inputFocused = true"
              @blur="inputFocused = false"
              @compositionstart="isComposing = true"
              @compositionend="isComposing = false"
              @keydown.enter.exact="handleEnter"
              @input="autoResize"
              :placeholder="inputPlaceholder"
              rows="1"
              class="qg-sidebar__input"
              :disabled="loading || inputDisabled"
            ></textarea>
            <button class="qg-sidebar__send" :disabled="!inputText.trim() || loading || inputDisabled" @click="sendMessage">
              <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                <path d="M22 2L11 13M22 2l-7 20-4-9-9-4 20-7z"/>
              </svg>
            </button>
          </div>
        </footer>
      </template>

      <!-- ═══ Archive tab ═══ -->
      <template v-else>
        <!-- Viewing a single note -->
        <template v-if="selectedNote">
          <div class="qg-sidebar__noteHead">
            <button class="qg-iconbtn" @click="selectedNote = null" title="返回列表">
              <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><path d="M15 18l-6-6 6-6"/></svg>
            </button>
            <div class="qg-sidebar__noteHeadInfo">
              <span class="qg-sidebar__noteHeadTitle">{{ selectedNote.title }}</span>
              <span class="qg-sidebar__noteHeadMeta" data-mono>{{ formatDate(selectedNote.created_at) }}</span>
            </div>
            <button class="qg-iconbtn" @click="deleteNote(selectedNote.id)" title="删除">
              <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/></svg>
            </button>
          </div>
          <div class="qg-sidebar__messages qg-sidebar__noteBody">
            <div v-for="(msg, i) in selectedNote.messages" :key="i" class="qg-sidebar__msg" :data-role="msg.role">
              <div class="qg-sidebar__bubble" v-html="formatMessage(msg.content)"></div>
            </div>
          </div>
        </template>

        <!-- Notes list -->
        <template v-else>
          <div class="qg-sidebar__archiveList" v-if="archiveNotes.length">
            <div
              v-for="note in archiveNotes"
              :key="note.id"
              class="qg-sidebar__noteItem"
              @click="selectedNote = note"
            >
              <div class="qg-sidebar__noteItemHead">
                <span class="qg-sidebar__noteItemTitle">{{ note.title }}</span>
                <button class="qg-sidebar__noteItemDel" @click.stop="deleteNote(note.id)" title="删除">
                  <svg viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"><path d="M6 6l12 12M18 6L6 18"/></svg>
                </button>
              </div>
              <div class="qg-sidebar__noteItemMeta" data-mono>
                <span>{{ note.topic || 'general' }}</span>
                <span>{{ formatDate(note.created_at) }}</span>
                <span>{{ note.messages?.length || 0 }} msgs</span>
              </div>
              <p class="qg-sidebar__noteItemPreview">{{ notePreview(note) }}</p>
            </div>
          </div>
          <div v-else class="qg-sidebar__empty">
            <svg class="qg-sidebar__emptyIcon" viewBox="0 0 24 24" width="28" height="28" fill="none" stroke="currentColor" stroke-width="1.2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"/><polyline points="17 21 17 13 7 13 7 21"/><polyline points="7 3 7 8 15 8"/>
            </svg>
            <p class="qg-sidebar__emptyTitle">No saved notes</p>
            <p class="qg-sidebar__emptyBody">Archive a chat session to save it here for later review.</p>
          </div>
        </template>
      </template>
    </aside>
  </transition>
</template>

<script setup>
import { ref, computed, watch, nextTick, onMounted } from 'vue';
import { questionApi } from '../api';
import { marked } from 'marked';

marked.use({ breaks: true, gfm: true });

const MIN_WIDTH = 300;
const MAX_WIDTH = 560;
const WIDTH_STORAGE_KEY = 'qg_sidebar_width';

const props = defineProps({
  open: { type: Boolean, default: false },
  studyMode: { type: String, default: 'answer' },
  courseId: { type: String, default: null },
  topic: { type: String, default: null },
  currentQuestion: { type: Object, default: null },
  questionAnswered: { type: Boolean, default: false },
  userAnswer: { type: Object, default: null },
  quotedText: { type: String, default: '' },
});

const emit = defineEmits(['close', 'clear-quote', 'question-deleted', 'width-change']);

// ─── Core state ──────────────────────────────────────────────────────
const chatMode = ref('qa');
const messages = ref([]);
const inputText = ref('');
const inputFocused = ref(false);
const isComposing = ref(false);
const loading = ref(false);
const streamingContent = ref('');
const deleteLoading = ref(false);
const deleteResult = ref(null);
const messagesRef = ref(null);
const inputRef = ref(null);

// ─── Tabs ────────────────────────────────────────────────────────────
const activeTab = ref('chat');

// ─── Smart scroll ────────────────────────────────────────────────────
const userScrolledUp = ref(false);

// ─── Resize ──────────────────────────────────────────────────────────
const sidebarWidth = ref(parseInt(localStorage.getItem(WIDTH_STORAGE_KEY)) || 380);

// ─── Archive ─────────────────────────────────────────────────────────
const archiveNotes = ref([]);
const selectedNote = ref(null);
const archiveSaving = ref(false);
const archiveToast = ref(false);

// ─── Computed ────────────────────────────────────────────────────────
const effectiveMode = computed(() => {
  if (props.studyMode === 'notes' || props.studyMode === 'raw') return 'study';
  return chatMode.value;
});

const inputDisabled = computed(() => {
  if (props.studyMode === 'answer' && !props.questionAnswered) return true;
  return false;
});

const statusText = computed(() => {
  if (effectiveMode.value === 'study') return 'Study';
  if (effectiveMode.value === 'review') return 'Review';
  return 'Q&A';
});

const emptyTitle = computed(() => {
  if (effectiveMode.value === 'study') return 'Study Assistant';
  if (effectiveMode.value === 'review') return 'Question Reviewer';
  return 'AI Tutor';
});

const emptyBody = computed(() => {
  if (props.studyMode === 'answer' && !props.questionAnswered) {
    return 'Answer the question first, then ask me anything about it.';
  }
  if (effectiveMode.value === 'study') {
    return 'Select text from the content to quote, or ask any question about this topic.';
  }
  if (effectiveMode.value === 'review') {
    return 'Found an issue with this question? Tell me what looks wrong.';
  }
  return 'Have questions about this topic? Ask away.';
});

const inputPlaceholder = computed(() => {
  if (inputDisabled.value) return 'Answer the question first...';
  if (props.quotedText) return 'Ask about the quoted text...';
  return 'Ask a question...';
});

const truncatedQuote = computed(() => {
  const t = props.quotedText || '';
  return t.length > 120 ? t.slice(0, 120) + '...' : t;
});

// ─── Watchers ────────────────────────────────────────────────────────
watch(() => chatMode.value, () => {
  messages.value = [];
  deleteResult.value = null;
  streamingContent.value = '';
});

watch(() => props.currentQuestion?.id, () => {
  if (props.studyMode === 'answer') {
    messages.value = [];
    deleteResult.value = null;
    streamingContent.value = '';
  }
});

watch(() => [props.studyMode, props.topic], () => {
  if (props.studyMode !== 'answer') {
    messages.value = [];
    streamingContent.value = '';
  }
});

watch(() => props.questionAnswered, (val) => {
  if (!val && props.studyMode === 'answer') {
    messages.value = [];
    streamingContent.value = '';
  }
});

// Emit width on mount and change
watch(sidebarWidth, (w) => emit('width-change', w), { immediate: true });

// Focus input when quote arrives
watch(() => props.quotedText, (val) => {
  if (val) {
    activeTab.value = 'chat';
    nextTick(() => inputRef.value?.focus());
  }
});

// ─── Smart scroll ────────────────────────────────────────────────────
function onMessagesScroll() {
  const el = messagesRef.value;
  if (!el) return;
  const atBottom = el.scrollHeight - el.scrollTop - el.clientHeight < 48;
  userScrolledUp.value = !atBottom;
}

function scrollToBottom() {
  if (userScrolledUp.value) return;
  nextTick(() => {
    if (messagesRef.value) {
      messagesRef.value.scrollTop = messagesRef.value.scrollHeight;
    }
  });
}

function forceScrollBottom() {
  userScrolledUp.value = false;
  nextTick(() => {
    if (messagesRef.value) {
      messagesRef.value.scrollTop = messagesRef.value.scrollHeight;
    }
  });
}

watch([messages, streamingContent], scrollToBottom, { deep: true });

// ─── Resize ──────────────────────────────────────────────────────────
function startResize(e) {
  const startX = e.clientX;
  const startW = sidebarWidth.value;
  document.body.style.cursor = 'col-resize';
  document.body.style.userSelect = 'none';

  function onMove(ev) {
    const delta = startX - ev.clientX;
    sidebarWidth.value = Math.min(MAX_WIDTH, Math.max(MIN_WIDTH, startW + delta));
  }
  function onUp() {
    document.removeEventListener('mousemove', onMove);
    document.removeEventListener('mouseup', onUp);
    document.body.style.cursor = '';
    document.body.style.userSelect = '';
    localStorage.setItem(WIDTH_STORAGE_KEY, sidebarWidth.value);
  }
  document.addEventListener('mousemove', onMove);
  document.addEventListener('mouseup', onUp);
}

// ─── Formatting ──────────────────────────────────────────────────────
function formatMessage(text) {
  if (!text) return '';
  const clean = text
    .replace(/\[RECOMMENDATION: DELETE\]/g, '')
    .replace(/\[CONFIRMED: DELETE\]/g, '')
    .replace(/\[REJECTED: KEEP\]/g, '');
  try { return marked.parse(clean); }
  catch { return clean; }
}

// ─── Input ───────────────────────────────────────────────────────────
function handleEnter(e) {
  if (isComposing.value) return;
  e.preventDefault();
  sendMessage();
}

function autoResize() {
  const el = inputRef.value;
  if (!el) return;
  el.style.height = 'auto';
  el.style.height = Math.min(el.scrollHeight, 120) + 'px';
}

function setChatMode(m) { chatMode.value = m; }

// ─── Send message ────────────────────────────────────────────────────
async function sendMessage() {
  if (!inputText.value.trim() || loading.value || inputDisabled.value) return;

  let userContent = inputText.value.trim();

  if (props.quotedText) {
    const quoteLine = props.quotedText.split('\n').map(l => `> ${l}`).join('\n');
    userContent = `${quoteLine}\n\n${userContent}`;
    emit('clear-quote');
  }

  messages.value.push({ role: 'user', content: userContent });
  inputText.value = '';
  nextTick(autoResize);
  loading.value = true;
  streamingContent.value = '';
  userScrolledUp.value = false;

  try {
    let config;

    if (effectiveMode.value === 'study') {
      const context = { topic: props.topic, quoted_text: props.quotedText || '' };
      config = questionApi.getStudyChatStreamConfig(messages.value, context, props.courseId);
    } else {
      const questionData = {
        id: props.currentQuestion?.id,
        topic: props.currentQuestion?.topic,
        question_text: props.currentQuestion?.question_text,
        options: props.currentQuestion?.options,
        answer: props.currentQuestion?.answer,
        explanation: props.currentQuestion?.explanation,
        user_selected: props.userAnswer?.selected || null,
        user_correct: props.userAnswer?.correct ?? null,
      };
      config = questionApi.getChatStreamConfig(chatMode.value, messages.value, questionData, props.courseId);
    }

    const response = await fetch(config.url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(config.data),
    });

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let fullResponse = '';
    let recommendDelete = false;

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      const lines = decoder.decode(value).split('\n');
      for (const line of lines) {
        if (!line.startsWith('data: ')) continue;
        try {
          const data = JSON.parse(line.slice(6));
          if (data.error) throw new Error(data.error);
          if (data.chunk) {
            fullResponse += data.chunk;
            streamingContent.value = fullResponse;
          }
          if (data.done) recommendDelete = data.recommend_delete || false;
        } catch { /* partial chunk */ }
      }
    }

    streamingContent.value = '';
    messages.value.push({ role: 'assistant', content: fullResponse, recommendDelete });
  } catch (err) {
    streamingContent.value = '';
    messages.value.push({ role: 'assistant', content: 'Error: ' + err.message });
  } finally {
    loading.value = false;
  }
}

// ─── Deletion ────────────────────────────────────────────────────────
async function requestDeletion() {
  if (!props.currentQuestion?.id) return;
  deleteLoading.value = true;
  try {
    const r = await questionApi.requestDelete(props.currentQuestion.id, messages.value);
    deleteResult.value = r.data;
    if (r.data.deleted) emit('question-deleted', props.currentQuestion.id);
  } catch (err) {
    deleteResult.value = { deleted: false, reasoning: err.message };
  } finally {
    deleteLoading.value = false;
  }
}

// ─── Archive ─────────────────────────────────────────────────────────
async function loadArchive() {
  try {
    const r = await questionApi.getChatNotes(props.courseId);
    archiveNotes.value = r.data?.results || r.data || [];
  } catch { archiveNotes.value = []; }
}

function switchToArchive() {
  activeTab.value = 'archive';
  selectedNote.value = null;
  loadArchive();
}

async function archiveSession() {
  if (!messages.value.length || archiveSaving.value) return;
  archiveSaving.value = true;
  try {
    const firstUserMsg = messages.value.find(m => m.role === 'user');
    const title = (firstUserMsg?.content || 'Chat session').replace(/^>.*\n+/gm, '').trim().slice(0, 80) || 'Chat session';
    await questionApi.saveChatNote({
      course_id: props.courseId || '',
      topic: props.topic || '',
      title,
      messages: messages.value.map(m => ({ role: m.role, content: m.content })),
      study_mode: props.studyMode,
    });
    archiveToast.value = true;
    setTimeout(() => { archiveToast.value = false; }, 2000);
    loadArchive();
  } catch (err) {
    console.error('Failed to archive:', err);
  } finally {
    archiveSaving.value = false;
  }
}

async function deleteNote(id) {
  try {
    await questionApi.deleteChatNote(id);
    archiveNotes.value = archiveNotes.value.filter(n => n.id !== id);
    if (selectedNote.value?.id === id) selectedNote.value = null;
  } catch (err) {
    console.error('Failed to delete note:', err);
  }
}

function notePreview(note) {
  const first = note.messages?.find(m => m.role === 'user');
  const text = (first?.content || '').replace(/^>.*$/gm, '').trim();
  return text.length > 100 ? text.slice(0, 100) + '...' : text;
}

function formatDate(iso) {
  if (!iso) return '';
  const d = new Date(iso);
  const m = String(d.getMonth() + 1).padStart(2, '0');
  const day = String(d.getDate()).padStart(2, '0');
  const h = String(d.getHours()).padStart(2, '0');
  const min = String(d.getMinutes()).padStart(2, '0');
  return `${m}-${day} ${h}:${min}`;
}

onMounted(loadArchive);

defineExpose({ focusInput: () => nextTick(() => inputRef.value?.focus()) });
</script>

<style scoped>
/* ─── Sidebar shell ───────────────────────────────────────────────────── */
.qg-sidebar {
  position: fixed;
  top: 0;
  right: 0;
  bottom: 0;
  z-index: 50;
  display: flex;
  flex-direction: column;
  background: var(--qg-surface-base);
  border-left: 1px solid var(--qg-border-default);
  box-shadow: var(--qg-shadow-2);
}

/* Subtle scrollbar for ALL scrollable areas inside sidebar */
.qg-sidebar ::-webkit-scrollbar { width: 4px; }
.qg-sidebar ::-webkit-scrollbar-track { background: transparent; }
.qg-sidebar ::-webkit-scrollbar-thumb {
  background: color-mix(in oklch, var(--qg-text-muted) 40%, transparent);
  border-radius: 4px;
}
.qg-sidebar ::-webkit-scrollbar-thumb:hover {
  background: var(--qg-text-muted);
}
.qg-sidebar * { scrollbar-width: thin; scrollbar-color: color-mix(in oklch, var(--qg-text-muted) 40%, transparent) transparent; }

/* ─── Resize handle ───────────────────────────────────────────────────── */
.qg-sidebar__resize {
  position: absolute;
  left: -3px;
  top: 0;
  bottom: 0;
  width: 6px;
  cursor: col-resize;
  z-index: 2;
}
.qg-sidebar__resize::after {
  content: "";
  position: absolute;
  left: 2px;
  top: 0;
  bottom: 0;
  width: 2px;
  background: transparent;
  transition: background var(--qg-dur-fast) var(--qg-ease);
}
.qg-sidebar__resize:hover::after {
  background: var(--qg-accent);
}

/* ─── Slide transition ────────────────────────────────────────────────── */
.qg-sidebar-slide-enter-active,
.qg-sidebar-slide-leave-active {
  transition: transform var(--qg-dur-slow) var(--qg-ease);
}
.qg-sidebar-slide-enter-from,
.qg-sidebar-slide-leave-to {
  transform: translateX(100%);
}

/* ─── Header ──────────────────────────────────────────────────────────── */
.qg-sidebar__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  padding: 12px 14px;
  border-bottom: 1px solid var(--qg-border-default);
  background: var(--qg-surface-raised);
  flex-shrink: 0;
}
.qg-sidebar__headLeft {
  display: flex;
  align-items: center;
  gap: 8px;
}
.qg-sidebar__headIcon { color: var(--qg-accent); flex-shrink: 0; }
.qg-sidebar__headTitle {
  font-family: var(--qg-font-display);
  font-size: var(--qg-text-sm);
  font-weight: 500;
  letter-spacing: -0.01em;
  color: var(--qg-text-primary);
}
.qg-sidebar__headRight {
  display: flex;
  align-items: center;
  gap: 6px;
}

/* ─── Tabs ────────────────────────────────────────────────────────────── */
.qg-sidebar__tabs {
  display: flex;
  flex-shrink: 0;
  border-bottom: 1px solid var(--qg-border-default);
  background: var(--qg-surface-raised);
}
.qg-sidebar__tab {
  flex: 1;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 9px 0;
  background: transparent;
  border: none;
  cursor: pointer;
  font-size: var(--qg-text-sm);
  font-weight: 500;
  color: var(--qg-text-tertiary);
  position: relative;
  transition: color var(--qg-dur-fast) var(--qg-ease);
}
.qg-sidebar__tab:hover { color: var(--qg-text-secondary); }
.qg-sidebar__tab[aria-selected="true"] { color: var(--qg-text-primary); }
.qg-sidebar__tab[aria-selected="true"]::after {
  content: "";
  position: absolute;
  left: 20%;
  right: 20%;
  bottom: -1px;
  height: 2px;
  background: var(--qg-accent);
  border-radius: 2px 2px 0 0;
}
.qg-sidebar__tabBadge {
  font-size: 10px;
  padding: 1px 6px;
  border-radius: var(--qg-radius-pill);
  background: var(--qg-surface-sunken);
  color: var(--qg-text-tertiary);
}
.qg-sidebar__tab[aria-selected="true"] .qg-sidebar__tabBadge {
  background: var(--qg-accent-soft);
  color: var(--qg-accent);
}

/* ─── Status bar ──────────────────────────────────────────────────────── */
.qg-sidebar__status {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 5px 14px;
  font-size: 10px;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: var(--qg-text-tertiary);
  background: var(--qg-surface-sunken);
  border-bottom: 1px solid var(--qg-border-default);
  flex-shrink: 0;
}
.qg-sidebar__statusDot {
  width: 5px; height: 5px;
  border-radius: 50%;
  background: var(--qg-success);
}
.qg-sidebar__status[data-mode="review"] .qg-sidebar__statusDot { background: var(--qg-warning); }
.qg-sidebar__status[data-mode="study"] .qg-sidebar__statusDot { background: var(--qg-accent); }
.qg-sidebar__modeSeg {
  margin-left: auto;
  padding: 2px;
}
.qg-sidebar__modeSeg .qg-segment__btn {
  padding: 3px 8px;
  font-size: 10px;
}

/* ─── Messages area ───────────────────────────────────────────────────── */
.qg-sidebar__messages {
  flex: 1;
  overflow-y: auto;
  padding: 14px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.qg-sidebar__empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  padding: 48px 20px;
  gap: 8px;
}
.qg-sidebar__emptyIcon { color: var(--qg-text-muted); margin-bottom: 4px; }
.qg-sidebar__emptyTitle {
  font-family: var(--qg-font-display);
  font-size: var(--qg-text-lg);
  font-weight: 500;
  color: var(--qg-text-primary);
  margin: 0;
  letter-spacing: -0.015em;
}
.qg-sidebar__emptyBody {
  font-size: var(--qg-text-sm);
  color: var(--qg-text-tertiary);
  line-height: 1.5;
  margin: 0;
  max-width: 260px;
}

/* ─── Scroll-to-bottom button ─────────────────────────────────────────── */
.qg-sidebar__scrollDown {
  position: absolute;
  bottom: 80px;
  left: 50%;
  transform: translateX(-50%);
  width: 32px; height: 32px;
  border-radius: 50%;
  background: var(--qg-surface-raised);
  border: 1px solid var(--qg-border-default);
  color: var(--qg-text-secondary);
  box-shadow: var(--qg-shadow-1);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  z-index: 3;
  transition: border-color var(--qg-dur-fast) var(--qg-ease);
}
.qg-sidebar__scrollDown:hover {
  border-color: var(--qg-border-strong);
  color: var(--qg-text-primary);
}

/* ─── Messages ────────────────────────────────────────────────────────── */
.qg-sidebar__msg { display: flex; flex-direction: column; }
.qg-sidebar__msg[data-role="user"] { align-items: flex-end; }

.qg-sidebar__bubble {
  max-width: 88%;
  padding: 10px 14px;
  border-radius: var(--qg-radius-lg);
  font-size: var(--qg-text-sm);
  line-height: 1.6;
  word-wrap: break-word;
  overflow-wrap: break-word;
}

.qg-sidebar__msg[data-role="assistant"] .qg-sidebar__bubble {
  background: var(--qg-surface-sunken);
  color: var(--qg-text-primary);
  border-top-left-radius: var(--qg-radius-xs);
  border: 1px solid var(--qg-border-default);
}
.qg-sidebar__msg[data-role="user"] .qg-sidebar__bubble {
  background: var(--qg-accent);
  color: var(--qg-accent-on);
  border-top-right-radius: var(--qg-radius-xs);
}

.qg-sidebar__cursor {
  display: inline-block;
  width: 2px; height: 1em;
  background: var(--qg-text-primary);
  margin-left: 2px;
  vertical-align: text-bottom;
  animation: qg-blink 1s step-end infinite;
}
@keyframes qg-blink { 0%, 100% { opacity: 1; } 50% { opacity: 0; } }

.qg-sidebar__dots { display: inline-flex; gap: 4px; padding: 4px 0; }
.qg-sidebar__dots span {
  width: 5px; height: 5px;
  border-radius: 50%;
  background: var(--qg-text-tertiary);
  animation: qg-dotPulse 1.4s ease-in-out infinite;
}
.qg-sidebar__dots span:nth-child(2) { animation-delay: 0.15s; }
.qg-sidebar__dots span:nth-child(3) { animation-delay: 0.3s; }
@keyframes qg-dotPulse {
  0%, 80%, 100% { opacity: 0.3; transform: scale(0.8); }
  40% { opacity: 1; transform: scale(1); }
}

.qg-sidebar__deleteCard {
  display: flex; align-items: center; justify-content: space-between; gap: 10px;
  margin-top: 8px; padding: 10px 12px;
  background: var(--qg-danger-soft);
  border: 1px solid color-mix(in oklch, var(--qg-danger) 30%, transparent);
  border-radius: var(--qg-radius-md);
  font-size: var(--qg-text-xs); font-weight: 500; color: var(--qg-danger);
}
.qg-sidebar__deleteBtn { padding: 4px 10px !important; font-size: var(--qg-text-xs) !important; flex-shrink: 0; }

.qg-sidebar__notice {
  display: flex; align-items: center; justify-content: space-between;
  padding: 8px 12px; border-radius: var(--qg-radius-md);
  font-size: var(--qg-text-xs); font-weight: 500;
}
.qg-sidebar__notice[data-tone="success"] { background: var(--qg-success-soft); color: var(--qg-success); }
.qg-sidebar__notice[data-tone="danger"] { background: var(--qg-danger-soft); color: var(--qg-danger); }
.qg-sidebar__noticeDismiss {
  background: none; border: none; color: inherit; cursor: pointer;
  font-size: 16px; line-height: 1; opacity: 0.6;
}
.qg-sidebar__noticeDismiss:hover { opacity: 1; }

/* ─── Bubble typography ───────────────────────────────────────────────── */
.qg-sidebar__bubble :deep(p) { margin: 0 0 8px; font-size: inherit; line-height: 1.6; }
.qg-sidebar__bubble :deep(p:last-child) { margin-bottom: 0; }
.qg-sidebar__bubble :deep(h1), .qg-sidebar__bubble :deep(h2), .qg-sidebar__bubble :deep(h3) {
  font-weight: 600; margin: 12px 0 6px; line-height: 1.3; color: var(--qg-text-primary);
}
.qg-sidebar__bubble :deep(h1) { font-size: 1.1em; }
.qg-sidebar__bubble :deep(h2) { font-size: 1.05em; }
.qg-sidebar__bubble :deep(h3) { font-size: 1em; }
.qg-sidebar__bubble :deep(ul), .qg-sidebar__bubble :deep(ol) { margin: 0 0 8px; padding-left: 18px; }
.qg-sidebar__bubble :deep(li) { margin-bottom: 3px; }
.qg-sidebar__bubble :deep(ul) { list-style-type: disc; }
.qg-sidebar__bubble :deep(ol) { list-style-type: decimal; }
.qg-sidebar__bubble :deep(code) { font-family: var(--qg-font-mono); font-size: 0.875em; padding: 1px 5px; border-radius: 4px; }
.qg-sidebar__msg[data-role="assistant"] .qg-sidebar__bubble :deep(code) { background: var(--qg-surface-base); border: 1px solid var(--qg-border-default); color: var(--qg-text-primary); }
.qg-sidebar__msg[data-role="user"] .qg-sidebar__bubble :deep(code) { background: color-mix(in oklch, var(--qg-accent-on) 15%, transparent); }
.qg-sidebar__bubble :deep(pre) { background: var(--qg-surface-sunken); border: 1px solid var(--qg-border-default); padding: 10px 12px; border-radius: var(--qg-radius-md); overflow-x: auto; margin: 8px 0; font-size: 0.8125rem; line-height: 1.5; }
.qg-sidebar__bubble :deep(pre code) { background: transparent !important; border: none !important; padding: 0; display: block; }
.qg-sidebar__bubble :deep(blockquote) { margin: 8px 0; padding: 4px 12px; border-left: 2px solid var(--qg-border-strong); color: var(--qg-text-secondary); font-style: italic; }
.qg-sidebar__msg[data-role="user"] .qg-sidebar__bubble :deep(blockquote) { border-left-color: color-mix(in oklch, var(--qg-accent-on) 40%, transparent); color: color-mix(in oklch, var(--qg-accent-on) 80%, transparent); }
.qg-sidebar__bubble :deep(a) { color: var(--qg-accent); text-decoration: underline; text-underline-offset: 2px; }
.qg-sidebar__msg[data-role="user"] .qg-sidebar__bubble :deep(a) { color: var(--qg-accent-on); }

/* ─── Quote preview ───────────────────────────────────────────────────── */
.qg-sidebar__quote {
  padding: 10px 14px;
  background: var(--qg-accent-soft);
  border-top: 1px solid color-mix(in oklch, var(--qg-accent) 20%, transparent);
  flex-shrink: 0;
}
.qg-sidebar__quoteHead { display: flex; align-items: center; justify-content: space-between; margin-bottom: 4px; }
.qg-sidebar__quoteLabel { font-size: 9px; letter-spacing: 0.14em; color: var(--qg-accent); font-weight: 500; }
.qg-sidebar__quoteDismiss { background: none; border: none; cursor: pointer; color: var(--qg-accent); font-size: 16px; line-height: 1; opacity: 0.6; padding: 0 2px; }
.qg-sidebar__quoteDismiss:hover { opacity: 1; }
.qg-sidebar__quoteText { font-size: var(--qg-text-xs); line-height: 1.5; color: var(--qg-text-secondary); margin: 0; display: -webkit-box; -webkit-line-clamp: 3; line-clamp: 3; -webkit-box-orient: vertical; overflow: hidden; }

.qg-quote-slide-enter-active, .qg-quote-slide-leave-active { transition: max-height var(--qg-dur-base) var(--qg-ease), opacity var(--qg-dur-base) var(--qg-ease); overflow: hidden; }
.qg-quote-slide-enter-from, .qg-quote-slide-leave-to { max-height: 0; opacity: 0; }
.qg-quote-slide-enter-to, .qg-quote-slide-leave-from { max-height: 120px; opacity: 1; }

/* ─── Toast ───────────────────────────────────────────────────────────── */
.qg-sidebar__toast {
  position: absolute;
  bottom: 72px;
  left: 50%;
  transform: translateX(-50%);
  padding: 6px 16px;
  background: var(--qg-success);
  color: var(--qg-accent-on);
  border-radius: var(--qg-radius-pill);
  font-size: var(--qg-text-xs);
  font-weight: 500;
  letter-spacing: 0.02em;
  z-index: 3;
  pointer-events: none;
}

/* ─── Footer / input ──────────────────────────────────────────────────── */
.qg-sidebar__foot {
  padding: 10px 14px;
  border-top: 1px solid var(--qg-border-default);
  background: var(--qg-surface-raised);
  flex-shrink: 0;
}
.qg-sidebar__inputWrap {
  display: flex; align-items: flex-end; gap: 8px;
  background: var(--qg-surface-sunken);
  border: 1px solid var(--qg-border-default);
  border-radius: var(--qg-radius-lg);
  padding: 6px 6px 6px 14px;
  transition: border-color var(--qg-dur-fast) var(--qg-ease), background var(--qg-dur-fast) var(--qg-ease), box-shadow var(--qg-dur-fast) var(--qg-ease);
}
.qg-sidebar__inputWrap--focus { border-color: var(--qg-border-focus); background: var(--qg-surface-raised); box-shadow: var(--qg-shadow-focus); }
.qg-sidebar__input {
  flex: 1; background: transparent; border: none; padding: 6px 0;
  font-family: var(--qg-font-body); font-size: var(--qg-text-sm); line-height: 1.5;
  color: var(--qg-text-primary); resize: none; outline: none; max-height: 120px;
}
.qg-sidebar__input::placeholder { color: var(--qg-text-muted); }
.qg-sidebar__input:disabled { opacity: 0.5; cursor: not-allowed; }
.qg-sidebar__send {
  flex-shrink: 0; width: 32px; height: 32px;
  display: inline-flex; align-items: center; justify-content: center;
  background: var(--qg-accent); color: var(--qg-accent-on); border: none;
  border-radius: var(--qg-radius-md); cursor: pointer;
  transition: background var(--qg-dur-fast) var(--qg-ease), transform var(--qg-dur-fast) var(--qg-ease), opacity var(--qg-dur-fast) var(--qg-ease);
}
.qg-sidebar__send:hover:not(:disabled) { background: var(--qg-accent-hover); transform: scale(1.04); }
.qg-sidebar__send:disabled { opacity: 0.35; cursor: not-allowed; }

/* ─── Archive: note detail header ─────────────────────────────────────── */
.qg-sidebar__noteHead {
  display: flex; align-items: center; gap: 10px;
  padding: 10px 14px;
  border-bottom: 1px solid var(--qg-border-default);
  background: var(--qg-surface-sunken);
  flex-shrink: 0;
}
.qg-sidebar__noteHeadInfo { flex: 1; min-width: 0; }
.qg-sidebar__noteHeadTitle {
  font-family: var(--qg-font-display);
  font-size: var(--qg-text-sm); font-weight: 500;
  color: var(--qg-text-primary); letter-spacing: -0.01em;
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
  display: block;
}
.qg-sidebar__noteHeadMeta { font-size: 10px; color: var(--qg-text-tertiary); letter-spacing: 0.04em; }
.qg-sidebar__noteBody { padding-top: 16px; }

/* ─── Archive: list ───────────────────────────────────────────────────── */
.qg-sidebar__archiveList {
  flex: 1; overflow-y: auto;
  padding: 12px;
  display: flex; flex-direction: column; gap: 8px;
}
.qg-sidebar__noteItem {
  padding: 12px 14px;
  background: var(--qg-surface-raised);
  border: 1px solid var(--qg-border-default);
  border-radius: var(--qg-radius-md);
  cursor: pointer;
  transition: border-color var(--qg-dur-fast) var(--qg-ease), background var(--qg-dur-fast) var(--qg-ease);
}
.qg-sidebar__noteItem:hover { border-color: var(--qg-border-strong); background: var(--qg-surface-sunken); }
.qg-sidebar__noteItemHead { display: flex; align-items: center; justify-content: space-between; gap: 8px; margin-bottom: 4px; }
.qg-sidebar__noteItemTitle {
  font-size: var(--qg-text-sm); font-weight: 500;
  color: var(--qg-text-primary); letter-spacing: -0.005em;
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis; flex: 1;
}
.qg-sidebar__noteItemDel {
  flex-shrink: 0; background: none; border: none; color: var(--qg-text-muted);
  cursor: pointer; padding: 2px; opacity: 0;
  transition: opacity var(--qg-dur-fast) var(--qg-ease), color var(--qg-dur-fast) var(--qg-ease);
}
.qg-sidebar__noteItem:hover .qg-sidebar__noteItemDel { opacity: 1; }
.qg-sidebar__noteItemDel:hover { color: var(--qg-danger); }
.qg-sidebar__noteItemMeta {
  display: flex; gap: 8px;
  font-size: 10px; letter-spacing: 0.04em;
  color: var(--qg-text-tertiary); margin-bottom: 6px;
}
.qg-sidebar__noteItemPreview {
  font-size: var(--qg-text-xs); line-height: 1.5;
  color: var(--qg-text-tertiary); margin: 0;
  display: -webkit-box; -webkit-line-clamp: 2; line-clamp: 2;
  -webkit-box-orient: vertical; overflow: hidden;
}

/* ─── Fade transition ─────────────────────────────────────────────────── */
.qg-fade-enter-active, .qg-fade-leave-active { transition: opacity var(--qg-dur-base) var(--qg-ease); }
.qg-fade-enter-from, .qg-fade-leave-to { opacity: 0; }

/* ─── Mobile ──────────────────────────────────────────────────────────── */
@media (max-width: 768px) {
  .qg-sidebar { width: 100% !important; border-left: none; }
  .qg-sidebar__resize { display: none; }
}
</style>
