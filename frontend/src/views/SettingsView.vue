<template>
  <div class="settings-page">
    <div class="tabs-container glass p-2 mb-8 flex gap-2">
      <button v-if="authStore.isAdmin" :class="['tab-btn flex-1', activeTab === 'company' ? 'active shadow-sm' : '']" @click="activeTab = 'company'">Company Profile</button>
      <button v-if="authStore.isAdmin" :class="['tab-btn flex-1', activeTab === 'email' ? 'active shadow-sm' : '']" @click="activeTab = 'email'">Email Gateway</button>
      <button :class="['tab-btn flex-1', activeTab === 'team' ? 'active shadow-sm' : '']" @click="activeTab = 'team'">Fleet Management</button>
      <button :class="['tab-btn flex-1', activeTab === 'notifications' ? 'active shadow-sm' : '']" @click="activeTab = 'notifications'">Notifications</button>
    </div>

    <!-- COMPANY TAB -->
    <div v-if="activeTab === 'company'" class="card glass shadow-hover">
      <h2 class="text-bold mb-6 uppercase letter-spacing-1" style="font-size: 14px;">Organization Details</h2>
      <form @submit.prevent="saveCompany" class="grid grid-cols-2 gap-6" v-if="companyForm">
        <div>
          <label class="text-xs text-bold mb-2 flex uppercase">Company Name</label>
          <input type="text" v-model="companyForm.name" class="form-input glass" required />
        </div>
        <div>
          <label class="text-xs text-bold mb-2 flex uppercase">Active Plan</label>
          <div class="mt-1"><span class="badge badge-green px-4 py-2">{{ companyForm.plan }}</span></div>
        </div>
        <div>
          <label class="text-xs text-bold mb-2 flex uppercase">Business Timezone</label>
          <select v-model="companyForm.timezone" class="form-select glass">
            <option value="UTC">UTC (Universal)</option>
            <option value="America/New_York">EST (New York)</option>
            <option value="Asia/Kolkata">IST (India)</option>
          </select>
        </div>
        <div class="col-span-2 pt-4">
          <button type="submit" class="btn btn-primary px-8" :disabled="loading.company">
            <span v-if="loading.company" class="spinner">🌀</span>
            <span v-else>Update Organization</span>
          </button>
        </div>
      </form>
    </div>

    <!-- EMAIL TAB -->
    <div v-if="activeTab === 'email'" class="card glass shadow-hover">
      <h2 class="text-bold mb-2 uppercase letter-spacing-1" style="font-size: 14px;">SMTP Configuration</h2>
      <p class="text-sm text-gray mb-8">Configure the outgoing mail server for workflow triggers.</p>
      
      <form @submit.prevent="saveEmail" class="grid grid-cols-2 gap-6" v-if="emailForm">
        <div>
          <label class="text-xs text-bold mb-2 flex uppercase">SMTP Host</label>
          <input type="text" v-model="emailForm.smtp_host" placeholder="smtp.gmail.com" class="form-input glass" />
        </div>
        <div>
          <label class="text-xs text-bold mb-2 flex uppercase">SMTP Port</label>
          <input type="number" v-model="emailForm.smtp_port" placeholder="587" class="form-input glass" />
        </div>
        <div>
          <label class="text-xs text-bold mb-2 flex uppercase">SMTP Username</label>
          <input type="text" v-model="emailForm.smtp_user" class="form-input glass" />
        </div>
        <div>
          <label class="text-xs text-bold mb-2 flex uppercase">SMTP Password</label>
          <input type="password" v-model="emailForm.smtp_password" class="form-input glass" />
        </div>
        <div>
          <label class="text-xs text-bold mb-2 flex uppercase">Default From Email</label>
          <input type="email" v-model="emailForm.from_email" placeholder="noreply@company.com" class="form-input glass" />
        </div>
        <div class="flex items-center gap-3 mt-4">
          <div class="toggle-switch">
             <input type="checkbox" v-model="emailForm.email_enabled" id="email_enabled" />
             <label for="email_enabled"></label>
          </div>
          <label for="email_enabled" class="text-sm font-semibold">Enabled Outbound Email</label>
        </div>
        
        <div class="col-span-2 pt-4">
          <button type="submit" class="btn btn-primary px-8" :disabled="loading.email">Sync Gateway Settings</button>
        </div>
      </form>

      <div class="mt-12 pt-8 border-t">
        <h3 class="text-bold mb-2" style="font-size: 16px;">Diagnostic Hub</h3>
        <p class="text-sm text-gray mb-6">Send a test payload to verify connectivity.</p>
        <div class="flex gap-3 w-full max-w-lg">
          <input type="email" v-model="testEmail" placeholder="you@domain.com" class="form-input glass" />
          <button class="btn btn-outlined whitespace-nowrap" @click="sendTest" :disabled="!testEmail || loading.test">
              <span v-if="loading.test" class="spinner">🌀</span><span v-else>Trigger Test Execution</span>
          </button>
        </div>
      </div>
    </div>

    <!-- TEAM TAB -->
    <div v-if="activeTab === 'team'" class="card glass shadow-hover">
      <div class="flex items-center gap-6 mb-8 border-b pb-4">
        <button :class="['text-sm font-bold uppercase transition-all', teamSubTab === 'members' ? 'text-indigo border-b-2 border-indigo pb-2' : 'text-gray pb-2 hover:text-indigo']" @click="teamSubTab = 'members'">Personnel</button>
        <button v-if="authStore.isAdmin" :class="['text-sm font-bold uppercase transition-all', teamSubTab === 'roles' ? 'text-indigo border-b-2 border-indigo pb-2' : 'text-gray pb-2 hover:text-indigo']" @click="teamSubTab = 'roles'">Access Roles</button>
      </div>

      <!-- PERSONNEL SUB-TAB -->
      <div v-if="teamSubTab === 'members'">
        <div class="flex items-center justify-between mb-8">
          <div>
            <h2 class="text-bold m-0 uppercase letter-spacing-1" style="font-size: 14px;">Fleet Personnel</h2>
            <p class="text-sm text-gray m-0 mt-1">Direct management of your workspace collaborators.</p>
          </div>
          <button v-if="authStore.isAdmin" class="btn btn-primary" @click="showInviteModal = true">Enroll New Member</button>
        </div>
        
        <div class="flex flex-col gap-4">
          <div v-for="user in store.users" :key="user.id" class="glass p-5 rounded-2xl flex items-center justify-between shadow-sm">
             <div class="flex items-center gap-4">
               <div class="avatar indigo-gradient">{{ user.first_name ? user.first_name[0] : 'U' }}</div>
               <div class="flex flex-col">
                 <span class="text-bold text-sm">{{ user.full_name || user.email }}</span>
                 <span class="text-xs text-muted">{{ user.email }}</span>
               </div>
             </div>
             <div class="flex items-center gap-4">
               <span :class="['badge px-3 py-1', user.role?.is_admin ? 'badge-amber' : 'badge-indigo']">{{ user.role?.name || 'No Role' }}</span>
               <span :class="['badge px-3 py-1', user.is_active ? 'badge-green' : 'badge-gray']">{{ user.is_active ? 'Online' : 'Restricted' }}</span>
               <div v-if="authStore.isAdmin" class="flex items-center gap-2 border-l pl-4 ml-2">
                  <select :value="user.role" @change="updateRole(user.id, $event.target.value)" class="text-xs p-1 glass rounded-lg">
                    <option v-for="role in store.roles" :key="role.id" :value="role.id">{{ role.name }}</option>
                  </select>
                  <button class="btn btn-outlined text-xs py-2 px-3 text-red" @click="deactivate(user.id)" v-if="user.is_active">Suspend</button>
                  <div v-else class="text-xs text-muted italic">Suspended</div>
               </div>
             </div>
          </div>
        </div>
      </div>

      <!-- ROLES SUB-TAB -->
      <div v-if="teamSubTab === 'roles'">
        <div class="flex items-center justify-between mb-8">
          <div>
            <h2 class="text-bold m-0 uppercase letter-spacing-1" style="font-size: 14px;">Access Roles</h2>
            <p class="text-sm text-gray m-0 mt-1">Define permissions and access levels for your team.</p>
          </div>
          <button class="btn btn-primary" @click="openRoleModal()">Define New Role</button>
        </div>

        <div class="grid grid-cols-1 gap-4">
          <div v-for="role in store.roles" :key="role.id" class="glass p-5 rounded-2xl flex items-center justify-between shadow-sm">
            <div class="flex flex-col">
              <span class="text-bold text-sm">{{ role.name }}</span>
              <span class="text-xs text-muted">{{ role.is_admin ? 'Has Admin Privileges' : 'Standard Member' }}</span>
            </div>
            <div class="flex items-center gap-3">
              <button class="btn btn-ghost text-xs" @click="openRoleModal(role)">Edit</button>
              <button class="btn btn-ghost text-xs text-red" @click="deleteRole(role.id)" v-if="!['Admin', 'Employee'].includes(role.name)">Delete</button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- ROLE MODAL -->
    <div v-if="showRoleModal" class="modal-backdrop" @click="showRoleModal = false">
      <div class="modal" @click.stop>
        <h2 class="text-bold mb-6 mt-0">{{ editingRole ? 'Edit Access Role' : 'Define New Role' }}</h2>
        <form @submit.prevent="saveRole">
          <div class="mb-4">
            <label class="text-sm text-bold mb-2">Role Name</label>
            <input type="text" v-model="roleForm.name" class="form-input" required />
          </div>
          <div class="flex items-center gap-3 mb-6">
            <div class="toggle-switch">
               <input type="checkbox" v-model="roleForm.is_admin" id="role_is_admin" />
               <label for="role_is_admin"></label>
            </div>
            <label for="role_is_admin" class="text-sm font-semibold">Grant Administrative Privileges</label>
          </div>
          <div class="flex justify-between">
            <button type="button" class="btn btn-ghost" @click="showRoleModal = false">Cancel</button>
            <button type="submit" class="btn btn-primary" :disabled="loading.role">Save Role</button>
          </div>
        </form>
      </div>
    </div>

    <!-- INVITE MODAL -->
    <div v-if="showInviteModal" class="modal-backdrop" @click="showInviteModal = false">
      <div class="modal" @click.stop>
        <h2 class="text-bold mb-6 mt-0">Add Team Member</h2>
        <form @submit.prevent="inviteUser">
          <div class="grid-2 mb-4">
            <div>
              <label class="text-sm text-bold mb-2">First Name</label>
              <input type="text" v-model="inviteForm.first_name" class="form-input" />
            </div>
            <div>
              <label class="text-sm text-bold mb-2">Last Name</label>
              <input type="text" v-model="inviteForm.last_name" class="form-input" />
            </div>
          </div>
          <div class="mb-4">
            <label class="text-sm text-bold mb-2">Email Address *</label>
            <input type="email" v-model="inviteForm.email" class="form-input" required />
          </div>
          <div class="mb-4">
            <label class="text-sm text-bold mb-2">Password *</label>
            <input type="password" v-model="inviteForm.password" class="form-input" required />
          </div>
          <div class="mb-6">
            <label class="text-sm text-bold mb-2">Role *</label>
            <select v-model="inviteForm.role" class="form-select" required>
              <option v-for="role in store.roles" :key="role.id" :value="role.id">{{ role.name }}</option>
            </select>
          </div>
          <div class="flex justify-between">
            <button type="button" class="btn btn-ghost" @click="showInviteModal = false">Cancel</button>
            <button type="submit" class="btn btn-primary" :disabled="loading.invite">Add Member</button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useSettingsStore } from '@/stores/settings'
import { useAuthStore } from '@/stores/auth'
import { useEmailNotificationStore } from '@/stores/emailNotification'

const store = useSettingsStore()
const authStore = useAuthStore()
const emailStore = useEmailNotificationStore()

const activeTab = ref('team') // default to team as it's accessible to all
const teamSubTab = ref('members')
const loading = reactive({ company: false, email: false, test: false, invite: false, role: false })

const companyForm = ref(null)
const emailForm = ref(null)
const testEmail = ref('')
const showInviteModal = ref(false)
const showRoleModal = ref(false)
const editingRole = ref(null)

const roleForm = reactive({
  name: '',
  is_admin: false
})

const inviteForm = reactive({
  first_name: '',
  last_name: '',
  email: '',
  password: '',
  role: ''
})

onMounted(async () => {
  if (authStore.isAdmin) {
    const cData = await store.fetchCompanySettings()
    companyForm.value = { ...cData }
    
    const eData = await store.fetchEmailSettings()
    emailForm.value = { ...eData }
  }
  
  await store.fetchRoles()
  if (store.roles.length > 0) {
    inviteForm.role = store.roles.find(r => r.name === 'Employee')?.id || store.roles[0].id
  }
  store.fetchUsers()
})

const saveCompany = async () => {
  loading.company = true
  await store.saveCompanySettings(companyForm.value)
  loading.company = false
}

const saveEmail = async () => {
  loading.email = true
  await store.saveEmailSettings(emailForm.value)
  loading.email = false
}

const sendTest = async () => {
  loading.test = true
  await emailStore.sendTestEmail(testEmail.value)
  loading.test = false
}

const updateRole = async (id, role) => {
  await store.updateUserRole(id, role)
}

const deactivate = async (id) => {
  if (confirm('Are you sure you want to deactivate this user?')) {
    await store.deactivateUser(id)
  }
}

const openRoleModal = (role = null) => {
  editingRole.value = role
  if (role) {
    roleForm.name = role.name
    roleForm.is_admin = role.is_admin
  } else {
    roleForm.name = ''
    roleForm.is_admin = false
  }
  showRoleModal.value = true
}

const saveRole = async () => {
  loading.role = true
  try {
    if (editingRole.value) {
      await store.updateRole(editingRole.value.id, roleForm)
    } else {
      await store.createRole(roleForm)
    }
    showRoleModal.value = false
  } finally {
    loading.role = false
  }
}

const deleteRole = async (id) => {
  if (confirm('Are you sure you want to delete this role?')) {
    await store.deleteRole(id)
  }
}

const inviteUser = async () => {
  loading.invite = true
  try {
    await store.createUser(inviteForm)
    showInviteModal.value = false
    inviteForm.first_name = ''
    inviteForm.last_name = ''
    inviteForm.email = ''
    inviteForm.password = ''
    // Reset to default employee role if possible
    inviteForm.role = store.roles.find(r => r.name === 'Employee')?.id || store.roles[0]?.id
  } finally {
    loading.invite = false
  }
}
</script>
<style scoped>
.tabs-container {
  border-radius: 12px;
  background: rgba(0,0,0,0.02);
}
.tab-btn {
  padding: 12px 16px;
  border-radius: 10px;
  font-size: 14px;
  font-weight: 600;
  color: var(--text-secondary);
  border: none;
  background: transparent;
  cursor: pointer;
  transition: all 0.2s;
}
.tab-btn:hover { color: var(--text-primary); background: rgba(0,0,0,0.03); }
.tab-btn.active {
  background: white;
  color: var(--accent-indigo);
}

.avatar {
  width: 44px; height: 44px; border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  color: white; font-weight: 800; font-size: 16px;
}

.grid { display: grid; }
.grid-cols-2 { grid-template-columns: 1fr 1fr; }
.col-span-2 { grid-column: span 2; }
.gap-6 { gap: 24px; }
.rounded-2xl { border-radius: 16px; }
.uppercase { text-transform: uppercase; }
.letter-spacing-1 { letter-spacing: 1px; }

.whitespace-nowrap { white-space: nowrap; }
.max-w-lg { max-width: 512px; }
.border-t { border-top: 1px solid var(--border-color); }
</style>
