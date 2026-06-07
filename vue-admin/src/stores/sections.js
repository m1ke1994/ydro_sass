import { ref } from 'vue'
import { defineStore } from 'pinia'

import { createSectionRequest, getSectionRequest, getSectionsRequest, patchSectionRequest } from '../api/sections'

export const useSectionsStore = defineStore('sections', () => {
  const sections = ref([])
  const currentSection = ref(null)
  const loading = ref(false)

  async function fetchSections(siteId) {
    loading.value = true
    try {
      const { data } = await getSectionsRequest(siteId)
      sections.value = Array.isArray(data) ? data : []
      return sections.value
    } finally {
      loading.value = false
    }
  }

  async function fetchSection(siteId, sectionId) {
    loading.value = true
    try {
      const { data } = await getSectionRequest(siteId, sectionId)
      currentSection.value = data
      return data
    } finally {
      loading.value = false
    }
  }

  async function patchSection(siteId, sectionId, payload) {
    const { data } = await patchSectionRequest(siteId, sectionId, payload)
    const idx = sections.value.findIndex((item) => item.id === data.id)
    if (idx >= 0) {
      sections.value[idx] = data
    }
    currentSection.value = data
    return data
  }

  async function createSection(siteId, payload) {
    const { data } = await createSectionRequest(siteId, payload)
    sections.value.push(data)
    return data
  }

  function reset() {
    sections.value = []
    currentSection.value = null
  }

  return {
    sections,
    currentSection,
    loading,
    fetchSections,
    fetchSection,
    patchSection,
    createSection,
    reset,
  }
})
