import axios from "axios";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "/api";

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: { "Content-Type": "application/json" },
  timeout: 30000,
});

// Attach access token to every request
api.interceptors.request.use((config) => {
  const token = localStorage.getItem("access_token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Handle 401 by attempting a token refresh
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    if (
      error.response?.status === 401 &&
      !originalRequest._retry &&
      !originalRequest.url.includes("/auth/")
    ) {
      originalRequest._retry = true;
      const refreshToken = localStorage.getItem("refresh_token");
      if (refreshToken) {
        try {
          const { data } = await axios.post("/api/auth/refresh", {
            refresh_token: refreshToken,
          });
          localStorage.setItem("access_token", data.access_token);
          localStorage.setItem("refresh_token", data.refresh_token);
          originalRequest.headers.Authorization = `Bearer ${data.access_token}`;
          return api(originalRequest);
        } catch {
          localStorage.removeItem("access_token");
          localStorage.removeItem("refresh_token");
          window.location.href = "/login";
        }
      } else {
        window.location.href = "/login";
      }
    }

    const message =
      error.response?.data?.detail || error.message || "Something went wrong";
    return Promise.reject(new Error(message));
  }
);

// ── Chat ──
export const sendMessage = async (message, conversationId = null) => {
  const payload = { message };
  if (conversationId) payload.conversation_id = conversationId;
  const { data } = await api.post("/chat", payload);
  return data;
};

// ── Conversations ──
export const conversationApi = {
  list: () => api.get("/conversations"),
  create: (title = "New Chat") => api.post("/conversations", { title }),
  get: (id) => api.get(`/conversations/${id}`),
  update: (id, title) => api.put(`/conversations/${id}`, { title }),
  delete: (id) => api.delete(`/conversations/${id}`),
  getMessages: (id) => api.get(`/conversations/${id}/messages`),
};

// ── Auth ──
export const authApi = {
  login: (email, password) => api.post("/auth/login", { email, password }),
  register: (username, email, password, full_name) =>
    api.post("/auth/register", { username, email, password, full_name }),
  logout: () => api.post("/auth/logout"),
  refresh: (refresh_token) => api.post("/auth/refresh", { refresh_token }),
};

// ── Users ──
export const userApi = {
  getProfile: () => api.get("/users/me"),
  updateProfile: (fields) => api.put("/users/me", fields),
};

// ── Memory ──
export const memoryApi = {
  list: (category = null) => {
    const params = category ? { category } : {};
    return api.get("/memory", { params });
  },
  search: (query, category = null) => {
    const body = { query };
    if (category) body.category = category;
    return api.post("/memory/search", body);
  },
  stats: () => api.get("/memory/stats"),
  delete: (id) => api.delete(`/memory/${id}`),
  clearAll: () => api.delete("/memory"),
};

// ── Voice ──
export const voiceApi = {
  transcribe: (audioBase64, filename = "audio.wav", language = null) => {
    const body = { audio: audioBase64, filename };
    if (language) body.language = language;
    return api.post("/voice/transcribe", body);
  },
  speak: (text, voice = null, rate = null) => {
    const body = { text };
    if (voice) body.voice = voice;
    if (rate) body.rate = rate;
    return api.post("/voice/speak", body);
  },
  chat: (audioBase64, options = {}) => {
    const body = { audio: audioBase64, ...options };
    return api.post("/voice/chat", body);
  },
  chatUpload: (formData) => {
    return api.post("/voice/chat/upload", formData, {
      headers: { "Content-Type": "multipart/form-data" },
      timeout: 60000,
    });
  },
  settings: () => api.get("/voice/settings"),
  voices: (language = null) => {
    const params = language ? { language } : {};
    return api.get("/voice/voices", { params });
  },
  status: () => api.get("/voice/status"),
};

// ── RAG (Knowledge Base) ──
export const ragApi = {
  upload: (formData) => {
    return api.post("/rag/upload", formData, {
      headers: { "Content-Type": "multipart/form-data" },
      timeout: 120000,
    });
  },
  documents: () => api.get("/rag/documents"),
  deleteDocument: (id) => api.delete(`/rag/document/${id}`),
  query: (question, nResults = 5) => api.post("/rag/query", { question, n_results: nResults }),
  stats: () => api.get("/rag/stats"),
};

// -- Analytics --
export const analyticsApi = {
  overview: (days = 7) => api.get("/analytics/overview", { params: { days } }),
  tools: () => api.get("/analytics/tools"),
  performance: () => api.get("/analytics/performance"),
  history: (limit = 50, offset = 0) =>
    api.get("/analytics/history", { params: { limit, offset } }),
  traces: (limit = 20) => api.get("/analytics/traces", { params: { limit } }),
  errors: (limit = 50) => api.get("/analytics/errors", { params: { limit } }),
};

// ── MCP (Model Context Protocol) ──
export const mcpApi = {
  status: () => api.get("/mcp/status"),
  servers: () => api.get("/mcp/servers"),
  tools: () => api.get("/mcp/tools"),
  connect: (name) => api.post("/mcp/connect", { name }),
  disconnect: (name) => api.post("/mcp/disconnect", { name }),
  refresh: () => api.post("/mcp/refresh"),
};

// ── Vision & Multimodal AI ──
export const visionApi = {
  upload: (formData) => {
    return api.post("/vision/upload", formData, {
      headers: { "Content-Type": "multipart/form-data" },
      timeout: 120000,
    });
  },
  analyze: (formData) => {
    return api.post("/vision/analyze", formData, {
      headers: { "Content-Type": "multipart/form-data" },
      timeout: 120000,
    });
  },
  ocr: (formData) => {
    return api.post("/vision/ocr", formData, {
      headers: { "Content-Type": "multipart/form-data" },
      timeout: 120000,
    });
  },
  question: (formData) => {
    return api.post("/vision/question", formData, {
      headers: { "Content-Type": "multipart/form-data" },
      timeout: 120000,
    });
  },
  caption: (formData) => {
    return api.post("/vision/caption", formData, {
      headers: { "Content-Type": "multipart/form-data" },
      timeout: 120000,
    });
  },
  chart: (formData) => {
    return api.post("/vision/chart", formData, {
      headers: { "Content-Type": "multipart/form-data" },
      timeout: 120000,
    });
  },
  uiAnalysis: (formData) => {
    return api.post("/vision/ui-analysis", formData, {
      headers: { "Content-Type": "multipart/form-data" },
      timeout: 120000,
    });
  },
  history: () => api.get("/vision/history"),
  deleteImage: (id) => api.delete(`/vision/image/${id}`),
  search: (formData) => {
    return api.post("/vision/search", formData, {
      headers: { "Content-Type": "multipart/form-data" },
      timeout: 30000,
    });
  },
};

export default api;
