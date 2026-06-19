<template>
  <div class="min-h-[80vh] flex items-center justify-center bg-slate-50 py-12 px-4 sm:px-6 lg:px-8">
    <div class="max-w-xl w-full bg-white rounded-2xl shadow-xl p-8 space-y-8">
      <div>
        <h2 class="text-center text-3xl font-extrabold text-slate-900 tracking-tight">
          Create a Buyer Account
        </h2>
        <p class="mt-2 text-center text-sm text-slate-600">
          Already have an account?
          <NuxtLink to="/login" class="font-medium text-indigo-600 hover:text-indigo-500 transition-colors">
            Log in
          </NuxtLink>
        </p>
      </div>

      <!-- Account Type Step -->
      <div v-if="step === 1" class="space-y-6">
        <h3 class="text-base font-semibold text-slate-700 text-center">Step 1 of 2 — Account Type</h3>
        <p class="text-sm text-slate-500 text-center">Are you buying as an individual or for a business?</p>
        <div class="grid grid-cols-2 gap-4">
          <button
            id="btn-individual"
            @click="form.accountType = 'INDIVIDUAL'"
            :class="['border-2 rounded-2xl p-5 flex flex-col items-center gap-3 transition-all', form.accountType === 'INDIVIDUAL' ? 'border-indigo-500 bg-indigo-50' : 'border-slate-200 hover:border-indigo-300']"
          >
            <span class="text-4xl">🧑</span>
            <div class="text-center">
              <p class="font-semibold text-slate-900">Individual</p>
              <p class="text-xs text-slate-500 mt-1">Personal purchases, no KYB required</p>
            </div>
            <div v-if="form.accountType === 'INDIVIDUAL'" class="w-5 h-5 rounded-full bg-indigo-500 flex items-center justify-center">
              <svg class="w-3 h-3 text-white" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd"/></svg>
            </div>
          </button>
          <button
            id="btn-business"
            @click="form.accountType = 'BUSINESS'"
            :class="['border-2 rounded-2xl p-5 flex flex-col items-center gap-3 transition-all', form.accountType === 'BUSINESS' ? 'border-indigo-500 bg-indigo-50' : 'border-slate-200 hover:border-indigo-300']"
          >
            <span class="text-4xl">🏢</span>
            <div class="text-center">
              <p class="font-semibold text-slate-900">Business</p>
              <p class="text-xs text-slate-500 mt-1">Company purchases, team & KYB features</p>
            </div>
            <div v-if="form.accountType === 'BUSINESS'" class="w-5 h-5 rounded-full bg-indigo-500 flex items-center justify-center">
              <svg class="w-3 h-3 text-white" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd"/></svg>
            </div>
          </button>
        </div>
        <UButton @click="step = 2" color="indigo" block size="xl" class="font-semibold" :disabled="!form.accountType">
          Continue →
        </UButton>
      </div>

      <!-- Registration Form Step -->
      <form v-if="step === 2" class="space-y-6" @submit.prevent="handleRegister">
        <div class="flex items-center justify-between">
          <button type="button" @click="step = 1" class="text-sm text-indigo-600 hover:underline flex items-center gap-1">
            ← Back
          </button>
          <span class="text-xs font-medium px-2.5 py-1 rounded-full" :class="form.accountType === 'BUSINESS' ? 'bg-blue-50 text-blue-700' : 'bg-green-50 text-green-700'">
            {{ form.accountType === 'BUSINESS' ? '🏢 Business' : '🧑 Individual' }}
          </span>
        </div>

        <div class="grid grid-cols-1 gap-y-5 gap-x-4 sm:grid-cols-2">
          <!-- Full Name -->
          <div class="space-y-1 sm:col-span-2">
            <label class="block text-sm font-medium text-slate-700">Full Name <span class="text-red-500">*</span></label>
            <div class="relative">
              <span class="absolute inset-y-0 left-3 flex items-center pointer-events-none">
                <svg class="w-4 h-4 text-slate-400" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                </svg>
              </span>
              <input v-model="form.name" type="text" placeholder="e.g. John Doe" required
                class="w-full rounded-lg border border-slate-200 bg-white pl-9 pr-4 py-3 text-sm text-slate-800 shadow-sm focus:border-indigo-400 focus:outline-none focus:ring-2 focus:ring-indigo-200" />
            </div>
          </div>

          <!-- Email -->
          <div class="space-y-1">
            <label class="block text-sm font-medium text-slate-700">Email Address <span class="text-red-500">*</span></label>
            <div class="relative">
              <span class="absolute inset-y-0 left-3 flex items-center pointer-events-none">
                <svg class="w-4 h-4 text-slate-400" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                </svg>
              </span>
              <input v-model="form.email" type="email" placeholder="john@example.com" required
                class="w-full rounded-lg border border-slate-200 bg-white pl-9 pr-4 py-3 text-sm text-slate-800 shadow-sm focus:border-indigo-400 focus:outline-none focus:ring-2 focus:ring-indigo-200" />
            </div>
          </div>

          <!-- Phone -->
          <div class="space-y-1">
            <label class="block text-sm font-medium text-slate-700">Phone Number</label>
            <div class="relative">
              <span class="absolute inset-y-0 left-3 flex items-center pointer-events-none">
                <svg class="w-4 h-4 text-slate-400" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z" />
                </svg>
              </span>
              <input v-model="form.phone" type="tel" placeholder="+1 (555) 000-0000"
                class="w-full rounded-lg border border-slate-200 bg-white pl-9 pr-4 py-3 text-sm text-slate-800 shadow-sm focus:border-indigo-400 focus:outline-none focus:ring-2 focus:ring-indigo-200" />
            </div>
          </div>

          <!-- Password -->
          <div class="space-y-1 sm:col-span-2">
            <label class="block text-sm font-medium text-slate-700">Password <span class="text-red-500">*</span></label>
            <div class="relative">
              <span class="absolute inset-y-0 left-3 flex items-center pointer-events-none">
                <svg class="w-4 h-4 text-slate-400" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                </svg>
              </span>
              <input v-model="form.password" :type="showPassword ? 'text' : 'password'"
                placeholder="Create a strong password (min 8 chars)" required
                class="w-full rounded-lg border border-slate-200 bg-white pl-9 pr-10 py-3 text-sm text-slate-800 shadow-sm focus:border-indigo-400 focus:outline-none focus:ring-2 focus:ring-indigo-200" />
              <button type="button" @click="showPassword = !showPassword"
                class="absolute inset-y-0 right-3 flex items-center text-slate-400 hover:text-slate-600">
                <svg v-if="!showPassword" class="w-4 h-4" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                  <path stroke-linecap="round" stroke-linejoin="round" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                </svg>
                <svg v-else class="w-4 h-4" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l3.59 3.59m0 0A9.953 9.953 0 0112 5c4.478 0 8.268 2.943 9.543 7a10.025 10.025 0 01-4.132 5.411m0 0L21 21" />
                </svg>
              </button>
            </div>
          </div>
        </div>

        <div v-if="error" class="bg-red-50 border border-red-200 text-red-700 text-sm px-4 py-3 rounded-xl">
          {{ error }}
        </div>

        <label class="flex items-start gap-3 mt-4 cursor-pointer">
          <input v-model="form.terms" type="checkbox" id="terms"
            class="mt-0.5 w-4 h-4 rounded border-slate-300 accent-indigo-600 cursor-pointer flex-shrink-0" />
          <span class="text-sm text-slate-700">
            I agree to the
            <a href="#" class="text-indigo-600 hover:underline">Terms of Service</a>
            and
            <a href="#" class="text-indigo-600 hover:underline">Privacy Policy</a>
          </span>
        </label>

        <UButton type="submit" color="indigo" block size="xl" class="w-full justify-center font-semibold shadow-md" :loading="loading">
          Create Account
        </UButton>
      </form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useAuthStore } from '~/stores/auth'

const router = useRouter()
const authStore = useAuthStore()

const step = ref(1)
const loading = ref(false)
const error = ref('')
const showPassword = ref(false)

const form = ref({
  name: '',
  email: '',
  phone: '',
  password: '',
  terms: false,
  accountType: 'INDIVIDUAL' as 'INDIVIDUAL' | 'BUSINESS',
})

const handleRegister = async () => {
  if (!form.value.terms) {
    error.value = 'Please agree to terms and conditions.'
    return
  }
  if (form.value.password.length < 8) {
    error.value = 'Password must be at least 8 characters.'
    return
  }
  loading.value = true
  error.value = ''
  try {
    await authStore.register({
      email: form.value.email,
      password: form.value.password,
      full_name: form.value.name,
      phone: form.value.phone || undefined,
      role: 'BUYER' as any,
      account_type: form.value.accountType,
    } as any)
    router.push('/buyer/dashboard')
  } catch (e: any) {
    error.value = e?.data?.detail || 'Registration failed. Please try again.'
  } finally {
    loading.value = false
  }
}
</script>
