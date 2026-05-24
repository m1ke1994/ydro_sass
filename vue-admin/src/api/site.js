import http from './http'

export const getMySitesRequest = () => http.get('/api/admin/my-sites/')
export const getMySiteRequest = (siteId) => http.get(`/api/admin/my-sites/${siteId}/`)
