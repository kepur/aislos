<template>
  <div class="max-w-3xl mx-auto space-y-6 py-6">
    <div class="flex items-center space-x-4 mb-6">
      <UButton :to="orderId ? `/buyer/orders/${orderId}` : '/buyer/orders'" color="gray" variant="ghost" icon="i-heroicons-arrow-left" size="sm" />
      <div>
        <h1 class="text-2xl font-bold text-slate-900">{{ appStore.t('buyer.disputes.openTitle') }}</h1>
        <p class="text-sm text-slate-500 mt-1">
          {{ orderId ? `${appStore.t('buyer.disputes.colOrder')} #${orderId.slice(0, 8).toUpperCase()}` : appStore.t('buyer.disputes.selectOrder') }}
        </p>
      </div>
    </div>

    <div class="bg-red-50 border border-red-200 rounded-xl p-6 mb-8 flex items-start">
      <UIcon name="i-heroicons-exclamation-triangle" class="w-8 h-8 text-red-600 mr-4 flex-shrink-0" />
      <div>
        <h4 class="font-bold text-red-900 mb-1">{{ appStore.t('buyer.disputes.frozenTitle') }}</h4>
        <p class="text-sm text-red-800">{{ appStore.t('buyer.disputes.frozenDesc') }}</p>
      </div>
    </div>

    <UCard>
      <form class="space-y-6" @submit.prevent="submitDispute">
        <UFormGroup :label="appStore.t('buyer.disputes.reasonLabel')" required>
          <USelect v-model="form.reason" :options="reasonOptions" size="lg" />
        </UFormGroup>

        <UFormGroup :label="appStore.t('buyer.disputes.resolutionLabel')" required>
          <div class="grid grid-cols-1 sm:grid-cols-3 gap-4 mt-2">
            <div @click="form.resolution = 'full_refund'" :class="['border rounded-xl p-4 text-center cursor-pointer transition-colors', form.resolution === 'full_refund' ? 'border-red-500 bg-red-50' : 'border-slate-200 hover:border-red-300']">
              <div class="font-bold text-slate-900">{{ appStore.t('buyer.disputes.fullRefund') }}</div>
              <div class="text-xs text-slate-500 mt-1">{{ appStore.t('buyer.disputes.fullRefundHint') }}</div>
            </div>
            <div @click="form.resolution = 'partial_refund'" :class="['border rounded-xl p-4 text-center cursor-pointer transition-colors', form.resolution === 'partial_refund' ? 'border-orange-500 bg-orange-50' : 'border-slate-200 hover:border-orange-300']">
              <div class="font-bold text-slate-900">{{ appStore.t('buyer.disputes.partialRefund') }}</div>
              <div class="text-xs text-slate-500 mt-1">{{ appStore.t('buyer.disputes.partialRefundHint') }}</div>
            </div>
            <div @click="form.resolution = 'replacement'" :class="['border rounded-xl p-4 text-center cursor-pointer transition-colors', form.resolution === 'replacement' ? 'border-blue-500 bg-blue-50' : 'border-slate-200 hover:border-blue-300']">
              <div class="font-bold text-slate-900">{{ appStore.t('buyer.disputes.replacement') }}</div>
              <div class="text-xs text-slate-500 mt-1">{{ appStore.t('buyer.disputes.replacementHint') }}</div>
            </div>
          </div>
        </UFormGroup>

        <UFormGroup :label="appStore.t('buyer.disputes.refundAmount')" v-if="form.resolution === 'partial_refund'" required>
          <div class="relative">
                  <span class="absolute inset-y-0 left-3 flex items-center text-slate-400 text-sm pointer-events-none">$</span>
                  <input v-model="form.amount" type="number" placeholder="" min="0"
                    class="w-full rounded-lg border border-slate-200 bg-white pl-7 pr-4 py-3 text-sm text-slate-800 shadow-sm focus:border-indigo-400 focus:outline-none focus:ring-2 focus:ring-indigo-200" />
                </div>
          <p class="text-xs text-slate-500 mt-1">Max: $2,150.00</p>
        </UFormGroup>

        <UFormGroup :label="appStore.t('buyer.disputes.detailsLabel')" required>
          <UTextarea v-model="form.details" :rows="5" :placeholder="appStore.t('buyer.disputes.detailsPh')" />
        </UFormGroup>

        <UFormGroup :label="appStore.t('buyer.disputes.evidenceLabel')" required>
          <div class="border-2 border-dashed border-slate-300 rounded-lg p-8 text-center hover:bg-slate-50 cursor-pointer">
            <UIcon name="i-heroicons-camera" class="w-10 h-10 text-slate-400 mx-auto mb-2" />
            <p class="text-sm font-medium text-slate-700">{{ appStore.t('buyer.disputes.evidenceHint') }}</p>
            <p class="text-xs text-slate-500 mt-1">{{ appStore.t('buyer.disputes.evidenceRequired') }}</p>
          </div>
        </UFormGroup>

        <div class="pt-4 border-t border-slate-200 flex justify-end space-x-4">
          <UButton color="gray" variant="ghost" size="lg" to="/buyer/disputes">{{ appStore.t('buyer.disputes.cancel') }}</UButton>
          <UButton type="submit" color="red" size="lg" class="px-8 font-bold" :loading="submitting" :disabled="!orderId">
            {{ appStore.t('buyer.disputes.submit') }}
          </UButton>
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

const appStore = useAppStore()
const router = useRouter()
const route = useRoute()
const { openDispute } = useApi()
const orderId = computed(() => String(route.query.order_id || ''))
const submitting = ref(false)
const reasonOptions = [
  'ITEM_NOT_RECEIVED',
  'ITEM_DAMAGED',
  'ITEM_WRONG',
  'QUANTITY_MISMATCH',
  'QUALITY_ISSUE',
  'DELIVERY_DELAY',
  'OTHER'
]
const form = ref({
  reason: '',
  resolution: 'full_refund',
  amount: null,
  details: ''
})

const submitDispute = async () => {
  if (!orderId.value) {
    alert(appStore.t('buyer.disputes.missingOrder'))
    return
  }
  if (!confirm(appStore.t('buyer.disputes.confirmOpen'))) return
  submitting.value = true
  const amount = form.value.amount ? Math.round(Number(form.value.amount) * 100) : null
  const { error } = await openDispute(orderId.value, {
    reason: form.value.reason,
    reason_code: form.value.reason,
    description: form.value.details,
    requested_resolution: form.value.resolution,
    refund_amount_minor: amount,
    evidence: [],
  })
  submitting.value = false
  if (error) {
    alert(error.detail || error.message || appStore.t('buyer.disputes.openFailed'))
  } else {
    alert(appStore.t('buyer.disputes.openSuccess'))
    router.push('/buyer/disputes')
  }
}
</script>
