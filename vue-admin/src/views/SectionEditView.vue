<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'

import DynamicForm from '../components/DynamicForm.vue'
import { useSectionsStore } from '../stores/sections'
import { useSiteStore } from '../stores/site'

const route = useRoute()
const sectionsStore = useSectionsStore()
const siteStore = useSiteStore()

const loading = ref(false)
const saving = ref(false)
const errorMessage = ref('')
const successMessage = ref('')

const contentModel = ref({})
const contentJsonText = ref('{}')

const siteId = computed(() => Number(route.params.siteId))
const sectionId = computed(() => Number(route.params.sectionId))

const currentSection = computed(() => sectionsStore.currentSection)
const sectionTitle = computed(() => currentSection.value?.title || `Section ${sectionId.value}`)
const schema = computed(() => currentSection.value?.schema || currentSection.value?.schema_template?.schema || { fields: [] })
const hasSchema = computed(() => Array.isArray(schema.value?.fields) && schema.value.fields.length > 0)

function clone(value) {
  return value === undefined ? {} : JSON.parse(JSON.stringify(value))
}

async function load() {
  loading.value = true
  errorMessage.value = ''

  try {
    siteStore.selectSite(siteId.value)

    if (!siteStore.currentSite) {
      await siteStore.fetchSite(siteId.value)
    }

    const data = await sectionsStore.fetchSection(siteId.value, sectionId.value)
    contentModel.value = clone(data?.content || {})
    contentJsonText.value = JSON.stringify(data?.content || {}, null, 2)
  } catch (error) {
    errorMessage.value = error?.response?.data?.detail || 'Не удалось загрузить секцию.'
  } finally {
    loading.value = false
  }
}

async function save() {
  saving.value = true
  errorMessage.value = ''
  successMessage.value = ''

  try {
    let payloadContent = contentModel.value

    if (!hasSchema.value) {
      payloadContent = JSON.parse(contentJsonText.value || '{}')
      contentModel.value = payloadContent
    }

    await sectionsStore.patchSection(siteId.value, sectionId.value, {
      content: payloadContent,
    })

    successMessage.value = 'Сохранено'
    setTimeout(() => {
      successMessage.value = ''
    }, 2500)
  } catch (error) {
    if (error instanceof SyntaxError) {
      errorMessage.value = 'Некорректный JSON в редакторе.'
    } else {
      const detail = error?.response?.data
      errorMessage.value = detail && typeof detail === 'object'
        ? JSON.stringify(detail, null, 2)
        : 'Ошибка при сохранении.'
    }
  } finally {
    saving.value = false
  }
}

onMounted(load)
</script>

<template>
  <div class="space-y-6">
    <div class="flex flex-wrap items-center justify-between gap-3">
      <div>
        <RouterLink :to="`/sites/${siteId}/sections`" class="text-sm font-medium text-brand-700 hover:text-brand-800">← К разделам</RouterLink>
        <h1 class="mt-2 text-3xl font-semibold text-slate-900">{{ sectionTitle }}</h1>
      </div>

      <button
        type="button"
        class="rounded-xl bg-brand-600 px-4 py-2 text-sm font-semibold text-white transition hover:bg-brand-700 disabled:cursor-not-allowed disabled:opacity-70"
        :disabled="saving || loading"
        @click="save"
      >
        {{ saving ? 'Сохранение...' : 'Сохранить' }}
      </button>
    </div>

    <p v-if="errorMessage" class="whitespace-pre-wrap rounded-xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">
      {{ errorMessage }}
    </p>

    <div v-if="successMessage" class="fixed right-4 top-4 z-50 rounded-xl bg-emerald-600 px-4 py-2 text-sm font-semibold text-white shadow-soft">
      {{ successMessage }}
    </div>

    <section v-if="loading" class="rounded-2xl border border-slate-200 bg-white p-6 shadow-soft">
      <p class="text-sm text-slate-500">Загрузка секции...</p>
    </section>

    <section v-else class="rounded-2xl border border-slate-200 bg-white p-6 shadow-soft">
      <h2 class="mb-4 text-lg font-semibold text-slate-900">Контент</h2>

      <DynamicForm v-if="hasSchema" v-model="contentModel" :schema="schema" />

      <textarea
        v-else
        v-model="contentJsonText"
        class="min-h-72 w-full rounded-xl border border-slate-300 bg-slate-50 px-3 py-2 font-mono text-sm outline-none focus:border-brand-500 focus:ring-2 focus:ring-brand-200"
      />

      <p class="mt-2 text-xs text-slate-500">
        {{ hasSchema ? 'Форма построена по schema JSON.' : 'Schema не найдена, используется универсальный JSON-редактор.' }}
      </p>
    </section>
  </div>
</template>
