import { defineStore } from 'pinia'
import { reactive, computed } from 'vue'
import api from '../api/client'

export const useAuthStore = defineStore('auth', () => {
  const state = reactive({
    accessToken: localStorage.getItem('access_token') || '',
    refreshToken: localStorage.getItem('refresh_token') || '',
    user: null,
    initialized: false,
    chefToken: localStorage.getItem('chef_token') || '',
  })

  const isLoggedIn = computed(() => !!state.accessToken)
  const isChefAuthed = computed(() => !!state.chefToken)
  const user = computed(() => state.user)

  function setTokens(access, refresh) {
    state.accessToken = access
    state.refreshToken = refresh
    localStorage.setItem('access_token', access)
    localStorage.setItem('refresh_token', refresh)
  }

  function clearTokens() {
    state.accessToken = ''
    state.refreshToken = ''
    state.user = null
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
  }

  async function login(email, password) {
    const { data } = await api.post('/auth/login/', {
      username: email,
      password,
    })
    setTokens(data.access, data.refresh)
    await fetchProfile()
  }

  async function googleLogin(idToken) {
    const { data } = await api.post('/auth/google/', { id_token: idToken })
    setTokens(data.access, data.refresh)
    state.user = data.user
  }

  async function register(email, password, nickname) {
    await api.post('/auth/register/', { email, password, nickname })
    await login(email, password)
  }

  function logout() {
    clearTokens()
    state.chefToken = ''
    localStorage.removeItem('chef_token')
    localStorage.removeItem('chef_logged_in')
  }

  async function fetchProfile() {
    try {
      const { data } = await api.get('/auth/me/')
      state.user = data
    } catch {
      // Token expired or invalid — will be handled by interceptor
    }
  }

  async function init() {
    if (state.initialized) return
    if (state.accessToken) {
      await fetchProfile()
    }
    state.initialized = true
  }

  // Chef second-level auth
  function chefLogin(token) {
    state.chefToken = token
    localStorage.setItem('chef_token', token)
    localStorage.setItem('chef_logged_in', 'true')
  }

  function chefLogout() {
    state.chefToken = ''
    localStorage.removeItem('chef_token')
    localStorage.removeItem('chef_logged_in')
  }

  function checkChefAuth() {
    return !!state.chefToken
  }

  return {
    state,
    isLoggedIn,
    isChefAuthed,
    user,
    setTokens,
    clearTokens,
    login,
    googleLogin,
    register,
    logout,
    fetchProfile,
    init,
    chefLogin,
    chefLogout,
    checkChefAuth,
  }
})

// Backward-compatible reactive auth object for legacy components
export const auth = reactive({
  get isLoggedIn() {
    return !!localStorage.getItem('chef_token')
  },
  get token() {
    return localStorage.getItem('chef_token') || ''
  },
  login(token) {
    localStorage.setItem('chef_token', token)
    localStorage.setItem('chef_logged_in', 'true')
  },
  logout() {
    localStorage.removeItem('chef_token')
    localStorage.removeItem('chef_logged_in')
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
  },
  checkAuth() {
    return !!localStorage.getItem('chef_token')
  },
})
