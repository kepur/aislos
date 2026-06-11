<template>
  <div class="min-h-screen bg-slate-900 flex items-center justify-center p-4">
    <div class="w-full max-w-sm">
      <div class="text-center mb-8">
        <div class="w-16 h-16 bg-primary-600 rounded-2xl flex items-center justify-center mx-auto mb-4">
          <svg class="w-8 h-8 text-white" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
          </svg>
        </div>
        <h1 class="text-2xl font-bold text-white">ProcurePing</h1>
        <p class="text-slate-400 text-sm mt-1">{{ t('login.subtitle') }}</p>
      </div>

      <!-- Language switcher -->
      <div class="flex justify-center mb-4">
        <select class="text-xs border border-slate-600 rounded-lg px-3 py-1.5 bg-slate-800 text-slate-300" :value="locale" @change="switchLocale($event.target.value)">
          <option v-for="l in supportedLocales" :key="l.code" :value="l.code">{{ l.name }}</option>
        </select>
      </div>

      <div class="bg-white rounded-2xl p-6 shadow-xl">
        <div class="space-y-4">
          <div>
            <label class="block text-sm font-medium text-slate-700 mb-1.5">{{ t('login.email') }}</label>
            <input v-model="email" type="email" class="input" placeholder="admin@procureping.com" @keyup.enter="login" />
          </div>
          <div>
            <label class="block text-sm font-medium text-slate-700 mb-1.5">{{ t('login.password') }}</label>
            <input v-model="password" type="password" class="input" placeholder="••••••••" @keyup.enter="login" />
          </div>
          <p v-if="error" class="text-sm text-red-600 bg-red-50 px-3 py-2 rounded-lg">{{ error }}</p>
          <button class="btn-primary w-full py-2.5" :disabled="loading" @click="login">
            {{ loading ? t('login.signingIn') : t('login.signIn') }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { useAuthStore } from '@/stores/auth'
import { SUPPORTED_LOCALES, applyDirection } from '@/i18n'

const { t, locale } = useI18n()
const auth = useAuthStore()
const router = useRouter()
const email = ref('admin@procureping.com')
const password = ref('')
const loading = ref(false)
const error = ref('')
const supportedLocales = SUPPORTED_LOCALES

function switchLocale(lang) {
  locale.value = lang
  localStorage.setItem('admin_locale', lang)
  applyDirection(lang)
}

async function login() {
  if (!email.value || !password.value) { error.value = t('login.adminOnly'); return }
  loading.value = true
  error.value = ''
  try {
    await auth.login(email.value, password.value)
    router.push('/dashboard')
  } catch (e) {
    error.value = e.response?.data?.detail || e.message || 'Login failed'
  } finally {
    loading.value = false
  }
}
</script>
