<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { BarChart3, Blocks, ExternalLink, Inbox, SearchCheck, Send } from '@lucide/vue'

import { getSiteAnalyticsSummaryRequest } from '../api/analytics'
import { getSiteTelegramRequest } from '../api/site'
import DashboardStats from '../components/DashboardStats.vue'
import { useSiteStore } from '../stores/site'

const route = useRoute()
const router = useRouter()
const siteStore = useSiteStore()
const loading = ref(false)
const error = ref('')
const summary = ref(null)
const telegram = ref(null)

const siteId = computed(() => Number(route.params.siteId))
const stats = computed(() => [
  { label: 'Заявки', value: summary.value?.leads_count ?? 0, sub: 'за последние 14 дней' },
  { label: 'Посетители', value: summary.value?.visitors_unique ?? 0, sub: 'уникальные пользователи' },
  { label: 'Просмотры', value: summary.value?.pageviews_count ?? 0, sub: 'просмотры страниц' },
  { label: 'Конверсия', value: `${summary.value?.conversion ?? 0}%`, sub: 'посетители, оставившие заявку' },
])

const actions = computed(() => [
  { label: 'Посмотреть заявки', text: 'Новые обращения клиентов', icon: Inbox, to: `/sites/${siteId.value}/leads` },
  { label: 'Изменить сайт', text: 'Тексты, изображения и разделы', icon: Blocks, to: `/sites/${siteId.value}/sections` },
  { label: 'Открыть аналитику', text: 'Посетители и популярные страницы', icon: BarChart3, to: `/sites/${siteId.value}/analytics` },
  { label: 'Проверить SEO', text: 'Найти проблемы сайта', icon: SearchCheck, to: `/sites/${siteId.value}/seo` },
  { label: telegram.value?.connected ? 'Telegram подключен' : 'Подключить Telegram', text: 'Получать заявки сразу в чат', icon: Send, to: `/sites/${siteId.value}/integration` },
])

function openPublicSite() {
  const domain = siteStore.currentSite?.domain
  if (!domain) return
  window.open(domain.startsWith('http') ? domain : `http://${domain}`, '_blank', 'noopener,noreferrer')
}

async function load() {
  loading.value = true
  error.value = ''
  try {
    siteStore.selectSite(siteId.value)
    if (!siteStore.currentSite) await siteStore.fetchSite(siteId.value)
    const [{ data }, telegramData] = await Promise.all([
      getSiteAnalyticsSummaryRequest(siteId.value, { days: 14 }),
      getSiteTelegramRequest(siteId.value),
    ])
    summary.value = data
    telegram.value = telegramData.data
  } catch (e) {
    error.value = e?.response?.data?.detail || 'Не удалось загрузить данные сайта.'
  } finally {
    loading.value = false
  }
}

onMounted(load)
</script>

<template>
  <div class="page-stack">
    <header class="page-heading page-heading-actions">
      <div>
        <p class="eyebrow">Главная</p>
        <h1>{{ siteStore.currentSite?.name || 'Ваш сайт' }}</h1>
        <p>{{ siteStore.currentSite?.domain || 'Домен пока не указан' }}</p>
      </div>
      <button type="button" class="action-button-secondary" :disabled="!siteStore.currentSite?.domain" @click="openPublicSite">
        <ExternalLink :size="17" />
        Открыть сайт
      </button>
    </header>

    <p v-if="error" class="notice-error">{{ error }}</p>
    <section v-if="loading" class="empty-state"><span class="loading-dot" /><p>Собираем информацию...</p></section>

    <template v-else>
      <DashboardStats :items="stats" />
      <section>
        <div class="section-heading">
          <div>
            <h2>Быстрые действия</h2>
            <p>Основные задачи всегда под рукой.</p>
          </div>
        </div>
        <div class="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
          <button v-for="action in actions" :key="action.to" type="button" class="quick-action" @click="router.push(action.to)">
            <component :is="action.icon" :size="21" />
            <span>
              <strong>{{ action.label }}</strong>
              <small>{{ action.text }}</small>
            </span>
          </button>
        </div>
      </section>
    </template>
  </div>
</template>
