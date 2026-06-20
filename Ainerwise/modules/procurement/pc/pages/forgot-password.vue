<template>
  <div class="min-h-[80vh] flex items-center justify-center bg-slate-50 px-4 py-12 sm:px-6 lg:px-8">
    <div class="w-full max-w-md rounded-2xl bg-white p-8 shadow-xl">
      <div class="text-center">
        <div class="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-indigo-50 text-indigo-600">
          <svg class="h-7 w-7" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" d="M15 7a2 2 0 012 2m4 0a6 6 0 01-7.743 5.743L11 17H9v2H7v2H4a1 1 0 01-1-1v-2.586a1 1 0 01.293-.707l5.964-5.964A6 6 0 1121 9z" />
          </svg>
        </div>
        <h1 class="mt-5 text-3xl font-extrabold tracking-tight text-slate-900">Reset your password</h1>
        <p class="mt-2 text-sm text-slate-600">
          Enter the email tied to your AinerWise Procurement account. If the account exists, we will send a one-time reset link.
        </p>
      </div>

      <form v-if="!sent" class="mt-8 space-y-5" @submit.prevent="requestReset">
        <div>
          <label class="block text-sm font-medium text-slate-700">Email address</label>
          <div class="relative mt-1">
            <span class="pointer-events-none absolute inset-y-0 left-3 flex items-center">
              <svg class="h-4 w-4 text-slate-400" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
              </svg>
            </span>
            <input
              v-model="email"
              type="email"
              required
              autocomplete="email"
              placeholder="you@company.com"
              class="w-full rounded-lg border border-slate-200 bg-white py-3 pl-9 pr-4 text-sm text-slate-800 shadow-sm focus:border-indigo-400 focus:outline-none focus:ring-2 focus:ring-indigo-200"
            />
          </div>
        </div>

        <div v-if="error" class="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          {{ error }}
        </div>

        <UButton type="submit" color="indigo" block size="xl" class="w-full justify-center font-semibold shadow-md" :loading="loading">
          Send reset link
        </UButton>
      </form>

      <div v-else class="mt-8 rounded-2xl border border-emerald-200 bg-emerald-50 p-5 text-center">
        <p class="font-semibold text-emerald-900">Check your inbox</p>
        <p class="mt-2 text-sm text-emerald-700">
          If an active account exists for <span class="font-semibold">{{ email }}</span>, a reset link has been sent.
        </p>
      </div>

      <div class="mt-6 text-center">
        <NuxtLink to="/login" class="text-sm font-medium text-indigo-600 hover:text-indigo-500">
          Back to sign in
        </NuxtLink>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
definePageMeta({ middleware: "guest" });

const config = useRuntimeConfig();
const email = ref("");
const loading = ref(false);
const sent = ref(false);
const error = ref("");

async function requestReset() {
  if (loading.value) return;
  loading.value = true;
  error.value = "";
  try {
    await $fetch(`${config.public.apiBase}/auth/request-password-reset`, {
      method: "POST",
      body: { email: email.value },
    });
    sent.value = true;
  } catch {
    // Keep the response generic to avoid account enumeration.
    sent.value = true;
  } finally {
    loading.value = false;
  }
}
</script>
