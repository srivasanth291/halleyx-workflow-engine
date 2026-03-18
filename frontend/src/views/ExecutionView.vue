<template>
  <div class="execution-page">
    <div class="flex items-center mb-8 gap-4">
      <router-link to="/workflows" class="btn-back glass shadow-hover">←</router-link>
      <div>
        <h1 class="text-bold m-0" style="font-size: 24px;">Execution Details</h1>
        <p class="text-gray m-0 text-sm mt-1">ID: <span class="code-font">{{ executionId }}</span></p>
      </div>
      <div class="flex-1"></div>
      <StatusBadge :status="execStore.currentExecution?.status" />
    </div>

    <div v-if="loading.main" class="text-center p-12"><span class="spinner">🌀</span> Loading...</div>
    
    <div v-else-if="execution" class="grid-layout">
       <!-- LEFT COLUMN -->
       <div class="flex flex-col gap-6">
         <!-- Status Card -->
         <div class="card glass">
           <h2 class="text-bold text-sm mb-6 uppercase letter-spacing-1">Status Overview</h2>
           <div class="info-row">
             <span class="label">Workflow</span>
             <span class="value">{{ execution.workflow_name }} <span class="v-tag">v{{ execution.workflow_version }}</span></span>
           </div>
           <div class="info-row">
             <span class="label">Started By</span>
             <span class="value">{{ execution.triggered_by_email }}</span>
           </div>
           <div class="info-row">
             <span class="label">Initiated</span>
             <span class="value">{{ formatDate(execution.started_at) }}</span>
           </div>
           
           <div class="flex flex-col gap-3 mt-8" v-if="['pending', 'in_progress', 'failed'].includes(execution.status)">
             <button class="btn btn-danger w-full" v-if="['pending', 'in_progress'].includes(execution.status)" @click="cancelExec">Cancel Execution</button>
             <button class="btn btn-primary w-full" v-if="execution.status === 'failed'" @click="retryExec">Retry Workflow</button>
           </div>
         </div>

         <!-- Progress Tracking -->
         <div class="card glass">
            <h2 class="text-bold text-sm mb-6 uppercase letter-spacing-1">Step Progress</h2>
            <StepProgress 
              :steps="workflowSteps" 
              :currentStepId="execution.current_step_id" 
              :logs="execution.logs"
              :status="execution.status"
            />
         </div>

         <!-- Workflow Map -->
         <WorkflowChart 
           :steps="workflowSteps" 
           :currentStepId="execution.current_step_id" 
         />

         <!-- Input Data -->
         <div class="card glass">
           <h2 class="text-bold text-sm mb-4 uppercase letter-spacing-1">Input Data</h2>
           <div class="code-block glass">
             <pre>{{ formatJSON(execution.data) }}</pre>
           </div>
         </div>
       </div>

       <!-- RIGHT COLUMN -->
       <div class="flex flex-col gap-6" style="grid-column: span 2;">
         <!-- Current Action (If Pending Approval) -->
         <div v-if="pendingStepInfo" class="card glass action-required">
           <div class="flex items-center justify-between mb-6">
               <div>
                  <h2 class="text-bold m-0" style="font-size: 18px;">Action Required</h2>
                  <p class="text-sm mt-1 m-0 text-indigo">Pending approval for: <span class="text-bold">{{ pendingStepInfo.step_name }}</span></p>
               </div>
               <div class="action-avatar indigo-gradient">!</div>
           </div>
           <div class="flex flex-col gap-2 mb-6">
             <label class="text-sm text-bold mb-1">Response Comments</label>
             <textarea v-model="approvalComment" class="form-textarea glass" rows="3" placeholder="Add relevant details for your decision..."></textarea>
           </div>
           <div class="flex justify-end gap-3">
             <button class="btn btn-danger" @click="handleAction('reject')" :disabled="loading.action">Reject</button>
             <button class="btn btn-outlined" @click="handleAction('return_step')" :disabled="loading.action">Return to Previous</button>
             <button class="btn btn-primary" @click="handleAction('approve')" :disabled="loading.action">Approve & Continue</button>
           </div>
         </div>

         <!-- Execution Logs -->
         <div class="card glass flex-1">
           <h2 class="text-bold text-sm mb-6 uppercase letter-spacing-1">Execution Path</h2>
           <LogTimeline :logs="execution.logs" />
         </div>
       </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRoute } from 'vue-router'
import { useExecutionStore } from '@/stores/execution'
import { useWorkflowStore } from '@/stores/workflow'
import StatusBadge from '@/components/common/StatusBadge.vue'
import LogTimeline from '@/components/execution/LogTimeline.vue'
import StepProgress from '@/components/execution/StepProgress.vue'
import WorkflowChart from '@/components/workflow/WorkflowChart.vue'

const route = useRoute()
const execStore = useExecutionStore()
const wfStore = useWorkflowStore()

const executionId = computed(() => route.params.id)
const execution = computed(() => execStore.currentExecution)
const workflowSteps = ref([])

const loading = ref({ main: false, action: false })
const approvalComment = ref('')

let pollInterval = null

onMounted(async () => {
    loading.value.main = true
    try {
       const res = await execStore.fetchExecution(executionId.value)
       if (res && res.workflow) {
          const wf = await wfStore.fetchWorkflow(res.workflow)
          workflowSteps.value = wf.steps || []
       }
    } finally {
       loading.value.main = false
    }
    // Poll every 10s while execution is active
    pollInterval = setInterval(async () => {
      const current = execStore.currentExecution
      if (current && ['pending', 'in_progress'].includes(current.status)) {
        execStore.fetchExecution(executionId.value)
      } else {
        clearInterval(pollInterval)
      }
    }, 10000)
})

onUnmounted(() => clearInterval(pollInterval))

const pendingStepInfo = computed(() => {
    if (!execution.value) return null
    if (execution.value.status !== 'in_progress') return null
    
    const logs = execution.value.logs || []
    if (logs.length === 0) return null
    
    // Reverse find the last log entry
    for (let i = logs.length - 1; i >= 0; i--) {
        if (logs[i].status === 'pending_approval') {
            return logs[i]
        }
        if (['approve', 'reject', 'return'].includes(logs[i].status)) {
            // Already resolved
            return null;
        }
    }
    return null
})

const formatDate = (dateStr) => {
  if (!dateStr) return ''
  const d = new Date(dateStr)
  return d.toLocaleDateString() + ' ' + d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })
}

const formatJSON = (obj) => {
  return JSON.stringify(obj, null, 2)
}

const getLogMarkerClass = (status) => {
  const s = (status || '').toLowerCase()
  if (s === 'completed' || s === 'approve') return 'marker-green'
  if (s === 'failed' || s === 'reject' || s === 'error') return 'marker-red'
  if (s === 'pending_approval' || s === 'return' || s === 'started' || s === 'pending') return 'marker-amber'
  return 'marker-gray'
}

const handleAction = async (actionStr) => {
    loading.value.action = true
    try {
        if (actionStr === 'approve') {
            await execStore.approveStep(executionId.value, approvalComment.value || 'Approved')
        } else if (actionStr === 'reject') {
            await execStore.rejectStep(executionId.value, approvalComment.value || 'Rejected')
        } else if (actionStr === 'return_step') {
            await execStore.returnStep(executionId.value, approvalComment.value || 'Returned')
        }
        approvalComment.value = ''
    } finally {
        loading.value.action = false
    }
}

const cancelExec = async () => {
    if(confirm('Cancel execution?')) {
        await execStore.cancelExecution(executionId.value)
    }
}

const retryExec = async () => {
    if(confirm('Retry execution?')) {
        await execStore.retryExecution(executionId.value)
    }
}
</script>

<style scoped>
.grid-layout {
  display: grid;
  grid-template-columns: 1fr 2fr;
  gap: 24px;
}
.btn-back {
  width: 40px; height: 40px; border-radius: 12px;
  display: flex; align-items: center; justify-content: center;
  text-decoration: none; font-size: 18px; color: var(--text-primary);
  border: 1px solid var(--border-color);
}
.info-row {
  display: flex; justify-content: space-between; align-items: center;
  padding: 12px 0; border-bottom: 1px dashed var(--border-color);
}
.info-row:last-of-type { border-bottom: none; }
.info-row .label { font-size: 13px; color: var(--text-muted); }
.info-row .value { font-size: 14px; font-weight: 600; }
.v-tag {
  font-size: 10px; background: var(--accent-indigo-light);
  color: var(--accent-indigo); padding: 2px 6px; border-radius: 4px;
  vertical-align: middle; margin-left: 4px;
}

.code-block {
  background: #0f172a; color: #cbd5e1;
  padding: 16px; border-radius: 12px;
  font-family: monospace; font-size: 12px;
  overflow-x: auto; margin-top: 8px;
}
.code-block pre { margin: 0; }

.action-required {
  border: 1px solid var(--accent-indigo);
  background: linear-gradient(to bottom right, #ffffff, #f5f3ff);
}
.action-avatar {
  width: 48px; height: 48px; border-radius: 14px;
  display: flex; align-items: center; justify-content: center;
  color: white; font-weight: 800; font-size: 24px;
}

.letter-spacing-1 { letter-spacing: 1px; }
.uppercase { text-transform: uppercase; }
</style>
