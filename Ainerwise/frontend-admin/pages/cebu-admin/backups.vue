<template>
  <div class="space-y-6">
    <div class="flex flex-wrap items-center justify-between gap-3">
      <div><h1 class="admin-page-title">Cebu Backup Operations</h1><p class="admin-page-desc">Real archives, schedules, retention and downloadable job records</p></div>
      <button class="btn-primary" :disabled="running" @click="runManual">{{ running ? 'Running…' : 'Run manual backup' }}</button>
    </div>
    <p v-if="error" class="text-sm text-red-400">{{ error }}</p>
    <form class="admin-panel grid gap-3 p-5 md:grid-cols-4" @submit.prevent="createSchedule">
      <input v-model="form.name" required class="input-field" placeholder="Schedule name"/>
      <select v-model="form.frequency" class="input-field"><option>WEEKLY</option><option>MONTHLY</option><option>CUSTOM</option></select>
      <input v-model.number="form.hour" class="input-field" type="number" min="0" max="23" placeholder="Hour"/>
      <button class="btn-primary">Create schedule</button>
    </form>
    <section>
      <h2 class="mb-3 font-semibold text-white">Schedules</h2>
      <div class="grid gap-3 md:grid-cols-3">
        <article v-for="row in schedules" :key="row.id" class="admin-panel p-4 text-sm">
          <p class="font-semibold text-white">{{ row.name }}</p><p class="text-slate-400">{{ row.frequency }} · {{ row.enabled ? 'enabled' : 'disabled' }}</p><p class="text-xs text-slate-500">Next: {{ row.next_run_at || '-' }}</p>
          <button class="mt-3 text-xs font-semibold text-red-300" @click="removeSchedule(row.id)">Delete</button>
        </article>
      </div>
    </section>
    <section>
      <h2 class="mb-3 font-semibold text-white">Backup jobs</h2>
      <div class="admin-panel overflow-x-auto"><table class="admin-table min-w-full text-sm"><thead><tr><th>Status</th><th>Size</th><th>Started</th><th>Finished</th><th>Archive</th></tr></thead><tbody><tr v-for="row in jobs" :key="row.id"><td><StatusBadge :status="row.status"/></td><td>{{ row.archive_size_bytes || 0 }}</td><td>{{ row.started_at || '-' }}</td><td>{{ row.finished_at || '-' }}</td><td><button class="text-cyan-300" @click="download(row.id)">Download</button></td></tr></tbody></table></div>
    </section>
  </div>
</template>
<script setup lang="ts">
definePageMeta({layout:'default',middleware:['auth']})
const {apiFetch}=useApi();const schedules=ref<any[]>([]);const jobs=ref<any[]>([]);const error=ref('');const running=ref(false);const form=reactive({name:'Scheduled backup',frequency:'WEEKLY',hour:2})
async function load(){const [s,j]=await Promise.all([apiFetch<any>('/admin/cebu/backups/schedules'),apiFetch<any>('/admin/cebu/backups/jobs')]);schedules.value=s.items;jobs.value=j.items}
async function createSchedule(){try{await apiFetch('/admin/cebu/backups/schedules',{method:'POST',body:form});await load()}catch(e:any){error.value=e?.data?.detail||e?.message}}
async function removeSchedule(id:string){try{await apiFetch(`/admin/cebu/backups/schedules/${id}`,{method:'DELETE'});await load()}catch(e:any){error.value=e?.data?.detail||e?.message}}
async function runManual(){running.value=true;try{await apiFetch('/admin/cebu/backups/manual',{method:'POST'});await load()}catch(e:any){error.value=e?.data?.detail||e?.message}finally{running.value=false}}
async function download(id:string){try{const blob=await apiFetch<Blob>(`/admin/cebu/backups/jobs/${id}/download`,{responseType:'blob'});const url=URL.createObjectURL(blob);const link=document.createElement('a');link.href=url;link.download=`ainerwise-backup-${id}.zip`;link.click();URL.revokeObjectURL(url)}catch(e:any){error.value=e?.data?.detail||e?.message}}
onMounted(()=>load().catch((e:any)=>error.value=e?.data?.detail||e?.message))
</script>
