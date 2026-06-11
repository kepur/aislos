<template>
  <div class="min-h-screen bg-slate-50 flex flex-col">
    <div class="bg-white border-b border-slate-100 px-4 h-14 flex items-center gap-3 sticky top-0 z-40 pt-safe">
      <button type="button" class="text-slate-600 p-1 -ml-1" @click="$router.back()">
        <svg class="w-6 h-6" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" d="M15 19l-7-7 7-7" />
        </svg>
      </button>
      <h1 class="font-semibold text-slate-900 flex-1">Make an Offer</h1>
    </div>

    <div class="flex-1 overflow-y-auto pb-40">
      <!-- Intent Summary -->
      <div v-if="intent" class="mx-4 mt-4 card bg-slate-50 border border-slate-200">
        <p class="text-xs text-slate-500 font-medium uppercase tracking-wide mb-1">Buyer Request</p>
        <h3 class="font-bold text-slate-900 text-sm mb-1">{{ intent.title }}</h3>
        <p class="text-xs text-slate-500">{{ intent.qty }} {{ intent.unit }}
          <span v-if="intent.budget_max_minor"> · Budget: {{ formatPrice(intent.budget_max_minor, intent.currency) }}</span>
        </p>
      </div>

      <!-- Offer Form -->
      <form class="px-4 mt-4 space-y-4" @submit.prevent="submitOffer">
        <!-- Tier -->
        <div>
          <label class="block text-sm font-medium text-slate-700 mb-2">Offer Tier</label>
          <div class="grid grid-cols-3 gap-2">
            <button
              v-for="tier in tiers"
              :key="tier.value"
              type="button"
              class="py-2.5 px-2 rounded-xl border-2 text-center transition-all"
              :class="form.tier === tier.value ? 'border-primary-500 bg-primary-50' : 'border-slate-200 bg-white'"
              @click="form.tier = tier.value"
            >
              <div class="text-lg mb-0.5">{{ tier.emoji }}</div>
              <div class="text-xs font-semibold" :class="form.tier === tier.value ? 'text-primary-700' : 'text-slate-600'">{{ tier.label }}</div>
            </button>
          </div>
        </div>

        <!-- Pricing -->
        <div class="grid grid-cols-2 gap-3">
          <div>
            <label class="block text-sm font-medium text-slate-700 mb-1.5">Unit Price (₱) *</label>
            <input v-model.number="unitPrice" type="number" min="0" step="0.01" placeholder="0.00" class="input-field" required />
          </div>
          <div>
            <label class="block text-sm font-medium text-slate-700 mb-1.5">Qty Available *</label>
            <input v-model.number="form.qty_available" type="number" min="1" class="input-field" required />
          </div>
        </div>

        <!-- Delivery fee -->
        <div>
          <label class="block text-sm font-medium text-slate-700 mb-1.5">Shipping From Address *</label>
          <select v-model="selectedOriginAddressId" class="input-field" @change="recalculateShipping">
            <option value="">Select origin address</option>
            <option v-for="addr in shippingAddresses" :key="addr.id" :value="addr.id">
              {{ addr.label }} · {{ addr.city }} · {{ addr.country_name }}
            </option>
          </select>
          <p v-if="shippingAddressLoading" class="text-xs text-slate-500 mt-1">Loading shipping addresses...</p>
        </div>

        <div>
          <label class="block text-sm font-medium text-slate-700 mb-1.5">Delivery Fee (₱)</label>
          <div class="relative">
            <span class="absolute left-4 top-1/2 -translate-y-1/2 text-slate-500 text-sm">₱</span>
            <input v-model.number="deliveryFeeDisplay" type="number" min="0" step="0.01" placeholder="0" class="input-field pl-9" />
          </div>
          <p v-if="shippingEstimate" class="text-xs text-primary-700 mt-1">
            Estimated by route: {{ shippingEstimate.estimated_days_min }}-{{ shippingEstimate.estimated_days_max }} days
          </p>
          <p v-else-if="shippingEstimateLoading" class="text-xs text-slate-500 mt-1">Estimating shipping...</p>
        </div>

        <!-- Total Preview -->
        <div v-if="totalPrice > 0" class="bg-primary-50 rounded-xl px-4 py-3 flex justify-between items-center border border-primary-100">
          <span class="text-sm text-primary-700 font-medium">Total (excl. delivery)</span>
          <span class="text-lg font-extrabold text-primary-900">{{ formatPrice(totalPrice) }}</span>
        </div>

        <!-- Warranty -->
        <div>
          <label class="block text-sm font-medium text-slate-700 mb-1.5">Warranty (optional)</label>
          <input v-model="form.warranty" type="text" placeholder="e.g. 12 months manufacturer warranty" class="input-field" />
        </div>

        <!-- Stock Confidence -->
        <div>
          <label class="block text-sm font-medium text-slate-700 mb-2">Stock Availability</label>
          <div class="flex gap-2">
            <button
              v-for="s in stockOptions"
              :key="s.value"
              type="button"
              class="flex-1 py-2 rounded-xl border-2 text-xs font-semibold transition-all"
              :class="form.stock_confidence === s.value ? 'border-primary-500 bg-primary-50 text-primary-700' : 'border-slate-200 bg-white text-slate-600'"
              @click="form.stock_confidence = s.value"
            >
              {{ s.emoji }} {{ s.label }}
            </button>
          </div>
        </div>

        <!-- Note -->
        <div>
          <label class="block text-sm font-medium text-slate-700 mb-1.5">Note to Buyer (optional)</label>
          <textarea v-model="form.message" class="input-field resize-none" rows="3" placeholder="Brand info, specifications, why choose us…" maxlength="500"></textarea>
        </div>

        <!-- Offer Expiry -->
        <div>
          <label class="block text-sm font-medium text-slate-700 mb-1.5">Offer Valid Until</label>
          <input v-model="form.expires_at" type="date" class="input-field" :min="minDate" />
        </div>

        <p v-if="error" class="bg-red-50 text-red-700 text-sm px-4 py-3 rounded-xl border border-red-200">{{ error }}</p>
      </form>
    </div>

    <!-- Submit -->
    <div class="sticky-bottom-action">
      <button type="button" class="btn-primary" :disabled="!canSubmit || loading" @click="submitOffer">
        <span v-if="!loading">Submit Offer</span>
        <span v-else class="flex items-center justify-center gap-2">
          <svg class="animate-spin w-4 h-4" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
          </svg>
          Submitting…
        </span>
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { showToast } from "vant";

definePageMeta({ layout: "default", middleware: ["supplier"] });
useHead({ title: "Make an Offer" });

const route = useRoute();
const router = useRouter();
const intentStore = useIntentStore();
const offerStore = useOfferStore();
const { formatPrice } = useApiUtils();
const api = useApiFetch();

const intentId = route.query.intent_id as string;
const loading = ref(false);
const error = ref("");
const unitPrice = ref<number>(0);
const deliveryFeeDisplay = ref<number>(0);
const selectedOriginAddressId = ref<string>("");
const shippingAddresses = ref<any[]>([]);
const shippingAddressLoading = ref(false);
const shippingEstimateLoading = ref(false);
const shippingEstimate = ref<{
  total_shipping_minor: number;
  estimated_days_min: number;
  estimated_days_max: number;
  currency: string;
} | null>(null);

watch(deliveryFeeDisplay, (val) => {
  form.delivery_fee_minor = Math.round((val || 0) * 100);
});

const form = reactive({
  qty_available: 1,
  unit_price_minor: 0,
  delivery_fee_minor: 0,
  currency: "PHP",
  tier: "GOOD" as "GOOD" | "BETTER" | "BEST" | "CUSTOM",
  stock_confidence: "FIRM" as "FIRM" | "BACKORDER" | "UNKNOWN",
  message: "",
  expires_at: "",
  warranty: "" as string | undefined,
});

const intent = computed(() => intentStore.currentIntent);
const totalPrice = computed(() => unitPrice.value * form.qty_available * 100);
const minDate = computed(() => {
  const d = new Date();
  d.setDate(d.getDate() + 1);
  return d.toISOString().slice(0, 10);
});

watch([unitPrice], () => {
  form.unit_price_minor = Math.round(unitPrice.value * 100);
});

const tiers = [
  { value: "GOOD", label: "Good", emoji: "📦" },
  { value: "BETTER", label: "Better", emoji: "⚡" },
  { value: "BEST", label: "Best", emoji: "⭐" },
];

const stockOptions = [
  { value: "FIRM", label: "In Stock", emoji: "✅" },
  { value: "BACKORDER", label: "Backorder", emoji: "⚠️" },
  { value: "UNKNOWN", label: "Unknown", emoji: "🔄" },
];

const canSubmit = computed(() => unitPrice.value > 0 && form.qty_available > 0);

const selectedOriginAddress = computed(() =>
  shippingAddresses.value.find((a) => a.id === selectedOriginAddressId.value) || null
);

async function submitOffer() {
  if (!canSubmit.value || loading.value) return;
  if (!intentId) { error.value = "Missing intent ID"; return; }
  loading.value = true;
  error.value = "";
  const payload: Record<string, unknown> = {
    qty_available: form.qty_available,
    unit_price_minor: form.unit_price_minor,
    delivery_fee_minor: form.delivery_fee_minor,
    currency: form.currency,
    tier: form.tier,
    stock_confidence: form.stock_confidence,
    message: form.message || undefined,
    expires_at: form.expires_at ? new Date(form.expires_at).toISOString() : undefined,
    warranty: form.warranty || undefined,
  };
  try {
    await offerStore.submitOffer(intentId, payload);
    showToast({ type: "success", message: "Offer submitted!" });
    router.push("/supplier/offers");
  } catch (err: unknown) {
    const e = err as { data?: { detail?: unknown } };
    const detail = e?.data?.detail;
    error.value = typeof detail === "string" ? detail : JSON.stringify(detail) || "Failed to submit offer";
  } finally {
    loading.value = false;
  }
}

async function loadShippingFromAddresses() {
  shippingAddressLoading.value = true;
  try {
    shippingAddresses.value = await api("/addresses?address_type=SHIPPING_FROM");
    const defaultAddr = shippingAddresses.value.find((a: any) => a.is_default);
    if (defaultAddr) {
      selectedOriginAddressId.value = defaultAddr.id;
    } else if (shippingAddresses.value.length) {
      selectedOriginAddressId.value = shippingAddresses.value[0].id;
    }
  } catch {
    shippingAddresses.value = [];
  } finally {
    shippingAddressLoading.value = false;
  }
}

async function recalculateShipping() {
  if (!selectedOriginAddress.value || !intent.value) {
    shippingEstimate.value = null;
    return;
  }
  shippingEstimateLoading.value = true;
  try {
    const res = await api<{
      estimates: Array<{
        total_shipping_minor: number;
        estimated_days_min: number;
        estimated_days_max: number;
        currency: string;
      }>;
    }>("/shipping/estimate", {
      method: "POST",
      body: {
        origin_country: selectedOriginAddress.value.country_code || "PH",
        dest_country: intent.value.country || "PH",
        weight_kg: Math.max(form.qty_available, 1),
        declared_value_minor: Math.max(form.unit_price_minor * form.qty_available, 0),
        currency: form.currency,
      },
    });
    shippingEstimate.value = res.estimates?.[0] || null;
    if (shippingEstimate.value) {
      form.delivery_fee_minor = shippingEstimate.value.total_shipping_minor;
      deliveryFeeDisplay.value = Number((shippingEstimate.value.total_shipping_minor / 100).toFixed(2));
    }
  } catch {
    shippingEstimate.value = null;
  } finally {
    shippingEstimateLoading.value = false;
  }
}

// Default expiry 3 days
const defaultExpiry = new Date();
defaultExpiry.setDate(defaultExpiry.getDate() + 3);
form.expires_at = defaultExpiry.toISOString().slice(0, 10);

onMounted(async () => {
  await loadShippingFromAddresses();
  if (intentId) {
    await intentStore.fetchIntent(intentId);
    if (intent.value) {
      form.qty_available = intent.value.qty ?? 1;
    }
  }
  await recalculateShipping();
});

watch(
  () => [form.qty_available, unitPrice.value, selectedOriginAddressId.value, intent.value?.country],
  async () => {
    await recalculateShipping();
  }
);
</script>
