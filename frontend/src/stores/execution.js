import { defineStore } from 'pinia'
import executionService from '@/services/execution.service'
import workflowService from '@/services/workflow.service'
import { useNotificationStore } from '@/stores/notification'

export const useExecutionStore = defineStore('execution', {
  state: () => ({
    executions: [],
    currentExecution: null,
    auditStats: { total: 0, completed: 0, failed: 0, pending: 0, in_progress: 0, canceled: 0 },
    loading: false
  }),
  actions: {
    async executeWorkflow(wfId, data, maxIter) {
      this.loading = true
      try {
        const res = await workflowService.execute(wfId, data, maxIter)
        const ns = useNotificationStore()
        ns.success('Workflow execution started!')
        return res.data
      } finally {
        this.loading = false
      }
    },
    async fetchExecutions(params) {
      this.loading = true
      try {
        const res = await executionService.getAll(params)
        this.executions = res.data.results || res.data
      } finally {
        this.loading = false
      }
    },
    async fetchExecution(id) {
      const res = await executionService.getOne(id)
      this.currentExecution = res.data
      return res.data
    },
    async approveStep(id, comment) {
      const res = await executionService.approve(id, comment)
      this.currentExecution = res.data
      useNotificationStore().success('Step approved')
      return res.data
    },
    async rejectStep(id, comment) {
      const res = await executionService.reject(id, comment)
      this.currentExecution = res.data
      useNotificationStore().success('Step rejected')
      return res.data
    },
    async returnStep(id, comment) {
      const res = await executionService.returnStep(id, comment)
      this.currentExecution = res.data
      useNotificationStore().success('Step returned')
      return res.data
    },
    async retryExecution(id) {
      const res = await executionService.retry(id)
      this.currentExecution = res.data
      useNotificationStore().success('Execution retried')
      return res.data
    },
    async cancelExecution(id) {
      const res = await executionService.cancel(id)
      this.currentExecution = res.data
      useNotificationStore().warning('Execution canceled')
      return res.data
    },
    async fetchAuditLog(params) {
      this.loading = true
      try {
        const res = await executionService.getAuditLog(params)
        this.executions = res.data.results || res.data || []
        this.auditStats = res.data.stats || { total: 0, completed: 0, failed: 0, pending: 0, in_progress: 0, canceled: 0 }
        return res.data
      } finally {
        this.loading = false
      }
    }
  }
})
