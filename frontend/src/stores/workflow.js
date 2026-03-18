import { defineStore } from 'pinia'
import workflowService from '@/services/workflow.service'
import { useNotificationStore } from '@/stores/notification'

export const useWorkflowStore = defineStore('workflow', {
  state: () => ({
    workflows: [],
    currentWorkflow: null,
    totalCount: 0,
    loading: false
  }),
  actions: {
    async fetchWorkflows(params) {
      this.loading = true
      try {
        const res = await workflowService.getAll(params)
        if (res.data.results) {
            this.workflows = res.data.results
            this.totalCount = res.data.count
        } else {
            this.workflows = res.data
        }
      } finally {
        this.loading = false
      }
    },
    async fetchWorkflow(id) {
      this.loading = true
      try {
        const res = await workflowService.getOne(id)
        this.currentWorkflow = res.data
        return res.data
      } finally {
        this.loading = false
      }
    },
    async createWorkflow(data) {
      this.loading = true
      try {
        const res = await workflowService.create(data)
        const ns = useNotificationStore()
        ns.success('Workflow created!')
        return res.data
      } finally {
        this.loading = false
      }
    },
    async updateWorkflow(id, data) {
      this.loading = true
      try {
        const res = await workflowService.update(id, data)
        const ns = useNotificationStore()
        ns.success(`New version v${res.data.version} created!`)
        this.currentWorkflow = res.data
        return res.data
      } finally {
        this.loading = false
      }
    },
    async deleteWorkflow(id) {
      await workflowService.delete(id)
      const ns = useNotificationStore()
      ns.success('Workflow disabled.')
    },
    async fetchVersions(id) {
      const res = await workflowService.getVersions(id)
      return res.data
    },
    async rollback(id, targetVersion) {
      this.loading = true
      try {
        const res = await workflowService.rollback(id, targetVersion)
        const ns = useNotificationStore()
        ns.success(`Rolled back to v${targetVersion}!`)
        return res.data
      } finally {
        this.loading = false
      }
    }
  }
})
