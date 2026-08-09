<template>
  <div class="space-y-6 max-w-2xl">
    <div>
      <h1 class="text-xl font-bold ws-title">{{ $t('portal.profile') }}</h1>
      <p class="text-sm ws-faint mt-1">Manage your account information</p>
    </div>

    <form class="portal-card space-y-5" @submit.prevent="handleSaveProfile">
      <h2 class="text-sm font-bold ws-title">Personal Information</h2>
      <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label class="block text-xs font-semibold ws-muted mb-1.5 uppercase tracking-wider">Full Name</label>
          <input v-model="form.full_name" type="text" class="portal-input" />
        </div>
        <div>
          <label class="block text-xs font-semibold ws-muted mb-1.5 uppercase tracking-wider">Email</label>
          <input :value="user?.email" type="email" disabled class="portal-input !ws-soft cursor-not-allowed opacity-60" />
        </div>
        <div>
          <label class="block text-xs font-semibold ws-muted mb-1.5 uppercase tracking-wider">Phone</label>
          <input v-model="form.phone" type="text" class="portal-input" />
        </div>
        <div>
          <label class="block text-xs font-semibold ws-muted mb-1.5 uppercase tracking-wider">Country</label>
          <input v-model="form.country" type="text" class="portal-input" />
        </div>
        <div>
          <label class="block text-xs font-semibold ws-muted mb-1.5 uppercase tracking-wider">Language</label>
          <select v-model="form.language" class="portal-input">
            <option value="en">English</option>
            <option value="zh">中文</option>
            <option value="sr">Srpski</option>
          </select>
        </div>
      </div>
      <button type="submit" :disabled="saving"
 class="text-sm font-medium text-white bg-gradient-to-r from-blue-500 to-indigo-500 px-6 py-2.5 rounded-xl hover:shadow-lg hover:shadow-blue-500/20 transition-all disabled:opacity-50">
        {{ saving ? 'Saving...' : 'Save Changes' }}
      </button>
    </form>

    <form class="portal-card space-y-5" @submit.prevent="handleChangePassword">
      <h2 class="text-sm font-bold ws-title">Change Password</h2>
      <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label class="block text-xs font-semibold ws-muted mb-1.5 uppercase tracking-wider">Current Password</label>
          <input v-model="pwForm.current_password" type="password" required class="portal-input" />
        </div>
        <div>
          <label class="block text-xs font-semibold ws-muted mb-1.5 uppercase tracking-wider">New Password</label>
          <input v-model="pwForm.new_password" type="password" required class="portal-input" minlength="8" />
        </div>
      </div>
      <p v-if="pwMessage" :class="pwError ? 'text-red-500' : 'text-emerald-600'" class="text-sm font-medium">{{ pwMessage }}</p>
      <button type="submit" :disabled="changingPw"
 class="text-sm font-medium ws-title ws-soft px-6 py-2.5 rounded-xl hover:bg-slate-200 transition disabled:opacity-50">
        {{ changingPw ? 'Changing...' : 'Change Password' }}
      </button>
    </form>

    <section class="portal-card space-y-5">
      <div>
        <h2 class="text-sm font-bold ws-title">Privacy & Data</h2>
        <p class="mt-1 text-sm ws-muted">Export your account data or request account deletion. Financial, audit, order and project evidence may be retained after personal details are anonymized.</p>
      </div>
      <p v-if="privacyMessage" class="rounded-xl bg-blue-50 p-3 text-sm text-blue-700">{{ privacyMessage }}</p>
      <div class="flex flex-wrap gap-3">
        <button type="button" :disabled="privacyBusy" class="text-sm font-medium text-white bg-blue-600 px-5 py-2.5 rounded-xl disabled:opacity-50" @click="createExport">
          Create data export
        </button>
        <button type="button" :disabled="privacyBusy || pendingDeletion" class="text-sm font-medium text-red-700 bg-red-50 px-5 py-2.5 rounded-xl disabled:opacity-50" @click="requestDeletion">
          {{ pendingDeletion ? 'Deletion requested' : 'Request account deletion' }}
        </button>
      </div>
      <div v-if="privacyRequests.length" class="space-y-2">
        <article v-for="item in privacyRequests" :key="item.id" class="rounded-xl border ws-hairline p-3 text-sm">
          <div class="flex flex-wrap items-center justify-between gap-2">
            <div><span class="font-semibold capitalize">{{ item.request_type }}</span> · {{ item.status }}</div>
            <div class="flex gap-2">
              <button v-if="item.request_type === 'export' && item.status === 'ready'" type="button" class="ws-accent hover:underline" @click="downloadExport(item.id)">Download</button>
              <button v-if="item.status === 'requested'" type="button" class="text-red-600 hover:underline" @click="cancelPrivacy(item.id)">Cancel</button>
            </div>
          </div>
          <p v-if="item.review_reason" class="mt-1 text-xs ws-muted">{{ item.review_reason }}</p>
        </article>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
definePageMeta({ layout: 'procurement', middleware: 'auth' })

const { user, fetchUser } = useAuth()
const { apiFetch } = useApi()
const saving = ref(false)
const changingPw = ref(false)
const pwMessage = ref('')
const pwError = ref(false)
const privacyRequests = ref<any[]>([])
const privacyBusy = ref(false)
const privacyMessage = ref('')
const pendingDeletion = computed(() => privacyRequests.value.some(item => item.request_type === 'delete' && item.status === 'requested'))

const form = reactive({
 full_name: '',
 phone: '',
 country: '',
 language: 'en',
})

const pwForm = reactive({
 current_password: '',
 new_password: '',
})

watch(user, (u) => {
 if (u) {
    Object.assign(form, {
 full_name: u.full_name || '',
 phone: (u as any).phone || '',
 country: (u as any).country || '',
 language: (u as any).language || 'en',
    })
  }
}, { immediate: true })

async function handleSaveProfile() {
 saving.value = true
 try {
 await apiFetch('/auth/me', { method: 'PUT', body: form })
 await fetchUser()
  } catch (e: any) { console.error(e) }
 finally { saving.value = false }
}

async function handleChangePassword() {
 changingPw.value = true
 pwMessage.value = ''
 pwError.value = false
 try {
 await apiFetch('/auth/change-password', { method: 'PUT', body: pwForm })
 pwMessage.value = 'Password changed successfully.'
    Object.assign(pwForm, { current_password: '', new_password: '' })
  } catch (e: any) {
 pwError.value = true
 pwMessage.value = e?.data?.detail || 'Failed to change password.'
  } finally {
 changingPw.value = false
  }
}

async function loadPrivacy() {
 privacyRequests.value = await apiFetch<any[]>('/privacy/requests')
}

async function createExport() {
 privacyBusy.value = true
 privacyMessage.value = ''
 try {
 await apiFetch('/privacy/export', { method: 'POST' })
 privacyMessage.value = 'Your export is ready for download for seven days.'
 await loadPrivacy()
  } catch (e: any) { privacyMessage.value = e?.data?.detail || 'Export could not be created.' }
 finally { privacyBusy.value = false }
}

async function downloadExport(id: string) {
 const blob = await apiFetch<Blob>(`/privacy/exports/${id}`, { responseType: 'blob' })
 const url = URL.createObjectURL(blob)
 const link = document.createElement('a')
 link.href = url
 link.download = 'ainerwise-data-export.json'
 link.click()
  URL.revokeObjectURL(url)
}

async function requestDeletion() {
 if (!confirm('Request account deletion? An administrator will verify the request before personal details are anonymized.')) return
 privacyBusy.value = true
 try {
 await apiFetch('/privacy/delete-request', { method: 'POST' })
 await loadPrivacy()
  } finally { privacyBusy.value = false }
}

async function cancelPrivacy(id: string) {
 await apiFetch(`/privacy/requests/${id}/cancel`, { method: 'POST' })
 await loadPrivacy()
}

onMounted(loadPrivacy)
</script>
