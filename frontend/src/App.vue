<template>
  <div v-if="authStore.loading" class="flex items-center justify-center p-4 min-h-screen">
    <div class="spinner text-center text-gray">Loading FlowEngine...</div>
  </div>
  <div v-else class="app-wrapper">
    <template v-if="isAuthenticated && isNotLoginRoute">
      <AppSidebar />
      <div class="main-content">
        <AppNavbar />
        <div class="page-container">
          <router-view />
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
import { computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import AppSidebar from '@/components/layout/AppSidebar.vue'
import AppNavbar from '@/components/layout/AppNavbar.vue'
import ToastNotification from '@/components/common/ToastNotification.vue'

const authStore = useAuthStore()
const route = useRoute()
const router = useRouter()

const isAuthenticated = computed(() => !!authStore.user)
const isNotLoginRoute = computed(() => route.path !== '/login')

onMounted(async () => {
  if (localStorage.getItem('access_token')) {
    try {
      await authStore.fetchProfile()
    } catch {
      router.push('/login')
    }
  } else {
    authStore.loading = false
  }
})
</script>

<style scoped>
.min-h-screen { min-height: 100vh; }
.app-wrapper {
  display: flex;
  min-height: 100vh;
}
.main-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  margin-left: var(--sidebar-width);
}
.page-container {
  padding: 24px;
  margin-top: var(--navbar-height);
  flex: 1;
}
</style>
