import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  { path: '/', redirect: '/dashboard' },
  { path: '/dashboard', name: 'dashboard', component: () => import('../views/DashboardView.vue') },
  { path: '/login', name: 'login', component: () => import('../views/LoginView.vue'), meta: { public: true } },
  { path: '/workflows', name: 'workflows', component: () => import('../views/WorkflowListView.vue') },
  { path: '/workflows/new', name: 'workflow-new', component: () => import('../views/WorkflowEditorView.vue') },
  { path: '/workflows/:id/edit', name: 'workflow-edit', component: () => import('../views/WorkflowEditorView.vue') },
  { path: '/workflows/:workflowId/steps/:stepId/rules', name: 'rules', component: () => import('../views/RuleEditorView.vue') },
  { path: '/workflows/:id/execute', name: 'execute', component: () => import('../views/ExecutionView.vue') },
  { path: '/audit', name: 'audit', component: () => import('../views/AuditLogView.vue') },
  { path: '/notifications', name: 'notifications', component: () => import('../views/NotificationsView.vue') },
  { path: '/settings', name: 'settings', component: () => import('../views/SettingsView.vue') },
  { path: '/tasks', name: 'tasks', component: () => import('../views/TasksView.vue') },
]

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes
})

router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('access_token')
  const isPublic = to.meta.public

  if (!token && !isPublic) {
    next({ name: 'login' })
  } else if (token && to.name === 'login' && !isPublic) {
    // Only redirect from login to workflows if we are sure there is a token
    // Actually, just let it pass if it's already on login, 
    // or let the App.vue logic handle the profile check.
    next()
  } else {
    next()
  }
})

export default router
