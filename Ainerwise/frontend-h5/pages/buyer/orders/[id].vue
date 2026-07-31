<template>
  <div v-if="order" class="space-y-4 p-4">
    <div class="m-card">
      <div class="flex justify-between">
        <h1 class="text-lg font-bold text-slate-800">Order {{ order.id.slice(0, 8) }}</h1>
        <span class="status-pill bg-indigo-50 text-indigo-600">{{ order.status }}</span>
      </div>
      <p class="mt-3 text-2xl font-bold text-slate-800">{{ money(order.total_minor, order.currency) }}</p>
      <button v-if="order.status !== 'completed'" class="m-btn-primary mt-4" @click="complete">Complete order</button>
    </div>
    <div class="m-card">
      <h2 class="text-sm font-bold text-slate-800">Delivery timeline</h2>
      <div v-for="item in deliveries" :key="item.id" class="mt-3 border-t border-slate-100 pt-3">
        <div class="flex justify-between text-xs">
          <span class="text-slate-600">{{ item.tracking_number || item.carrier || 'Delivery' }}</span>
          <span class="text-slate-400">{{ item.status }}</span>
        </div>
        <button v-if="item.status === 'delivered'" class="mt-2 text-xs font-semibold text-indigo-600" @click="accept(item.id)">Accept delivery</button>
      </div>
      <p v-if="!deliveries.length" class="mt-3 text-xs text-slate-400">No delivery scheduled.</p>
    </div>
    <div class="grid grid-cols-2 gap-2">
      <NuxtLink :to="`/messages/${order.id}`" class="m-btn-primary block text-center">Message supplier</NuxtLink>
      <NuxtLink :to="`/buyer/disputes/new?order_id=${order.id}`" class="m-btn block border border-red-100 bg-red-50 text-center text-red-600">Open dispute</NuxtLink>
    </div>
    <p v-if="error" class="m-card text-sm text-red-600">{{ error }}</p>
  </div>
</template>
<script setup lang="ts">
definePageMeta({ middleware: ['auth'] }); const route = useRoute(); const api = useCommerce(); const id = String(route.params.id); const order = ref<any>(); const deliveries = ref<any[]>([]); const error = ref(''); const money = (value: number, currency: string) => new Intl.NumberFormat(undefined, { style: 'currency', currency }).format(value / 100); async function load() { order.value = await api.getOrder(id); deliveries.value = (await api.listDeliveries(id)).items } async function complete() { try { order.value = await api.completeOrder(id) } catch (e: any) { error.value = e?.data?.detail || e?.message } } async function accept(deliveryId: string) { try { await api.acceptDelivery(deliveryId); await load() } catch (e: any) { error.value = e?.data?.detail || e?.message } } onMounted(async () => { try { await load() } catch (e: any) { error.value = e?.data?.detail || e?.message } })
</script>
