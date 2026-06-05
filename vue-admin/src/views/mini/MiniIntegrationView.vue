<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { CheckCircle2, MessageCircle, Send, Unplug } from '@lucide/vue'

import { miniTelegramDisconnect, miniTelegramSendTest, miniTelegramStatus } from '../../api/mini'
import { disconnectSiteTelegramRequest, getSiteTelegramRequest, sendSiteTelegramTestRequest } from '../../api/site'

const route = useRoute()
const loading = ref(false)
const action = ref('')
const error = ref('')
const success = ref('')
const telegram = ref(null)
const connected = computed(() => Boolean(telegram.value?.connected))
const siteId = computed(() => Number(route.params.siteId || 0))
const isSiteMode = computed(() => siteId.value > 0)

async function load() {
  loading.value = true
  error.value = ''
  try {
    if (isSiteMode.value) {
      const { data } = await getSiteTelegramRequest(siteId.value)
      telegram.value = data
    } else {
      telegram.value = await miniTelegramStatus()
    }
  }
  catch (e) { error.value = e?.response?.data?.detail || 'Не удалось проверить подключение Telegram.' }
  finally { loading.value = false }
}

function connect() {
  if (!telegram.value?.telegram_connect_url) {
    error.value = 'Ссылка подключения пока недоступна. Обновите страницу позже.'
    return
  }
  window.open(telegram.value.telegram_connect_url, '_blank', 'noopener,noreferrer')
}

async function copyCommand() {
  if (!telegram.value?.start_command) return
  action.value = 'copy'; error.value = ''; success.value = ''
  try {
    await navigator.clipboard.writeText(telegram.value.start_command)
    success.value = 'Команда скопирована.'
  } catch {
    error.value = 'Не удалось скопировать команду. Выделите ее вручную.'
  } finally {
    action.value = ''
  }
}

async function sendTest() {
  action.value = 'test'; error.value = ''; success.value = ''
  try {
    const result = isSiteMode.value ? await sendSiteTelegramTestRequest(siteId.value) : await miniTelegramSendTest()
    const data = result?.data || result
    success.value = data?.detail || 'Тестовое сообщение отправлено.'
  }
  catch (e) { error.value = e?.response?.data?.detail || 'Не удалось отправить тестовое сообщение.' }
  finally { action.value = '' }
}

async function disconnect() {
  action.value = 'disconnect'; error.value = ''; success.value = ''
  try {
    const result = isSiteMode.value ? await disconnectSiteTelegramRequest(siteId.value) : await miniTelegramDisconnect()
    const data = result?.data || result
    success.value = data?.detail || 'Telegram отключен.'
    await load()
  }
  catch (e) { error.value = e?.response?.data?.detail || 'Не удалось отключить Telegram.' }
  finally { action.value = '' }
}

onMounted(load)
</script>

<template>
  <div class="page-stack">
    <header class="page-heading">
      <p class="eyebrow">Мгновенные уведомления</p>
      <h1>Telegram</h1>
      <p>Получайте новые заявки в подключенный Telegram-чат.</p>
    </header>
    <p v-if="error" class="notice-error">{{ error }}</p>
    <p v-if="success" class="notice-success">{{ success }}</p>
    <section v-if="loading" class="empty-state"><span class="loading-dot" /><p>Проверяем подключение...</p></section>
    <template v-else>
      <section class="surface">
        <div class="flex flex-col gap-5 sm:flex-row sm:items-center sm:justify-between">
          <div class="flex items-start gap-3">
            <span class="inline-flex h-12 w-12 shrink-0 items-center justify-center rounded-lg" :class="connected ? 'bg-emerald-50 text-emerald-700' : 'bg-slate-100 text-slate-500'">
              <CheckCircle2 v-if="connected" :size="24" /><MessageCircle v-else :size="24" />
            </span>
            <div>
              <h2 class="text-lg font-semibold text-slate-950">{{ connected ? 'Telegram подключен' : 'Telegram не подключен' }}</h2>
              <p class="mt-1 text-sm leading-6 text-slate-600">{{ connected ? 'Новые заявки будут приходить в ваш чат.' : 'Подключите чат, чтобы сразу узнавать о новых заявках.' }}</p>
            </div>
          </div>
          <button v-if="!connected && telegram?.telegram_connect_url" type="button" class="action-button-primary" @click="connect">
            <MessageCircle :size="18" />Подключить Telegram
          </button>
        </div>
      </section>

      <section class="surface">
        <div class="section-heading"><div><h2>Как это работает</h2><p>Подключение занимает меньше минуты.</p></div></div>
        <ol class="grid gap-3 sm:grid-cols-3">
          <li v-for="(text, index) in ['Откройте бота', 'Отправьте команду /start с токеном', 'Вернитесь сюда и отправьте тест']" :key="text" class="rounded-lg bg-slate-50 p-4 text-sm leading-6 text-slate-700">
            <strong class="mb-2 block text-cyan-800">Шаг {{ index + 1 }}</strong>{{ text }}
          </li>
        </ol>
        <div v-if="!connected && telegram?.start_command" class="mt-4 rounded-lg border border-slate-200 bg-slate-50 p-4">
          <p class="text-sm font-semibold text-slate-800">Команда для подключения</p>
          <code class="mt-2 block overflow-x-auto rounded-lg bg-white px-3 py-2 text-sm text-slate-800">{{ telegram.start_command }}</code>
          <div class="mt-3 flex flex-col gap-2 sm:flex-row">
            <button v-if="telegram?.telegram_connect_url" type="button" class="action-button-primary" @click="connect"><MessageCircle :size="17" />Открыть бота</button>
            <button type="button" class="action-button-secondary" :disabled="Boolean(action)" @click="copyCommand">Скопировать команду</button>
          </div>
          <p v-if="!telegram?.telegram_bot_username" class="mt-3 text-sm text-amber-700">В env не указан TELEGRAM_BOT_USERNAME, поэтому автоматическая ссылка на бота недоступна.</p>
        </div>
      </section>

      <section v-if="connected" class="surface">
        <div class="section-heading"><div><h2>Проверка подключения</h2><p>Тестовое сообщение отправляется только после нажатия кнопки.</p></div></div>
        <div class="flex flex-col gap-2 sm:flex-row">
          <button type="button" class="action-button-primary" :disabled="Boolean(action)" @click="sendTest"><Send :size="17" />{{ action === 'test' ? 'Отправляем...' : 'Отправить тестовое сообщение' }}</button>
          <button type="button" class="action-button-danger" :disabled="Boolean(action)" @click="disconnect"><Unplug :size="17" />Отключить Telegram</button>
        </div>
      </section>
    </template>
  </div>
</template>
