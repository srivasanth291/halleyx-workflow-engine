import api from './api'
export default {
  getAll:  wId      => api.get(`/workflows/${wId}/steps/`),
  create:  (wId, d) => api.post(`/workflows/${wId}/steps/`, d),
  update:  (id, d)  => api.put(`/steps/${id}/`, d),
  delete:  id       => api.delete(`/steps/${id}/`),
  reorder: d        => api.post('/steps/reorder/', d),
}
