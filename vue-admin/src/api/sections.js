import http from './http'

export const getSectionsRequest = () => http.get('/api/client/sections/')
export const getSectionFormRequest = (slug) => http.get(`/api/client/sections/${slug}/form/`)
export const patchSectionRequest = (slug, payload) => http.patch(`/api/client/sections/${slug}/`, payload)
