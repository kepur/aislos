<template>
  <div class="space-y-6 max-w-2xl">
    <div>
      <h1 class="text-xl font-bold text-slate-800">{{ $t('portal.profile') }}</h1>
      <p class="text-sm text-slate-400 mt-1">Manage your account information</p>
    </div>

    <!-- User Info -->
    <form class="portal-card space-y-5" @submit.prevent="handleSaveProfile">
      <h2 class="text-sm font-bold text-slate-800">Personal Information</h2>
      <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label class="block text-xs font-semibold text-slate-500 mb-1.5 uppercase tracking-wider">Full Name</label>
          <input v-model="form.full_name" type="text" class="portal-input" />
        </div>
        <div>
          <label class="block text-xs font-semibold text-slate-500 mb-1.5 uppercase tracking-wider">Email</label>
          <input :value="user?.email" type="email" disabled class="portal-input !bg-slate-100 cursor-not-allowed opacity-60" />
        </div>
        <div>
          <label class="block text-xs font-semibold text-slate-500 mb-1.5 uppercase tracking-wider">Phone</label>
          <input v-model="form.phone" type="text" class="portal-input" />
        </div>
        <div>
          <label class="block text-xs font-semibold text-slate-500 mb-1.5 uppercase tracking-wider">Country</label>
          <input v-model="form.country" type="text" class="portal-input" />
        </div>
        <div>
          <label class="block text-xs font-semibold text-slate-500 mb-1.5 uppercase tracking-wider">Language</label>
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

    <!-- Change Password -->
    <form class="portal-card space-y-5" @submit.prevent="handleChangePassword">
      <h2 class="text-sm font-bold text-slate-800">Change Password</h2>
      <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label class="block text-xs font-semibold text-slate-500 mb-1.5 uppercase tracking-wider">Current Password</label>
          <input v-model="pwForm.current_password" type="password" required class="portal-input" />
        </div>
        <div>
          <label class="block text-xs font-semibold text-slate-500 mb-1.5 uppercase tracking-wider">New Password</label>
          <input v-model="pwForm.new_password" type="password" required class="portal-input" minlength="8" />
        </div>
      </div>
      <p v-if="pwMessage" :class="pwError ? 'text-red-500' : 'text-emerald-600'" class="text-sm font-medium">{{ pwMessage }}</p>
      <button type="submit" :disabled="changingPw"
        class="text-sm font-medium text-slate-700 bg-slate-100 px-6 py-2.5 rounded-xl hover:bg-slate-200 transition disabled:opacity-50">
        {{ changingPw ? 'Changing...' : 'Change Password' }}
      </button>
    </form>
  </div>
</template>

<script setup lang="ts">
definePageMeta({ layout: 'portal', middleware: 'auth' })

const { user, fetchUser } = useAuth()
const { apiFetch } = useApi()
const saving = ref(false)
const changingPw = ref(false)
const pwMessage = ref('')
const pwError = ref(false)

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
</script>
