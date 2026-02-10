import axios from 'axios'

const API_BASE = import.meta.env.PROD ? '/api' : 'http://127.0.0.1:8000/api'
const LOGIN_PATH = '/login'

const api = axios.create({
  baseURL: API_BASE,
  timeout: 120000,
})

// Request interceptor: inject JWT
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Response interceptor: auto refresh on 401
let isRefreshing = false
let refreshQueue = []

function processQueue(error, token) {
  refreshQueue.forEach((p) => {
    if (error) {
      p.reject(error)
    } else {
      p.resolve(token)
    }
  })
  refreshQueue = []
}

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config

    if (
      !error.response ||
      error.response.status !== 401 ||
      originalRequest._retry ||
      originalRequest.url?.includes('/auth/login') ||
      originalRequest.url?.includes('/auth/token/refresh') ||
      originalRequest.url?.includes('/auth/register') ||
      originalRequest.url?.includes('/auth/google')
    ) {
      return Promise.reject(error)
    }

    if (isRefreshing) {
      return new Promise((resolve, reject) => {
        refreshQueue.push({
          resolve: (token) => {
            originalRequest.headers.Authorization = `Bearer ${token}`
            resolve(api(originalRequest))
          },
          reject,
        })
      })
    }

    originalRequest._retry = true
    isRefreshing = true

    const refreshToken = localStorage.getItem('refresh_token')
    if (!refreshToken) {
      isRefreshing = false
      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
      window.location.href = LOGIN_PATH
      return Promise.reject(error)
    }

    try {
      const { data } = await axios.post(
        `${api.defaults.baseURL}/auth/token/refresh/`,
        { refresh: refreshToken }
      )
      const newAccess = data.access
      const newRefresh = data.refresh || refreshToken
      localStorage.setItem('access_token', newAccess)
      localStorage.setItem('refresh_token', newRefresh)
      originalRequest.headers.Authorization = `Bearer ${newAccess}`
      processQueue(null, newAccess)
      return api(originalRequest)
    } catch (refreshError) {
      processQueue(refreshError, null)
      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
      window.location.href = LOGIN_PATH
      return Promise.reject(refreshError)
    } finally {
      isRefreshing = false
    }
  }
)

export default api
