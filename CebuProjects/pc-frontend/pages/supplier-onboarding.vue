<template>
  <div class="bg-indigo-900 py-24 sm:py-32 overflow-hidden relative">
    <div class="absolute inset-0 opacity-10 bg-[url('https://www.transparenttextures.com/patterns/cubes.png')]"></div>
    <div class="mx-auto max-w-7xl px-6 lg:px-8 relative z-10">
      <div class="mx-auto max-w-2xl text-center">
        <h2 class="text-3xl font-bold tracking-tight text-white sm:text-4xl">Grow Your B2B Sales</h2>
        <p class="mt-4 text-lg leading-8 text-indigo-200">Join thousands of verified suppliers winning high-value contracts on ProcurePing.</p>
        <div class="mt-8 flex items-center justify-center gap-x-6">
          <UButton size="xl" color="white" to="/register">Apply as Supplier</UButton>
          <UButton size="xl" color="indigo" variant="ghost" class="text-white" to="/how-it-works">Learn more <span aria-hidden="true">→</span></UButton>
        </div>
      </div>
      
      <div class="mt-20 grid grid-cols-1 md:grid-cols-3 gap-8 text-center text-white">
        <div>
          <UIcon name="i-heroicons-bolt" class="h-10 w-10 mx-auto text-indigo-400 mb-4" />
          <h3 class="font-bold text-xl mb-2">Instant Lead Matching</h3>
          <p class="text-indigo-200 text-sm">Get notified instantly when buyers post requests matching your exact inventory and capabilities.</p>
        </div>
        <div>
          <UIcon name="i-heroicons-shield-check" class="h-10 w-10 mx-auto text-indigo-400 mb-4" />
          <h3 class="font-bold text-xl mb-2">Guaranteed Payments</h3>
          <p class="text-indigo-200 text-sm">Funds are secured in escrow before you ship. Never worry about unpaid invoices again.</p>
        </div>
        <div>
          <UIcon name="i-heroicons-globe-alt" class="h-10 w-10 mx-auto text-indigo-400 mb-4" />
          <h3 class="font-bold text-xl mb-2">Global Reach</h3>
          <p class="text-indigo-200 text-sm">Expand your business to international buyers with built-in multi-currency support.</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
definePageMeta({ layout: 'default' })
</script>
