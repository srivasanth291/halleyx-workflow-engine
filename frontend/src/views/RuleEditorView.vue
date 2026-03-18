<template>
  <div class="rules-page">
    <div class="flex items-center mb-6 gap-4">
      <router-link :to="`/workflows/${workflowId}/edit`" class="btn btn-ghost" style="padding: 6px;">←</router-link>
      <div>
        <h1 class="text-bold m-0" style="font-size: 20px;">Rules Configuration</h1>
        <p class="text-gray m-0 text-sm mt-1">Step: {{ step?.name || 'Loading...' }}</p>
      </div>
    </div>

    <div class="card glass shadow-hover p-0 overflow-hidden">
      <div class="flex items-center justify-between p-6 bg-white/50 backdrop-blur-sm">
         <h2 class="text-bold m-0 uppercase letter-spacing-1" style="font-size: 14px;">Logic Branching Registry</h2>
         <button class="btn btn-primary px-6" @click="openModal()">+ Add Logic Branch</button>
      </div>

      <div class="table-container">
        <table>
          <thead>
            <tr>
              <th class="uppercase letter-spacing-1 text-xs px-6 py-4">Execution Priority</th>
              <th class="uppercase letter-spacing-1 text-xs px-6 py-4">Evaluation Condition</th>
              <th class="uppercase letter-spacing-1 text-xs px-6 py-4">Target Destination</th>
              <th class="uppercase letter-spacing-1 text-xs px-6 py-4">Operations</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="rule in rules" :key="rule.id" class="hover-row">
              <td class="px-6 py-4">
                <div class="priority-badge indigo-gradient shadow-sm">{{ rule.priority }}</div>
              </td>
              <td class="px-6 py-4">
                <code class="code-chip glass border border-indigo-200 text-indigo-700">{{ rule.condition }}</code>
              </td>
              <td class="px-6 py-4">
                <span v-if="rule.next_step_id" class="font-semibold text-sm">{{ getStepName(rule.next_step_id) }}</span>
                <span v-else class="text-muted text-xs uppercase letter-spacing-1 font-bold">终止 Terminal End</span>
              </td>
              <td class="px-6 py-4">
                <div class="flex items-center gap-2">
                  <button class="btn btn-outlined text-xs py-2 px-4" @click="openModal(rule)">Config</button>
                  <button class="btn btn-outlined text-xs py-2 px-4 text-red" @click="deleteRule(rule.id)">Delete</button>
                </div>
              </td>
            </tr>
            <tr v-if="rules.length === 0">
              <td colspan="4" class="text-center text-gray p-12 italic">No logic branches established. The engine will halt if no conditions match.</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Rule Modal -->
    <div v-if="modal.show" class="modal-backdrop" @click="closeModal">
      <div class="modal" @click.stop>
        <h2 class="text-bold mb-4 mt-0">{{ modal.isEdit ? 'Edit Rule' : 'Add Rule' }}</h2>
        <form @submit.prevent="saveRule">
          <div class="mb-4">
            <label class="text-sm text-bold mb-2 flex justify-between items-center">
              Condition Statement
              <span v-if="syntaxStatus === 'valid'" class="text-green text-xs">✓ Valid Syntax</span>
              <span v-else-if="syntaxStatus === 'invalid'" class="text-red text-xs">✗ Invalid</span>
              <button type="button" class="btn btn-ghost text-xs py-0 px-2" @click="validateSyntax">Verify Syntax</button>
            </label>
            <input type="text" v-model="form.condition" class="form-input code-font" placeholder="e.g. amount > 1000 && country == 'US' or DEFAULT" required />
            <p class="text-xs text-gray mt-1">Use 'DEFAULT' as a fallback condition.</p>
          </div>
          
          <div class="mb-4">
            <label class="text-sm text-bold mb-2">Next Step</label>
            <select v-model="form.next_step_id" class="form-select">
              <option :value="null">-- End Workflow --</option>
              <option v-for="s in workflowSteps" :key="s.id" :value="s.id">{{ s.order }}: {{ s.name }}</option>
            </select>
          </div>

          <div class="mb-6">
            <label class="text-sm text-bold mb-2">Priority</label>
            <input type="number" v-model.number="form.priority" class="form-input" min="1" required />
            <p class="text-xs text-gray mt-1">Lower number = higher priority (evaluated first).</p>
          </div>

          <div class="flex justify-between">
            <button type="button" class="btn btn-ghost" @click="closeModal">Cancel</button>
            <button type="submit" class="btn btn-primary" :disabled="loading.save">Save Rule</button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import { useRoute } from 'vue-router'
import ruleService from '@/services/rule.service'
import { useWorkflowStore } from '@/stores/workflow'
import { useNotificationStore } from '@/stores/notification'

const route = useRoute()
const store = useWorkflowStore()
const ns = useNotificationStore()

const workflowId = computed(() => route.params.workflowId)
const stepId = computed(() => route.params.stepId)

const step = ref(null)
const rules = ref([])
const workflowSteps = ref([])

const loading = reactive({ main: false, save: false })
const syntaxStatus = ref(null)

const modal = reactive({ show: false, isEdit: false })
const form = reactive({ id: null, condition: '', next_step_id: null, priority: 1 })

onMounted(async () => {
  loading.main = true
  try {
    const wf = await store.fetchWorkflow(workflowId.value)
    workflowSteps.value = wf.steps || []
    step.value = workflowSteps.value.find(s => s.id === parseInt(stepId.value) || s.id === stepId.value)
    
    await loadRules()
  } finally {
    loading.main = false
  }
})

const loadRules = async () => {
  const res = await ruleService.getAll(stepId.value)
  // Assumes backend sorted by priority
  rules.value = res.data.results || res.data
}

const getStepName = (id) => {
  const s = workflowSteps.value.find(x => String(x.id) === String(id))
  return s ? s.name : 'Unknown'
}

const openModal = (r = null) => {
  syntaxStatus.value = null
  if (r) {
    modal.isEdit = true
    form.id = r.id
    form.condition = r.condition
    form.next_step_id = r.next_step_id
    form.priority = r.priority
  } else {
    modal.isEdit = false
    form.id = null
    form.condition = ''
    form.next_step_id = null
    form.priority = rules.value.length + 1
  }
  modal.show = true
}

const closeModal = () => { modal.show = false }

const validateSyntax = async () => {
  if (!form.condition) return
  if (form.condition === 'DEFAULT') {
    syntaxStatus.value = 'valid'
    return
  }
  try {
    const res = await ruleService.validate({ condition: form.condition })
    syntaxStatus.value = res.data.valid ? 'valid' : 'invalid'
    if (!res.data.valid) ns.error(res.data.error || 'Syntax Error')
  } catch (e) {
    syntaxStatus.value = 'invalid'
  }
}

const saveRule = async () => {
  loading.save = true
  try {
    const payload = {
      step: parseInt(stepId.value) || stepId.value,
      condition: form.condition,
      next_step_id: form.next_step_id,
      priority: form.priority
    }
    if (modal.isEdit) {
      await ruleService.update(form.id, payload)
      ns.success('Rule updated')
    } else {
      await ruleService.create(payload)
      ns.success('Rule created')
    }
    closeModal()
    await loadRules()
  } finally {
    loading.save = false
  }
}

const deleteRule = async (id) => {
  if (confirm('Delete this rule?')) {
    await ruleService.delete(id)
    ns.success('Rule deleted')
    await loadRules()
  }
}
</script>

<style scoped>
.priority-badge {
  width: 32px; height: 32px; border-radius: 8px;
  display: flex; align-items: center; justify-content: center;
  color: white; font-weight: 800; font-size: 14px;
}
.code-chip {
  padding: 4px 10px; border-radius: 6px; font-family: 'JetBrains Mono', monospace;
  font-size: 12px; font-weight: 600;
}
.table-container { overflow-x: auto; }
.hover-row:hover { background: rgba(0,0,0,0.01); }

.code-font { font-family: 'JetBrains Mono', monospace; }
.text-green { color: var(--accent-green); }
.text-red { color: var(--accent-red); }
.text-xs { font-size: 11px; }
.text-muted { color: var(--text-muted); }
.uppercase { text-transform: uppercase; }
.letter-spacing-1 { letter-spacing: 1px; }

.border-indigo-200 { border-color: rgba(99, 102, 241, 0.2); }
.text-indigo-700 { color: var(--accent-indigo); }
</style>
