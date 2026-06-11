<template>
  <div class="section-padding">
    <div class="container-main max-w-2xl">
      <div class="text-center mb-10">
        <h1 class="text-3xl font-bold text-white drop-shadow-[0_0_8px_rgba(255,255,255,0.3)]">{{ $t('supplier.title') }}</h1>
        <p class="mt-3 text-slate-300">{{ $t('supplier.subtitle') }}</p>
      </div>

      <div v-if="submitted" class="bg-emerald-500/10 border border-emerald-500/30 rounded-xl p-8 text-center glass-panel">
        <p class="text-emerald-400 text-lg font-medium">{{ $t('supplier.success') }}</p>
        <NuxtLink to="/" class="mt-4 inline-block text-primary-400 hover:underline">{{ $t('common.back') }}</NuxtLink>
      </div>

      <form v-else @submit.prevent="handleSubmit" class="glass-panel p-8 space-y-5 border-primary-500/30 shadow-[0_0_30px_rgba(14,165,233,0.1)]">
        <div>
          <label class="block text-sm font-medium text-slate-300 mb-1">{{ $t('supplier.companyName') }}</label>
          <input v-model="form.company_name" type="text" required class="input-field" />
        </div>
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label class="block text-sm font-medium text-slate-300 mb-1">{{ $t('supplier.country') }}</label>
            <input v-model="form.country" type="text" required class="input-field" />
          </div>
          <div>
            <label class="block text-sm font-medium text-slate-300 mb-1">{{ $t('supplier.companyType') }}</label>
            <select v-model="form.company_type" class="input-field">
              <option value="manufacturer" class="bg-slate-900 text-white">Manufacturer</option>
              <option value="distributor" class="bg-slate-900 text-white">Distributor / Agent</option>
              <option value="installer" class="bg-slate-900 text-white">Installer / Service Provider</option>
            </select>
          </div>
        </div>
        <div>
          <label class="block text-sm font-medium text-slate-300 mb-1">Contact Email</label>
          <input v-model="form.email" type="email" required class="input-field" />
        </div>
        <div>
          <label class="block text-sm font-medium text-slate-300 mb-1">Contact Phone / Telegram / WhatsApp</label>
          <input v-model="form.phone" type="text" class="input-field" />
        </div>
        <div>
          <label class="block text-sm font-medium text-slate-300 mb-1">{{ $t('supplier.productCategories') }}</label>
          <textarea v-model="form.categories" rows="3" class="input-field" placeholder="e.g. KNX actuators, sensors, CCTV cameras..."></textarea>
        </div>
        <div>
          <label class="block text-sm font-medium text-slate-300 mb-1">Additional Notes</label>
          <textarea v-model="form.notes" rows="3" class="input-field"></textarea>
        </div>
        <button type="submit" :disabled="loading" class="btn-primary w-full shadow-[0_0_15px_rgba(14,165,233,0.3)]">
          {{ loading ? $t('common.loading') : $t('supplier.submit') }}
        </button>
      </form>
    </div>
  </div>
</template>

<script setup lang="ts">
const { apiFetch } = useApi()
const submitted = ref(false)
const loading = ref(false)

const form = reactive({
  company_name: '',
  country: '',
  company_type: 'manufacturer',
  email: '',
  phone: '',
  categories: '',
  notes: '',
})

async function handleSubmit() {
  loading.value = true
  try {
    await apiFetch('/vendors/apply', {
      method: 'POST',
      body: {
        company_name: form.company_name,
        country: form.country,
        company_type: form.company_type,
        email: form.email,
        phone: form.phone,
        contact_info: { categories: form.categories, notes: form.notes },
      },
    })
    submitted.value = true
  } catch {}
  loading.value = false
}
</script>
