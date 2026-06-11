<template>
  <div class="bg-white py-24">
    <div class="mx-auto max-w-7xl px-6 lg:px-8">
      <div class="mx-auto max-w-2xl text-center">
        <h2 class="text-3xl font-bold tracking-tight text-gray-900 sm:text-4xl">Trust & Safety</h2>
        <p class="mt-4 text-lg leading-8 text-gray-600">Our comprehensive approach to securing your B2B transactions.</p>
      </div>

      <div class="mt-16 bg-slate-50 rounded-3xl p-8 md:p-12 border border-slate-100">
        <div class="grid grid-cols-1 md:grid-cols-2 gap-12 items-center">
          <div>
            <h3 class="text-2xl font-bold text-slate-900 mb-4">KYB (Know Your Business) Verification</h3>
            <p class="text-slate-600 mb-6">Every buyer and supplier on ProcurePing undergoes rigorous identity verification, business registration checks, and sanctions screening before they can transact.</p>
            <ul class="space-y-3">
              <li class="flex items-start">
                <UIcon name="i-heroicons-check-circle" class="w-6 h-6 text-green-500 mr-2 shrink-0" />
                <span class="text-slate-700">Corporate Registry Verification</span>
              </li>
              <li class="flex items-start">
                <UIcon name="i-heroicons-check-circle" class="w-6 h-6 text-green-500 mr-2 shrink-0" />
                <span class="text-slate-700">Beneficial Owner Identity Checks</span>
              </li>
              <li class="flex items-start">
                <UIcon name="i-heroicons-check-circle" class="w-6 h-6 text-green-500 mr-2 shrink-0" />
                <span class="text-slate-700">Global Watchlist Screening</span>
              </li>
            </ul>
          </div>
          <div class="bg-white p-8 rounded-2xl shadow-sm border border-slate-200 flex justify-center">
            <UIcon name="i-heroicons-shield-check" class="w-48 h-48 text-indigo-100" />
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
definePageMeta({ layout: 'default' })
</script>
