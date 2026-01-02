import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

const api = axios.create({
    baseURL: API_BASE_URL,
    headers: {
        'Content-Type': 'application/json',
    },
});

// Add auth token to requests
api.interceptors.request.use((config) => {
    const token = localStorage.getItem('access_token'); // Fixed: use 'access_token' to match main API
    if (token) {
        config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
});

// Conversations API
export const conversationsAPI = {
    // Create a new conversation
    create: (datasetId: number, initialQuery?: string) =>
        api.post('/conversations', { dataset_id: datasetId, initial_query: initialQuery }),

    // List all conversations
    list: (datasetId?: number, limit = 50) =>
        api.get('/conversations', { params: { dataset_id: datasetId, limit } }),

    // Get a specific conversation with messages
    get: (conversationId: number) =>
        api.get(`/conversations/${conversationId}`),

    // Send a message in a conversation
    sendMessage: (conversationId: number, content: string) =>
        api.post(`/conversations/${conversationId}/messages`, { content }),

    // Delete a conversation
    delete: (conversationId: number) =>
        api.delete(`/conversations/${conversationId}`),
};

export { api };
