<template>
  <div class="min-h-screen bg-slate-50 flex flex-col">
    <div class="bg-white border-b border-slate-100 px-4 h-14 flex items-center gap-3 pt-safe">
      <button type="button" class="text-slate-600 p-1 -ml-1" @click="$router.back()">
        <svg class="w-6 h-6" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" d="M15 19l-7-7 7-7" />
        </svg>
      </button>
      <span class="font-semibold text-slate-900">Reset Password</span>
    </div>

    <div class="flex-1 px-6 py-8">
      <div v-if="!sent">
        <div class="w-16 h-16 bg-amber-100 rounded-2xl flex items-center justify-center mx-auto mb-4">
          <svg class="w-8 h-8 text-amber-600" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" d="M15 7a2 2 0 012 2m4 0a6 6 0 01-7.743 5.743L11 17H9v2H7v2H4a1 1 0 01-1-1v-2.586a1 1 0 01.293-.707l5.964-5.964A6 6 0 1121 9z" />
          </svg>
        </div>
        <h1 class="text-2xl font-bold text-slate-900 text-center mb-2">Forgot Password?</h1>
        <p class="text-slate-500 text-sm text-center mb-8">Enter your email and we'll send a reset link.</p>

        <form @submit.prevent="handleReset">
          <div class="mb-4">
            <label class="block text-sm font-medium text-slate-700 mb-1.5">Email</label>
            <input v-model="email" type="email" class="input-field" placeholder="you@company.com" required />
          </div>
          <button type="submit" class="btn-primary" :disabled="loading">
            {{ loading ? "Sending…" : "Send Reset Link" }}
          </button>
        </form>
      </div>

      <div v-else class="text-center py-12">
        <div class="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
          <svg class="w-8 h-8 text-green-600" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7" />
          </svg>
        </div>
        <h2 class="text-xl font-bold text-slate-900 mb-2">Check your inbox</h2>
        <p class="text-slate-500 text-sm mb-6">We sent a reset link to <strong>{{ email }}</strong></p>
        <NuxtLink to="/auth/login">
          <button type="button" class="btn-primary">Back to Sign In</button>
        </NuxtLink>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
definePageMeta({ layout: "default" });
useHead({ title: "Reset Password" });

const config = useRuntimeConfig();
const email = ref("");
const loading = ref(false);
const sent = ref(false);

async function handleReset() {
  loading.value = true;
  try {
    await $fetch(`${config.public.apiBase}/auth/reset-password`, {
      method: "POST",
      body: { email: email.value },
    });
  } catch {
    // Show success anyway to prevent email enumeration
  } finally {
    sent.value = true;
    loading.value = false;
  }
}
</script>
