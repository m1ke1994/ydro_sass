<script setup>
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { ExternalLink, LogOut, Menu } from '@lucide/vue'

import { useAuthStore } from '../stores/auth'
import { useSectionsStore } from '../stores/sections'
import { useSiteStore } from '../stores/site'

const emit = defineEmits(['toggle-sidebar'])
const router = useRouter()
const authStore = useAuthStore()
const siteStore = useSiteStore()
const sectionsStore = useSectionsStore()

const siteTitle = computed(() => siteStore.currentSite?.name || 'Выберите сайт')
const canOpenSite = computed(() => Boolean(siteStore.currentSite?.domain))

function openPublicSite() {
  const domain = siteStore.currentSite?.domain
  if (!domain) return
  const normalized = domain.startsWith('http://') || domain.startsWith('https://') ? domain : `http://${domain}`
  window.open(normalized, '_blank', 'noopener,noreferrer')
}

function logout() {
  authStore.logout()
  siteStore.reset()
  sectionsStore.reset()
  router.push('/login')
}
</script>

<template>
  <header class="sticky top-0 z-20 border-b border-slate-200 bg-white/95 backdrop-blur">
    <div class="flex min-h-16 items-center justify-between gap-3 px-4 sm:px-6 lg:px-8">
      <div class="flex min-w-0 items-center gap-3">
        <button type="button" class="icon-button lg:hidden" aria-label="Открыть меню" @click="emit('toggle-sidebar')">
          <Menu :size="21" />
        </button>
        <div class="min-w-0">
          <p class="text-xs text-slate-500">Текущий сайт</p>
          <p class="truncate text-base font-semibold text-slate-900">{{ siteTitle }}</p>
        </div>
      </div>

      <div class="flex items-center gap-2">
        <button
          type="button"
          class="action-button-secondary hidden sm:inline-flex"
          :disabled="!canOpenSite"
          @click="openPublicSite"
        >
          <ExternalLink :size="17" />
          Открыть сайт
        </button>
        <button type="button" class="icon-button" aria-label="Выйти" title="Выйти" @click="logout">
          <LogOut :size="19" />
        </button>
      </div>
    </div>
  </header>
</template>
