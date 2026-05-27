import http from './http'

export async function uploadMediaFile({ file, site, section, field }) {
  const formData = new FormData()
  formData.append('file', file)
  if (site !== undefined && site !== null && site !== '') {
    formData.append('site', String(site))
  }
  if (section !== undefined && section !== null && section !== '') {
    formData.append('section', String(section))
  }
  if (field !== undefined && field !== null && field !== '') {
    formData.append('field', String(field))
  }

  const { data } = await http.post('/api/uploads/', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  })
  return data
}
