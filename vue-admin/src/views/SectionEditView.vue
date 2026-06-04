<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { ArrowLeft, Save } from '@lucide/vue'

import DynamicForm from '../components/DynamicForm.vue'
import { useSectionsStore } from '../stores/sections'
import { useSiteStore } from '../stores/site'

const route = useRoute()
const sectionsStore = useSectionsStore()
const siteStore = useSiteStore()
const loading = ref(false)
const saving = ref(false)
const error = ref('')
const success = ref('')
const content = ref({})
const siteId = computed(() => Number(route.params.siteId))
const sectionId = computed(() => Number(route.params.sectionId))
const section = computed(() => sectionsStore.currentSection)
const schema = computed(() => section.value?.schema || section.value?.schema_template?.schema || { fields: [] })
const hasSchema = computed(() => Array.isArray(schema.value?.fields) && schema.value.fields.length > 0)
const uploadContext = computed(() => ({
  siteId: siteId.value,
  siteSlug: siteStore.currentSite?.slug || '',
  sectionKey: section.value?.key || '',
  apiBaseUrl: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000',
}))

function clone(value) { return JSON.parse(JSON.stringify(value || {})) }

async function load() {
  loading.value = true
  error.value = ''
  try {
    siteStore.selectSite(siteId.value)
    if (!siteStore.currentSite) await siteStore.fetchSite(siteId.value)
    const data = await sectionsStore.fetchSection(siteId.value, sectionId.value)
    content.value = clone(data?.content)
  } catch (e) {
    error.value = e?.response?.data?.detail || 'Не удалось загрузить раздел.'
  } finally {
    loading.value = false
  }
}

async function save() {
  if (!hasSchema.value) return
  saving.value = true
  error.value = ''
  success.value = ''
  try {
    await sectionsStore.patchSection(siteId.value, sectionId.value, { content: content.value })
    success.value = 'Изменения сохранены. Они появятся на сайте после обновления страницы.'
  } catch (e) {
    error.value = 'Не удалось сохранить изменения. Проверьте заполненные поля и попробуйте снова.'
  } finally {
    saving.value = false
  }
}

onMounted(load)
</script>

<template>
  <div class="page-stack">
    <header class="page-heading page-heading-actions">
      <div>
        <RouterLink :to="`/sites/${siteId}/sections`" class="inline-flex items-center gap-2 text-sm font-medium text-cyan-800"><ArrowLeft :size="16" />К разделам</RouterLink>
        <h1>{{ section?.title || 'Редактирование раздела' }}</h1>
        <p>Измените нужные поля и нажмите «Сохранить».</p>
      </div>
      <button type="button" class="action-button-primary" :disabled="saving || loading || !hasSchema" @click="save">
        <Save :size="17" />{{ saving ? 'Сохраняем...' : 'Сохранить' }}
      </button>
    </header>
    <p v-if="error" class="notice-error">{{ error }}</p>
    <p v-if="success" class="notice-success">{{ success }}</p>
    <section v-if="loading" class="empty-state"><span class="loading-dot" /><p>Загружаем содержимое...</p></section>
    <section v-else-if="!hasSchema" class="empty-state">
      <h2>Этот раздел пока нельзя изменить здесь</h2>
      <p>Обратитесь к администратору, чтобы настроить удобную форму редактирования.</p>
    </section>
    <section v-else class="surface">
      <DynamicForm v-model="content" :schema="schema" :upload-context="uploadContext" />
    </section>
  </div>
</template>
