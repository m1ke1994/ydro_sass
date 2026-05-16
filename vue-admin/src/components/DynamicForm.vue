<script setup>
import DynamicField from './DynamicField.vue'

const props = defineProps({
  schema: {
    type: Object,
    default: () => ({}),
  },
  modelValue: {
    type: Object,
    default: () => ({}),
  },
})

const emit = defineEmits(['update:modelValue'])

function updateField(key, value) {
  emit('update:modelValue', {
    ...(typeof props.modelValue === 'object' && props.modelValue ? props.modelValue : {}),
    [key]: value,
  })
}
</script>

<template>
  <div class="space-y-5">
    <DynamicField
      v-for="field in schema?.fields || []"
      :key="field.key"
      :field="field"
      :model-value="modelValue?.[field.key]"
      @update:model-value="(value) => updateField(field.key, value)"
    />
  </div>
</template>
