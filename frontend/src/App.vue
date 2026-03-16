<template>
  <div>
    <template v-if="authStore.isAuthenticated && route.path !== '/login'">
      <div class="app-layout">
        <AppSidebar />
        <div class="app-main">
          <AppNavbar :title="route.meta?.title || 'FlowEngine'" />
          <div class="app-content">
            <router-view />
          </div>
        </div>
      </div>
    </template>
    <template v-else>
      <router-view />
    </template>
    <ToastNotification />
  </div>
</template>

<script setup>
import { onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import AppSidebar from '@/components/layout/AppSidebar.vue'
import AppNavbar from '@/components/layout/AppNavbar.vue'
import ToastNotification from '@/components/common/ToastNotification.vue'

const route = useRoute()
const authStore = useAuthStore()

onMounted(async () => {
  if (authStore.isAuthenticated && !authStore.user) {
    try { await authStore.fetchProfile() } catch {}
  }
})
</script>
