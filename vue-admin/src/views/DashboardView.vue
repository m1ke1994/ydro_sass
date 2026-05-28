<script setup>
import { computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'

import { useAuthStore } from '../stores/auth'
import { useSectionsStore } from '../stores/sections'
import { useSiteStore } from '../stores/site'

const router = useRouter()
const authStore = useAuthStore()
const siteStore = useSiteStore()
const sectionsStore = useSectionsStore()

const hasManySites = computed(() => siteStore.sites.length > 1)

async function openSite(siteId) {
  siteStore.selectSite(siteId)
  sectionsStore.reset()
  router.push(`/sites/${siteId}/sections`)
}

onMounted(async () => {
  if (!authStore.user) {
    await authStore.getCurrentUser()
  }

  const sites = await siteStore.fetchSites()

  if (sites.length === 1) {
    await openSite(sites[0].id)
  }
})
</script>

<template>
  <div class="space-y-6">
    <div>
      <h1 class="text-3xl font-semibold text-slate-900">Мои сайты</h1>
      <p class="mt-2 text-slate-500">Выберите сайт для управления разделами и контентом.</p>
    </div>

    <section v-if="siteStore.loading" class="rounded-2xl border border-slate-200 bg-white p-5 shadow-soft">
      <p class="text-sm text-slate-500">Загрузка сайтов...</p>
    </section>

    <section v-else-if="siteStore.sites.length === 0" class="rounded-2xl border border-slate-200 bg-white p-5 shadow-soft">
      <p class="text-sm text-slate-500">Сайты не найдены для текущего пользователя.</p>
    </section>

    <section v-else class="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
      <article
        v-for="site in siteStore.sites"
        :key="site.id"
        class="rounded-2xl border border-slate-200 bg-white p-5 shadow-soft"
      >
        <p class="text-xs uppercase tracking-wider text-slate-500">/{{ site.slug }}</p>
        <h2 class="mt-1 text-lg font-semibold text-slate-900">{{ site.name }}</h2>
        <p class="mt-1 text-sm text-slate-500">{{ site.domain || 'Домен не указан' }}</p>
        <p class="mt-3 text-xs text-slate-500">Активных секций: {{ site.sections_count }}</p>
        <p class="mt-2 text-xs text-slate-500">API key: <span class="font-mono">{{ site.api_key }}</span></p>

        <button
          type="button"
          class="mt-4 inline-flex rounded-xl bg-brand-600 px-4 py-2 text-sm font-semibold text-white transition hover:bg-brand-700"
          @click="openSite(site.id)"
        >
          Открыть
        </button>
      </article>
    </section>

    <p v-if="!hasManySites && siteStore.sites.length === 1" class="text-sm text-slate-500">
      Если сайт один, он открывается автоматически.
    </p>
  </div>
</template>
