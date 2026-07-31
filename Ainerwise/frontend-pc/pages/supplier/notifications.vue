<template>
  <section class="space-y-5">
    <div class="flex justify-between">
      <h1 class="text-2xl font-bold text-white">通知</h1>
      <button class="text-primary-300" @click="readAll">全部已读</button>
    </div>
    <button
      v-for="item in items"
      :key="item.id"
      class="pc-card block w-full text-left"
      @click="read(item)"
    >
      <p class="font-semibold text-white">{{ item.title }}</p>
      <p class="text-sm text-slate-400">{{ item.body }}</p>
      <p class="text-xs text-slate-500">{{ item.status }}</p>
    </button>
  </section>
</template>
<script setup lang="ts">definePageMeta({layout:'procurement',middleware:['auth']});const api=useCommerce();const items=ref<any[]>([]);async function load(){items.value=(await api.listNotifications()).items}async function read(x:any){if(x.status==='unread')await api.markRead(x.id);await load()}async function readAll(){await api.markAllRead();await load()}onMounted(load)</script>
