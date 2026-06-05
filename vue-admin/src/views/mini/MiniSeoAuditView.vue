<script setup>
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { Download, SearchCheck } from '@lucide/vue'

import { miniSeoDetail, miniSeoExport, miniSeoIssues, miniSeoLatest, miniSeoStart } from '../../api/mini'
import { useSiteStore } from '../../stores/site'

const route = useRoute()
const siteStore = useSiteStore()
const domain = ref('')
const loading = ref(false)
const downloading = ref(false)
const error = ref('')
const latest = ref(null)
const detail = ref(null)
const issues = ref([])
let timer = null

const siteId = computed(() => Number(route.params.siteId || 0))
const auditId = computed(() => latest.value?.audit_id || detail.value?.audit_id)
const running = computed(() => ['pending', 'running'].includes(String(detail.value?.status || latest.value?.status || '').toLowerCase()))
const score = computed(() => Number(detail.value?.score ?? latest.value?.score ?? 0))

function statusText() {
  const status = String(detail.value?.status || latest.value?.status || '').toLowerCase()
  return { pending: 'Ждет запуска', running: 'Проверяем сайт', done: 'Проверка завершена', completed: 'Проверка завершена', failed: 'Не удалось проверить сайт', error: 'Не удалось проверить сайт' }[status] || 'Проверка не запускалась'
}

function severityInfo(value) {
  return {
    high: { label: 'Критично', class: 'status-danger' },
    medium: { label: 'Важно', class: 'status-warning' },
    low: { label: 'Рекомендация', class: 'status-neutral' },
  }[value] || { label: 'Рекомендация', class: 'status-neutral' }
}

async function loadAudit(id) {
  detail.value = await miniSeoDetail(id)
  const result = await miniSeoIssues(id)
  issues.value = result?.rows || []
}

function stopPolling() {
  if (timer) clearInterval(timer)
  timer = null
}

function startPolling() {
  stopPolling()
  timer = setInterval(async () => {
    try {
      await loadAudit(auditId.value)
      if (!running.value) stopPolling()
    } catch { stopPolling() }
  }, 4000)
}

async function findLatest() {
  if (!domain.value.trim()) { error.value = 'Введите домен сайта.'; return }
  loading.value = true; error.value = ''
  try {
    latest.value = await miniSeoLatest(domain.value.trim())
    if (latest.value?.audit_id) {
      await loadAudit(latest.value.audit_id)
      if (running.value) startPolling()
    }
  } catch (e) { error.value = e?.response?.data?.detail || 'Для этого домена еще нет готовой проверки.' }
  finally { loading.value = false }
}

async function startAudit() {
  if (!domain.value.trim()) { error.value = 'Введите домен сайта.'; return }
  loading.value = true; error.value = ''; issues.value = []
  try {
    latest.value = await miniSeoStart(domain.value.trim())
    await loadAudit(latest.value.audit_id)
    if (running.value) startPolling()
  } catch (e) { error.value = e?.response?.data?.detail || 'Не удалось запустить проверку сайта.' }
  finally { loading.value = false }
}

async function downloadPdf() {
  if (!auditId.value) return
  downloading.value = true; error.value = ''
  try {
    const blob = await miniSeoExport(auditId.value)
    const href = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = href; link.download = `seo-audit-${domain.value}.pdf`; link.click()
    URL.revokeObjectURL(href)
  } catch (e) { error.value = e?.response?.data?.detail || 'Не удалось скачать PDF-отчет.' }
  finally { downloading.value = false }
}

onMounted(async () => {
  if (siteId.value) {
    siteStore.selectSite(siteId.value)
    if (!siteStore.currentSite) await siteStore.fetchSite(siteId.value)
    domain.value = siteStore.currentSite?.domain || ''
  }
})
onUnmounted(stopPolling)
</script>

<template>
  <div class="page-stack">
    <header class="page-heading">
      <p class="eyebrow">Проверка сайта</p>
      <h1>SEO-аудит</h1>
      <p>Найдите проблемы, которые мешают сайту быть заметнее в поиске.</p>
    </header>

    <section class="surface">
      <label class="text-sm font-semibold text-slate-800" for="seo-domain">Домен сайта</label>
      <div class="mt-2 flex flex-col gap-2 sm:flex-row">
        <input id="seo-domain" v-model="domain" class="form-control flex-1" placeholder="example.com">
        <button type="button" class="action-button-primary" :disabled="loading" @click="startAudit"><SearchCheck :size="18" />{{ loading ? 'Проверяем...' : 'Проверить сайт' }}</button>
        <button type="button" class="action-button-secondary" :disabled="loading" @click="findLatest">Показать прошлую проверку</button>
      </div>
    </section>

    <p v-if="error" class="notice-error">{{ error }}</p>
    <section v-if="running" class="notice-info">Проверяем страницы сайта. Результаты обновятся автоматически.</section>

    <template v-if="detail || latest">
      <section class="grid gap-4 sm:grid-cols-[220px_1fr]">
        <article class="surface flex min-h-44 flex-col items-center justify-center text-center">
          <p class="text-sm text-slate-500">Оценка SEO</p>
          <p class="mt-2 text-5xl font-semibold" :class="score >= 80 ? 'text-emerald-600' : score >= 50 ? 'text-amber-600' : 'text-rose-600'">{{ score }}</p>
          <p class="mt-2 text-sm text-slate-600">{{ statusText() }}</p>
        </article>
        <article class="surface">
          <div class="section-heading">
            <div><h2>Результат проверки</h2><p>Исправляйте проблемы сверху вниз.</p></div>
            <button type="button" class="action-button-secondary" :disabled="!auditId || downloading" @click="downloadPdf"><Download :size="17" />{{ downloading ? 'Готовим...' : 'Скачать PDF' }}</button>
          </div>
          <div class="grid grid-cols-2 gap-3 sm:grid-cols-3">
            <div class="rounded-lg bg-slate-50 p-3"><p class="text-xs text-slate-500">Проверено страниц</p><strong class="mt-1 block text-xl">{{ detail?.pages_count || 0 }}</strong></div>
            <div class="rounded-lg bg-rose-50 p-3"><p class="text-xs text-rose-600">Критичных проблем</p><strong class="mt-1 block text-xl text-rose-700">{{ detail?.breakdown?.high_issues || 0 }}</strong></div>
            <div class="rounded-lg bg-amber-50 p-3"><p class="text-xs text-amber-700">Важных проблем</p><strong class="mt-1 block text-xl text-amber-800">{{ detail?.breakdown?.medium_issues || 0 }}</strong></div>
          </div>
        </article>
      </section>

      <section>
        <div class="section-heading"><div><h2>Найденные проблемы</h2><p>Простые объяснения и рекомендации по исправлению.</p></div></div>
        <div v-if="issues.length" class="grid gap-3">
          <article v-for="issue in issues" :key="issue.id" class="surface">
            <div class="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
              <div>
                <span class="status-badge" :class="severityInfo(issue.severity).class">{{ severityInfo(issue.severity).label }}</span>
                <h3 class="mt-3 font-semibold text-slate-950">{{ issue.issue_title || 'Проблема на странице' }}</h3>
                <p class="mt-2 break-words text-sm text-slate-500">{{ issue.page_url || domain }}</p>
                <p class="mt-3 text-sm leading-6 text-slate-700">{{ issue.recommendation || 'Проверьте страницу и исправьте найденную проблему.' }}</p>
              </div>
            </div>
          </article>
        </div>
        <div v-else class="empty-state"><SearchCheck :size="30" /><h2>Проблем не найдено</h2><p>Или проверка еще выполняется.</p></div>
      </section>
    </template>
  </div>
</template>
