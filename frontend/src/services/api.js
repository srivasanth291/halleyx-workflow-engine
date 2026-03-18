import axios from 'axios'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api',
})

api.interceptors.request.use(config => {
  const token = localStorage.getItem('access_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

api.interceptors.response.use(
  response => response,
  async error => {
    const originalRequest = error.config
    
    if (error.response?.status === 401 && !originalRequest._retry && originalRequest.url !== '/auth/login/') {
      originalRequest._retry = true
      
      try {
        const refreshToken = localStorage.getItem('refresh_token')
        if (refreshToken) {
          const res = await axios.post(`${api.defaults.baseURL}/auth/token/refresh/`, { refresh: refreshToken })
          localStorage.setItem('access_token', res.data.access)
          originalRequest.headers.Authorization = `Bearer ${res.data.access}`
          return api(originalRequest)
        }
      } catch (e) {
        localStorage.removeItem('access_token')
        localStorage.removeItem('refresh_token')
        window.location.href = '/login'
      }
    }
    
    const { useNotificationStore } = await import('@/stores/notification')
    const notifStore = useNotificationStore()
    const msg = error.response?.data?.detail || error.response?.data?.error || error.response?.data?.non_field_errors?.[0] || error.message || 'An error occurred'
    
    if (error.response?.status !== 401) {
        notifStore.error(msg)
    }
    
    return Promise.reject(error)
  }
)

export default api
