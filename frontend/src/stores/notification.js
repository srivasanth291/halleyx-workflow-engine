import { defineStore } from 'pinia'

export const useNotificationStore = defineStore('notification', {
  state: () => ({
    toasts: []
  }),
  actions: {
    addToast(type, message, duration = 4000) {
      const id = Date.now() + Math.random().toString(36).substr(2, 5)
      this.toasts.push({ id, type, message })
      setTimeout(() => {
        this.remove(id)
      }, duration)
    },
    success(message) { this.addToast('success', message) },
    error(message) { this.addToast('error', message) },
    warning(message) { this.addToast('warning', message) },
    info(message) { this.addToast('info', message) },
    remove(id) {
      this.toasts = this.toasts.filter(t => t.id !== id)
    }
  }
})
