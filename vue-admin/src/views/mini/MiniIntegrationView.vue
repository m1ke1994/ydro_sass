<script setup>
import { onMounted, ref } from 'vue'

import { miniSettings } from '../../api/mini'

const loading = ref(false)
const error = ref('')
const settings = ref(null)

onMounted(async () => {
  loading.value = true
  try {
    settings.value = await miniSettings()
  } catch (e) {
    error.value = e?.response?.data?.detail || 'Не удалось загрузить данные интеграции.'
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <section class="space-y-4 rounded-2xl border border-slate-200 bg-white p-4">
    <h2 class="text-base font-semibold text-slate-900">Интеграция mini</h2>

    <p v-if="loading" class="text-sm text-slate-500">Загрузка...</p>
    <p v-if="error" class="rounded-xl border border-rose-200 bg-rose-50 p-3 text-sm text-rose-700">{{ error }}</p>

    <div class="rounded-xl border border-slate-200 bg-slate-50 p-3 text-sm">
      <p><strong>API key:</strong> {{ settings?.api_key || '—' }}</p>
      <p class="mt-2"><strong>Тег трекера:</strong></p>
      <pre class="mt-1 overflow-x-auto whitespace-pre-wrap text-xs">{{ settings?.public_script_tag || '—' }}</pre>
      <p class="mt-2"><strong>URL скрипта:</strong> {{ settings?.tracker_script_url || '—' }}</p>
    </div>

    <div class="rounded-xl border border-slate-200 p-3 text-sm">
      <p class="font-medium text-slate-800">Отправка лида с сайта</p>
      <pre class="mt-2 overflow-x-auto whitespace-pre-wrap text-xs">POST /api/mini/public/lead/
Header: X-API-KEY: {{ settings?.api_key || 'YOUR_API_KEY' }}
Body: {"name":"Иван","phone":"+7999...","message":"Нужна консультация"}</pre>
    </div>
  </section>
</template>
