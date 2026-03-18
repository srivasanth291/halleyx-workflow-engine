import { defineStore } from 'pinia'
import settingsService from '@/services/settings.service'
import authService from '@/services/auth.service'
import { useNotificationStore } from '@/stores/notification'

export const useSettingsStore = defineStore('settings', {
  state: () => ({
    emailSettings: null,
    companySettings: null,
    notifSettings: null,
    users: [],
    roles: [],
    loading: false
  }),
  actions: {
    async fetchRoles() {
      const res = await authService.getRoles()
      this.roles = res.data.results || res.data
      return this.roles
    },
    async createRole(data) {
      const res = await authService.createRole(data)
      useNotificationStore().success('Role created successfully')
      await this.fetchRoles()
      return res.data
    },
    async updateRole(id, data) {
      const res = await authService.updateRole(id, data)
      useNotificationStore().success('Role updated successfully')
      await this.fetchRoles()
      return res.data
    },
    async deleteRole(id) {
      const res = await authService.deleteRole(id)
      useNotificationStore().success('Role deleted successfully')
      await this.fetchRoles()
      return res.data
    },
    async fetchEmailSettings() {
      const res = await settingsService.getEmail()
      this.emailSettings = res.data
      return res.data
    },
    async saveEmailSettings(data) {
      const res = await settingsService.saveEmail(data)
      this.emailSettings = res.data
      useNotificationStore().success('Email settings saved')
      return res.data
    },
    async fetchCompanySettings() {
      const res = await settingsService.getCompany()
      this.companySettings = res.data
      return res.data
    },
    async saveCompanySettings(data) {
      const res = await settingsService.saveCompany(data)
      this.companySettings = res.data
      useNotificationStore().success('Company settings saved')
      return res.data
    },
    async fetchNotifSettings() {
      const res = await settingsService.getNotifSettings()
      this.notifSettings = res.data
      return res.data
    },
    async saveNotifSettings(data) {
      const res = await settingsService.saveNotifSettings(data)
      this.notifSettings = res.data
      useNotificationStore().success('Notification settings saved')
      return res.data
    },
    async fetchUsers() {
      this.loading = true
      try {
        const res = await authService.getUsers()
        this.users = res.data.results || res.data
      } finally {
        this.loading = false
      }
    },
    async createUser(data) {
      const res = await authService.createUser(data)
      useNotificationStore().success('User created')
      await this.fetchUsers()
      return res.data
    },
    async updateUserRole(id, role) {
      const res = await authService.updateUser(id, { role })
      useNotificationStore().success('User role updated')
      await this.fetchUsers()
      return res.data
    },
    async deactivateUser(id) {
      const res = await authService.deactivateUser(id)
      useNotificationStore().success('User deactivated')
      await this.fetchUsers()
      return res.data
    }
  }
})
