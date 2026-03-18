<template>
  <div class="wf-editor-page">
    <div class="flex items-center justify-between mb-6">
      <div class="flex items-center gap-4">
        <router-link to="/workflows" class="btn btn-ghost" style="padding: 6px;">←</router-link>
        <div>
          <h1 class="text-bold m-0" style="font-size: 20px;">{{ isEditing ? 'Edit Workflow' : 'Create Workflow' }}</h1>
          <p class="text-gray m-0 text-sm mt-1" v-if="isEditing">Version {{ form.version }}</p>
        </div>
      </div>
      <div class="flex items-center gap-3">
        <button class="btn btn-ghost" @click="showVersionsModal = true" v-if="isEditing">Versions</button>
        <button class="btn btn-danger" @click="confirmDelete = true" v-if="isEditing">Disable</button>
        <button class="btn btn-primary" @click="saveWorkflow" :disabled="loading.save">
          <span v-if="loading.save" class="spinner">🌀</span>
          <span v-else>Save Workflow</span>
        </button>
      </div>
    </div>

    <div class="card glass mb-8 shadow-hover">
      <h2 class="text-bold mb-6" style="font-size: 18px;">Basic Information</h2>
      <div class="mb-6">
        <label class="text-sm text-bold mb-2 flex">Workflow Name</label>
        <input type="text" v-model="form.name" class="form-input glass" placeholder="e.g. Employee Onboarding" />
      </div>

      <div class="border-t pt-8">
        <h3 class="text-bold mb-2" style="font-size: 16px;">Input Schema</h3>
        <p class="text-sm text-gray mb-6">Define the data fields required to start this workflow. These will be validated on execution.</p>
        
        <div class="schema-fields flex flex-col gap-4">
          <div v-for="(field, index) in form.input_schema.fields" :key="index" class="schema-field-row glass shadow-hover p-4 rounded-xl">
            <div class="flex items-start gap-4">
              <div class="flex-1 grid grid-cols-2 gap-4">
                 <div>
                   <label class="text-xs text-bold mb-1 flex uppercase letter-spacing-1">Field Name</label>
                   <input type="text" v-model="field.name" class="form-input text-sm" placeholder="amount" />
                 </div>
                 <div>
                   <label class="text-xs text-bold mb-1 flex uppercase letter-spacing-1">Type</label>
                   <select v-model="field.type" class="form-select text-sm">
                     <option value="string">String</option>
                     <option value="number">Number</option>
                     <option value="boolean">Boolean</option>
                   </select>
                 </div>
                 <div class="col-span-2" v-if="field.type === 'string'">
                   <label class="text-xs text-bold mb-1 flex uppercase letter-spacing-1">Allowed Values (Comma separated)</label>
                   <input type="text" v-model="field.allowed_values_str" @change="updateAllowedValues(field)" class="form-input text-sm" placeholder="US, UK, IN" />
                 </div>
                 <div class="col-span-2 flex items-center gap-3 mt-2">
                   <div class="toggle-switch">
                      <input type="checkbox" v-model="field.required" :id="'req-'+index" />
                      <label :for="'req-'+index"></label>
                   </div>
                   <label :for="'req-'+index" class="text-sm font-semibold">Required for initiation</label>
                 </div>
              </div>
              <button class="btn-icon text-red mt-1" @click="removeField(index)" title="Remove Field">🗑</button>
            </div>
          </div>
        </div>
        
        <button class="btn btn-outlined mt-6" @click="addField">+ Add New Field</button>
      </div>
    </div>

    <!-- Steps Listing -->
    <div v-if="isEditing" class="card glass shadow-hover">
      <div class="flex items-center justify-between mb-8">
        <h2 class="text-bold m-0" style="font-size: 18px;">Workflow Steps</h2>
        <button class="btn btn-primary" @click="openStepModal()">+ Add New Step</button>
      </div>

      <div class="steps-list flex flex-col gap-4">
        <div v-for="step in sortedSteps" :key="step.id" class="step-item glass p-5 flex items-center justify-between shadow-sm">
          <div class="flex items-center gap-6">
            <div class="step-order indigo-gradient">{{ step.order }}</div>
            <div>
              <div class="text-bold mb-1" style="font-size: 16px;">{{ step.name }}</div>
              <div class="flex items-center gap-2">
                <span class="badge" :class="getStepBadgeClass(step.step_type)">{{ step.step_type }}</span>
                <span class="text-xs text-muted">{{ step.rules ? step.rules.length : 0 }} branching rules</span>
              </div>
            </div>
          </div>
          <div class="flex items-center gap-2">
            <button class="btn btn-outlined text-sm px-4" @click="openStepModal(step)">Settings</button>
            <router-link :to="`/workflows/${form.id}/steps/${step.id}/rules`" class="btn btn-outlined text-sm px-4">Logic Rules</router-link>
            <button class="btn btn-outlined text-sm text-red px-4" @click="deleteStep(step.id)">Delete</button>
          </div>
        </div>
        <div v-if="steps.length === 0" class="text-center p-12 text-gray italic">No steps defined. Add a step to begin the workflow process.</div>
      </div>
      
      <div v-if="steps.length > 0" class="mt-8 pt-8 border-t">
         <label class="text-sm text-bold mb-3 flex uppercase letter-spacing-1">Entry Point Step</label>
         <div class="flex items-center gap-4">
           <select v-model="form.start_step_id" class="form-select max-w-sm glass">
             <option :value="null">Select a start step</option>
             <option v-for="st in sortedSteps" :key="st.id" :value="st.id">{{ st.order }}: {{ st.name }}</option>
           </select>
           <button class="btn btn-primary px-6" @click="updateStartStep" :disabled="loading.startStep">Set Initial Step</button>
         </div>
      </div>
    </div>

    <!-- Step Edit/Create Modal -->
    <div v-if="stepModal.show" class="modal-backdrop" @click="closeStepModal">
      <div class="modal modal-lg" @click.stop>
        <h2 class="text-bold mb-6 mt-0">{{ stepModal.isEdit ? 'Edit Step' : 'Add Step' }}</h2>
        <form @submit.prevent="saveStep">
          <div class="grid-2 mb-4">
            <div>
              <label class="text-sm text-bold mb-2">Step Name</label>
              <input type="text" v-model="stepForm.name" class="form-input" required />
            </div>
            <div>
              <label class="text-sm text-bold mb-2">Step Type</label>
              <select v-model="stepForm.step_type" class="form-select" required>
                <option value="task">Task (Action)</option>
                <option value="approval">Approval</option>
                <option value="notification">Notification</option>
              </select>
            </div>
          </div>
          <div class="mb-6">
            <label class="text-sm text-bold mb-2">Order</label>
            <input type="number" v-model.number="stepForm.order" class="form-input" required />
          </div>

          <h3 class="text-bold mb-4" style="font-size: 14px;">Metadata Configuration</h3>
          
          <div v-if="stepForm.step_type === 'approval'" class="grid-2 gap-4 mb-6">
             <div>
               <label class="text-sm text-bold mb-2">Assignee Email</label>
               <input type="email" v-model="stepForm.metadata.assignee_email" class="form-input" required />
             </div>
             <div>
               <label class="text-sm text-bold mb-2">Timeout (Hours)</label>
               <input type="number" v-model.number="stepForm.metadata.timeout_hours" class="form-input" />
             </div>
             <div>
               <label class="text-sm text-bold mb-2">On Timeout Action</label>
               <select v-model="stepForm.metadata.on_timeout" class="form-select">
                 <option value="escalate">Escalate</option>
                 <option value="auto_approve">Auto Approve</option>
                 <option value="auto_reject">Auto Reject</option>
               </select>
             </div>
             <div v-if="stepForm.metadata.on_timeout === 'escalate'">
               <label class="text-sm text-bold mb-2">Escalate To (Email)</label>
               <input type="email" v-model="stepForm.metadata.escalate_to" class="form-input" />
             </div>
          </div>

          <div v-if="stepForm.step_type === 'notification'" class="grid-2 gap-4 mb-6">
             <div>
               <label class="text-sm text-bold mb-2">Channel</label>
               <select v-model="stepForm.metadata.channel" class="form-select">
                 <option value="email">Email</option>
                 <option value="slack">Slack</option>
                 <option value="ui_message">App Message</option>
               </select>
             </div>
             <div>
               <label class="text-sm text-bold mb-2">Subject</label>
               <input type="text" v-model="stepForm.metadata.subject" class="form-input" v-if="stepForm.metadata.channel === 'email'" />
             </div>
             <div style="grid-column: span 2;">
               <label class="text-sm text-bold mb-2">Template</label>
               <textarea v-model="stepForm.metadata.template" class="form-textarea" rows="3" placeholder="Use {field_name} for variables"></textarea>
             </div>
             <div style="grid-column: span 2;">
               <label class="text-sm text-bold mb-2">Recipients (Comma separated emails)</label>
               <input type="text" v-model="stepForm.metadata.recipients_str" @change="updateRecipients" class="form-input" />
             </div>
          </div>

          <div v-if="stepForm.step_type === 'task'" class="mb-6">
             <label class="text-sm text-bold mb-2">Task Instructions</label>
             <textarea v-model="stepForm.metadata.instructions" class="form-textarea" rows="3"></textarea>
          </div>

          <div class="flex justify-between">
            <button type="button" class="btn btn-ghost" @click="closeStepModal">Cancel</button>
            <button type="submit" class="btn btn-primary" :disabled="loading.step">Save Step</button>
          </div>
        </form>
      </div>
    </div>

    <!-- Versions Modal -->
    <div v-if="showVersionsModal" class="modal-backdrop" @click="showVersionsModal = false">
      <div class="modal" @click.stop>
        <div class="flex items-center justify-between mb-4">
          <h2 class="text-bold mt-0 m-0">Version History</h2>
          <button class="btn-icon" @click="showVersionsModal = false">✕</button>
        </div>
        <div v-if="loading.versions" class="p-4 text-center"><span class="spinner">🌀</span></div>
        <div v-else class="flex flex-col gap-3">
          <div v-for="v in versions" :key="v.id" class="p-3 border rounded-lg flex items-center justify-between" :style="{borderColor: v.version === form.version ? 'var(--accent-green)' : 'var(--border-color)'}">
             <div>
               <div class="text-bold">Version {{ v.version }}</div>
               <div class="text-sm text-gray">{{ new Date(v.created_at).toLocaleString() }}</div>
             </div>
             <div>
               <span v-if="v.version === form.version" class="badge badge-green">Current</span>
               <button v-else class="btn btn-outlined text-sm" @click="rollback(v.version)">Restore</button>
             </div>
          </div>
        </div>
      </div>
    </div>

    <ConfirmModal v-model="confirmDelete" title="Disable Workflow" message="Are you sure you want to disable this workflow? It will no longer be available for execution." confirmText="Disable" @confirm="disableWorkflow" :loading="loading.delete" />

  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useWorkflowStore } from '@/stores/workflow'
import { useAuthStore } from '@/stores/auth'
import { useNotificationStore } from '@/stores/notification'
import stepService from '@/services/step.service'
import ConfirmModal from '@/components/common/ConfirmModal.vue'

const router = useRouter()
const route = useRoute()
const store = useWorkflowStore()
const authStore = useAuthStore()
const ns = useNotificationStore()

const isAdmin = computed(() => authStore.isAdmin)

const isEditing = computed(() => !!route.params.id)
const workflowId = computed(() => route.params.id)

const loading = reactive({ save: false, step: false, versions: false, delete: false, startStep: false })
const showVersionsModal = ref(false)
const confirmDelete = ref(false)
const versions = ref([])

const form = reactive({
  id: null,
  name: '',
  version: 1,
  start_step_id: null,
  input_schema: { fields: [] }
})

const steps = ref([])

const sortedSteps = computed(() => {
  return [...steps.value].sort((a, b) => a.order - b.order)
})

const getStepBadgeClass = (type) => {
  if (type === 'approval') return 'badge-amber'
  if (type === 'notification') return 'badge-blue'
  return 'badge-indigo'
}

// Need to refetch when route changes
watch(() => route.params.id, async (newId) => {
  if (!isAdmin.value) {
    router.push('/workflows')
    return
  }
  if (newId) {
     await loadWorkflow()
  } else {
     resetForm()
  }
})

const resetForm = () => {
    form.id = null
    form.name = ''
    form.version = 1
    form.start_step_id = null
    form.input_schema = { fields: [] }
    steps.value = []
}

onMounted(async () => {
  if (!isAdmin.value) {
    router.push('/workflows')
    return
  }
  if (isEditing.value) {
    await loadWorkflow()
    loadVersions()
  }
})

const loadWorkflow = async () => {
  const wf = await store.fetchWorkflow(workflowId.value)
  form.id = wf.id
  form.name = wf.name
  form.version = wf.version
  form.start_step_id = wf.start_step_id
  
  if (wf.input_schema && wf.input_schema.fields && Array.isArray(wf.input_schema.fields)) {
    form.input_schema = JSON.parse(JSON.stringify(wf.input_schema))
    form.input_schema.fields.forEach(f => {
      if (f.allowed_values) f.allowed_values_str = f.allowed_values.join(', ')
    })
  } else {
    form.input_schema = { fields: [] }
  }

  // Load steps
  steps.value = wf.steps || []
}

const loadVersions = async () => {
  loading.versions = true
  try {
    versions.value = await store.fetchVersions(workflowId.value)
  } finally {
    loading.versions = false
  }
}

const addField = () => {
  form.input_schema.fields.push({
    name: '', type: 'string', required: false, allowed_values: [], allowed_values_str: ''
  })
}

const removeField = (idx) => {
  form.input_schema.fields.splice(idx, 1)
}

const updateAllowedValues = (field) => {
  if (field.allowed_values_str) {
    field.allowed_values = field.allowed_values_str.split(',').map(s => s.trim()).filter(Boolean)
  } else {
    field.allowed_values = []
  }
}

const saveWorkflow = async () => {
  if (!form.name.trim()) {
    ns.error('Workflow Name is required')
    return
  }
  loading.save = true
  try {
    const schemaToSave = {
      fields: form.input_schema.fields.map(f => {
        const { allowed_values_str, ...rest } = f
        if (rest.type !== 'string') rest.allowed_values = []
        return rest
      })
    }

    const payload = {
      name: form.name,
      input_schema: schemaToSave,
    }

    if (isEditing.value) {
      const saved = await store.updateWorkflow(workflowId.value, payload)
      // New version is created. 
      // Update route param ID!
      router.push(`/workflows/${saved.id}/edit`)
    } else {
      const saved = await store.createWorkflow(payload)
      router.push(`/workflows/${saved.id}/edit`)
    }
  } finally {
    loading.save = false
  }
}

const disableWorkflow = async () => {
  loading.delete = true
  try {
    await store.deleteWorkflow(workflowId.value)
    router.push('/workflows')
  } finally {
    loading.delete = false
    confirmDelete.value = false
  }
}

const rollback = async (v) => {
  loading.versions = true
  try {
    const saved = await store.rollback(workflowId.value, v)
    showVersionsModal.value = false
    router.push(`/workflows/${saved.id}/edit`)
  } finally {
    loading.versions = false
  }
}

const updateStartStep = async () => {
    loading.startStep = true
    try {
        await store.updateWorkflow(workflowId.value, { 
           start_step_id: form.start_step_id,
           input_schema: form.input_schema // must include again or it might be wiped if not partial
        })
        ns.success('Start step updated!')
    } finally {
        loading.startStep = false
    }
}

// STEP LOGIC
const stepModal = reactive({
  show: false,
  isEdit: false
})
const stepForm = reactive({
  id: null,
  name: '',
  step_type: 'task',
  order: 1,
  metadata: {}
})

const openStepModal = (st = null) => {
  if (st) {
    stepModal.isEdit = true
    stepForm.id = st.id
    stepForm.name = st.name
    stepForm.step_type = st.step_type
    stepForm.order = st.order
    stepForm.metadata = JSON.parse(JSON.stringify(st.metadata || {}))
    if (st.metadata?.recipients) {
      stepForm.metadata.recipients_str = st.metadata.recipients.join(', ')
    }
  } else {
    stepModal.isEdit = false
    stepForm.id = null
    stepForm.name = ''
    stepForm.step_type = 'task'
    stepForm.order = steps.value.length + 1
    stepForm.metadata = {}
  }
  stepModal.show = true
}

const closeStepModal = () => {
  stepModal.show = false
}

const updateRecipients = () => {
  if (stepForm.metadata.recipients_str) {
    stepForm.metadata.recipients = stepForm.metadata.recipients_str.split(',').map(s => s.trim()).filter(Boolean)
  } else {
    stepForm.metadata.recipients = []
  }
}

const saveStep = async () => {
  loading.step = true
  try {
    if (stepForm.step_type === 'notification') updateRecipients()

    const payload = {
      workflow: workflowId.value,
      name: stepForm.name,
      step_type: stepForm.step_type,
      order: stepForm.order,
      metadata: stepForm.metadata
    }

    if (stepModal.isEdit) {
      await stepService.update(stepForm.id, payload)
      ns.success('Step updated')
    } else {
      await stepService.create(payload)
      ns.success('Step created')
    }
    await loadWorkflow()
    closeStepModal()
  } finally {
    loading.step = false
  }
}

const deleteStep = async (id) => {
  if (confirm('Are you sure you want to delete this step? Rules associated will also be deleted.')) {
    await stepService.delete(id)
    ns.success('Step deleted')
    await loadWorkflow()
  }
}
</script>

<style scoped>
.schema-fields { width: 100%; }
.schema-field-row { border: 1px solid var(--border-color); }

/* Step List Premium */
.step-item {
  border-radius: 16px;
  background: white;
  border: 1px solid var(--border-color);
}
.step-order {
  width: 44px; height: 44px; border-radius: 12px;
  display: flex; align-items: center; justify-content: center;
  color: white; font-weight: 800; font-size: 18px;
}

/* Toggle Switch Premium */
.toggle-switch {
  position: relative;
  width: 44px; height: 24px;
}
.toggle-switch input { display: none; }
.toggle-switch label {
  position: absolute; top: 0; left: 0; right: 0; bottom: 0;
  background: #e2e8f0; border-radius: 20px; cursor: pointer;
  transition: all 0.3s;
}
.toggle-switch label:after {
  content: ''; position: absolute; left: 2px; top: 2px;
  width: 20px; height: 20px; background: white;
  border-radius: 50%; box-shadow: 0 2px 4px rgba(0,0,0,0.1);
  transition: all 0.3s;
}
.toggle-switch input:checked + label { background: var(--accent-indigo); }
.toggle-switch input:checked + label:after { left: 22px; }

.badge-amber { background: var(--accent-amber-light); color: var(--accent-amber); }
.badge-blue { background: var(--accent-indigo-light); color: var(--accent-indigo); }
.badge-indigo { background: #f1f5f9; color: var(--text-secondary); }

.grid { display: grid; }
.grid-cols-2 { grid-template-columns: 1fr 1fr; }
.col-span-2 { grid-column: span 2; }
.gap-4 { gap: 16px; }
.rounded-xl { border-radius: 12px; }
.letter-spacing-1 { letter-spacing: 1px; }
.uppercase { text-transform: uppercase; }
.max-w-sm { max-width: 320px; }
</style>
