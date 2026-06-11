<template>
  <div class="bg-white">
    <div class="py-24 sm:py-32">
      <div class="mx-auto max-w-7xl px-6 lg:px-8">
        <div class="mx-auto max-w-2xl lg:text-center">
          <h2 class="text-base font-semibold leading-7 text-indigo-600">ProcurePing</h2>
          <p class="mt-2 text-3xl font-bold tracking-tight text-gray-900 sm:text-4xl">How It Works</p>
          <p class="mt-6 text-lg leading-8 text-gray-600">The modern B2B marketplace connecting verified buyers with trusted suppliers through a secure escrow platform.</p>
        </div>
        
        <div class="mx-auto mt-16 max-w-2xl sm:mt-20 lg:mt-24 lg:max-w-4xl">
          <dl class="grid max-w-xl grid-cols-1 gap-x-8 gap-y-10 lg:max-w-none lg:grid-cols-2 lg:gap-y-16">
            <div class="relative pl-16">
              <dt class="text-base font-semibold leading-7 text-gray-900">
                <div class="absolute left-0 top-0 flex h-10 w-10 items-center justify-center rounded-lg bg-indigo-600">
                  <UIcon name="i-heroicons-document-plus" class="h-6 w-6 text-white" />
                </div>
                1. Post a Request
              </dt>
              <dd class="mt-2 text-base leading-7 text-gray-600">Buyers submit their detailed requirements, including specifications, quantities, and delivery timelines.</dd>
            </div>
            
            <div class="relative pl-16">
              <dt class="text-base font-semibold leading-7 text-gray-900">
                <div class="absolute left-0 top-0 flex h-10 w-10 items-center justify-center rounded-lg bg-indigo-600">
                  <UIcon name="i-heroicons-bolt" class="h-6 w-6 text-white" />
                </div>
                2. Receive Offers
              </dt>
              <dd class="mt-2 text-base leading-7 text-gray-600">Verified suppliers in matching categories are notified instantly and submit competitive quotes.</dd>
            </div>

            <div class="relative pl-16">
              <dt class="text-base font-semibold leading-7 text-gray-900">
                <div class="absolute left-0 top-0 flex h-10 w-10 items-center justify-center rounded-lg bg-indigo-600">
                  <UIcon name="i-heroicons-shield-check" class="h-6 w-6 text-white" />
                </div>
                3. Secure Escrow
              </dt>
              <dd class="mt-2 text-base leading-7 text-gray-600">The buyer selects an offer and funds the order via escrow, protecting both parties until delivery.</dd>
            </div>

            <div class="relative pl-16">
              <dt class="text-base font-semibold leading-7 text-gray-900">
                <div class="absolute left-0 top-0 flex h-10 w-10 items-center justify-center rounded-lg bg-indigo-600">
                  <UIcon name="i-heroicons-truck" class="h-6 w-6 text-white" />
                </div>
                4. Delivery & Payout
              </dt>
              <dd class="mt-2 text-base leading-7 text-gray-600">Upon successful delivery and buyer confirmation, funds are automatically released to the supplier.</dd>
            </div>
          </dl>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
definePageMeta({ layout: 'default' })
</script>
