<template>
  <div class="space-y-6">
    <h1 class="admin-page-title">Cebu Trade Operations</h1>
    <div class="grid gap-3 md:grid-cols-4">
      <NuxtLink v-for="item in sections" :key="item.to" :to="item.to" class="admin-panel p-4 font-semibold text-cyan-300">{{ item.label }}</NuxtLink>
    </div>
  </div>
</template>
<script setup lang="ts">definePageMeta({layout:'default',middleware:['auth']});const sections=[{to:'/cebu-admin/shipping',label:'Shipping'},{to:'/cebu-admin/ad-campaigns',label:'Ad Campaigns'},{to:'/cebu-admin/marketplace',label:'Marketplace'},{to:'/cebu-admin/trust',label:'Trust'},{to:'/cebu-admin/escrow',label:'Escrow'},{to:'/cebu-admin/payouts',label:'Payouts'},{to:'/cebu-admin/deposits',label:'Deposits'},{to:'/cebu-admin/verification',label:'KYC Verification'},{to:'/cebu-admin/kyc-media',label:'KYC Media'},{to:'/cebu-admin/payments',label:'Payments'},{to:'/cebu-admin/notifications',label:'Notifications'},{to:'/cebu-admin/backups',label:'Backups'}]</script>
