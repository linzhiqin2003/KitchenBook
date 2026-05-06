import axios from 'axios';

const api = axios.create({
    baseURL: '/api/questiongen',
    headers: {
        'Content-Type': 'application/json',
    },
});

export const questionApi = {
    // Get all available courses
    getCourses() {
        return api.get('/questions/courses/');
    },

    // Get all questions (optionally filtered by course)
    getQuestions(courseId = null) {
        const params = courseId ? { course_id: courseId } : {};
        return api.get('/questions/', { params });
    },

    // Get a single question
    getQuestion(id) {
        return api.get(`/questions/${id}/`);
    },

    // Generate a new question
    generateQuestion(seed = null, courseId = null) {
        return api.post('/questions/generate/', {
            seed,
            course_id: courseId
        });
    },

    // Smart next - prioritizes cached questions, filters by topic/difficulty/type, excludes seen
    smartNext(seenIds = [], generateIfEmpty = true, topic = null, difficulty = null, courseId = null, questionType = 'mcq') {
        return api.post('/questions/smart-next/', {
            seen_ids: seenIds,
            generate_if_empty: generateIfEmpty,
            topic: topic,
            difficulty: difficulty,
            course_id: courseId,
            question_type: questionType
        });
    },

    // Batch generate questions
    batchGenerate(limit = 5, courseId = null, questionType = 'mcq', topic = null, difficulty = null) {
        return api.post('/questions/batch-generate/', {
            limit,
            course_id: courseId,
            question_type: questionType,
            topic,
            difficulty
        });
    },

    // Grade a fill-in-blank or essay answer (mcq is graded client-side)
    gradeAnswer(questionId, answer) {
        return api.post(`/questions/${questionId}/grade/`, { answer });
    },

    // ─── Knowledge points (study notes) ──────────────────────────────
    // List points for a course/topic. Returns the raw queryset (no pagination set).
    getNotes(courseId, topic = null) {
        const params = { course_id: courseId };
        if (topic) params.topic = topic;
        return api.get('/notes/', { params });
    },
    // Per-course list of topics + their note counts.
    getNotesTopics(courseId) {
        return api.get('/notes/topics/', { params: { course_id: courseId } });
    },
    // (Re)generate notes for one course+topic.
    generateNotes(courseId, topic, replace = true) {
        return api.post('/notes/generate/', { course_id: courseId, topic, replace });
    },

    // ─── Raw courseware (the source markdown the AI was fed) ─────────
    getCoursewareChapter(courseId, topic) {
        return api.get('/courseware/chapter/', { params: { course_id: courseId, topic } });
    },
    getCoursewareTopics(courseId) {
        return api.get('/courseware/topics/', { params: { course_id: courseId } });
    },
    getCoursewareSummary(courseId, topic, lang = 'en') {
        return api.get('/courseware/summary/', { params: { course_id: courseId, topic, lang } });
    },
    getCoursewareSummaryIndex(courseId) {
        return api.get('/courseware/summary-index/', { params: { course_id: courseId } });
    },
    getReviewData(courseId) {
        return api.get('/courseware/review/', { params: { course_id: courseId } });
    },

    // Get available topics for a course
    getTopics(courseId = null) {
        const params = courseId ? { course_id: courseId } : {};
        return api.get('/questions/topics/', { params });
    },

    // Get statistics about cached questions
    getStats(courseId = null) {
        const params = courseId ? { course_id: courseId } : {};
        return api.get('/questions/stats/', { params });
    },

    // AI Chat - Q&A or Review mode (non-streaming)
    chat(mode, messages, currentQuestion, courseId = null) {
        return api.post('/questions/chat/', {
            mode,
            messages,
            current_question: currentQuestion,
            course_id: courseId
        });
    },

    // AI Chat Streaming - returns the endpoint URL and data for fetch/SSE
    getChatStreamConfig(mode, messages, currentQuestion, courseId = null) {
        const baseURL = api.defaults.baseURL || '';
        return {
            url: `${baseURL}/questions/chat-stream/`,
            data: {
                mode,
                messages,
                current_question: currentQuestion,
                course_id: courseId
            }
        };
    },

    // Study mode streaming config — for notes/courseware browsing
    getStudyChatStreamConfig(messages, context, courseId = null) {
        const baseURL = api.defaults.baseURL || '';
        return {
            url: `${baseURL}/questions/chat-stream/`,
            data: {
                mode: 'study',
                messages,
                current_question: context,
                course_id: courseId
            }
        };
    },

    // ─── Chat notes (archived sessions) ────────────────────────────────
    getChatNotes(courseId = null) {
        const params = courseId ? { course_id: courseId } : {};
        return api.get('/chat-notes/', { params });
    },
    saveChatNote(data) {
        return api.post('/chat-notes/', data);
    },
    deleteChatNote(id) {
        return api.delete(`/chat-notes/${id}/`);
    },

    // Request to delete a question (with reasoner confirmation)
    requestDelete(questionId, conversationHistory) {
        return api.post(`/questions/${questionId}/request-delete/`, {
            conversation_history: conversationHistory
        });
    }
};

export default api;

