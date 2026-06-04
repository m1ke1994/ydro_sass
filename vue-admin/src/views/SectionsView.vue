<script setup>
import { computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { Blocks } from '@lucide/vue'
import SectionList from '../components/SectionList.vue'
import { useSectionsStore } from '../stores/sections'
import { useSiteStore } from '../stores/site'

const route = useRoute()
const siteStore = useSiteStore()
const sectionsStore = useSectionsStore()
const siteId = computed(() => Number(route.params.siteId))

onMounted(async () => {
  siteStore.selectSite(siteId.value)
  if (!siteStore.currentSite) await siteStore.fetchSite(siteId.value)
  await sectionsStore.fetchSections(siteId.value)
})
</script>

<template>
  <div class="page-stack">
    <header class="page-heading">
      <p class="eyebrow">Содержимое сайта</p>
      <h1>Редактирование сайта</h1>
      <p>Выберите раздел, чтобы изменить текст, изображения, кнопки и ссылки.</p>
    </header>
    <section v-if="sectionsStore.loading" class="empty-state"><span class="loading-dot" /><p>Загружаем разделы...</p></section>
    <section v-else-if="sectionsStore.sections.length === 0" class="empty-state"><Blocks :size="30" /><h2>Разделов пока нет</h2><p>Обратитесь к администратору, чтобы добавить первый раздел сайта.</p></section>
    <SectionList v-else :site-id="siteId" :sections="sectionsStore.sections" />
  </div>
</template>
