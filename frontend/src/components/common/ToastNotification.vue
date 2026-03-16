<template>
  <div class="toast-wrap">
    <transition-group name="toast-anim">
      <div v-for="t in store.toasts" :key="t.id" :class="['toast-item', `toast-${t.type}`]">
        <span class="toast-icon">
          <svg v-if="t.type==='success'" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="20 6 9 17 4 12"/></svg>
          <svg v-else-if="t.type==='error'" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
          <svg v-else-if="t.type==='warning'" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>
          <svg v-else width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
        </span>
        <span class="toast-msg">{{ t.message }}</span>
        <button class="toast-x" @click="store.remove(t.id)">×</button>
      </div>
    </transition-group>
  </div>
</template>

<script setup>
import { useNotificationStore } from '@/stores/notification'
const store = useNotificationStore()
</script>

<style scoped>
.toast-wrap { position:fixed; top:16px; right:16px; z-index:9999; display:flex; flex-direction:column; gap:8px; }
.toast-item { display:flex; align-items:flex-start; gap:10px; padding:14px 16px; background:white; border-radius:10px; box-shadow:0 4px 12px rgba(0,0,0,.15); font-size:14px; min-width:280px; max-width:360px; }
.toast-success { border-left:4px solid #16A34A; }
.toast-error   { border-left:4px solid #DC2626; }
.toast-warning { border-left:4px solid #D97706; }
.toast-info    { border-left:4px solid #2563EB; }
.toast-success .toast-icon { color:#16A34A; }
.toast-error   .toast-icon { color:#DC2626; }
.toast-warning .toast-icon { color:#D97706; }
.toast-info    .toast-icon { color:#2563EB; }
.toast-icon { flex-shrink:0; margin-top:2px; }
.toast-msg { flex:1; line-height:1.5; }
.toast-x { background:none; border:none; font-size:18px; cursor:pointer; color:#94A3B8; line-height:1; padding:0; }
.toast-anim-enter-active { transition:all .3s ease; }
.toast-anim-leave-active { transition:all .2s ease; }
.toast-anim-enter-from,.toast-anim-leave-to { transform:translateX(100%); opacity:0; }
</style>
