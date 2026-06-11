<template>
  <div class="min-h-screen bg-slate-50">
    <div class="bg-white border-b border-slate-100 px-4 h-14 flex items-center gap-3 sticky top-0 z-40 pt-safe">
      <button type="button" class="text-slate-600 p-1 -ml-1" @click="$router.back()">
        <svg class="w-6 h-6" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" d="M15 19l-7-7 7-7" />
        </svg>
      </button>
      <h1 class="font-semibold text-slate-900 flex-1">{{ $t("buyer.compare_offers") }}</h1>
    </div>

    <div v-if="loading" class="p-4 space-y-3">
      <div v-for="n in 3" :key="n" class="card"><div class="shimmer h-24 rounded"></div></div>
    </div>

    <div v-else-if="offers.length === 0" class="empty-state py-20">
      <p class="text-slate-500 font-medium">{{ $t("pages.no_offers_to_compare") }}</p>
    </div>

    <div v-else class="p-4 space-y-3">
      <div v-for="(offer, idx) in offers" :key="offer.id" class="card" :class="idx === 0 ? 'ring-2 ring-primary-400' : ''">
        <div class="flex justify-between items-start mb-2">
          <div>
            <p v-if="idx === 0" class="text-xs text-primary-600 font-semibold mb-0.5">Best Price</p>
            <p class="font-bold text-slate-900 text-xl">{{ formatPrice(offer.total_price_minor, offer.currency) }}</p>
            <p class="text-xs text-slate-500">{{ formatPrice(offer.unit_price_minor, offer.currency) }} / unit</p>
          </div>
          <span class="text-xs px-2 py-0.5 rounded-full font-medium" :class="getOfferBadgeClass(offer.status)">
            {{ getOfferStatusLabel(offer.status) }}
          </span>
        </div>
        <div class="grid grid-cols-2 gap-2 text-xs text-slate-600 my-3">
          <div class="bg-slate-50 rounded-lg p-2">
            <p class="text-slate-400 mb-0.5">Available</p>
            <p class="font-semibold">{{ offer.qty_available }} units</p>
          </div>
          <div class="bg-slate-50 rounded-lg p-2">
            <p class="text-slate-400 mb-0.5">Tier</p>
            <p class="font-semibold">{{ offer.tier || "—" }}</p>
          </div>
          <div v-if="offer.eta_date" class="bg-slate-50 rounded-lg p-2">
            <p class="text-slate-400 mb-0.5">ETA</p>
            <p class="font-semibold">{{ formatDate(offer.eta_date) }}</p>
          </div>
          <div class="bg-slate-50 rounded-lg p-2">
            <p class="text-slate-400 mb-0.5">Stock</p>
            <p class="font-semibold">{{ offer.stock_confidence || "—" }}</p>
          </div>
        </div>
        <div class="bg-primary-50 border border-primary-100 rounded-lg p-3 mb-3">
          <div class="flex items-center justify-between text-xs">
            <p class="text-primary-700 font-semibold">Estimated Shipping</p>
            <span v-if="shippingLoadingMap[offer.id]" class="text-primary-500">Calculating...</span>
          </div>
          <p class="text-sm font-semibold text-primary-900 mt-1">
            {{ shippingCostLabel(offer) }}
          </p>
          <p class="text-xs text-primary-700 mt-1">
            Landed Total: <span class="font-semibold">{{ landedTotalLabel(offer) }}</span>
            <span v-if="shippingEtaLabel(offer)"> · ETA {{ shippingEtaLabel(offer) }}</span>
          </p>
        </div>
        <p v-if="offer.message" class="text-xs text-slate-600 italic mb-3">"{{ offer.message }}"</p>
        <button type="button"
          v-if="intentStatus === 'ACTIVE'"
          class="w-full py-2.5 bg-primary-600 text-white rounded-xl text-sm font-semibold active:bg-primary-700"
          @click="awardOffer(offer.id)"
        >
          Award This Offer
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { showConfirmDialog, showToast } from "vant";

definePageMeta({ layout: "default", middleware: ["buyer"] });
useHead({ title: "Compare Offers" });

const route = useRoute();
const router = useRouter();
const intentStore = useIntentStore();
const api = useApiFetch();
const { formatPrice, formatDate, getOfferStatusLabel } = useApiUtils();

const intentId = route.query.intent_id as string;
const loading = ref(true);
const offers = computed(() => intentStore.offers.slice().sort((a, b) => a.total_price_minor - b.total_price_minor));
const intentStatus = computed(() => intentStore.currentIntent?.status);
const shippingEstimateMap = ref<Record<string, { total_shipping_minor: number; estimated_days_min: number; estimated_days_max: number; currency: string } | null>>({});
const shippingLoadingMap = ref<Record<string, boolean>>({});

function getOfferBadgeClass(status: string) {
  const map: Record<string, string> = {
    SUBMITTED: "badge-primary",
    VIEWED: "badge-primary",
    SHORTLISTED: "badge-warning",
    AWARDED: "badge-success",
    REJECTED: "badge-gray",
    WITHDRAWN: "badge-gray",
  };
  return map[status] || "badge-gray";
}

async function awardOffer(offerId: string) {
  try {
    await showConfirmDialog({ title: "Award this offer?", message: "This will create an order and notify the supplier." });
    await intentStore.awardOffer(offerId);
    showToast({ type: "success", message: "Offer awarded! Order created." });
    router.push("/buyer/orders");
  } catch {
    // user cancelled or error
  }
}

function resolveWeightKg() {
  const attrs = (intentStore.currentIntent?.attrs_jsonb || {}) as Record<string, unknown>;
  const unitWeight = Number(attrs.unit_weight_kg ?? attrs.weight_kg ?? 0);
  if (Number.isFinite(unitWeight) && unitWeight > 0) {
    return unitWeight;
  }
  const qty = Number(intentStore.currentIntent?.qty || 1);
  return Math.max(1, Math.min(qty, 20000));
}

async function fetchShippingEstimateForOffer(offer: any) {
  const offerId = String(offer.id);
  shippingLoadingMap.value[offerId] = true;
  try {
    const country = intentStore.currentIntent?.country || "PH";
    const response = await api<{ estimates: Array<{ total_shipping_minor: number; estimated_days_min: number; estimated_days_max: number; currency: string }> }>("/shipping/estimate", {
      method: "POST",
      body: {
        origin_country: country,
        dest_country: country,
        weight_kg: resolveWeightKg(),
        declared_value_minor: offer.total_price_minor,
        currency: offer.currency || "PHP",
      },
    });
    const best = response.estimates?.[0];
    shippingEstimateMap.value[offerId] = best
      ? {
          total_shipping_minor: Number(best.total_shipping_minor || 0),
          estimated_days_min: Number(best.estimated_days_min || 0),
          estimated_days_max: Number(best.estimated_days_max || 0),
          currency: best.currency || offer.currency || "PHP",
        }
      : null;
  } catch {
    shippingEstimateMap.value[offerId] = null;
  } finally {
    shippingLoadingMap.value[offerId] = false;
  }
}

function shippingCostLabel(offer: any) {
  const estimate = shippingEstimateMap.value[String(offer.id)];
  if (!estimate) return "—";
  return formatPrice(estimate.total_shipping_minor, estimate.currency || offer.currency);
}

function landedTotalLabel(offer: any) {
  const estimate = shippingEstimateMap.value[String(offer.id)];
  if (!estimate) return formatPrice(offer.total_price_minor, offer.currency);
  const total = Number(offer.total_price_minor || 0) + Number(estimate.total_shipping_minor || 0);
  return formatPrice(total, estimate.currency || offer.currency);
}

function shippingEtaLabel(offer: any) {
  const estimate = shippingEstimateMap.value[String(offer.id)];
  if (!estimate) return "";
  return `${estimate.estimated_days_min}-${estimate.estimated_days_max}d`;
}

onMounted(async () => {
  if (intentId) {
    await intentStore.fetchIntent(intentId);
    await intentStore.fetchOffers(intentId);
    await Promise.all(intentStore.offers.map((offer) => fetchShippingEstimateForOffer(offer)));
  }
  loading.value = false;
});
</script>
