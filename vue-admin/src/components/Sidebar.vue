<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'

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

const navItems = [
  { label: 'Главная', to: '/dashboard', icon: '⌂' },
  { label: 'Разделы', to: '/sections', icon: '▦' },
  { label: 'Медиафайлы', disabled: true, icon: '◫' },
  { label: 'SEO и аналитика', disabled: true, icon: '◎' },
  { label: 'Дизайн и настройки', disabled: true, icon: '✦' },
  { label: 'Пользователи', disabled: true, icon: '◉' },
  { label: 'Подписка', disabled: true, icon: '◆' },
  { label: 'Уведомления', disabled: true, icon: '◌' },
]

const userLabel = computed(() => {
  if (!authStore.user) return 'Пользователь'
  return authStore.user.first_name || authStore.user.username || 'Пользователь'
})

const siteLabel = computed(() => siteStore.site?.domain || siteStore.site?.name || 'Ваш сайт')

function isActive(item) {
  return item.to && route.path.startsWith(item.to)
}
</script>

<template>
  <div>
    <div
      class="fixed inset-0 z-30 bg-slate-900/50 lg:hidden"
      :class="open ? 'block' : 'hidden'"
      @click="emit('close')"
    />

    <aside
      class="fixed inset-y-0 left-0 z-40 flex w-72 flex-col bg-sidebar-gradient p-4 text-slate-200 shadow-2xl transition-transform duration-300"
      :class="open ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'"
    >
      <div class="rounded-2xl border border-white/10 bg-white/5 p-4">
        <p class="text-xs uppercase tracking-[0.2em] text-brand-200/90">MindFlow</p>
        <p class="mt-2 text-lg font-semibold text-white">Панель управления</p>
      </div>

      <div class="mt-4 rounded-2xl border border-white/10 bg-white/5 p-4">
        <p class="text-xs text-slate-300">Текущий сайт</p>
        <p class="mt-1 truncate text-sm font-semibold text-white">{{ siteLabel }}</p>
      </div>

      <nav class="mt-5 flex-1 space-y-1 overflow-y-auto pr-1">
        <template v-for="item in navItems" :key="item.label">
          <RouterLink
            v-if="!item.disabled"
            :to="item.to"
            class="flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition"
            :class="isActive(item)
              ? 'bg-brand-600 text-white shadow-lg shadow-brand-900/35'
              : 'text-slate-200 hover:bg-white/10 hover:text-white'"
            @click="emit('close')"
          >
            <span class="inline-flex h-7 w-7 items-center justify-center rounded-lg bg-white/10 text-xs">{{ item.icon }}</span>
            {{ item.label }}
          </RouterLink>

          <button
            v-else
            type="button"
            class="flex w-full cursor-not-allowed items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium text-slate-400"
            disabled
          >
            <span class="inline-flex h-7 w-7 items-center justify-center rounded-lg bg-white/5 text-xs">{{ item.icon }}</span>
            {{ item.label }}
          </button>
        </template>
      </nav>

      <div class="rounded-2xl border border-white/10 bg-white/5 p-3">
        <p class="text-xs text-slate-300">{{ userLabel }}</p>
        <p class="mt-1 truncate text-sm text-slate-100">{{ authStore.user?.email || 'no-email' }}</p>
      </div>
    </aside>
  </div>
</template>
