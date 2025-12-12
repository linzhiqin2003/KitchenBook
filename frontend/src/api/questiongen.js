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

    // Smart next - prioritizes cached questions, filters by topic/difficulty, excludes seen
    smartNext(seenIds = [], generateIfEmpty = true, topic = null, difficulty = null, courseId = null) {
        return api.post('/questions/smart-next/', {
            seen_ids: seenIds,
            generate_if_empty: generateIfEmpty,
            topic: topic,
            difficulty: difficulty,
            course_id: courseId
        });
    },

    // Batch generate questions
    batchGenerate(limit = 5, courseId = null) {
        return api.post('/questions/batch-generate/', {
            limit,
            course_id: courseId
        });
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

    // Request to delete a question (with reasoner confirmation)
    requestDelete(questionId, conversationHistory) {
        return api.post(`/questions/${questionId}/request-delete/`, {
            conversation_history: conversationHistory
        });
    }
};

export default api;

