import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useNotificationStore = defineStore('notification', () => {
  const toasts = ref([])
  function add(type, message, duration = 4000) {
    const id = Date.now() + Math.random()
    toasts.value.push({ id, type, message })
    setTimeout(() => remove(id), duration)
  }
  function remove(id) { toasts.value = toasts.value.filter(t => t.id !== id) }
  return {
    toasts,
    remove,
    success: m => add('success', m),
    error:   m => add('error', m),
    warning: m => add('warning', m),
    info:    m => add('info', m),
  }
})
