<template>
  <div class="sidebar">
    <div class="sidebar-header">
      <div class="logo-icon">⚡</div>
      <div class="logo-text">FlowEngine</div>
    </div>
    
    <div class="sidebar-nav">
      <router-link to="/dashboard" class="nav-item">
        <span class="icon">🏠</span> Dashboard
      </router-link>
      <router-link to="/tasks" class="nav-item">
        <span class="icon">📋</span> Tasks
      </router-link>
      <router-link to="/workflows" class="nav-item">
        <span class="icon">📋</span> Workflows
      </router-link>
      <router-link to="/audit" class="nav-item">
        <span class="icon">📊</span> Audit Log
      </router-link>
      <router-link to="/notifications" class="nav-item">
        <span class="icon">🔔</span> Notifications
      </router-link>
      <router-link to="/settings" class="nav-item">
        <span class="icon">⚙️</span> Settings
      </router-link>
    </div>

    <div class="sidebar-footer" v-if="authStore.user">
      <div class="company-card">
        <div class="text-bold text-sm">{{ authStore.user.company_name }}</div>
        <div class="badge badge-green mt-1">{{ planDisplay }}</div>
      </div>
      <div class="user-row mt-4">
        <div class="avatar">{{ initials }}</div>
        <div class="user-info flex-1">
          <div class="text-sm text-bold truncate">{{ authStore.user.full_name || authStore.user.email }}</div>
        </div>
        <button class="btn-icon text-red" @click="handleLogout" title="Logout">
          🚪
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const authStore = useAuthStore()
const router = useRouter()

const initials = computed(() => {
  if (!authStore.user) return ''
  const first = authStore.user.first_name ? authStore.user.first_name[0] : ''
  const last = authStore.user.last_name ? authStore.user.last_name[0] : ''
  return (first + last).toUpperCase() || authStore.user.email[0].toUpperCase()
})

const planDisplay = computed(() => {
    const plan = authStore.user?.company_plan || 'pro'
    return plan.charAt(0).toUpperCase() + plan.slice(1)
})

const handleLogout = async () => {
  await authStore.logout()
  router.push('/login')
}
</script>

<style scoped>
.sidebar {
  width: var(--sidebar-width);
  background: var(--bg-sidebar);
  border-right: 1px solid var(--border-color);
  position: fixed;
  top: 0;
  bottom: 0;
  left: 0;
  display: flex;
  flex-direction: column;
  z-index: 100;
}
.sidebar-header {
  padding: 20px;
  display: flex;
  align-items: center;
  gap: 12px;
}
.logo-icon {
  width: 32px;
  height: 32px;
  background: var(--accent-green);
  color: white;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: bold;
}
.logo-text {
  font-size: 17px;
  font-weight: bold;
}
.sidebar-nav {
  padding: 12px 8px;
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.nav-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 12px;
  border-radius: 8px;
  text-decoration: none;
  color: var(--text-secondary);
  font-size: 14px;
  font-weight: 500;
  transition: all 0.2s;
  border-left: 3px solid transparent;
}
.nav-item:hover {
  background: var(--bg-page);
  color: var(--text-primary);
}
.nav-item.router-link-active {
  background: var(--accent-green-light);
  color: var(--accent-green);
  border-left-color: var(--accent-green);
}
.icon { font-size: 17px; }
.sidebar-footer {
  border-top: 1px solid var(--border-color);
  padding: 14px;
}
.company-card {
  background: var(--bg-page);
  border-radius: 8px;
  padding: 12px;
}
.user-row {
  display: flex;
  align-items: center;
  gap: 12px;
}
.avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: var(--accent-green);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: bold;
}
.user-info { overflow: hidden; }
.truncate { white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.text-red:hover { color: var(--error-text); }
</style>
