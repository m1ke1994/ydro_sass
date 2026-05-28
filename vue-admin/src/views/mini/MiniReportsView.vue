<script setup>
import { onMounted, ref } from 'vue'

import { miniReportDaily, miniReportSendNow, miniSetReportDaily } from '../../api/mini'

const loading = ref(false)
const sending = ref(false)
const enabled = ref(false)
const message = ref('')
const error = ref('')

async function loadDaily() {
  loading.value = true
  error.value = ''
  try {
    const data = await miniReportDaily()
    enabled.value = Boolean(data?.daily_pdf_enabled)
  } catch (e) {
    error.value = e?.response?.data?.detail || 'Не удалось загрузить настройки отчётов.'
  } finally {
    loading.value = false
  }
}

async function saveDaily() {
  error.value = ''
  try {
    const data = await miniSetReportDaily(enabled.value)
    enabled.value = Boolean(data?.daily_pdf_enabled)
    message.value = 'Настройка сохранена.'
  } catch (e) {
    error.value = e?.response?.data?.detail || 'Не удалось сохранить настройку.'
  }
}

async function sendNow() {
  sending.value = true
  error.value = ''
  message.value = ''
  try {
    const data = await miniReportSendNow()
    message.value = data?.detail || 'Отчёт отправлен.'
  } catch (e) {
    error.value = e?.response?.data?.detail || 'Не удалось отправить отчёт.'
  } finally {
    sending.value = false
  }
}

onMounted(loadDaily)
</script>

<template>
  <section class="space-y-4 rounded-2xl border border-slate-200 bg-white p-4">
    <h2 class="text-base font-semibold text-slate-900">Отчёты mini</h2>
    <p v-if="loading" class="text-sm text-slate-500">Загрузка...</p>
    <p v-if="error" class="rounded-xl border border-rose-200 bg-rose-50 p-3 text-sm text-rose-700">{{ error }}</p>
    <p v-if="message" class="rounded-xl border border-emerald-200 bg-emerald-50 p-3 text-sm text-emerald-700">{{ message }}</p>

    <label class="flex items-center gap-2 text-sm">
      <input v-model="enabled" type="checkbox">
      Ежедневный PDF в Telegram
    </label>

    <div class="flex flex-wrap gap-2">
      <button class="rounded-xl border border-slate-300 px-4 py-2 text-sm" @click="saveDaily">Сохранить</button>
      <button class="rounded-xl bg-brand-600 px-4 py-2 text-sm font-semibold text-white hover:bg-brand-700 disabled:opacity-70" :disabled="sending" @click="sendNow">
        {{ sending ? 'Отправляем...' : 'Отправить сейчас' }}
      </button>
    </div>
  </section>
</template>
