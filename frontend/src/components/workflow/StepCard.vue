<template>
  <div class="step-card">
    <div class="step-drag">⠿</div>
    <div class="step-num">{{ index + 1 }}</div>
    <div class="step-name">{{ step.name }}</div>
    <span :class="['badge', typeBadge]">{{ step.step_type }}</span>
    <div class="step-actions">
      <button class="btn-icon indigo" @click="$emit('edit', step)" title="Edit">
        <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M11 4H4a2 2 0 00-2 2v14a2 2 0 002 2h14a2 2 0 002-2v-7"/>
          <path d="M18.5 2.5a2.121 2.121 0 013 3L12 15l-4 1 1-4 9.5-9.5z"/>
        </svg>
      </button>
      <button class="btn-icon indigo" @click="$emit('rules', step)" title="Rules">
        <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <polyline points="9 11 12 14 22 4"/>
          <path d="M21 12v7a2 2 0 01-2 2H5a2 2 0 01-2-2V5a2 2 0 012-2h11"/>
        </svg>
      </button>
      <button class="btn-icon danger" @click="$emit('delete', step)" title="Delete">
        <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M3 6h18M8 6V4h8v2M19 6l-1 14H6L5 6"/>
        </svg>
      </button>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
defineEmits(['edit', 'rules', 'delete'])
const props = defineProps({ step: Object, index: Number })
const typeBadge = computed(() => ({
  approval:     'badge-amber',
  notification: 'badge-info',
  task:         'badge-purple',
}[props.step.step_type] || 'badge-gray'))
</script>

<style scoped>
.step-card {
  display: flex; align-items: center; gap: 12px;
  background: white; border: 1px solid var(--border-color);
  border-radius: 8px; padding: 14px 16px;
  cursor: grab; transition: box-shadow .15s;
}
.step-card:hover { box-shadow: var(--card-shadow); }
.step-drag { color: var(--text-muted); font-size: 16px; cursor: grab; }
.step-num {
  width: 24px; height: 24px; background: var(--text-primary);
  color: white; border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  font-size: 12px; font-weight: 700; flex-shrink: 0;
}
.step-name { flex: 1; font-weight: 600; font-size: 14px; }
.step-actions { display: flex; gap: 4px; }
</style>
