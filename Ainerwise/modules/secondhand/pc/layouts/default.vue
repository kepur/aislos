<template>
  <div class="min-h-screen flex flex-col">
    <header class="sticky top-0 z-40 border-b border-slate-200 bg-white/90 backdrop-blur">
      <div class="mx-auto flex h-16 max-w-7xl items-center gap-4 px-4 sm:px-6 lg:px-8">
        <NuxtLink to="/" class="flex items-center gap-2 whitespace-nowrap">
          <span class="flex h-8 w-8 items-center justify-center rounded-xl bg-brand-600 text-sm font-black text-white">2H</span>
          <span class="text-xl font-bold tracking-tight text-slate-900">2Hands</span>
        </NuxtLink>

        <nav class="hidden items-center gap-6 text-sm font-medium text-slate-600 md:flex">
          <NuxtLink to="/" class="whitespace-nowrap transition-colors hover:text-brand-700">Browse</NuxtLink>
          <NuxtLink to="/sell" class="whitespace-nowrap transition-colors hover:text-brand-700">Sell an item</NuxtLink>
        </nav>

        <div class="flex flex-1 items-center justify-end gap-3">
          <a
            :href="$config.public.aislosSiteUrl"
            class="hidden whitespace-nowrap rounded-full border border-brand-200 bg-brand-50 px-3 py-1.5 text-sm font-semibold text-brand-700 transition-colors hover:bg-brand-100 lg:inline-flex"
          >← AinerWise 官网</a>

          <ClientOnly>
            <template v-if="auth.isLoggedIn">
              <NuxtLink to="/me" class="whitespace-nowrap text-sm font-medium text-slate-700 hover:text-brand-700">
                {{ auth.displayName }}
              </NuxtLink>
              <button class="text-sm text-slate-400 hover:text-slate-600" @click="signOut">Sign out</button>
            </template>
            <NuxtLink v-else to="/login" class="whitespace-nowrap text-sm font-medium text-slate-700 hover:text-brand-700">
              Sign in
            </NuxtLink>
          </ClientOnly>

          <NuxtLink to="/sell" class="btn-primary whitespace-nowrap !px-4 !py-2">Sell</NuxtLink>
        </div>
      </div>
    </header>

    <main class="flex-1">
      <slot />
    </main>

    <footer class="mt-16 border-t border-slate-200 bg-white">
      <div class="mx-auto max-w-7xl px-4 py-10 text-sm text-slate-500 sm:px-6 lg:px-8">
        <div class="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <p>© {{ new Date().getFullYear() }} 2Hands · part of AinerWise</p>
          <p class="max-w-xl text-xs leading-relaxed text-slate-400">
            2Hands never holds your money. Buyer and seller settle directly at pickup —
            the platform keeps the record. A seller's address is only shared with a buyer
            they approve, and can be withdrawn at any time.
          </p>
        </div>
      </div>
    </footer>
  </div>
</template>

<script setup lang="ts">
const auth = useAuthStore()
const router = useRouter()

onMounted(() => auth.hydrate())

function signOut() {
  auth.logout()
  router.push('/')
}
</script>
