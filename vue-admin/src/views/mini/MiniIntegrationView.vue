<script setup>
import { onMounted, ref } from 'vue'

import {
  miniSettings,
  miniTelegramDisconnect,
  miniTelegramSendTest,
  miniTelegramStatus,
} from '../../api/mini'

const loading = ref(false)
const actionLoading = ref(false)
const error = ref('')
const success = ref('')
const settings = ref(null)
const telegram = ref(null)

async function loadData() {
  loading.value = true
  error.value = ''
  try {
    const [settingsPayload, telegramPayload] = await Promise.all([
      miniSettings(),
      miniTelegramStatus(),
    ])
    settings.value = settingsPayload
    telegram.value = telegramPayload
  } catch (e) {
    error.value = e?.response?.data?.detail || 'Не удалось загрузить данные интеграции.'
  } finally {
    loading.value = false
  }
}

function openTelegramConnect() {
  const url = telegram.value?.telegram_connect_url
  if (!url) {
    error.value = 'Не найден URL для подключения Telegram.'
    return
  }
  window.open(url, '_blank', 'noopener,noreferrer')
}

async function sendTestMessage() {
  actionLoading.value = true
  error.value = ''
  success.value = ''
  try {
    const response = await miniTelegramSendTest()
    success.value = response?.detail || 'Тестовое сообщение отправлено.'
  } catch (e) {
    error.value = e?.response?.data?.detail || 'Не удалось отправить тестовое сообщение.'
  } finally {
    actionLoading.value = false
  }
}

async function disconnectTelegram() {
  actionLoading.value = true
  error.value = ''
  success.value = ''
  try {
    const response = await miniTelegramDisconnect()
    success.value = response?.detail || 'Telegram отключен.'
    await loadData()
  } catch (e) {
    error.value = e?.response?.data?.detail || 'Не удалось отключить Telegram.'
  } finally {
    actionLoading.value = false
  }
}

onMounted(loadData)
</script>

<template>
  <section class="space-y-4 rounded-2xl border border-slate-200 bg-white p-4">
    <h2 class="text-base font-semibold text-slate-900">Интеграции mini</h2>

    <p v-if="loading" class="text-sm text-slate-500">Загрузка...</p>
    <p v-if="error" class="rounded-xl border border-rose-200 bg-rose-50 p-3 text-sm text-rose-700">{{ error }}</p>
    <p v-if="success" class="rounded-xl border border-emerald-200 bg-emerald-50 p-3 text-sm text-emerald-700">{{ success }}</p>

    <div class="rounded-xl border border-slate-200 bg-slate-50 p-3 text-sm">
      <p><strong>API key:</strong> {{ settings?.api_key || '—' }}</p>
      <p class="mt-2"><strong>Тег трекера:</strong></p>
      <pre class="mt-1 overflow-x-auto whitespace-pre-wrap text-xs">{{ settings?.public_script_tag || '—' }}</pre>
      <p class="mt-2"><strong>URL скрипта:</strong> {{ settings?.tracker_script_url || '—' }}</p>
    </div>

    <div class="rounded-xl border border-slate-200 p-3 text-sm">
      <h3 class="font-semibold text-slate-900">Telegram</h3>
      <p class="mt-2">
        <strong>Статус:</strong>
        {{ telegram?.connected ? 'Telegram подключен' : 'Telegram не подключен' }}
      </p>

      <div class="mt-3 flex flex-wrap gap-2">
        <button
          class="rounded-xl bg-brand-600 px-4 py-2 text-sm font-semibold text-white hover:bg-brand-700 disabled:opacity-70"
          :disabled="actionLoading || !telegram?.telegram_connect_url"
          @click="openTelegramConnect"
        >
          Подключить Telegram
        </button>
        <button
          class="rounded-xl border border-slate-300 px-4 py-2 text-sm disabled:opacity-70"
          :disabled="actionLoading || !telegram?.connected"
          @click="sendTestMessage"
        >
          Отправить тестовое сообщение
        </button>
        <button
          class="rounded-xl border border-rose-300 px-4 py-2 text-sm text-rose-700 disabled:opacity-70"
          :disabled="actionLoading || !telegram?.connected"
          @click="disconnectTelegram"
        >
          Отключить Telegram
        </button>
      </div>

      <details class="mt-3">
        <summary class="cursor-pointer text-xs text-slate-500">Технические детали</summary>
        <p class="mt-2 break-all text-xs text-slate-500">
          Connect URL: {{ telegram?.telegram_connect_url || '—' }}
        </p>
      </details>
    </div>

    <div class="rounded-xl border border-slate-200 p-3 text-sm">
      <p class="font-medium text-slate-800">Отправка лида с сайта</p>
      <pre class="mt-2 overflow-x-auto whitespace-pre-wrap text-xs">POST /api/mini/public/lead/
Header: X-API-KEY: {{ settings?.api_key || 'YOUR_API_KEY' }}
Body: {"name":"Иван","phone":"+7999...","message":"Нужна консультация"}</pre>
    </div>
  </section>
</template>
