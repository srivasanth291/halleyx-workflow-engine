<template>
  <div>
    <div class="page-header">
      <div>
        <h1 class="page-title">Workflows</h1>
        <p class="page-subtitle">Manage and automate your business processes</p>
      </div>
      <button class="btn btn-primary" @click="router.push('/workflows/new')">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
          <line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/>
        </svg>
        Create Workflow
      </button>
    </div>

    <!-- Filter Bar -->
    <div class="filter-bar">
      <input v-model="search" class="form-input flex-grow" style="max-width:320px" placeholder="Search workflows..." />
      <select v-model="statusFilter" class="form-input form-select" style="width:160px">
        <option value="">All Status</option>
        <option value="true">Active</option>
        <option value="false">Inactive</option>
      </select>
      <button class="btn btn-ghost btn-sm" @click="resetFilters">Reset</button>
    </div>

    <!-- Table -->
    <div class="table-card">
      <div class="table-wrap">
        <table>
          <thead>
            <tr>
              <th>ID</th><th>NAME</th><th>STEPS</th>
              <th>VERSION</th><th>STATUS</th>
              <th>CREATED AT</th><th>ACTIONS</th>
            </tr>
          </thead>
          <tbody>
            <template v-if="wfStore.loading">
              <tr v-for="i in 5" :key="i">
                <td><div class="skeleton skel-text" style="width:80px"></div></td>
                <td><div class="skeleton skel-text" style="width:160px"></div></td>
                <td><div class="skeleton skel-text" style="width:30px"></div></td>
                <td><div class="skeleton skel-text" style="width:40px"></div></td>
                <td><div class="skeleton skel-text" style="width:60px"></div></td>
                <td><div class="skeleton skel-text" style="width:100px"></div></td>
                <td><div class="skeleton skel-text" style="width:80px"></div></td>
              </tr>
            </template>
            <template v-else-if="wfStore.workflows.length">
              <tr v-for="wf in wfStore.workflows" :key="wf.id" :class="wf.is_active ? 'row-success' : ''">
                <td><span class="mono" :title="wf.id">{{ wf.id.slice(0, 8) }}...</span></td>
                <td><span style="font-weight:600">{{ wf.name }}</span></td>
                <td><span class="badge-count">{{ wf.steps_count || 0 }}</span></td>
                <td><span class="badge badge-indigo">v{{ wf.version }}</span></td>
                <td><StatusBadge :status="wf.is_active ? 'active' : 'inactive'" /></td>
                <td class="text-secondary text-sm">{{ fmtDate(wf.created_at) }}</td>
                <td>
                  <div class="flex gap-2">
                    <button class="btn-icon indigo" title="Edit" @click="router.push(`/workflows/${wf.id}/edit`)">
                      <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M11 4H4a2 2 0 00-2 2v14a2 2 0 002 2h14a2 2 0 002-2v-7"/>
                        <path d="M18.5 2.5a2.121 2.121 0 013 3L12 15l-4 1 1-4 9.5-9.5z"/>
                      </svg>
                    </button>
                    <button class="btn-icon" title="Version History" style="color:#D97706" @click="openVersionModal(wf)">
                      <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/>
                      </svg>
                    </button>
                    <button class="btn-icon success" title="Execute" @click="router.push(`/workflows/${wf.id}/execute`)">
                      <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <polygon points="5 3 19 12 5 21 5 3"/>
                      </svg>
                    </button>
                    <button class="btn-icon danger" title="Delete" @click="openDelete(wf)">
                      <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M3 6h18M8 6V4h8v2M19 6l-1 14H6L5 6"/>
                      </svg>
                    </button>
                  </div>
                </td>
              </tr>
            </template>
            <tr v-else>
              <td colspan="7">
                <div class="empty-state">
                  <h3>No workflows found</h3>
                  <p>Create your first workflow to start automating</p>
                  <button class="btn btn-outlined" @click="router.push('/workflows/new')">+ Create Workflow</button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
      <div class="pagination" v-if="wfStore.totalCount > 0">
        <span class="pagination-info">Showing {{ wfStore.workflows.length }} of {{ wfStore.totalCount }} workflows</span>
        <div class="pagination-btns">
          <button class="pag-btn" :disabled="page === 1" @click="page--; fetchData()">←</button>
          <button
            v-for="p in totalPages"
            :key="p"
            :class="['pag-btn', page === p ? 'active' : '']"
            @click="page = p; fetchData()"
          >{{ p }}</button>
          <button class="pag-btn" :disabled="page === totalPages" @click="page++; fetchData()">→</button>
        </div>
      </div>
    </div>

    <!-- Version History Modal -->
    <div v-if="showVersionModal" class="modal-backdrop" @click.self="showVersionModal = false">
      <div class="modal modal-md">
        <div class="modal-header">
          <div>
            <h3>Version History</h3>
            <p class="text-sm text-secondary">{{ selectedWf?.name }}</p>
          </div>
          <button class="btn-icon" @click="showVersionModal = false">✕</button>
        </div>
        <div class="modal-body" style="gap:0;padding:16px 24px">
          <div v-if="loadingVersions" style="text-align:center;padding:20px">Loading...</div>
          <div v-else class="version-timeline">
            <div v-for="v in versions" :key="v.id" class="version-item">
              <div :class="['version-dot', v.is_active ? 'current' : 'locked']"></div>
              <div style="flex:1">
                <div class="flex items-center gap-2">
                  <strong>Version {{ v.version }}</strong>
                  <span v-if="v.is_active" class="badge badge-success" style="font-size:11px">CURRENT</span>
                  <span v-else class="badge badge-gray" style="font-size:11px">🔒 LOCKED</span>
                </div>
                <div class="text-sm text-secondary" style="margin-top:2px">{{ fmtDate(v.created_at) }}</div>
              </div>
              <button v-if="!v.is_active" class="btn btn-ghost btn-sm" @click="doRollback(v.version)">Rollback</button>
            </div>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn btn-ghost" @click="showVersionModal = false">Close</button>
        </div>
      </div>
    </div>

    <!-- Delete Confirm Modal -->
    <ConfirmModal
      v-if="showDeleteModal"
      title="Delete Workflow?"
      :message="`This will deactivate &quot;${selectedWf?.name}&quot;. History is preserved.`"
      confirmText="Delete Workflow"
      type="delete"
      @confirm="confirmDelete"
      @cancel="showDeleteModal = false"
    />
  </div>
</template>

<script setup>
import { ref, watch, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useWorkflowStore } from '@/stores/workflow'
import { useNotificationStore } from '@/stores/notification'
import StatusBadge from '@/components/common/StatusBadge.vue'
import ConfirmModal from '@/components/common/ConfirmModal.vue'

const router = useRouter()
const wfStore = useWorkflowStore()
const notif = useNotificationStore()

const search = ref('')
const statusFilter = ref('')
const page = ref(1)
const showVersionModal = ref(false)
const showDeleteModal = ref(false)
const selectedWf = ref(null)
const versions = ref([])
const loadingVersions = ref(false)
const totalPages = computed(() => Math.max(1, Math.ceil(wfStore.totalCount / 10)))

let searchTimer = null
watch(search, () => {
  clearTimeout(searchTimer)
  searchTimer = setTimeout(fetchData, 300)
})
watch(statusFilter, fetchData)

async function fetchData() {
  await wfStore.fetchWorkflows({
    search: search.value,
    is_active: statusFilter.value || undefined,
    page: page.value,
  })
}

function resetFilters() {
  search.value = ''
  statusFilter.value = ''
  page.value = 1
  fetchData()
}

async function openVersionModal(wf) {
  selectedWf.value = wf
  showVersionModal.value = true
  loadingVersions.value = true
  try {
    versions.value = await wfStore.fetchVersions(wf.id)
  } finally {
    loadingVersions.value = false
  }
}

async function doRollback(targetVersion) {
  try {
    await wfStore.rollback(selectedWf.value.id, targetVersion)
    notif.success(`Rolled back to v${targetVersion}!`)
    showVersionModal.value = false
    await fetchData()
  } catch {
    notif.error('Rollback failed')
  }
}

function openDelete(wf) {
  selectedWf.value = wf
  showDeleteModal.value = true
}

async function confirmDelete() {
  try {
    await wfStore.deleteWorkflow(selectedWf.value.id)
    notif.success('Workflow deleted!')
    showDeleteModal.value = false
  } catch {
    notif.error('Delete failed')
  }
}

function fmtDate(d) {
  if (!d) return ''
  return new Date(d).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
}

onMounted(fetchData)
</script>
