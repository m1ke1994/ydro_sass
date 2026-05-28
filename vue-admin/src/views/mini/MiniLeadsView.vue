<script setup>
import { onMounted, ref } from 'vue'

import { miniLeadStatus, miniLeads } from '../../api/mini'

const leads = ref([])
const loading = ref(false)
const error = ref('')

async function loadLeads() {
  loading.value = true
  error.value = ''
  try {
    const data = await miniLeads()
    leads.value = Array.isArray(data) ? data : []
  } catch (e) {
    error.value = e?.response?.data?.detail || 'Не удалось загрузить заявки.'
  } finally {
    loading.value = false
  }
}

async function updateStatus(lead, status) {
  try {
    await miniLeadStatus(lead.id, status)
    lead.status = status
  } catch (e) {
    error.value = e?.response?.data?.detail || 'Не удалось обновить статус.'
  }
}

onMounted(loadLeads)
</script>

<template>
  <section class="rounded-2xl border border-slate-200 bg-white p-4">
    <div class="mb-3 flex items-center justify-between">
      <h2 class="text-base font-semibold text-slate-900">Заявки mini</h2>
      <button class="rounded-lg border border-slate-300 px-3 py-1.5 text-sm" @click="loadLeads">Обновить</button>
    </div>

    <p v-if="error" class="mb-3 rounded-xl border border-rose-200 bg-rose-50 p-3 text-sm text-rose-700">{{ error }}</p>
    <p v-if="loading" class="text-sm text-slate-500">Загрузка...</p>

    <div class="overflow-x-auto">
      <table class="min-w-full text-sm">
        <thead>
          <tr class="border-b border-slate-100 text-left text-slate-500">
            <th class="px-2 py-2">Дата</th>
            <th class="px-2 py-2">Имя</th>
            <th class="px-2 py-2">Телефон</th>
            <th class="px-2 py-2">Источник</th>
            <th class="px-2 py-2">Статус</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="lead in leads" :key="lead.id" class="border-b border-slate-50">
            <td class="px-2 py-2">{{ lead.created_at }}</td>
            <td class="px-2 py-2">{{ lead.name || '—' }}</td>
            <td class="px-2 py-2">{{ lead.phone || '—' }}</td>
            <td class="px-2 py-2">{{ lead.source_url || '—' }}</td>
            <td class="px-2 py-2">
              <select
                class="rounded border border-slate-300 px-2 py-1"
                :value="lead.status"
                @change="updateStatus(lead, $event.target.value)"
              >
                <option value="new">new</option>
                <option value="in_progress">in_progress</option>
                <option value="closed">closed</option>
              </select>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </section>
</template>
