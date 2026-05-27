<script setup>
import { computed, ref } from 'vue'

import { uploadMediaFile } from '../api/media'

defineOptions({ name: 'DynamicField' })

const props = defineProps({
  field: {
    type: Object,
    required: true,
  },
  modelValue: {
    type: [String, Number, Boolean, Array, Object, null],
    default: '',
  },
  uploadContext: {
    type: Object,
    default: () => ({}),
  },
  pathPrefix: {
    type: String,
    default: '',
  },
})

const emit = defineEmits(['update:modelValue'])

const fieldType = computed(() => props.field?.type || 'text')
const fieldKey = computed(() => props.field?.key || '')
const fieldKeyLower = computed(() => String(fieldKey.value).toLowerCase())
const inputId = computed(() => `field-${props.pathPrefix || fieldKey.value || Math.random().toString(36).slice(2)}`)

const mediaKeyPattern = /(image|background_image|background_video|poster|avatar|photo|gallery|video)/i
const isMediaType = computed(() => fieldType.value === 'image' || fieldType.value === 'video')
const isMediaByKey = computed(() => mediaKeyPattern.test(fieldKeyLower.value))
const isMediaField = computed(() => isMediaType.value || isMediaByKey.value)
const mediaType = computed(() => {
  if (fieldType.value === 'video' || fieldKeyLower.value.includes('video')) {
    return 'video'
  }
  return 'image'
})

const fileInputRef = ref(null)
const uploading = ref(false)
const uploadError = ref('')

const apiBaseUrl = computed(() => {
  const explicit = props.uploadContext?.apiBaseUrl
  if (explicit) {
    return String(explicit).replace(/\/+$/, '')
  }
  return String(import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000').replace(/\/+$/, '')
})

const mediaValue = computed(() => (typeof props.modelValue === 'string' ? props.modelValue : ''))

const mediaPreviewUrl = computed(() => {
  const value = mediaValue.value
  if (!value) return ''

  if (value.startsWith('http://') || value.startsWith('https://')) {
    return value
  }

  if (value.startsWith('/')) {
    return `${apiBaseUrl.value}${value}`
  }

  return `${apiBaseUrl.value}/${value}`
})

const uploadActionLabel = computed(() => {
  const rawLabel = String(props.field?.label || '').trim().toLowerCase()
  if (rawLabel) {
    return `Загрузить ${rawLabel}`
  }
  return mediaType.value === 'video' ? 'Загрузить видео' : 'Загрузить изображение'
})

function cloneValue(value) {
  return value === undefined ? undefined : JSON.parse(JSON.stringify(value))
}

function defaultForField(field) {
  if (field && Object.prototype.hasOwnProperty.call(field, 'default')) {
    return cloneValue(field.default)
  }

  if (field?.type === 'number') return 0
  if (field?.type === 'boolean') return false
  if (field?.type === 'repeater') return []
  return ''
}

function updateText(event) {
  emit('update:modelValue', event.target.value)
}

function updateNumber(event) {
  const raw = event.target.value
  emit('update:modelValue', raw === '' ? '' : Number(raw))
}

function updateBoolean(event) {
  emit('update:modelValue', Boolean(event.target.checked))
}

function clearMedia() {
  uploadError.value = ''
  emit('update:modelValue', '')
  if (fileInputRef.value) {
    fileInputRef.value.value = ''
  }
}

function openUploadDialog() {
  uploadError.value = ''
  fileInputRef.value?.click()
}

async function onFileSelected(event) {
  const file = event?.target?.files?.[0]
  if (!file) return

  uploadError.value = ''
  uploading.value = true

  try {
    const payload = await uploadMediaFile({
      file,
      site: props.uploadContext?.siteId || props.uploadContext?.siteSlug || '',
      section: props.uploadContext?.sectionKey || 'uploads',
      field: props.pathPrefix || fieldKey.value,
    })

    emit('update:modelValue', payload?.path || payload?.url || '')
  } catch (error) {
    const detail = error?.response?.data?.detail
    uploadError.value = detail || 'Не удалось загрузить файл.'
  } finally {
    uploading.value = false
    if (fileInputRef.value) {
      fileInputRef.value.value = ''
    }
  }
}

const repeaterRows = computed(() => (Array.isArray(props.modelValue) ? props.modelValue : []))

function addRow() {
  const row = {}
  for (const nested of props.field.fields || []) {
    row[nested.key] = defaultForField(nested)
  }
  emit('update:modelValue', [...repeaterRows.value, row])
}

function removeRow(index) {
  const next = [...repeaterRows.value]
  next.splice(index, 1)
  emit('update:modelValue', next)
}

function updateRepeaterCell(index, key, value) {
  const next = [...repeaterRows.value]
  next[index] = { ...(next[index] || {}), [key]: value }
  emit('update:modelValue', next)
}
</script>

<template>
  <div class="space-y-2">
    <div class="flex items-center justify-between">
      <label :for="inputId" class="text-sm font-medium text-slate-800">
        {{ field.label || field.key }}
      </label>
      <span v-if="field.required" class="text-xs text-rose-500">обязательно</span>
    </div>

    <p v-if="field.help_text" class="text-xs text-slate-500">{{ field.help_text }}</p>

    <template v-if="fieldType === 'textarea'">
      <textarea
        :id="inputId"
        :value="modelValue || ''"
        :placeholder="field.placeholder || ''"
        class="min-h-28 w-full rounded-xl border border-slate-300 px-3 py-2 text-sm outline-none transition focus:border-brand-500 focus:ring-2 focus:ring-brand-200"
        @input="updateText"
      />
    </template>

    <template v-else-if="fieldType === 'number'">
      <input
        :id="inputId"
        type="number"
        :value="modelValue"
        :placeholder="field.placeholder || ''"
        class="w-full rounded-xl border border-slate-300 px-3 py-2 text-sm outline-none transition focus:border-brand-500 focus:ring-2 focus:ring-brand-200"
        @input="updateNumber"
      />
    </template>

    <template v-else-if="fieldType === 'boolean'">
      <label class="inline-flex cursor-pointer items-center gap-2 rounded-xl border border-slate-200 bg-slate-50 px-3 py-2">
        <input type="checkbox" class="h-4 w-4" :checked="Boolean(modelValue)" @change="updateBoolean" />
        <span class="text-sm text-slate-700">{{ Boolean(modelValue) ? 'Включено' : 'Выключено' }}</span>
      </label>
    </template>

    <template v-else-if="fieldType === 'select'">
      <select
        :id="inputId"
        :value="modelValue || ''"
        class="w-full rounded-xl border border-slate-300 px-3 py-2 text-sm outline-none transition focus:border-brand-500 focus:ring-2 focus:ring-brand-200"
        @change="updateText"
      >
        <option value="">Выберите значение</option>
        <option v-for="opt in field.options || []" :key="typeof opt === 'string' ? opt : opt.value" :value="typeof opt === 'string' ? opt : opt.value">
          {{ typeof opt === 'string' ? opt : opt.label }}
        </option>
      </select>
    </template>

    <template v-else-if="fieldType === 'repeater'">
      <div class="space-y-3 rounded-2xl border border-slate-200 bg-slate-50 p-3">
        <div
          v-for="(row, index) in repeaterRows"
          :key="`${field.key}-row-${index}`"
          class="space-y-3 rounded-xl border border-slate-200 bg-white p-3"
        >
          <div class="flex items-center justify-between">
            <p class="text-xs font-semibold uppercase tracking-wide text-slate-500">Элемент {{ index + 1 }}</p>
            <button
              type="button"
              class="rounded-lg border border-rose-200 px-2 py-1 text-xs font-medium text-rose-600 hover:bg-rose-50"
              @click="removeRow(index)"
            >
              Удалить
            </button>
          </div>

          <DynamicField
            v-for="nested in field.fields || []"
            :key="`${field.key}-${index}-${nested.key}`"
            :field="nested"
            :model-value="row?.[nested.key]"
            :upload-context="uploadContext"
            :path-prefix="`${pathPrefix}.${index}.${nested.key}`"
            @update:model-value="(value) => updateRepeaterCell(index, nested.key, value)"
          />
        </div>

        <button
          type="button"
          class="rounded-xl border border-brand-200 bg-white px-3 py-2 text-sm font-medium text-brand-700 hover:bg-brand-50"
          @click="addRow"
        >
          + Добавить элемент
        </button>
      </div>
    </template>

    <template v-else-if="isMediaField">
      <div class="space-y-3 rounded-xl border border-slate-200 bg-slate-50 p-3">
        <input
          :id="inputId"
          ref="fileInputRef"
          type="file"
          class="hidden"
          :accept="mediaType === 'video' ? 'video/*' : 'image/*'"
          @change="onFileSelected"
        >

        <div v-if="mediaValue" class="flex items-start gap-3">
          <div class="h-16 w-16 overflow-hidden rounded-lg border border-slate-200 bg-white">
            <img v-if="mediaType === 'image'" :src="mediaPreviewUrl" alt="preview" class="h-full w-full object-cover" />
            <video v-else :src="mediaPreviewUrl" class="h-full w-full object-cover" muted playsinline controls />
          </div>

          <div class="min-w-0 flex-1">
            <p class="truncate text-xs text-slate-500">{{ mediaValue }}</p>
            <div class="mt-2 flex flex-wrap gap-2">
              <button
                type="button"
                class="rounded-lg border border-brand-200 bg-white px-2.5 py-1 text-xs font-medium text-brand-700 hover:bg-brand-50"
                :disabled="uploading"
                @click="openUploadDialog"
              >
                {{ uploading ? 'Загрузка...' : 'Заменить' }}
              </button>
              <button
                type="button"
                class="rounded-lg border border-rose-200 bg-white px-2.5 py-1 text-xs font-medium text-rose-600 hover:bg-rose-50"
                :disabled="uploading"
                @click="clearMedia"
              >
                Удалить
              </button>
            </div>
          </div>
        </div>

        <button
          v-else
          type="button"
          class="rounded-xl border border-brand-200 bg-white px-3 py-2 text-sm font-medium text-brand-700 hover:bg-brand-50"
          :disabled="uploading"
          @click="openUploadDialog"
        >
          {{ uploading ? 'Загрузка...' : uploadActionLabel }}
        </button>

        <p v-if="uploadError" class="text-xs text-rose-600">{{ uploadError }}</p>
      </div>
    </template>

    <template v-else>
      <input
        :id="inputId"
        type="text"
        :value="modelValue || ''"
        :placeholder="field.placeholder || ''"
        class="w-full rounded-xl border border-slate-300 px-3 py-2 text-sm outline-none transition focus:border-brand-500 focus:ring-2 focus:ring-brand-200"
        @input="updateText"
      />
    </template>
  </div>
</template>
