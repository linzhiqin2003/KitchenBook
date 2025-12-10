import axios from 'axios';

const api = axios.create({
    baseURL: '/api',
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

    // Generate a new question
    generateQuestion(seed = null) {
        return api.post('/questions/generate/', { seed });
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
