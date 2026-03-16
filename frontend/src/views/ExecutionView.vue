<template>
  <div style="max-width:860px;margin:0 auto">

    <!-- Workflow info banner -->
    <div
      v-if="workflow"
      class="card"
      style="background:var(--accent-green-light);border:1px solid var(--accent-green-border);padding:16px 20px;margin-bottom:20px;display:flex;justify-content:space-between;align-items:center"
    >
      <div class="flex items-center gap-3">
        <span style="font-size:18px;font-weight:700">{{ workflow.name }}</span>
        <span class="badge badge-indigo">v{{ workflow.version }}</span>
        <span class="text-sm text-secondary">{{ workflow.steps?.length || 0 }} Steps</span>
      </div>
      <div class="flex items-center gap-2">
        <StatusBadge v-if="execution" :status="execution.status" />
        <button
          v-if="execution?.status === 'in_progress'"
          class="btn btn-ghost btn-sm"
          style="color:#DC2626;border-color:#DC2626"
          @click="handleCancel"
        >✕ Cancel</button>
      </div>
    </div>

    <!-- INPUT FORM (shown when no execution or after failed) -->
    <div v-if="!execution || execution.status === 'failed'" class="card card-body" style="margin-bottom:20px">
      <h3 style="font-size:16px;font-weight:700;margin-bottom:4px">Input Data</h3>
      <p class="text-sm text-secondary" style="margin-bottom:20px">Fill required fields to execute workflow</p>

      <div v-if="workflow?.input_schema?.fields?.length" style="display:grid;grid-template-columns:1fr 1fr;gap:16px">
        <div v-for="field in workflow.input_schema.fields" :key="field.name" class="form-group">
          <label class="form-label">
            {{ field.name }} <span v-if="field.required" class="req">*</span>
          </label>
          <template v-if="field.type === 'boolean'">
            <div class="toggle-row">
              <button type="button" class="toggle" :class="{on: inputData[field.name]}" @click="inputData[field.name] = !inputData[field.name]"></button>
              <span>{{ inputData[field.name] ? 'True' : 'False' }}</span>
            </div>
          </template>
          <template v-else-if="field.allowed_values?.length">
            <select v-model="inputData[field.name]" class="form-input form-select">
              <option value="">-- Select --</option>
              <option v-for="v in field.allowed_values" :key="v" :value="v">{{ v }}</option>
            </select>
          </template>
          <template v-else-if="field.type === 'number'">
            <input v-model.number="inputData[field.name]" type="number" class="form-input" :placeholder="field.name" />
          </template>
          <template v-else>
            <input v-model="inputData[field.name]" type="text" class="form-input" :placeholder="field.name" />
          </template>
        </div>
      </div>
      <div v-else class="alert alert-warning" style="margin-top:16px">
        No input fields defined in workflow schema.
      </div>

      <div class="form-group" style="margin-top:16px;max-width:200px">
        <label class="form-label">Max Iterations</label>
        <input v-model.number="maxIter" type="number" class="form-input" min="1" max="100" />
        <span class="form-hint">Loop prevention limit (default: 10)</span>
      </div>

      <div v-if="execError" class="alert alert-error" style="margin-top:16px">{{ execError }}</div>

      <button
        class="btn btn-primary btn-full btn-lg"
        style="margin-top:20px"
        :disabled="executing"
        @click="handleExecute"
      >
        <span v-if="executing" class="spinner"></span>
        {{ executing ? 'Starting...' : '▶ Execute Workflow' }}
      </button>
    </div>

    <!-- PROGRESS -->
    <div v-if="execution" class="card card-body" style="margin-bottom:20px">
      <div class="flex items-center justify-between" style="margin-bottom:20px">
        <h3 style="font-size:16px;font-weight:700">Execution Progress</h3>
        <span class="mono text-sm text-muted">{{ execution.id?.slice(0, 12) }}...</span>
      </div>

      <StepProgress
        :steps="workflow?.steps || []"
        :logs="execution.logs || []"
        :current-step-id="execution.current_step_id"
      />

      <!-- Approval action panel -->
      <div
        v-if="currentStep && currentStep.step_type === 'approval' && execution.status === 'in_progress'"
        class="action-card approval"
        style="margin-top:16px"
      >
        <div class="flex items-center justify-between">
          <div>
            <p style="font-weight:700;color:#1D4ED8;font-size:15px">{{ currentStep.name }}</p>
            <p class="text-sm" style="color:#3B82F6;margin-top:3px">
              Waiting for: {{ currentStep.metadata?.assignee_email }}
            </p>
          </div>
          <span class="text-sm text-secondary">⏱ In progress...</span>
        </div>
        <div class="flex gap-3" style="margin-top:14px">
          <button class="btn btn-primary btn-sm" @click="openAction('approve')">✅ Approve</button>
          <button class="btn btn-danger btn-sm" @click="openAction('reject')">❌ Reject</button>
          <button class="btn btn-ghost btn-sm" @click="openAction('return')">↩ Return</button>
        </div>
      </div>

      <!-- Failed panel -->
      <div v-if="execution.status === 'failed'" class="action-card failed" style="margin-top:16px">
        <p style="font-weight:700;color:#DC2626;font-size:15px">❌ Execution Failed</p>
        <p class="text-sm text-secondary" style="margin-top:4px">{{ lastError }}</p>
        <div class="flex gap-3" style="margin-top:14px">
          <button class="btn btn-amber btn-sm" @click="handleRetry">🔄 Retry Failed Step</button>
        </div>
      </div>

      <!-- Completed banner -->
      <div v-if="execution.status === 'completed'" class="alert alert-success" style="margin-top:16px">
        ✅ Workflow completed successfully!
      </div>
    </div>

    <!-- LOGS -->
    <div v-if="execution" class="card card-body">
      <h3 style="font-size:16px;font-weight:700;margin-bottom:20px">Execution Logs</h3>
      <LogTimeline :logs="execution.logs" />
    </div>

    <!-- Action Comment Modal -->
    <div v-if="showActionModal" class="modal-backdrop" @click.self="showActionModal = false">
      <div class="modal modal-sm">
        <div class="modal-header">
          <h3>{{ actionLabel }}</h3>
          <button class="btn-icon" @click="showActionModal = false">✕</button>
        </div>
        <div class="modal-body">
          <div class="form-group">
            <label class="form-label">Comment (optional)</label>
            <textarea v-model="actionComment" class="form-input form-textarea" placeholder="Add a comment..."></textarea>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn btn-ghost flex-1" @click="showActionModal = false">Cancel</button>
          <button
            :class="['btn', 'flex-1', actionType === 'approve' ? 'btn-primary' : actionType === 'reject' ? 'btn-danger' : 'btn-ghost']"
            @click="confirmAction"
          >{{ actionLabel }}</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, onUnmounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import { useWorkflowStore } from '@/stores/workflow'
import { useExecutionStore } from '@/stores/execution'
import { useNotificationStore } from '@/stores/notification'
import StatusBadge from '@/components/common/StatusBadge.vue'
import StepProgress from '@/components/execution/StepProgress.vue'
import LogTimeline from '@/components/execution/LogTimeline.vue'

const route = useRoute()
const wfStore = useWorkflowStore()
const execStore = useExecutionStore()
const notif = useNotificationStore()

const workflowId = route.params.id
const workflow = computed(() => wfStore.currentWorkflow)
const execution = computed(() => execStore.currentExecution)

const inputData = reactive({})
const maxIter = ref(10)
const executing = ref(false)
const execError = ref('')
const showActionModal = ref(false)
const actionType = ref('')
const actionComment = ref('')

const actionLabel = computed(() => ({
  approve: 'Approve',
  reject:  'Reject',
  return:  'Return to Employee',
}[actionType.value] || ''))

const currentStep = computed(() => {
  if (!execution.value?.current_step_id || !workflow.value?.steps) return null
  return workflow.value.steps.find(s => s.id === execution.value.current_step_id) || null
})

const lastError = computed(() => {
  const logs = execution.value?.logs || []
  for (let i = logs.length - 1; i >= 0; i--) {
    if (logs[i].error) return logs[i].error
  }
  return 'An error occurred'
})

let pollTimer = null

watch(() => execution.value?.status, (s) => {
  if (s === 'in_progress') startPoll()
  else stopPoll()
})

function startPoll() {
  if (pollTimer) return
  pollTimer = setInterval(async () => {
    if (execution.value?.id) await execStore.fetchExecution(execution.value.id)
  }, 3000)
}

function stopPoll() {
  if (pollTimer) { clearInterval(pollTimer); pollTimer = null }
}

onUnmounted(stopPoll)

async function handleExecute() {
  execError.value = ''
  for (const f of workflow.value?.input_schema?.fields || []) {
    if (f.required && (inputData[f.name] === undefined || inputData[f.name] === '' || inputData[f.name] === null)) {
      execError.value = `"${f.name}" is required`; return
    }
  }
  executing.value = true
  try {
    await execStore.executeWorkflow(workflowId, { ...inputData }, maxIter.value)
    notif.success('Execution started!')
    startPoll()
  } catch (e) {
    const d = e.response?.data
    execError.value = d?.detail || JSON.stringify(d) || 'Execution failed'
  } finally {
    executing.value = false
  }
}

function openAction(type) {
  actionType.value = type
  actionComment.value = ''
  showActionModal.value = true
}

async function confirmAction() {
  try {
    if (actionType.value === 'approve')      await execStore.approveStep(execution.value.id, actionComment.value)
    else if (actionType.value === 'reject')  await execStore.rejectStep(execution.value.id, actionComment.value)
    else                                     await execStore.returnStep(execution.value.id, actionComment.value)
    notif.success('Action recorded!')
    showActionModal.value = false
  } catch (e) {
    notif.error(e.response?.data?.detail || 'Action failed')
  }
}

async function handleCancel() {
  try {
    await execStore.cancelExecution(execution.value.id)
    notif.success('Execution canceled!')
    stopPoll()
  } catch (e) {
    notif.error(e.response?.data?.detail || 'Cancel failed')
  }
}

async function handleRetry() {
  try {
    await execStore.retryExecution(execution.value.id)
    notif.success('Retrying...')
    startPoll()
  } catch (e) {
    notif.error(e.response?.data?.detail || 'Retry failed')
  }
}

onMounted(() => {
  execStore.currentExecution = null
  wfStore.fetchWorkflow(workflowId)
})
</script>
