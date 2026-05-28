<script setup>
import { ref } from 'vue'

import { miniSeoDetail, miniSeoHistory, miniSeoLatest, miniSeoRecommendations, miniSeoStart } from '../../api/mini'

const domain = ref('')
const loading = ref(false)
const error = ref('')
const latest = ref(null)
const detail = ref(null)
const history = ref([])
const recommendations = ref([])

async function refreshLatest() {
  if (!domain.value.trim()) {
    error.value = 'Введите домен.'
    return
  }
  loading.value = true
  error.value = ''
  try {
    latest.value = await miniSeoLatest(domain.value.trim().toLowerCase())
    if (latest.value?.audit_id) {
      await loadAudit(latest.value.audit_id)
    }
  } catch (e) {
    error.value = e?.response?.data?.detail || 'Не удалось получить последний аудит.'
  } finally {
    loading.value = false
  }
}

async function startAudit() {
  if (!domain.value.trim()) {
    error.value = 'Введите домен.'
    return
  }
  loading.value = true
  error.value = ''
  try {
    latest.value = await miniSeoStart(domain.value.trim().toLowerCase())
    await loadAudit(latest.value.audit_id)
  } catch (e) {
    error.value = e?.response?.data?.detail || 'Не удалось запустить аудит.'
  } finally {
    loading.value = false
  }
}

async function loadAudit(auditId) {
  const [d, h, r] = await Promise.all([
    miniSeoDetail(auditId),
    miniSeoHistory(auditId),
    miniSeoRecommendations(auditId),
  ])
  detail.value = d
  history.value = h?.rows || []
  recommendations.value = r?.items || []
}
</script>

<template>
  <section class="space-y-4 rounded-2xl border border-slate-200 bg-white p-4">
    <h2 class="text-base font-semibold text-slate-900">SEO-аудит mini</h2>

    <div class="flex flex-wrap gap-2">
      <input v-model="domain" class="w-full max-w-xs rounded-xl border border-slate-300 px-3 py-2 text-sm" placeholder="example.com">
      <button class="rounded-xl border border-slate-300 px-4 py-2 text-sm" :disabled="loading" @click="refreshLatest">Проверить последний</button>
      <button class="rounded-xl bg-brand-600 px-4 py-2 text-sm font-semibold text-white hover:bg-brand-700 disabled:opacity-70" :disabled="loading" @click="startAudit">Запустить аудит</button>
    </div>

    <p v-if="error" class="rounded-xl border border-rose-200 bg-rose-50 p-3 text-sm text-rose-700">{{ error }}</p>

    <div v-if="latest" class="rounded-xl border border-slate-200 bg-slate-50 p-3 text-sm">
      <p><strong>Audit ID:</strong> {{ latest.audit_id || '—' }}</p>
      <p><strong>Статус:</strong> {{ latest.status || '—' }}</p>
      <p><strong>Домен:</strong> {{ latest.domain || '—' }}</p>
    </div>

    <div v-if="detail" class="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
      <article class="rounded-xl border border-slate-200 p-3">
        <p class="text-xs text-slate-500">Score</p>
        <p class="text-xl font-semibold">{{ detail.score }}</p>
      </article>
      <article class="rounded-xl border border-slate-200 p-3">
        <p class="text-xs text-slate-500">Страниц</p>
        <p class="text-xl font-semibold">{{ detail.pages_count }}</p>
      </article>
      <article class="rounded-xl border border-slate-200 p-3">
        <p class="text-xs text-slate-500">High issues</p>
        <p class="text-xl font-semibold">{{ detail.breakdown?.high_issues || 0 }}</p>
      </article>
      <article class="rounded-xl border border-slate-200 p-3">
        <p class="text-xs text-slate-500">Medium issues</p>
        <p class="text-xl font-semibold">{{ detail.breakdown?.medium_issues || 0 }}</p>
      </article>
    </div>

    <div v-if="recommendations.length" class="rounded-xl border border-slate-200 p-3">
      <h3 class="mb-2 text-sm font-semibold">Рекомендации</h3>
      <ul class="list-disc space-y-1 pl-5 text-sm text-slate-700">
        <li v-for="item in recommendations" :key="item">{{ item }}</li>
      </ul>
    </div>

    <div v-if="history.length" class="rounded-xl border border-slate-200 p-3">
      <h3 class="mb-2 text-sm font-semibold">История</h3>
      <div class="overflow-x-auto">
        <table class="min-w-full text-sm">
          <thead>
            <tr class="border-b border-slate-100 text-left text-slate-500">
              <th class="px-2 py-2">Audit</th>
              <th class="px-2 py-2">Score</th>
              <th class="px-2 py-2">Pages</th>
              <th class="px-2 py-2">Created</th>
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
