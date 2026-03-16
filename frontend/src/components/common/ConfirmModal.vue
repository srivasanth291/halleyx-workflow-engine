<template>
  <div class="modal-backdrop" @click.self="$emit('cancel')">
    <div class="modal modal-sm">
      <div style="text-align:center;padding:32px 24px 16px">
        <div :class="['confirm-icon', type==='delete'?'ci-red':'ci-amber']">
          <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path v-if="type==='delete'" d="M3 6h18M8 6V4h8v2M19 6l-1 14H6L5 6"/>
            <template v-else><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></template>
          </svg>
        </div>
        <h3 style="font-size:18px;font-weight:700;margin:14px 0 8px">{{ title }}</h3>
        <p style="color:var(--text-secondary);font-size:14px;line-height:1.6">{{ message }}</p>
      </div>
      <div class="modal-footer">
        <button class="btn btn-ghost flex-1" @click="$emit('cancel')">Cancel</button>
        <button :class="['btn','flex-1',confirmClass]" @click="$emit('confirm')">{{ confirmText }}</button>
      </div>
    </div>
  </div>
</template>

<script setup>
defineEmits(['confirm','cancel'])
defineProps({
  title:        { type:String, default:'Are you sure?' },
  message:      { type:String, default:'This cannot be undone.' },
  confirmText:  { type:String, default:'Confirm' },
  confirmClass: { type:String, default:'btn-danger' },
  type:         { type:String, default:'warning' },
})
</script>

<style scoped>
.confirm-icon { width:52px;height:52px;border-radius:50%;display:flex;align-items:center;justify-content:center;margin:0 auto; }
.ci-red   { background:var(--error-bg);   color:var(--error-text); }
.ci-amber { background:var(--warning-bg); color:var(--warning-text); }
</style>
