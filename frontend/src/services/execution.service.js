import api from './api'

class ExecutionService {
  getAll(params) { return api.get('/executions/', { params }) }
  getOne(id) { return api.get(`/executions/${id}/`) }
  approve(id, comment) { return api.post(`/executions/${id}/approve/`, { comment }) }
  reject(id, comment) { return api.post(`/executions/${id}/reject/`, { comment }) }
  returnStep(id, comment) { return api.post(`/executions/${id}/return_step/`, { comment }) }
  cancel(id) { return api.post(`/executions/${id}/cancel/`) }
  retry(id) { return api.post(`/executions/${id}/retry/`) }
  getPendingTasks() { return api.get('/executions/pending-tasks/') }
  getAuditLog(params) { return api.get('/audit/', { params }) }
}
export default new ExecutionService()
