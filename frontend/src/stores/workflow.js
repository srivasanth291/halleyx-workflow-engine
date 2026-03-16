import { defineStore } from 'pinia'
import { ref } from 'vue'
import workflowService from '@/services/workflow.service'

export const useWorkflowStore = defineStore('workflow', () => {
  const workflows = ref([])
  const currentWorkflow = ref(null)
  const totalCount = ref(0)
  const loading = ref(false)

  async function fetchWorkflows(params = {}) {
    loading.value = true
    try {
      const res = await workflowService.getAll(params)
      workflows.value = res.data.results || res.data
      totalCount.value = res.data.count || 0
      return res.data
    } finally { loading.value = false }
  }

  async function fetchWorkflow(id) {
    loading.value = true
    try {
      const res = await workflowService.getOne(id)
      currentWorkflow.value = res.data
      return res.data
    } finally { loading.value = false }
  }

  async function createWorkflow(data) {
    const res = await workflowService.create(data)
    return res.data
  }

  async function updateWorkflow(id, data) {
    const res = await workflowService.update(id, data)
    currentWorkflow.value = res.data
    return res.data
  }

  async function deleteWorkflow(id) {
    await workflowService.delete(id)
    await fetchWorkflows()
  }

  async function fetchVersions(id) {
    const res = await workflowService.getVersions(id)
    return res.data
  }

  async function rollback(id, targetVersion) {
    const res = await workflowService.rollback(id, { target_version: targetVersion })
    return res.data
  }

  return { workflows, currentWorkflow, totalCount, loading, fetchWorkflows, fetchWorkflow, createWorkflow, updateWorkflow, deleteWorkflow, fetchVersions, rollback }
})
