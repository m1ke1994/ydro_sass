<script setup>
import { ChevronRight, Image, LayoutTemplate, MessageSquareText, Pencil, Rows3 } from '@lucide/vue'
import { getSectionLabel } from '../utils/sectionLabels'

defineProps({ siteId: { type: Number, required: true }, sections: { type: Array, default: () => [] } })

const icons = { hero: Image, about: MessageSquareText, services: Rows3, reviews: MessageSquareText, gallery: Image }
function sectionIcon(section) { return icons[section.section_type || section.key] || LayoutTemplate }
</script>

<template>
  <div v-if="sections.length" class="grid gap-3">
    <article v-for="section in sections.filter((item) => item.is_active)" :key="section.id" class="surface flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
      <div class="flex min-w-0 items-center gap-3">
        <span class="inline-flex h-11 w-11 shrink-0 items-center justify-center rounded-lg bg-cyan-50 text-cyan-700">
          <component :is="sectionIcon(section)" :size="21" />
        </span>
        <div class="min-w-0">
          <p class="truncate font-semibold text-slate-950">{{ getSectionLabel(section) }}</p>
          <p class="mt-1 text-sm text-slate-500">{{ section.is_active ? 'Виден посетителям сайта' : 'Скрыт от посетителей' }}</p>
        </div>
      </div>
      <div class="flex items-center gap-2">
        <span class="status-badge" :class="section.is_active ? 'status-success' : 'status-neutral'">{{ section.is_active ? 'Опубликован' : 'Скрыт' }}</span>
        <RouterLink :to="`/sites/${siteId}/sections/${section.id}`" class="action-button-secondary flex-1 sm:flex-none">
          <Pencil :size="16" /> Изменить <ChevronRight :size="16" />
        </RouterLink>
      </div>
    </article>
  </div>
</template>
