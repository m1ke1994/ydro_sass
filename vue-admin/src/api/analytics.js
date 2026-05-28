import http from './http'

export const getSiteAnalyticsSummaryRequest = (siteId, params = {}) =>
  http.get(`/api/admin/my-sites/${siteId}/analytics/summary/`, { params })
