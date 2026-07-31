<template>
  <div v-if="request" class="space-y-4 p-4">
    <div class="m-card">
      <div class="flex justify-between gap-3">
        <h1 class="text-lg font-bold text-slate-800">{{ request.title }}</h1>
        <span class="status-pill bg-indigo-50 text-indigo-600">{{ request.status }}</span>
      </div>
      <p class="mt-3 text-sm text-slate-500">{{ request.description }}</p>
      <button v-if="request.status === 'draft' || request.status === 'matching'" class="m-btn-primary mt-4" @click="publish">Publish request</button>
    </div>
    <div class="m-card">
      <div class="flex justify-between">
        <h2 class="text-sm font-bold text-slate-800">Offers</h2>
        <NuxtLink :to="`/buyer/compare?request_id=${request.id}`" class="text-xs text-indigo-600">Compare {{ offers.length }}</NuxtLink>
      </div>
      <div v-for="offer in offers" :key="offer.id" class="mt-3 flex justify-between border-t border-slate-100 pt-3 text-xs">
        <span class="text-slate-500">{{ offer.supplier_company_id.slice(0, 8) }}</span>
        <span class="font-semibold text-slate-800">{{ money(offer.price_minor, offer.currency) }}</span>
      </div>
    </div>
    <div class="m-card">
      <div class="flex justify-between">
        <h2 class="text-sm font-bold text-slate-800">Matched listings</h2>
        <button class="text-xs text-indigo-600" @click="loadCandidates">Refresh</button>
      </div>
      <div v-for="item in candidates" :key="item.id" class="mt-3 border-t border-slate-100 pt-3">
        <p class="text-sm font-medium text-slate-700">{{ item.title }}</p>
        <button class="mt-2 text-xs font-semibold text-indigo-600" @click="bind(item.id)">Bind to request</button>
      </div>
    </div>
    <p v-if="error" class="m-card text-sm text-red-600">{{ error }}</p>
  </div>
</template>
<script setup lang="ts">
definePageMeta({ middleware: ['auth'] }); const route = useRoute(); const api = useCommerce(); const id = String(route.params.id); const request = ref<any>(); const offers = ref<any[]>([]); const candidates = ref<any[]>([]); const error = ref(''); const money = (value: number, currency: string) => new Intl.NumberFormat(undefined, { style: 'currency', currency }).format(value / 100); async function load() { request.value = await api.getProcurementRequest(id); offers.value = (await api.listOffers(id)).items } async function loadCandidates() { try { candidates.value = (await api.listCandidates(id)).items } catch (e: any) { error.value = e?.data?.detail || e?.message } } async function publish() { request.value = await api.publishRequest(id); await loadCandidates() } async function bind(listingId: string) { request.value = await api.bindCandidate(id, listingId) } onMounted(async () => { try { await load(); if (request.value.status !== 'draft') await loadCandidates() } catch (e: any) { error.value = e?.data?.detail || e?.message } })
</script>
