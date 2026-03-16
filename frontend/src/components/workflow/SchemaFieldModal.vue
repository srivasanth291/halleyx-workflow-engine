<template>
  <div class="modal-backdrop" @click.self="$emit('cancel')">
    <div class="modal modal-sm">
      <div class="modal-header">
        <h3>Add Input Field</h3>
        <button class="btn-icon" @click="$emit('cancel')">✕</button>
      </div>
      <div class="modal-body">
        <div class="form-group">
          <label class="form-label">Field Name <span class="req">*</span></label>
          <input v-model="form.name" class="form-input" placeholder="e.g. amount" />
        </div>
        <div class="form-group">
          <label class="form-label">Type</label>
          <select v-model="form.type" class="form-input form-select">
            <option value="string">String</option>
            <option value="number">Number</option>
            <option value="boolean">Boolean</option>
            <option value="date">Date</option>
          </select>
        </div>
        <div class="toggle-row">
          <button type="button" class="toggle" :class="{on: form.required}" @click="form.required = !form.required"></button>
          <span class="toggle-label">Required field</span>
        </div>
        <div class="form-group">
          <label class="form-label">Allowed Values</label>
          <input v-model="form.allowed_values_str" class="form-input" placeholder="High, Medium, Low" />
          <span class="form-hint">Comma separated. Leave empty to allow any value.</span>
        </div>
        <p v-if="error" class="form-error-msg">{{ error }}</p>
      </div>
      <div class="modal-footer">
        <button class="btn btn-ghost flex-1" @click="$emit('cancel')">Cancel</button>
        <button class="btn btn-primary flex-1" @click="submit">Add Field</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue'
const emit = defineEmits(['add', 'cancel'])
const form = reactive({ name: '', type: 'string', required: true, allowed_values_str: '' })
const error = ref('')

function submit() {
  if (!form.name.trim()) { error.value = 'Field name is required'; return }
  const allowed = form.allowed_values_str
    ? form.allowed_values_str.split(',').map(v => v.trim()).filter(Boolean)
    : []
  emit('add', {
    name: form.name.trim(),
    type: form.type,
    required: form.required,
    allowed_values: allowed,
  })
}
</script>
