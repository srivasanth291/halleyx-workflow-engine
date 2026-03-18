import api from './api'

class NotificationService {
  getAll(params) { return api.get('/notifications/', { params }) }
  getStats() { return api.get('/notifications/stats/') }
  sendTestEmail(recipient) { return api.post('/notifications/test-email/', { recipient }) }
}
export default new NotificationService()
