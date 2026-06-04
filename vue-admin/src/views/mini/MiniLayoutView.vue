<script setup>
import { computed, onMounted, ref } from 'vue'

import { miniSubscriptionCreatePayment, miniSubscriptionPlans, miniSubscriptionStatus } from '../../api/mini'

const status = ref(null)
const plans = ref([])
const loading = ref(false)
const paying = ref(false)
const error = ref('')

const isActive = computed(() => status.value?.status === 'active')
const isTrial = computed(() => Boolean(status.value?.is_trial))
const billingEnabled = computed(() => Boolean(status.value?.billing_enabled))
const showBillingWarning = computed(() => billingEnabled.value && !isActive.value)

async function loadSubscription() {
  loading.value = true
  error.value = ''
  try {
    const [statusData, plansData] = await Promise.all([miniSubscriptionStatus(), miniSubscriptionPlans()])
    status.value = statusData
    plans.value = Array.isArray(plansData) ? plansData : []
  } catch (e) {
    error.value = e?.response?.data?.detail || 'Не удалось загрузить статус подписки.'
  } finally {
    loading.value = false
  }
}

async function payNow() {
  if (paying.value) return
  paying.value = true
  error.value = ''
  try {
    const plan = plans.value[0]
    if (!plan?.id) {
      error.value = 'Нет активных тарифов.'
      return
    }

    const payment = await miniSubscriptionCreatePayment(plan.id)
    const redirectUrl = payment?.checkout_url || payment?.confirmation_url
    if (!redirectUrl) {
      error.value = 'Платёж создан, но ссылка не получена.'
      return
    }

    window.location.href = redirectUrl
  } catch (e) {
    error.value = e?.response?.data?.detail || 'Не удалось запустить оплату.'
  } finally {
    paying.value = false
  }
}

onMounted(loadSubscription)
</script>

<template>
  <section class="space-y-4">
    <div class="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
      <h1 class="text-xl font-semibold text-slate-900">Дополнительные инструменты</h1>
      <p class="mt-1 text-sm text-slate-500">Отчёты, настройки и дополнительные возможности сайта.</p>
    </div>

    <div v-if="loading" class="rounded-2xl border border-slate-200 bg-white p-4 text-sm text-slate-500">
      Проверяем подписку...
    </div>

    <div v-else-if="showBillingWarning" class="rounded-2xl border border-amber-200 bg-amber-50 p-4">
      <p class="text-sm font-medium text-amber-900">Подписка не активна.</p>
      <p class="mt-1 text-sm text-amber-800">Для доступа к аналитике, SEO и отчётам нужна активная подписка.</p>
      <button
        class="mt-3 inline-flex items-center rounded-xl bg-amber-600 px-4 py-2 text-sm font-semibold text-white hover:bg-amber-700 disabled:opacity-70"
        :disabled="paying"
        @click="payNow"
      >
        {{ paying ? 'Переход...' : 'Оплатить' }}
      </button>
      <p v-if="error" class="mt-2 text-sm text-rose-700">{{ error }}</p>
    </div>

    <div v-else-if="isTrial" class="rounded-2xl border border-cyan-200 bg-cyan-50 p-4 text-sm text-cyan-900">
      Демо-период активен до: {{ status?.paid_until || 'не указано' }}
    </div>

    <div class="rounded-2xl border border-slate-200 bg-white p-2 shadow-sm">
      <nav class="flex flex-wrap gap-2">
        <RouterLink class="rounded-lg px-3 py-2 text-sm font-medium text-slate-600 hover:bg-slate-100" active-class="bg-brand-50 text-brand-700" to="/mini">Статистика</RouterLink>
        <RouterLink class="rounded-lg px-3 py-2 text-sm font-medium text-slate-600 hover:bg-slate-100" active-class="bg-brand-50 text-brand-700" to="/mini/leads">Заявки</RouterLink>
        <RouterLink class="rounded-lg px-3 py-2 text-sm font-medium text-slate-600 hover:bg-slate-100" active-class="bg-brand-50 text-brand-700" to="/mini/seo">Проверка сайта</RouterLink>
        <RouterLink class="rounded-lg px-3 py-2 text-sm font-medium text-slate-600 hover:bg-slate-100" active-class="bg-brand-50 text-brand-700" to="/mini/reports">Отчёты</RouterLink>
        <RouterLink class="rounded-lg px-3 py-2 text-sm font-medium text-slate-600 hover:bg-slate-100" active-class="bg-brand-50 text-brand-700" to="/mini/settings">Настройки</RouterLink>
        <RouterLink class="rounded-lg px-3 py-2 text-sm font-medium text-slate-600 hover:bg-slate-100" active-class="bg-brand-50 text-brand-700" to="/mini/integration">Telegram</RouterLink>
      </nav>
    </div>

    <RouterView />
  </section>
</template>
