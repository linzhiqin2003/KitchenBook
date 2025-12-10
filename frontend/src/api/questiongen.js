import axios from 'axios';

const api = axios.create({
    baseURL: '/api/questiongen',
    headers: {
        'Content-Type': 'application/json',
    },
});

export const questionApi = {
    // Get all questions
    getQuestions() {
        return api.get('/questions/');
    },

    // Get a single question
    getQuestion(id) {
        return api.get(`/questions/${id}/`);
    },

    // Generate a new question (forces AI generation)
    // topic: optional topic filter (e.g., 'git', 'sql', 'all' for random)
    generateQuestion(seed = null, topic = null) {
        return api.post('/questions/generate/', { seed, topic });
    },

    // Smart next: prioritizes cached questions, falls back to generation
    // seenIds: array of question IDs the user has already seen
    // preferCached: if true, prefer cached over new AI generation
    // topic: optional topic filter (e.g., 'git', 'sql', 'all' for random)
    smartNext(seenIds = [], preferCached = true, topic = null) {
        return api.post('/questions/smart-next/', {
            seen_ids: seenIds,
            prefer_cached: preferCached,
            topic: topic
        });
    },

    // Get random cached question (never generates new)
    // topic: optional topic filter
    randomCached(seenIds = [], topic = null) {
        return api.post('/questions/random-cached/', {
            seen_ids: seenIds,
            topic: topic
        });
    },

    // Get stats about cached questions
    getStats() {
        return api.get('/questions/stats/');
    },

    // Batch generate questions
    // topic: optional topic filter
    batchGenerate(limit = 5, topic = null) {
        return api.post('/questions/batch-generate/', { limit, topic });
    },

    // Get available topics
    getTopics() {
        return api.get('/questions/topics/');
    },
};

export default api;


