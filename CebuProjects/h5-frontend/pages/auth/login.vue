<template>
  <div class="min-h-screen bg-slate-50 flex flex-col">
    <!-- Header -->
    <div class="bg-white border-b border-slate-100 px-4 h-14 flex items-center gap-3 pt-safe">
      <button type="button" class="text-slate-600 p-1 -ml-1" @click="$router.back()">
        <svg class="w-6 h-6" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" d="M15 19l-7-7 7-7" />
        </svg>
      </button>
      <span class="font-semibold text-slate-900">{{ $t("auth.sign_in") }}</span>
    </div>

    <div class="flex-1 px-6 py-8">
      <!-- Logo -->
      <div class="text-center mb-6">
        <div class="w-16 h-16 bg-primary-600 rounded-2xl flex items-center justify-center mx-auto mb-3 shadow-lg">
          <span class="text-white font-extrabold text-2xl">PP</span>
        </div>
        <h1 class="text-2xl font-bold text-slate-900">{{ $t("auth.welcome_back") }}</h1>
        <p class="text-slate-500 text-sm mt-1">Sign in to your ProcurePing account</p>
      </div>

      <!-- Demo Mode Banner -->
      <div class="mb-5 rounded-xl border border-amber-200 bg-amber-50 p-4">
        <p class="text-amber-800 text-xs font-semibold mb-2">🧪 Demo quick access accounts</p>
        <div class="space-y-1.5">
          <button type="button"
            v-for="acc in demoAccounts"
            :key="acc.email"
            class="w-full flex items-center justify-between text-left text-xs bg-white rounded-lg px-3 py-2 border border-amber-100 hover:bg-amber-50 transition"
            @click="fillDemo(acc)"
          >
            <span class="font-medium text-slate-700">{{ acc.label }}</span>
            <span class="text-slate-400 font-mono">{{ acc.email }} / {{ acc.password }}</span>
          </button>
        </div>
        <p class="text-amber-600 text-xs mt-2">
          {{ $t("auth.demo_tip") }}
          <span v-if="!authStore.isDemoMode"> Demo account login may be disabled by system mode.</span>
        </p>
      </div>

      <!-- Form -->
      <form class="space-y-4" @submit.prevent="handleLogin">
        <div>
          <label class="block text-sm font-medium text-slate-700 mb-1.5">{{ $t("auth.email") }}</label>
          <input
            v-model="email"
            type="email"
            autocomplete="email"
            placeholder="you@company.com"
            class="input-field"
            :class="{ 'border-red-400 ring-red-200': errors.email }"
            required
          />
          <p v-if="errors.email" class="text-red-500 text-xs mt-1">{{ errors.email }}</p>
        </div>

        <div>
          <div class="flex justify-between mb-1.5">
            <label class="text-sm font-medium text-slate-700">{{ $t("auth.password") }}</label>
            <NuxtLink to="/auth/reset-password" class="text-xs text-primary-600 font-medium">{{ $t("auth.forgot_password") }}</NuxtLink>
          </div>
          <div class="relative">
            <input
              v-model="password"
              :type="showPw ? 'text' : 'password'"
              autocomplete="current-password"
              placeholder="••••••••"
              class="input-field pr-12"
              :class="{ 'border-red-400': errors.password }"
              required
            />
            <button
              type="button"
              class="absolute right-4 top-1/2 -translate-y-1/2 text-slate-400"
              @click="showPw = !showPw"
            >
              <svg class="w-5 h-5" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
                <path v-if="!showPw" stroke-linecap="round" stroke-linejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                <path v-else stroke-linecap="round" stroke-linejoin="round" d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l3.59 3.59m0 0A9.953 9.953 0 0112 5c4.478 0 8.268 2.943 9.543 7a10.025 10.025 0 01-4.132 5.411m0 0L21 21" />
              </svg>
            </button>
          </div>
        </div>

        <p v-if="errors.general" class="bg-red-50 text-red-700 text-sm px-4 py-3 rounded-xl border border-red-200">
          {{ errors.general }}
        </p>

        <button type="submit" class="btn-primary mt-2" :disabled="loading">
          <span v-if="!loading">{{ $t("auth.sign_in") }}</span>
          <span v-else class="flex items-center justify-center gap-2">
            <svg class="animate-spin w-4 h-4" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
            </svg>
            Signing in…
          </span>
        </button>
      </form>

      <!-- Divider -->
      <div class="flex items-center gap-3 my-6">
        <div class="flex-1 h-px bg-slate-200"></div>
        <span class="text-xs text-slate-400 font-medium">OR</span>
        <div class="flex-1 h-px bg-slate-200"></div>
      </div>

      <!-- Register Links -->
      <div v-if="authStore.isRegistrationEnabled" class="space-y-3">
        <NuxtLink to="/auth/register?role=BUYER">
          <button type="button" class="btn-secondary text-sm py-3">{{ $t("auth.register_buyer") }}</button>
        </NuxtLink>
        <NuxtLink to="/auth/register?role=SUPPLIER_ADMIN">
          <button type="button" class="btn-ghost text-sm py-3">{{ $t("auth.register_supplier") }}</button>
        </NuxtLink>
      </div>
      <div v-else class="text-center text-xs text-slate-400 px-4">
        Registration is currently by invitation only. Contact an admin to get access.
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
definePageMeta({ layout: "default", middleware: ["guest"] });
useHead({ title: "Sign In" });

const authStore = useAuthStore();
const router = useRouter();
const route = useRoute();

const email = ref("");
const password = ref("");
const showPw = ref(false);
const loading = ref(false);
const errors = ref<Record<string, string>>({});

const demoAccounts = [
  { label: "Demo Buyer", email: "buyer@demo.procureping", password: "123" },
  { label: "Demo Supplier", email: "supplier@demo.procureping", password: "123" },
];

function fillDemo(acc: { email: string; password: string }) {
  email.value = acc.email;
  password.value = acc.password;
}

onMounted(async () => {
  await authStore.fetchSystemMode();
});

async function handleLogin() {
  errors.value = {};
  if (!email.value) { errors.value.email = "Email is required"; return; }
  if (!password.value) { errors.value.password = "Password is required"; return; }

  loading.value = true;
  try {
    await authStore.login(email.value, password.value);
    // return_url takes priority (from marketplace CTA, etc.)
    const returnUrl = route.query.return_url as string;
    const redirect = route.query.redirect as string;
    if (returnUrl) {
      router.push(returnUrl);
    } else if (redirect) {
      router.push(redirect);
    } else if (authStore.isBuyer) {
      router.push("/buyer/home");
    } else if (authStore.isSupplier) {
      router.push("/supplier/pings");
    } else {
      router.push("/admin/dashboard");
    }
  } catch (err: unknown) {
    const e = err as { data?: { detail?: string } };
    errors.value.general = e?.data?.detail || "Invalid email or password";
  } finally {
    loading.value = false;
  }
}
</script>
