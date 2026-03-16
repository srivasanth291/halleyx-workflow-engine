import api from './api'
export default {
  getAll:      p  => api.get('/workflows/', { params: p }),
  getOne:      id => api.get(`/workflows/${id}/`),
  create:      d  => api.post('/workflows/', d),
  update:      (id, d) => api.put(`/workflows/${id}/`, d),
  delete:      id => api.delete(`/workflows/${id}/`),
  getVersions: id => api.get(`/workflows/${id}/versions/`),
  rollback:    (id, d) => api.post(`/workflows/${id}/rollback/`, d),
}
