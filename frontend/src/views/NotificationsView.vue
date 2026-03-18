<template>
  <div class="notifications-page">
    <div class="flex items-center justify-between mb-6">
      <div>
        <h1 class="text-bold m-0" style="font-size: 24px;">Notifications</h1>
        <p class="text-gray m-0 mt-1">System alerts and workflow messages</p>
      </div>
    </div>

    <div class="grid grid-cols-2 gap-6 mb-8">
      <div class="card glass p-6 shadow-hover border-accent-indigo">
        <h3 class="text-bold m-0 mb-2 uppercase letter-spacing-1" style="font-size: 14px;">Message Logistics</h3>
        <p class="text-sm text-gray m-0 mb-6">Real-time status of all outbound workflow communications.</p>
        <div class="flex gap-3">
           <div class="stat-bubble indigo-gradient">
             <span class="label">Sent</span>
             <span class="val">{{ store.stats?.total_sent || 0 }}</span>
           </div>
           <div class="stat-bubble amber-gradient">
             <span class="label">Wait</span>
             <span class="val">{{ store.stats?.total_pending || 0 }}</span>
           </div>
           <div class="stat-bubble red-gradient">
             <span class="label">Fail</span>
             <span class="val">{{ store.stats?.total_failed || 0 }}</span>
           </div>
        </div>
      </div>
      <div class="card glass p-6 shadow-hover border-accent-green">
        <h3 class="text-bold m-0 mb-2 uppercase letter-spacing-1" style="font-size: 14px;">Channel Distribution</h3>
        <div class="grid grid-cols-3 gap-4 mt-6">
           <div class="channel-card glass">
             <div class="icon">📧</div>
             <div class="text-bold" style="font-size: 24px;">{{ store.stats?.channels?.email || 0 }}</div>
             <div class="text-xs text-gray uppercase mt-1">Emails</div>
           </div>
           <div class="channel-card glass">
             <div class="icon">💬</div>
             <div class="text-bold" style="font-size: 24px;">{{ store.stats?.channels?.slack || 0 }}</div>
             <div class="text-xs text-gray uppercase mt-1">Slack</div>
           </div>
           <div class="channel-card glass">
             <div class="icon">📱</div>
             <div class="text-bold" style="font-size: 24px;">{{ store.stats?.channels?.ui_message || 0 }}</div>
             <div class="text-xs text-gray uppercase mt-1">Direct</div>
           </div>
        </div>
      </div>
    </div>

    <div class="card glass p-0 overflow-hidden shadow-hover">
      <div v-if="store.loading" class="p-12 text-center"><span class="spinner">🌀</span> Fetching communication logs...</div>
      <div v-else class="table-container">
        <table>
          <thead>
            <tr>
              <th class="uppercase letter-spacing-1 text-xs">Medium</th>
              <th class="uppercase letter-spacing-1 text-xs">Recipient</th>
              <th class="uppercase letter-spacing-1 text-xs">Payload Reference</th>
              <th class="uppercase letter-spacing-1 text-xs">Status</th>
              <th class="uppercase letter-spacing-1 text-xs">Timestamp</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="msg in store.notifications" :key="msg.id" class="hover-row">
              <td class="px-6 py-4">
                <span class="badge" :class="getChannelClass(msg.channel)">{{ msg.channel }}</span>
              </td>
              <td class="px-6 py-4">
                <div class="text-sm font-semibold">{{ msg.recipient }}</div>
              </td>
              <td class="px-6 py-4">
                <div class="text-sm text-bold">{{ msg.subject || 'System Trigger' }}</div>
              </td>
              <td class="px-6 py-4">
                <StatusBadge :status="msg.status" />
              </td>
              <td class="px-6 py-4 text-xs text-muted font-mono">
                {{ formatDate(msg.sent_at || msg.created_at) }}
              </td>
            </tr>
            <tr v-if="store.notifications.length === 0">
              <td colspan="5" class="text-center text-gray p-12 italic">No communication records found in the current audit period.</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script setup>
import { onMounted, onUnmounted } from 'vue'
import { useEmailNotificationStore } from '@/stores/emailNotification'
import StatusBadge from '@/components/common/StatusBadge.vue'

const store = useEmailNotificationStore()
let refreshInterval = null

const loadData = () => {
  store.fetchStats()
  store.fetchNotifications()
}

onMounted(() => {
  loadData()
  refreshInterval = setInterval(loadData, 60000)
})

onUnmounted(() => clearInterval(refreshInterval))

const formatDate = (dateStr) => {
  if (!dateStr) return '—'
  const d = new Date(dateStr)
  return d.toLocaleDateString() + ' ' + d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
}
const getChannelClass = (channel) => {
  if (channel === 'email') return 'badge-indigo'
  if (channel === 'slack') return 'badge-amber'
  return 'badge-green'
}
</script>

<style scoped>
.grid { display: grid; }
.grid-cols-2 { grid-template-columns: 1fr 1fr; }
.grid-cols-3 { grid-template-columns: repeat(3, 1fr); }
.gap-6 { gap: 24px; }
.gap-4 { gap: 16px; }

.stat-bubble {
  padding: 12px 20px;
  border-radius: 14px;
  display: flex;
  flex-direction: column;
  min-width: 100px;
}
.stat-bubble .label { font-size: 11px; text-transform: uppercase; font-weight: 700; opacity: 0.8; }
.stat-bubble .val { font-size: 20px; font-weight: 800; }

.channel-card {
  padding: 16px;
  border-radius: 16px;
  text-align: center;
  border: 1px solid var(--border-color);
}
.channel-card .icon { font-size: 24px; margin-bottom: 8px; }

.table-container { overflow-x: auto; }
.hover-row:hover { background: rgba(0,0,0,0.01); }

.letter-spacing-1 { letter-spacing: 1px; }
.uppercase { text-transform: uppercase; }
.text-xs { font-size: 11px; }
.text-muted { color: var(--text-muted); }
.font-mono { font-family: 'JetBrains Mono', monospace; }

.border-accent-indigo { border-left: 4px solid var(--accent-indigo); }
.border-accent-green { border-left: 4px solid var(--accent-green); }
</style>
