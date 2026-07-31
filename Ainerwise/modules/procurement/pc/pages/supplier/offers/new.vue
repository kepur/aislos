<template>
  <div class="space-y-6 max-w-5xl mx-auto py-6">
    <div class="flex items-center space-x-4 mb-2">
      <UButton to="/supplier/inbox" color="gray" variant="ghost" icon="i-heroicons-arrow-left" size="sm" />
      <div>
        <h1 class="text-2xl font-bold text-slate-900">Submit Offer</h1>
        <p class="text-sm text-slate-500 mt-1">
          <span v-if="intent">For Request: {{ intent.title }} (Ref: #{{ String(intent.id).slice(0, 8) }})</span>
          <span v-else>Load a buyer request from the supplier inbox before submitting an offer.</span>
        </p>
      </div>
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
      <!-- Buyer Request Summary -->
      <div class="lg:col-span-1 space-y-6">
        <UCard class="bg-slate-50 border-slate-200">
          <template #header>
            <h3 class="text-sm font-semibold text-slate-900 uppercase tracking-wider">Request Details</h3>
          </template>

          <dl class="space-y-4 text-sm">
            <div>
              <dt class="font-medium text-slate-500">Quantity</dt>
              <dd class="font-bold text-slate-900 mt-0.5">{{ qty }} {{ intent?.unit || 'pcs' }}</dd>
            </div>
            <div>
              <dt class="font-medium text-slate-500">Buyer Budget</dt>
              <dd class="font-bold text-slate-900 mt-0.5">{{ budgetLabel }}</dd>
            </div>
            <div>
              <dt class="font-medium text-slate-500">Delivery Location</dt>
              <dd class="font-medium text-slate-900 mt-0.5">{{ deliveryLocationLabel }}</dd>
            </div>
            <div>
              <dt class="font-medium text-slate-500">Required By</dt>
              <dd class="font-medium text-slate-900 mt-0.5">{{ requiredByLabel }}</dd>
            </div>
            <div>
              <dt class="font-medium text-slate-500">Notes</dt>
              <dd class="text-slate-700 mt-0.5 italic">"{{ intent?.notes || 'No additional buyer notes.' }}"</dd>
            </div>
          </dl>

          <div class="mt-6 pt-4 border-t border-slate-200">
            <UBadge color="green" variant="subtle" class="w-full justify-center">Verified Buyer Request</UBadge>
          </div>
        </UCard>
      </div>

      <!-- Offer Form -->
      <div class="lg:col-span-2">
        <UCard>
          <form class="space-y-6" @submit.prevent="submitOffer">
            <div class="grid grid-cols-2 gap-6">
              <div class="space-y-1">
                <label class="block text-sm font-medium text-slate-700">Unit Price <span class="text-red-500">*</span></label>
                <div class="relative">
                  <span class="absolute inset-y-0 left-3 flex items-center text-slate-400 text-sm pointer-events-none">$</span>
                  <input v-model="form.unitPrice" type="number" step="0.01" min="0"
                    class="w-full rounded-lg border border-slate-200 bg-white pl-7 pr-4 py-3 text-sm text-slate-800 shadow-sm focus:border-indigo-400 focus:outline-none focus:ring-2 focus:ring-indigo-200" />
                </div>
              </div>

              <div class="space-y-1">
                <label class="block text-sm font-medium text-slate-700">Total Item Cost</label>
                <div class="relative">
                  <span class="absolute inset-y-0 left-3 flex items-center text-slate-400 text-sm pointer-events-none">$</span>
                  <input :value="totalItemCost" disabled type="text"
                    class="w-full rounded-lg border border-slate-100 bg-slate-50 pl-7 pr-4 py-3 text-sm text-slate-600 cursor-not-allowed" />
                </div>
              </div>
            </div>

            <div class="grid grid-cols-2 gap-6">
              <UFormGroup label="Shipping From Address" required>
                <USelect
                  v-model="selectedOriginAddressId"
                  :options="shippingAddressOptions"
                  option-attribute="label"
                  value-attribute="value"
                  size="lg"
                  @change="recalculateShipping"
                />
              </UFormGroup>

              <UFormGroup label="Destination Country">
                <UInput :model-value="destCountry" disabled size="lg" class="bg-slate-50" />
              </UFormGroup>
            </div>

            <div class="grid grid-cols-2 gap-6">
              <div class="space-y-1">
                <label class="block text-sm font-medium text-slate-700">Delivery Fee <span class="text-red-500">*</span></label>
                <div class="relative">
                  <span class="absolute inset-y-0 left-3 flex items-center text-slate-400 text-sm pointer-events-none">$</span>
                  <input v-model="form.deliveryFee" type="number" step="0.01" min="0"
                    class="w-full rounded-lg border border-slate-200 bg-white pl-7 pr-4 py-3 text-sm text-slate-800 shadow-sm focus:border-indigo-400 focus:outline-none focus:ring-2 focus:ring-indigo-200" />
                </div>
                <p v-if="shippingEstimate" class="text-xs text-primary-600 mt-1">
                  Estimated ETA {{ shippingEstimate.estimated_days_min }}-{{ shippingEstimate.estimated_days_max }} days
                </p>
                <p v-else class="text-xs text-slate-500 mt-1">Distance is 4.2 km</p>
              </div>

              <UFormGroup label="Total Landed Cost">
                <div class="h-[44px] flex items-center px-4 bg-indigo-50 border border-indigo-200 rounded-md text-lg font-bold text-indigo-700">
                  ${{ totalLandedCost }}
                </div>
              </UFormGroup>
            </div>

            <div class="border-t border-slate-200 my-6"></div>

            <div class="grid grid-cols-2 gap-6">
              <div class="space-y-1">
                <label class="block text-sm font-medium text-slate-700">ETA (Estimated Time of Arrival) <span class="text-red-500">*</span></label>
                <div class="relative">
                  <span class="absolute inset-y-0 left-3 flex items-center pointer-events-none">
                    <svg class="w-4 h-4 text-slate-400" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                  </span>
                  <input v-model="form.eta" type="text" placeholder="e.g. Tomorrow, 2:00 PM"
                    class="w-full rounded-lg border border-slate-200 bg-white pl-9 pr-4 py-3 text-sm text-slate-800 shadow-sm focus:border-indigo-400 focus:outline-none focus:ring-2 focus:ring-indigo-200" />
                </div>
              </div>

              <UFormGroup label="Stock Confidence" required>
                <USelect v-model="form.stock" :options="stockOptions" option-attribute="label" value-attribute="value" size="lg" />
              </UFormGroup>
            </div>

            <UFormGroup label="Warranty / Return Policy">
              <UInput v-model="form.warranty" placeholder="e.g. Return if defective" size="lg" />
            </UFormGroup>

            <UFormGroup label="Notes to Buyer">
              <UTextarea v-model="form.notes" :rows="3" placeholder="Specify brand, packaging details, or delivery requirements..." />
            </UFormGroup>

            <p v-if="error" class="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">{{ error }}</p>

            <div class="pt-4 flex justify-end space-x-4">
              <UButton color="gray" variant="ghost" size="lg" to="/supplier/inbox">Cancel</UButton>
              <UButton type="submit" color="indigo" size="lg" class="px-8 font-bold" icon="i-heroicons-paper-airplane" :loading="loading" :disabled="!intent || !canSubmit">Send Offer</UButton>
            </div>
          </form>
        </UCard>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import type { Intent } from '~/types'

definePageMeta({
  layout: 'supplier'
})

const router = useRouter()
const route = useRoute()
const api = useApiFetch()
const offerStore = useOfferStore()
const intent = ref<Intent | null>(null)
const loading = ref(false)
const error = ref('')
const intentCountry = ref('PH')
const selectedOriginAddressId = ref<string>('')
const shippingAddresses = ref<any[]>([])
const shippingEstimate = ref<{ total_shipping_minor: number; estimated_days_min: number; estimated_days_max: number; currency: string } | null>(null)

const form = ref({
  unitPrice: 4.20,
  deliveryFee: 50.00,
  eta: 'Tomorrow, 2:00 PM',
  stock: 'FIRM',
  warranty: 'Return if defective',
  notes: 'We have Republic Cement in stock. Can deliver by tomorrow 2PM via our flatbed truck. Price includes unloading at the site.'
})

const stockOptions = [
  { label: 'High (In Warehouse)', value: 'FIRM' },
  { label: 'Medium (Supplier Network)', value: 'UNKNOWN' },
  { label: 'Low (Need to order)', value: 'BACKORDER' },
]

const intentId = computed(() => (typeof route.query.intent_id === 'string' ? route.query.intent_id : ''))
const qty = computed(() => Math.max(1, Number(intent.value?.qty || 1)))
const currency = computed(() => intent.value?.currency || shippingEstimate.value?.currency || 'PHP')
const canSubmit = computed(() => Boolean(intentId.value && form.value.unitPrice > 0 && qty.value > 0))

const totalItemCost = computed(() => {
  return (form.value.unitPrice * qty.value).toFixed(2)
})

const totalLandedCost = computed(() => {
  return ((form.value.unitPrice * qty.value) + Number(form.value.deliveryFee)).toFixed(2)
})

const destCountry = computed(() => intentCountry.value || 'PH')
const budgetLabel = computed(() => {
  const row = intent.value
  if (!row) return 'Loading...'
  if (row.budget_min_minor && row.budget_max_minor) {
    return `${formatMinor(row.budget_min_minor, row.currency)} - ${formatMinor(row.budget_max_minor, row.currency)}`
  }
  if (row.budget_max_minor) return `Up to ${formatMinor(row.budget_max_minor, row.currency)}`
  return 'Open'
})
const deliveryLocationLabel = computed(() => {
  const row = intent.value
  if (!row) return 'Loading...'
  return [row.city, row.country].filter(Boolean).join(', ') || `${row.radius_km || 30} km service area`
})
const requiredByLabel = computed(() => {
  const row = intent.value
  if (!row) return 'Loading...'
  const dates = [row.delivery_window_start, row.delivery_window_end].filter(Boolean)
  if (dates.length) return dates.map((value) => new Date(String(value)).toLocaleDateString('en-PH')).join(' - ')
  return row.expires_at ? `Before ${new Date(row.expires_at).toLocaleDateString('en-PH')}` : 'Flexible'
})
const shippingAddressOptions = computed(() =>
  shippingAddresses.value.map((a: any) => ({
    label: `${a.label} · ${a.city} · ${a.country_name}`,
    value: a.id
  }))
)

function formatMinor(amountMinor: number, valueCurrency = 'PHP') {
  try {
    return new Intl.NumberFormat('en-PH', {
      style: 'currency',
      currency: valueCurrency,
      minimumFractionDigits: 0,
      maximumFractionDigits: 2,
    }).format(amountMinor / 100)
  } catch {
    return `${(amountMinor / 100).toLocaleString()} ${valueCurrency}`
  }
}

async function submitOffer() {
  if (!canSubmit.value || loading.value) return
  if (!window.confirm(`Submit offer with Total Landed Cost of ${formatMinor(Math.round(Number(totalLandedCost.value) * 100), currency.value)}?`)) return
  loading.value = true
  error.value = ''
  const payload: Record<string, unknown> = {
    qty_available: qty.value,
    unit_price_minor: Math.round(Number(form.value.unitPrice) * 100),
    delivery_fee_minor: Math.round(Number(form.value.deliveryFee) * 100),
    currency: currency.value,
    tier: 'GOOD',
    stock_confidence: form.value.stock,
    message: form.value.notes || undefined,
    warranty: form.value.warranty || undefined,
  }
  try {
    await offerStore.submitOffer(intentId.value, payload)
    window.alert('Offer submitted to the buyer.')
    await router.push('/supplier/offers')
  } catch (err: any) {
    const detail = err?.data?.detail
    error.value = typeof detail === 'string' ? detail : JSON.stringify(detail) || 'Failed to submit offer'
  } finally {
    loading.value = false
  }
}

const selectedOriginAddress = computed(() =>
  shippingAddresses.value.find((a: any) => a.id === selectedOriginAddressId.value) || null
)

async function loadShippingAddresses() {
  try {
    shippingAddresses.value = await api('/addresses?address_type=SHIPPING_FROM')
    const defaultAddr = shippingAddresses.value.find((a: any) => a.is_default)
    if (defaultAddr) selectedOriginAddressId.value = defaultAddr.id
    else if (shippingAddresses.value.length) selectedOriginAddressId.value = shippingAddresses.value[0].id
  } catch {
    shippingAddresses.value = []
  }
}

async function loadIntentCountry() {
  if (!intentId.value) {
    error.value = 'Missing buyer request id.'
    return
  }
  try {
    const row = await api<Intent>(`/intents/${intentId.value}`)
    intent.value = row
    intentCountry.value = row.country || 'PH'
    if (row.budget_max_minor && row.qty) {
      form.value.unitPrice = Number(((row.budget_max_minor / 100) / Math.max(1, row.qty)).toFixed(2))
    }
  } catch (err: any) {
    intentCountry.value = 'PH'
    error.value = err?.data?.detail || 'Failed to load buyer request.'
  }
}

async function recalculateShipping() {
  if (!selectedOriginAddress.value) return
  try {
    const res = await api<{
      estimates: Array<{ total_shipping_minor: number; estimated_days_min: number; estimated_days_max: number; currency: string }>
    }>('/shipping/estimate', {
      method: 'POST',
      body: {
        origin_country: selectedOriginAddress.value.country_code || 'PH',
        dest_country: destCountry.value || 'PH',
        weight_kg: qty.value,
        declared_value_minor: Math.round(form.value.unitPrice * qty.value * 100),
        currency: currency.value
      }
    })
    shippingEstimate.value = res.estimates?.[0] || null
    if (shippingEstimate.value) {
      form.value.deliveryFee = Number((shippingEstimate.value.total_shipping_minor / 100).toFixed(2))
    }
  } catch {
    shippingEstimate.value = null
  }
}

onMounted(async () => {
  await loadShippingAddresses()
  await loadIntentCountry()
  await recalculateShipping()
})

watch(() => [form.value.unitPrice, selectedOriginAddressId.value, destCountry.value], async () => {
  await recalculateShipping()
})
</script>
