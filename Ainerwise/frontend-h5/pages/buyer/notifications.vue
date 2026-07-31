<template>
  <div class="space-y-3 p-4">
    <div class="flex justify-between">
      <h1 class="text-xl font-bold text-slate-800">Notifications</h1>
      <button class="text-xs font-semibold text-indigo-600" @click="readAll">Mark all read</button>
    </div>
    <button
      v-for="item in items"
      :key="item.id"
      class="m-card block w-full text-left"
      @click="read(item)"
    >
      <p class="text-sm font-semibold text-slate-800">{{ item.title }}</p>
      <p class="mt-1 text-xs text-slate-400">{{ item.body }}</p>
    </button>
    <p v-if="error" class="m-card text-sm text-red-600">{{ error }}</p>
  </div>
</template>
<script setup lang="ts">definePageMeta({ middleware: ['auth'] }); const api = useCommerce(); const items = ref<any[]>([]); const error = ref(''); async function load() { items.value = (await api.listNotifications()).items } async function read(item: any) { if (item.status === 'unread') await api.markRead(item.id); if (item.link_path) await navigateTo(item.link_path.replace('/commerce/orders/', '/buyer/orders/')) } async function readAll() { await api.markAllRead(); await load() } onMounted(async () => { try { await load() } catch (e: any) { error.value = e?.data?.detail || e?.message } })</script>
