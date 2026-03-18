import api from './api'

class SettingsService {
  getEmail() { return api.get('/settings/email/') }
  saveEmail(data) { return api.put('/settings/email/', data) }
  getCompany() { return api.get('/settings/company/') }
  saveCompany(data) { return api.put('/settings/company/', data) }
  getNotifSettings() { return api.get('/settings/notifications/') }
  saveNotifSettings(data) { return api.put('/settings/notifications/', data) }
}
export default new SettingsService()
