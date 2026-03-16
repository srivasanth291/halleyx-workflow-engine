import api from './api'
export default {
  register:      d  => api.post('/auth/register/', d),
  login:         d  => api.post('/auth/login/', d),
  logout:        d  => api.post('/auth/logout/', d),
  getProfile:    () => api.get('/auth/me/'),
  updateProfile: d  => api.put('/auth/me/', d),
  refreshToken:  d  => api.post('/auth/token/refresh/', d),
  createUser:    d  => api.post('/auth/users/', d),
  getUsers:      p  => api.get('/auth/users/', { params: p }),
}
