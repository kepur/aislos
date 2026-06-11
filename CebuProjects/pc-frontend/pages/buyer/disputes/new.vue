<template>
  <div class="max-w-3xl mx-auto space-y-6 py-6">
    <div class="flex items-center space-x-4 mb-6">
      <UButton to="/buyer/orders/1" color="gray" variant="ghost" icon="i-heroicons-arrow-left" size="sm" />
      <div>
        <h1 class="text-2xl font-bold text-slate-900">Open a Dispute</h1>
        <p class="text-sm text-slate-500 mt-1">Order #ORD-82910 • 500 bags Portland Cement</p>
      </div>
    </div>

    <div class="bg-red-50 border border-red-200 rounded-xl p-6 mb-8 flex items-start">
      <UIcon name="i-heroicons-exclamation-triangle" class="w-8 h-8 text-red-600 mr-4 flex-shrink-0" />
      <div>
        <h4 class="font-bold text-red-900 mb-1">Escrow Funds Frozen</h4>
        <p class="text-sm text-red-800">By opening a dispute, the $2,150.00 held in escrow will remain frozen. It will not be released to the supplier until this dispute is resolved by our administrative team.</p>
      </div>
    </div>

    <UCard>
      <form class="space-y-6" @submit.prevent="submitDispute">
        <UFormGroup label="Reason for Dispute" required>
          <USelect v-model="form.reason" :options="['Items not delivered', 'Items damaged or defective', 'Incorrect items received', 'Quantity mismatch', 'Other']" size="lg" />
        </UFormGroup>
        
        <UFormGroup label="Requested Resolution" required>
          <div class="grid grid-cols-1 sm:grid-cols-3 gap-4 mt-2">
            <div @click="form.resolution = 'full_refund'" :class="['border rounded-xl p-4 text-center cursor-pointer transition-colors', form.resolution === 'full_refund' ? 'border-red-500 bg-red-50' : 'border-slate-200 hover:border-red-300']">
              <div class="font-bold text-slate-900">Full Refund</div>
              <div class="text-xs text-slate-500 mt-1">Return all items</div>
            </div>
            <div @click="form.resolution = 'partial_refund'" :class="['border rounded-xl p-4 text-center cursor-pointer transition-colors', form.resolution === 'partial_refund' ? 'border-orange-500 bg-orange-50' : 'border-slate-200 hover:border-orange-300']">
              <div class="font-bold text-slate-900">Partial Refund</div>
              <div class="text-xs text-slate-500 mt-1">Keep some items</div>
            </div>
            <div @click="form.resolution = 'replacement'" :class="['border rounded-xl p-4 text-center cursor-pointer transition-colors', form.resolution === 'replacement' ? 'border-blue-500 bg-blue-50' : 'border-slate-200 hover:border-blue-300']">
              <div class="font-bold text-slate-900">Replacement</div>
              <div class="text-xs text-slate-500 mt-1">Exchange items</div>
            </div>
          </div>
        </UFormGroup>
        
        <UFormGroup label="Refund Amount Requested" v-if="form.resolution === 'partial_refund'" required>
          <div class="relative">
                  <span class="absolute inset-y-0 left-3 flex items-center text-slate-400 text-sm pointer-events-none">$</span>
                  <input v-model="form.amount" type="number" placeholder="" min="0"
                    class="w-full rounded-lg border border-slate-200 bg-white pl-7 pr-4 py-3 text-sm text-slate-800 shadow-sm focus:border-indigo-400 focus:outline-none focus:ring-2 focus:ring-indigo-200" />
                </div>
          <p class="text-xs text-slate-500 mt-1">Max: $2,150.00</p>
        </UFormGroup>

        <UFormGroup label="Detailed Explanation" required>
          <UTextarea v-model="form.details" :rows="5" placeholder="Please describe exactly what went wrong..." />
        </UFormGroup>
        
        <UFormGroup label="Evidence (Photos/Documents)" required>
          <div class="border-2 border-dashed border-slate-300 rounded-lg p-8 text-center hover:bg-slate-50 cursor-pointer">
            <UIcon name="i-heroicons-camera" class="w-10 h-10 text-slate-400 mx-auto mb-2" />
            <p class="text-sm font-medium text-slate-700">Click to upload photos of the issue</p>
            <p class="text-xs text-slate-500 mt-1">Required for damaged or incorrect item claims.</p>
          </div>
        </UFormGroup>

        <div class="pt-4 border-t border-slate-200 flex justify-end space-x-4">
          <UButton color="gray" variant="ghost" size="lg" to="/buyer/disputes">Cancel</UButton>
          <UButton type="submit" color="red" size="lg" class="px-8 font-bold">Submit Dispute</UButton>
        </div>
      </form>
    </UCard>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'

definePageMeta({
  layout: 'buyer'
})

const router = useRouter()
const form = ref({
  reason: '',
  resolution: 'full_refund',
  amount: null,
  details: ''
})

const submitDispute = () => {
  if(confirm('Are you sure you want to open this dispute? Escrow funds will be frozen.')) {
    alert('Dispute opened. Our admin team will review this shortly.')
    router.push('/buyer/dashboard')
  }
}
</script>
