import { defineStore } from 'pinia'
import { ref } from 'vue'
import executionService from '@/services/execution.service'

export const useExecutionStore = defineStore('execution', () => {
  const executions = ref([])
  const currentExecution = ref(null)
  const auditStats = ref(null)
  const loading = ref(false)

  async function executeWorkflow(workflowId, data, maxIterations = 10) {
    loading.value = true
    try {
      const res = await executionService.execute(workflowId, { data, max_iterations: maxIterations })
      currentExecution.value = res.data
      return res.data
    } finally { loading.value = false }
  }

  async function fetchExecution(id) {
    const res = await executionService.getOne(id)
    currentExecution.value = res.data
    return res.data
  }

  async function fetchExecutions(params = {}) {
    loading.value = true
    try {
      const res = await executionService.getAll(params)
      executions.value = res.data.results || []
      return res.data
    } finally { loading.value = false }
  }

  async function approveStep(id, comment = '') {
    const r = await executionService.approve(id, { action: 'approve', comment })
    currentExecution.value = r.data
    return r.data
  }

  async function rejectStep(id, comment = '') {
    const r = await executionService.reject(id, { action: 'reject', comment })
    currentExecution.value = r.data
    return r.data
  }

  async function returnStep(id, comment = '') {
    const r = await executionService.returnStep(id, { action: 'return', comment })
    currentExecution.value = r.data
    return r.data
  }

  async function cancelExecution(id) {
    const r = await executionService.cancel(id)
    currentExecution.value = r.data
    return r.data
  }

  async function retryExecution(id) {
    const r = await executionService.retry(id)
    currentExecution.value = r.data
    return r.data
  }

  async function fetchAuditLog(params = {}) {
    loading.value = true
    try {
      const res = await executionService.getAuditLog(params)
      executions.value = res.data.results || []
      auditStats.value = res.data.stats || null
      return res.data
    } finally { loading.value = false }
  }

  return {
    executions,
    currentExecution,
    auditStats,
    loading,
    executeWorkflow,
    fetchExecution,
    fetchExecutions,
    approveStep,
    rejectStep,
    returnStep,
    cancelExecution,
    retryExecution,
    fetchAuditLog,
  }
})
