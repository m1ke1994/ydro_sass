<script setup>
import { onMounted, ref } from 'vue'

import { miniDevices, miniEngagement, miniOverview, miniSummary, miniUnique } from '../../api/mini'

const loading = ref(false)
const error = ref('')
const overview = ref(null)
const summary = ref(null)
const devices = ref(null)
const engagement = ref(null)
const unique = ref(null)

async function loadData() {
  loading.value = true
  error.value = ''
  try {
    const [o, s, d, e, u] = await Promise.all([
      miniOverview(),
      miniSummary(),
      miniDevices(),
      miniEngagement(),
      miniUnique(),
    ])
    overview.value = o
    summary.value = s
    devices.value = d
    engagement.value = e
    unique.value = u
  } catch (err) {
    error.value = err?.response?.data?.detail || 'Не удалось загрузить mini-аналитику.'
  } finally {
    loading.value = false
  }
}

onMounted(loadData)
</script>

<template>
  <div class="space-y-4">
    <div v-if="loading" class="rounded-2xl border border-slate-200 bg-white p-4 text-sm text-slate-500">Загрузка...</div>
    <p v-if="error" class="rounded-xl border border-rose-200 bg-rose-50 p-3 text-sm text-rose-700">{{ error }}</p>

    <div class="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
      <article class="rounded-2xl border border-slate-200 bg-white p-4" v-for="item in [
        { label: 'Визиты', value: overview?.visits_total ?? 0 },
        { label: 'Уникальные', value: overview?.visitors_unique ?? 0 },
        { label: 'Формы', value: overview?.forms_total ?? 0 },
        { label: 'Конверсия', value: `${Number(overview?.conversion ?? 0).toFixed(2)}%` },
      ]" :key="item.label">
        <p class="text-sm text-slate-500">{{ item.label }}</p>
        <p class="mt-2 text-2xl font-semibold text-slate-900">{{ item.value }}</p>
      </article>
    </div>

    <div class="grid gap-4 lg:grid-cols-2">
      <section class="rounded-2xl border border-slate-200 bg-white p-4">
        <h2 class="text-base font-semibold text-slate-900">Источники</h2>
        <div class="mt-3 overflow-x-auto">
          <table class="min-w-full text-sm">
            <thead>
              <tr class="border-b border-slate-100 text-left text-slate-500">
                <th class="px-2 py-2">Источник</th>
                <th class="px-2 py-2">Визиты</th>
                <th class="px-2 py-2">Лиды</th>
                <th class="px-2 py-2">CR%</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="row in (summary?.source_performance || []).slice(0, 7)" :key="row.source" class="border-b border-slate-50">
                <td class="px-2 py-2">{{ row.source }}</td>
                <td class="px-2 py-2">{{ row.visits }}</td>
                <td class="px-2 py-2">{{ row.leads }}</td>
                <td class="px-2 py-2">{{ row.conversion_pct }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>

      <section class="rounded-2xl border border-slate-200 bg-white p-4">
        <h2 class="text-base font-semibold text-slate-900">Устройства</h2>
        <div class="mt-3 overflow-x-auto">
          <table class="min-w-full text-sm">
            <thead>
              <tr class="border-b border-slate-100 text-left text-slate-500">
                <th class="px-2 py-2">Тип</th>
                <th class="px-2 py-2">Доля %</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="row in devices?.devices || []" :key="row.device_type" class="border-b border-slate-50">
                <td class="px-2 py-2">{{ row.device_type }}</td>
                <td class="px-2 py-2">{{ row.percent }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>
    </div>

    <section class="rounded-2xl border border-slate-200 bg-white p-4">
      <h2 class="text-base font-semibold text-slate-900">Вовлечённость</h2>
      <p class="mt-2 text-sm text-slate-600">Среднее время на странице: {{ engagement?.avg_time_on_page_seconds ?? 0 }} сек</p>
      <p class="text-sm text-slate-600">Общее время на сайте: {{ engagement?.total_time_on_site_seconds ?? 0 }} сек</p>
      <p class="mt-2 text-sm text-slate-600">Уникальные (суммарно): {{ unique?.total_unique ?? 0 }}</p>
    </section>
  </div>
</template>
