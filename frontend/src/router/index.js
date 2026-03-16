import { createRouter, createWebHistory } from 'vue-router'
import LoginView            from '@/views/LoginView.vue'
import WorkflowListView     from '@/views/WorkflowListView.vue'
import WorkflowEditorView   from '@/views/WorkflowEditorView.vue'
import RuleEditorView       from '@/views/RuleEditorView.vue'
import ExecutionView        from '@/views/ExecutionView.vue'
import AuditLogView         from '@/views/AuditLogView.vue'

const routes = [
  { path: '/', redirect: '/workflows' },
  { path: '/login', component: LoginView, meta: { public: true } },
  { path: '/workflows', component: WorkflowListView, meta: { title: 'Workflows' } },
  { path: '/workflows/new', component: WorkflowEditorView, meta: { title: 'Create Workflow' } },
  { path: '/workflows/:id/edit', component: WorkflowEditorView, meta: { title: 'Edit Workflow' } },
  { path: '/workflows/:workflowId/steps/:stepId/rules', component: RuleEditorView, meta: { title: 'Rule Editor' } },
  { path: '/workflows/:id/execute', component: ExecutionView, meta: { title: 'Execute Workflow' } },
  { path: '/audit', component: AuditLogView, meta: { title: 'Audit Log' } },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach(to => {
  const token = localStorage.getItem('access_token')
  if (!to.meta.public && !token) return '/login'
  if (to.path === '/login' && token) return '/workflows'
})

export default router
