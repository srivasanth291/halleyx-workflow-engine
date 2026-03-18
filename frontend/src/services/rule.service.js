import api from './api'

class RuleService {
  getAll(stepId) { return api.get(`/rules/`, { params: { step: stepId } }) }
  getOne(id) { return api.get(`/rules/${id}/`) }
  create(data) { return api.post('/rules/', data) }
  update(id, data) { return api.put(`/rules/${id}/`, data) }
  delete(id) { return api.delete(`/rules/${id}/`) }
  validate(data) { return api.post('/rules/validate_syntax/', data) }
  reorder(data) { return api.post('/rules/reorder/', data) }
}
export default new RuleService()
