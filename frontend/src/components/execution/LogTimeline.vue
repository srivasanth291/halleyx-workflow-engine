<template>
  <div class="timeline" v-if="logs && logs.length">
    <div v-for="(log, i) in logs" :key="i" class="timeline-item">
      <div class="timeline-dot" :style="{ color: dotColor(log) }"></div>
      <div class="timeline-time">{{ formatTime(log.action_at || log.started_at || log.retried_at || log.canceled_at) }}</div>
      <div class="timeline-msg">{{ logMessage(log) }}</div>
      <div v-if="log.rule_matched" class="timeline-rule">
        Rule: {{ log.rule_matched }}
        <span v-if="log.next_step_name"> → {{ log.next_step_name }}</span>
      </div>
      <div
        v-if="log.error"
        class="timeline-rule"
        style="background:var(--error-bg);border-color:#FECACA;color:var(--error-text)"
      >
        Error: {{ log.error }}
      </div>
    </div>
  </div>
  <div v-else class="empty-state" style="padding:30px">
    <p>No logs yet.</p>
  </div>
</template>

<script setup>
defineProps({ logs: Array })

function dotColor(log) {
  const s = log.status || ''
  if (['completed', 'approve'].includes(s)) return '#16A34A'
  if (['failed', 'reject'].includes(s))     return '#DC2626'
  if (['pending_approval', 'in_progress'].includes(s)) return '#2563EB'
  if (log.action === 'canceled') return '#64748B'
  if (log.action === 'retry')    return '#D97706'
  return '#CBD5E1'
}

function logMessage(log) {
  if (log.action === 'canceled') return `Execution canceled by ${log.canceled_by}`
  if (log.action === 'retry')    return `Retry #${log.retry_number} of step: ${log.retried_step} by ${log.retried_by}`
  if (log.step_name) {
    if (log.status === 'completed' || log.status === 'approve')
      return `${log.step_name} — Completed${log.action_by ? ' by ' + log.action_by : ''}`
    if (log.status === 'reject')
      return `${log.step_name} — Rejected by ${log.action_by}${log.comment ? ': ' + log.comment : ''}`
    if (log.status === 'return')
      return `${log.step_name} — Returned by ${log.action_by}${log.comment ? ': ' + log.comment : ''}`
    if (log.status === 'pending_approval')
      return `${log.step_name} — Waiting for approval from ${log.comment?.replace('Waiting for approval from ', '') || '...'}`
    if (log.status === 'started')  return `${log.step_name} — Started`
    if (log.status === 'failed')   return `${log.step_name} — Failed`
  }
  if (log.error) return `Error: ${log.error}`
  return JSON.stringify(log).slice(0, 80)
}

function formatTime(ts) {
  if (!ts) return ''
  try {
    return new Date(ts).toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', second: '2-digit' })
  } catch { return ts }
}
</script>
