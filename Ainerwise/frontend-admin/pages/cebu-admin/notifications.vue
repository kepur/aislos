<template>
  <div class="space-y-5">
    <div class="flex flex-wrap items-center justify-between gap-3"><div><h1 class="admin-page-title">Cebu Notifications</h1><p class="admin-page-desc">Real notification inbox and delivery smoke test</p></div><div class="flex gap-2"><NuxtLink class="btn-secondary" to="/cebu-admin/settings">Manage templates</NuxtLink><button class="btn-primary" @click="test">Send test notification</button></div></div>
    <p v-if="error" class="text-sm text-red-400">{{ error }}</p>
    <div class="admin-panel overflow-x-auto"><table class="admin-table min-w-full text-sm"><thead><tr><th>Event</th><th>Title</th><th>Portal</th><th>Status</th><th>Created</th></tr></thead><tbody><tr v-for="row in items" :key="row.id"><td>{{ row.event_type }}</td><td>{{ row.title }}</td><td>{{ row.portal_key }}</td><td><StatusBadge :status="row.status"/></td><td>{{ row.created_at }}</td></tr></tbody></table></div>
  </div>
</template>
<script setup lang="ts">
definePageMeta({layout:'default',middleware:['auth']})
const {apiFetch}=useApi();const items=ref<any[]>([]);const error=ref('')
async function load(){items.value=(await apiFetch<any>('/admin/cebu/notifications')).items}
async function test(){const title=window.prompt('Notification title','Cebu Admin delivery test');if(!title)return;try{await apiFetch('/admin/cebu/notifications/test',{method:'POST',body:{title,body:'Generated from the Cebu Admin operations console.'}});await load()}catch(e:any){error.value=e?.data?.detail||e?.message}}
onMounted(()=>load().catch((e:any)=>error.value=e?.data?.detail||e?.message))
</script>
