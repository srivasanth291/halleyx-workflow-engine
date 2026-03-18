<template>
  <span :class="['badge', badgeClass]">
    {{ label || styledStatus }}
  </span>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  status: String,
  label: String
})

const styledStatus = computed(() => {
  if (!props.status) return ''
  return props.status.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())
})

const badgeClass = computed(() => {
  const s = (props.status || '').toLowerCase()
  if (['completed', 'sent', 'active', 'approve'].includes(s)) return 'badge-green'
  if (['failed', 'error', 'rejected', 'reject'].includes(s)) return 'badge-red'
  if (['pending', 'in_progress', 'pending_approval', 'escalated'].includes(s)) return 'badge-amber'
  if (['canceled', 'inactive', 'return'].includes(s)) return 'badge-gray'
  if (s === 'email') return 'badge-blue'
  if (s === 'slack') return 'badge-purple'
  if (s === 'ui_message' || s === 'task') return 'badge-gray'
  if (s === 'approval') return 'badge-amber'
  if (s === 'notification') return 'badge-blue'
  return 'badge-gray'
})
</script>
