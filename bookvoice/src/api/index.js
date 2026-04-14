import axios from 'axios'

const api = axios.create({
  baseURL: '/api'
})

export const uploadFiles = (formData) => {
  return api.post('/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  })
}

export const getTasks = () => api.get('/tasks')

export const getTaskDetail = (taskId) => api.get(`/task/${taskId}`)

export const downloadTask = (taskId) => {
  return api.get(`/task/${taskId}/download`, { responseType: 'blob' })
}

export const getLogs = () => api.get('/logs')

export default api
