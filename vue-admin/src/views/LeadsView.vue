<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { Inbox, RefreshCw, X } from '@lucide/vue'

import { useLeadsStore } from '../stores/leads'
import { useSiteStore } from '../stores/site'

const route = useRoute()
const siteStore = useSiteStore()
const leadsStore = useLeadsStore()
const error = ref('')
const updatingLeadId = ref(null)
const selectedLead = ref(null)
const statusFilter = ref('')

const siteId = computed(() => Number(route.params.siteId))
const leads = computed(() => leadsStore.leads)
const statusOptions = [
  { value: 'new', label: 'Новая', class: 'status-danger' },
  { value: 'in_progress', label: 'В работе', class: 'status-warning' },
  { value: 'done', label: 'Завершена', class: 'status-success' },
  { value: 'archived', label: 'Спам', class: 'status-neutral' },
]

function statusOption(value) {
  return statusOptions.find((item) => item.value === value) || statusOptions[0]
}

function formatDate(value) {
  if (!value) return 'Не указано'
  return new Intl.DateTimeFormat('ru-RU', { dateStyle: 'medium', timeStyle: 'short' }).format(new Date(value))
}

function pageLabel(value) {
  if (!value) return 'Не указано'
  try {
    const url = new URL(value)
    return url.pathname || '/'
  } catch {
    return value
  }
}

async function load() {
  error.value = ''
  try {
    siteStore.selectSite(siteId.value)
    if (!siteStore.currentSite) await siteStore.fetchSite(siteId.value)
    await leadsStore.fetchLeads({ siteId: siteId.value, status: statusFilter.value })
  } catch (e) {
    error.value = e?.response?.data?.detail || 'Не удалось загрузить заявки. Попробуйте обновить страницу.'
  }
}

async function updateStatus(lead, status) {
  if (!status || status === lead.status) return
  updatingLeadId.value = lead.id
  error.value = ''
  try {
    const updated = await leadsStore.patchLeadStatus(lead.id, status)
    if (selectedLead.value?.id === lead.id) selectedLead.value = updated
  } catch (e) {
    error.value = e?.response?.data?.detail || 'Не удалось изменить статус заявки.'
  } finally {
    updatingLeadId.value = null
  }
}

async function openLead(leadId) {
  try {
    selectedLead.value = await leadsStore.fetchLead(leadId)
  } catch (e) {
    error.value = e?.response?.data?.detail || 'Не удалось открыть заявку.'
  }
}

onMounted(load)
</script>

<template>
  <div class="page-stack">
    <header class="page-heading page-heading-actions">
      <div>
        <p class="eyebrow">Обращения клиентов</p>
        <h1>Заявки</h1>
        <p>Все обращения с сайта {{ siteStore.currentSite?.name || '' }} в одном месте.</p>
      </div>
      <div class="flex flex-col gap-2 sm:flex-row">
        <select v-model="statusFilter" class="form-control sm:w-44" @change="load">
          <option value="">Все статусы</option>
          <option v-for="option in statusOptions" :key="option.value" :value="option.value">{{ option.label }}</option>
        </select>
        <button type="button" class="action-button-secondary" @click="load">
          <RefreshCw :size="17" />
          Обновить
        </button>
      </div>
    </header>

    <p v-if="error" class="notice-error">{{ error }}</p>
    <section v-if="leadsStore.loading" class="empty-state"><span class="loading-dot" /><p>Загружаем заявки...</p></section>
    <section v-else-if="leads.length === 0" class="empty-state">
      <Inbox :size="30" />
      <h2>Заявок пока нет</h2>
      <p>Когда посетитель заполнит форму на сайте, его обращение появится здесь.</p>
    </section>

    <template v-else>
      <section class="surface hidden overflow-x-auto lg:block">
        <table class="data-table">
          <thead>
            <tr>
              <th>Дата</th>
              <th>Клиент</th>
              <th>Контакты</th>
              <th>Комментарий</th>
              <th>Страница</th>
              <th>Статус</th>
              <th><span class="sr-only">Действия</span></th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="lead in leads" :key="lead.id">
              <td class="whitespace-nowrap">{{ formatDate(lead.created_at) }}</td>
              <td class="font-semibold text-slate-950">{{ lead.name || 'Имя не указано' }}</td>
              <td>
                <a v-if="lead.phone" :href="`tel:${lead.phone}`" class="block font-medium text-cyan-800">{{ lead.phone }}</a>
                <a v-if="lead.email" :href="`mailto:${lead.email}`" class="mt-1 block text-xs text-slate-500">{{ lead.email }}</a>
              </td>
              <td class="max-w-64"><p class="line-clamp-2">{{ lead.message || 'Без комментария' }}</p></td>
              <td>{{ pageLabel(lead.source_url) }}</td>
              <td>
                <select :value="lead.status" class="form-control min-w-36" :disabled="updatingLeadId === lead.id" @change="updateStatus(lead, $event.target.value)">
                  <option v-for="option in statusOptions" :key="option.value" :value="option.value">{{ option.label }}</option>
                </select>
              </td>
              <td><button type="button" class="action-button-secondary min-h-9 px-3 py-1.5" @click="openLead(lead.id)">Подробнее</button></td>
            </tr>
          </tbody>
        </table>
      </section>

      <section class="grid gap-3 lg:hidden">
        <article v-for="lead in leads" :key="lead.id" class="surface">
          <div class="flex items-start justify-between gap-3">
            <div class="min-w-0">
              <p class="truncate font-semibold text-slate-950">{{ lead.name || 'Имя не указано' }}</p>
              <p class="mt-1 text-xs text-slate-500">{{ formatDate(lead.created_at) }}</p>
            </div>
            <span class="status-badge" :class="statusOption(lead.status).class">{{ statusOption(lead.status).label }}</span>
          </div>
          <div class="mt-4 grid gap-2 text-sm text-slate-600">
            <a v-if="lead.phone" :href="`tel:${lead.phone}`" class="font-medium text-cyan-800">{{ lead.phone }}</a>
            <a v-if="lead.email" :href="`mailto:${lead.email}`">{{ lead.email }}</a>
            <p>{{ lead.message || 'Без комментария' }}</p>
            <p class="text-xs text-slate-500">Страница: {{ pageLabel(lead.source_url) }}</p>
          </div>
          <div class="mt-4 flex gap-2">
            <select :value="lead.status" class="form-control flex-1" @change="updateStatus(lead, $event.target.value)">
              <option v-for="option in statusOptions" :key="option.value" :value="option.value">{{ option.label }}</option>
            </select>
            <button type="button" class="action-button-secondary" @click="openLead(lead.id)">Подробнее</button>
          </div>
        </article>
      </section>
    </template>

    <div v-if="selectedLead" class="fixed inset-0 z-50 flex items-end bg-slate-950/45 sm:items-center sm:justify-center sm:p-5" @click.self="selectedLead = null">
      <section class="max-h-[92vh] w-full overflow-y-auto rounded-t-lg bg-white p-5 shadow-2xl sm:max-w-2xl sm:rounded-lg">
        <div class="flex items-start justify-between gap-3">
          <div>
            <p class="eyebrow">Карточка заявки</p>
            <h2 class="mt-1 text-xl font-semibold text-slate-950">{{ selectedLead.name || 'Имя не указано' }}</h2>
          </div>
          <button type="button" class="icon-button" aria-label="Закрыть" @click="selectedLead = null"><X :size="19" /></button>
        </div>
        <div class="mt-5 grid gap-4 text-sm sm:grid-cols-2">
          <p><strong class="block text-slate-500">Дата</strong>{{ formatDate(selectedLead.created_at) }}</p>
          <p><strong class="block text-slate-500">Статус</strong>{{ statusOption(selectedLead.status).label }}</p>
          <p><strong class="block text-slate-500">Телефон</strong>{{ selectedLead.phone || 'Не указано' }}</p>
          <p><strong class="block text-slate-500">Электронная почта</strong>{{ selectedLead.email || 'Не указано' }}</p>
          <p><strong class="block text-slate-500">Форма</strong>{{ selectedLead.form_name || 'Не указано' }}</p>
          <p><strong class="block text-slate-500">Источник</strong>{{ pageLabel(selectedLead.source_url) }}</p>
          <p class="sm:col-span-2"><strong class="block text-slate-500">Комментарий</strong>{{ selectedLead.message || 'Не указано' }}</p>
        </div>
      </section>
    </div>
  </div>
</template>
