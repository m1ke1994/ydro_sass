<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { BarChart3, MonitorSmartphone, RefreshCw } from '@lucide/vue'

import { getSiteAnalyticsSummaryRequest } from '../api/analytics'
import { miniDevices, miniSummary } from '../api/mini'
import DashboardStats from '../components/DashboardStats.vue'
import { useSiteStore } from '../stores/site'

const route = useRoute()
const siteStore = useSiteStore()
const loading = ref(false)
const error = ref('')
const summary = ref(null)
const devices = ref(null)
const marketing = ref(null)
const days = ref(14)
const siteId = computed(() => Number(route.params.siteId))
const deviceRows = computed(() => distributionRows(devices.value?.devices))
const browserRows = computed(() => distributionRows(devices.value?.browsers))
const osRows = computed(() => distributionRows(devices.value?.os))

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
    const [{ data }, deviceData, marketingData] = await Promise.all([
      getSiteAnalyticsSummaryRequest(siteId.value, { days: days.value }),
      miniDevices({ days: days.value }),
      miniSummary({ days: days.value }),
    ])
    summary.value = data
    devices.value = deviceData
    marketing.value = marketingData
  } catch (e) {
    error.value = e?.response?.data?.detail || 'Не удалось загрузить аналитику.'
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
    <section v-if="loading" class="empty-state"><span class="loading-dot" /><p>Собираем статистику...</p></section>
    <template v-else>
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
          <div v-if="(marketing?.source_performance || []).length" class="space-y-2">
            <div v-for="item in marketing.source_performance.slice(0, 8)" :key="item.source" class="grid grid-cols-[1fr_auto_auto] items-center gap-3 border-b border-slate-100 py-3 last:border-0">
              <span class="truncate text-sm font-medium">{{ item.source || 'Прямой переход' }}</span>
              <span class="text-xs text-slate-500">{{ item.visits }} визитов</span>
              <span class="status-badge status-success">{{ item.leads }} заявок</span>
            </div>
          </div>
          <div v-else class="empty-state min-h-32"><p>Данных об источниках пока нет.</p></div>
        </section>
      </div>
    </template>
  </div>
</template>
