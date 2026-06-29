import axios from 'axios';

const api = axios.create({
  baseURL: '/api',
  timeout: 30000,
  headers: { 'Content-Type': 'application/json' },
});

// Analysis
export const analyzeCode = (data: { code: string; language?: string; use_llm?: boolean }) =>
  api.post('/analysis/analyze', data);

export const getLanguages = () => api.get('/analysis/languages');

// Documents
export const uploadDocument = (formData: FormData) =>
  api.post('/documents/upload', formData, { headers: { 'Content-Type': 'multipart/form-data' } });

export const generatePlan = (data: any) => api.post('/documents/generate-plan', data);
export const getPlans = (params?: any) => api.get('/documents/plans', { params });
export const getPlan = (id: string) => api.get(`/documents/plans/${id}`);
export const reviewPlan = (id: string, data: any) => api.post(`/documents/plans/${id}/review`, data);

// Tests
export const generateTests = (data: any) => api.post('/tests/generate', data);
export const runTests = (data: any) => api.post('/tests/run', data);
export const generateAndRun = (data: any) => api.post('/tests/generate-and-run', data);

// Scoring
export const getScoringTemplates = () => api.get('/scoring/templates');
export const computeScore = (data: any) => api.post('/scoring/compute', data);
export const compareSubmissions = (data: any[]) => api.post('/scoring/compare', data);

// LLM
export const getLLMProviders = () => api.get('/llm/providers');
export const addLLMProvider = (data: any) => api.post('/llm/providers', data);
export const testLLMProvider = (data: any) => api.post('/llm/providers/test', data);
export const removeLLMProvider = (type: string, model: string) =>
  api.delete(`/llm/providers/${type}/${model}`);

// Batch
export const submitBatch = (data: any) => api.post('/batch/submit', data);
export const getBatchStatus = () => api.get('/batch/status');

// Health
export const healthCheck = () => api.get('/health');

// Projects
export const createProject = (data: { name: string; description?: string; language?: string }) =>
  api.post('/projects', data);

export const getProjects = () => api.get('/projects');

export const getProject = (id: string) => api.get(`/projects/${id}`);

// Submissions
export const uploadSubmission = (projectId: string, formData: FormData) =>
  api.post(`/projects/${projectId}/submissions/upload`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });

export const getSubmissions = (projectId: string) =>
  api.get(`/projects/${projectId}/submissions`);

export default api;