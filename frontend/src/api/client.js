import axios from 'axios';

const api = axios.create({
  baseURL: '/api',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json'
  }
});

const DEFAULT_DEERFLOW_CONTROL_TIMEOUT_MS = 60000;

const parsePositiveNumber = (value, fallback) => {
  const parsed = Number(value);
  return Number.isFinite(parsed) && parsed > 0 ? parsed : fallback;
};

const deerflowControlRequestConfig = {
  timeout: parsePositiveNumber(
    import.meta.env?.VITE_DEERFLOW_CONTROL_TIMEOUT_MS,
    DEFAULT_DEERFLOW_CONTROL_TIMEOUT_MS
  )
};

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

export const clearAuthSession = () => {
  localStorage.removeItem(AUTH_TOKEN_KEY);
  localStorage.removeItem(AUTH_STUDENT_KEY);
};

api.interceptors.request.use((config) => {
  const token = getAuthToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

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

export const getProfile = async () => {
  const response = await api.get('/profile');
  return response.data;
};

export const updateProfile = async (data) => {
  const response = await api.put('/profile', data);
  return response.data;
};

export const getChatHistory = async (limit) => {
  const config = limit == null ? undefined : { params: { limit } };
  const response = await api.get('/chat/history', config);
  return response.data;
};

export const createTask = async (data) => {
  const response = await api.post('/tasks', data);
  return response.data;
};

export const completeTask = async (data) => {
  const response = await api.post('/task-complete', data);
  return response.data;
};

export const getStudent = async (email) => {
  const response = await api.get(`/students/${encodeURIComponent(email)}`);
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

export const getDeerflowStatus = async () => {
  const response = await api.get('/deerflow/status', deerflowControlRequestConfig);
  return response.data;
};

export const getSkills = async () => {
  const response = await api.get('/deerflow/skills', deerflowControlRequestConfig);
  return response.data;
};

export const toggleSkill = async (name, enabled) => {
  const response = await api.put(
    `/deerflow/skills/${encodeURIComponent(name)}`,
    { enabled },
    deerflowControlRequestConfig
  );
  return response.data;
};

export const getModels = async () => {
  const response = await api.get('/deerflow/models', deerflowControlRequestConfig);
  return response.data;
};

export const sendChat = async (data, config = {}) => {
  // data: { messages: [{role, content}], student_name }
  // DeerFlow 经 DeepSeek 推理可能耗时数十秒，超时需高于后端 httpx 的 120s
  const response = await api.post('/chat', data, { timeout: 130000, ...config });
  return response.data;
};

export const extractTask = async (data, config = {}) => {
  // data: { student_email, messages: [{role, content}] }
  const response = await api.post('/chat/extract-task', data, { timeout: 130000, ...config });
  return response.data;
};

export const healthCheck = async () => {
  const response = await api.get('/health');
  return response.data;
};

export default api;
