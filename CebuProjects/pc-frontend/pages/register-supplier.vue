<template>
  <div class="min-h-screen flex items-center justify-center bg-slate-50 py-12 px-4 sm:px-6 lg:px-8">
    <div class="max-w-2xl w-full bg-white rounded-2xl shadow-xl p-8 space-y-8">
      <div>
        <h2 class="text-center text-3xl font-extrabold text-slate-900 tracking-tight">
          Supplier Application (KYB)
        </h2>
        <p class="mt-2 text-center text-sm text-slate-600">
          We verify all suppliers to maintain a trusted marketplace.
        </p>
      </div>
      
      <form class="mt-8 space-y-6" @submit.prevent="handleRegister">
        <!-- Account Type -->
        <div class="space-y-4">
          <h3 class="text-lg font-medium leading-6 text-slate-900 border-b border-slate-200 pb-2">0. Supplier Type</h3>
          <p class="text-sm text-slate-500">Are you registering as an individual freelancer/trader, or as a registered business?</p>
          <div class="grid grid-cols-2 gap-4">
            <button
              type="button"
              id="acct-individual"
              @click="form.accountType = 'INDIVIDUAL'"
              :class="['border-2 rounded-xl p-4 flex flex-col items-center gap-2 transition-all', form.accountType === 'INDIVIDUAL' ? 'border-indigo-500 bg-indigo-50' : 'border-slate-200 hover:border-indigo-300']"
            >
              <span class="text-3xl">🧑‍💼</span>
              <p class="font-semibold text-slate-900 text-sm">Individual / Freelancer</p>
              <p class="text-xs text-slate-500 text-center">B2C focused, simpler onboarding</p>
            </button>
            <button
              type="button"
              id="acct-business"
              @click="form.accountType = 'BUSINESS'"
              :class="['border-2 rounded-xl p-4 flex flex-col items-center gap-2 transition-all', form.accountType === 'BUSINESS' ? 'border-indigo-500 bg-indigo-50' : 'border-slate-200 hover:border-indigo-300']"
            >
              <span class="text-3xl">🏭</span>
              <p class="font-semibold text-slate-900 text-sm">Registered Business</p>
              <p class="text-xs text-slate-500 text-center">B2B/B2C/BOTH support, full KYB</p>
            </button>
          </div>
        </div>

        <!-- Step 1: Company Info -->
        <div class="space-y-6">
          <h3 class="text-lg font-medium leading-6 text-slate-900 border-b border-slate-200 pb-2">1. Company Information</h3>
          <div class="grid grid-cols-1 gap-y-6 gap-x-4 sm:grid-cols-2">
            <UFormGroup label="Legal Company Name" class="sm:col-span-2" required>
              <UInput v-model="form.companyName" placeholder="e.g. Cebu Builders Hub Inc." size="lg" />
            </UFormGroup>
            
            <UFormGroup label="Registration Number / TIN" required>
              <UInput v-model="form.taxId" placeholder="TIN / DTI / SEC" size="lg" />
            </UFormGroup>

            <UFormGroup label="Business Phone" required>
              <UInput v-model="form.phone" type="tel" placeholder="+1 (555) 000-0000" size="lg" />
            </UFormGroup>

            <UFormGroup label="Primary Category" class="sm:col-span-2" required>
              <USelect v-model="form.category" :options="['Construction Materials', 'Marine Parts', 'Auto Parts', 'IT / Electronics', 'Office Supplies']" placeholder="Select primary category" size="lg" />
            </UFormGroup>
          </div>
        </div>

        <!-- Step 2: Location -->
        <div class="space-y-6 pt-4">
          <h3 class="text-lg font-medium leading-6 text-slate-900 border-b border-slate-200 pb-2">2. Physical Location</h3>
          <div class="grid grid-cols-1 gap-y-6 gap-x-4 sm:grid-cols-2">
            <UFormGroup label="Country" required>
              <USelect v-model="form.country" :options="['United States', 'Philippines', 'Japan']" size="lg" />
            </UFormGroup>
            <UFormGroup label="City/Province" required>
              <UInput v-model="form.city" placeholder="e.g. Mandaue City" size="lg" />
            </UFormGroup>
            <UFormGroup label="Full Address" class="sm:col-span-2" required>
              <UTextarea v-model="form.address" :rows="2" placeholder="Warehouse or showroom address..." />
            </UFormGroup>
          </div>
        </div>

        <!-- Step 3: Documents -->
        <div class="space-y-6 pt-4">
          <h3 class="text-lg font-medium leading-6 text-slate-900 border-b border-slate-200 pb-2">3. Document Upload (KYB)</h3>
          
          <UFormGroup label="Business Permit / Registration Certificate" required>
            <label class="block border-2 border-dashed border-slate-300 rounded-lg p-6 text-center hover:bg-slate-50 cursor-pointer">
              <UIcon name="i-heroicons-document-arrow-up" class="w-8 h-8 text-slate-400 mx-auto mb-2" />
              <p class="text-sm text-slate-600">{{ files.business ? files.business.name : 'Upload PDF or Image' }}</p>
              <input class="hidden" type="file" accept="application/pdf,image/*" @change="setFile('business', $event)" />
            </label>
          </UFormGroup>
          
          <UFormGroup label="Valid ID of Authorized Representative" required>
            <label class="block border-2 border-dashed border-slate-300 rounded-lg p-6 text-center hover:bg-slate-50 cursor-pointer">
              <UIcon name="i-heroicons-identification" class="w-8 h-8 text-slate-400 mx-auto mb-2" />
              <p class="text-sm text-slate-600">{{ files.ownerId ? files.ownerId.name : 'Upload Passport or Government ID' }}</p>
              <input class="hidden" type="file" accept="application/pdf,image/*" @change="setFile('ownerId', $event)" />
            </label>
          </UFormGroup>
        </div>

        <div class="pt-6">
          <UAlert
            v-if="message"
            class="mb-4"
            :color="messageType"
            :title="message"
          />
          <UButton type="submit" color="indigo" block size="xl" :loading="submitting" class="w-full justify-center font-semibold shadow-md">
            {{ submitting ? 'Submitting...' : 'Submit Application' }}
          </UButton>
          <p class="text-xs text-slate-500 text-center mt-3">Applications are typically reviewed within 24-48 hours.</p>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const authStore = useAuthStore()
const config = useRuntimeConfig()

definePageMeta({
  middleware: 'auth',
})

const form = ref({
  companyName: '',
  taxId: '',
  phone: '',
  category: '',
  country: '',
  city: '',
  address: '',
  accountType: 'BUSINESS' as 'INDIVIDUAL' | 'BUSINESS',
})

const files = reactive<{ business: File | null; ownerId: File | null }>({
  business: null,
  ownerId: null,
})
const submitting = ref(false)
const message = ref('')
const messageType = ref<'red' | 'green' | 'blue'>('blue')

function setFile(kind: 'business' | 'ownerId', event: Event) {
  const input = event.target as HTMLInputElement
  files[kind] = input.files?.[0] ?? null
}

async function ensureCompany() {
  const payload = {
    name: form.value.companyName,
    tax_id: form.value.taxId,
    country: form.value.country,
    city: form.value.city,
    address: form.value.address,
  }

  try {
    await $fetch(`${config.public.apiBase}/companies/me`, {
      method: 'PATCH',
      body: payload,
      headers: { Authorization: `Bearer ${authStore.accessToken}` },
    })
  } catch (err: any) {
    if (err?.response?.status !== 404 && err?.statusCode !== 404) throw err
    await $fetch(`${config.public.apiBase}/companies`, {
      method: 'POST',
      body: payload,
      headers: { Authorization: `Bearer ${authStore.accessToken}` },
    })
  }
}

async function uploadDocument(file: File, docType: 'BUSINESS_REGISTRATION' | 'OWNER_ID') {
  const formData = new FormData()
  formData.append('file', file)
  const uploaded = await $fetch<{ url: string }>(`${config.public.apiBase}/uploads`, {
    method: 'POST',
    body: formData,
    headers: { Authorization: `Bearer ${authStore.accessToken}` },
  })
  await $fetch(`${config.public.apiBase}/companies/me/documents`, {
    method: 'POST',
    body: {
      doc_type: docType,
      file_url: uploaded.url,
      original_filename: file.name,
    },
    headers: { Authorization: `Bearer ${authStore.accessToken}` },
  })
}

const handleRegister = async () => {
  message.value = ''
  if (!files.business || !files.ownerId) {
    messageType.value = 'red'
    message.value = 'Please upload both required KYB documents.'
    return
  }

  submitting.value = true
  try {
    await ensureCompany()
    await uploadDocument(files.business, 'BUSINESS_REGISTRATION')
    await uploadDocument(files.ownerId, 'OWNER_ID')
    await $fetch(`${config.public.apiBase}/companies/me/verification/submit`, {
      method: 'POST',
      headers: { Authorization: `Bearer ${authStore.accessToken}` },
    })
    // Update account type
    try {
      await $fetch(`${config.public.apiBase}/auth/me/account-type`, {
        method: 'PATCH',
        body: { account_type: form.value.accountType },
        headers: { Authorization: `Bearer ${authStore.accessToken}` },
      })
    } catch {}
    messageType.value = 'green'
    message.value = 'Application submitted. Admin review is now pending.'
    setTimeout(() => router.push('/supplier/dashboard'), 900)
  } catch (err: any) {
    messageType.value = 'red'
    message.value = err?.data?.detail || err?.message || 'Submission failed.'
  } finally {
    submitting.value = false
  }
}
</script>
