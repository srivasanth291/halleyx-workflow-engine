<template>
  <div>
    <div class="page-header">
      <div>
        <h1 class="page-title">Audit Log</h1>
        <p class="page-subtitle">Track all workflow executions for compliance</p>
      </div>
    </div>

    <!-- Stats Cards -->
    <div class="stats-grid" v-if="execStore.auditStats">
      <div class="stat-card">
        <div class="stat-label">Total Executions</div>
        <div class="stat-value" style="color:var(--text-primary)">{{ execStore.auditStats.total || 0 }}</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">Completed</div>
        <div class="stat-value" style="color:var(--success-text)">{{ execStore.auditStats.completed || 0 }}</div>
        <div class="stat-sub" v-if="execStore.auditStats.total">
          {{ Math.round((execStore.auditStats.completed / execStore.auditStats.total) * 100) }}% success
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-label">Failed</div>
        <div class="stat-value" style="color:var(--error-text)">{{ execStore.auditStats.failed || 0 }}</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">Pending / Active</div>
        <div class="stat-value" style="color:var(--warning-text)">
          {{ (execStore.auditStats.pending || 0) + (execStore.auditStats.in_progress || 0) }}
        </div>
      </div>
    </div>

    <!-- Filters -->
    <div class="filter-bar">
      <input v-model="filters.date_from" type="date" class="form-input" style="width:150px" />
      <input v-model="filters.date_to" type="date" class="form-input" style="width:150px" />
      <select v-model="filters.status" class="form-input form-select" style="width:160px">
        <option value="">All Status</option>
        <option value="completed">Completed</option>
        <option value="failed">Failed</option>
        <option value="pending">Pending</option>
        <option value="in_progress">In Progress</option>
        <option value="canceled">Canceled</option>
      </select>
      <input v-model="filters.search" class="form-input flex-grow" placeholder="Search execution ID..." />
      <button class="btn btn-primary btn-sm" @click="loadAudit">Apply</button>
      <button class="btn btn-ghost btn-sm" @click="resetFilters">Reset</button>
    </div>

    <!-- Table -->
    <div class="table-card">
      <div class="table-wrap">
        <table>
          <thead>
            <tr>
              <th>EXEC ID</th><th>WORKFLOW</th><th>VERSION</th>
              <th>STATUS</th><th>STARTED BY</th>
              <th>START TIME</th><th>END TIME</th>
              <th>DURATION</th><th>ACTIONS</th>
            </tr>
          </thead>
          <tbody>
            <template v-if="execStore.loading">
              <tr v-for="i in 5" :key="i">
                <td v-for="j in 9" :key="j"><div class="skeleton skel-text"></div></td>
              </tr>
            </template>
            <template v-else-if="execStore.executions.length">
              <tr
                v-for="ex in execStore.executions"
                :key="ex.id"
                :class="ex.status === 'completed' ? 'row-success' : ex.status === 'failed' ? 'row-error' : ''"
              >
                <td><span class="mono" :title="ex.id">{{ ex.id?.slice(0, 8) }}...</span></td>
                <td><span style="font-weight:600">{{ ex.workflow_name || '—' }}</span></td>
                <td><span class="badge badge-indigo">v{{ ex.workflow_version }}</span></td>
                <td><StatusBadge :status="ex.status" /></td>
                <td class="text-sm text-secondary">{{ ex.triggered_by_email || '—' }}</td>
                <td class="text-sm text-secondary">{{ fmtDT(ex.started_at) }}</td>
                <td class="text-sm text-secondary">{{ fmtDT(ex.ended_at) }}</td>
                <td class="text-sm text-secondary">{{ calcDuration(ex.started_at, ex.ended_at) }}</td>
                <td>
                  <div class="flex gap-2">
                    <button
                      class="btn btn-ghost btn-sm"
                      style="color:var(--accent-indigo);border-color:var(--accent-indigo)"
                      @click="openDrawer(ex)"
                    >View Logs</button>
                    <button v-if="ex.status === 'failed'" class="btn btn-amber btn-sm" @click="handleRetry(ex)">🔄 Retry</button>
                  </div>
                </td>
              </tr>
            </template>
            <tr v-else>
              <td colspan="9">
                <div class="empty-state">
                  <h3>No executions found</h3>
                  <p>Execute a workflow to see logs here</p>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Pagination -->
      <div class="pagination" v-if="totalCount > 0">
        <span class="pagination-info">
          Showing {{ execStore.executions.length }} of {{ totalCount }} executions
        </span>
        <div class="pagination-btns">
          <button class="pag-btn" :disabled="page === 1" @click="page--; loadAudit()">←</button>
          <button
            v-for="p in Math.min(5, Math.ceil(totalCount / 10))"
            :key="p"
            :class="['pag-btn', page === p ? 'active' : '']"
            @click="page = p; loadAudit()"
          >{{ p }}</button>
          <button class="pag-btn" :disabled="page >= Math.ceil(totalCount / 10)" @click="page++; loadAudit()">→</button>
        </div>
      </div>
    </div>

    <!-- Side Drawer -->
    <div v-if="showDrawer">
      <div class="drawer-backdrop" @click="showDrawer = false"></div>
      <transition name="slide">
        <div class="drawer">
          <div class="drawer-header">
            <div class="flex items-center justify-between">
              <div>
                <h3 style="font-size:16px;font-weight:700">Execution Logs</h3>
                <p class="mono text-sm text-muted">
                  {{ selectedExec?.id?.slice(0, 12) }}... — {{ selectedExec?.workflow_name }} v{{ selectedExec?.workflow_version }}
                </p>
              </div>
              <button class="btn-icon" @click="showDrawer = false">✕</button>
            </div>
            <div class="flex gap-3" style="margin-top:10px">
              <StatusBadge :status="selectedExec?.status" />
              <span class="text-sm text-secondary">{{ calcDuration(selectedExec?.started_at, selectedExec?.ended_at) }}</span>
              <span class="text-sm text-secondary">by {{ selectedExec?.triggered_by_email }}</span>
            </div>
          </div>
          <div class="drawer-body">
            <LogTimeline :logs="drawerLogs" />
          </div>
          <div class="drawer-footer">
            <button
              v-if="selectedExec?.status === 'failed'"
              class="btn btn-amber flex-1"
              @click="handleRetry(selectedExec); showDrawer = false"
            >🔄 Retry Failed Step</button>
            <button class="btn btn-ghost flex-1" @click="showDrawer = false">Close</button>
          </div>
        </div>
      </transition>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useExecutionStore } from '@/stores/execution'
import { useNotificationStore } from '@/stores/notification'
import StatusBadge from '@/components/common/StatusBadge.vue'
import LogTimeline from '@/components/execution/LogTimeline.vue'
import executionService from '@/services/execution.service'

const execStore = useExecutionStore()
const notif = useNotificationStore()

const page = ref(1)
const totalCount = ref(0)
const filters = reactive({ date_from: '', date_to: '', status: '', search: '' })
const showDrawer = ref(false)
const selectedExec = ref(null)
const drawerLogs = ref([])

async function loadAudit() {
  const params = { page: page.value }
  if (filters.status)    params.status    = filters.status
  if (filters.search)    params.search    = filters.search
  if (filters.date_from) params.date_from = filters.date_from
  if (filters.date_to)   params.date_to   = filters.date_to
  const res = await execStore.fetchAuditLog(params)
  totalCount.value = res.count || 0
}

function resetFilters() {
  Object.assign(filters, { date_from: '', date_to: '', status: '', search: '' })
  page.value = 1
  loadAudit()
}

async function openDrawer(ex) {
  selectedExec.value = ex
  showDrawer.value = true
  drawerLogs.value = []
  try {
    const res = await executionService.getOne(ex.id)
    drawerLogs.value = res.data.logs || []
  } catch { drawerLogs.value = [] }
}

async function handleRetry(ex) {
  try {
    await execStore.retryExecution(ex.id)
    notif.success('Retrying execution!')
    await loadAudit()
  } catch (e) {
    notif.error(e.response?.data?.detail || 'Retry failed')
  }
}

function fmtDT(d) {
  if (!d) return '—'
  return new Date(d).toLocaleString('en-US', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })
}

function calcDuration(start, end) {
  if (!start || !end) return '—'
  const secs = Math.floor((new Date(end) - new Date(start)) / 1000)
  if (secs < 60)   return `${secs}s`
  if (secs < 3600) return `${Math.floor(secs / 60)}m ${secs % 60}s`
  return `${Math.floor(secs / 3600)}h ${Math.floor((secs % 3600) / 60)}m`
}

onMounted(loadAudit)
</script>
