<template>
  <section class="space-y-5">
    <div class="flex items-end justify-between gap-4">
      <div><p class="text-xs uppercase tracking-wider text-indigo-400">AinerWise AI solution projects</p><h1 class="mt-1 text-2xl font-bold text-white">Buyer projects</h1></div>
      <button class="btn-primary" @click="createProject">New project</button>
    </div>
    <div class="grid gap-4 md:grid-cols-2">
      <NuxtLink v-for="item in items" :key="item.id" :to="localized(`/market/buyer/projects/${item.id}`)" class="pc-card block hover:border-indigo-400/40">
        <div class="flex justify-between gap-4"><div><h2 class="font-semibold text-white">{{ item.title }}</h2><p class="mt-1 text-xs text-slate-500">{{ item.project_type }}</p></div><span class="text-sm text-slate-400">{{ item.status }}</span></div>
        <p class="mt-3 text-sm text-slate-400">{{ item.description || 'Open the AI project workspace to complete requirements and freeze the BOQ.' }}</p>
      </NuxtLink>
    </div>
    <p v-if="!items.length && !error" class="pc-card text-slate-400">No buyer projects yet.</p>
    <p v-if="error" class="pc-card text-red-300">{{ error }}</p>
  </section>
</template>
<script setup lang="ts">
const { localized } = useLocalizedLink()
definePageMeta({ layout: 'procurement', middleware: ['auth'], alias: ['/buyer/projects'] })
const { apiFetch } = useApi(); const items = ref<any[]>([]); const error = ref('')
async function load(){items.value=(await apiFetch<any>('/buyer/projects')).items}
async function createProject(){const title=window.prompt('Project title');if(!title)return;try{const row=await apiFetch<any>('/buyer/projects',{method:'POST',body:{title}});await navigateTo(`/market/buyer/projects/${row.id}`)}catch(e:any){error.value=e?.data?.detail||e?.message}}
onMounted(()=>load().catch((e:any)=>error.value=e?.data?.detail||e?.message))
</script>
