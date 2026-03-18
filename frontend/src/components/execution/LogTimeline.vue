<template>
  <div class="timeline">
    <div v-for="(log, i) in logs" :key="i" class="timeline-item">
      <div :class="['timeline-marker', getLogMarkerClass(log.status)]"></div>
      <div class="timeline-content glass shadow-hover">
        <div class="flex justify-between items-center mb-1">
          <span class="text-bold text-sm">{{ log.step_name || log.action || 'System' }}</span>
          <span class="text-xs text-gray">{{ formatDate(log.started_at || log.timestamp || log.action_at || '') }}</span>
        </div>
        <div class="text-sm flex items-center gap-2 mt-1">
          <StatusBadge :status="log.status" v-if="log.status" />
          <span class="text-gray" v-if="log.action_by">by {{ log.action_by }}</span>
        </div>
        <div v-if="log.rule_matched" class="text-xs mt-2 text-gray bg-gray-light p-2 rounded">
          <strong>Rule matched:</strong> <span class="code-font">{{ log.rule_matched }}</span>
        </div>
        <div v-if="log.error" class="text-red text-sm mt-2 p-2 bg-red-light rounded">{{ log.error }}</div>
        <div v-if="log.comment" class="text-sm mt-2 italic text-gray">"{{ log.comment }}"</div>
        <div v-if="log.info" class="text-sm mt-2 text-gray">{{ log.info }}</div>
      </div>
    </div>
  </div>
</template>

<script setup>
import StatusBadge from '@/components/common/StatusBadge.vue'

const props = defineProps({
  logs: { type: Array, default: () => [] }
})

const formatDate = (dateStr) => {
  if (!dateStr) return ''
  const d = new Date(dateStr)
  return d.toLocaleDateString() + ' ' + d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })
}

const getLogMarkerClass = (status) => {
  const s = (status || '').toLowerCase()
  if (s === 'completed' || s === 'approve') return 'marker-green'
  if (s === 'failed' || s === 'reject' || s === 'error') return 'marker-red'
  if (s === 'pending_approval' || s === 'return' || s === 'started' || s === 'pending') return 'marker-amber'
  return 'marker-gray'
}
</script>

<style scoped>
.timeline {
  display: flex;
  flex-direction: column;
  gap: 0;
  position: relative;
  margin-top: 10px;
}
.timeline::before {
  content: '';
  position: absolute;
  top: 0;
  bottom: 0;
  left: 11px;
  width: 2px;
  background: var(--border-color);
}
.timeline-item {
  display: flex;
  gap: 16px;
  padding-bottom: 24px;
  position: relative;
}
.timeline-item:last-child {
  padding-bottom: 0;
}
.timeline-marker {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: var(--border-color);
  border: 4px solid var(--bg-page);
  z-index: 10;
}
.marker-green { background: var(--accent-green); }
.marker-red { background: var(--accent-red); }
.marker-amber { background: var(--accent-amber); }
.marker-gray { background: var(--text-muted); }

.timeline-content {
  flex: 1;
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  padding: 14px 16px;
  border-radius: 12px;
  margin-top: -6px;
}
.bg-gray-light { background: #f8fafc; }
.bg-red-light { background: var(--accent-red-light); }
.rounded { border-radius: 6px; }
.text-red { color: var(--accent-red); }
.code-font { font-family: monospace; }
</style>
