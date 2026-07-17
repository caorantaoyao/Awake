import axios from 'axios';

const api = axios.create({
  baseURL: '/api',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json'
  }
});

const CHAT_TIMEOUT_MS = 130000;
const CONTROL_TIMEOUT_MS = 60000;

const AUTH_TOKEN_KEY = 'awaken_access_token';
const AUTH_STUDENT_KEY = 'awaken_student';

export const getAuthToken = () => localStorage.getItem(AUTH_TOKEN_KEY);

export const getStoredStudent = () => {
  const raw = localStorage.getItem(AUTH_STUDENT_KEY);
  if (!raw) return null;
  try {
    return JSON.parse(raw);
  } catch {
    localStorage.removeItem(AUTH_STUDENT_KEY);
    return null;
  }
};

export const saveAuthSession = ({ accessToken, student }) => {
  localStorage.setItem(AUTH_TOKEN_KEY, accessToken);
  localStorage.setItem(AUTH_STUDENT_KEY, JSON.stringify(student));
};

export const updateStoredStudent = (patch) => {
  const current = getStoredStudent();
  if (!current) return null;
  const updated = { ...current, ...patch };
  localStorage.setItem(AUTH_STUDENT_KEY, JSON.stringify(updated));
  return updated;
};

export const clearAuthSession = () => {
  localStorage.removeItem(AUTH_TOKEN_KEY);
  localStorage.removeItem(AUTH_STUDENT_KEY);
};

export const isAuthenticated = () => !!getAuthToken();

api.interceptors.request.use((config) => {
  const token = getAuthToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    const status = error.response?.status;
    if (status === 401) {
      if (window.location.pathname.startsWith('/login')
        || window.location.pathname.startsWith('/register')) {
        return Promise.reject(error);
      }
      clearAuthSession();
      const from = `${window.location.pathname}${window.location.search}${window.location.hash}`;
      const redirect = `/login?from=${encodeURIComponent(from || '/app/today')}`;
      window.location.replace(redirect);
    }
    return Promise.reject(error);
  }
);

// ─── Auth ───

export const registerStudent = async (data) => {
  const response = await api.post('/register', data);
  return response.data;
};

export const loginStudent = async (data) => {
  const response = await api.post('/login', data);
  return response.data;
};

export const getCurrentStudent = async () => {
  const response = await api.get('/auth/me');
  return response.data;
};

// ─── Profile ───

export const getProfile = async () => {
  const response = await api.get('/profile');
  return response.data;
};

export const updateProfile = async (data) => {
  const response = await api.put('/profile', data);
  return response.data;
};

export const completeOnboarding = async (data) => {
  const response = await api.post('/onboarding/complete', data);
  return response.data;
};

// ─── Legacy chat history (SQLite-backed) ───

export const getChatHistory = async (limit) => {
  const config = limit == null ? undefined : { params: { limit } };
  const response = await api.get('/chat/history', config);
  return response.data;
};

export const clearChatHistory = async () => {
  const response = await api.delete('/chat/history');
  return response.data;
};

// ─── Conversations (DeerFlow Threads) ───

export const listConversations = async () => {
  const response = await api.get('/conversations');
  return response.data;
};

export const createConversation = async (data = {}) => {
  const response = await api.post('/conversations', data);
  return response.data;
};

export const getConversation = async (id) => {
  const response = await api.get(`/conversations/${id}`);
  return response.data;
};

export const updateConversation = async (id, data) => {
  const response = await api.patch(`/conversations/${id}`, data);
  return response.data;
};

export const deleteConversation = async (id) => {
  const response = await api.delete(`/conversations/${id}`);
  return response.data;
};

// ─── SSE Streaming Chat ───

/**
 * 发起 SSE 流式对话。
 * @param {Object} params
 * @param {string} params.message - 用户消息
 * @param {number} [params.conversationId] - 会话 ID，不传则创建新会话
 * @param {string} [params.modelName]
 * @param {boolean} [params.thinkingEnabled]
 * @param {boolean} [params.isPlanMode]
 * @param {string[]} [params.fileIds] - 上传的文件 ID 列表
 * @param {AbortSignal} [params.signal] - 取消信号
 * @param {Function} params.onEvent - 事件回调 (event) => void
 *   event.type: 'meta' | 'text' | 'thinking' | 'plan' | 'artifact' | 'tool' | 'done' | 'error'
 */
export const streamChat = async ({
  message,
  conversationId,
  modelName,
  thinkingEnabled,
  isPlanMode,
  fileIds,
  signal,
  onEvent,
}) => {
  const token = getAuthToken();
  const body = {
    message,
    ...(conversationId && { conversation_id: conversationId }),
    ...(modelName && { model_name: modelName }),
    ...(thinkingEnabled && { thinking_enabled: true }),
    ...(isPlanMode && { is_plan_mode: true }),
    ...(fileIds && fileIds.length > 0 && { file_ids: fileIds }),
  };

  const response = await fetch('/api/chat/stream', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...(token && { Authorization: `Bearer ${token}` }),
    },
    body: JSON.stringify(body),
    signal,
  });

  if (!response.ok) {
    let detail = `请求失败 (HTTP ${response.status})`;
    try {
      const errData = await response.json();
      detail = errData.detail || detail;
    } catch {}
    throw new Error(detail);
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = '';
  let currentEvent = 'message';

  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });

      let newlineIndex;
      while ((newlineIndex = buffer.indexOf('\n')) !== -1) {
        const line = buffer.slice(0, newlineIndex).trim();
        buffer = buffer.slice(newlineIndex + 1);

        if (!line) continue;

        if (line.startsWith('event:')) {
          currentEvent = line.slice(6).trim();
          continue;
        }

        if (line.startsWith('data:')) {
          const dataStr = line.slice(5).trim();
          if (!dataStr) continue;
          try {
            const data = JSON.parse(dataStr);
            onEvent?.({ type: currentEvent, ...data });
          } catch {
            // skip malformed JSON
          }
          currentEvent = 'message';
        }
      }
    }
  } finally {
    reader.releaseLock();
  }
};

// ─── Non-streaming chat (legacy compat) ───

export const sendChat = async (data, config = {}) => {
  const response = await api.post('/chat', data, { timeout: CHAT_TIMEOUT_MS, ...config });
  return response.data;
};

export const extractTask = async (data, config = {}) => {
  const response = await api.post('/chat/extract-task', data, { timeout: CHAT_TIMEOUT_MS, ...config });
  return response.data;
};

// ─── Suggestions ───

export const getSuggestions = async (messages) => {
  const response = await api.post('/chat/suggestions', { messages }, { timeout: 15000 });
  return response.data.suggestions || [];
};

// ─── File Upload ───

export const uploadFiles = async (conversationId, files) => {
  const formData = new FormData();
  files.forEach((f) => formData.append('files', f));
  const response = await api.post('/chat/upload', formData, {
    params: { conversation_id: conversationId },
    headers: { 'Content-Type': 'multipart/form-data' },
    timeout: 60000,
  });
  return response.data;
};

// ─── Tasks ───

export const createTask = async (data) => {
  const response = await api.post('/tasks', data);
  return response.data;
};

export const completeTask = async (data) => {
  const response = await api.post('/task-complete', data);
  return response.data;
};

export const getTask = async (taskId) => {
  const response = await api.get(`/tasks/${taskId}`);
  return response.data;
};

export const getTodayTasks = async () => {
  const response = await api.get('/tasks/today');
  return response.data;
};

// ─── Student ───

export const getStudent = async (email) => {
  const response = await api.get(`/students/${encodeURIComponent(email)}`);
  return response.data;
};

// ─── Resources / Growth ───

export const getResources = async (resourceType) => {
  const config = resourceType == null
    ? undefined
    : { params: { resource_type: resourceType } };
  const response = await api.get('/resources', config);
  return response.data;
};

export const getGrowthEvents = async (limit) => {
  const config = limit == null ? undefined : { params: { limit } };
  const response = await api.get('/growth/events', config);
  return response.data;
};

export const getGrowthSummary = async () => {
  const response = await api.get('/growth/summary');
  return response.data;
};

// ─── DeerFlow Capabilities ───

export const getDeerflowStatus = async () => {
  const response = await api.get('/deerflow/status', { timeout: CONTROL_TIMEOUT_MS });
  return response.data;
};

export const getSkills = async () => {
  const response = await api.get('/deerflow/skills', { timeout: CONTROL_TIMEOUT_MS });
  return response.data;
};

export const toggleSkill = async (name, enabled) => {
  const response = await api.put(
    `/deerflow/skills/${encodeURIComponent(name)}`,
    { enabled },
    { timeout: CONTROL_TIMEOUT_MS }
  );
  return response.data;
};

export const getModels = async () => {
  const response = await api.get('/deerflow/models', { timeout: CONTROL_TIMEOUT_MS });
  return response.data;
};

// ─── Preferences ───

export const getPreferences = async () => {
  const response = await api.get('/students/me/preferences');
  return response.data;
};

export const updatePreferences = async (data) => {
  const response = await api.put('/students/me/preferences', data);
  return response.data;
};

// ─── Health ───

export const healthCheck = async () => {
  const response = await api.get('/health');
  return response.data;
};

// ─── Artifacts ───

export const listArtifacts = async (conversationId) => {
  const response = await api.get(`/conversations/${conversationId}/artifacts`, { timeout: CONTROL_TIMEOUT_MS });
  return response.data.data?.artifacts || [];
};

export const getArtifactUrl = (conversationId, artifactPath) => {
  const token = getAuthToken();
  const base = `/api/conversations/${conversationId}/artifacts/${artifactPath}`;
  return token ? `${base}?_t=${encodeURIComponent(token)}` : base;
};

// ─── Feedback ───

export const submitFeedback = async (conversationId, runId, { rating, comment } = {}) => {
  const response = await api.put(
    `/conversations/${conversationId}/runs/${encodeURIComponent(runId)}/feedback`,
    { rating, comment },
    { timeout: CONTROL_TIMEOUT_MS }
  );
  return response.data;
};

// ─── Input Polish ───

export const polishInput = async (text) => {
  const response = await api.post('/input-polish', { text }, { timeout: 15000 });
  return response.data.data?.polished_text || text;
};

// ─── MCP Servers ───

export const listMcpServers = async () => {
  const response = await api.get('/mcp', { timeout: CONTROL_TIMEOUT_MS });
  return response.data.data?.servers || [];
};

// ─── Run History ───

export const listRuns = async (conversationId = null) => {
  const url = conversationId ? `/conversations/${conversationId}/runs` : '/runs';
  const response = await api.get(url, { timeout: CONTROL_TIMEOUT_MS });
  return response.data.data?.runs || [];
};

// ─── Scheduled Tasks ───

export const listScheduledTasks = async () => {
  const response = await api.get('/scheduled-tasks', { timeout: CONTROL_TIMEOUT_MS });
  return response.data.data?.tasks || [];
};

export const createScheduledTask = async (data) => {
  const response = await api.post('/scheduled-tasks', data, { timeout: CONTROL_TIMEOUT_MS });
  return response.data;
};

export default api;
