<template>
  <div class="step-progress">
    <div v-for="(step, index) in steps" :key="step.id" class="progress-item" :class="getStepClass(step)">
      <div class="step-circle">
        <span v-if="isStepCompleted(step)">✓</span>
        <span v-else>{{ index + 1 }}</span>
      </div>
      <div class="step-info">
        <div class="step-name">{{ step.name }}</div>
        <div class="step-status">{{ getStepStatusText(step) }}</div>
      </div>
      <div v-if="index < steps.length - 1" class="step-line"></div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  steps: { type: Array, default: () => [] },
  currentStepId: { type: String, default: null },
  logs: { type: Array, default: () => [] },
  status: { type: String, default: 'pending' }
})

const getStepClass = (step) => {
  if (isStepCompleted(step)) return 'completed'
  if (String(step.id) === String(props.currentStepId)) return 'active'
  return 'pending'
}

const isStepCompleted = (step) => {
  return props.logs.some(log => String(log.step_id) === String(step.id) && log.status === 'completed')
}

const getStepStatusText = (step) => {
  if (isStepCompleted(step)) return 'Completed'
  if (String(step.id) === String(props.currentStepId)) return 'In Progress'
  return 'Pending'
}
</script>

<style scoped>
.step-progress {
  display: flex;
  flex-direction: column;
  gap: 20px;
}
.progress-item {
  display: flex;
  align-items: center;
  gap: 16px;
  position: relative;
}
.step-circle {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: bold;
  font-size: 14px;
  border: 2px solid var(--border-color);
  background: white;
  z-index: 2;
}
.step-info {
  display: flex;
  flex-direction: column;
}
.step-name {
  font-weight: 600;
  font-size: 14px;
}
.step-status {
  font-size: 12px;
  color: var(--text-muted);
}
.step-line {
  position: absolute;
  top: 32px;
  left: 15px;
  width: 2px;
  height: 20px;
  background: var(--border-color);
}

.completed .step-circle {
  background: var(--accent-green);
  border-color: var(--accent-green);
  color: white;
}
.completed .step-line {
  background: var(--accent-green);
}
.active .step-circle {
  border-color: var(--accent-indigo);
  color: var(--accent-indigo);
  box-shadow: 0 0 0 4px var(--accent-indigo-light);
}
</style>
