<template>
  <div class="space-y-6">
    <div><h1 class="admin-page-title">Cebu Shipping</h1><p class="admin-page-desc">Manage real shipping routes and weight-based rates</p></div>
    <p v-if="error" class="text-sm text-red-400">{{ error }}</p>
    <form class="admin-panel grid gap-3 p-4 md:grid-cols-5" @submit.prevent="createRoute">
      <input v-model="routeForm.origin_country" required class="input-field" placeholder="Origin country"/>
      <input v-model="routeForm.dest_country" required class="input-field" placeholder="Destination country"/>
      <input v-model="routeForm.shipping_method" required class="input-field" placeholder="Method"/>
      <input v-model="routeForm.description" class="input-field" placeholder="Description"/>
      <button class="btn-primary">Create route</button>
    </form>
    <section class="grid gap-3 md:grid-cols-2">
      <article v-for="row in routes" :key="row.id" class="admin-panel p-4 text-sm">
        <div class="flex justify-between gap-3"><p class="font-semibold text-white">{{ row.origin_country }} → {{ row.dest_country }}</p><StatusBadge :status="row.status"/></div>
        <p class="mt-2 text-slate-400">{{ row.shipping_method }} · {{ row.description || '-' }}</p>
        <div class="mt-4 flex gap-2">
          <button class="btn-secondary" @click="selectedRoute=row.id">Add rate</button>
          <button v-if="row.status==='ACTIVE'" class="btn-secondary" @click="deactivate('routes',row.id)">Deactivate</button>
        </div>
      </article>
    </section>
    <form v-if="selectedRoute" class="admin-panel grid gap-3 p-4 md:grid-cols-5" @submit.prevent="createRate">
      <input v-model.number="rateForm.weight_min_kg" class="input-field" type="number" min="0" step="0.1" placeholder="Min kg"/>
      <input v-model.number="rateForm.weight_max_kg" class="input-field" type="number" min="0" step="0.1" placeholder="Max kg"/>
      <input v-model.number="rateForm.price_per_kg_minor" required class="input-field" type="number" min="1" placeholder="Price/kg minor"/>
      <input v-model="rateForm.currency" required class="input-field" placeholder="Currency"/>
      <button class="btn-primary">Create rate</button>
    </form>
    <div class="admin-panel overflow-x-auto"><table class="admin-table min-w-full text-sm"><thead><tr><th>Route</th><th>Weight</th><th>Price/kg</th><th>Currency</th><th>Status</th><th>Action</th></tr></thead><tbody><tr v-for="row in rates" :key="row.id"><td>{{ row.route_id }}</td><td>{{ row.weight_min_kg }}–{{ row.weight_max_kg }}</td><td>{{ row.price_per_kg_minor }}</td><td>{{ row.currency }}</td><td><StatusBadge :status="row.status"/></td><td><button v-if="row.status==='ACTIVE'" class="text-red-300" @click="deactivate('rates',row.id)">Deactivate</button></td></tr></tbody></table></div>
  </div>
</template>
<script setup lang="ts">
definePageMeta({layout:'default',middleware:['auth']})
const {apiFetch}=useApi();const routes=ref<any[]>([]);const rates=ref<any[]>([]);const error=ref('');const selectedRoute=ref('');const routeForm=reactive({origin_country:'PH',dest_country:'PH',shipping_method:'ROAD',description:''});const rateForm=reactive({weight_min_kg:0,weight_max_kg:99999,price_per_kg_minor:100,currency:'PHP'})
async function load(){const [r,rr]=await Promise.all([apiFetch<any>('/admin/cebu-trade/shipping/routes'),apiFetch<any>('/admin/cebu-trade/shipping/rates')]);routes.value=r.items;rates.value=rr.items}
async function createRoute(){try{const row=await apiFetch<any>('/admin/cebu-trade/shipping/routes',{method:'POST',body:routeForm});selectedRoute.value=row.id;await load()}catch(e:any){error.value=e?.data?.detail||e?.message}}
async function createRate(){try{await apiFetch('/admin/cebu-trade/shipping/rates',{method:'POST',body:{...rateForm,route_id:selectedRoute.value,valid_from:new Date().toISOString().slice(0,10)}});await load()}catch(e:any){error.value=e?.data?.detail||e?.message}}
async function deactivate(kind:string,id:string){try{await apiFetch(`/admin/cebu-trade/shipping/${kind}/${id}`,{method:'DELETE'});await load()}catch(e:any){error.value=e?.data?.detail||e?.message}}
onMounted(()=>load().catch((e:any)=>error.value=e?.data?.detail||e?.message))
</script>
