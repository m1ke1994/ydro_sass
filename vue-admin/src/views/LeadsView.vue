<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'

import { useLeadsStore } from '../stores/leads'
import { useSiteStore } from '../stores/site'

const route = useRoute()
const siteStore = useSiteStore()
const leadsStore = useLeadsStore()

const errorMessage = ref('')
const updatingLeadId = ref(null)
const selectedLead = ref(null)

const siteId = computed(() => Number(route.params.siteId))
const leads = computed(() => leadsStore.leads)

const statusOptions = [
  { value: 'new', label: 'Новая' },
  { value: 'in_progress', label: 'В работе' },
  { value: 'done', label: 'Завершена' },
  { value: 'archived', label: 'Архив' },
]

function formatDate(value) {
  if (!value) return '—'
  return new Date(value).toLocaleString('ru-RU')
}

async function load() {
  errorMessage.value = ''
  try {
    siteStore.selectSite(siteId.value)
    if (!siteStore.currentSite) {
      await siteStore.fetchSite(siteId.value)
    }
    await leadsStore.fetchLeads({ siteId: siteId.value })
  } catch (error) {
    errorMessage.value = error?.response?.data?.detail || 'Не удалось загрузить заявки.'
  }
}

async function updateStatus(lead, nextStatus) {
  if (!nextStatus || nextStatus === lead.status) return
  updatingLeadId.value = lead.id
  errorMessage.value = ''
  try {
    await leadsStore.patchLeadStatus(lead.id, nextStatus)
    if (selectedLead.value?.id === lead.id) {
      selectedLead.value = { ...selectedLead.value, status: nextStatus }
    }
  } catch (error) {
    errorMessage.value = error?.response?.data?.detail || 'Не удалось обновить статус.'
  } finally {
    updatingLeadId.value = null
  }
}

async function openLead(leadId) {
  try {
    selectedLead.value = await leadsStore.fetchLead(leadId)
  } catch (error) {
    errorMessage.value = error?.response?.data?.detail || 'Не удалось открыть заявку.'
  }
}

onMounted(load)
</script>

<template>
  <div class="space-y-6">
    <div class="flex flex-wrap items-center justify-between gap-3">
      <div>
        <RouterLink :to="`/sites/${siteId}/sections`" class="text-sm font-medium text-brand-700 hover:text-brand-800">← К разделам</RouterLink>
        <h1 class="mt-2 text-3xl font-semibold text-slate-900">Заявки: {{ siteStore.currentSite?.name || 'Сайт' }}</h1>
        <p class="mt-2 text-slate-500">Входящие заявки с публичного сайта.</p>
      </div>
      <button
        type="button"
        class="rounded-xl bg-brand-600 px-4 py-2 text-sm font-semibold text-white transition hover:bg-brand-700"
        @click="load"
      >
        Обновить
      </button>
    </div>

    <p v-if="errorMessage" class="whitespace-pre-wrap rounded-xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">
      {{ errorMessage }}
    </p>

    <section class="rounded-2xl border border-slate-200 bg-white p-4 shadow-soft sm:p-6">
      <p v-if="leadsStore.loading" class="text-sm text-slate-500">Загрузка заявок...</p>

      <p v-else-if="leads.length === 0" class="text-sm text-slate-500">Пока нет заявок.</p>

      <div v-else class="overflow-x-auto">
        <table class="min-w-full text-left text-sm">
          <thead class="text-xs uppercase tracking-wide text-slate-500">
            <tr class="border-b border-slate-200">
              <th class="px-3 py-3">Дата</th>
              <th class="px-3 py-3">Имя</th>
              <th class="px-3 py-3">Телефон</th>
              <th class="px-3 py-3">Email</th>
              <th class="px-3 py-3">Услуга</th>
              <th class="px-3 py-3">Сообщение</th>
              <th class="px-3 py-3">Статус</th>
              <th class="px-3 py-3">Детали</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="lead in leads" :key="lead.id" class="border-b border-slate-100">
              <td class="px-3 py-3 text-slate-700">{{ formatDate(lead.created_at) }}</td>
              <td class="px-3 py-3 font-medium text-slate-900">{{ lead.name }}</td>
              <td class="px-3 py-3 text-slate-700">{{ lead.phone }}</td>
              <td class="px-3 py-3 text-slate-700">{{ lead.email || '—' }}</td>
              <td class="px-3 py-3 text-slate-700">{{ lead.service_title || lead.service_type || '—' }}</td>
              <td class="max-w-[280px] truncate px-3 py-3 text-slate-700">{{ lead.message || '—' }}</td>
              <td class="px-3 py-3">
                <select
                  :value="lead.status"
                  class="rounded-lg border border-slate-300 px-2 py-1 text-sm"
                  :disabled="updatingLeadId === lead.id"
                  @change="updateStatus(lead, $event.target.value)"
                >
                  <option v-for="option in statusOptions" :key="option.value" :value="option.value">
                    {{ option.label }}
                  </option>
                </select>
              </td>
              <td class="px-3 py-3">
                <button
                  type="button"
                  class="rounded-lg border border-slate-300 px-3 py-1.5 text-xs font-semibold text-slate-700 transition hover:bg-slate-100"
                  @click="openLead(lead.id)"
                >
                  Открыть
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>

    <div v-if="selectedLead" class="rounded-2xl border border-slate-200 bg-white p-5 shadow-soft">
      <div class="flex items-start justify-between gap-3">
        <h2 class="text-xl font-semibold text-slate-900">Заявка #{{ selectedLead.id }}</h2>
        <button
          type="button"
          class="rounded-lg border border-slate-300 px-3 py-1.5 text-xs font-semibold text-slate-700 transition hover:bg-slate-100"
          @click="selectedLead = null"
        >
          Закрыть
        </button>
      </div>

      <div class="mt-4 grid gap-3 text-sm text-slate-700 sm:grid-cols-2">
        <p><span class="font-semibold">Дата:</span> {{ formatDate(selectedLead.created_at) }}</p>
        <p><span class="font-semibold">Статус:</span> {{ statusOptions.find((x) => x.value === selectedLead.status)?.label || selectedLead.status }}</p>
        <p><span class="font-semibold">Имя:</span> {{ selectedLead.name }}</p>
        <p><span class="font-semibold">Телефон:</span> {{ selectedLead.phone }}</p>
        <p><span class="font-semibold">Email:</span> {{ selectedLead.email || '—' }}</p>
        <p><span class="font-semibold">Форма:</span> {{ selectedLead.form_name || '—' }}</p>
        <p><span class="font-semibold">Тип услуги:</span> {{ selectedLead.service_type || '—' }}</p>
        <p><span class="font-semibold">Услуга:</span> {{ selectedLead.service_title || '—' }}</p>
        <p class="sm:col-span-2"><span class="font-semibold">Секция:</span> {{ selectedLead.section_key || '—' }}</p>
        <p class="sm:col-span-2"><span class="font-semibold">Source URL:</span> {{ selectedLead.source_url || '—' }}</p>
        <p class="sm:col-span-2"><span class="font-semibold">Сообщение:</span> {{ selectedLead.message || '—' }}</p>
      </div>
    </div>
  </div>
</template>
