<template>
  <div class="audit-page">
    <div class="flex items-center justify-between mb-6">
      <div>
        <h1 class="text-bold m-0" style="font-size: 24px;">Audit Log</h1>
        <p class="text-gray m-0 mt-1">Track all workflow executions and system activity</p>
      </div>
    </div>

    <!-- Stats Summary -->
    <!-- Stats Summary -->
    <div v-if="stats" class="grid grid-cols-4 gap-6 mb-8">
       <div class="card glass p-6 shadow-hover text-center">
         <div class="text-xs text-muted uppercase text-bold mb-2 letter-spacing-1">Activity Stream</div>
         <div class="text-bold text-3xl letter-spacing-tight">{{ stats.total }}</div>
         <div class="text-xs text-gray mt-1">Total Executions</div>
       </div>
       <div class="card glass p-6 shadow-hover text-center border-b-amber">
         <div class="text-xs text-muted uppercase text-bold mb-2 letter-spacing-1">Live Cycles</div>
         <div class="text-bold text-3xl text-amber letter-spacing-tight">{{ stats.in_progress + stats.pending }}</div>
         <div class="text-xs text-gray mt-1">Active Now</div>
       </div>
       <div class="card glass p-6 shadow-hover text-center border-b-green">
         <div class="text-xs text-muted uppercase text-bold mb-2 letter-spacing-1">Success Rate</div>
         <div class="text-bold text-3xl text-green letter-spacing-tight">{{ stats.completed }}</div>
         <div class="text-xs text-gray mt-1">Finalized</div>
       </div>
       <div class="card glass p-6 shadow-hover text-center border-b-red">
         <div class="text-xs text-muted uppercase text-bold mb-2 letter-spacing-1">Terminations</div>
         <div class="text-bold text-3xl text-red letter-spacing-tight">{{ stats.failed }}</div>
         <div class="text-xs text-gray mt-1">Failed Runs</div>
       </div>
    </div>

    <div class="card glass p-0 overflow-hidden shadow-hover">
      <div v-if="store.loading" class="p-12 text-center"><span class="spinner">🌀</span> Loading audit logs...</div>
      <div v-else class="table-container">
        <table>
          <thead>
            <tr>
              <th class="uppercase letter-spacing-1 text-xs px-6 py-4">Trace ID</th>
              <th class="uppercase letter-spacing-1 text-xs px-6 py-4">Workflow Engine</th>
              <th class="uppercase letter-spacing-1 text-xs px-6 py-4">Current state</th>
              <th class="uppercase letter-spacing-1 text-xs px-6 py-4">Originator</th>
              <th class="uppercase letter-spacing-1 text-xs px-6 py-4">Performance</th>
              <th class="uppercase letter-spacing-1 text-xs px-6 py-4">Interaction</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="ex in store.executions" :key="ex.id" class="hover-row">
              <td class="px-6 py-4">
                <span class="code-font text-xs bg-slate-100 p-1 px-2 rounded-md">{{ ex.id.split('-')[0] }}</span>
              </td>
              <td class="px-6 py-4">
                <div class="text-bold text-sm">{{ ex.workflow_name }}</div>
                <div class="text-xs text-muted mono-font mt-0.5">Deployment v{{ ex.workflow_version }}</div>
              </td>
              <td class="px-6 py-4"><StatusBadge :status="ex.status" /></td>
              <td class="px-6 py-4 text-sm font-semibold">{{ ex.triggered_by_email }}</td>
              <td class="px-6 py-4 text-sm text-indigo font-bold">{{ getDuration(ex.started_at, ex.ended_at) }}</td>
              <td class="px-6 py-4">
                <router-link :to="`/workflows/${ex.id}/execute`" class="btn btn-outlined text-xs py-2" style="text-decoration: none;">Deep Trace</router-link>
              </td>
            </tr>
            <tr v-if="store.executions.length === 0">
              <td colspan="6" class="text-center text-gray p-12 italic">No operational records within the current audit window.</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, onUnmounted } from 'vue'
import { useExecutionStore } from '@/stores/execution'
import StatusBadge from '@/components/common/StatusBadge.vue'

const store = useExecutionStore()
const stats = computed(() => store.auditStats)
let refreshInterval = null

const loadData = () => store.fetchAuditLog()

onMounted(() => {
  loadData()
  refreshInterval = setInterval(loadData, 30000)
})

onUnmounted(() => {
  clearInterval(refreshInterval)
})

const getDuration = (start, end) => {
  if (!start) return '—'
  const s = new Date(start)
  const e = end ? new Date(end) : new Date()
  const diffSec = Math.floor((e - s) / 1000)
  
  if (diffSec < 60) return `${diffSec}s`
  const m = Math.floor(diffSec / 60)
  const sec = diffSec % 60
  if (m < 60) return `${m}m ${sec}s`
  const h = Math.floor(m / 60)
  return `${h}h ${m % 60}m`
}
</script>

<style scoped>
.grid { display: grid; }
.grid-cols-4 { grid-template-columns: repeat(4, 1fr); }
.gap-6 { gap: 24px; }

.text-3xl { font-size: 30px; }
.letter-spacing-tight { letter-spacing: -1px; }
.letter-spacing-1 { letter-spacing: 1px; }

.table-container { overflow-x: auto; }
.hover-row:hover { background: rgba(0,0,0,0.01); }

.code-font { font-family: 'JetBrains Mono', monospace; }
.mono-font { font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace; }

.text-green { color: var(--accent-green); }
.text-red { color: var(--accent-red); }
.text-amber { color: var(--accent-amber); }
.text-indigo { color: var(--accent-indigo); }
.text-muted { color: var(--text-muted); }

.border-b-green { border-bottom: 4px solid var(--accent-green); }
.border-b-red { border-bottom: 4px solid var(--accent-red); }
.border-b-amber { border-bottom: 4px solid var(--accent-amber); }

.uppercase { text-transform: uppercase; }
.text-xs { font-size: 11px; }
</style>
