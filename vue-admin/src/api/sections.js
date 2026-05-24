import http from './http'

export const getSectionsRequest = (siteId) => http.get(`/api/admin/my-sites/${siteId}/sections/`)
export const getSectionRequest = (siteId, sectionId) => http.get(`/api/admin/my-sites/${siteId}/sections/${sectionId}/`)
export const patchSectionRequest = (siteId, sectionId, payload) => http.patch(`/api/admin/my-sites/${siteId}/sections/${sectionId}/`, payload)
export const createSectionRequest = (siteId, payload) => http.post(`/api/admin/my-sites/${siteId}/sections/`, payload)
export const deleteSectionRequest = (siteId, sectionId) => http.delete(`/api/admin/my-sites/${siteId}/sections/${sectionId}/`)
