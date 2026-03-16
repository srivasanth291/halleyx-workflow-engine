<template>
  <span :class="['badge', cfg.cls]">
    <span v-if="cfg.dot" class="dot" :class="{'dot-pulse': props.status==='in_progress'}"></span>
    {{ cfg.label }}
  </span>
</template>

<script setup>
import { computed } from 'vue'
const props = defineProps({ status: String })
const map = {
  pending:     { cls:'badge-warning', label:'Pending',     dot:true  },
  in_progress: { cls:'badge-info',    label:'In Progress', dot:true  },
  completed:   { cls:'badge-success', label:'Completed',   dot:false },
  failed:      { cls:'badge-error',   label:'Failed',      dot:false },
  canceled:    { cls:'badge-gray',    label:'Canceled',    dot:false },
  active:      { cls:'badge-success', label:'Active',      dot:false },
  inactive:    { cls:'badge-gray',    label:'Inactive',    dot:false },
}
const cfg = computed(() => map[props.status] || { cls:'badge-gray', label: props.status, dot:false })
</script>
