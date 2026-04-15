import axios from 'axios'

const API_KEY = import.meta.env.VITE_API_KEY || 'dev-key-change-me'

const api = axios.create({
  baseURL: '/api',
  headers: {
    'X-API-Key': API_KEY
  }
})

export const uploadFiles = (formData) => {
  return api.post('/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data', 'X-API-Key': API_KEY }
  })
}

export const getTasks = () => api.get('/tasks')

export const getTaskDetail = (taskId) => api.get(`/task/${taskId}`)

export const downloadTask = (taskId) => {
  return api.get(`/task/${taskId}/download`, { responseType: 'blob' })
}

export const retryTask = (taskId) => api.post(`/task/${taskId}/retry`)

export const getLogs = () => api.get('/logs')

export const getLogContent = (filename) => api.get(`/logs/${filename}`)

export const deleteTask = (taskId) => api.delete(`/task/${taskId}`)

export const deleteFile = (fileId) => api.delete(`/file/${fileId}`)

export const getTaskProgress = (taskId) => api.get(`/task/${taskId}/progress`)

export default api
