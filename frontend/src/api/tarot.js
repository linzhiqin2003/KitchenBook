import axios from 'axios';
import API_BASE_URL from '../config/api';

const apiClient = axios.create({
  baseURL: `${API_BASE_URL}/api/tarot`,
  headers: {
    'Content-Type': 'application/json',
  },
});

const tarotApi = {
  getCards() {
    return apiClient.get('/cards/');
  },
  getCard(id) {
    return apiClient.get(`/cards/${id}/`);
  },
  getSpreads() {
    return apiClient.get('/spreads/');
  },
  divine(question, cards, spreadType) {
    return apiClient.post('/divine/', {
      question,
      cards,
      spread_type: spreadType,
    });
  },
};

export default tarotApi;
