import { defineStore } from 'pinia'
import notificationService from '@/services/notification.service'
import { useNotificationStore } from '@/stores/notification'

export const useEmailNotificationStore = defineStore('emailNotification', {
  state: () => ({
    notifications: [],
    stats: null,
    loading: false
  }),
  actions: {
    async fetchNotifications(params) {
      this.loading = true
      try {
        const res = await notificationService.getAll(params)
        this.notifications = res.data.results || res.data
        return res.data
      } finally {
        this.loading = false
      }
    },
    async fetchStats() {
      const res = await notificationService.getStats()
      this.stats = res.data
      return res.data
    },
    async sendTestEmail(recipient) {
      const res = await notificationService.sendTestEmail(recipient)
      if (res.data.success) {
        useNotificationStore().success('Test email sent!')
      } else {
        useNotificationStore().error(res.data.message || 'Error sending email')
      }
      return res.data
    }
  }
})
