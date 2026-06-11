<template>
  <div class="px-4 py-4">
    <!-- Guest view -->
    <div v-if="!isLoggedIn" class="space-y-4">
      <!-- Login prompt card -->
      <div class="bg-white rounded-2xl p-6 text-center border border-slate-100 shadow-sm">
        <div class="w-20 h-20 mx-auto rounded-full bg-gradient-to-br from-blue-100 to-indigo-100 flex items-center justify-center mb-4">
          <svg class="w-10 h-10 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="1.5">
            <path stroke-linecap="round" stroke-linejoin="round" d="M15.75 6a3.75 3.75 0 1 1-7.5 0 3.75 3.75 0 0 1 7.5 0ZM4.501 20.118a7.5 7.5 0 0 1 14.998 0A17.933 17.933 0 0 1 12 21.75c-2.676 0-5.216-.584-7.499-1.632Z" />
          </svg>
        </div>
        <h2 class="text-lg font-bold text-slate-800">Welcome to AinerWise</h2>
        <p class="text-sm text-slate-400 mt-2">Login to manage projects and get AI consultation</p>
        <div class="mt-5 space-y-2">
          <NuxtLink to="/login"
            class="block w-full text-sm font-semibold bg-blue-500 text-white py-3 rounded-xl shadow-md shadow-blue-500/20">
            Login
          </NuxtLink>
          <NuxtLink to="/register"
            class="block w-full text-sm font-semibold text-blue-500 bg-blue-50 py-3 rounded-xl">
            Create Account
          </NuxtLink>
        </div>
      </div>

      <!-- Quick links for guests -->
      <div class="space-y-2">
        <NuxtLink to="/about" class="flex items-center justify-between bg-white rounded-xl px-4 py-3.5 border border-slate-100 shadow-sm active:bg-slate-50">
          <div class="flex items-center gap-3">
            <span class="text-lg">🏢</span>
            <span class="text-sm font-medium text-slate-700">About AinerWise</span>
          </div>
          <svg class="w-4 h-4 text-slate-300" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="m8.25 4.5 7.5 7.5-7.5 7.5" />
          </svg>
        </NuxtLink>
        <NuxtLink to="/contact" class="flex items-center justify-between bg-white rounded-xl px-4 py-3.5 border border-slate-100 shadow-sm active:bg-slate-50">
          <div class="flex items-center gap-3">
            <span class="text-lg">📧</span>
            <span class="text-sm font-medium text-slate-700">Contact Us</span>
          </div>
          <svg class="w-4 h-4 text-slate-300" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="m8.25 4.5 7.5 7.5-7.5 7.5" />
          </svg>
        </NuxtLink>
        <NuxtLink to="/services" class="flex items-center justify-between bg-white rounded-xl px-4 py-3.5 border border-slate-100 shadow-sm active:bg-slate-50">
          <div class="flex items-center gap-3">
            <span class="text-lg">🔧</span>
            <span class="text-sm font-medium text-slate-700">Services</span>
          </div>
          <svg class="w-4 h-4 text-slate-300" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="m8.25 4.5 7.5 7.5-7.5 7.5" />
          </svg>
        </NuxtLink>
      </div>
    </div>

    <!-- Logged in view -->
    <template v-else>
      <!-- User card -->
      <div class="bg-white rounded-2xl p-5 border border-slate-100 shadow-sm mb-4">
        <div class="flex items-center gap-4">
          <div class="w-16 h-16 rounded-full bg-gradient-to-br from-blue-400 to-indigo-500 flex items-center justify-center shadow-lg shadow-blue-500/20">
            <span class="text-xl font-bold text-white">{{ userInitial }}</span>
          </div>
          <div>
            <h2 class="text-lg font-bold text-slate-800">{{ user?.full_name || 'User' }}</h2>
            <p class="text-xs text-slate-400">{{ user?.email }}</p>
            <span class="inline-block mt-1 text-[10px] font-semibold text-blue-500 bg-blue-50 px-2 py-0.5 rounded-full">{{ user?.role }}</span>
          </div>
        </div>
      </div>

      <!-- Profile form -->
      <form @submit.prevent="handleSaveProfile" class="bg-white rounded-2xl p-4 border border-slate-100 shadow-sm space-y-4 mb-4">
        <h3 class="text-sm font-bold text-slate-800">Personal Information</h3>
        <div class="space-y-3">
          <div>
            <label class="block text-[10px] font-semibold text-slate-400 mb-1 uppercase tracking-wider">Full Name</label>
            <input v-model="form.full_name" type="text"
              class="w-full text-sm border border-slate-200 rounded-xl px-3 py-2.5 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-300" />
          </div>
          <div>
            <label class="block text-[10px] font-semibold text-slate-400 mb-1 uppercase tracking-wider">Phone</label>
            <input v-model="form.phone" type="text"
              class="w-full text-sm border border-slate-200 rounded-xl px-3 py-2.5 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-300" />
          </div>
          <div>
            <label class="block text-[10px] font-semibold text-slate-400 mb-1 uppercase tracking-wider">Language</label>
            <select v-model="form.language"
              class="w-full text-sm border border-slate-200 rounded-xl px-3 py-2.5 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-300 bg-white">
              <option value="en">English</option>
              <option value="zh">中文</option>
              <option value="sr">Srpski</option>
            </select>
          </div>
        </div>
        <button type="submit" :disabled="saving"
          class="w-full text-sm font-semibold bg-blue-500 text-white py-2.5 rounded-xl shadow-sm disabled:opacity-50">
          {{ saving ? 'Saving...' : 'Save Changes' }}
        </button>
      </form>

      <!-- Actions -->
      <div class="space-y-2">
        <NuxtLink to="/about" class="flex items-center justify-between bg-white rounded-xl px-4 py-3.5 border border-slate-100 shadow-sm">
          <div class="flex items-center gap-3">
            <span class="text-lg">🏢</span>
            <span class="text-sm font-medium text-slate-700">About</span>
          </div>
          <svg class="w-4 h-4 text-slate-300" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="m8.25 4.5 7.5 7.5-7.5 7.5" />
          </svg>
        </NuxtLink>
        <NuxtLink to="/contact" class="flex items-center justify-between bg-white rounded-xl px-4 py-3.5 border border-slate-100 shadow-sm">
          <div class="flex items-center gap-3">
            <span class="text-lg">📧</span>
            <span class="text-sm font-medium text-slate-700">Contact</span>
          </div>
          <svg class="w-4 h-4 text-slate-300" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="m8.25 4.5 7.5 7.5-7.5 7.5" />
          </svg>
        </NuxtLink>
        <button @click="handleLogout"
          class="flex items-center justify-between w-full bg-white rounded-xl px-4 py-3.5 border border-red-100 shadow-sm text-left">
          <div class="flex items-center gap-3">
            <span class="text-lg">🚪</span>
            <span class="text-sm font-medium text-red-500">Logout</span>
          </div>
        </button>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
const { user, isLoggedIn, logout, fetchUser } = useAuth()
const { apiFetch } = useApi()
const saving = ref(false)

const form = reactive({
  full_name: '',
  phone: '',
  language: 'en',
})

const userInitial = computed(() => {
  const name = user.value?.full_name || user.value?.email || 'U'
  return name.charAt(0).toUpperCase()
})

watch(user, (u) => {
  if (u) {
    Object.assign(form, {
      full_name: u.full_name || '',
      phone: (u as any).phone || '',
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

function handleLogout() {
  logout()
  navigateTo('/')
}
</script>
