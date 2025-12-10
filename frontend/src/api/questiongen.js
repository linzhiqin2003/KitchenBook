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
    generateQuestion(seed = null) {
        return api.post('/questions/generate/', { seed });
    },

    // Smart next: prioritizes cached questions, falls back to generation
    // seen_ids: array of question IDs the user has already seen
    // prefer_cached: if true, prefer cached over new AI generation
    smartNext(seenIds = [], preferCached = true) {
        return api.post('/questions/smart-next/', {
            seen_ids: seenIds,
            prefer_cached: preferCached
        });
    },

    // Get random cached question (never generates new)
    randomCached(seenIds = []) {
        return api.post('/questions/random-cached/', { seen_ids: seenIds });
    },

    // Get stats about cached questions
    getStats() {
        return api.get('/questions/stats/');
    },

    // Batch generate questions
    batchGenerate(limit = 5) {
        return api.post('/questions/batch-generate/', { limit });
    },

    // Get available topics
    getTopics() {
        return api.get('/questions/topics/');
    },
};

export default api;

