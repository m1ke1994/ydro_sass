<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'

import DynamicForm from '../components/DynamicForm.vue'
import { useSectionsStore } from '../stores/sections'

const route = useRoute()
const sectionsStore = useSectionsStore()

const loading = ref(false)
const saving = ref(false)
const errorMessage = ref('')
const successMessage = ref('')

const contentModel = ref({})
const settingsText = ref('{}')

const sectionSlug = computed(() => route.params.slug)

const sectionTitle = computed(() => {
  const section = sectionsStore.currentSectionForm?.section
  return section?.name || sectionSlug.value
})

const schema = computed(() => sectionsStore.currentSectionForm?.schema || { fields: [] })

function clone(value) {
  return value === undefined ? {} : JSON.parse(JSON.stringify(value))
}

async function load() {
  loading.value = true
  errorMessage.value = ''
  try {
    const data = await sectionsStore.fetchSectionForm(sectionSlug.value)
    contentModel.value = clone(data?.content || {})
    settingsText.value = JSON.stringify(data?.settings || {}, null, 2)
  } catch (error) {
    errorMessage.value = error?.response?.data?.detail || 'РќРµ СѓРґР°Р»РѕСЃСЊ Р·Р°РіСЂСѓР·РёС‚СЊ СЂР°Р·РґРµР».'
  } finally {
    loading.value = false
  }
}

async function save() {
  saving.value = true
  errorMessage.value = ''
  successMessage.value = ''

  try {
    await sectionsStore.patchSection(sectionSlug.value, {
      content: contentModel.value,
    })

    successMessage.value = 'РЎРѕС…СЂР°РЅРµРЅРѕ'
    setTimeout(() => {
      successMessage.value = ''
    }, 2500)
  } catch (error) {
    const detail = error?.response?.data
    errorMessage.value = detail && typeof detail === 'object'
      ? JSON.stringify(detail, null, 2)
      : 'РћС€РёР±РєР° РїСЂРё СЃРѕС…СЂР°РЅРµРЅРёРё.'
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
        <RouterLink to="/sections" class="text-sm font-medium text-brand-700 hover:text-brand-800">в†ђ Рљ СЂР°Р·РґРµР»Р°Рј</RouterLink>
        <h1 class="mt-2 text-3xl font-semibold text-slate-900">{{ sectionTitle }}</h1>
      </div>

      <button
        type="button"
        class="rounded-xl bg-brand-600 px-4 py-2 text-sm font-semibold text-white transition hover:bg-brand-700 disabled:cursor-not-allowed disabled:opacity-70"
        :disabled="saving || loading"
        @click="save"
      >
        {{ saving ? 'РЎРѕС…СЂР°РЅРµРЅРёРµ...' : 'РЎРѕС…СЂР°РЅРёС‚СЊ' }}
      </button>
    </div>

    <p v-if="errorMessage" class="whitespace-pre-wrap rounded-xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">
      {{ errorMessage }}
    </p>

    <div v-if="successMessage" class="fixed right-4 top-4 z-50 rounded-xl bg-emerald-600 px-4 py-2 text-sm font-semibold text-white shadow-soft">
      {{ successMessage }}
    </div>

    <section v-if="loading" class="rounded-2xl border border-slate-200 bg-white p-6 shadow-soft">
      <p class="text-sm text-slate-500">Р—Р°РіСЂСѓР·РєР° СЃРµРєС†РёРё...</p>
    </section>

    <section v-else class="rounded-2xl border border-slate-200 bg-white p-6 shadow-soft">
      <h2 class="mb-4 text-lg font-semibold text-slate-900">РљРѕРЅС‚РµРЅС‚</h2>
      <DynamicForm v-model="contentModel" :schema="schema" />
    </section>

    <section v-if="!loading" class="rounded-2xl border border-slate-200 bg-white p-6 shadow-soft">
      <h2 class="mb-4 text-lg font-semibold text-slate-900">РќР°СЃС‚СЂРѕР№РєРё СЃРµРєС†РёРё</h2>
      <textarea
        v-model="settingsText"
        readonly
        class="min-h-40 w-full rounded-xl border border-slate-300 bg-slate-50 px-3 py-2 font-mono text-xs outline-none"
      />
      <p class="mt-2 text-xs text-slate-500">
        РќР°СЃС‚СЂРѕР№РєРё РѕС‚РѕР±СЂР°Р¶Р°СЋС‚СЃСЏ РґР»СЏ СЃРїСЂР°РІРєРё. Р’ client API СЃРѕС…СЂР°РЅСЏРµС‚СЃСЏ С‚РѕР»СЊРєРѕ `content`.
      </p>
    </section>
  </div>
</template>
