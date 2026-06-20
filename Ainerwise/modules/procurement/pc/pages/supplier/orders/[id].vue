<template>
  <div class="space-y-6">
    <div v-if="loading && !order" class="flex justify-center py-20">
      <UIcon name="i-heroicons-arrow-path" class="h-8 w-8 animate-spin text-slate-400" />
    </div>

    <template v-else-if="order">
      <div class="flex flex-wrap items-center gap-4">
        <UButton to="/supplier/orders" color="gray" variant="ghost" icon="i-heroicons-arrow-left" size="sm" />
        <div class="flex-1">
          <div class="flex flex-wrap items-center gap-3">
            <h1 class="text-2xl font-bold text-slate-900">Order #{{ shortId(order.id).toUpperCase() }}</h1>
            <UBadge :color="statusColor(order.status)" variant="solid">{{ order.status }}</UBadge>
          </div>
          <p class="mt-1 text-sm text-slate-500">
            Intent {{ shortId(order.intent_id) }} · Offer {{ shortId(order.offer_id) }} · Created {{ formatDate(order.created_at) }}
          </p>
        </div>
        <UButton color="gray" variant="soft" icon="i-heroicons-chat-bubble-left" to="/supplier/messages">
          Message Buyer
        </UButton>
      </div>

      <UAlert
        v-if="error"
        color="red"
        variant="soft"
        icon="i-heroicons-exclamation-triangle"
        :title="error"
      />

      <div class="rounded-2xl border border-emerald-200 bg-emerald-50 p-6 shadow-sm">
        <div class="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
          <div class="flex items-start gap-4">
            <UIcon name="i-heroicons-shield-check" class="mt-1 h-8 w-8 flex-shrink-0 text-emerald-600" />
            <div>
              <h2 class="text-lg font-bold text-emerald-950">Commercial Status</h2>
              <p class="mt-1 text-sm text-emerald-800">
                {{ escrowText }}
              </p>
              <p v-if="order.escrow" class="mt-2 text-xs text-emerald-700">
                Escrow {{ order.escrow.status }} · Provider {{ order.escrow.provider || 'AinerWise Core' }}
              </p>
            </div>
          </div>
          <div class="text-left md:text-right">
            <p class="text-sm font-medium text-emerald-800">Order Amount</p>
            <p class="text-3xl font-extrabold text-emerald-700">{{ formatPrice(order.total_amount_minor, order.currency) }}</p>
          </div>
        </div>
      </div>

      <div class="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <UCard>
          <template #header>
            <h3 class="text-lg font-medium text-slate-900">Order Details</h3>
          </template>
          <dl class="space-y-4 text-sm">
            <div class="flex justify-between gap-4">
              <dt class="text-slate-500">Buyer ID</dt>
              <dd class="font-mono text-slate-900">{{ order.buyer_id || 'N/A' }}</dd>
            </div>
            <div class="flex justify-between gap-4">
              <dt class="text-slate-500">Supplier Company</dt>
              <dd class="font-mono text-slate-900">{{ order.company_id || 'N/A' }}</dd>
            </div>
            <div class="flex justify-between gap-4">
              <dt class="text-slate-500">Current Status</dt>
              <dd><UBadge :color="statusColor(order.status)" variant="subtle">{{ order.status }}</UBadge></dd>
            </div>
            <div class="flex justify-between gap-4 border-t border-slate-100 pt-4">
              <dt class="font-semibold text-slate-900">Total</dt>
              <dd class="font-bold text-indigo-700">{{ formatPrice(order.total_amount_minor, order.currency) }}</dd>
            </div>
          </dl>
        </UCard>

        <UCard>
          <template #header>
            <div>
              <h3 class="text-lg font-medium text-slate-900">Delivery Status</h3>
              <p class="mt-1 text-sm text-slate-500">Update fulfillment without leaving AinerWise Procurement.</p>
            </div>
          </template>

          <div class="space-y-4">
            <div v-if="order.delivery" class="rounded-2xl border border-slate-200 bg-slate-50 p-4 text-sm">
              <div class="flex items-center justify-between gap-4">
                <div>
                  <p class="font-semibold text-slate-900">{{ order.delivery.status }}</p>
                  <p v-if="order.delivery.tracking_number" class="mt-1 text-slate-500">
                    Tracking: {{ order.delivery.tracking_number }}
                  </p>
                  <p v-if="order.delivery.updated_at" class="mt-1 text-xs text-slate-400">
                    Updated {{ formatDate(order.delivery.updated_at) }}
                  </p>
                </div>
                <UBadge :color="deliveryColor(order.delivery.status)" variant="subtle">{{ order.delivery.status }}</UBadge>
              </div>
            </div>
            <div v-else class="rounded-2xl border border-dashed border-slate-200 bg-slate-50 p-4 text-sm text-slate-500">
              No delivery update has been submitted yet.
            </div>

            <div class="grid gap-4 sm:grid-cols-2">
              <UFormGroup label="Next Delivery Status">
                <USelect
                  v-model="deliveryStatus"
                  :options="deliveryStatusOptions"
                  option-attribute="label"
                  value-attribute="value"
                  :disabled="!canUpdateDelivery"
                />
              </UFormGroup>
              <UFormGroup label="Tracking Number">
                <UInput v-model="trackingNumber" placeholder="Optional tracking number" :disabled="!canUpdateDelivery" />
              </UFormGroup>
            </div>

            <UAlert
              v-if="!canUpdateDelivery"
              color="gray"
              variant="soft"
              icon="i-heroicons-information-circle"
              title="Delivery can only be updated while the order is paid, in progress, or delivered."
            />

            <div class="flex justify-end">
              <UButton color="indigo" :loading="deliverySaving" :disabled="!canUpdateDelivery" @click="updateDelivery">
                Save Delivery Update
              </UButton>
            </div>
          </div>
        </UCard>
      </div>

      <UCard>
        <template #header>
          <div class="flex items-center justify-between">
            <h3 class="text-lg font-medium text-slate-900">Rate Buyer</h3>
            <UBadge :color="buyerReview.transaction_channel === 'ONLINE' ? 'blue' : 'gray'" variant="soft">
              {{ buyerReview.transaction_channel }}
            </UBadge>
          </div>
        </template>

        <div class="space-y-4">
          <p class="text-sm text-slate-500">
            After a completed deal, sellers can rate buyer reliability and communication. Offline deals do not include logistics scoring.
          </p>
          <UFormGroup label="Transaction Type">
            <USelect
              v-model="buyerReview.transaction_channel"
              :options="[
                { label: 'Online transaction', value: 'ONLINE' },
                { label: 'Offline transaction', value: 'OFFLINE' }
              ]"
              option-attribute="label"
              value-attribute="value"
            />
          </UFormGroup>
          <div class="grid grid-cols-1 gap-4 md:grid-cols-2">
            <UFormGroup label="Buyer Reliability">
              <USelect v-model="buyerReview.buyer_rating" :options="ratingOptions" option-attribute="label" value-attribute="value" />
            </UFormGroup>
            <UFormGroup label="Buyer Communication">
              <USelect v-model="buyerReview.communication_rating" :options="ratingOptions" option-attribute="label" value-attribute="value" />
            </UFormGroup>
          </div>
          <UFormGroup label="Comment">
            <UTextarea v-model="buyerReview.comment" rows="3" placeholder="Payment readiness, response quality, requirements clarity..." />
          </UFormGroup>
          <div class="flex justify-end">
            <UButton color="indigo" :loading="submittingReview" @click="submitBuyerReview">Submit Buyer Review</UButton>
          </div>
        </div>
      </UCard>
    </template>

    <div v-else class="py-20 text-center text-slate-400">
      <p>Order not found.</p>
      <UButton to="/supplier/orders" color="indigo" variant="ghost" class="mt-4">Back to Orders</UButton>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { Order } from '~/types'

definePageMeta({ layout: 'supplier' })

const route = useRoute()
const authStore = useAuthStore()
const config = useRuntimeConfig()
const orderStore = useOrderStore()
const toast = useToast()
const { formatPrice } = useApiUtils()

const orderId = computed(() => String(route.params.id || ''))
const order = computed<Order | null>(() => orderStore.currentOrder)
const loading = ref(true)
const error = ref('')
const deliverySaving = ref(false)
const submittingReview = ref(false)
const deliveryStatus = ref('DISPATCHED')
const trackingNumber = ref('')

const ratingOptions = [
  { label: '5 - Excellent', value: 5 },
  { label: '4 - Good', value: 4 },
  { label: '3 - Average', value: 3 },
  { label: '2 - Poor', value: 2 },
  { label: '1 - Bad', value: 1 },
]

const deliveryStatusOptions = [
  { label: 'Ready for pickup', value: 'READY_FOR_PICKUP' },
  { label: 'Dispatched / shipped', value: 'DISPATCHED' },
  { label: 'Delivered', value: 'DELIVERED' },
  { label: 'Failed', value: 'FAILED' },
]

const buyerReview = reactive({
  transaction_channel: 'ONLINE',
  buyer_rating: 5,
  communication_rating: 5,
  comment: '',
})

const canUpdateDelivery = computed(() => {
  return ['PAID_IN_ESCROW', 'IN_PROGRESS', 'DELIVERED'].includes(order.value?.status || '')
})

const escrowText = computed(() => {
  if (!order.value?.escrow) return 'Payment or escrow has not been captured yet for this order.'
  if (['AUTH_HELD', 'CAPTURED'].includes(order.value.escrow.status)) {
    return 'Funds are secured and will be released after buyer acceptance.'
  }
  if (order.value.escrow.status === 'RELEASED') return 'Funds have been released for this order.'
  return `Escrow status is ${order.value.escrow.status}.`
})

watch(order, (value) => {
  if (!value?.delivery) return
  trackingNumber.value = value.delivery.tracking_number || ''
  if (value.delivery.status) deliveryStatus.value = value.delivery.status
}, { immediate: true })

function shortId(value?: string | null) {
  return value ? String(value).slice(0, 8) : 'N/A'
}

function formatDate(value?: string) {
  if (!value) return 'N/A'
  try {
    return new Intl.DateTimeFormat('en-PH', { dateStyle: 'medium', timeStyle: 'short' }).format(new Date(value))
  } catch {
    return value
  }
}

function statusColor(status: string) {
  const map: Record<string, string> = {
    CREATED: 'gray',
    AWAITING_PAYMENT: 'yellow',
    PAID_IN_ESCROW: 'indigo',
    IN_PROGRESS: 'blue',
    DELIVERED: 'green',
    ACCEPTED: 'green',
    PAYOUT_RELEASED: 'green',
    DISPUTED: 'red',
    CANCELED: 'gray',
    REFUNDED: 'gray',
  }
  return map[status] || 'gray'
}

function deliveryColor(status: string) {
  const map: Record<string, string> = {
    PENDING: 'yellow',
    READY_FOR_PICKUP: 'blue',
    DISPATCHED: 'indigo',
    DELIVERED: 'green',
    ACCEPTED: 'green',
    FAILED: 'red',
  }
  return map[status] || 'gray'
}

async function loadOrder() {
  loading.value = true
  error.value = ''
  try {
    await orderStore.fetchOrder(orderId.value)
  } catch (e: any) {
    const detail = e?.data?.detail || e?.message
    error.value = typeof detail === 'string' ? detail : 'Failed to load order.'
  } finally {
    loading.value = false
  }
}

async function updateDelivery() {
  if (!order.value || !canUpdateDelivery.value) return
  deliverySaving.value = true
  try {
    await orderStore.createDelivery(order.value.id, deliveryStatus.value, trackingNumber.value || undefined)
    toast.add({ title: 'Delivery updated', color: 'green' })
    await loadOrder()
  } catch (e: any) {
    const detail = e?.data?.detail || e?.message
    toast.add({ title: typeof detail === 'string' ? detail : 'Delivery update failed', color: 'red' })
  } finally {
    deliverySaving.value = false
  }
}

async function submitBuyerReview() {
  if (!order.value) return
  submittingReview.value = true
  try {
    await $fetch(`${config.public.apiBase}/orders/${order.value.id}/reviews/buyer`, {
      method: 'POST',
      body: {
        transaction_channel: buyerReview.transaction_channel,
        buyer_rating: Number(buyerReview.buyer_rating),
        communication_rating: Number(buyerReview.communication_rating),
        comment: buyerReview.comment || undefined,
      },
      headers: { Authorization: `Bearer ${authStore.accessToken}` },
    })
    toast.add({ title: 'Buyer review submitted', color: 'green' })
  } catch (e: any) {
    toast.add({ title: e?.data?.detail || 'Review failed', color: 'red' })
  } finally {
    submittingReview.value = false
  }
}

onMounted(loadOrder)
</script>
