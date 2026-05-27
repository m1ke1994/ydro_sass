import { ref } from 'vue'
import { defineStore } from 'pinia'

import { getLeadRequest, getLeadsRequest, patchLeadStatusRequest } from '../api/leads'

export const useLeadsStore = defineStore('leads', () => {
  const leads = ref([])
  const currentLead = ref(null)
  const loading = ref(false)

  async function fetchLeads({ siteId, status } = {}) {
    loading.value = true
    try {
      const params = {}
      if (siteId) params.site_id = siteId
      if (status) params.status = status
      const { data } = await getLeadsRequest(params)
      leads.value = Array.isArray(data) ? data : []
      return leads.value
    } finally {
      loading.value = false
    }
  }

  async function fetchLead(leadId) {
    const { data } = await getLeadRequest(leadId)
    currentLead.value = data
    return data
  }

  async function patchLeadStatus(leadId, status) {
    const { data } = await patchLeadStatusRequest(leadId, { status })
    const index = leads.value.findIndex((item) => item.id === data.id)
    if (index >= 0) {
      leads.value[index] = { ...leads.value[index], ...data }
    }
    if (currentLead.value?.id === data.id) {
      currentLead.value = { ...currentLead.value, ...data }
    }
    return data
  }

  function reset() {
    leads.value = []
    currentLead.value = null
  }

  return {
    leads,
    currentLead,
    loading,
    fetchLeads,
    fetchLead,
    patchLeadStatus,
    reset,
  }
})
