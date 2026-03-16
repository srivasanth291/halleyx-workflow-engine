import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import authService from '@/services/auth.service'

export const useAuthStore = defineStore('auth', () => {
  const user = ref(null)
  const accessToken = ref(localStorage.getItem('access_token'))
  const refreshToken = ref(localStorage.getItem('refresh_token'))
  const loading = ref(false)
  const isAuthenticated = computed(() => !!accessToken.value)

  function setTokens(access, refresh) {
    accessToken.value = access
    refreshToken.value = refresh
    localStorage.setItem('access_token', access)
    localStorage.setItem('refresh_token', refresh)
  }

  function clearAuth() {
    accessToken.value = null
    refreshToken.value = null
    user.value = null
    localStorage.clear()
  }

  async function register(data) {
    loading.value = true
    try {
      const res = await authService.register(data)
      setTokens(res.data.tokens.access, res.data.tokens.refresh)
      user.value = res.data.user
      return res.data
    } finally { loading.value = false }
  }

  async function login(data) {
    loading.value = true
    try {
      const res = await authService.login(data)
      setTokens(res.data.access, res.data.refresh)
      user.value = res.data.user
      return res.data
    } finally { loading.value = false }
  }

  async function logout() {
    try { await authService.logout({ refresh: refreshToken.value }) } catch {}
    clearAuth()
    window.location.href = '/login'
  }

  async function fetchProfile() {
    const res = await authService.getProfile()
    user.value = res.data
    return res.data
  }

  return { user, accessToken, refreshToken, loading, isAuthenticated, register, login, logout, fetchProfile }
})
