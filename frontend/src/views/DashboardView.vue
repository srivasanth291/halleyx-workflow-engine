<template>
  <div class="dashboard-page">
    <div class="mb-8">
      <h1 class="text-bold m-0" style="font-size: 28px;">Welcome back, {{ user?.first_name || 'User' }}!</h1>
      <p class="text-gray m-0 mt-1">Here's what's happening in your organization today.</p>
    </div>

    <!-- Stats Row -->
    <div class="stats-grid mb-8">
      <div class="stat-card glass shadow-hover">
        <div class="stat-icon bg-indigo-gradient">📊</div>
        <div class="stat-info">
          <span class="stat-label">Active Workflows</span>
          <span class="stat-value">{{ store.workflows.length }}</span>
        </div>
      </div>
      <div class="stat-card glass shadow-hover">
        <div class="stat-icon bg-green-gradient">✅</div>
        <div class="stat-info">
          <span class="stat-label">Executions Today</span>
          <span class="stat-value">{{ execStore.auditStats.total || 0 }}</span>
        </div>
      </div>
      <div class="stat-card glass shadow-hover">
        <div class="stat-icon bg-amber-gradient">⏳</div>
        <div class="stat-info">
          <span class="stat-label">Pending Approvals</span>
          <span class="stat-value">{{ execStore.auditStats.pending || 0 }}</span>
        </div>
      </div>
      <div class="stat-card glass shadow-hover">
        <div class="stat-icon bg-red-gradient">🛑</div>
        <div class="stat-info">
          <span class="stat-label">Failed Tasks</span>
          <span class="stat-value">{{ execStore.auditStats.failed || 0 }}</span>
        </div>
      </div>
    </div>

    <div class="dashboard-content-grid">
      <!-- Recent Executions -->
      <div class="card glass">
        <div class="flex items-center justify-between mb-6">
          <h2 class="text-bold m-0" style="font-size: 18px;">Recent Executions</h2>
          <router-link to="/audit" class="text-indigo text-bold text-sm" style="text-decoration: none;">View All</router-link>
        </div>
        <div class="mini-table">
          <div v-for="ex in recentExecutions" :key="ex.id" class="mini-row">
            <div class="flex items-center gap-3">
               <div class="status-dot" :class="ex.status"></div>
               <div class="flex flex-col">
                 <span class="text-bold text-sm">{{ ex.workflow_name }}</span>
                 <span class="text-xs text-gray">Started {{ formatDate(ex.started_at) }}</span>
               </div>
            </div>
            <StatusBadge :status="ex.status" />
          </div>
          <div v-if="recentExecutions.length === 0" class="text-center py-8 text-gray">
            No recent activity.
          </div>
        </div>
      </div>

      <!-- Quick Actions -->
      <div class="card glass">
        <h2 class="text-bold mb-6" style="font-size: 18px;">Quick Actions</h2>
        <div class="actions-list">
          <button class="action-btn glass" @click="$router.push('/workflows/new')">
            <span class="action-icon">➕</span>
            <div class="text-left">
              <div class="text-bold text-sm">Create Workflow</div>
              <div class="text-xs text-gray">Design a new process</div>
            </div>
          </button>
          <button class="action-btn glass" @click="$router.push('/settings')">
            <span class="action-icon">👥</span>
            <div class="text-left">
              <div class="text-bold text-sm">Invite Team</div>
              <div class="text-xs text-gray">Add collaborators</div>
            </div>
          </button>
          <button class="action-btn glass" @click="$router.push('/notifications')">
            <span class="action-icon">🔔</span>
            <div class="text-left">
              <div class="text-bold text-sm">System Logs</div>
              <div class="text-xs text-gray">Check notifications</div>
            </div>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, onUnmounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { useWorkflowStore } from '@/stores/workflow'
import { useExecutionStore } from '@/stores/execution'
import StatusBadge from '@/components/common/StatusBadge.vue'

const auth = useAuthStore()
const store = useWorkflowStore()
const execStore = useExecutionStore()

const user = computed(() => auth.user)
const recentExecutions = computed(() => execStore.executions?.slice(0, 5) || [])
let refreshInterval = null

const loadData = () => {
  store.fetchWorkflows()
  execStore.fetchAuditLog()
}

onMounted(() => {
  loadData()
  refreshInterval = setInterval(loadData, 60000)
})

onUnmounted(() => {
  clearInterval(refreshInterval)
})

const formatDate = (dateStr) => {
  if (!dateStr) return ''
  const d = new Date(dateStr)
  return d.toLocaleDateString()
}
</script>

<style scoped>
.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 20px;
}
.stat-card {
  padding: 24px;
  display: flex;
  align-items: center;
  gap: 16px;
  border-radius: 20px;
  transition: transform 0.2s;
}
.stat-card:hover {
  transform: translateY(-5px);
}
.stat-icon {
  width: 50px; height: 50px;
  border-radius: 12px;
  display: flex; align-items: center; justify-content: center;
  font-size: 24px;
}
.bg-indigo-gradient { background: linear-gradient(135deg, #6366f1 0%, #4f46e5 100%); color: white; }
.bg-green-gradient { background: linear-gradient(135deg, #10b981 0%, #059669 100%); color: white; }
.bg-amber-gradient { background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%); color: white; }
.bg-red-gradient { background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%); color: white; }

.stat-info { display: flex; flex-direction: column; }
.stat-label { font-size: 13px; color: var(--text-muted); font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; }
.stat-value { font-size: 24px; font-weight: 800; color: var(--text-primary); }

.dashboard-content-grid {
  display: grid;
  grid-template-columns: 2fr 1fr;
  gap: 24px;
}

.mini-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 0;
  border-bottom: 1px solid rgba(0,0,0,0.05);
}
.mini-row:last-child { border-bottom: none; }

.status-dot { width: 8px; height: 8px; border-radius: 50%; background: #CBD5E1; }
.status-dot.completed { background: #10B981; box-shadow: 0 0 8px #10B981; }
.status-dot.in_progress { background: #6366F1; box-shadow: 0 0 8px #6366F1; }
.status-dot.failed { background: #EF4444; box-shadow: 0 0 8px #EF4444; }

.actions-list { display: flex; flex-direction: column; gap: 12px; }
.action-btn {
  display: flex; align-items: center; gap: 16px;
  padding: 16px; border-radius: 16px;
  border: 1px solid rgba(0,0,0,0.05);
  cursor: pointer; text-align: left;
  transition: all 0.2s;
}
.action-btn:hover { background: rgba(99, 102, 241, 0.05); border-color: rgba(99, 102, 241, 0.2); }
.action-icon { font-size: 20px; }
</style>
