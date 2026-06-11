<template>
  <div class="min-h-[80vh] flex flex-col items-center justify-center bg-slate-50 py-12 px-4 sm:px-6 lg:px-8">
    <div class="max-w-4xl w-full text-center mb-12">
      <h2 class="text-3xl md:text-4xl font-extrabold text-slate-900 tracking-tight">
        Join {{ $config.public.appName }}
      </h2>
      <p class="mt-4 text-lg text-slate-600 max-w-2xl mx-auto">
        Select how you want to use the platform. Buyers post requests, suppliers compete with offers.
      </p>
    </div>

    <div class="max-w-5xl w-full grid md:grid-cols-3 gap-8">
      <!-- Buyer Card -->
      <div 
        @click="selectRole('buyer')"
        class="bg-white rounded-2xl shadow-lg hover:shadow-xl transition-all p-8 cursor-pointer border-2 border-transparent hover:border-indigo-500 group flex flex-col h-full"
      >
        <div class="w-16 h-16 rounded-full bg-blue-50 text-blue-600 flex items-center justify-center mb-6 group-hover:scale-110 transition-transform">
          <UIcon name="i-heroicons-shopping-bag" class="w-8 h-8" />
        </div>
        <h3 class="text-2xl font-bold text-slate-900 mb-3">I am a Buyer</h3>
        <p class="text-slate-600 mb-8 flex-grow">
          I want to post procurement requests, receive competitive offers from verified suppliers, and pay securely via escrow.
        </p>
        <UButton color="blue" variant="soft" block size="lg" class="group-hover:bg-blue-600 group-hover:text-white transition-colors">
          Register as Buyer
        </UButton>
      </div>

      <!-- Supplier Card -->
      <div 
        @click="selectRole('supplier')"
        class="bg-white rounded-2xl shadow-lg hover:shadow-xl transition-all p-8 cursor-pointer border-2 border-transparent hover:border-indigo-500 group flex flex-col h-full relative overflow-hidden"
      >
        <div class="absolute top-0 right-0 bg-green-500 text-white text-xs font-bold px-3 py-1 rounded-bl-lg">
          GROW SALES
        </div>
        <div class="w-16 h-16 rounded-full bg-green-50 text-green-600 flex items-center justify-center mb-6 group-hover:scale-110 transition-transform">
          <UIcon name="i-heroicons-truck" class="w-8 h-8" />
        </div>
        <h3 class="text-2xl font-bold text-slate-900 mb-3">I am a Supplier</h3>
        <p class="text-slate-600 mb-8 flex-grow">
          I want to receive real-time pings for buyer requests in my area, submit quotes, and get paid securely after delivery.
        </p>
        <UButton color="green" variant="soft" block size="lg" class="group-hover:bg-green-600 group-hover:text-white transition-colors">
          Register as Supplier
        </UButton>
      </div>

      <!-- Staff Card -->
      <div 
        class="bg-slate-50 rounded-2xl p-8 border border-slate-200 flex flex-col h-full opacity-80"
      >
        <div class="w-16 h-16 rounded-full bg-slate-200 text-slate-500 flex items-center justify-center mb-6">
          <UIcon name="i-heroicons-shield-exclamation" class="w-8 h-8" />
        </div>
        <h3 class="text-2xl font-bold text-slate-700 mb-3">Platform Staff</h3>
        <p class="text-slate-500 mb-8 flex-grow">
          Administrative console for managing users, handling disputes, and overseeing platform operations.
        </p>
        <UButton color="gray" variant="solid" block size="lg" disabled>
          Invite Only
        </UButton>
      </div>
    </div>
    
    <div class="mt-12 text-center text-slate-600">
      Already have an account? 
      <NuxtLink to="/login" class="font-medium text-indigo-600 hover:text-indigo-500">
        Log in instead
      </NuxtLink>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'

const router = useRouter()

const selectRole = (role: 'buyer' | 'supplier') => {
  if (role === 'buyer') {
    router.push('/register-buyer')
  } else {
    router.push('/register-supplier')
  }
}
</script>
