<script setup>
defineProps({
  items: {
    type: Array,
    default: () => [],
  },
})
</script>

<template>
  <div class="grid grid-cols-2 gap-3 xl:grid-cols-4">
    <article
      v-for="item in items"
      :key="item.label"
      class="rounded-lg border border-slate-200 bg-white p-4 shadow-sm sm:p-5"
    >
      <p class="text-xs font-medium text-slate-500">{{ item.label }}</p>
      <p class="mt-2 text-2xl font-semibold text-slate-950 sm:text-3xl">{{ item.value }}</p>
      <p v-if="item.sub" class="mt-1 hidden text-xs leading-5 text-slate-500 sm:block">{{ item.sub }}</p>
    </article>
  </div>
</template>
