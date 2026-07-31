<template>
  <div class="space-y-4 px-4 py-4">
    <div><h1 class="text-lg font-bold text-slate-800">Approvals</h1><p class="text-xs text-slate-400">Quotes and delivered orders waiting for you.</p></div>
    <p v-if="message" class="rounded-xl bg-emerald-50 p-3 text-xs text-emerald-700">{{ message }}</p>
    <section class="rounded-2xl border border-slate-100 bg-white p-4 shadow-sm">
      <h2 class="text-sm font-bold text-slate-800">Quotes</h2>
      <div class="mt-3 space-y-3">
        <div v-for="quote in data.quotes || []" :key="quote.id" class="rounded-xl bg-slate-50 p-3">
          <div class="flex justify-between gap-2"><p class="font-bold text-slate-800">{{ quote.currency }} {{ Number(quote.total || 0).toLocaleString() }}</p><StatusBadge :status="quote.status" /></div>
          <div class="mt-3 grid grid-cols-3 gap-2">
            <button class="rounded-lg bg-emerald-600 py-2 text-[11px] font-semibold text-white" @click="respond(quote.id, 'accepted')">Accept</button>
            <button class="rounded-lg bg-red-50 py-2 text-[11px] font-semibold text-red-600" @click="respond(quote.id, 'rejected')">Decline</button>
            <button class="rounded-lg bg-blue-50 py-2 text-[11px] font-semibold text-blue-600" @click="respond(quote.id, 'client_questions')">Questions</button>
          </div>
        </div>
        <p v-if="!(data.quotes || []).length" class="py-4 text-center text-xs text-slate-400">No quote approvals pending.</p>
      </div>
    </section>
    <section class="rounded-2xl border border-slate-100 bg-white p-4 shadow-sm">
      <h2 class="text-sm font-bold text-slate-800">Deliveries</h2>
      <div class="mt-3 space-y-3">
        <div v-for="delivery in data.deliveries || []" :key="delivery.id" class="rounded-xl bg-slate-50 p-3">
          <p class="text-sm font-semibold text-slate-700">{{ delivery.request_title }}</p>
          <p class="mt-1 text-[11px] text-slate-400">{{ delivery.carrier || 'Carrier pending' }} · {{ delivery.tracking_number || 'No tracking' }}</p>
          <button class="mt-3 w-full rounded-lg bg-emerald-600 py-2 text-xs font-semibold text-white" @click="acceptDelivery(delivery.id)">Accept delivery</button>
        </div>
        <p v-if="!(data.deliveries || []).length" class="py-4 text-center text-xs text-slate-400">No delivery acceptance pending.</p>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
definePageMeta({ layout: 'customer-mobile', middleware: 'auth' })
const { apiFetch } = useApi()
const data = ref<any>({ quotes: [], deliveries: [] })
const message = ref('')
async function load() { data.value = await apiFetch('/customer/workspace/approvals') }
async function respond(id: string, status: string) { await apiFetch(`/quotes/${id}/status`, { method: 'PATCH', body: { status } }); message.value = 'Quote response saved.'; await load() }
async function acceptDelivery(id: string) { await apiFetch(`/commerce/deliveries/${id}/status`, { method: 'PATCH', body: { status: 'accepted' } }); message.value = 'Delivery accepted.'; await load() }
onMounted(load)
</script>
