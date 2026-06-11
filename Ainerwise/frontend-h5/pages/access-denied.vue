<template>
  <div class="min-h-screen flex items-center justify-center px-6">
    <div class="w-full max-w-sm rounded-3xl border border-slate-200 bg-white p-7 text-center shadow-xl shadow-slate-200/50">
      <div class="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-amber-50 text-2xl">!</div>
      <p class="mt-5 text-[10px] font-bold uppercase tracking-[0.2em] text-amber-500">{{ portal.name }}</p>
      <h1 class="mt-2 text-xl font-bold text-slate-800">Access denied</h1>
      <p class="mt-3 text-sm leading-6 text-slate-500">
        This account is not assigned to this Portal. Portal data remains protected by the shared Core permission layer.
      </p>
      <button class="mt-6 w-full rounded-xl bg-slate-900 py-3 text-sm font-semibold text-white" @click="logout">
        Sign out and switch account
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
definePageMeta({ layout: 'auth' })

const { logout } = useAuth()
const { portal } = usePortalMode()
</script>
