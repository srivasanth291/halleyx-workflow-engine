<template>
  <div class="workflow-chart-container glass">
    <div class="chart-header">
      <span class="text-bold text-sm uppercase">Workflow Map</span>
    </div>
    <div class="chart-body">
      <div v-for="(step, index) in sortedSteps" :key="step.id" class="chart-step-wrapper">
        <div 
          class="chart-step glass shadow-hover" 
          :class="{ active: currentStepId === String(step.id) }"
        >
          <div class="step-type-icon">{{ getStepIcon(step.step_type) }}</div>
          <div class="step-details">
            <div class="step-name">{{ step.name }}</div>
            <div class="step-meta">Order {{ step.order }} • {{ step.step_type }}</div>
          </div>
        </div>
        <div v-if="index < sortedSteps.length - 1" class="chart-arrow">
          <svg width="20" height="40" viewBox="0 0 20 40">
            <path d="M10 0 L10 40 M5 35 L10 40 L15 35" fill="none" stroke="var(--border-color)" stroke-width="2" />
          </svg>
        </div>
      </div>
      <div class="chart-end">
        <div class="end-node">END</div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  steps: { type: Array, default: () => [] },
  currentStepId: { type: String, default: null }
})

const sortedSteps = computed(() => {
  return [...props.steps].sort((a, b) => a.order - b.order)
})

const getStepIcon = (type) => {
  if (type === 'approval') return '⚖️'
  if (type === 'notification') return '🔔'
  return '⚙️'
}
</script>

<style scoped>
.workflow-chart-container {
  padding: 20px;
  border-radius: 16px;
  max-height: 500px;
  overflow-y: auto;
}
.chart-header { margin-bottom: 24px; text-align: center; }
.chart-body {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0;
}
.chart-step-wrapper {
  display: flex;
  flex-direction: column;
  align-items: center;
}
.chart-step {
  width: 200px;
  padding: 16px;
  border-radius: 14px;
  display: flex;
  align-items: center;
  gap: 12px;
  border: 1px solid var(--border-color);
  background: white;
  transition: all 0.3s;
}
.chart-step.active {
  border-color: var(--accent-indigo);
  background: var(--accent-indigo-light);
  transform: scale(1.05);
  box-shadow: 0 10px 25px -5px rgba(99, 102, 241, 0.2);
}
.step-type-icon { font-size: 20px; }
.step-name { font-weight: 700; font-size: 14px; color: var(--text-primary); }
.step-meta { font-size: 11px; color: var(--text-muted); text-transform: uppercase; margin-top: 2px; }

.chart-arrow {
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.chart-end { margin-top: 20px; }
.end-node {
  width: 60px; height: 60px;
  border-radius: 50%;
  background: #f1f5f9;
  border: 2px dashed var(--border-color);
  display: flex; align-items: center; justify-content: center;
  font-weight: 800; font-size: 11px; color: var(--text-muted);
}
</style>
