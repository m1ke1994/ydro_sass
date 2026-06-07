<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { LayoutTemplate } from '@lucide/vue'

import { getSectionLabel } from '../utils/sectionLabels'

const props = defineProps({
  siteId: {
    type: Number,
    required: true,
  },
  sections: {
    type: Array,
    default: () => [],
  },
})

const route = useRoute()
const currentSectionId = computed(() => Number(route.params.sectionId))
const visibleSections = computed(() => props.sections.filter((section) => section.is_active))
</script>

<template>
  <aside class="surface h-fit p-3 lg:sticky lg:top-24">
    <p class="px-3 pb-2 text-xs font-semibold uppercase tracking-wide text-slate-500">Разделы сайта</p>
    <nav class="space-y-1">
      <RouterLink
        v-for="item in visibleSections"
        :key="item.id"
        :to="`/sites/${siteId}/sections/${item.id}`"
        class="flex items-center gap-2 rounded-lg px-3 py-2.5 text-sm font-medium transition"
        :class="currentSectionId === item.id ? 'bg-cyan-50 text-cyan-900' : 'text-slate-700 hover:bg-slate-50'"
      >
        <LayoutTemplate :size="17" />
        <span>{{ getSectionLabel(item) }}</span>
      </RouterLink>
    </nav>
  </aside>
</template>
