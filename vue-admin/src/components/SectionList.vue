<script setup>
defineProps({
  sections: {
    type: Array,
    default: () => [],
  },
})

const iconsByType = {
  hero: '✦',
  about: '◉',
  services: '▦',
  reviews: '✎',
  gallery: '▣',
  contacts: '✆',
}

function typeIcon(type) {
  return iconsByType[type] || '◌'
}
</script>

<template>
  <div class="space-y-3">
    <article
      v-for="section in sections"
      :key="section.id"
      class="flex flex-col gap-3 rounded-2xl border border-slate-200 bg-white p-4 shadow-soft sm:flex-row sm:items-center sm:justify-between"
    >
      <div class="flex items-start gap-3">
        <span class="inline-flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-brand-100 text-brand-700">
          {{ typeIcon(section.section_type) }}
        </span>

        <div>
          <p class="text-sm font-semibold text-slate-900">{{ section.name }}</p>
          <p class="text-xs text-slate-500">/{{ section.slug }} · {{ section.section_type }}</p>
        </div>
      </div>

      <div class="flex items-center gap-3 sm:justify-end">
        <span
          class="rounded-full px-2.5 py-1 text-xs font-semibold"
          :class="section.is_active ? 'bg-emerald-100 text-emerald-700' : 'bg-slate-100 text-slate-500'"
        >
          {{ section.is_active ? 'Опубликован' : 'Черновик' }}
        </span>

        <RouterLink
          :to="`/sections/${section.slug}`"
          class="rounded-xl border border-brand-200 bg-brand-50 px-3 py-1.5 text-xs font-semibold text-brand-700 transition hover:bg-brand-100"
        >
          Редактировать
        </RouterLink>
      </div>
    </article>
  </div>
</template>
