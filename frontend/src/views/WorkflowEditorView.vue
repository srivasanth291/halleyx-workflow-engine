<template>
  <div>
    <div class="flex gap-6">
      <!-- LEFT PANEL: Workflow Details Form -->
      <div style="width:40%;flex-shrink:0">
        <div class="card card-body" style="display:flex;flex-direction:column;gap:20px">
          <h2 style="font-size:18px;font-weight:700">{{ isCreate ? 'Create Workflow' : 'Edit Workflow' }}</h2>

          <div class="form-group">
            <label class="form-label">Workflow Name <span class="req">*</span></label>
            <input v-model="form.name" class="form-input" placeholder="e.g. Expense Approval" />
          </div>

          <div v-if="!isCreate" class="toggle-row">
            <button type="button" class="toggle" :class="{on: form.is_active}" @click="form.is_active = !form.is_active"></button>
            <span class="toggle-label">Is Active</span>
          </div>

          <div class="divider"></div>

          <div>
            <div class="flex items-center justify-between" style="margin-bottom:12px">
              <div>
                <p style="font-weight:600;font-size:15px">Input Schema</p>
                <p class="text-sm text-secondary">Fields required when executing</p>
              </div>
            </div>
            <div v-if="form.input_schema.fields.length" class="table-card" style="margin-bottom:12px">
              <table>
                <thead>
                  <tr><th>FIELD</th><th>TYPE</th><th>REQ</th><th>VALUES</th><th></th></tr>
                </thead>
                <tbody>
                  <tr v-for="(f, i) in form.input_schema.fields" :key="i">
                    <td class="mono" style="font-size:12px">{{ f.name }}</td>
                    <td><span class="badge badge-gray" style="font-size:11px">{{ f.type }}</span></td>
                    <td>{{ f.required ? '✅' : '—' }}</td>
                    <td class="text-sm text-secondary">{{ f.allowed_values?.join(', ') || '—' }}</td>
                    <td>
                      <button class="btn-icon danger" @click="removeField(i)">
                        <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                          <path d="M3 6h18M8 6V4h8v2M19 6l-1 14H6L5 6"/>
                        </svg>
                      </button>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
            <button class="btn btn-outlined btn-full" style="border-style:dashed" @click="showSchemaModal = true">
              + Add Field
            </button>
          </div>

          <div class="divider"></div>

          <button class="btn btn-primary btn-full btn-lg" :disabled="saving" @click="save">
            <span v-if="saving" class="spinner"></span>
            {{ saving ? 'Saving...' : (isCreate ? 'Create Workflow' : 'Save Changes') }}
          </button>

          <p v-if="saveError" class="form-error-msg">{{ saveError }}</p>
        </div>
      </div>

      <!-- RIGHT PANEL: Steps -->
      <div style="flex:1">
        <div class="card card-body">
          <div class="flex items-center justify-between" style="margin-bottom:16px">
            <div>
              <h2 style="font-size:18px;font-weight:700">Steps</h2>
              <p class="text-sm text-secondary">Drag to reorder</p>
            </div>
            <button class="btn btn-outlined btn-sm" :disabled="isCreate || !workflowId" @click="openAddStep">
              + Add Step
            </button>
          </div>

          <div v-if="isCreate" class="empty-state" style="padding:40px 20px">
            <p>Save the workflow first to add steps</p>
          </div>
          <div v-else-if="steps.length === 0" class="empty-state" style="padding:40px 20px">
            <h3>No steps yet</h3>
            <p>Add steps to define your workflow process</p>
            <button class="btn btn-outlined" @click="openAddStep">+ Add Step</button>
          </div>
          <div v-else style="display:flex;flex-direction:column;gap:10px">
            <StepCard
              v-for="(step, i) in steps"
              :key="step.id"
              :step="step"
              :index="i"
              @edit="openEditStep(step)"
              @rules="goToRules(step)"
              @delete="openDeleteStep(step)"
            />
          </div>
        </div>
      </div>
    </div>

    <SchemaFieldModal v-if="showSchemaModal" @add="addField" @cancel="showSchemaModal = false" />

    <StepModal
      v-if="showStepModal"
      :workflow-id="workflowId"
      :step="editingStep"
      @saved="onStepSaved"
      @cancel="showStepModal = false; editingStep = null"
    />

    <ConfirmModal
      v-if="showDeleteStepModal"
      title="Delete Step?"
      message="This will delete the step and all its rules."
      confirmText="Delete Step"
      type="delete"
      @confirm="confirmDeleteStep"
      @cancel="showDeleteStepModal = false"
    />
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useWorkflowStore } from '@/stores/workflow'
import { useNotificationStore } from '@/stores/notification'
import stepService from '@/services/step.service'
import StepCard from '@/components/workflow/StepCard.vue'
import StepModal from '@/components/workflow/StepModal.vue'
import SchemaFieldModal from '@/components/workflow/SchemaFieldModal.vue'
import ConfirmModal from '@/components/common/ConfirmModal.vue'

const route = useRoute()
const router = useRouter()
const wfStore = useWorkflowStore()
const notif = useNotificationStore()

const isCreate = computed(() => route.path === '/workflows/new')
const workflowId = computed(() => route.params.id)

const form = reactive({ name: '', is_active: true, input_schema: { fields: [] } })
const steps = ref([])
const saving = ref(false)
const saveError = ref('')
const showSchemaModal = ref(false)
const showStepModal = ref(false)
const editingStep = ref(null)
const showDeleteStepModal = ref(false)
const deletingStep = ref(null)

onMounted(async () => {
  if (!isCreate.value && workflowId.value) {
    const wf = await wfStore.fetchWorkflow(workflowId.value)
    form.name = wf.name
    form.is_active = wf.is_active
    form.input_schema = wf.input_schema || { fields: [] }
    steps.value = wf.steps || []
  }
})

async function save() {
  saveError.value = ''
  if (!form.name.trim()) { saveError.value = 'Workflow name is required'; return }
  saving.value = true
  try {
    if (isCreate.value) {
      const wf = await wfStore.createWorkflow({ name: form.name, input_schema: form.input_schema })
      notif.success('Workflow created!')
      router.push(`/workflows/${wf.id}/edit`)
    } else {
      const wf = await wfStore.updateWorkflow(workflowId.value, {
        name: form.name,
        is_active: form.is_active,
        input_schema: form.input_schema,
      })
      notif.success(`New version v${wf.version} created!`)
    }
  } catch (e) {
    saveError.value = e.response?.data?.detail || JSON.stringify(e.response?.data) || 'Save failed'
  } finally {
    saving.value = false
  }
}

function addField(field) {
  form.input_schema.fields.push(field)
  showSchemaModal.value = false
}

function removeField(i) {
  form.input_schema.fields.splice(i, 1)
}

function openAddStep() { editingStep.value = null; showStepModal.value = true }
function openEditStep(step) { editingStep.value = step; showStepModal.value = true }
function goToRules(step) { router.push(`/workflows/${workflowId.value}/steps/${step.id}/rules`) }
function openDeleteStep(step) { deletingStep.value = step; showDeleteStepModal.value = true }

async function onStepSaved() {
  showStepModal.value = false
  editingStep.value = null
  const wf = await wfStore.fetchWorkflow(workflowId.value)
  steps.value = wf.steps || []
}

async function confirmDeleteStep() {
  try {
    await stepService.delete(deletingStep.value.id)
    notif.success('Step deleted!')
    showDeleteStepModal.value = false
    const wf = await wfStore.fetchWorkflow(workflowId.value)
    steps.value = wf.steps || []
  } catch {
    notif.error('Delete failed')
  }
}
</script>
