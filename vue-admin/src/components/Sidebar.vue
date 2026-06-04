<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import {
  BarChart3,
  Blocks,
  CircleGauge,
  Globe2,
  Inbox,
  LayoutDashboard,
  SearchCheck,
  Send,
  X,
} from '@lucide/vue'

import { useAuthStore } from '../stores/auth'
import { useSiteStore } from '../stores/site'

defineProps({
  open: {
    type: Boolean,
    default: false,
  },
})

const emit = defineEmits(['close'])
const route = useRoute()
const authStore = useAuthStore()
const siteStore = useSiteStore()

const siteId = computed(() => siteStore.currentSiteId)
const siteLabel = computed(() => siteStore.currentSite?.name || 'Сайт не выбран')
const userLabel = computed(() => authStore.user?.first_name || authStore.user?.username || 'Пользователь')

const navItems = computed(() => {
  const items = [{ label: 'Мои сайты', to: '/dashboard', icon: LayoutDashboard }]
  if (!siteId.value) return items

  return [
    ...items,
    { label: 'Главная', to: `/sites/${siteId.value}/overview`, icon: CircleGauge },
    { label: 'Заявки', to: `/sites/${siteId.value}/leads`, icon: Inbox },
    { label: 'Аналитика', to: `/sites/${siteId.value}/analytics`, icon: BarChart3 },
    { label: 'Редактирование сайта', to: `/sites/${siteId.value}/sections`, icon: Blocks },
    { label: 'SEO-аудит', to: `/sites/${siteId.value}/seo`, icon: SearchCheck },
    { label: 'Telegram', to: `/sites/${siteId.value}/integration`, icon: Send },
  ]
})

function isActive(item) {
  if (item.to === '/dashboard') return route.path === '/dashboard'
  return route.path.startsWith(item.to)
}
</script>

<template>
  <div>
    <button
      v-if="open"
      type="button"
      class="fixed inset-0 z-30 bg-slate-950/45 lg:hidden"
      aria-label="Закрыть меню"
      @click="emit('close')"
    />

    <aside
      class="fixed inset-y-0 left-0 z-40 flex w-[min(19rem,88vw)] flex-col border-r border-slate-800 bg-slate-950 px-4 py-5 text-slate-200 shadow-2xl transition-transform duration-200 lg:w-64"
      :class="open ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'"
    >
      <div class="flex items-center justify-between gap-3 px-2">
        <div class="flex items-center gap-3">
          <span class="inline-flex h-10 w-10 items-center justify-center rounded-lg bg-cyan-500 text-slate-950">
            <Globe2 :size="21" stroke-width="2.2" />
          </span>
          <div>
            <p class="text-lg font-semibold text-white">Yadro</p>
            <p class="text-xs text-slate-400">Управление сайтом</p>
          </div>
        </div>
        <button type="button" class="icon-button border-slate-700 text-slate-300 lg:hidden" aria-label="Закрыть меню" @click="emit('close')">
          <X :size="20" />
        </button>
      </div>

      <div class="mt-6 rounded-lg border border-slate-800 bg-slate-900 p-3">
        <p class="text-xs text-slate-400">Выбранный сайт</p>
        <p class="mt-1 truncate text-sm font-semibold text-white">{{ siteLabel }}</p>
      </div>

      <nav class="mt-5 flex-1 space-y-1 overflow-y-auto">
        <RouterLink
          v-for="item in navItems"
          :key="item.to"
          :to="item.to"
          class="flex min-h-11 items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition"
          :class="isActive(item) ? 'bg-cyan-500 text-slate-950' : 'text-slate-300 hover:bg-slate-900 hover:text-white'"
          @click="emit('close')"
        >
          <component :is="item.icon" :size="19" />
          <span>{{ item.label }}</span>
        </RouterLink>
      </nav>

      <div class="border-t border-slate-800 pt-4">
        <p class="truncate text-sm font-medium text-white">{{ userLabel }}</p>
        <p class="mt-1 truncate text-xs text-slate-400">{{ authStore.user?.email || '' }}</p>
      </div>
    </aside>
  </div>
</template>
