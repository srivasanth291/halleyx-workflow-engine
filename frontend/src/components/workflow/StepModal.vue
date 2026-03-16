<template>
  <div class="modal-backdrop" @click.self="$emit('cancel')">
    <div class="modal modal-lg">
      <div class="modal-header">
        <h3>{{ step ? 'Edit Step' : 'Add Step' }}</h3>
        <button class="btn-icon" @click="$emit('cancel')">✕</button>
      </div>
      <div class="modal-body">

        <div class="form-group">
          <label class="form-label">Step Name <span class="req">*</span></label>
          <input v-model="form.name" class="form-input" placeholder="e.g. Manager Approval" />
        </div>

        <div class="form-group">
          <label class="form-label">Step Type</label>
          <div class="step-type-grid">
            <div
              v-for="t in types"
              :key="t.value"
              :class="['step-type-card', form.step_type === t.value ? `selected-${t.value}` : '']"
              @click="form.step_type = t.value"
            >
              <div class="step-type-icon">{{ t.icon }}</div>
              <div class="step-type-name">{{ t.name }}</div>
              <div class="step-type-desc">{{ t.desc }}</div>
            </div>
          </div>
        </div>

        <div class="form-group">
          <label class="form-label">Step Order</label>
          <input v-model.number="form.order" type="number" class="form-input" style="width:100px" min="1" />
        </div>

        <div class="divider"></div>
        <p style="font-weight:600;font-size:13px;color:var(--text-secondary);margin-bottom:14px">STEP METADATA</p>

        <!-- APPROVAL METADATA -->
        <template v-if="form.step_type === 'approval'">
          <div class="form-group">
            <label class="form-label">Assignee Email <span class="req">*</span></label>
            <input v-model="meta.assignee_email" type="email" class="form-input" placeholder="manager@company.com" />
          </div>
          <div class="form-group">
            <label class="form-label">Instructions</label>
            <textarea v-model="meta.instructions" class="form-input form-textarea" placeholder="Review carefully before approving"></textarea>
          </div>
          <div class="flex gap-4">
            <div class="form-group flex-1">
              <label class="form-label">Timeout Hours</label>
              <input v-model.number="meta.timeout_hours" type="number" class="form-input" min="1" />
            </div>
            <div class="form-group flex-1">
              <label class="form-label">On Timeout</label>
              <select v-model="meta.on_timeout" class="form-input form-select">
                <option value="escalate">Escalate</option>
                <option value="auto_approve">Auto Approve</option>
                <option value="auto_reject">Auto Reject</option>
              </select>
            </div>
          </div>
          <div v-if="meta.on_timeout === 'escalate'" class="form-group">
            <label class="form-label">Escalate To</label>
            <input v-model="meta.escalate_to" type="email" class="form-input" placeholder="director@company.com" />
          </div>
        </template>

        <!-- NOTIFICATION METADATA -->
        <template v-if="form.step_type === 'notification'">
          <div class="form-group">
            <label class="form-label">Channel</label>
            <select v-model="meta.notification_channel" class="form-input form-select">
              <option value="email">Email</option>
              <option value="slack">Slack</option>
              <option value="ui_message">UI Message</option>
            </select>
          </div>
          <div class="form-group">
            <label class="form-label">Message Template</label>
            <textarea v-model="meta.template" class="form-input form-textarea" placeholder="Expense {amount} from {country} has been approved!"></textarea>
            <span class="form-hint">Use {field_name} for dynamic values from input schema</span>
          </div>
          <div class="form-group">
            <label class="form-label">Recipients</label>
            <input v-model="meta.recipients_str" class="form-input" placeholder="hr@company.com, finance@company.com" />
            <span class="form-hint">Comma separated email addresses</span>
          </div>
        </template>

        <!-- TASK METADATA -->
        <template v-if="form.step_type === 'task'">
          <div class="form-group">
            <label class="form-label">Instructions</label>
            <textarea v-model="meta.instructions" class="form-input form-textarea" placeholder="Describe what this task should do"></textarea>
          </div>
        </template>

        <p v-if="error" class="form-error-msg">{{ error }}</p>
      </div>
      <div class="modal-footer">
        <button class="btn btn-ghost flex-1" @click="$emit('cancel')">Cancel</button>
        <button class="btn btn-primary flex-1" :disabled="saving" @click="save">
          <span v-if="saving" class="spinner"></span>
          {{ saving ? 'Saving...' : 'Save Step' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref, onMounted } from 'vue'
import stepService from '@/services/step.service'
import { useNotificationStore } from '@/stores/notification'

const props = defineProps({ workflowId: String, step: Object })
const emit = defineEmits(['saved', 'cancel'])
const notif = useNotificationStore()

const types = [
  { value: 'approval',     name: 'Approval',     icon: '👍', desc: 'Requires user approval'     },
  { value: 'notification', name: 'Notification', icon: '🔔', desc: 'Sends alerts or messages'   },
  { value: 'task',         name: 'Task',         icon: '🔧', desc: 'Automated action'            },
]

const form = reactive({ name: '', step_type: 'approval', order: 1 })
const meta = reactive({
  assignee_email: '', instructions: '',
  timeout_hours: 24, on_timeout: 'escalate', escalate_to: '',
  notification_channel: 'email', template: '', recipients_str: '',
})
const error = ref('')
const saving = ref(false)

onMounted(() => {
  if (props.step) {
    form.name = props.step.name
    form.step_type = props.step.step_type
    form.order = props.step.order
    const m = props.step.metadata || {}
    meta.assignee_email       = m.assignee_email || ''
    meta.instructions         = m.instructions || ''
    meta.timeout_hours        = m.timeout_hours || 24
    meta.on_timeout           = m.on_timeout || 'escalate'
    meta.escalate_to          = m.escalate_to || ''
    meta.notification_channel = m.notification_channel || 'email'
    meta.template             = m.template || ''
    meta.recipients_str       = (m.recipients || []).join(', ')
  }
})

async function save() {
  error.value = ''
  if (!form.name.trim()) { error.value = 'Step name is required'; return }
  if (form.step_type === 'approval' && !meta.assignee_email) { error.value = 'Assignee email is required'; return }
  if (form.step_type === 'notification' && !meta.notification_channel) { error.value = 'Notification channel is required'; return }

  let metadata = {}
  if (form.step_type === 'approval') {
    metadata = {
      assignee_email: meta.assignee_email,
      instructions:  meta.instructions,
      timeout_hours:  meta.timeout_hours,
      on_timeout:     meta.on_timeout,
      escalate_to:    meta.escalate_to,
    }
  } else if (form.step_type === 'notification') {
    metadata = {
      notification_channel: meta.notification_channel,
      template:   meta.template,
      recipients: meta.recipients_str.split(',').map(r => r.trim()).filter(Boolean),
    }
  } else {
    metadata = { instructions: meta.instructions }
  }

  const payload = { name: form.name, step_type: form.step_type, order: form.order, metadata }
  saving.value = true
  try {
    if (props.step) {
      await stepService.update(props.step.id, payload)
      notif.success('Step updated!')
    } else {
      await stepService.create(props.workflowId, payload)
      notif.success('Step added!')
    }
    emit('saved')
  } catch (e) {
    error.value = e.response?.data?.detail || JSON.stringify(e.response?.data) || 'Save failed'
  } finally {
    saving.value = false
  }
}
</script>
