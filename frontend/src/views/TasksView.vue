<template>
  <div class="tasks-page">
    <div class="flex items-center justify-between mb-6">
      <div>
        <h1 class="text-bold m-0" style="font-size: 24px;">My Tasks</h1>
        <p class="text-gray m-0 mt-1">Pending approvals and actions required from you</p>
      </div>
      <button class="btn btn-outlined" @click="fetchTasks">
        <span v-if="loading" class="spinner">🌀</span>
        <span v-else>🔄 Refresh</span>
      </button>
    </div>

    <div v-if="loading" class="text-center p-12">
      <span class="spinner" style="font-size: 32px;">🌀</span>
      <p class="text-gray mt-4">Fetching your tasks...</p>
    </div>

    <div v-else-if="tasks.length === 0" class="card text-center py-10 glass">
      <div class="text-gray mb-4" style="font-size: 48px;">✅</div>
      <h3 class="text-bold mb-2 m-0">All caught up!</h3>
      <p class="text-gray mt-1">You have no pending tasks at the moment.</p>
    </div>

    <div v-else class="grid-card">
      <div v-for="task in tasks" :key="task.id" class="task-card glass shadow-hover">
        <div class="task-header">
           <div class="flex flex-col">
             <span class="text-bold task-title">{{ task.workflow_name }}</span>
             <span class="text-sm text-gray mt-1">Execution ID: {{ task.id.substring(0, 8) }}</span>
           </div>
           <StatusBadge status="warning" label="Pending Approval" />
        </div>
        
        <div class="task-body mt-6">
          <div class="data-preview glass p-3 rounded-lg mb-4">
            <div class="text-xs text-bold uppercase letter-spacing-1 text-muted mb-2">Request Data</div>
            <div v-for="(val, key) in task.data" :key="key" class="flex justify-between text-sm py-1">
              <span class="text-gray">{{ key }}:</span>
              <span class="text-bold">{{ val }}</span>
            </div>
          </div>
          <div class="stat-mini">
            <span class="label">Triggered By</span>
            <span class="val">{{ task.triggered_by_email }}</span>
          </div>
          <div class="stat-mini">
            <span class="label">Date</span>
            <span class="val">{{ formatDate(task.started_at) }}</span>
          </div>
        </div>

        <div class="task-footer mt-8 pt-4 flex items-center justify-between gap-3">
           <button class="btn btn-outlined flex-1 text-red" @click="openActionModal(task, 'reject')">Reject</button>
           <button class="btn btn-primary flex-1 indigo-gradient" @click="openActionModal(task, 'approve')">Approve</button>
        </div>
      </div>
    </div>

    <!-- Action Modal -->
    <div v-if="actionModal.show" class="modal-backdrop" @click="closeActionModal">
      <div class="modal" @click.stop>
        <h2 class="text-bold mb-2 mt-0">{{ actionModal.type === 'approve' ? 'Approve' : 'Reject' }} Request</h2>
        <p class="text-gray text-sm mb-6">Execution for {{ actionModal.task?.workflow_name }}</p>
        
        <div class="mb-6">
          <label class="text-sm text-bold mb-2 flex">Comments</label>
          <textarea v-model="actionModal.comment" class="form-textarea glass" placeholder="Enter reason or feedback..."></textarea>
        </div>

        <div class="flex justify-between mt-6">
           <button type="button" class="btn btn-ghost" @click="closeActionModal">Cancel</button>
           <button class="btn" :class="actionModal.type === 'approve' ? 'btn-primary indigo-gradient' : 'btn-danger'" @click="submitAction" :disabled="submitting">
             <span v-if="submitting" class="spinner">🌀</span>
             <span v-else>{{ actionModal.type === 'approve' ? 'Confirm Approval' : 'Confirm Rejection' }}</span>
           </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, reactive } from 'vue'
import { useRouter } from 'vue-router'
import executionService from '@/services/execution.service'
import { useNotificationStore } from '@/stores/notification'
import StatusBadge from '@/components/common/StatusBadge.vue'

const router = useRouter()
const ns = useNotificationStore()
const tasks = ref([])
const loading = ref(true)
const submitting = ref(false)

const actionModal = reactive({
  show: false,
  task: null,
  type: 'approve',
  comment: ''
})

let refreshInterval = null

const fetchTasks = async () => {
  loading.value = true
  try {
    const res = await executionService.getPendingTasks()
    tasks.value = res.data
  } catch (error) {
    ns.error('Failed to fetch tasks')
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  fetchTasks()
  refreshInterval = setInterval(fetchTasks, 30000)
})

onUnmounted(() => {
  clearInterval(refreshInterval)
})

const formatDate = (dateStr) => {
  if (!dateStr) return ''
  const d = new Date(dateStr)
  return d.toLocaleDateString() + ' ' + d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
}

const openActionModal = (task, type) => {
  actionModal.task = task
  actionModal.type = type
  actionModal.comment = type === 'approve' ? 'Approved' : 'Rejected'
  actionModal.show = true
}

const closeActionModal = () => {
  actionModal.show = false
  actionModal.task = null
}

const submitAction = async () => {
  submitting.value = true
  try {
    if (actionModal.type === 'approve') {
      await executionService.approve(actionModal.task.id, { comment: actionModal.comment })
      ns.success('Task approved successfully')
    } else {
      await executionService.reject(actionModal.task.id, { comment: actionModal.comment })
      ns.success('Task rejected successfully')
    }
    closeActionModal()
    fetchTasks()
  } catch (error) {
    ns.error('Failed to process task')
  } finally {
    submitting.value = false
  }
}
</script>

<style scoped>
.grid-card {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(340px, 1fr));
  gap: 24px;
}
.task-card {
  display: flex; flex-direction: column;
  background: white; border-radius: 20px; padding: 24px;
  border: 1px solid var(--border-color);
}
.task-title { font-size: 18px; color: var(--text-primary); }
.data-preview { background: rgba(0,0,0,0.02); }
.stat-mini {
  display: flex; justify-content: space-between; align-items: center;
  padding: 10px 0; border-bottom: 1px dashed var(--border-color);
}
.stat-mini:last-child { border-bottom: none; }
.stat-mini .label { font-size: 13px; color: var(--text-muted); }
.stat-mini .val { font-size: 13px; font-weight: 700; }
</style>
