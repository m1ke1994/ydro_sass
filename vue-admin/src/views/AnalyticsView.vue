<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { BarChart3, Copy, KeyRound, MonitorSmartphone, RefreshCw } from '@lucide/vue'

import { getSiteAnalyticsSummaryRequest } from '../api/analytics'
import DashboardStats from '../components/DashboardStats.vue'
import { refreshSiteTrackingKeyRequest } from '../api/site'
import { useSiteStore } from '../stores/site'

const route = useRoute()
const siteStore = useSiteStore()
const loading = ref(false)
const error = ref('')
const success = ref('')
const summary = ref(null)
const days = ref(14)
const action = ref('')
const siteId = computed(() => Number(route.params.siteId))
const trackerScript = computed(() => summary.value?.tracker?.script_tag || siteStore.currentSite?.tracker_script_tag || '')
const deviceRows = computed(() => distributionRows(summary.value?.devices))
const browserRows = computed(() => distributionRows(summary.value?.browsers))
const osRows = computed(() => distributionRows(summary.value?.os))

const stats = computed(() => [
  { label: 'Посетители', value: summary.value?.visit_count ?? 0, sub: 'всего посещений' },
  { label: 'Уникальные', value: summary.value?.visitors_unique ?? 0, sub: 'разные пользователи' },
  { label: 'Просмотры', value: summary.value?.pageviews_count ?? 0, sub: 'открытые страницы' },
  { label: 'Заявки', value: summary.value?.leads_count ?? 0, sub: `конверсия ${summary.value?.conversion ?? 0}%` },
])

function deviceLabel(value) {
  return { desktop: 'Компьютер', mobile: 'Телефон', tablet: 'Планшет' }[value] || value || 'Не определено'
}

function distributionRows(distribution) {
  const entries = Object.entries(distribution || {})
  const total = entries.reduce((sum, [, count]) => sum + Number(count || 0), 0)
  return entries
    .map(([name, count]) => ({
      name,
      count: Number(count || 0),
      percent: total ? Math.round((Number(count || 0) / total) * 100) : 0,
    }))
    .filter((item) => item.count > 0)
    .sort((left, right) => right.count - left.count)
}

async function load() {
  loading.value = true
  error.value = ''
  try {
    siteStore.selectSite(siteId.value)
    if (!siteStore.currentSite) await siteStore.fetchSite(siteId.value)
    const { data } = await getSiteAnalyticsSummaryRequest(siteId.value, { days: days.value })
    summary.value = data
  } catch (e) {
    error.value = e?.response?.data?.detail || 'Не удалось загрузить аналитику.'
  } finally {
    loading.value = false
  }
}

async function copyScript() {
  if (!trackerScript.value) return
  action.value = 'copy'; error.value = ''; success.value = ''
  try {
    await navigator.clipboard.writeText(trackerScript.value)
    success.value = 'Скрипт аналитики скопирован.'
  } catch {
    error.value = 'Не удалось скопировать скрипт. Выделите код вручную.'
  } finally {
    action.value = ''
  }
}

async function refreshKey() {
  action.value = 'key'; error.value = ''; success.value = ''
  try {
    const { data } = await refreshSiteTrackingKeyRequest(siteId.value)
    summary.value = {
      ...(summary.value || {}),
      tracker: {
        api_key: data.api_key,
        script_tag: data.tracker_script_tag,
      },
    }
    await siteStore.fetchSite(siteId.value)
    success.value = data?.detail || 'Ключ аналитики обновлен.'
  } catch (e) {
    error.value = e?.response?.data?.detail || 'Не удалось обновить ключ аналитики.'
  } finally {
    action.value = ''
  }
}

onMounted(load)
</script>

<template>
  <div class="page-stack">
    <header class="page-heading page-heading-actions">
      <div>
        <p class="eyebrow">Посетители сайта</p>
        <h1>Аналитика</h1>
        <p>Понятная статистика без технических данных.</p>
      </div>
      <div class="flex gap-2">
        <select v-model.number="days" class="form-control w-36" @change="load">
          <option :value="7">7 дней</option><option :value="14">14 дней</option><option :value="30">30 дней</option><option :value="90">90 дней</option>
        </select>
        <button type="button" class="icon-button" title="Обновить" aria-label="Обновить" @click="load"><RefreshCw :size="18" /></button>
      </div>
    </header>

    <p v-if="error" class="notice-error">{{ error }}</p>
    <p v-if="success" class="notice-success">{{ success }}</p>
    <section v-if="loading" class="empty-state"><span class="loading-dot" /><p>Собираем статистику...</p></section>
    <template v-else>
      <section class="surface">
        <div class="section-heading">
          <div><h2>Скрипт аналитики</h2><p>Вставьте этот код на публичный сайт перед закрывающим тегом body.</p></div>
          <KeyRound :size="21" class="text-cyan-700" />
        </div>
        <code class="block overflow-x-auto rounded-lg bg-slate-950 px-4 py-3 text-sm leading-6 text-slate-50">{{ trackerScript || 'Ключ аналитики пока не создан.' }}</code>
        <div class="mt-3 flex flex-col gap-2 sm:flex-row">
          <button type="button" class="action-button-primary" :disabled="!trackerScript || Boolean(action)" @click="copyScript"><Copy :size="17" />Скопировать скрипт</button>
          <button type="button" class="action-button-secondary" :disabled="Boolean(action)" @click="refreshKey"><KeyRound :size="17" />{{ action === 'key' ? 'Обновляем...' : 'Обновить ключ' }}</button>
        </div>
      </section>

      <DashboardStats :items="stats" />
      <div class="grid gap-4 xl:grid-cols-2">
        <section class="surface">
          <div class="section-heading"><div><h2>Популярные страницы</h2><p>Что посетители смотрят чаще всего.</p></div><BarChart3 :size="21" class="text-cyan-700" /></div>
          <div v-if="(summary?.top_pages || []).length" class="space-y-2">
            <div v-for="page in summary.top_pages" :key="page.pathname" class="flex items-center justify-between gap-4 border-b border-slate-100 py-3 last:border-0">
              <span class="min-w-0 truncate text-sm font-medium text-slate-800">{{ page.pathname || '/' }}</span>
              <span class="status-badge status-neutral">{{ page.count }} просмотров</span>
            </div>
          </div>
          <div v-else class="empty-state min-h-32"><p>Данных о страницах пока нет.</p></div>
        </section>

        <section class="surface">
          <div class="section-heading"><div><h2>Устройства</h2><p>С чего заходят ваши клиенты.</p></div><MonitorSmartphone :size="21" class="text-cyan-700" /></div>
          <div v-if="deviceRows.length" class="space-y-2">
            <div v-for="item in deviceRows" :key="item.name" class="flex items-center justify-between border-b border-slate-100 py-3 last:border-0">
              <span class="text-sm font-medium">{{ deviceLabel(item.name) }}</span>
              <strong class="text-sm text-slate-950">{{ item.percent }}%</strong>
            </div>
          </div>
          <div v-else class="empty-state min-h-32"><p>Данных об устройствах пока нет.</p></div>
        </section>

        <section class="surface">
          <div class="section-heading"><div><h2>Браузеры</h2><p>Какими программами пользуются посетители.</p></div></div>
          <div v-if="browserRows.length" class="space-y-2">
            <div v-for="item in browserRows.slice(0, 8)" :key="item.name" class="flex items-center justify-between border-b border-slate-100 py-3 last:border-0">
              <span class="text-sm">{{ item.name === 'Unknown' ? 'Не определено' : item.name }}</span><strong class="text-sm">{{ item.percent }}%</strong>
            </div>
          </div>
          <div v-else class="empty-state min-h-32"><p>Данных о браузерах пока нет.</p></div>
        </section>

        <section class="surface">
          <div class="section-heading"><div><h2>Операционные системы</h2><p>Какие системы установлены на устройствах посетителей.</p></div></div>
          <div v-if="osRows.length" class="space-y-2">
            <div v-for="item in osRows.slice(0, 8)" :key="item.name" class="flex items-center justify-between border-b border-slate-100 py-3 last:border-0">
              <span class="text-sm">{{ item.name === 'Unknown' ? 'Не определено' : item.name }}</span><strong class="text-sm">{{ item.percent }}%</strong>
            </div>
          </div>
          <div v-else class="empty-state min-h-32"><p>Данных об операционных системах пока нет.</p></div>
        </section>

        <section class="surface">
          <div class="section-heading"><div><h2>Источники переходов</h2><p>Откуда приходят посетители и заявки.</p></div></div>
          <div v-if="(summary?.sources || []).length" class="space-y-2">
            <div v-for="item in summary.sources.slice(0, 8)" :key="item.referrer || 'direct'" class="grid grid-cols-[1fr_auto] items-center gap-3 border-b border-slate-100 py-3 last:border-0">
              <span class="truncate text-sm font-medium">{{ item.referrer || 'Прямой переход' }}</span>
              <span class="text-xs text-slate-500">{{ item.count }} визитов</span>
            </div>
          </div>
          <div v-else class="empty-state min-h-32"><p>Данных об источниках пока нет.</p></div>
        </section>

        <section class="surface">
          <div class="section-heading"><div><h2>Время на сайте</h2><p>Средняя длительность визита.</p></div></div>
          <p class="text-4xl font-semibold text-slate-950">{{ summary?.avg_duration || 0 }} сек.</p>
          <p class="mt-2 text-sm text-slate-500">Метрика появится после закрытия страницы посетителем или смены вкладки.</p>
        </section>
      </div>
    </template>
  </div>
</template>
