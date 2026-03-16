<template>
  <div class="login-page">
    <div class="login-card">
      <div class="login-logo">
        <div class="login-icon">⚡</div>
        <h1 class="login-title">FlowEngine</h1>
        <p class="login-sub">Automate your business workflows</p>
      </div>

      <div class="login-tabs">
        <button :class="['tab-btn', tab === 'login' ? 'tab-active' : '']" @click="tab = 'login'">Login</button>
        <button :class="['tab-btn', tab === 'register' ? 'tab-active' : '']" @click="tab = 'register'">Register Company</button>
      </div>

      <!-- LOGIN FORM -->
      <div v-if="tab === 'login'" class="login-form">
        <div class="form-group">
          <label class="form-label">Email Address</label>
          <input v-model="loginForm.email" type="email" class="form-input" placeholder="admin@company.com" @keyup.enter="handleLogin" />
        </div>
        <div class="form-group">
          <label class="form-label">Password</label>
          <div class="pw-wrap">
            <input v-model="loginForm.password" :type="showPw ? 'text' : 'password'" class="form-input" @keyup.enter="handleLogin" />
            <button type="button" class="pw-eye" @click="showPw = !showPw">{{ showPw ? '🙈' : '👁️' }}</button>
          </div>
        </div>
        <div v-if="error" class="alert alert-error">{{ error }}</div>
        <button class="btn btn-primary btn-full btn-lg" :disabled="loading" @click="handleLogin">
          <span v-if="loading" class="spinner"></span>
          {{ loading ? 'Logging in...' : 'Login →' }}
        </button>
      </div>

      <!-- REGISTER FORM -->
      <div v-if="tab === 'register'" class="login-form">
        <div class="form-group">
          <label class="form-label">Company Name <span class="req">*</span></label>
          <input v-model="regForm.company_name" class="form-input" placeholder="TCS India" />
        </div>
        <div class="form-group">
          <label class="form-label">Admin Email <span class="req">*</span></label>
          <input v-model="regForm.email" type="email" class="form-input" placeholder="admin@company.com" />
        </div>
        <div class="form-group">
          <label class="form-label">Password <span class="req">*</span></label>
          <input v-model="regForm.password" type="password" class="form-input" />
        </div>
        <div class="form-group">
          <label class="form-label">Plan</label>
          <div class="plan-grid">
            <div
              v-for="p in plans"
              :key="p.value"
              :class="['plan-card', regForm.plan === p.value ? 'active' : '']"
              @click="regForm.plan = p.value"
            >
              <span v-if="p.popular" class="plan-badge">Most Popular</span>
              <div class="plan-card-name">{{ p.name }}</div>
              <div class="plan-card-desc">{{ p.desc }}</div>
              <div class="plan-card-price">{{ p.price }}</div>
            </div>
          </div>
        </div>
        <div v-if="error" class="alert alert-error">{{ error }}</div>
        <button class="btn btn-primary btn-full btn-lg" :disabled="loading" @click="handleRegister">
          <span v-if="loading" class="spinner"></span>
          {{ loading ? 'Creating...' : 'Create Account →' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const authStore = useAuthStore()

const tab = ref('login')
const showPw = ref(false)
const loading = ref(false)
const error = ref('')

const loginForm = reactive({ email: '', password: '' })
const regForm = reactive({ company_name: '', email: '', password: '', plan: 'pro' })

const plans = [
  { value: 'basic',      name: 'Basic',      desc: '5 workflows', price: 'Free',    popular: false },
  { value: 'pro',        name: 'Pro',        desc: '50 workflows', price: '$29/mo', popular: true  },
  { value: 'enterprise', name: 'Enterprise', desc: 'Unlimited',    price: 'Custom', popular: false },
]

async function handleLogin() {
  error.value = ''
  if (!loginForm.email || !loginForm.password) { error.value = 'Please fill all fields'; return }
  loading.value = true
  try {
    await authStore.login(loginForm)
    router.push('/workflows')
  } catch (e) {
    error.value = e.response?.data?.detail || 'Invalid credentials'
  } finally { loading.value = false }
}

async function handleRegister() {
  error.value = ''
  if (!regForm.company_name || !regForm.email || !regForm.password) {
    error.value = 'Please fill all required fields'; return
  }
  loading.value = true
  try {
    await authStore.register({ ...regForm, first_name: 'Admin', last_name: 'User' })
    router.push('/workflows')
  } catch (e) {
    const d = e.response?.data
    error.value = d?.detail || Object.values(d || {})[0] || 'Registration failed'
  } finally { loading.value = false }
}
</script>

<style scoped>
.login-page {
  min-height: 100vh; background: var(--bg-page);
  display: flex; align-items: center; justify-content: center; padding: 16px;
}
.login-card {
  background: white; border-radius: var(--modal-radius);
  box-shadow: 0 4px 24px rgba(0,0,0,.1);
  width: 100%; max-width: 460px; padding: 40px;
}
.login-logo { text-align: center; margin-bottom: 28px; }
.login-icon {
  width: 48px; height: 48px; background: var(--accent-green);
  border-radius: 12px; display: flex; align-items: center;
  justify-content: center; font-size: 22px; margin: 0 auto 12px;
}
.login-title { font-size: 26px; font-weight: 700; }
.login-sub { color: var(--text-secondary); font-size: 14px; margin-top: 4px; }
.login-tabs { display: flex; border-bottom: 1px solid var(--border-color); margin-bottom: 24px; }
.tab-btn {
  flex: 1; padding: 11px; background: none; border: none;
  font-size: 14px; font-weight: 500; cursor: pointer;
  color: var(--text-secondary); border-bottom: 2px solid transparent;
  margin-bottom: -1px; transition: all .15s;
}
.tab-active { color: var(--accent-green); border-bottom-color: var(--accent-green); }
.login-form { display: flex; flex-direction: column; gap: 16px; }
.pw-wrap { position: relative; }
.pw-wrap .form-input { padding-right: 40px; }
.pw-eye {
  position: absolute; right: 10px; top: 50%;
  transform: translateY(-50%); background: none;
  border: none; cursor: pointer; font-size: 16px;
}
</style>
