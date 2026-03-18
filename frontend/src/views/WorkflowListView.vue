<template>
  <div class="workflow-list-page">
    <div class="flex items-center justify-between mb-6">
      <div>
        <h1 class="text-bold m-0" style="font-size: 24px;">Workflows</h1>
        <p class="text-gray m-0 mt-1">Design and manage your automated processes</p>
      </div>
      <router-link v-if="isAdmin" to="/workflows/new" class="btn btn-primary">
        + Create Workflow
      </router-link>
    </div>

    <div v-if="store.loading" class="text-center p-4">
      <span class="spinner">🌀</span> Loading workflows...
    </div>

    <div v-else-if="store.workflows.length === 0" class="card text-center py-10">
      <div class="text-gray mb-4" style="font-size: 48px;">📋</div>
      <h3 class="text-bold mb-2 m-0">No workflows found</h3>
      <p class="text-gray mb-6 mt-1">Get started by creating your first workflow.</p>
      <router-link v-if="isAdmin" to="/workflows/new" class="btn btn-primary">+ Create Workflow</router-link>
    </div>

    <div v-else class="grid-card">
      <div v-for="wf in store.workflows" :key="wf.id" class="wf-card glass shadow-hover">
        <div class="wf-header">
           <div class="flex flex-col">
             <span class="text-bold wf-title">{{ wf.name }}</span>
             <span class="text-sm text-gray mt-1">Version {{ wf.version }}</span>
           </div>
           <StatusBadge :status="wf.is_active ? 'active' : 'inactive'" />
        </div>
        
        <div class="wf-body mt-6">
          <div class="stat-mini">
            <span class="label">Steps</span>
            <span class="val">{{ wf.steps ? wf.steps.length : '0' }}</span>
          </div>
          <div class="stat-mini">
            <span class="label">Updated</span>
            <span class="val">{{ formatDate(wf.updated_at) }}</span>
          </div>
        </div>

        <div class="wf-footer mt-8 pt-4 flex items-center justify-between gap-3">
           <router-link v-if="isAdmin" :to="`/workflows/${wf.id}/edit`" class="btn btn-outlined flex-1 text-center">Edit</router-link>
           <button class="btn btn-primary flex-1 shadow-sm" @click="openExecuteModal(wf)">Execute</button>
        </div>
      </div>
    </div>
    
    <!-- Execute Modal -->
    <div v-if="executeModal.show" class="modal-backdrop" @click="closeExecuteModal">
      <div class="modal" @click.stop>
        <h2 class="text-bold mb-2 mt-0">Execute Workflow</h2>
        <p class="text-gray text-sm mb-6">Provide input data for {{ executeModal.workflow?.name }}</p>
        
        <form @submit.prevent="runExecution">
          <div v-for="field in inputSchemaFields" :key="field.name" class="mb-4">
            <label class="text-sm text-bold mb-2 flex">
              {{ formatFieldName(field.name) }}
              <span v-if="field.required" class="text-red ml-1">*</span>
            </label>
            
            <select v-if="field.allowed_values && field.allowed_values.length" v-model="executeForm[field.name]" class="form-select" :required="field.required">
              <option value="">Select {{ field.name }}</option>
              <option v-for="val in field.allowed_values" :key="val" :value="val">{{ val }}</option>
            </select>
            
            <input v-else-if="field.type === 'number'" type="number" v-model.number="executeForm[field.name]" class="form-input" :required="field.required" step="any" />
            
            <div v-else-if="field.type === 'boolean'" class="flex items-center gap-2">
               <input type="checkbox" v-model="executeForm[field.name]" :required="field.required && !executeForm[field.name]" />
               <span class="text-sm">Enabled</span>
            </div>

            <input v-else type="text" v-model="executeForm[field.name]" class="form-input" :required="field.required" />
          </div>

          <div class="mb-6">
            <label class="text-sm text-bold mb-2 flex">Max Iterations</label>
            <input type="number" v-model.number="executeMaxIter" class="form-input" min="1" max="100" />
          </div>

          <div class="flex justify-between mt-6">
             <button type="button" class="btn btn-ghost" @click="closeExecuteModal">Cancel</button>
             <button type="submit" class="btn btn-primary" :disabled="executing">
               <span v-if="executing" class="spinner">🌀</span>
               <span v-else>Run Execution</span>
             </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { useWorkflowStore } from '@/stores/workflow'
import { useExecutionStore } from '@/stores/execution'
import { useAuthStore } from '@/stores/auth'
import StatusBadge from '@/components/common/StatusBadge.vue'

const store = useWorkflowStore()
const execStore = useExecutionStore()
const authStore = useAuthStore()
const router = useRouter()

const isAdmin = computed(() => authStore.isAdmin)
let refreshInterval = null

const executeModal = reactive({
  show: false,
  workflow: null
})
const executeForm = reactive({})
const executeMaxIter = ref(10)
const executing = ref(false)

const loadData = () => store.fetchWorkflows()

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
  return d.toLocaleDateString() + ' ' + d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
}

const inputSchemaFields = computed(() => {
  if (!executeModal.workflow || !executeModal.workflow.input_schema) return []
  return executeModal.workflow.input_schema.fields || []
})

const formatFieldName = (name) => {
  return name.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())
}

const openExecuteModal = async (wf) => {
  const fullWf = await store.fetchWorkflow(wf.id)
  executeModal.workflow = fullWf
  
  // Reset form
  Object.keys(executeForm).forEach(k => delete executeForm[k])
  
  const fields = fullWf.input_schema?.fields || []
  fields.forEach(f => {
    if (f.type === 'boolean') executeForm[f.name] = false
    else if (f.type === 'number') executeForm[f.name] = null
    else executeForm[f.name] = ''
  })
  
  executeModal.show = true
}

const closeExecuteModal = () => {
  executeModal.show = false
  executeModal.workflow = null
}

const runExecution = async () => {
  executing.value = true
  try {
    const res = await execStore.executeWorkflow(executeModal.workflow.id, executeForm, executeMaxIter.value)
    closeExecuteModal()
    router.push(`/workflows/${res.id}/execute`)
  } finally {
    executing.value = false
  }
}
</script>

<style scoped>
.py-10 { padding-top: 40px; padding-bottom: 40px; }
.grid-card {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 24px;
}
.wf-card {
  display: flex; flex-direction: column;
  background: white; border-radius: 20px; padding: 24px;
  border: 1px solid var(--border-color);
}
.wf-header {
  display: flex; justify-content: space-between; align-items: flex-start;
}
.wf-title { font-size: 18px; color: var(--text-primary); letter-spacing: -0.5px; }

.stat-mini {
  display: flex; justify-content: space-between; align-items: center;
  padding: 10px 0; border-bottom: 1px dashed var(--border-color);
}
.stat-mini:last-child { border-bottom: none; }
.stat-mini .label { font-size: 13px; color: var(--text-muted); font-weight: 500; }
.stat-mini .val { font-size: 13px; font-weight: 700; color: var(--text-primary); }

.modal-footer {
  margin-top: 24px;
  display: flex; justify-content: flex-end; gap: 12px;
}
.border-t { border-top: 1px solid var(--border-color); }
.pt-4 { padding-top: 16px; }
.ml-1 { margin-left: 4px; }
.text-red { color: var(--error-text); }
</style>
