<template>
  <div class="space-y-6">
    <div class="flex items-center space-x-4 mb-2">
      <UButton to="/supplier/dashboard" color="gray" variant="ghost" icon="i-heroicons-arrow-left" size="sm" />
      <div>
        <div class="flex items-center space-x-3">
          <h1 class="text-2xl font-bold text-slate-900">Order #ORD-82910</h1>
          <UBadge color="blue" variant="solid">Pending Delivery</UBadge>
        </div>
        <p class="text-sm text-slate-500 mt-1">500 bags Portland Cement • Awarded Oct 25, 2023</p>
      </div>
    </div>

    <!-- Escrow Alert -->
    <div class="bg-green-50 border border-green-200 rounded-xl p-6 flex items-start shadow-sm">
      <UIcon name="i-heroicons-shield-check" class="w-8 h-8 text-green-600 mr-4 flex-shrink-0" />
      <div class="flex-1">
        <h4 class="font-bold text-green-900 mb-1">Funds Secured in Escrow</h4>
        <p class="text-sm text-green-800">The buyer has authorized $2,150.00. This amount is held by ProcurePing and will be released to your wallet once the buyer confirms delivery.</p>
      </div>
      <div class="text-right">
        <div class="text-sm text-green-800 font-medium">Payout Amount</div>
        <div class="text-2xl font-bold text-green-700">$2,150.00</div>
      </div>
    </div>

    <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
      <!-- Fulfillment Actions -->
      <UCard>
        <template #header>
          <h3 class="text-lg font-medium text-slate-900">Fulfillment Status</h3>
        </template>
        
        <div class="space-y-6">
          <div class="relative max-w-sm mx-auto">
            <div class="absolute top-1/2 left-0 w-full h-1 bg-slate-200 -translate-y-1/2 z-0"></div>
            <div class="absolute top-1/2 left-0 w-1/2 h-1 bg-indigo-500 -translate-y-1/2 z-0"></div>
            
            <div class="relative z-10 flex justify-between">
              <div class="flex flex-col items-center">
                <div class="w-8 h-8 rounded-full bg-indigo-500 text-white flex items-center justify-center border-4 border-white"><UIcon name="i-heroicons-check" class="w-4 h-4"/></div>
                <span class="text-xs font-medium mt-2">Awarded</span>
              </div>
              <div class="flex flex-col items-center">
                <div class="w-8 h-8 rounded-full bg-indigo-500 text-white flex items-center justify-center border-4 border-white shadow animate-pulse">2</div>
                <span class="text-xs font-medium mt-2 text-indigo-600">In Transit</span>
              </div>
              <div class="flex flex-col items-center">
                <div class="w-8 h-8 rounded-full bg-slate-200 text-slate-400 flex items-center justify-center border-4 border-white">3</div>
                <span class="text-xs font-medium mt-2 text-slate-400">Delivered</span>
              </div>
            </div>
          </div>
          
          <div class="pt-4 border-t border-slate-100">
            <h4 class="font-medium text-slate-900 mb-4">Required Actions</h4>
            
            <div class="space-y-4">
              <UFormGroup label="Upload Proof of Delivery (Delivery Receipt)">
                <div class="border-2 border-dashed border-slate-300 rounded-lg p-4 text-center hover:bg-slate-50 cursor-pointer">
                  <UIcon name="i-heroicons-camera" class="w-6 h-6 text-slate-400 mx-auto mb-1" />
                  <p class="text-xs text-slate-600">Upload signed DR / Photo</p>
                </div>
              </UFormGroup>
              
              <UButton block color="indigo" size="lg" class="font-bold">Mark as Delivered</UButton>
            </div>
          </div>
        </div>
      </UCard>

      <!-- Logistics Details -->
      <UCard>
        <template #header>
          <div class="flex justify-between items-center">
            <h3 class="text-lg font-medium text-slate-900">Delivery Details</h3>
            <UButton size="xs" color="gray" variant="ghost" icon="i-heroicons-chat-bubble-left">Message Buyer</UButton>
          </div>
        </template>
        
        <dl class="space-y-4">
          <div>
            <dt class="text-xs font-semibold text-slate-500 uppercase">Buyer</dt>
            <dd class="mt-1 flex items-center text-sm font-medium text-slate-900">
              <UAvatar src="https://i.pravatar.cc/150?u=buyer" size="xs" class="mr-2" />
              Oceanic Transport Corp.
            </dd>
          </div>
          <div class="pt-2 border-t border-slate-100">
            <dt class="text-xs font-semibold text-slate-500 uppercase">Delivery Address</dt>
            <dd class="mt-1 text-sm text-slate-900 flex items-start">
              <UIcon name="i-heroicons-map-pin" class="w-5 h-5 text-slate-400 mr-2 mt-0.5 flex-shrink-0" />
              123 Construction Site Blvd, Mandaue City, Cebu
            </dd>
            <UButton variant="link" color="indigo" size="xs" class="mt-1 ml-5">View on Map</UButton>
          </div>
          <div class="pt-2 border-t border-slate-100">
            <dt class="text-xs font-semibold text-slate-500 uppercase">Promised ETA</dt>
            <dd class="mt-1 text-sm text-slate-900 font-medium text-red-600">Tomorrow, 2:00 PM</dd>
          </div>
          <div class="pt-2 border-t border-slate-100">
            <dt class="text-xs font-semibold text-slate-500 uppercase">Order Summary</dt>
            <dd class="mt-1">
              <div class="flex justify-between text-sm">
                <span class="text-slate-600">500 x Portland Cement</span>
                <span class="font-medium text-slate-900">$2,100.00</span>
              </div>
              <div class="flex justify-between text-sm mt-1">
                <span class="text-slate-600">Delivery</span>
                <span class="font-medium text-slate-900">$50.00</span>
              </div>
            </dd>
          </div>
        </dl>
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
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
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
  </div>
</template>

<script setup lang="ts">
definePageMeta({
  layout: 'supplier'
})

const route = useRoute()
const authStore = useAuthStore()
const config = useRuntimeConfig()
const toast = useToast()
const submittingReview = ref(false)

const ratingOptions = [
  { label: '5 - Excellent', value: 5 },
  { label: '4 - Good', value: 4 },
  { label: '3 - Average', value: 3 },
  { label: '2 - Poor', value: 2 },
  { label: '1 - Bad', value: 1 },
]

const buyerReview = reactive({
  transaction_channel: 'ONLINE',
  buyer_rating: 5,
  communication_rating: 5,
  comment: '',
})

async function submitBuyerReview() {
  submittingReview.value = true
  try {
    await $fetch(`${config.public.apiBase}/orders/${route.params.id}/reviews/buyer`, {
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
</script>
