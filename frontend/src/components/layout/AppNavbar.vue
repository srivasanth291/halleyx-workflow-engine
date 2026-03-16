<template>
  <header class="navbar">
    <h1 class="nb-title">{{ title }}</h1>
    <div class="nb-right">
      <button class="btn-icon">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M18 8A6 6 0 006 8c0 7-3 9-3 9h18s-3-2-3-9"/>
          <path d="M13.73 21a2 2 0 01-3.46 0"/>
        </svg>
      </button>
      <div class="nb-sep"></div>
      <div class="nb-user">
        <div class="nb-avatar">{{ initials }}</div>
        <span>{{ user?.full_name || user?.email || '' }}</span>
      </div>
    </div>
  </header>
</template>

<script setup>
import { computed } from 'vue'
import { useAuthStore } from '@/stores/auth'

defineProps({ title: String })

const authStore = useAuthStore()
const user = computed(() => authStore.user)
const initials = computed(() => {
  const n = user.value?.full_name || user.value?.email || 'U'
  return n.split(' ').map(w => w[0]).join('').toUpperCase().slice(0, 2)
})
</script>

<style scoped>
.navbar {
  position: fixed; top: 0; left: var(--sidebar-width); right: 0;
  height: var(--navbar-height); background: var(--bg-navbar);
  border-bottom: 1px solid var(--border-color);
  display: flex; align-items: center; justify-content: space-between;
  padding: 0 24px; z-index: 99;
}
.nb-title { font-size: 17px; font-weight: 700; }
.nb-right { display: flex; align-items: center; gap: 12px; }
.nb-sep { width: 1px; height: 22px; background: var(--border-color); }
.nb-user { display: flex; align-items: center; gap: 8px; font-size: 14px; font-weight: 500; }
.nb-avatar {
  width: 30px; height: 30px; background: var(--accent-green);
  border-radius: 50%; display: flex; align-items: center;
  justify-content: center; font-size: 11px; font-weight: 700; color: white;
}
</style>
