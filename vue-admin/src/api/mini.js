import http from './http'

export async function miniOverview(params = {}) {
  const { data } = await http.get('/api/mini/analytics/overview/', { params })
  return data
}

export async function miniSummary(params = {}) {
  const { data } = await http.get('/api/mini/analytics/summary/', { params })
  return data
}

export async function miniDevices(params = {}) {
  const { data } = await http.get('/api/mini/analytics/devices/', { params })
  return data
}

export async function miniEngagement(params = {}) {
  const { data } = await http.get('/api/mini/analytics/engagement/', { params })
  return data
}

export async function miniUnique(params = {}) {
  const { data } = await http.get('/api/mini/analytics/unique-daily/', { params })
  return data
}

export async function miniAiRecommendations(params = {}) {
  const { data } = await http.get('/api/mini/analytics/ai-recommendations/', { params })
  return data
}

export async function miniLeads(params = {}) {
  const { data } = await http.get('/api/mini/leads/', { params })
  return data
}

export async function miniLeadStatus(leadId, status) {
  const { data } = await http.patch(`/api/mini/leads/${leadId}/status/`, { status })
  return data
}

export async function miniSettings() {
  const { data } = await http.get('/api/mini/client/settings/')
  return data
}

export async function miniSaveSettings(payload) {
  const { data } = await http.patch('/api/mini/client/settings/', payload)
  return data
}

export async function miniTelegramStatus() {
  const { data } = await http.get('/api/mini/client/telegram/')
  return data
}

export async function miniTelegramSendTest() {
  const { data } = await http.post('/api/mini/client/telegram/test/', {})
  return data
}

export async function miniTelegramDisconnect() {
  const { data } = await http.post('/api/mini/client/telegram/disconnect/', {})
  return data
}

export async function miniReportDaily() {
  const { data } = await http.get('/api/mini/reports/toggle-daily/')
  return data
}

export async function miniSetReportDaily(enabled) {
  const { data } = await http.post('/api/mini/reports/toggle-daily/', { enabled })
  return data
}

export async function miniReportSendNow() {
  const { data } = await http.post('/api/mini/reports/send-now/', {})
  return data
}

export async function miniSubscriptionStatus() {
  const { data } = await http.get('/api/mini/subscription/status/')
  return data
}

export async function miniSubscriptionPlans() {
  const { data } = await http.get('/api/mini/subscription/plans/')
  return data
}

export async function miniSubscriptionCreatePayment(planId) {
  const { data } = await http.post('/api/mini/subscription/create-payment/', { plan_id: planId })
  return data
}

export async function miniSeoStart(domain) {
  const { data } = await http.post('/api/mini/seo/start/', { domain })
  return data
}

export async function miniSeoLatest(domain) {
  const { data } = await http.get('/api/mini/seo/latest/', { params: { domain } })
  return data
}

export async function miniSeoAudits(params = {}) {
  const { data } = await http.get('/api/mini/seo/audits/', { params })
  return data
}

export async function miniSeoDetail(auditId) {
  const { data } = await http.get(`/api/mini/seo/${auditId}/`)
  return data
}

export async function miniSeoPages(auditId) {
  const { data } = await http.get(`/api/mini/seo/${auditId}/pages/`)
  return data
}

export async function miniSeoIssues(auditId, params = {}) {
  const { data } = await http.get(`/api/mini/seo/${auditId}/issues/`, { params })
  return data
}

export async function miniSeoHistory(auditId) {
  const { data } = await http.get(`/api/mini/seo/${auditId}/history/`)
  return data
}

export async function miniSeoRecommendations(auditId) {
  const { data } = await http.get(`/api/mini/seo/${auditId}/ai-recommendations/`)
  return data
}

export async function miniSeoExport(auditId) {
  const response = await http.get(`/api/mini/seo/${auditId}/export/`, { responseType: 'blob' })
  return response.data
}
