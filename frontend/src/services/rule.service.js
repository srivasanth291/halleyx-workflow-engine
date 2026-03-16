import api from './api'
export default {
  getAll:   sId      => api.get(`/steps/${sId}/rules/`),
  create:   (sId, d) => api.post(`/steps/${sId}/rules/`, d),
  update:   (id, d)  => api.put(`/rules/${id}/`, d),
  delete:   id       => api.delete(`/rules/${id}/`),
  validate: d        => api.post('/rules/validate/', d),
  reorder:  (sId, d) => api.post(`/steps/${sId}/rules/reorder/`, d),
}
