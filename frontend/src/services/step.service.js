import api from './api'

class StepService {
  getAll(workflowId) { return api.get(`/steps/`, { params: { workflow_id: workflowId }}) }
  getOne(id) { return api.get(`/steps/${id}/`) }
  create(data) { return api.post('/steps/', data) }
  update(id, data) { return api.put(`/steps/${id}/`, data) }
  delete(id) { return api.delete(`/steps/${id}/`) }
  reorder(data) { return api.post('/steps/reorder/', data) }
}
export default new StepService()
