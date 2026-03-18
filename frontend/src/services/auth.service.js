import api from './api'

class AuthService {
  login(data) { return api.post('/auth/login/', data) }
  logout(data) { return api.post('/auth/logout/', data) }
  getProfile() { return api.get('/auth/me/') }
  updateProfile(data) { return api.put('/auth/me/', data) }
  getUsers(params) { return api.get('/auth/users/', { params }) }
  createUser(data) { return api.post('/auth/users/', data) }
  updateUser(id, data) { return api.put(`/auth/users/${id}/`, data) }
  deactivateUser(id) { return api.post(`/auth/users/${id}/deactivate/`) }
  getRoles() { return api.get('/auth/roles/') }
  createRole(data) { return api.post('/auth/roles/', data) }
  updateRole(id, data) { return api.put(`/auth/roles/${id}/`, data) }
  deleteRole(id) { return api.delete(`/auth/roles/${id}/`) }
}

export default new AuthService()
