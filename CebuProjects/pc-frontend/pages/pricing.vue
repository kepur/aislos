<template>
  <div class="bg-white py-24 sm:py-32">
    <div class="mx-auto max-w-7xl px-6 lg:px-8">
      <div class="mx-auto max-w-2xl text-center">
        <h2 class="text-3xl font-bold tracking-tight text-gray-900 sm:text-4xl">Transparent Pricing</h2>
        <p class="mt-4 text-lg leading-8 text-gray-600">No hidden fees. You only pay when you successfully transact.</p>
      </div>
      
      <div class="mx-auto mt-16 grid max-w-lg grid-cols-1 gap-y-6 sm:mt-20 lg:max-w-4xl lg:grid-cols-2 lg:gap-x-8">
        
        <!-- Buyer Pricing -->
        <div class="rounded-3xl p-8 ring-1 ring-gray-200 xl:p-10">
          <div class="flex items-center justify-between gap-x-4">
            <h3 class="text-lg font-semibold leading-8 text-gray-900">For Buyers</h3>
          </div>
          <p class="mt-4 text-sm leading-6 text-gray-600">Free to post requests and connect with suppliers.</p>
          <p class="mt-6 flex items-baseline gap-x-1">
            <span class="text-4xl font-bold tracking-tight text-gray-900">Free</span>
            <span class="text-sm font-semibold leading-6 text-gray-600">/ forever</span>
          </p>
          <ul role="list" class="mt-8 space-y-3 text-sm leading-6 text-gray-600">
            <li class="flex gap-x-3"><UIcon name="i-heroicons-check" class="h-6 w-5 flex-none text-indigo-600" /> Unlimited RFQs</li>
            <li class="flex gap-x-3"><UIcon name="i-heroicons-check" class="h-6 w-5 flex-none text-indigo-600" /> Escrow protection included</li>
            <li class="flex gap-x-3"><UIcon name="i-heroicons-check" class="h-6 w-5 flex-none text-indigo-600" /> Buyer protection policy</li>
          </ul>
          <UButton block color="indigo" variant="outline" class="mt-8" to="/register">Create Buyer Account</UButton>
        </div>
        
        <!-- Supplier Pricing -->
        <div class="rounded-3xl p-8 ring-2 ring-indigo-600 xl:p-10 bg-slate-50">
          <div class="flex items-center justify-between gap-x-4">
            <h3 class="text-lg font-semibold leading-8 text-indigo-600">For Suppliers</h3>
            <UBadge color="indigo" variant="soft" size="sm">Most Popular</UBadge>
          </div>
          <p class="mt-4 text-sm leading-6 text-gray-600">Pay a small success fee only when an order is completed.</p>
          <p class="mt-6 flex items-baseline gap-x-1">
            <span class="text-4xl font-bold tracking-tight text-gray-900">1.5%</span>
            <span class="text-sm font-semibold leading-6 text-gray-600">/ transaction</span>
          </p>
          <ul role="list" class="mt-8 space-y-3 text-sm leading-6 text-gray-600">
            <li class="flex gap-x-3"><UIcon name="i-heroicons-check" class="h-6 w-5 flex-none text-indigo-600" /> No monthly subscription</li>
            <li class="flex gap-x-3"><UIcon name="i-heroicons-check" class="h-6 w-5 flex-none text-indigo-600" /> Guaranteed escrow payouts</li>
            <li class="flex gap-x-3"><UIcon name="i-heroicons-check" class="h-6 w-5 flex-none text-indigo-600" /> Premium matchmaking algorithm</li>
          </ul>
          <UButton block color="indigo" class="mt-8" to="/register">Apply as Supplier</UButton>
        </div>

      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
definePageMeta({ layout: 'default' })
</script>
