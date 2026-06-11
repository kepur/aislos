<template>
  <div class="space-y-6">
    <div v-if="loading && !order" class="flex justify-center py-20">
      <UIcon name="i-heroicons-arrow-path" class="w-8 h-8 animate-spin text-slate-400" />
    </div>

    <template v-else-if="order">
      <!-- Header -->
      <div class="flex items-center gap-4 flex-wrap">
        <UButton to="/buyer/orders" color="gray" variant="ghost" icon="i-heroicons-arrow-left" size="sm" />
        <div class="flex-1">
          <div class="flex items-center gap-3 flex-wrap">
            <h1 class="text-2xl font-bold text-slate-900">Order #{{ order.id.split('-')[0].toUpperCase() }}</h1>
            <UBadge :color="statusColor(order.status)" variant="solid">{{ order.status }}</UBadge>
          </div>
          <p class="text-sm text-slate-500 mt-1">Placed {{ new Date(order.created_at).toLocaleDateString() }}</p>
        </div>
      </div>

      <!-- Escrow Banner -->
      <div class="bg-indigo-900 rounded-2xl p-6 text-white shadow-lg overflow-hidden relative">
        <div class="absolute right-0 top-0 opacity-10">
          <UIcon name="i-heroicons-shield-check" class="w-64 h-64 -mt-10 -mr-10" />
        </div>
        <div class="relative z-10 flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <h2 class="text-xl font-bold flex items-center">
              <UIcon name="i-heroicons-lock-closed" class="w-6 h-6 mr-2 text-indigo-300" />
              {{ formatMinor(order.total_amount_minor, order.currency) }} in Secure Escrow
            </h2>
            <p class="text-indigo-200 mt-1">Funds are held safely and released only on delivery confirmation.</p>
          </div>
          <div class="flex gap-3 flex-wrap">
            <UButton
              v-if="order.status === 'DELIVERED'"
              color="white"
              variant="solid"
              class="text-indigo-900 font-bold px-6"
              :loading="confirming"
              @click="confirmDelivery"
            >
              ✓ Confirm Delivery
            </UButton>
            <UButton
              v-if="['PAID_IN_ESCROW','IN_PROGRESS','DELIVERED'].includes(order.status)"
              color="red"
              variant="soft"
              :to="`/buyer/disputes/new?order_id=${order.id}`"
            >
              Open Dispute
            </UButton>
            <!-- Pay from wallet if awaiting payment -->
            <UButton
              v-if="order.status === 'AWAITING_PAYMENT'"
              color="indigo"
              icon="i-heroicons-credit-card"
              :loading="paying"
              @click="payFromWallet"
            >
              Pay from Wallet
            </UButton>
          </div>
        </div>
      </div>

      <!-- Order Progress -->
      <UCard>
        <div class="py-2">
          <div class="flex items-start justify-between max-w-3xl mx-auto relative">
            <div class="absolute top-4 left-0 right-0 h-1 bg-slate-200" />
            <div
              class="absolute top-4 left-0 h-1 bg-green-500 transition-all"
              :style="{ width: progressWidth }"
            />
            <div v-for="(step, i) in steps" :key="step.key" class="flex flex-col items-center z-10 w-1/5">
              <div :class="[
                'w-8 h-8 rounded-full flex items-center justify-center border-4 border-white shadow',
                stepDone(step.key) ? 'bg-green-500 text-white' : stepActive(step.key) ? 'bg-indigo-500 text-white animate-pulse' : 'bg-slate-200 text-slate-400'
              ]">
                <UIcon v-if="stepDone(step.key)" name="i-heroicons-check" class="w-4 h-4" />
                <span v-else class="text-xs font-bold">{{ i + 1 }}</span>
              </div>
              <span :class="['text-xs font-medium mt-2 text-center', stepActive(step.key) ? 'text-indigo-600' : stepDone(step.key) ? 'text-green-700' : 'text-slate-400']">
                {{ step.label }}
              </span>
            </div>
          </div>
        </div>
      </UCard>

      <!-- Details Grid -->
      <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
        <!-- Order Summary -->
        <UCard>
          <template #header>
            <h3 class="text-lg font-medium text-slate-900">Order Details</h3>
          </template>
          <dl class="space-y-3">
            <div class="flex justify-between">
              <dt class="text-sm text-slate-500">Item</dt>
              <dd class="text-sm font-medium text-slate-900 text-right max-w-xs">{{ order.item_description || '—' }}</dd>
            </div>
            <div class="flex justify-between">
              <dt class="text-sm text-slate-500">Quantity</dt>
              <dd class="text-sm font-medium text-slate-900">{{ order.qty || '—' }} {{ order.unit || '' }}</dd>
            </div>
            <div class="flex justify-between">
              <dt class="text-sm text-slate-500">Unit Price</dt>
              <dd class="text-sm font-medium text-slate-900">{{ formatMinor(order.unit_price_minor, order.currency) }}</dd>
            </div>
            <div class="flex justify-between">
              <dt class="text-sm text-slate-500">Subtotal</dt>
              <dd class="text-sm font-medium text-slate-900">{{ formatMinor(order.subtotal_minor || order.total_amount_minor, order.currency) }}</dd>
            </div>
            <div class="flex justify-between border-t border-slate-100 pt-3">
              <dt class="text-base font-bold text-slate-900">Total (Escrow)</dt>
              <dd class="text-base font-bold text-indigo-700">{{ formatMinor(order.total_amount_minor, order.currency) }}</dd>
            </div>
          </dl>
        </UCard>

        <!-- Supplier Info -->
        <UCard>
          <template #header>
            <h3 class="text-lg font-medium text-slate-900">Supplier & Logistics</h3>
          </template>
          <div class="flex items-center gap-4 mb-4">
            <div class="w-10 h-10 rounded-xl bg-indigo-100 flex items-center justify-center text-xl">🏢</div>
            <div class="flex-1">
              <p class="font-bold text-slate-900">{{ order.supplier_company_name || 'Supplier' }}</p>
              <p class="text-xs text-green-600 flex items-center gap-1">
                <UIcon name="i-heroicons-shield-check" class="w-3 h-3" /> Verified Supplier
              </p>
            </div>
            <UButton color="gray" variant="ghost" icon="i-heroicons-chat-bubble-left" size="xs" :to="`/buyer/messages`" />
          </div>
          <dl class="space-y-3 border-t border-slate-100 pt-4">
            <div v-if="order.delivery_address">
              <dt class="text-xs font-semibold text-slate-500 uppercase">Delivery Address</dt>
              <dd class="mt-1 text-sm text-slate-900">{{ order.delivery_address }}</dd>
            </div>
            <div v-if="order.estimated_delivery">
              <dt class="text-xs font-semibold text-slate-500 uppercase">Estimated Delivery</dt>
              <dd class="mt-1 text-sm font-medium text-slate-900">{{ new Date(order.estimated_delivery).toLocaleDateString() }}</dd>
            </div>
            <div>
              <dt class="text-xs font-semibold text-slate-500 uppercase">Last Updated</dt>
              <dd class="mt-1 text-sm text-slate-900">{{ new Date(order.updated_at).toLocaleString() }}</dd>
            </div>
          </dl>
        </UCard>
      </div>

      <!-- Delivery History -->
      <UCard v-if="deliveries.length > 0">
        <template #header>
          <h3 class="text-lg font-medium text-slate-900">📦 Delivery Records</h3>
        </template>
        <div class="space-y-3">
          <div v-for="d in deliveries" :key="d.id" class="flex gap-4 p-3 rounded-xl border border-slate-100 hover:bg-slate-50">
            <div class="flex-shrink-0 w-10 h-10 rounded-xl bg-green-50 flex items-center justify-center text-green-600">
              <UIcon name="i-heroicons-truck" class="w-5 h-5" />
            </div>
            <div class="flex-1">
              <p class="text-sm font-medium text-slate-900">{{ d.notes || 'Delivery update' }}</p>
              <p class="text-xs text-slate-400 mt-0.5">{{ new Date(d.created_at).toLocaleString() }}</p>
              <div v-if="d.proof_urls && d.proof_urls.length" class="flex gap-2 mt-2">
                <a v-for="url in d.proof_urls" :key="url" :href="url" target="_blank" class="text-xs text-indigo-600 hover:underline">
                  📷 Photo proof
                </a>
              </div>
            </div>
            <UBadge :color="d.status === 'DELIVERED' ? 'green' : 'yellow'" variant="subtle" class="self-start">{{ d.status }}</UBadge>
          </div>
        </div>
      </UCard>

      <UCard v-if="canReviewSeller">
        <template #header>
          <div class="flex items-center justify-between">
            <h3 class="text-lg font-medium text-slate-900">Rate Seller</h3>
            <UBadge :color="sellerReview.transaction_channel === 'ONLINE' ? 'blue' : 'gray'" variant="soft">
              {{ sellerReview.transaction_channel }}
            </UBadge>
          </div>
        </template>

        <div class="space-y-4">
          <UFormGroup label="Transaction Type">
            <USelect
              v-model="sellerReview.transaction_channel"
              :options="[
                { label: 'Online transaction with logistics', value: 'ONLINE' },
                { label: 'Offline transaction / self pickup', value: 'OFFLINE' }
              ]"
              option-attribute="label"
              value-attribute="value"
            />
          </UFormGroup>

          <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
            <UFormGroup label="Product Quality">
              <USelect v-model="sellerReview.product_quality_rating" :options="ratingOptions" option-attribute="label" value-attribute="value" />
            </UFormGroup>
            <UFormGroup v-if="sellerReview.transaction_channel === 'ONLINE'" label="Logistics">
              <USelect v-model="sellerReview.logistics_rating" :options="ratingOptions" option-attribute="label" value-attribute="value" />
            </UFormGroup>
            <UFormGroup label="Seller Communication">
              <USelect v-model="sellerReview.communication_rating" :options="ratingOptions" option-attribute="label" value-attribute="value" />
            </UFormGroup>
          </div>

          <UFormGroup label="Comment">
            <UTextarea v-model="sellerReview.comment" rows="3" placeholder="Share what went well or what needs improvement..." />
          </UFormGroup>

          <div class="flex justify-end">
            <UButton color="indigo" :loading="submittingReview" @click="submitSellerReview">Submit Review</UButton>
          </div>
        </div>
      </UCard>
    </template>

    <div v-else class="text-center py-20 text-slate-400">
      <div class="text-5xl mb-3">📦</div>
      <p>Order not found.</p>
      <UButton to="/buyer/orders" color="indigo" variant="ghost" class="mt-4">Back to Orders</UButton>
    </div>
  </div>
</template>

<script setup lang="ts">
definePageMeta({ layout: 'buyer', middleware: ['buyer'] })

const route = useRoute()
const authStore = useAuthStore()
const config = useRuntimeConfig()
const toast = useToast()

const order = ref<any>(null)
const deliveries = ref<any[]>([])
const loading = ref(true)
const confirming = ref(false)
const paying = ref(false)
const submittingReview = ref(false)

const ratingOptions = [
  { label: '5 - Excellent', value: 5 },
  { label: '4 - Good', value: 4 },
  { label: '3 - Average', value: 3 },
  { label: '2 - Poor', value: 2 },
  { label: '1 - Bad', value: 1 },
]

const sellerReview = reactive({
  transaction_channel: 'ONLINE',
  product_quality_rating: 5,
  logistics_rating: 5,
  communication_rating: 5,
  comment: '',
})

const canReviewSeller = computed(() => {
  return order.value && ['ACCEPTED', 'PAYOUT_RELEASED'].includes(order.value.status)
})

const steps = [
  { key: 'PAID_IN_ESCROW', label: 'Escrow Paid' },
  { key: 'IN_PROGRESS', label: 'In Progress' },
  { key: 'DELIVERED', label: 'Delivered' },
  { key: 'PAYOUT_RELEASED', label: 'Completed' },
]
const stepOrder = steps.map(s => s.key)

const currentStepIdx = computed(() => {
  if (!order.value) return 0
  if (['ACCEPTED', 'PAYOUT_RELEASED'].includes(order.value.status)) return steps.length - 1
  const idx = stepOrder.indexOf(order.value.status)
  return idx === -1 ? 0 : idx
})

const progressWidth = computed(() => `${(currentStepIdx.value / (steps.length - 1)) * 100}%`)

function stepDone(key: string) {
  return stepOrder.indexOf(key) < currentStepIdx.value
}
function stepActive(key: string) {
  return stepOrder.indexOf(key) === currentStepIdx.value
}

function statusColor(s: string) {
  return {
    AWAITING_PAYMENT: 'orange',
    PAID_IN_ESCROW: 'blue',
    IN_PROGRESS: 'purple',
    DELIVERED: 'indigo',
    ACCEPTED: 'green',
    PAYOUT_RELEASED: 'green',
    DISPUTED: 'red',
    CANCELED: 'gray',
    REFUNDED: 'gray',
  }[s] || 'gray'
}

function formatMinor(minor: number, currency = 'PHP') {
  if (!minor) return '—'
  const amount = minor / 100
  try { return new Intl.NumberFormat('en-PH', { style: 'currency', currency, minimumFractionDigits: 0, maximumFractionDigits: 0 }).format(amount) }
  catch { return `${amount.toLocaleString()} ${currency}` }
}

async function loadOrder() {
  loading.value = true
  try {
    const headers = { Authorization: `Bearer ${authStore.accessToken}` }
    const [ord, del] = await Promise.all([
      $fetch<any>(`${config.public.apiBase}/orders/${route.params.id}`, { headers }),
      $fetch<any>(`${config.public.apiBase}/orders/${route.params.id}/delivery`, { headers }).catch(() => []),
    ])
    order.value = ord
    deliveries.value = Array.isArray(del) ? del : del?.records ?? []
  } catch (e: any) {
    console.error('Order load error:', e)
  } finally {
    loading.value = false
  }
}

async function confirmDelivery() {
  confirming.value = true
  try {
    await $fetch(`${config.public.apiBase}/orders/${route.params.id}/accept`, {
      method: 'POST',
      headers: { Authorization: `Bearer ${authStore.accessToken}` },
    })
    toast.add({ title: 'Delivery confirmed! Escrow will be released.', color: 'green' })
    await loadOrder()
  } catch (e: any) {
    toast.add({ title: e?.data?.detail || 'Failed to confirm delivery', color: 'red' })
  } finally {
    confirming.value = false
  }
}

async function payFromWallet() {
  paying.value = true
  try {
    await $fetch(`${config.public.apiBase}/orders/${route.params.id}/pay-from-wallet`, {
      method: 'POST',
      headers: { Authorization: `Bearer ${authStore.accessToken}` },
    })
    toast.add({ title: 'Payment successful! Order is now funded.', color: 'green' })
    await loadOrder()
  } catch (e: any) {
    toast.add({ title: e?.data?.detail || 'Payment failed. Check your wallet balance.', color: 'red' })
  } finally {
    paying.value = false
  }
}

async function submitSellerReview() {
  submittingReview.value = true
  try {
    const body: Record<string, any> = {
      transaction_channel: sellerReview.transaction_channel,
      product_quality_rating: Number(sellerReview.product_quality_rating),
      communication_rating: Number(sellerReview.communication_rating),
      comment: sellerReview.comment || undefined,
    }
    if (sellerReview.transaction_channel === 'ONLINE') {
      body.logistics_rating = Number(sellerReview.logistics_rating)
    }
    await $fetch(`${config.public.apiBase}/orders/${route.params.id}/reviews/seller`, {
      method: 'POST',
      body,
      headers: { Authorization: `Bearer ${authStore.accessToken}` },
    })
    toast.add({ title: 'Seller review submitted', color: 'green' })
  } catch (e: any) {
    toast.add({ title: e?.data?.detail || 'Review failed', color: 'red' })
  } finally {
    submittingReview.value = false
  }
}

onMounted(() => loadOrder())
</script>
