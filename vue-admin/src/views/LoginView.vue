<script setup>
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'

import { useAuthStore } from '../stores/auth'

const router = useRouter()
const authStore = useAuthStore()

const form = reactive({
  username: 'meditation_owner',
  password: 'test-test',
})

const loading = ref(false)
const errorMessage = ref('')

async function submit() {
  loading.value = true
  errorMessage.value = ''

  try {
    await authStore.login({
      username: form.username,
      password: form.password,
    })
    router.push('/dashboard')
  } catch (error) {
    errorMessage.value = error?.response?.data?.detail || 'Не удалось войти. Проверьте логин и пароль.'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="flex min-h-screen items-center justify-center bg-gradient-to-b from-slate-100 via-slate-50 to-brand-50 px-4">
    <div class="w-full max-w-md rounded-2xl border border-white bg-white p-8 shadow-soft">
      <p class="text-xs uppercase tracking-[0.25em] text-brand-600">Vue Admin</p>
      <h1 class="mt-3 text-2xl font-semibold text-slate-900">Вход в панель</h1>
      <p class="mt-2 text-sm text-slate-500">Управляйте контентом вашего сайта из одного кабинета.</p>

      <form class="mt-6 space-y-4" @submit.prevent="submit">
        <div>
          <label class="mb-1 block text-sm font-medium text-slate-700">Email или username</label>
          <input
            v-model="form.username"
            type="text"
            autocomplete="username"
            class="w-full rounded-xl border border-slate-300 px-3 py-2 outline-none transition focus:border-brand-500 focus:ring-2 focus:ring-brand-200"
            placeholder="meditation_owner"
          />
        </div>

        <div>
          <label class="mb-1 block text-sm font-medium text-slate-700">Пароль</label>
          <input
            v-model="form.password"
            type="password"
            autocomplete="current-password"
            class="w-full rounded-xl border border-slate-300 px-3 py-2 outline-none transition focus:border-brand-500 focus:ring-2 focus:ring-brand-200"
            placeholder="••••••••"
          />
        </div>

        <p v-if="errorMessage" class="rounded-xl border border-rose-200 bg-rose-50 px-3 py-2 text-sm text-rose-700">
          {{ errorMessage }}
        </p>

        <button
          type="submit"
          :disabled="loading"
          class="inline-flex w-full items-center justify-center rounded-xl bg-brand-600 px-4 py-2.5 text-sm font-semibold text-white transition hover:bg-brand-700 disabled:cursor-not-allowed disabled:opacity-70"
        >
          {{ loading ? 'Входим...' : 'Войти' }}
        </button>
      </form>
    </div>
  </div>
</template>
