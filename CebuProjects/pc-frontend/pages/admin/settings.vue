<template>
  <div class="max-w-4xl mx-auto space-y-6">
    <div>
      <h1 class="text-2xl font-bold text-slate-900">Platform Settings</h1>
      <p class="text-slate-500 mt-1">Global configurations for the marketplace.</p>
    </div>

    <UCard>
      <template #header>
        <h3 class="text-lg font-medium text-slate-900">Escrow & Fees</h3>
      </template>
      
      <div class="space-y-4">
        <div class="flex justify-between items-center py-2 border-b border-slate-100">
          <div>
            <p class="font-medium text-slate-900">Standard Buyer Fee (%)</p>
            <p class="text-sm text-slate-500">Applied to order total</p>
          </div>
          <UInput type="number" model-value="2.5" class="w-24" />
        </div>
        
        <div class="flex justify-between items-center py-2 border-b border-slate-100">
          <div>
            <p class="font-medium text-slate-900">Standard Supplier Fee (%)</p>
            <p class="text-sm text-slate-500">Deducted from final payout</p>
          </div>
          <UInput type="number" model-value="1.5" class="w-24" />
        </div>

        <div class="flex justify-between items-center py-2">
          <div>
            <p class="font-medium text-slate-900">Escrow Lock Period (Days)</p>
            <p class="text-sm text-slate-500">Auto-release after delivery confirmation</p>
          </div>
          <UInput type="number" model-value="14" class="w-24" />
        </div>
      </div>
      
      <div class="flex justify-end mt-6">
        <UButton color="indigo">Update Platform Configuration</UButton>
      </div>
    </UCard>
  </div>
</template>

<script setup lang="ts">
definePageMeta({ layout: 'admin' })
</script>
