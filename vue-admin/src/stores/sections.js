import { ref } from 'vue'
import { defineStore } from 'pinia'

import { getSectionFormRequest, getSectionsRequest, patchSectionRequest } from '../api/sections'

export const useSectionsStore = defineStore('sections', () => {
  const sections = ref([])
  const currentSectionForm = ref(null)
  const loading = ref(false)

  async function fetchSections() {
    loading.value = true
    try {
      const { data } = await getSectionsRequest()
      sections.value = data
      return data
    } finally {
      loading.value = false
    }
  }

  async function fetchSectionForm(slug) {
    loading.value = true
    try {
      const { data } = await getSectionFormRequest(slug)
      currentSectionForm.value = data
      return data
    } finally {
      loading.value = false
    }
  }

  async function patchSection(slug, payload) {
    const { data } = await patchSectionRequest(slug, payload)
    return data
  }

  return {
    sections,
    currentSectionForm,
    loading,
    fetchSections,
    fetchSectionForm,
    patchSection,
  }
})
