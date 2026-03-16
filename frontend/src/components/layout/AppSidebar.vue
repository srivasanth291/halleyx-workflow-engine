<template>
  <aside class="sidebar">
    <div class="sb-logo">
      <div class="sb-logo-icon">⚡</div>
      <span class="sb-logo-text">FlowEngine</span>
    </div>
    <nav class="sb-nav">
      <router-link
        v-for="item in navItems"
        :key="item.path"
        :to="item.path"
        class="nav-link"
        active-class="nav-link-active"
      >
        <span v-html="item.icon" class="nav-icon"></span>
        <span>{{ item.label }}</span>
      </router-link>
    </nav>
    <div class="sb-bottom">
      <div class="sb-company">
        <span class="sb-company-name">{{ user?.company_name || 'Company' }}</span>
        <span class="badge badge-success" style="font-size:11px">{{ user?.company_plan || 'Pro' }}</span>
      </div>
      <div class="sb-user">
        <div class="sb-avatar">{{ initials }}</div>
        <span class="sb-uname">{{ user?.full_name || user?.email || 'User' }}</span>
        <button class="btn-icon danger" @click="authStore.logout()" title="Logout">
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M9 21H5a2 2 0 01-2-2V5a2 2 0 012-2h4"/>
            <polyline points="16 17 21 12 16 7"/>
            <line x1="21" y1="12" x2="9" y2="12"/>
          </svg>
        </button>
      </div>
    </div>
  </aside>
</template>

<script setup>
import { computed } from 'vue'
import { useAuthStore } from '@/stores/auth'

const authStore = useAuthStore()
const user = computed(() => authStore.user)
const initials = computed(() => {
  const n = user.value?.full_name || user.value?.email || 'U'
  return n.split(' ').map(w => w[0]).join('').toUpperCase().slice(0, 2)
})

const navItems = [
  {
    path: '/workflows',
    label: 'Workflows',
    icon: `<svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
      <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/>
      <polyline points="14 2 14 8 20 8"/>
      <line x1="16" y1="13" x2="8" y2="13"/>
      <line x1="16" y1="17" x2="8" y2="17"/>
    </svg>`
  },
  {
    path: '/audit',
    label: 'Audit Log',
    icon: `<svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
      <polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/>
    </svg>`
  },
]
</script>

<style scoped>
.sidebar {
  position: fixed; top: 0; left: 0;
  width: var(--sidebar-width); height: 100vh;
  background: var(--bg-sidebar); border-right: 1px solid var(--border-color);
  display: flex; flex-direction: column; z-index: 100;
}
.sb-logo {
  display: flex; align-items: center; gap: 10px;
  padding: 18px 16px; border-bottom: 1px solid var(--border-color);
}
.sb-logo-icon {
  width: 30px; height: 30px; background: var(--accent-green);
  border-radius: 7px; display: flex; align-items: center;
  justify-content: center; font-size: 14px; color: white;
}
.sb-logo-text { font-size: 16px; font-weight: 700; }
.sb-nav {
  padding: 12px 8px; flex: 1;
  display: flex; flex-direction: column; gap: 2px;
}
.nav-link {
  display: flex; align-items: center; gap: 10px;
  padding: 9px 10px; border-radius: 8px;
  font-size: 14px; font-weight: 500;
  color: var(--text-secondary); text-decoration: none;
  transition: all .15s; border-left: 3px solid transparent;
}
.nav-link:hover { background: var(--bg-page); color: var(--text-primary); }
.nav-link-active {
  background: var(--accent-green-light) !important;
  color: var(--accent-green) !important;
  border-left-color: var(--accent-green) !important;
}
.nav-icon { display: flex; align-items: center; }
.sb-bottom {
  padding: 14px 12px; border-top: 1px solid var(--border-color);
  display: flex; flex-direction: column; gap: 10px;
}
.sb-company {
  background: var(--bg-page); border-radius: 8px;
  padding: 10px 12px; display: flex;
  align-items: center; justify-content: space-between;
}
.sb-company-name {
  font-size: 13px; font-weight: 600;
  overflow: hidden; text-overflow: ellipsis;
  white-space: nowrap; max-width: 130px;
}
.sb-user { display: flex; align-items: center; gap: 8px; }
.sb-avatar {
  width: 30px; height: 30px; background: var(--accent-green);
  border-radius: 50%; display: flex; align-items: center;
  justify-content: center; font-size: 11px; font-weight: 700;
  color: white; flex-shrink: 0;
}
.sb-uname {
  flex: 1; font-size: 13px; font-weight: 500;
  overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
}
</style>
