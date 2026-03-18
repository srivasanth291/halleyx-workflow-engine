<template>
  <div class="navbar">
    <div class="navbar-left">
      <div class="page-title">{{ routeName }}</div>
    </div>
    <div class="navbar-right">
      <router-link to="/notifications" class="bell-btn position-relative">
        🔔
        <span v-if="unreadCount > 0" class="badge-count">{{ unreadCount }}</span>
      </router-link>
      <div class="separator"></div>
      <div class="user-profile">
        <div class="avatar-small">{{ initials }}</div>
        <div class="user-name">{{ authStore.user?.full_name || authStore.user?.email }}</div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useEmailNotificationStore } from '@/stores/emailNotification'

const route = useRoute()
const authStore = useAuthStore()
const notifStore = useEmailNotificationStore()

const routeName = computed(() => {
  const defaultNames = {
    workflows: 'Workflows',
    'workflow-new': 'Create Workflow',
    'workflow-edit': 'Edit Workflow',
    rules: 'Rules Config',
    execute: 'Execute Workflow',
    audit: 'Audit Log',
    notifications: 'Notifications',
    settings: 'Settings'
  }
  return defaultNames[route.name] || 'FlowEngine'
})

const initials = computed(() => {
  if (!authStore.user) return ''
  const first = authStore.user.first_name ? authStore.user.first_name[0] : ''
  const last = authStore.user.last_name ? authStore.user.last_name[0] : ''
  return (first + last).toUpperCase() || authStore.user.email[0].toUpperCase()
})

const unreadCount = computed(() => {
  return notifStore.stats?.total_pending || 0
})

onMounted(() => {
  if (authStore.user) {
    notifStore.fetchStats()
  }
})
</script>

<style scoped>
.navbar {
  height: var(--navbar-height);
  background: var(--bg-card);
  border-bottom: 1px solid var(--border-color);
  padding: 0 24px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  position: fixed;
  top: 0;
  left: var(--sidebar-width);
  right: 0;
  z-index: 90;
}
.page-title {
  font-size: 17px;
  font-weight: bold;
}
.navbar-right {
  display: flex;
  align-items: center;
  gap: 16px;
}
.bell-btn {
  background: transparent;
  border: none;
  font-size: 20px;
  cursor: pointer;
  text-decoration: none;
  position: relative;
}
.position-relative { position: relative; }
.badge-count {
  position: absolute;
  top: -4px;
  right: -8px;
  background: var(--error-text);
  color: white;
  font-size: 10px;
  font-weight: bold;
  padding: 2px 6px;
  border-radius: 10px;
}
.separator {
  width: 1px;
  height: 24px;
  background: var(--border-color);
}
.user-profile {
  display: flex;
  align-items: center;
  gap: 8px;
}
.avatar-small {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: var(--accent-green-light);
  color: var(--accent-green-dark);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: bold;
}
.user-name {
  font-size: 14px;
  font-weight: 500;
}
</style>
