<template>
  <div class="min-h-screen bg-slate-50 flex flex-col">
    <div class="bg-white border-b border-slate-100 px-4 h-14 flex items-center gap-3 sticky top-0 z-40 pt-safe">
      <button type="button" class="text-slate-600 p-1 -ml-1" @click="$router.back()">
        <svg class="w-6 h-6" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" d="M15 19l-7-7 7-7" />
        </svg>
      </button>
      <h1 class="font-semibold text-slate-900 flex-1">Change Password</h1>
    </div>

    <div class="flex-1 px-4 py-6 space-y-4">
      <div>
        <label class="block text-sm font-medium text-slate-700 mb-1.5">Current Password</label>
        <input v-model="form.current_password" type="password" class="input-field" placeholder="••••••••" autocomplete="current-password" />
      </div>
      <div>
        <label class="block text-sm font-medium text-slate-700 mb-1.5">New Password</label>
        <input v-model="form.new_password" type="password" class="input-field" placeholder="••••••••" autocomplete="new-password" />
        <p class="text-xs text-slate-400 mt-1">At least 8 characters</p>
      </div>
      <div>
        <label class="block text-sm font-medium text-slate-700 mb-1.5">Confirm New Password</label>
        <input v-model="form.confirm_password" type="password" class="input-field" placeholder="••••••••" autocomplete="new-password" />
      </div>

      <p v-if="success" class="bg-green-50 text-green-700 text-sm px-4 py-3 rounded-xl border border-green-200">
        Password changed. Please log in again.
      </p>
      <p v-if="error" class="bg-red-50 text-red-700 text-sm px-4 py-3 rounded-xl border border-red-200">{{ error }}</p>
    </div>

    <div class="sticky-bottom-action">
      <button type="button" class="btn-primary" :disabled="loading" @click="save">
        <span v-if="!loading">Change Password</span>
        <span v-else>Saving…</span>
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
definePageMeta({ layout: "default", middleware: ["auth"] });
useHead({ title: "Change Password" });

const authStore = useAuthStore();
const config = useRuntimeConfig();
const router = useRouter();
const loading = ref(false);
const success = ref(false);
const error = ref("");

const form = reactive({
  current_password: "",
  new_password: "",
  confirm_password: "",
});

async function save() {
  error.value = "";
  if (form.new_password.length < 8) { error.value = "New password must be at least 8 characters"; return; }
  if (form.new_password !== form.confirm_password) { error.value = "Passwords do not match"; return; }
  loading.value = true;
  try {
    await $fetch(`${config.public.apiBase}/users/me/password`, {
      method: "POST",
      headers: { Authorization: `Bearer ${authStore.accessToken}` },
      body: { current_password: form.current_password, new_password: form.new_password },
    });
    success.value = true;
    setTimeout(async () => {
      await authStore.logout();
      router.push("/auth/login");
    }, 1500);
  } catch (err: unknown) {
    const e = err as { data?: { detail?: string } };
    error.value = e?.data?.detail || "Failed to change password";
  } finally {
    loading.value = false;
  }
}
</script>
