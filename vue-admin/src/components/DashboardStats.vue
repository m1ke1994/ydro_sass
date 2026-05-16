<script setup>
defineProps({
  items: {
    type: Array,
    default: () => [],
  },
})
</script>

<template>
  <div class="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
    <article
      v-for="item in items"
      :key="item.label"
      class="rounded-2xl border border-slate-200 bg-white p-5 shadow-soft"
    >
      <p class="text-xs font-medium uppercase tracking-wide text-slate-500">{{ item.label }}</p>
      <p class="mt-2 text-3xl font-semibold text-slate-900">{{ item.value }}</p>
      <p v-if="item.sub" class="mt-1 text-sm text-slate-500">{{ item.sub }}</p>
    </article>
  </div>
</template>
