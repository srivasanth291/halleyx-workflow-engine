<template>
  <div class="stepper">
    <template v-for="(step, i) in steps" :key="step.id">
      <div class="stepper-item">
        <div :class="['stepper-circle', stepStatus(step.id)]">
          <span v-if="stepStatus(step.id) === 'completed'">✓</span>
          <span v-else-if="stepStatus(step.id) === 'in-progress'">
            <span class="spinner" style="width:16px;height:16px;border-width:2px;color:white"></span>
          </span>
          <span v-else-if="stepStatus(step.id) === 'failed'">✕</span>
          <span v-else style="font-size:11px">{{ i + 1 }}</span>
        </div>
        <div :class="['stepper-label', stepStatus(step.id)]">{{ step.name }}</div>
      </div>
      <div
        v-if="i < steps.length - 1"
        :class="['stepper-line', stepStatus(step.id) === 'completed' ? 'done' : 'pending-line']"
      ></div>
    </template>
  </div>
</template>

<script setup>
const props = defineProps({
  steps:         { type: Array,  default: () => [] },
  logs:          { type: Array,  default: () => [] },
  currentStepId: { type: String, default: null },
})

function stepStatus(stepId) {
  const log = props.logs.find(l => l.step_id === stepId)
  if (log) {
    if (['completed', 'approve'].includes(log.status)) return 'completed'
    if (['failed', 'reject'].includes(log.status))     return 'failed'
    if (log.status === 'pending_approval' || log.status === 'in_progress') return 'in-progress'
  }
  if (String(props.currentStepId) === String(stepId)) return 'in-progress'
  return 'pending'
}
</script>
