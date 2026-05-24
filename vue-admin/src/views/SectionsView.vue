<script setup>
import { computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'

import SectionList from '../components/SectionList.vue'
import { useSectionsStore } from '../stores/sections'
import { useSiteStore } from '../stores/site'

const route = useRoute()
const siteStore = useSiteStore()
const sectionsStore = useSectionsStore()

const siteId = computed(() => Number(route.params.siteId))

onMounted(async () => {
  siteStore.selectSite(siteId.value)

  if (!siteStore.currentSite) {
    await siteStore.fetchSite(siteId.value)
  }

  await sectionsStore.fetchSections(siteId.value)
})
</script>

<template>
  <div class="space-y-6">
    <div>
      <h1 class="text-3xl font-semibold text-slate-900">Разделы: {{ siteStore.currentSite?.name || 'Сайт' }}</h1>
      <p class="mt-2 text-slate-500">Список секций сайта, их порядок и статус публикации.</p>
    </div>

    <SectionList :site-id="siteId" :sections="sectionsStore.sections" />
  </div>
</template>
