<template>
  <div class="space-y-6">
    <div class="flex items-center space-x-4 mb-2">
      <UButton to="/buyer/requests/1/offers" color="gray" variant="ghost" icon="i-heroicons-arrow-left" size="sm" />
      <div>
        <h1 class="text-2xl font-bold text-slate-900">Offer from Cebu Builders Hub</h1>
        <p class="text-sm text-slate-500 mt-1">For Request: 500 bags Portland Cement</p>
      </div>
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
      <div class="lg:col-span-2 space-y-6">
        <!-- Quote Details -->
        <UCard>
          <template #header>
            <h3 class="text-lg font-medium text-slate-900">Quote Breakdown</h3>
          </template>
          
          <div class="space-y-4">
            <div class="flex justify-between items-center py-2 border-b border-slate-100">
              <span class="text-slate-600">Unit Price (500 bags)</span>
              <span class="font-medium text-slate-900">$4.20</span>
            </div>
            <div class="flex justify-between items-center py-2 border-b border-slate-100">
              <span class="text-slate-600">Subtotal</span>
              <span class="font-medium text-slate-900">$2,100.00</span>
            </div>
            <div class="flex justify-between items-center py-2 border-b border-slate-100">
              <span class="text-slate-600">Delivery Fee</span>
              <span class="font-medium text-slate-900">$50.00</span>
            </div>
            <div class="flex justify-between items-center py-3 bg-indigo-50 px-4 rounded-lg border border-indigo-100">
              <span class="font-bold text-indigo-900">Total Landed Cost</span>
              <span class="text-xl font-bold text-indigo-700">$2,150.00</span>
            </div>
          </div>
          
          <div class="mt-6 pt-6 border-t border-slate-200">
            <h4 class="text-sm font-semibold text-slate-900 mb-2">Supplier Notes</h4>
            <p class="text-sm text-slate-600 bg-slate-50 p-4 rounded-md border border-slate-200 italic">
              "We have Republic Cement in stock. Can deliver by tomorrow 2PM via our flatbed truck. Price includes unloading at the site."
            </p>
          </div>
        </UCard>

        <!-- Terms -->
        <UCard>
          <template #header>
            <h3 class="text-lg font-medium text-slate-900">Terms & Logistics</h3>
          </template>
          <dl class="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <dt class="text-xs font-semibold text-slate-500 uppercase">Estimated Arrival</dt>
              <dd class="mt-1 text-sm font-medium text-slate-900">Tomorrow, 2PM</dd>
            </div>
            <div>
              <dt class="text-xs font-semibold text-slate-500 uppercase">Stock Status</dt>
              <dd class="mt-1"><UBadge color="green" variant="subtle">High Confidence</UBadge></dd>
            </div>
            <div>
              <dt class="text-xs font-semibold text-slate-500 uppercase">Warranty</dt>
              <dd class="mt-1 text-sm text-slate-900">Return if defective</dd>
            </div>
            <div>
              <dt class="text-xs font-semibold text-slate-500 uppercase">Valid Until</dt>
              <dd class="mt-1 text-sm text-slate-900">Oct 26, 5:00 PM</dd>
            </div>
          </dl>
        </UCard>
      </div>

      <!-- Supplier Profile & Actions -->
      <div class="space-y-6">
        <UCard>
          <div class="text-center">
            <UAvatar src="https://i.pravatar.cc/150?u=1" size="3xl" class="mx-auto" />
            <h3 class="mt-4 text-lg font-bold text-slate-900 flex justify-center items-center">
              Cebu Builders Hub
              <UIcon name="i-heroicons-shield-check" class="w-5 h-5 text-green-500 ml-1" />
            </h3>
            <div class="flex justify-center items-center text-sm text-slate-500 mt-1">
              <UIcon name="i-heroicons-star" class="w-4 h-4 text-yellow-400 mr-1" />
              <span class="font-medium mr-1 text-slate-700">4.9</span> (124 reviews)
            </div>
            <div class="text-sm text-slate-500 mt-1">4.2 km away</div>
          </div>
          
          <div class="mt-6 space-y-3">
            <UButton block color="indigo" variant="solid" size="xl" class="font-bold shadow-md" @click="award">
              Award Order
            </UButton>
            <UButton block color="gray" variant="outline" icon="i-heroicons-chat-bubble-left">
              Message Supplier
            </UButton>
          </div>
        </UCard>
        
        <div class="bg-blue-50 border border-blue-100 rounded-lg p-4 flex items-start">
          <UIcon name="i-heroicons-shield-check" class="w-6 h-6 text-blue-600 mr-3 flex-shrink-0" />
          <div>
            <h4 class="text-sm font-bold text-blue-900">Escrow Protection</h4>
            <p class="text-xs text-blue-800 mt-1">If you award this offer, $2,150.00 will be held safely in escrow until you confirm delivery.</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'

definePageMeta({
  layout: 'buyer'
})

const router = useRouter()

const award = () => {
  if(confirm('Award this offer for $2,150.00?')) {
    alert('Offer awarded! Funds moved to active escrow.')
    router.push('/buyer/orders/1')
  }
}
</script>
