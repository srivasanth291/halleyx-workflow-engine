import api from './api'

class WorkflowService {
  getAll(params) { return api.get('/workflows/', { params }) }
  getOne(id) { return api.get(`/workflows/${id}/`) }
  create(data) { return api.post('/workflows/', data) }
  update(id, data) { return api.put(`/workflows/${id}/`, data) }
  delete(id) { return api.delete(`/workflows/${id}/`) }
  getVersions(id) { return api.get(`/workflows/${id}/versions/`) }
  rollback(id, targetVersion) { return api.post(`/workflows/${id}/rollback/`, { target_version: targetVersion }) }
  execute(id, data, maxIterations) { return api.post(`/workflows/${id}/execute/`, { data, max_iterations: maxIterations }) }
}
export default new WorkflowService()
