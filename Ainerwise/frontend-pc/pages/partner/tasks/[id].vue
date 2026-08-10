<template>
  <section class="space-y-5">
    <NuxtLink :to="localized('/partner/tasks')" class="text-sm text-blue-300">&larr; Back to tasks</NuxtLink>
    <p v-if="error" class="pc-card text-red-300">{{ error }}</p>
    <template v-if="task">
      <div class="pc-card"><div class="flex flex-wrap justify-between gap-4"><div><p class="text-xs uppercase tracking-wider text-blue-300">Dispatched work</p><h1 class="mt-2 text-3xl font-bold capitalize text-white">{{ label(task.task_type||'service task') }}</h1><p class="mt-2 text-sm text-slate-400">{{ task.project_title||task.device_name||'Project pending' }}</p></div><span class="h-fit rounded-full bg-blue-500/10 px-3 py-1 text-xs uppercase text-blue-300">{{ label(task.status) }}</span></div><dl class="mt-5 grid gap-4 text-sm sm:grid-cols-3"><div><dt class="text-slate-500">Region</dt><dd class="mt-1 text-white">{{ task.project_region||'Not set' }}</dd></div><div><dt class="text-slate-500">Due</dt><dd class="mt-1 text-white">{{ task.due_date||'Not set' }}</dd></div><div><dt class="text-slate-500">Work area</dt><dd class="mt-1 text-white">{{ task.device_name||'Not set' }}</dd></div></dl></div>
      <button v-if="['scheduled','due'].includes(task.status)" class="btn-primary" :disabled="saving" @click="changeStatus('in_progress')">Start task</button>
      <div v-if="task.status!=='done'&&task.status!=='completed_pending_acceptance'" class="pc-card space-y-4">
        <h2 class="font-semibold text-white">Submit completion evidence</h2>
        <input type="file" multiple accept="image/*" class="input-field" @change="onFiles">
        <p class="text-xs text-slate-500">{{ photos.length }} uploaded photos</p>
        <textarea v-model="notes" rows="5" class="input-field" placeholder="Completion notes and test results"/>
        <button class="btn-primary" :disabled="saving||uploading" @click="complete">Send for customer acceptance</button>
      </div>
      <div v-if="signingUrl" class="pc-card border-emerald-400/30"><p class="font-semibold text-emerald-300">Customer acceptance created</p><p class="mt-2 break-all text-sm text-slate-300">{{ signingUrl }}</p></div>
    </template>
  </section>
</template>
<script setup lang="ts">
const { localized } = useLocalizedLink()
definePageMeta({layout:'partner-workspace',middleware:['auth']});const route=useRoute();const {apiFetch}=useApi();const task=ref<any>();const error=ref('');const saving=ref(false);const uploading=ref(false);const photos=ref<string[]>([]);const notes=ref('');const signingUrl=ref('');const label=(v:string)=>v?.replaceAll('_',' ')||'unknown';async function load(){task.value=await apiFetch(`/partner/tasks/${route.params.id}`)}async function changeStatus(status:string){saving.value=true;try{task.value=await apiFetch(`/partner/tasks/${route.params.id}/status`,{method:'PATCH',body:{status}})}catch(e:any){error.value=e?.data?.detail||e?.message}finally{saving.value=false}}async function onFiles(event:Event){const files=(event.target as HTMLInputElement).files;if(!files?.length)return;uploading.value=true;try{for(const file of Array.from(files)){const p=await apiFetch<any>(`/files/upload-url?filename=${encodeURIComponent(file.name)}&content_type=${encodeURIComponent(file.type||'image/jpeg')}`,{method:'POST'});await $fetch(p.upload_url,{method:'PUT',body:file});photos.value.push(p.object_name)}}catch(e:any){error.value=e?.data?.detail||e?.message}finally{uploading.value=false}}async function complete(){saving.value=true;try{const r=await apiFetch<any>(`/partner/tasks/${route.params.id}/complete`,{method:'POST',body:{notes:notes.value||null,photos:photos.value,devices:[]}});signingUrl.value=r.customer_signing_url;await load()}catch(e:any){error.value=e?.data?.detail||e?.message}finally{saving.value=false}}onMounted(()=>load().catch((e:any)=>error.value=e?.data?.detail||e?.message))
</script>
