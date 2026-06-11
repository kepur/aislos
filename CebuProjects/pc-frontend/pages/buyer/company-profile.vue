<template>
  <div class="max-w-3xl mx-auto space-y-6">
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-2xl font-bold text-slate-900">Company Profile</h1>
        <p class="text-slate-500 mt-1">Your business information shown to suppliers.</p>
      </div>
      <UButton color="indigo" :loading="saving" @click="save">Save Changes</UButton>
    </div>

    <div v-if="loading" class="space-y-4">
      <div v-for="i in 4" :key="i" class="h-14 bg-slate-100 rounded-xl animate-pulse" />
    </div>

    <template v-else>
      <UCard>
        <template #header>
          <h3 class="font-semibold text-slate-900">Basic Information</h3>
        </template>
        <div class="space-y-4">
          <UFormGroup label="Company Name">
            <UInput v-model="form.company_name" placeholder="e.g. ABC Trading Corp" />
          </UFormGroup>
          <UFormGroup label="Registration Number (BRN / TIN)">
            <UInput v-model="form.registration_number" placeholder="12-345-678" />
          </UFormGroup>
          <div class="grid grid-cols-2 gap-4">
            <UFormGroup label="Industry">
              <UInput v-model="form.industry" placeholder="Construction, Retail..." />
            </UFormGroup>
            <UFormGroup label="Company Size">
              <USelect
                v-model="form.company_size"
                :options="['1-10', '11-50', '51-200', '201-500', '500+']"
              />
            </UFormGroup>
          </div>
          <UFormGroup label="Website">
            <UInput v-model="form.website" placeholder="https://example.com" type="url" />
          </UFormGroup>
          <UFormGroup label="Company Description">
            <UTextarea v-model="form.bio" rows="3" placeholder="Brief description of your business..." />
          </UFormGroup>
        </div>
      </UCard>

      <UCard>
        <template #header>
          <h3 class="font-semibold text-slate-900">Address</h3>
        </template>
        <div class="space-y-4">
          <UFormGroup label="Street Address">
            <UInput v-model="form.address_line1" placeholder="123 Business Ave" />
          </UFormGroup>
          <div class="grid grid-cols-2 gap-4">
            <UFormGroup label="City">
              <UInput v-model="form.city" placeholder="Cebu City" />
            </UFormGroup>
            <UFormGroup label="Country">
              <UInput v-model="form.country" placeholder="Philippines" />
            </UFormGroup>
          </div>
        </div>
      </UCard>

      <!-- KYB status banner -->
      <UAlert
        v-if="profile?.kyb_status"
        :color="profile.kyb_status === 'VERIFIED' ? 'green' : profile.kyb_status === 'PENDING' ? 'yellow' : 'blue'"
        :icon="profile.kyb_status === 'VERIFIED' ? 'i-heroicons-shield-check' : 'i-heroicons-document-check'"
        :title="kybTitle"
        :description="kybDesc"
      />
    </template>
  </div>
</template>

<script setup lang="ts">
definePageMeta({ layout: 'buyer', middleware: ['buyer'] })
const authStore = useAuthStore()
const config = useRuntimeConfig()
const toast = useToast()

const loading = ref(true)
const saving = ref(false)
const profile = ref<any>(null)

const form = ref({
  company_name: '',
  registration_number: '',
  industry: '',
  company_size: '1-10',
  website: '',
  bio: '',
  address_line1: '',
  city: '',
  country: 'Philippines',
})

const kybTitle = computed(() => {
  const s = profile.value?.kyb_status
  return s === 'VERIFIED' ? '✓ Business Verified' : s === 'PENDING' ? 'KYB Under Review' : 'Complete Business Verification'
})
const kybDesc = computed(() => {
  const s = profile.value?.kyb_status
  return s === 'VERIFIED'
    ? 'Your business is verified. Suppliers see you as a trusted buyer.'
    : s === 'PENDING'
    ? 'Your verification documents are being reviewed. This usually takes 1-2 business days.'
    : 'Submit your business registration documents to unlock higher trust levels and contract features.'
})

async function load() {
  loading.value = true
  try {
    const data = await $fetch<any>(`${config.public.apiBase}/buyer/company-profile`, {
      headers: { Authorization: `Bearer ${authStore.accessToken}` }
    })
    profile.value = data
    Object.assign(form.value, {
      company_name: data.company_name || '',
      registration_number: data.registration_number || '',
      industry: data.industry || '',
      company_size: data.company_size || '1-10',
      website: data.website || '',
      bio: data.bio || '',
      address_line1: data.address_line1 || '',
      city: data.city || '',
      country: data.country || 'Philippines',
    })
  } catch { /* new profile */ }
  finally { loading.value = false }
}

async function save() {
  saving.value = true
  try {
    await $fetch(`${config.public.apiBase}/buyer/company-profile`, {
      method: 'PATCH',
      body: form.value,
      headers: { Authorization: `Bearer ${authStore.accessToken}` }
    })
    toast.add({ title: 'Company profile saved!', color: 'green' })
  } catch (e: any) {
    toast.add({ title: e?.data?.detail || 'Save failed', color: 'red' })
  } finally { saving.value = false }
}

onMounted(() => load())
</script>
