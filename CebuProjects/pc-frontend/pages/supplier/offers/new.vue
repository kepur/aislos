<template>
  <div class="space-y-6 max-w-5xl mx-auto py-6">
    <div class="flex items-center space-x-4 mb-2">
      <UButton to="/supplier/inbox" color="gray" variant="ghost" icon="i-heroicons-arrow-left" size="sm" />
      <div>
        <h1 class="text-2xl font-bold text-slate-900">Submit Offer</h1>
        <p class="text-sm text-slate-500 mt-1">For Request: 500 bags Portland Cement (Ref: #REQ-82910)</p>
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
              <dd class="font-bold text-slate-900 mt-0.5">500 Bags</dd>
            </div>
            <div>
              <dt class="font-medium text-slate-500">Buyer Budget</dt>
              <dd class="font-bold text-slate-900 mt-0.5">$2,000 - $2,500</dd>
            </div>
            <div>
              <dt class="font-medium text-slate-500">Delivery Location</dt>
              <dd class="font-medium text-slate-900 mt-0.5">Mandaue City (4.2 km away)</dd>
            </div>
            <div>
              <dt class="font-medium text-slate-500">Required By</dt>
              <dd class="font-medium text-slate-900 mt-0.5">Tomorrow afternoon</dd>
            </div>
            <div>
              <dt class="font-medium text-slate-500">Notes</dt>
              <dd class="text-slate-700 mt-0.5 italic">"Looking for Holcim or Republic brand."</dd>
            </div>
          </dl>
          
          <div class="mt-6 pt-4 border-t border-slate-200">
            <UBadge color="green" variant="subtle" class="w-full justify-center">Pre-funded Escrow Status</UBadge>
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
                <USelect v-model="form.stock" :options="['High (In Warehouse)', 'Medium (Supplier Network)', 'Low (Need to order)']" size="lg" />
              </UFormGroup>
            </div>

            <UFormGroup label="Warranty / Return Policy">
              <UInput v-model="form.warranty" placeholder="e.g. Return if defective" size="lg" />
            </UFormGroup>

            <UFormGroup label="Notes to Buyer">
              <UTextarea v-model="form.notes" :rows="3" placeholder="Specify brand, packaging details, or delivery requirements..." />
            </UFormGroup>

            <div class="pt-4 flex justify-end space-x-4">
              <UButton color="gray" variant="ghost" size="lg" to="/supplier/inbox">Cancel</UButton>
              <UButton type="submit" color="indigo" size="lg" class="px-8 font-bold" icon="i-heroicons-paper-airplane">Send Offer</UButton>
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

definePageMeta({
  layout: 'supplier'
})

const router = useRouter()
const route = useRoute()
const api = useApiFetch()
const qty = 500
const intentCountry = ref('PH')
const selectedOriginAddressId = ref<string>('')
const shippingAddresses = ref<any[]>([])
const shippingEstimate = ref<{ total_shipping_minor: number; estimated_days_min: number; estimated_days_max: number; currency: string } | null>(null)

const form = ref({
  unitPrice: 4.20,
  deliveryFee: 50.00,
  eta: 'Tomorrow, 2:00 PM',
  stock: 'High (In Warehouse)',
  warranty: 'Return if defective',
  notes: 'We have Republic Cement in stock. Can deliver by tomorrow 2PM via our flatbed truck. Price includes unloading at the site.'
})

const totalItemCost = computed(() => {
  return (form.value.unitPrice * qty).toFixed(2)
})

const totalLandedCost = computed(() => {
  return ((form.value.unitPrice * qty) + Number(form.value.deliveryFee)).toFixed(2)
})

const destCountry = computed(() => intentCountry.value || 'PH')
const shippingAddressOptions = computed(() =>
  shippingAddresses.value.map((a: any) => ({
    label: `${a.label} · ${a.city} · ${a.country_name}`,
    value: a.id
  }))
)

const submitOffer = () => {
  if(confirm(`Submit offer with Total Landed Cost of $${totalLandedCost.value}?`)) {
    alert('Offer sent successfully to the buyer!')
    router.push('/supplier/dashboard')
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
  const intentId = route.query.intent_id as string | undefined
  if (!intentId) return
  try {
    const intent = await api<{ country?: string }>(`/intents/${intentId}`)
    intentCountry.value = intent.country || 'PH'
  } catch {
    intentCountry.value = 'PH'
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
        weight_kg: qty,
        declared_value_minor: Math.round(form.value.unitPrice * qty * 100),
        currency: 'USD'
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
