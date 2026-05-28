<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'

import DashboardStats from '../components/DashboardStats.vue'
import { getSiteAnalyticsSummaryRequest } from '../api/analytics'
import { useSiteStore } from '../stores/site'

const route = useRoute()
const siteStore = useSiteStore()

const loading = ref(false)
const errorMessage = ref('')
const summary = ref(null)
const days = ref(14)

const siteId = computed(() => Number(route.params.siteId))

const statItems = computed(() => {
  const payload = summary.value || {}
  return [
    { label: 'Визиты', value: payload.visit_count ?? 0 },
    { label: 'Уникальные', value: payload.visitors_unique ?? 0 },
    { label: 'Заявки', value: payload.leads_count ?? 0 },
    { label: 'Конверсия', value: `${payload.conversion ?? 0}%` },
  ]
})

async function load() {
  loading.value = true
  errorMessage.value = ''
  try {
    siteStore.selectSite(siteId.value)
    if (!siteStore.currentSite) {
      await siteStore.fetchSite(siteId.value)
    }
    const { data } = await getSiteAnalyticsSummaryRequest(siteId.value, { days: days.value })
    summary.value = data
  } catch (error) {
    errorMessage.value = error?.response?.data?.detail || 'Не удалось загрузить аналитику.'
  } finally {
    loading.value = false
  }
}

onMounted(load)
</script>

<template>
  <div class="space-y-6">
    <div class="flex flex-wrap items-center justify-between gap-3">
      <div>
        <RouterLink :to="`/sites/${siteId}/sections`" class="text-sm font-medium text-brand-700 hover:text-brand-800"
          >← К разделам</RouterLink
        >
        <h1 class="mt-2 text-3xl font-semibold text-slate-900">Аналитика: {{ siteStore.currentSite?.name || 'Сайт' }}</h1>
      </div>
      <div class="flex items-center gap-2">
        <select v-model.number="days" class="rounded-lg border border-slate-300 px-3 py-2 text-sm" @change="load">
          <option :value="7">7 дней</option>
          <option :value="14">14 дней</option>
          <option :value="30">30 дней</option>
          <option :value="90">90 дней</option>
        </select>
        <button
          type="button"
          class="rounded-xl bg-brand-600 px-4 py-2 text-sm font-semibold text-white transition hover:bg-brand-700"
          @click="load"
        >
          Обновить
        </button>
      </div>
    </div>

    <p v-if="errorMessage" class="whitespace-pre-wrap rounded-xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">
      {{ errorMessage }}
    </p>

    <section v-if="loading" class="rounded-2xl border border-slate-200 bg-white p-6 shadow-soft">
      <p class="text-sm text-slate-500">Загрузка аналитики...</p>
    </section>

    <template v-else>
      <DashboardStats :items="statItems" />

      <section class="rounded-2xl border border-slate-200 bg-white p-6 shadow-soft">
        <h2 class="text-lg font-semibold text-slate-900">Интеграция трекера</h2>
        <p class="mt-2 text-sm text-slate-600">Вставьте этот script на публичный сайт для сбора визитов и событий.</p>
        <textarea
          :value="summary?.tracker?.script_tag || ''"
          readonly
          class="mt-3 min-h-24 w-full rounded-xl border border-slate-300 bg-slate-50 px-3 py-2 font-mono text-xs text-slate-700"
        />
      </section>

      <section class="rounded-2xl border border-slate-200 bg-white p-6 shadow-soft">
        <h2 class="text-lg font-semibold text-slate-900">Топ страниц</h2>
        <div class="mt-4 overflow-x-auto">
          <table class="min-w-full text-left text-sm">
            <thead class="text-xs uppercase tracking-wide text-slate-500">
              <tr class="border-b border-slate-200">
                <th class="px-3 py-3">Path</th>
                <th class="px-3 py-3">Просмотры</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="row in summary?.top_pages || []" :key="row.pathname" class="border-b border-slate-100">
                <td class="px-3 py-3 font-mono text-slate-700">{{ row.pathname || '/' }}</td>
                <td class="px-3 py-3 text-slate-900">{{ row.count }}</td>
              </tr>
              <tr v-if="(summary?.top_pages || []).length === 0">
                <td class="px-3 py-3 text-slate-500" colspan="2">Данные пока не поступали.</td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>
    </template>
  </div>
</template>
