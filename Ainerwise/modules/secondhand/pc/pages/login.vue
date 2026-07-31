<template>
  <div class="mx-auto flex max-w-md flex-col justify-center px-4 py-16 sm:px-6">
    <div class="card p-8">
      <div class="mb-6 text-center">
        <span class="mx-auto mb-3 flex h-12 w-12 items-center justify-center rounded-2xl bg-brand-600 text-lg font-black text-white">2H</span>
        <h1 class="text-2xl font-bold text-slate-900">Sign in to 2Hands</h1>
        <p class="mt-1 text-sm text-slate-500">Buy, sell and arrange collection.</p>
      </div>

      <form class="space-y-4" @submit.prevent="submit">
        <div>
          <label class="label" for="email">Email</label>
          <input id="email" v-model="email" type="email" class="input" required autocomplete="email" />
        </div>
        <div>
          <label class="label" for="password">Password</label>
          <input id="password" v-model="password" type="password" class="input" required autocomplete="current-password" />
        </div>
        <p v-if="error" class="rounded-xl bg-rose-50 p-3 text-sm text-rose-700">{{ error }}</p>
        <button type="submit" class="btn-primary w-full" :disabled="busy">
          {{ busy ? 'Signing in…' : 'Sign in' }}
        </button>
      </form>
    </div>
  </div>
</template>

<script setup lang="ts">
const auth = useAuthStore()
const route = useRoute()
const router = useRouter()

const email = ref('')
const password = ref('')
const busy = ref(false)
const error = ref('')

async function submit() {
  busy.value = true
  error.value = ''
  try {
    await auth.login(email.value, password.value)
    router.push((route.query.redirect as string) || '/')
  } catch (err: any) {
    error.value = apiErrorMessage(err, 'Check your email and password')
  } finally {
    busy.value = false
  }
}

onMounted(() => auth.hydrate())
</script>
