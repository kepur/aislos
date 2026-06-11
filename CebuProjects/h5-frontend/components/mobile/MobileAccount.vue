<template>
  <div class="min-h-screen bg-slate-50">
    <div class="bg-white border-b border-slate-100 px-4 h-14 flex items-center gap-3 sticky top-0 z-40 pt-safe">
      <button v-if="showBack" class="text-slate-600 p-1 -ml-1" @click="$router.back()">
        <svg class="w-6 h-6" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" d="M15 19l-7-7 7-7" />
        </svg>
      </button>
      <h1 class="font-bold text-slate-900">{{ title }}</h1>
    </div>

    <div v-if="authStore.user">
      <div class="bg-white mx-4 mt-4 rounded-2xl p-5 shadow-card">
        <div class="flex items-center gap-4">
          <div class="relative w-16 h-16 rounded-full bg-primary-100 flex items-center justify-center text-2xl font-extrabold text-primary-700">
            {{ authStore.displayName.charAt(0).toUpperCase() }}
            <span
              v-if="trustProfile"
              class="absolute -top-1 -right-1 h-6 min-w-6 px-1 rounded-full bg-amber-500 text-white text-[10px] font-bold leading-none flex items-center justify-center"
              :title="tierLabel(trustProfile.trust_tier)"
            >
              👑
            </span>
          </div>
          <div class="flex-1 min-w-0">
            <h2 class="font-bold text-slate-900 text-lg leading-tight truncate">{{ authStore.displayName }}</h2>
            <p class="text-slate-500 text-sm truncate">{{ authStore.user.email }}</p>
            <span class="inline-flex items-center mt-1.5 px-2 py-0.5 rounded-full text-xs font-medium"
                  :class="authStore.isBuyer ? 'bg-primary-100 text-primary-700' : 'bg-amber-100 text-amber-700'">
              {{ getRoleLabel(authStore.user.role) }}
            </span>
          </div>
        </div>
      </div>

      <div v-if="trustProfile" class="bg-white mx-4 mt-3 rounded-2xl p-4 shadow-card">
        <div class="flex items-center justify-between mb-3">
          <div>
            <p class="text-xs font-semibold text-slate-500 uppercase tracking-wide">{{ $t("profile.trust_score") }}</p>
            <p class="text-2xl font-extrabold text-slate-900">{{ trustProfile.trust_score }}</p>
          </div>
          <span class="px-2.5 py-1 rounded-full text-xs font-bold" :class="tierClass(trustProfile.trust_tier)">
            {{ tierLabel(trustProfile.trust_tier) }}
          </span>
        </div>
        <div class="grid grid-cols-3 gap-2 text-center">
          <div class="bg-slate-50 rounded-xl p-2">
              <p class="text-[10px] text-slate-400">{{ $t("trust.deal_rate") }}</p>
            <p class="font-bold text-slate-800">{{ trustProfile.deal_completion_rate }}%</p>
          </div>
          <div class="bg-slate-50 rounded-xl p-2">
              <p class="text-[10px] text-slate-400">{{ $t("trust.profile_completion") }}</p>
            <p class="font-bold text-slate-800">{{ trustProfile.profile_completion_rate }}%</p>
          </div>
          <div class="bg-slate-50 rounded-xl p-2">
              <p class="text-[10px] text-slate-400">{{ $t("trust.deposit") }}</p>
            <p class="font-bold text-slate-800">{{ formatDeposit(trustProfile.deposit_amount_minor, trustProfile.deposit_currency) }}</p>
          </div>
        </div>
      </div>

      <div class="mx-4 mt-4 grid grid-cols-2 gap-3">
        <button v-for="item in quickItems" :key="item.label" class="card text-left active:bg-slate-50" @click="item.action()">
          <div class="w-10 h-10 rounded-xl flex items-center justify-center mb-3" :class="item.iconBg">
            <span class="text-lg">{{ item.icon }}</span>
          </div>
          <p class="text-sm font-bold text-slate-900">{{ item.label }}</p>
          <p class="text-xs text-slate-500 mt-1">{{ item.desc }}</p>
        </button>
      </div>

      <div class="mx-4 mt-4">
        <p class="section-title px-0">Account</p>
        <div class="bg-white rounded-2xl shadow-card overflow-hidden">
          <button v-for="item in accountItems" :key="item.label" class="list-item w-full border-b last:border-0 border-slate-50" @click="item.action?.()">
            <div class="w-9 h-9 rounded-xl flex items-center justify-center flex-shrink-0" :class="item.iconBg">
              <span class="text-lg">{{ item.icon }}</span>
            </div>
            <span class="flex-1 text-sm font-medium text-slate-800">{{ item.label }}</span>
            <svg class="w-4 h-4 text-slate-300" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" d="M9 5l7 7-7 7" />
            </svg>
          </button>
        </div>
      </div>

      <div class="mx-4 mt-4 mb-10">
        <button
          class="w-full py-4 flex items-center justify-center gap-2 text-red-600 font-semibold text-sm bg-white rounded-2xl shadow-card active:bg-red-50"
          @click="handleLogout"
        >
          Sign Out
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { showConfirmDialog, showToast } from "vant";
import { useI18n } from "vue-i18n";
import type { TrustMe, TrustProfile, TrustTier, UserRole } from "~/types";

const props = withDefaults(defineProps<{ showBack?: boolean; title?: string }>(), {
  showBack: true,
  title: "My Account",
});

const showBack = computed(() => props.showBack);
const title = computed(() => props.title);
const authStore = useAuthStore();
const router = useRouter();
const config = useRuntimeConfig();
const trustProfile = ref<TrustProfile | null>(null);
const { t } = useI18n({ useScope: "global" });

// Account context: feature flags based on account_type
const accountContext = ref<{ account_type: string; features: Record<string, boolean> } | null>(null);

const isBusiness = computed(() =>
  accountContext.value?.account_type === 'BUSINESS' || false
);

const walletRoute = computed(() => authStore.isSupplier ? "/supplier/wallet" : "/buyer/wallet");
const messagesRoute = computed(() => authStore.isSupplier ? "/supplier/messages" : "/buyer/messages");

function getRoleLabel(role: UserRole) {
  const labels: Partial<Record<UserRole, string>> = {
    BUYER: "Buyer",
    SUPPLIER_ADMIN: "Supplier Admin",
    SUPPLIER_AGENT: "Supplier Agent",
    ADMIN: "Admin",
    SUPER_ADMIN: "Super Admin",
    OPS_MANAGER: "Ops Manager",
    VERIFICATION_OFFICER: "Verification Officer",
    DISPUTE_AGENT: "Dispute Agent",
    FINANCE_OFFICER: "Finance Officer",
    RISK_ANALYST: "Risk Analyst",
    SUPPORT_AGENT: "Support Agent",
    AUDITOR: "Auditor",
  };
  return labels[role] || role;
}

const quickItems = computed(() => [
  { icon: "💳", label: t("nav.wallet"), desc: t("account.wallet_desc"), iconBg: "bg-green-50", action: () => router.push(walletRoute.value) },
  { icon: "💬", label: t("nav.messages"), desc: t("account.messages_desc"), iconBg: "bg-primary-50", action: () => router.push(messagesRoute.value) },
  { icon: "🔔", label: t("nav.notifications"), desc: t("account.notifications_desc"), iconBg: "bg-amber-50", action: () => router.push("/notifications") },
  { icon: "🛍️", label: "Marketplace", desc: "Browse products & suppliers", iconBg: "bg-purple-50", action: () => router.push("/marketplace") },
]);

const accountItems = computed(() => {
  const items = [
    { icon: "👤", label: t("profile.edit"), iconBg: "bg-primary-50", action: () => router.push("/profile/edit") },
    { icon: "🔒", label: t("profile.change_password"), iconBg: "bg-slate-100", action: () => router.push("/profile/change-password") },
    { icon: "🌐", label: t("profile.language"), iconBg: "bg-purple-50", action: () => router.push("/settings/language") },
    { icon: "🔔", label: t("account.notification_settings"), iconBg: "bg-amber-50", action: () => router.push("/settings/notifications") },
    { icon: "❓", label: t("account.contact_support"), iconBg: "bg-slate-100", action: () => showToast({ type: "text", message: "Email: support@procureping.com" }) },
  ];
  if (authStore.isSupplier) {
    // Company profile and catalog always shown for suppliers
    items.splice(1, 0, { icon: "📦", label: t("nav.catalog"), iconBg: "bg-amber-50", action: () => router.push("/supplier/catalog") });
    items.splice(2, 0, { icon: "📣", label: t("nav.adCampaigns") || "Ad Campaigns", iconBg: "bg-indigo-50", action: () => router.push("/supplier/ads") });
    // KYB and company profile only for BUSINESS account type
    if (isBusiness.value) {
      items.splice(1, 0, { icon: "🏢", label: t("account.company_profile"), iconBg: "bg-green-50", action: () => router.push("/profile/company") });
      items.splice(2, 0, { icon: "✅", label: "KYB Verification", iconBg: "bg-blue-50", action: () => router.push("/verification") });
    }
  } else {
    items.splice(1, 0, { icon: "🧾", label: t("account.offers_received"), iconBg: "bg-green-50", action: () => router.push("/buyer/offers") });
    // Business buyers see company profile and team
    if (isBusiness.value) {
      items.splice(2, 0, { icon: "🏢", label: t("account.company_profile"), iconBg: "bg-blue-50", action: () => router.push("/profile/company") });
    }
  }
  return items;
});

function tierLabel(tier: TrustTier) {
  const map: Record<TrustTier, string> = {
    BRONZE: t("trust.tiers.bronze"),
    SILVER: t("trust.tiers.silver"),
    GOLD: t("trust.tiers.gold"),
    PLATINUM: t("trust.tiers.platinum"),
    DIAMOND: t("trust.tiers.diamond"),
  };
  return map[tier] || tier;
}

function tierClass(tier: TrustTier) {
  return {
    BRONZE: "bg-amber-100 text-amber-700",
    SILVER: "bg-slate-100 text-slate-700",
    GOLD: "bg-yellow-100 text-yellow-700",
    PLATINUM: "bg-primary-100 text-primary-700",
    DIAMOND: "bg-green-100 text-green-700",
  }[tier] || "bg-slate-100 text-slate-700";
}

function formatDeposit(minor: number, currency = "PHP") {
  if (!minor) return "0";
  const amount = minor / 100;
  if (currency === "USDT") {
    return `${amount.toLocaleString("en-PH", { notation: "compact", maximumFractionDigits: 1 })} USDT`;
  }
  try {
    return new Intl.NumberFormat("en-PH", {
      style: "currency",
      currency,
      notation: "compact",
      maximumFractionDigits: 1,
    }).format(amount);
  } catch {
    return `${amount.toLocaleString("en-PH", { notation: "compact", maximumFractionDigits: 1 })} ${currency}`;
  }
}

onMounted(async () => {
  if (!authStore.accessToken) return;
  // Load trust profile
  try {
    const trust = await $fetch<TrustMe>(`${config.public.apiBase}/trust/me`, {
      headers: { Authorization: `Bearer ${authStore.accessToken}` },
    });
    trustProfile.value = trust.user;
  } catch {
    trustProfile.value = null;
  }
  // Load account context (feature flags)
  try {
    const ctx = await $fetch<{ account_type: string; features: Record<string, boolean> }>(
      `${config.public.apiBase}/auth/me/account-context`,
      { headers: { Authorization: `Bearer ${authStore.accessToken}` } }
    );
    accountContext.value = ctx;
  } catch {
    accountContext.value = null;
  }
});

async function handleLogout() {
  await showConfirmDialog({
    title: `${t("auth.sign_out")}?`,
    message: "You'll need to sign in again to access your account.",
    confirmButtonText: t("common.confirm"),
    cancelButtonText: t("common.cancel"),
  });
  await authStore.logout();
  router.push("/");
}
</script>
