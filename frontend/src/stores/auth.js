import { defineStore } from 'pinia'
import authService from '@/services/auth.service'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    user: null,
    loading: true
  }),
  getters: {
    // Role is a FK object {id, name, is_admin} — not a string
    isAdmin: (state) => {
      if (!state.user) return false
      const role = state.user.role
      if (!role) return false
      // Support both FK object (role.is_admin) and legacy string ('admin')
      if (typeof role === 'object') return role.is_admin === true
      return role === 'admin' || role === 'super_admin'
    }
  },
  actions: {
    async login(data) {
      const response = await authService.login(data)
      localStorage.setItem('access_token', response.data.access)
      localStorage.setItem('refresh_token', response.data.refresh)
      this.user = response.data.user
    },
    async logout() {
      try {
        const refresh = localStorage.getItem('refresh_token')
        if (refresh) await authService.logout({ refresh })
      } catch (e) {
        console.error(e)
      } finally {
        localStorage.removeItem('access_token')
        localStorage.removeItem('refresh_token')
        this.user = null
      }
    },
    async fetchProfile() {
      try {
        const response = await authService.getProfile()
        this.user = response.data
      } catch (e) {
        localStorage.removeItem('access_token')
        localStorage.removeItem('refresh_token')
        this.user = null
        throw e
      } finally {
        this.loading = false
      }
    }
  }
})
