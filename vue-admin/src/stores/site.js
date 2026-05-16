import { ref } from 'vue'
import { defineStore } from 'pinia'

import { getClientSiteRequest } from '../api/site'

export const useSiteStore = defineStore('site', () => {
  const site = ref(null)
  const loading = ref(false)

  async function fetchSite() {
    loading.value = true
    try {
      const { data } = await getClientSiteRequest()
      site.value = data
      return data
    } finally {
      loading.value = false
    }
  }

  return {
    site,
    loading,
    fetchSite,
  }
})
