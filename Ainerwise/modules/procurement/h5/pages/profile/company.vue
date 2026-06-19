<template>
  <div class="min-h-screen bg-slate-50 flex flex-col">
    <div class="bg-white border-b border-slate-100 px-4 h-14 flex items-center gap-3 sticky top-0 z-40 pt-safe">
      <button type="button" class="text-slate-600 p-1 -ml-1" @click="$router.back()">
        <svg class="w-6 h-6" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" d="M15 19l-7-7 7-7" />
        </svg>
      </button>
      <h1 class="font-semibold text-slate-900 flex-1">Company Profile</h1>
    </div>

    <div v-if="loading" class="flex-1 flex items-center justify-center">
      <div class="w-8 h-8 border-4 border-primary-200 border-t-primary-600 rounded-full animate-spin"></div>
    </div>

    <div v-else class="flex-1 overflow-y-auto pb-28">
      <div class="mx-4 mt-4 card space-y-4">
        <div v-if="company" class="flex items-center gap-4">
          <div class="w-14 h-14 bg-primary-100 rounded-2xl flex items-center justify-center text-2xl font-bold text-primary-700">
            {{ company.name?.charAt(0) }}
          </div>
          <div>
            <h2 class="font-bold text-slate-900">{{ company.name }}</h2>
            <span class="text-xs px-2 py-0.5 rounded-full font-medium"
              :class="company.verification_level === 'BUSINESS' ? 'bg-green-100 text-green-700' : company.verification_level === 'BASIC' ? 'bg-blue-100 text-blue-700' : 'bg-slate-100 text-slate-500'">
              {{ company.verification_level }} verified
            </span>
          </div>
        </div>

        <div v-if="company" class="divider -mx-4"></div>

        <div class="space-y-3">
          <div>
            <label class="block text-sm font-medium text-slate-700 mb-1.5">Company Name</label>
            <input v-model="form.name" class="input-field" placeholder="Legal company name" />
          </div>
          <div>
            <label class="block text-sm font-medium text-slate-700 mb-1.5">TIN / Registration Number</label>
            <input v-model="form.tax_id" class="input-field" placeholder="Optional" />
          </div>
          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="block text-sm font-medium text-slate-700 mb-1.5">Country</label>
              <input v-model="form.country" class="input-field" placeholder="Philippines" />
            </div>
            <div>
              <label class="block text-sm font-medium text-slate-700 mb-1.5">City</label>
              <input v-model="form.city" class="input-field" placeholder="Cebu" />
            </div>
          </div>
          <div>
            <label class="block text-sm font-medium text-slate-700 mb-1.5">Business Address</label>
            <textarea v-model="form.address" class="input-field min-h-20 resize-none" placeholder="Office, warehouse or billing address" />
          </div>
        </div>
      </div>

      <div v-if="company" class="mx-4 mt-4 card grid grid-cols-2 gap-3 text-sm">
        <div>
          <p class="text-xs text-slate-400 uppercase tracking-wide font-medium">Status</p>
          <p class="text-slate-800 font-medium mt-0.5">{{ company.status }}</p>
        </div>
        <div>
          <p class="text-xs text-slate-400 uppercase tracking-wide font-medium">Member Since</p>
          <p class="text-slate-800 font-medium mt-0.5">{{ formatDate(company.created_at) }}</p>
        </div>
      </div>

      <p v-if="success" class="mx-4 mt-4 bg-green-50 text-green-700 text-sm px-4 py-3 rounded-xl border border-green-200">
        Company profile saved.
      </p>
      <p v-if="error" class="mx-4 mt-4 bg-red-50 text-red-700 text-sm px-4 py-3 rounded-xl border border-red-200">{{ error }}</p>

      <div class="mx-4 mt-4">
        <NuxtLink to="/verification">
          <button type="button" class="btn-secondary text-sm py-3">
            View Verification Status
          </button>
        </NuxtLink>
      </div>
    </div>

    <div v-if="!loading" class="sticky-bottom-action">
      <button type="button" class="btn-primary" :disabled="saving || !form.name || !form.country" @click="saveCompany">
        <span v-if="!saving">{{ company ? "Save Company Profile" : "Create Company Profile" }}</span>
        <span v-else>Saving…</span>
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { Company } from "~/types";

definePageMeta({ layout: "default", middleware: ["auth"] });
useHead({ title: "Company Profile" });

const authStore = useAuthStore();
const config = useRuntimeConfig();
const { formatDate } = useApiUtils();

const loading = ref(true);
const saving = ref(false);
const success = ref(false);
const error = ref("");
const company = ref<Company | null>(null);

const form = reactive({
  name: "",
  tax_id: "",
  country: "Philippines",
  city: "Cebu",
  address: "",
});

function syncForm(next: Company | null) {
  form.name = next?.name || "";
  form.tax_id = next?.tax_id || "";
  form.country = next?.country || "Philippines";
  form.city = next?.city || "Cebu";
  form.address = next?.address || "";
}

onMounted(async () => {
  try {
    company.value = await $fetch<Company>(`${config.public.apiBase}/companies/my`, {
      headers: { Authorization: `Bearer ${authStore.accessToken}` },
    });
    syncForm(company.value);
  } catch {
    company.value = null;
    syncForm(null);
  } finally {
    loading.value = false;
  }
});

async function saveCompany() {
  saving.value = true;
  success.value = false;
  error.value = "";
  const body = {
    name: form.name,
    tax_id: form.tax_id || undefined,
    country: form.country,
    city: form.city || undefined,
    address: form.address || undefined,
  };
  try {
    company.value = await $fetch<Company>(
      `${config.public.apiBase}${company.value ? "/companies/me" : "/companies"}`,
      {
        method: company.value ? "PATCH" : "POST",
        headers: { Authorization: `Bearer ${authStore.accessToken}` },
        body,
      },
    );
    syncForm(company.value);
    success.value = true;
  } catch (err: unknown) {
    const e = err as { data?: { detail?: string } };
    error.value = e?.data?.detail || "Failed to save company profile";
  } finally {
    saving.value = false;
  }
}
</script>
