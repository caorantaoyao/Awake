import axios from 'axios';

const api = axios.create({
  baseURL: '/api',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json'
  }
});

export const registerStudent = async (data) => {
  const response = await api.post('/register', data);
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

export const sendChat = async (data) => {
  // data: { messages: [{role, content}], student_name }
  // DeerFlow 经 DeepSeek 推理可能耗时数十秒，超时需高于后端 httpx 的 120s
  const response = await api.post('/chat', data, { timeout: 130000 });
  return response.data;
};

export const extractTask = async (data) => {
  // data: { student_email, messages: [{role, content}] }
  const response = await api.post('/chat/extract-task', data, { timeout: 130000 });
  return response.data;
};

export const healthCheck = async () => {
  const response = await api.get('/health');
  return response.data;
};

export default api;
