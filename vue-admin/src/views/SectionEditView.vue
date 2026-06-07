<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { ArrowLeft, ExternalLink, RotateCcw, Save } from '@lucide/vue'

import DynamicForm from '../components/DynamicForm.vue'
import SectionSidebar from '../components/SectionSidebar.vue'
import { useSectionsStore } from '../stores/sections'
import { useSiteStore } from '../stores/site'
import { getSectionLabel } from '../utils/sectionLabels'

const route = useRoute()
const sectionsStore = useSectionsStore()
const siteStore = useSiteStore()
const loading = ref(false)
const saving = ref(false)
const error = ref('')
const success = ref('')
const content = ref({})
const originalContent = ref({})
const siteId = computed(() => Number(route.params.siteId))
const sectionId = computed(() => Number(route.params.sectionId))
const section = computed(() => sectionsStore.currentSection)
const sectionTitle = computed(() => getSectionLabel(section.value))
const schema = computed(() => section.value?.schema || section.value?.schema_template?.schema || { fields: [] })
const hasSchema = computed(() => Array.isArray(schema.value?.fields) && schema.value.fields.length > 0)
const uploadContext = computed(() => ({
  siteId: siteId.value,
  siteSlug: siteStore.currentSite?.slug || '',
  sectionKey: section.value?.key || '',
  apiBaseUrl: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000',
}))
const previewUrl = computed(() => {
  const domain = String(siteStore.currentSite?.domain || '').trim().replace(/\/+$/, '')
  if (!domain) return ''
  return /^https?:\/\//i.test(domain) ? domain : `http://${domain}`
})

function clone(value) {
  return JSON.parse(JSON.stringify(value || {}))
}

async function load() {
  loading.value = true
  error.value = ''
  success.value = ''
  try {
    siteStore.selectSite(siteId.value)
    if (!siteStore.currentSite) await siteStore.fetchSite(siteId.value)
    if (!sectionsStore.sections.length) await sectionsStore.fetchSections(siteId.value)
    const data = await sectionsStore.fetchSection(siteId.value, sectionId.value)
    content.value = clone(data?.content)
    originalContent.value = clone(data?.content)
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
    originalContent.value = clone(content.value)
    success.value = 'Изменения сохранены'
  } catch (e) {
    const details = e?.response?.data?.content
    error.value = Array.isArray(details)
      ? details.join(' ')
      : 'Не удалось сохранить изменения. Проверьте поля и попробуйте снова.'
  } finally {
    saving.value = false
  }
}

function cancelChanges() {
  content.value = clone(originalContent.value)
  error.value = ''
  success.value = ''
}

function openPreview() {
  if (previewUrl.value) {
    window.open(previewUrl.value, '_blank', 'noopener,noreferrer')
  }
}

onMounted(load)
watch(sectionId, load)
</script>

<template>
  <div class="page-stack">
    <header class="page-heading page-heading-actions">
      <div>
        <RouterLink :to="`/sites/${siteId}/sections`" class="inline-flex items-center gap-2 text-sm font-medium text-cyan-800">
          <ArrowLeft :size="16" />К разделам
        </RouterLink>
        <h1>{{ sectionTitle }}</h1>
        <p>Измените нужные тексты и изображения. Технические настройки сайта скрыты.</p>
      </div>
      <div class="flex flex-wrap gap-2">
        <button v-if="previewUrl" type="button" class="action-button-secondary" @click="openPreview">
          <ExternalLink :size="17" />Предпросмотр
        </button>
        <button type="button" class="action-button-secondary" :disabled="saving || loading" @click="cancelChanges">
          <RotateCcw :size="17" />Отменить
        </button>
        <button type="button" class="action-button-primary" :disabled="saving || loading || !hasSchema" @click="save">
          <Save :size="17" />{{ saving ? 'Сохраняем...' : 'Сохранить' }}
        </button>
      </div>
    </header>

    <p v-if="error" class="notice-error">{{ error }}</p>
    <p v-if="success" class="notice-success">{{ success }}</p>

    <section v-if="loading" class="empty-state">
      <span class="loading-dot" />
      <p>Загружаем содержимое...</p>
    </section>
    <section v-else-if="!hasSchema" class="empty-state">
      <h2>Этот раздел пока нельзя изменить здесь</h2>
      <p>Обратитесь к администратору, чтобы настроить удобную форму редактирования.</p>
    </section>
    <div v-else class="grid items-start gap-4 lg:grid-cols-[260px_minmax(0,1fr)]">
      <SectionSidebar :site-id="siteId" :sections="sectionsStore.sections" />
      <section class="surface">
        <DynamicForm v-model="content" :schema="schema" :upload-context="uploadContext" />
      </section>
    </div>
  </div>
</template>
