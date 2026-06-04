<script setup>
import { onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ArrowRight, ExternalLink, Globe2 } from '@lucide/vue'

import { useAuthStore } from '../stores/auth'
import { useSectionsStore } from '../stores/sections'
import { useSiteStore } from '../stores/site'

const router = useRouter()
const authStore = useAuthStore()
const siteStore = useSiteStore()
const sectionsStore = useSectionsStore()

function openSite(siteId) {
  siteStore.selectSite(siteId)
  sectionsStore.reset()
  router.push(`/sites/${siteId}/overview`)
}

function publicSiteUrl(domain) {
  if (!domain) return ''
  return domain.startsWith('http://') || domain.startsWith('https://') ? domain : `http://${domain}`
}

onMounted(async () => {
  if (!authStore.user) await authStore.getCurrentUser()
  await siteStore.fetchSites()
})
</script>

<template>
  <div class="page-stack">
    <header class="page-heading">
      <div>
        <p class="eyebrow">Панель управления</p>
        <h1>Мои сайты</h1>
        <p>Выберите сайт, чтобы посмотреть заявки, аналитику и изменить содержимое.</p>
      </div>
    </header>

    <section v-if="siteStore.loading" class="empty-state">
      <span class="loading-dot" />
      <p>Загружаем ваши сайты...</p>
    </section>

    <section v-else-if="siteStore.sites.length === 0" class="empty-state">
      <Globe2 :size="28" />
      <h2>Сайты пока не добавлены</h2>
      <p>Обратитесь к администратору, чтобы подключить первый сайт.</p>
    </section>

    <section v-else class="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
      <article v-for="site in siteStore.sites" :key="site.id" class="site-card">
        <div class="flex items-start justify-between gap-3">
          <span class="inline-flex h-11 w-11 items-center justify-center rounded-lg bg-cyan-50 text-cyan-700">
            <Globe2 :size="22" />
          </span>
          <span class="status-badge status-success">{{ site.is_active ? 'Сайт работает' : 'Сайт выключен' }}</span>
        </div>
        <div class="mt-5 min-w-0">
          <h2 class="truncate text-lg font-semibold text-slate-950">{{ site.name }}</h2>
          <p class="mt-1 truncate text-sm text-slate-500">{{ site.domain || 'Домен пока не указан' }}</p>
          <p class="mt-3 text-sm text-slate-600">Разделов на сайте: {{ site.sections_count || 0 }}</p>
        </div>
        <div class="mt-5 flex flex-wrap gap-2">
          <button type="button" class="action-button-primary flex-1" @click="openSite(site.id)">
            Управлять
            <ArrowRight :size="17" />
          </button>
          <a
            v-if="site.domain"
            :href="publicSiteUrl(site.domain)"
            target="_blank"
            rel="noreferrer"
            class="icon-button"
            title="Открыть сайт"
            aria-label="Открыть сайт"
          >
            <ExternalLink :size="18" />
          </a>
        </div>
      </article>
    </section>
  </div>
</template>
