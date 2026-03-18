<template>
  <div v-if="modelValue" class="modal-backdrop" @click="close">
    <div class="modal" @click.stop>
      <div class="flex items-center gap-3 mb-4">
        <div class="text-red" style="font-size: 24px;">{{ icon || '🗑' }}</div>
        <h2 class="text-bold m-0">{{ title }}</h2>
      </div>
      <p class="text-gray mb-6">{{ message }}</p>
      <div class="flex justify-between mt-6">
        <button class="btn btn-ghost" @click="close">Cancel</button>
        <button :class="['btn', confirmClass || 'btn-danger']" @click="confirm" :disabled="loading">
          <span v-if="loading" class="spinner">🌀</span>
          <span v-else>{{ confirmText || 'Confirm' }}</span>
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
defineProps({
  modelValue: Boolean,
  title: String,
  message: String,
  icon: String,
  confirmText: String,
  confirmClass: String,
  loading: Boolean
})
const emit = defineEmits(['update:modelValue', 'confirm'])

const close = () => {
  emit('update:modelValue', false)
}

const confirm = () => {
  emit('confirm')
}
</script>
