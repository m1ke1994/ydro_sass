<script setup>
import { computed, onUnmounted, ref } from 'vue'

import {
  miniSeoDetail,
  miniSeoExport,
  miniSeoHistory,
  miniSeoIssues,
  miniSeoLatest,
  miniSeoPages,
  miniSeoRecommendations,
  miniSeoStart,
} from '../../api/mini'

const domain = ref('')
const loading = ref(false)
const error = ref('')
const latest = ref(null)
const detail = ref(null)
const history = ref([])
const recommendations = ref([])
const pages = ref([])
const issues = ref([])
const severity = ref('all')
const downloadingPdf = ref(false)
let pollTimer = null

const severityOptions = [
  { value: 'all', label: 'Все' },
  { value: 'high', label: 'Критичные' },
  { value: 'medium', label: 'Средние' },
  { value: 'low', label: 'Низкие' },
]

const isAuditRunning = computed(() => {
  const status = String(latest.value?.status || detail.value?.status || '').toLowerCase()
  return status === 'pending' || status === 'running'
})

function normalizedDomain() {
  return domain.value.trim().toLowerCase()
}

function statusLabel(statusRaw) {
  const status = String(statusRaw || '').toLowerCase()
  if (status === 'pending') return 'В очереди'
  if (status === 'running') return 'Идёт проверка'
  if (status === 'done' || status === 'completed') return 'Завершён'
  if (status === 'failed' || status === 'error') return 'Ошибка'
  if (status === 'stopped') return 'Остановлен'
  return status || '—'
}

function stopPolling() {
  if (pollTimer) {
    clearInterval(pollTimer)
    pollTimer = null
  }
}

function startPolling() {
  stopPolling()
  pollTimer = setInterval(async () => {
    if (!latest.value?.audit_id) return
    try {
      const fresh = await miniSeoDetail(latest.value.audit_id)
      detail.value = fresh
      if (!isAuditRunning.value) {
        await reloadIssues()
        stopPolling()
      }
    } catch (_e) {
      stopPolling()
    }
  }, 4000)
}

async function reloadIssues() {
  if (!latest.value?.audit_id) {
    issues.value = []
    return
  }
  const params = severity.value !== 'all' ? { severity: severity.value } : {}
  const payload = await miniSeoIssues(latest.value.audit_id, params)
  issues.value = payload?.rows || []
}

async function loadAudit(auditId) {
  const [d, h, r, p] = await Promise.all([
    miniSeoDetail(auditId),
    miniSeoHistory(auditId),
    miniSeoRecommendations(auditId),
    miniSeoPages(auditId),
  ])
  detail.value = d
  history.value = h?.rows || []
  recommendations.value = r?.items || r?.recommendations || []
  pages.value = p?.rows || []
  await reloadIssues()
}

async function refreshLatest() {
  const value = normalizedDomain()
  if (!value) {
    error.value = 'Введите домен.'
    return
  }
  loading.value = true
  error.value = ''
  try {
    latest.value = await miniSeoLatest(value)
    if (latest.value?.audit_id) {
      await loadAudit(latest.value.audit_id)
      if (isAuditRunning.value) {
        startPolling()
      } else {
        stopPolling()
      }
    }
  } catch (e) {
    error.value = e?.response?.data?.detail || 'Не удалось получить последний аудит.'
  } finally {
    loading.value = false
  }
}

async function startAudit() {
  const value = normalizedDomain()
  if (!value) {
    error.value = 'Введите домен.'
    return
  }
  loading.value = true
  error.value = ''
  try {
    latest.value = await miniSeoStart(value)
    await loadAudit(latest.value.audit_id)
    if (isAuditRunning.value) {
      startPolling()
    }
  } catch (e) {
    error.value = e?.response?.data?.detail || 'Не удалось запустить аудит.'
  } finally {
    loading.value = false
  }
}

async function downloadPdf() {
  if (!latest.value?.audit_id || downloadingPdf.value) return
  downloadingPdf.value = true
  error.value = ''
  try {
    const blob = await miniSeoExport(latest.value.audit_id)
    const href = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = href
    link.download = `seo-audit-${latest.value.audit_id}.pdf`
    document.body.appendChild(link)
    link.click()
    link.remove()
    URL.revokeObjectURL(href)
  } catch (e) {
    error.value = e?.response?.data?.detail || 'Не удалось скачать PDF-отчёт.'
  } finally {
    downloadingPdf.value = false
  }
}

onUnmounted(stopPolling)
</script>

<template>
  <section class="space-y-4 rounded-2xl border border-slate-200 bg-white p-4">
    <h2 class="text-base font-semibold text-slate-900">SEO-аудит mini</h2>

    <div class="flex flex-wrap gap-2">
      <input
        v-model="domain"
        class="w-full max-w-xs rounded-xl border border-slate-300 px-3 py-2 text-sm"
        placeholder="example.com"
      >
      <button
        class="rounded-xl border border-slate-300 px-4 py-2 text-sm"
        :disabled="loading"
        @click="refreshLatest"
      >
        Проверить последний
      </button>
      <button
        class="rounded-xl bg-brand-600 px-4 py-2 text-sm font-semibold text-white hover:bg-brand-700 disabled:opacity-70"
        :disabled="loading"
        @click="startAudit"
      >
        Запустить аудит
      </button>
      <button
        class="rounded-xl border border-slate-300 px-4 py-2 text-sm"
        :disabled="!latest?.audit_id || downloadingPdf"
        @click="downloadPdf"
      >
        {{ downloadingPdf ? 'Готовим PDF...' : 'Скачать PDF-отчёт' }}
      </button>
    </div>

    <p v-if="error" class="rounded-xl border border-rose-200 bg-rose-50 p-3 text-sm text-rose-700">
      {{ error }}
    </p>

    <div v-if="latest" class="rounded-xl border border-slate-200 bg-slate-50 p-3 text-sm">
      <p><strong>Аудит:</strong> #{{ latest.audit_id || '—' }}</p>
      <p><strong>Статус:</strong> {{ statusLabel(latest.status || detail?.status) }}</p>
      <p><strong>Домен:</strong> {{ latest.domain || '—' }}</p>
      <p v-if="isAuditRunning" class="mt-2 text-amber-700">Идёт проверка страниц, подождите...</p>
    </div>

    <div v-if="detail" class="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
      <article class="rounded-xl border border-slate-200 p-3">
        <p class="text-xs text-slate-500">SEO Score</p>
        <p class="text-xl font-semibold">{{ detail.score }}</p>
      </article>
      <article class="rounded-xl border border-slate-200 p-3">
        <p class="text-xs text-slate-500">Проверено страниц</p>
        <p class="text-xl font-semibold">{{ detail.pages_count }}</p>
      </article>
      <article class="rounded-xl border border-slate-200 p-3">
        <p class="text-xs text-slate-500">Ошибок (high)</p>
        <p class="text-xl font-semibold">{{ detail.breakdown?.high_issues || 0 }}</p>
      </article>
      <article class="rounded-xl border border-slate-200 p-3">
        <p class="text-xs text-slate-500">Ошибок (medium)</p>
        <p class="text-xl font-semibold">{{ detail.breakdown?.medium_issues || 0 }}</p>
      </article>
    </div>

    <div v-if="recommendations.length" class="rounded-xl border border-slate-200 p-3">
      <h3 class="mb-2 text-sm font-semibold">Рекомендации</h3>
      <ul class="list-disc space-y-1 pl-5 text-sm text-slate-700">
        <li v-for="item in recommendations" :key="item">{{ item }}</li>
      </ul>
    </div>

    <div v-if="pages.length" class="rounded-xl border border-slate-200 p-3">
      <h3 class="mb-2 text-sm font-semibold">Страницы аудита</h3>
      <div class="overflow-x-auto">
        <table class="min-w-full text-sm">
          <thead>
            <tr class="border-b border-slate-100 text-left text-slate-500">
              <th class="px-2 py-2">URL</th>
              <th class="px-2 py-2">HTTP</th>
              <th class="px-2 py-2">Title</th>
              <th class="px-2 py-2">H1</th>
              <th class="px-2 py-2">TTFB, мс</th>
              <th class="px-2 py-2">Score</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="row in pages" :key="row.id" class="border-b border-slate-50">
              <td class="px-2 py-2">{{ row.url }}</td>
              <td class="px-2 py-2">{{ row.status_code }}</td>
              <td class="px-2 py-2">{{ row.title || '—' }}</td>
              <td class="px-2 py-2">{{ row.h1_count }}</td>
              <td class="px-2 py-2">{{ row.ttfb_ms }}</td>
              <td class="px-2 py-2">{{ row.performance_score }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <div v-if="latest?.audit_id" class="rounded-xl border border-slate-200 p-3">
      <div class="mb-2 flex flex-wrap items-center gap-2">
        <h3 class="text-sm font-semibold">SEO-проблемы</h3>
        <select
          v-model="severity"
          class="rounded-lg border border-slate-300 px-2 py-1 text-sm"
          @change="reloadIssues"
        >
          <option v-for="option in severityOptions" :key="option.value" :value="option.value">
            {{ option.label }}
          </option>
        </select>
      </div>
      <div v-if="issues.length" class="overflow-x-auto">
        <table class="min-w-full text-sm">
          <thead>
            <tr class="border-b border-slate-100 text-left text-slate-500">
              <th class="px-2 py-2">Серьёзность</th>
              <th class="px-2 py-2">Страница</th>
              <th class="px-2 py-2">Проблема</th>
              <th class="px-2 py-2">Рекомендация</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="row in issues" :key="row.id" class="border-b border-slate-50">
              <td class="px-2 py-2">{{ row.severity }}</td>
              <td class="px-2 py-2">{{ row.page_url }}</td>
              <td class="px-2 py-2">{{ row.issue_title }}</td>
              <td class="px-2 py-2">{{ row.recommendation }}</td>
            </tr>
          </tbody>
        </table>
      </div>
      <p v-else class="text-sm text-slate-500">Проблем не найдено по выбранному фильтру.</p>
    </div>

    <div v-if="history.length" class="rounded-xl border border-slate-200 p-3">
      <h3 class="mb-2 text-sm font-semibold">История аудитов</h3>
      <div class="overflow-x-auto">
        <table class="min-w-full text-sm">
          <thead>
            <tr class="border-b border-slate-100 text-left text-slate-500">
              <th class="px-2 py-2">Аудит</th>
              <th class="px-2 py-2">Score</th>
              <th class="px-2 py-2">Страниц</th>
              <th class="px-2 py-2">Дата</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="row in history" :key="row.audit_id" class="border-b border-slate-50">
              <td class="px-2 py-2">{{ row.audit_id }}</td>
              <td class="px-2 py-2">{{ row.score }}</td>
              <td class="px-2 py-2">{{ row.pages_count }}</td>
              <td class="px-2 py-2">{{ row.created_at }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </section>
</template>
