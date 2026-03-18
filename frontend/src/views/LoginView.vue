<template>
  <div class="login-container">
    <div class="split-layout">
      <!-- Left: Branding side -->
      <div class="branding-side">
        <div class="blob-bg"></div>
        <div class="branding-content">
          <div class="glass-badge mb-6 animate-fade-in">
            <span class="pulse-dot"></span>
            System Operational
          </div>
          
          <h1 class="branding-title animate-slide-up">
            Streamline your <br/>
            <span class="text-gradient">Business Workflow</span>
          </h1>
          
          <p class="branding-subtitle animate-slide-up-delay-1">
            FlowEngine provides the core infrastructure for rule-based automation, 
            helping your team focus on what truly matters.
          </p>

          <div class="feature-cards">
            <div class="mini-glass-card animate-slide-up-delay-2">
              <div class="card-icon">⚡</div>
              <div>
                <div class="text-bold text-sm">Lightning Fast</div>
                <div class="text-xs text-muted">Real-time execution</div>
              </div>
            </div>
            <div class="mini-glass-card animate-slide-up-delay-3">
              <div class="card-icon">🛡️</div>
              <div>
                <div class="text-bold text-sm">Enterprise Secure</div>
                <div class="text-xs text-muted">Isolated multi-tenancy</div>
              </div>
            </div>
          </div>
        </div>
        
        <div class="branding-footer">
          © 2026 Halleyx Technologies. Built for Peak Performance.
        </div>
      </div>

      <!-- Right: Auth side -->
      <div class="auth-side">
        <div class="auth-content animate-fade-in-right">
          <div class="mobile-logo-only mb-8">
            <div class="logo-circle indigo-gradient">⚡</div>
          </div>

          <div class="mb-10">
            <h2 class="auth-title">Welcome Back</h2>
            <p class="auth-subtitle">Log in to manage your organization's workflows.</p>
          </div>

          <form @submit.prevent="handleLogin" class="auth-form">
            <div class="form-group mb-6">
              <label class="form-label">Email Address</label>
              <div class="input-wrapper">
                <input 
                  type="email" 
                  v-model="form.email" 
                  class="premium-input" 
                  required 
                  placeholder="name@company.com" 
                />
              </div>
            </div>
            
            <div class="form-group mb-8">
              <div class="flex justify-between items-center mb-2">
                <label class="form-label">Password</label>
                <a href="#" class="forgot-link">Forgot password?</a>
              </div>
              <div class="input-wrapper">
                <input 
                  :type="showPassword ? 'text' : 'password'" 
                  v-model="form.password" 
                  class="premium-input pr-12" 
                  required 
                  placeholder="••••••••"
                />
                <button type="button" class="eye-toggle" @click="showPassword = !showPassword">
                  <span v-if="showPassword">👁️</span>
                  <span v-else>👁️‍🗨️</span>
                </button>
              </div>
            </div>

            <div v-if="error" class="error-toast mb-6">
              <span class="mr-2">⚠️</span> {{ error }}
            </div>

            <button type="submit" class="premium-btn w-full" :disabled="loading">
              <span v-if="loading" class="spinner mr-2">🌀</span>
              <span v-else>Sign In to Account</span>
            </button>
          </form>

          <div class="auth-footer mt-12">
            <p class="text-xs text-muted text-center italic">
              "Efficiency is doing things right; effectiveness is doing the right things."
            </p>
          </div>
        </div>
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

const form = reactive({ email: '', password: '' })
const showPassword = ref(false)
const loading = ref(false)
const error = ref('')

const handleLogin = async () => {
  loading.value = true
  error.value = ''
  try {
    await authStore.login(form)
    router.push('/workflows')
  } catch (e) {
    error.value = e.response?.data?.detail || 'Invalid email or password.'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-container {
  height: 100vh;
  width: 100vw;
  background: white;
  overflow: hidden;
  font-family: 'Inter', sans-serif;
}

.split-layout {
  display: flex;
  height: 100%;
}

/* Branding Side */
.branding-side {
  flex: 1.2;
  background: #0F172A;
  position: relative;
  display: flex;
  flex-direction: column;
  justify-content: center;
  padding: 80px;
  color: white;
  overflow: hidden;
}

@media (max-width: 1024px) {
  .branding-side { display: none; }
}

.blob-bg {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 120%;
  height: 120%;
  background: radial-gradient(circle at 70% 30%, rgba(99, 102, 241, 0.15) 0%, transparent 50%),
              radial-gradient(circle at 30% 70%, rgba(16, 185, 129, 0.1) 0%, transparent 50%);
  filter: blur(80px);
}

.branding-content {
  position: relative;
  z-index: 10;
  max-width: 560px;
}

.glass-badge {
  display: inline-flex;
  align-items: center;
  padding: 8px 16px;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 100px;
  font-size: 13px;
  font-weight: 500;
  color: #94a3b8;
}

.pulse-dot {
  width: 8px;
  height: 8px;
  background: #10B981;
  border-radius: 50%;
  margin-right: 10px;
  box-shadow: 0 0 10px rgba(16, 185, 129, 0.5);
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0% { transform: scale(1); opacity: 1; }
  50% { transform: scale(1.5); opacity: 0.5; }
  100% { transform: scale(1); opacity: 1; }
}

.branding-title {
  font-size: 56px;
  line-height: 1.1;
  font-weight: 800;
  margin-bottom: 24px;
  letter-spacing: -2px;
}

.text-gradient {
  background: linear-gradient(135deg, #818cf8 0%, #34d399 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

.branding-subtitle {
  font-size: 18px;
  color: #94a3b8;
  line-height: 1.6;
  margin-bottom: 48px;
}

.feature-cards {
  display: flex;
  gap: 20px;
}

.mini-glass-card {
  flex: 1;
  padding: 24px;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 20px;
  display: flex;
  align-items: center;
  gap: 16px;
  backdrop-filter: blur(10px);
}

.card-icon {
  font-size: 24px;
  width: 48px;
  height: 48px;
  background: rgba(255, 255, 255, 0.05);
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 12px;
}

.branding-footer {
  position: absolute;
  bottom: 40px;
  left: 80px;
  font-size: 12px;
  color: #475569;
}

/* Auth Side */
.auth-side {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 40px;
  background: #fcfcfc;
}

.auth-content {
  width: 100%;
  max-width: 420px;
}

.logo-circle {
  width: 50px;
  height: 50px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 24px;
  margin: 0 auto;
}

.auth-title {
  font-size: 32px;
  font-weight: 700;
  color: #0F172A;
  margin-bottom: 8px;
  text-align: center;
}

.auth-subtitle {
  color: #64748b;
  font-size: 15px;
  text-align: center;
}

.form-label {
  display: block;
  font-size: 14px;
  font-weight: 600;
  color: #334155;
  margin-bottom: 8px;
}

.input-wrapper {
  position: relative;
}

.premium-input {
  width: 100%;
  padding: 14px 16px;
  background: white;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  font-size: 15px;
  color: #1e293b;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  box-sizing: border-box;
}

.premium-input:focus {
  outline: none;
  border-color: #6366f1;
  box-shadow: 0 0 0 4px rgba(99, 102, 241, 0.1);
}

.eye-toggle {
  position: absolute;
  right: 14px;
  top: 50%;
  transform: translateY(-50%);
  background: none;
  border: none;
  cursor: pointer;
  opacity: 0.4;
  font-size: 18px;
  transition: opacity 0.2s;
}

.eye-toggle:hover { opacity: 0.8; }

.forgot-link {
  font-size: 13px;
  color: #6366f1;
  text-decoration: none;
  font-weight: 500;
}

.premium-btn {
  background: #0F172A;
  color: white;
  border: none;
  padding: 16px;
  border-radius: 12px;
  font-size: 15px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
}

.premium-btn:hover {
  background: #1e293b;
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(15, 23, 42, 0.15);
}

.premium-btn:active { transform: translateY(0); }

.premium-btn:disabled { opacity: 0.7; cursor: not-allowed; }

.error-toast {
  background: #fef2f2;
  color: #991b1b;
  padding: 12px 16px;
  border-radius: 10px;
  font-size: 13px;
  border: 1px solid #fee2e2;
  display: flex;
  align-items: center;
}

/* Animations */
.animate-fade-in { animation: fadeIn 0.8s ease-out; }
.animate-fade-in-right { animation: fadeInRight 0.8s ease-out; }
.animate-slide-up { animation: slideUp 0.8s ease-out backwards; }
.animate-slide-up-delay-1 { animation: slideUp 0.8s ease-out 0.2s backwards; }
.animate-slide-up-delay-2 { animation: slideUp 0.8s ease-out 0.4s backwards; }
.animate-slide-up-delay-3 { animation: slideUp 0.8s ease-out 0.6s backwards; }

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

@keyframes fadeInRight {
  from { opacity: 0; transform: translateX(20px); }
  to { opacity: 1; transform: translateX(0); }
}

@keyframes slideUp {
  from { opacity: 0; transform: translateY(30px); }
  to { opacity: 1; transform: translateY(0); }
}

.flex { display: flex; }
.justify-between { justify-content: space-between; }
.items-center { align-items: center; }
.w-full { width: 100%; }
.mb-2 { margin-bottom: 8px; }
.mb-6 { margin-bottom: 24px; }
.mb-8 { margin-bottom: 32px; }
.mb-10 { margin-bottom: 40px; }
.mt-12 { margin-top: 48px; }
.mr-2 { margin-right: 8px; }
.text-bold { font-weight: 700; }
.text-sm { font-size: 14px; }
.text-xs { font-size: 12px; }
.text-muted { color: #94a3b8; }
.text-center { text-align: center; }
.italic { font-style: italic; }
</style>
