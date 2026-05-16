<script setup>
import { onMounted } from 'vue'

import SectionList from '../components/SectionList.vue'
import { useSectionsStore } from '../stores/sections'

const sectionsStore = useSectionsStore()

onMounted(async () => {
  await sectionsStore.fetchSections()
})
</script>

<template>
  <div class="space-y-6">
    <div>
      <h1 class="text-3xl font-semibold text-slate-900">Разделы</h1>
      <p class="mt-2 text-slate-500">Список секций, их slug, тип и статус публикации.</p>
    </div>

    <SectionList :sections="sectionsStore.sections" />
  </div>
</template>
