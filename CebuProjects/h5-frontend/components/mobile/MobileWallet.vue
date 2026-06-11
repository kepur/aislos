<template>
  <div class="min-h-screen bg-slate-50 pb-10">
    <div class="bg-white border-b border-slate-100 px-4 h-14 flex items-center gap-3 sticky top-0 z-40 pt-safe">
      <button v-if="showBack" class="text-slate-600 p-1 -ml-1" @click="$router.back()">
        <svg class="w-6 h-6" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" d="M15 19l-7-7 7-7" />
        </svg>
      </button>
      <h1 class="font-semibold text-slate-900 flex-1">{{ title }}</h1>
      <button class="text-xs font-semibold text-primary-600" @click="loadWallet">{{ $t("common.refresh") }}</button>
    </div>

    <div class="mx-4 mt-4 rounded-2xl bg-primary-600 text-white p-5 shadow-card">
      <p class="text-xs text-primary-100 uppercase tracking-wide">{{ $t("wallet.available_balance") }}</p>
      <p class="text-3xl font-extrabold mt-2">{{ money(wallet?.available_balance_minor || 0, wallet?.currency || "PHP") }}</p>
      <div class="grid grid-cols-2 gap-3 mt-4 text-xs">
        <div class="rounded-xl bg-white/10 p-3">
          <p class="text-primary-100">{{ $t("wallet.locked") }}</p>
          <p class="font-bold mt-1">{{ money(wallet?.locked_balance_minor || 0, wallet?.currency || "PHP") }}</p>
        </div>
        <div class="rounded-xl bg-white/10 p-3">
          <p class="text-primary-100">{{ $t("wallet.deposited") }}</p>
          <p class="font-bold mt-1">{{ money(wallet?.total_deposited_minor || 0, wallet?.currency || "PHP") }}</p>
        </div>
      </div>
    </div>

    <div class="mx-4 mt-4 card space-y-4">
      <div>
        <p class="text-sm font-semibold text-slate-900">PHP Deposit</p>
        <p class="text-xs text-slate-500 mt-1">{{ $t("wallet.deposit_help") }}</p>
      </div>
      <input v-model.number="depositAmount" type="number" min="1" class="input-field" :placeholder="$t('wallet.amount')" />
      <select v-model="network" class="input-field bg-white">
        <option>LOCAL_BANK</option>
        <option>GCASH</option>
        <option>MAYA</option>
      </select>
      <button class="btn-primary" :disabled="creating" @click="createDeposit">
        {{ creating ? $t("wallet.creating") : $t("wallet.create_deposit_address") }}
      </button>
    </div>

    <div v-if="activeDeposit" class="mx-4 mt-4 card space-y-4">
      <div>
        <p class="text-sm font-semibold text-slate-900">{{ $t("wallet.deposit_address") }}</p>
        <p class="text-xs text-slate-500 mt-1">{{ $t("common.status") }}: {{ activeDeposit.status }}</p>
      </div>
      <p class="break-all rounded-xl bg-slate-50 p-3 text-xs font-mono text-slate-700">{{ activeDeposit.deposit_address }}</p>
      <input v-model="txHash" class="input-field" :placeholder="$t('wallet.paste_tx_hash')" />
      <button class="btn-primary" :disabled="submittingTx" @click="submitTx">
        {{ submittingTx ? $t("wallet.submitting") : $t("wallet.submit_tx_hash") }}
      </button>
    </div>

    <div v-if="notice" class="mx-4 mt-4 text-xs rounded-xl px-3 py-2" :class="noticeType === 'error' ? 'bg-red-50 text-red-700' : 'bg-green-50 text-green-700'">
      {{ notice }}
    </div>

    <div class="mx-4 mt-4">
      <p class="section-title px-0">{{ $t("wallet.ledger") }}</p>
      <div class="bg-white rounded-2xl shadow-card overflow-hidden">
        <div v-if="loading" class="p-6 text-center text-sm text-slate-400">{{ $t("common.loading") }}</div>
        <div v-else-if="!transactions.length" class="p-6 text-center text-sm text-slate-400">{{ $t("wallet.no_transactions") }}</div>
        <div v-for="tx in transactions" v-else :key="tx.id" class="list-item border-b last:border-0 border-slate-50">
          <div class="flex-1">
            <p class="text-sm font-semibold text-slate-800">{{ tx.note || tx.tx_type }}</p>
            <p class="text-xs text-slate-400">{{ new Date(tx.created_at).toLocaleString() }} · {{ tx.tx_type }}</p>
          </div>
          <p class="text-sm font-bold" :class="tx.amount_delta_minor >= 0 ? 'text-green-600' : 'text-slate-900'">
            {{ tx.amount_delta_minor >= 0 ? "+" : "-" }}{{ money(Math.abs(tx.amount_delta_minor), tx.currency) }}
          </p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useI18n } from "vue-i18n";

const props = withDefaults(defineProps<{ showBack?: boolean; title?: string }>(), {
  showBack: true,
  title: "Wallet",
});

type Wallet = {
  id: string;
  currency: string;
  available_balance_minor: number;
  locked_balance_minor: number;
  total_deposited_minor: number;
};
type WalletTransaction = {
  id: string;
  tx_type: string;
  amount_delta_minor: number;
  currency: string;
  note?: string;
  created_at: string;
};
type WalletDeposit = {
  id: string;
  amount_minor: number;
  currency: string;
  network: string;
  deposit_address: string;
  status: string;
};

const showBack = computed(() => props.showBack);
const title = computed(() => props.title);
const config = useRuntimeConfig();
const authStore = useAuthStore();
const loading = ref(true);
const creating = ref(false);
const submittingTx = ref(false);
const wallet = ref<Wallet | null>(null);
const transactions = ref<WalletTransaction[]>([]);
const activeDeposit = ref<WalletDeposit | null>(null);
const depositAmount = ref(100);
const network = ref("LOCAL_BANK");
const txHash = ref("");
const notice = ref("");
const noticeType = ref<"success" | "error">("success");
const { t } = useI18n({ useScope: "global" });

function headers() {
  return { Authorization: `Bearer ${authStore.accessToken}` };
}

function money(minor: number, currency = "PHP") {
  const amount = (minor || 0) / 100;
  if (currency === "USDT") {
    return `${amount.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })} USDT`;
  }
  try {
    return new Intl.NumberFormat("en-PH", { style: "currency", currency }).format(amount);
  } catch {
    return `${amount.toLocaleString("en-PH", { minimumFractionDigits: 2, maximumFractionDigits: 2 })} ${currency}`;
  }
}

async function loadWallet() {
  loading.value = true;
  try {
    const data = await $fetch<{ wallets: Wallet[] }>(`${config.public.apiBase}/wallets/me`, { headers: headers() });
    wallet.value = data.wallets[0] || null;
    transactions.value = await $fetch<WalletTransaction[]>(`${config.public.apiBase}/wallets/transactions`, { headers: headers() });
  } finally {
    loading.value = false;
  }
}

async function createDeposit() {
  creating.value = true;
  notice.value = "";
  try {
    activeDeposit.value = await $fetch<WalletDeposit>(`${config.public.apiBase}/wallets/deposits`, {
      method: "POST",
      body: {
        amount_minor: Math.round(Number(depositAmount.value || 0) * 100),
        currency: "PHP",
        network: network.value,
        provider: network.value === "LOCAL_BANK" ? "MANUAL_BANK" : "LOCAL_EWALLET",
        payment_method: network.value === "LOCAL_BANK" ? "PHP_MANUAL_BANK" : `PHP_${network.value}`,
      },
      headers: headers(),
    });
    noticeType.value = "success";
    notice.value = t("wallet.deposit_address_created");
  } catch (err: any) {
    noticeType.value = "error";
    notice.value = err?.data?.detail || err?.message || t("wallet.failed_create_deposit");
  } finally {
    creating.value = false;
  }
}

async function submitTx() {
  if (!activeDeposit.value || !txHash.value.trim()) return;
  submittingTx.value = true;
  try {
    activeDeposit.value = await $fetch<WalletDeposit>(`${config.public.apiBase}/wallets/deposits/${activeDeposit.value.id}/submit-tx`, {
      method: "POST",
      body: { tx_hash: txHash.value.trim() },
      headers: headers(),
    });
    txHash.value = "";
    noticeType.value = "success";
    notice.value = t("wallet.tx_submitted");
    await loadWallet();
  } catch (err: any) {
    noticeType.value = "error";
    notice.value = err?.data?.detail || err?.message || t("wallet.failed_submit_tx");
  } finally {
    submittingTx.value = false;
  }
}

onMounted(loadWallet);
</script>
