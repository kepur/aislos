<template>
  <div class="min-h-screen bg-slate-50 flex flex-col">
    <!-- Header -->
    <div class="bg-white border-b border-slate-100 px-4 h-14 flex items-center gap-3 pt-safe">
      <button type="button" class="text-slate-600 p-1 -ml-1" @click="$router.back()">
        <svg class="w-6 h-6" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" d="M15 19l-7-7 7-7" />
        </svg>
      </button>
      <span class="font-semibold text-slate-900">{{ $t("auth.create_account") }}</span>
    </div>

    <div class="flex-1 px-6 py-6 pb-10">
      <!-- Role toggle -->
      <div class="flex bg-slate-100 rounded-xl p-1 mb-6">
        <button type="button"
          class="flex-1 py-2 rounded-lg text-sm font-semibold transition-all"
          :class="role === 'BUYER' ? 'bg-white shadow text-primary-700' : 'text-slate-500'"
          @click="role = 'BUYER'"
        >
          {{ $t("auth.i_am_buyer") }}
        </button>
        <button type="button"
          class="flex-1 py-2 rounded-lg text-sm font-semibold transition-all"
          :class="role === 'SUPPLIER_ADMIN' ? 'bg-white shadow text-primary-700' : 'text-slate-500'"
          @click="role = 'SUPPLIER_ADMIN'"
        >
          {{ $t("auth.i_am_supplier") }}
        </button>
      </div>

      <!-- Role description -->
      <div class="mb-5 p-3.5 rounded-xl" :class="role === 'BUYER' ? 'bg-primary-50 border border-primary-100' : 'bg-amber-50 border border-amber-100'">
        <p class="text-sm" :class="role === 'BUYER' ? 'text-primary-700' : 'text-amber-700'">
          <template v-if="role === 'BUYER'">
            🛒 Post what you need and receive competitive offers from verified suppliers.
          </template>
          <template v-else>
            🏭 Get pinged when buyers need what you supply. Submit offers and grow your business.
          </template>
        </p>
      </div>

      <form class="space-y-4" @submit.prevent="handleRegister">
        <div>
          <label class="block text-sm font-medium text-slate-700 mb-1.5">{{ $t("auth.full_name") }}</label>
          <input v-model="form.full_name" type="text" placeholder="Juan dela Cruz" class="input-field" required />
        </div>

        <div>
          <label class="block text-sm font-medium text-slate-700 mb-1.5">{{ $t("auth.email") }}</label>
          <input v-model="form.email" type="email" placeholder="you@company.com" class="input-field" required />
        </div>

        <div>
          <label class="block text-sm font-medium text-slate-700 mb-1.5">{{ $t("auth.phone_optional") }}</label>
          <input v-model="form.phone" type="tel" placeholder="+63 9XX XXX XXXX" class="input-field" />
        </div>

        <div>
          <label class="block text-sm font-medium text-slate-700 mb-1.5">{{ $t("auth.password") }}</label>
          <div class="relative">
            <input
              v-model="form.password"
              :type="showPw ? 'text' : 'password'"
              placeholder="Min 8 characters"
              class="input-field pr-12"
              required
              minlength="8"
            />
            <button type="button" class="absolute right-4 top-1/2 -translate-y-1/2 text-slate-400" @click="showPw = !showPw">
              <svg class="w-5 h-5" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
              </svg>
            </button>
          </div>
        </div>

        <!-- Supplier extra fields -->
        <template v-if="role === 'SUPPLIER_ADMIN'">
          <div>
            <label class="block text-sm font-medium text-slate-700 mb-1.5">Company Name</label>
            <input v-model="form.company_name" type="text" placeholder="Your company name" class="input-field" />
          </div>
          <div>
            <label class="block text-sm font-medium text-slate-700 mb-1.5">City</label>
            <input v-model="form.city" type="text" placeholder="Cebu City" class="input-field" />
          </div>
        </template>

        <p v-if="errors.general" class="bg-red-50 text-red-700 text-sm px-4 py-3 rounded-xl border border-red-200">
          {{ errors.general }}
        </p>

        <div class="pt-2">
          <p class="text-xs text-slate-500 mb-4 leading-relaxed">
            By creating an account, you agree to our Terms of Service and Privacy Policy.
          </p>
          <button type="submit" class="btn-primary" :disabled="loading">
            <span v-if="!loading">{{ $t("auth.create_account") }}</span>
            <span v-else class="flex items-center justify-center gap-2">
              <svg class="animate-spin w-4 h-4" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
              </svg>
              Creating…
            </span>
          </button>
        </div>
      </form>

      <div class="text-center mt-5">
        <span class="text-sm text-slate-500">{{ $t("auth.have_account") }} </span>
        <NuxtLink to="/auth/login" class="text-sm text-primary-600 font-semibold">{{ $t("auth.sign_in") }}</NuxtLink>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { UserRole } from "~/types";
import { useI18n } from "vue-i18n";

definePageMeta({ layout: "default", middleware: ["guest"] });
useHead({ title: "Create Account" });

const authStore = useAuthStore();
const router = useRouter();
const route = useRoute();
const { t } = useI18n({ useScope: "global" });

const role = ref<UserRole>((route.query.role as UserRole) || "BUYER");
const showPw = ref(false);
const loading = ref(false);
const errors = ref<Record<string, string>>({});

const form = reactive({
  full_name: "",
  email: "",
  phone: "",
  password: "",
  company_name: "",
  city: "",
});

async function handleRegister() {
  errors.value = {};
  if (!form.full_name.trim()) {
    errors.value.general = t("auth.full_name_required");
    return;
  }
  if (!form.email.trim()) {
    errors.value.general = t("auth.email_required");
    return;
  }
  if (!form.password || form.password.length < 8) {
    errors.value.general = t("auth.password_min");
    return;
  }
  loading.value = true;
  try {
    await authStore.register({
      email: form.email,
      password: form.password,
      full_name: form.full_name,
      role: role.value,
      phone: form.phone || undefined,
    });
    if (authStore.isBuyer) {
      router.push("/buyer/home");
    } else {
      router.push("/supplier/pings");
    }
  } catch (err: unknown) {
    const e = err as { data?: { detail?: string | Array<{ msg: string }> } };
    const detail = e?.data?.detail;
    errors.value.general = Array.isArray(detail) ? detail[0]?.msg : (detail || "Registration failed");
  } finally {
    loading.value = false;
  }
}
</script>
