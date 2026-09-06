import axios from "axios";

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL,
});

// Attach the stored token to every outgoing request, if present.
api.interceptors.request.use((config) => {
  const token = localStorage.getItem("paperqa_token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// If the backend ever says the token is invalid/expired, clear it so the
// app doesn't keep sending a dead token on every subsequent request.
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem("paperqa_token");
    }
    return Promise.reject(error);
  }
);

export const authApi = {
  register: (email, password) =>
    api.post("/api/auth/register", { email, password }),
  login: (email, password) =>
    api.post("/api/auth/login", { email, password }),
  me: () => api.get("/api/auth/me"),
};

export const paperApi = {
  list: () => api.get("/api/papers"),
  upload: (file, onUploadProgress) => {
    const formData = new FormData();
    formData.append("file", file);
    return api.post("/api/papers/upload", formData, {
      headers: { "Content-Type": "multipart/form-data" },
      onUploadProgress,
    });
  },
  startIndexing: (paperId) => api.post(`/api/papers/${paperId}/index`),
  getStatus: (paperId) => api.get(`/api/papers/${paperId}/status`),
  ask: (paperId, question) =>
    api.post(`/api/papers/${paperId}/ask`, { question }),
};

export const chatApi = {
  createSession: (paperId, title = "New Chat") =>
    api.post(`/api/papers/${paperId}/sessions`, { title }),
  listSessions: (paperId) =>
    api.get(`/api/papers/${paperId}/sessions`),
  getSessionMessages: (sessionId) =>
    api.get(`/api/sessions/${sessionId}/messages`),
  sendMessage: (sessionId, content) =>
    api.post(`/api/sessions/${sessionId}/messages`, { content }),
  deleteSession: (sessionId) =>
    api.delete(`/api/sessions/${sessionId}`),
};

export default api;