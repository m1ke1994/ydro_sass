import http from './http'

export const getClientSiteRequest = () => http.get('/api/client/site/')
