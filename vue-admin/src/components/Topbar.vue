<script setup>
import { computed } from 'vue'
import { useRouter } from 'vue-router'

import { useAuthStore } from '../stores/auth'
import { useSectionsStore } from '../stores/sections'
import { useSiteStore } from '../stores/site'

const emit = defineEmits(['toggle-sidebar'])
const router = useRouter()
const authStore = useAuthStore()
const siteStore = useSiteStore()
const sectionsStore = useSectionsStore()

const siteTitle = computed(() => siteStore.currentSite?.name || 'Сайт не выбран')

function openPublicSite() {
  const domain = siteStore.currentSite?.domain
  if (!domain) return

  const normalized = domain.startsWith('http://') || domain.startsWith('https://')
    ? domain
    : `http://${domain}`

  window.open(normalized, '_blank')
}

function logout() {
  authStore.logout()
  siteStore.reset()
  sectionsStore.reset()
  router.push('/login')
}
</script>

<template>
  <header class="sticky top-0 z-20 border-b border-slate-200/80 bg-white/80 backdrop-blur">
    <div class="flex items-center justify-between gap-4 px-4 py-3 sm:px-6 lg:px-8">
      <div class="flex items-center gap-3">
        <button
          type="button"
          class="inline-flex h-10 w-10 items-center justify-center rounded-xl border border-slate-200 text-slate-700 lg:hidden"
          @click="emit('toggle-sidebar')"
        >
          ☰
        </button>
        <div>
          <p class="text-xs text-slate-500">Сайт</p>
          <h1 class="text-lg font-semibold text-slate-900">{{ siteTitle }}</h1>
        </div>
      </div>

      <div class="flex items-center gap-3">
        <button
          type="button"
          class="hidden rounded-xl border border-slate-200 bg-white px-4 py-2 text-sm font-medium text-slate-700 shadow-sm transition hover:border-brand-300 hover:text-brand-700 sm:inline-flex"
          @click="openPublicSite"
        >
          Просмотреть сайт
        </button>

        <div class="hidden items-center gap-2 rounded-xl bg-slate-100 px-3 py-2 sm:flex">
          <span class="inline-flex h-8 w-8 items-center justify-center rounded-full bg-brand-600 text-xs font-semibold text-white">
            {{ (authStore.user?.username || 'U').slice(0, 1).toUpperCase() }}
          </span>
          <div class="text-left">
            <p class="max-w-[130px] truncate text-xs font-medium text-slate-800">{{ authStore.user?.username }}</p>
            <button type="button" class="text-xs text-slate-500 hover:text-slate-800" @click="logout">Выйти</button>
          </div>
        </div>
      </div>
    </div>
  </header>
</template>
