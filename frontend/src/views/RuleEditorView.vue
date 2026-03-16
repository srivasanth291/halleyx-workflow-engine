<template>
  <div>
    <div class="breadcrumb">
      <router-link to="/workflows">Workflows</router-link>
      <span class="sep">›</span>
      <router-link :to="`/workflows/${workflowId}/edit`">{{ wfName }}</router-link>
      <span class="sep">›</span>
      <span class="cur">{{ stepName }} — Rules</span>
    </div>

    <div style="margin-top:20px">
      <div class="page-header">
        <div>
          <h1 class="page-title">Rules for {{ stepName }}</h1>
          <span class="badge badge-info">{{ rules.length }} rule{{ rules.length !== 1 ? 's' : '' }}</span>
        </div>
        <button class="btn btn-primary" @click="openAdd">+ Add Rule</button>
      </div>

      <div class="table-card">
        <table>
          <thead>
            <tr><th>#</th><th>PRIORITY</th><th>CONDITION</th><th>NEXT STEP</th><th>ACTIONS</th></tr>
          </thead>
          <tbody>
            <template v-if="rules.length">
              <tr v-for="(rule, i) in rules" :key="rule.id">
                <td class="text-muted text-sm">{{ i + 1 }}</td>
                <td>
                  <span
                    :style="priStyle(rule.priority)"
                    style="width:26px;height:26px;border-radius:50%;display:inline-flex;align-items:center;justify-content:center;font-size:12px;font-weight:700;color:white"
                  >{{ rule.priority }}</span>
                </td>
                <td>
                  <span :class="['code-chip', rule.condition.toUpperCase() === 'DEFAULT' ? 'default' : '']">
                    {{ rule.condition }}
                  </span>
                </td>
                <td>
                  <span v-if="rule.next_step_id" class="next-chip step">{{ getStepName(rule.next_step_id) }}</span>
                  <span v-else class="next-chip end">END</span>
                </td>
                <td>
                  <div class="flex gap-2">
                    <button class="btn-icon indigo" @click="openEdit(rule)">
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M11 4H4a2 2 0 00-2 2v14a2 2 0 002 2h14a2 2 0 002-2v-7"/>
                        <path d="M18.5 2.5a2.121 2.121 0 013 3L12 15l-4 1 1-4 9.5-9.5z"/>
                      </svg>
                    </button>
                    <button class="btn-icon danger" @click="openDeleteRule(rule)">
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M3 6h18M8 6V4h8v2M19 6l-1 14H6L5 6"/>
                      </svg>
                    </button>
                  </div>
                </td>
              </tr>
            </template>
            <tr v-else>
              <td colspan="5">
                <div class="empty-state" style="padding:40px">
                  <h3>No rules yet</h3>
                  <p>Add rules to control workflow transitions</p>
                  <button class="btn btn-outlined" @click="openAdd">+ Add Rule</button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
        <div style="padding:12px 16px">
          <div :class="['alert', hasDefault ? 'alert-warning' : 'alert-error']">
            <span>{{ hasDefault ? '⚠️ DEFAULT rule handles unmatched conditions' : '❌ DEFAULT rule is missing! Add it as fallback.' }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Rule Modal -->
    <div v-if="showModal" class="modal-backdrop" @click.self="closeModal">
      <div class="modal modal-lg">
        <div class="modal-header">
          <h3>{{ editingRule ? 'Edit Rule' : 'Add Rule' }}</h3>
          <button class="btn-icon" @click="closeModal">✕</button>
        </div>
        <div class="modal-body">
          <div class="form-group">
            <label class="form-label">Priority</label>
            <input v-model.number="ruleForm.priority" type="number" class="form-input" style="width:100px" min="1" />
            <span class="form-hint">Lower number = evaluated first</span>
          </div>

          <div class="form-group">
            <label class="form-label">Condition <span class="req">*</span></label>
            <textarea
              v-model="ruleForm.condition"
              class="form-input form-textarea code-input"
              placeholder="amount > 100 && country == 'US'"
              rows="3"
            ></textarea>
            <div class="op-chips" style="margin-top:8px">
              <button v-for="op in operators" :key="op" class="op-chip" @click="insertOp(op)">{{ op }}</button>
            </div>
            <div v-if="validation.valid === true" class="validation-bar valid" style="margin-top:8px">
              ✅ Valid condition syntax
            </div>
            <div v-else-if="validation.valid === false" class="validation-bar invalid" style="margin-top:8px">
              ❌ {{ validation.error }}
            </div>
          </div>

          <div class="form-group">
            <label class="form-label">Next Step</label>
            <select v-model="ruleForm.next_step_id" class="form-input form-select">
              <option value="">⛔ END — Terminate workflow</option>
              <option v-for="s in allSteps" :key="s.id" :value="s.id">{{ s.name }}</option>
            </select>
          </div>

          <p v-if="modalError" class="form-error-msg">{{ modalError }}</p>
        </div>
        <div class="modal-footer">
          <button class="btn btn-ghost flex-1" @click="closeModal">Cancel</button>
          <button
            class="btn btn-primary flex-1"
            :disabled="validation.valid === false || savingRule"
            @click="saveRule"
          >
            <span v-if="savingRule" class="spinner"></span>
            {{ savingRule ? 'Saving...' : 'Save Rule' }}
          </button>
        </div>
      </div>
    </div>

    <!-- Delete Confirm Modal -->
    <ConfirmModal
      v-if="showDeleteModal"
      title="Delete Rule?"
      message="This rule will be permanently deleted."
      confirmText="Delete Rule"
      type="delete"
      @confirm="confirmDeleteRule"
      @cancel="showDeleteModal = false"
    />
  </div>
</template>

<script setup>
import { ref, reactive, computed, watch, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import ruleService from '@/services/rule.service'
import stepService from '@/services/step.service'
import { useNotificationStore } from '@/stores/notification'
import ConfirmModal from '@/components/common/ConfirmModal.vue'

const route = useRoute()
const notif = useNotificationStore()

const workflowId = route.params.workflowId
const stepId = route.params.stepId

const rules = ref([])
const allSteps = ref([])
const stepName = ref('Step')
const wfName = ref('Workflow')
const showModal = ref(false)
const editingRule = ref(null)
const showDeleteModal = ref(false)
const deletingRule = ref(null)
const savingRule = ref(false)
const modalError = ref('')
const validation = reactive({ valid: null, error: '' })
const ruleForm = reactive({ condition: '', next_step_id: '', priority: 1 })

const operators = ['==', '!=', '>', '<', '>=', '<=', '&&', '||', 'contains()', 'startsWith()', 'endsWith()', 'DEFAULT']
const hasDefault = computed(() => rules.value.some(r => r.condition.toUpperCase() === 'DEFAULT'))

function priStyle(p) {
  if (p === 1)  return 'background:#16A34A'
  if (p === 2)  return 'background:#2563EB'
  return 'background:#94A3B8'
}

function getStepName(id) {
  return allSteps.value.find(s => s.id === id)?.name || id
}

let vTimer = null
watch(() => ruleForm.condition, async (val) => {
  clearTimeout(vTimer)
  if (!val) { validation.valid = null; return }
  vTimer = setTimeout(async () => {
    try {
      const res = await ruleService.validate({ condition: val })
      validation.valid = res.data.valid
      validation.error = res.data.error || ''
    } catch { validation.valid = null }
  }, 500)
})

function insertOp(op) {
  ruleForm.condition += (ruleForm.condition.endsWith(' ') || !ruleForm.condition ? '' : ' ') + op + ' '
}

function openAdd() {
  editingRule.value = null
  ruleForm.condition = ''
  ruleForm.next_step_id = ''
  ruleForm.priority = rules.value.length + 1
  validation.valid = null
  modalError.value = ''
  showModal.value = true
}

function openEdit(rule) {
  editingRule.value = rule
  ruleForm.condition = rule.condition
  ruleForm.next_step_id = rule.next_step_id || ''
  ruleForm.priority = rule.priority
  validation.valid = null
  modalError.value = ''
  showModal.value = true
}

function closeModal() { showModal.value = false; editingRule.value = null }

async function saveRule() {
  modalError.value = ''
  if (!ruleForm.condition.trim()) { modalError.value = 'Condition is required'; return }
  savingRule.value = true
  try {
    const data = {
      condition: ruleForm.condition,
      next_step_id: ruleForm.next_step_id || null,
      priority: ruleForm.priority,
    }
    if (editingRule.value) {
      await ruleService.update(editingRule.value.id, data)
      notif.success('Rule updated!')
    } else {
      await ruleService.create(stepId, data)
      notif.success('Rule added!')
    }
    await loadRules()
    closeModal()
  } catch (e) {
    modalError.value = e.response?.data?.detail || JSON.stringify(e.response?.data) || 'Save failed'
  } finally {
    savingRule.value = false
  }
}

function openDeleteRule(rule) { deletingRule.value = rule; showDeleteModal.value = true }

async function confirmDeleteRule() {
  try {
    await ruleService.delete(deletingRule.value.id)
    notif.success('Rule deleted!')
    showDeleteModal.value = false
    await loadRules()
  } catch {
    notif.error('Delete failed')
  }
}

async function loadRules() {
  const res = await ruleService.getAll(stepId)
  rules.value = res.data
}

onMounted(async () => {
  await loadRules()
  const stepsRes = await stepService.getAll(workflowId)
  allSteps.value = stepsRes.data || []
  const thisStep = allSteps.value.find(s => String(s.id) === String(stepId))
  stepName.value = thisStep?.name || 'Step'
  wfName.value = 'Workflow'
})
</script>
