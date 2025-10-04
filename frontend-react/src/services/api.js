import axios from 'axios';

const getApiUrl = () => {
  if (import.meta.env.VITE_API_URL) {
    return import.meta.env.VITE_API_URL;
  }
  
  if (typeof window !== 'undefined') {
    return `${window.location.origin}/api`;
  }
  
  return 'http://localhost:5000/api';
};

const API_BASE_URL = getApiUrl();

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      try {
        const refreshToken = localStorage.getItem('refresh_token');
        const response = await axios.post(`${API_BASE_URL}/auth/refresh`, {}, {
          headers: {
            Authorization: `Bearer ${refreshToken}`,
          },
        });

        const { access_token } = response.data;
        localStorage.setItem('access_token', access_token);

        originalRequest.headers.Authorization = `Bearer ${access_token}`;
        return api(originalRequest);
      } catch (refreshError) {
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        window.location.href = '/login';
        return Promise.reject(refreshError);
      }
    }

    return Promise.reject(error);
  }
);

export const authAPI = {
  login: (username, password) =>
    api.post('/auth/login', { username, password }),
  register: (userData) =>
    api.post('/auth/register', userData),
  getCurrentUser: () =>
    api.get('/auth/me'),
  logout: () =>
    api.post('/auth/logout'),
};

export const patientsAPI = {
  createPatient: (patientData) =>
    api.post('/patients', patientData),
  getPatients: () =>
    api.get('/patients'),
  getPatient: (patientId) =>
    api.get(`/patients/${patientId}`),
};

export const sessionsAPI = {
  startSession: (sessionData) =>
    api.post('/sessions/start', sessionData),
  getSession: (sessionId) =>
    api.get(`/sessions/${sessionId}`),
  updateSession: (sessionId, updateData) =>
    api.post(`/sessions/${sessionId}/update`, updateData),
  completeSession: (sessionId, completionData) =>
    api.post(`/sessions/${sessionId}/complete`, completionData),
};

export const assessmentsAPI = {
  createAssessment: (assessmentData) =>
    api.post('/assessments', assessmentData),
  getPatientAssessments: (patientId) =>
    api.get(`/assessments/patient/${patientId}`),
  getProgress: (patientId) =>
    api.get(`/assessments/progress/${patientId}`),
};

export default api;
