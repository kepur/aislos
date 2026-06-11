<template>
  <div class="min-h-screen bg-slate-50 flex flex-col">
    <div class="bg-white border-b border-slate-100 px-4 h-14 flex items-center gap-3 sticky top-0 z-40 pt-safe">
      <button type="button" class="text-slate-600 p-1 -ml-1" @click="$router.back()">
        <svg class="w-6 h-6" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" d="M15 19l-7-7 7-7" />
        </svg>
      </button>
      <h1 class="font-semibold text-slate-900 flex-1">{{ $t("pages.order_detail") }}</h1>
    </div>

    <div v-if="loading" class="p-4 space-y-3">
      <div class="card"><div class="shimmer h-24 rounded"></div></div>
    </div>

    <template v-else-if="order">
      <div class="flex-1 overflow-y-auto pb-40">
        <!-- Order Summary -->
        <div class="card mx-4 mt-4">
          <div class="flex justify-between items-center mb-3">
            <div>
              <p class="text-xs text-slate-500">Order</p>
              <p class="font-bold text-slate-900">#{{ order.id.slice(0, 8).toUpperCase() }}</p>
            </div>
            <span class="px-3 py-1 rounded-full text-sm font-semibold" :class="getOrderBadgeClass(order.status)">
              {{ getOrderStatusLabel(order.status) }}
            </span>
          </div>
          <div class="grid grid-cols-2 gap-4 text-sm">
            <div>
              <p class="text-xs text-slate-400">Total Amount</p>
              <p class="font-bold text-slate-900 text-lg">{{ formatPrice(order.total_amount_minor, order.currency) }}</p>
            </div>
            <div>
              <p class="text-xs text-slate-400">Order ID</p>
              <p class="font-semibold text-slate-800 font-mono text-sm">#{{ order.id.slice(0, 8).toUpperCase() }}</p>
            </div>
            <div>
              <p class="text-xs text-slate-400">Created</p>
              <p class="font-semibold text-slate-800">{{ formatDate(order.created_at) }}</p>
            </div>
          </div>
        </div>

        <!-- Escrow Status -->
        <div v-if="order.escrow" class="card mx-4 mt-3">
          <div class="flex items-center gap-2 mb-3">
            <svg class="w-5 h-5 text-green-600" fill="currentColor" viewBox="0 0 20 20">
              <path fill-rule="evenodd" d="M5 9V7a5 5 0 0110 0v2a2 2 0 012 2v5a2 2 0 01-2 2H5a2 2 0 01-2-2v-5a2 2 0 012-2zm8-2v2H7V7a3 3 0 016 0z" clip-rule="evenodd" />
            </svg>
            <h3 class="font-semibold text-slate-900">{{ $t("pages.escrow_protection") }}</h3>
            <span class="ml-auto badge-success text-xs">{{ order.escrow.status }}</span>
          </div>
          <div class="bg-green-50 rounded-xl p-3 text-xs text-green-700 leading-relaxed">
            {{ escrowMessage }}
          </div>
          <div class="mt-3 grid grid-cols-2 gap-3 text-xs">
            <div class="bg-slate-50 rounded-lg p-2.5">
              <p class="text-slate-400">Held</p>
              <p class="font-bold text-slate-800">{{ formatPrice(order.escrow.auth_amount_minor, order.escrow.currency) }}</p>
            </div>
            <div class="bg-slate-50 rounded-lg p-2.5">
              <p class="text-slate-400">Released</p>
              <p class="font-bold text-slate-800">{{ formatPrice(order.escrow.released_amount_minor, order.escrow.currency) }}</p>
            </div>
          </div>
        </div>

        <!-- Delivery Timeline -->
        <div v-if="order.delivery" class="card mx-4 mt-3">
          <h3 class="font-semibold text-slate-900 mb-3">{{ $t("pages.delivery_status") }}</h3>
          <div class="flex items-center gap-3 mb-2">
            <div class="w-3 h-3 rounded-full flex-shrink-0" :class="deliveryDotClass"></div>
            <div>
              <p class="font-semibold text-slate-800 text-sm">{{ order.delivery.status.replace(/_/g, " ") }}</p>
              <p v-if="order.delivery.tracking_number" class="text-xs text-slate-500">
                Tracking: {{ order.delivery.tracking_number }}
              </p>
            </div>
          </div>
          <div v-if="order.delivery.estimated_at" class="text-xs text-slate-500 mt-1">
            Est. delivery: {{ formatDate(order.delivery.estimated_at) }}
          </div>
        </div>

        <!-- Order Notes -->
        <div v-if="order.notes" class="card mx-4 mt-3">
          <p class="text-xs text-slate-500 font-medium mb-1">Order Notes</p>
          <p class="text-sm text-slate-700">{{ order.notes }}</p>
        </div>
      </div>

      <!-- Actions -->
      <div class="sticky-bottom-action space-y-2">
        <!-- Confirm Receipt -->
        <button type="button"
          v-if="order.status === 'DELIVERED'"
          class="btn-primary"
          :disabled="actionLoading"
          @click="confirmReceipt"
        >
          ✓ Confirm Receipt & Release Payment
        </button>

        <!-- Open Dispute -->
        <button type="button"
          v-if="['DELIVERED', 'IN_PROGRESS', 'PAID_IN_ESCROW'].includes(order.status)"
          class="w-full py-3 text-red-600 font-medium text-sm"
          @click="openDisputeSheet = true"
        >
          Report a Problem
        </button>

        <!-- Contact Supplier -->
        <NuxtLink v-if="order.status !== 'CANCELED'" :to="`/messages/${order.id}`">
          <button type="button" class="btn-secondary py-3 text-sm">
            Message Supplier
          </button>
        </NuxtLink>
      </div>

      <!-- Dispute Sheet -->
      <van-action-sheet v-model:show="openDisputeSheet" title="Report a Problem">
        <div class="px-4 pb-6 pt-2 space-y-4">
          <div>
            <label class="block text-sm font-medium text-slate-700 mb-1.5">Reason</label>
            <select v-model="disputeReason" class="input-field bg-white">
              <option value="">Select reason</option>
              <option value="ITEM_NOT_RECEIVED">Item not received</option>
              <option value="ITEM_DAMAGED">Item damaged</option>
              <option value="ITEM_WRONG">Wrong item delivered</option>
              <option value="QUANTITY_MISMATCH">Quantity mismatch</option>
              <option value="QUALITY_ISSUE">Quality issue</option>
              <option value="DELIVERY_DELAY">Delivery delay</option>
              <option value="OTHER">Other</option>
            </select>
          </div>
          <div>
            <label class="block text-sm font-medium text-slate-700 mb-1.5">Description</label>
            <textarea v-model="disputeDesc" class="input-field resize-none" rows="3" placeholder="Describe the issue…"></textarea>
          </div>
          <button type="button" class="btn-primary bg-red-600 hover:bg-red-700" :disabled="!disputeReason || actionLoading" @click="submitDispute">
            Submit Dispute
          </button>
        </div>
      </van-action-sheet>
    </template>
  </div>
</template>

<script setup lang="ts">
import { showConfirmDialog, showToast } from "vant";

definePageMeta({ layout: "default", middleware: ["buyer"] });
useHead({ title: "Order Detail" });

const route = useRoute();
const router = useRouter();
const orderStore = useOrderStore();
const { formatPrice, formatDate, getOrderStatusLabel } = useApiUtils();

const id = route.params.id as string;
const loading = ref(true);
const actionLoading = ref(false);
const openDisputeSheet = ref(false);
const disputeReason = ref("");
const disputeDesc = ref("");
const order = computed(() => orderStore.currentOrder);

const escrowMessage = computed(() => {
  const status = order.value?.escrow?.status;
  if (status === "CAPTURED") return "Your payment is securely held. Funds will be released to the supplier only after you confirm delivery.";
  if (status === "RELEASED") return "Payment has been released to the supplier. Thank you for using ProcurePing!";
  if (status === "REFUNDED") return "A refund has been processed to your account.";
  return "Escrow is active and protecting your transaction.";
});

const deliveryDotClass = computed(() => {
  const s = order.value?.delivery?.status;
  if (s === "DELIVERED") return "bg-green-500";
  if (s === "READY_FOR_PICKUP" || s === "DISPATCHED") return "bg-primary-500";
  return "bg-amber-500";
});

function getOrderBadgeClass(status: string) {
  const map: Record<string, string> = {
    CREATED: "badge-gray",
    AWAITING_PAYMENT: "badge-warning",
    PAID_IN_ESCROW: "badge-warning",
    IN_PROGRESS: "badge-primary",
    DELIVERED: "badge-success",
    ACCEPTED: "badge-success",
    PAYOUT_RELEASED: "badge-success",
    DISPUTED: "badge-danger",
    CANCELED: "badge-gray",
    REFUNDED: "badge-gray",
  };
  return map[status] || "badge-gray";
}

async function confirmReceipt() {
  await showConfirmDialog({
    title: "Confirm Receipt",
    message: "By confirming, you release the payment to the supplier. This cannot be undone.",
  });
  actionLoading.value = true;
  try {
    await orderStore.acceptDelivery(id);
    showToast({ type: "success", message: "Receipt confirmed! Payment released." });
    await orderStore.fetchOrder(id);
  } finally {
    actionLoading.value = false;
  }
}

async function submitDispute() {
  actionLoading.value = true;
  try {
    await orderStore.openDispute(id, disputeReason.value);
    openDisputeSheet.value = false;
    showToast({ type: "success", message: "Dispute submitted. Our team will review it." });
    router.push("/buyer/orders");
  } finally {
    actionLoading.value = false;
  }
}

onMounted(async () => {
  await orderStore.fetchOrder(id);
  loading.value = false;
});
</script>
