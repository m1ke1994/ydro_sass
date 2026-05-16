<script setup>
import { computed } from 'vue'

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
})

const emit = defineEmits(['update:modelValue'])

const fieldType = computed(() => props.field?.type || 'text')
const inputId = computed(() => `field-${props.field?.key || Math.random().toString(36).slice(2)}`)

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

    <template v-else>
      <input
        :id="inputId"
        :type="fieldType === 'image' || fieldType === 'video' ? 'url' : 'text'"
        :value="modelValue || ''"
        :placeholder="field.placeholder || (fieldType === 'image' ? '/media/...' : '')"
        class="w-full rounded-xl border border-slate-300 px-3 py-2 text-sm outline-none transition focus:border-brand-500 focus:ring-2 focus:ring-brand-200"
        @input="updateText"
      />
    </template>
  </div>
</template>
