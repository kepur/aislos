<template>
  <section class="container-main section-padding">
    <div class="mx-auto max-w-xl pc-card">
      <p class="pc-kicker">Cebu Buyer</p>
      <h1 class="mt-3 text-3xl font-bold text-white">Create a buyer account</h1>
      <p class="mt-2 text-sm text-slate-400">Use AinerWise for personal procurement or create a shared company workspace.</p>

      <div v-if="step === 1" class="mt-8 space-y-5">
        <div class="grid gap-3 sm:grid-cols-2">
          <button type="button" class="pc-feature-card text-left" :class="{ 'border-primary-500': accountType === 'individual' }" @click="accountType = 'individual'">
            <span class="font-semibold text-white">Individual</span>
            <span class="mt-1 block text-xs text-slate-400">Personal sourcing and purchases</span>
          </button>
          <button type="button" class="pc-feature-card text-left" :class="{ 'border-primary-500': accountType === 'business' }" @click="accountType = 'business'">
            <span class="font-semibold text-white">Business</span>
            <span class="mt-1 block text-xs text-slate-400">Company profile and shared buyer team</span>
          </button>
        </div>
        <button class="btn-primary w-full" @click="step = 2">Continue</button>
      </div>

      <form v-else class="mt-8 space-y-4" @submit.prevent="submit">
        <input v-model="form.full_name" class="input-field" required placeholder="Full name" />
        <input v-model="form.email" class="input-field" type="email" required placeholder="Email" />
        <input v-model="form.phone" class="input-field" placeholder="Phone" />
        <input v-if="accountType === 'business'" v-model="form.company_name" class="input-field" required placeholder="Company name" />
        <input v-model="form.password" class="input-field" type="password" minlength="8" required placeholder="Password, at least 8 characters" />
        <label class="flex items-start gap-3 text-sm text-slate-400">
          <input v-model="accepted" class="mt-1" type="checkbox" required />
          <span>I agree to the platform terms and privacy policy.</span>
        </label>
        <p v-if="error" class="text-sm text-red-300">{{ error }}</p>
        <div class="flex gap-3">
          <button type="button" class="btn-secondary flex-1" @click="step = 1">Back</button>
          <button class="btn-primary flex-1" :disabled="loading || !accepted">{{ loading ? 'Creating...' : 'Create account' }}</button>
        </div>
      </form>
    </div>
  </section>
</template>

<script setup lang="ts">
definePageMeta({ middleware: 'guest' })
const { register } = useAuth()
const step = ref(1)
const accountType = ref<'individual' | 'business'>('individual')
const accepted = ref(false)
const loading = ref(false)
const error = ref('')
const form = reactive({ full_name: '', email: '', phone: '', company_name: '', password: '' })

async function submit() {
  loading.value = true
  error.value = ''
  try {
    await register({
      ...form,
      role: 'buyer',
      company_name: accountType.value === 'business' ? form.company_name : undefined,
      company_type: 'buyer',
    })
    await navigateTo('/market/buyer/dashboard')
  } catch (e: any) {
    error.value = e?.data?.detail || 'Registration failed.'
  } finally {
    loading.value = false
  }
}
</script>
