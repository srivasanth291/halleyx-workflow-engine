import api from './api'
export default {
  execute:     (wId, d) => api.post(`/workflows/${wId}/execute/`, d),
  getOne:      id       => api.get(`/executions/${id}/`),
  getAll:      p        => api.get('/executions/', { params: p }),
  approve:     (id, d)  => api.post(`/executions/${id}/approve/`, d),
  reject:      (id, d)  => api.post(`/executions/${id}/reject/`, d),
  returnStep:  (id, d)  => api.post(`/executions/${id}/return/`, d),
  cancel:      id       => api.post(`/executions/${id}/cancel/`),
  retry:       id       => api.post(`/executions/${id}/retry/`),
  getAuditLog: p        => api.get('/audit/', { params: p }),
}
