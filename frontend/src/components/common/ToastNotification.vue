<template>
  <div class="toast-container">
    <TransitionGroup name="toast-list">
      <div v-for="toast in store.toasts" :key="toast.id" :class="['toast', `toast-${toast.type}`]">
        <div class="toast-icon">{{ icons[toast.type] }}</div>
        <div class="toast-message">{{ toast.message }}</div>
        <button class="toast-close" @click="store.remove(toast.id)">✕</button>
      </div>
    </TransitionGroup>
  </div>
</template>

<script setup>
import { useNotificationStore } from '@/stores/notification'

const store = useNotificationStore()

const icons = {
  success: '✅',
  error: '❌',
  warning: '⚠️',
  info: 'ℹ️'
}
</script>

<style scoped>
.toast-container {
  position: fixed;
  top: 24px;
  right: 24px;
  z-index: 9999;
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.toast {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px 16px;
  border-radius: var(--card-radius);
  background: white;
  box-shadow: 0 4px 12px rgba(0,0,0,0.15);
  min-width: 300px;
  border-left: 4px solid var(--border-color);
}
.toast-success { border-left-color: var(--success-text); }
.toast-error { border-left-color: var(--error-text); }
.toast-warning { border-left-color: var(--warning-text); }
.toast-info { border-left-color: var(--info-text); }

.toast-message { flex: 1; font-size: 14px; font-weight: 500; color: var(--text-primary); }
.toast-close {
  background: transparent;
  border: none;
  color: var(--text-muted);
  cursor: pointer;
  padding: 4px;
}
.toast-close:hover { color: var(--text-primary); }

.toast-list-enter-active,
.toast-list-leave-active {
  transition: all 0.3s ease;
}
.toast-list-enter-from {
  opacity: 0;
  transform: translateX(30px);
}
.toast-list-leave-to {
  opacity: 0;
  transform: translateX(30px);
}
</style>
