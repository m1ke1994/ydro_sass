<script setup>
import { computed, onMounted } from 'vue'

import DashboardStats from '../components/DashboardStats.vue'
import SectionList from '../components/SectionList.vue'
import { useAuthStore } from '../stores/auth'
import { useSectionsStore } from '../stores/sections'
import { useSiteStore } from '../stores/site'

const authStore = useAuthStore()
const siteStore = useSiteStore()
const sectionsStore = useSectionsStore()

const activeSectionsCount = computed(() => sectionsStore.sections.filter((item) => item.is_active).length)

const stats = computed(() => [
  {
    label: 'Количество разделов',
    value: sectionsStore.sections.length,
    sub: 'Всего в проекте',
  },
  {
    label: 'Название сайта',
    value: siteStore.site?.name || '—',
    sub: 'Текущий проект',
  },
  {
    label: 'Домен',
    value: siteStore.site?.domain || '—',
    sub: 'Публичный адрес',
  },
  {
    label: 'Активных секций',
    value: activeSectionsCount.value,
    sub: 'Опубликованные блоки',
  },
])

const featuredSections = computed(() => {
  const order = ['hero', 'about', 'services', 'reviews', 'gallery']
  const indexed = new Map(sectionsStore.sections.map((item) => [item.slug, item]))
  return order
    .map((slug) => indexed.get(slug))
    .filter(Boolean)
})

onMounted(async () => {
  if (!authStore.user) {
    await authStore.getCurrentUser()
  }

  await Promise.all([
    siteStore.fetchSite(),
    sectionsStore.fetchSections(),
  ])
})
</script>

<template>
  <div class="space-y-6">
    <div>
      <h1 class="text-3xl font-semibold text-slate-900">Главная</h1>
      <p class="mt-2 text-slate-500">Добро пожаловать! Управляйте контентом вашего сайта.</p>
    </div>

    <DashboardStats :items="stats" />

    <section class="rounded-2xl border border-slate-200 bg-white p-5 shadow-soft">
      <div class="mb-4 flex items-center justify-between">
        <h2 class="text-lg font-semibold text-slate-900">Разделы сайта</h2>
        <RouterLink
          to="/sections"
          class="rounded-xl bg-brand-600 px-4 py-2 text-sm font-semibold text-white transition hover:bg-brand-700"
        >
          Открыть все
        </RouterLink>
      </div>

      <SectionList :sections="featuredSections" />
    </section>
  </div>
</template>
