<template>
  <div class="space-y-6">
    <div>
      <h1 class="admin-page-title">Cebu Coverage Operations</h1>
      <p class="admin-page-desc">Manage supplier branches and service coverage used for matching and delivery.</p>
    </div>
    <p v-if="error" class="text-sm text-red-400">{{ error }}</p>

    <section class="admin-panel p-5">
      <h2 class="mb-4 font-semibold text-white">Create company branch</h2>
      <form class="grid gap-3 md:grid-cols-4" @submit.prevent="createBranch">
        <input v-model.trim="branchForm.company_id" required class="input-field" placeholder="Company UUID" />
        <input v-model.trim="branchForm.name" required class="input-field" placeholder="Branch name" />
        <input v-model.trim="branchForm.country" required class="input-field" placeholder="Country" />
        <input v-model.trim="branchForm.city" required class="input-field" placeholder="City" />
        <input v-model.number="branchForm.radius_km" required type="number" min="1" max="500" class="input-field" placeholder="Radius km" />
        <input v-model.trim="branchMethods" class="input-field md:col-span-2" placeholder="Delivery methods, comma separated" />
        <button class="btn-primary">Create branch</button>
      </form>
      <div class="mt-5 grid gap-3 md:grid-cols-2">
        <article v-for="row in branches" :key="row.id" class="rounded-lg border border-white/5 bg-slate-950/30 p-4 text-sm">
          <div class="flex justify-between gap-3"><p class="font-medium text-white">{{ row.name }}</p><StatusBadge :status="row.status" /></div>
          <p class="mt-2 text-slate-400">{{ row.city }}, {{ row.country }} · {{ row.radius_km }} km</p>
          <p class="mt-1 text-xs text-slate-500">Company {{ row.company_id }}</p>
          <button class="btn-secondary mt-3" type="button" @click="toggleBranch(row)">{{ row.status === 'ACTIVE' ? 'Deactivate' : 'Activate' }}</button>
        </article>
      </div>
    </section>

    <section class="admin-panel p-5">
      <h2 class="mb-4 font-semibold text-white">Create service area</h2>
      <form class="grid gap-3 md:grid-cols-4" @submit.prevent="createArea">
        <input v-model.trim="areaForm.name" required class="input-field" placeholder="Service area name" />
        <input v-model.trim="areaForm.company_id" class="input-field" placeholder="Company UUID (optional)" />
        <select v-model="areaForm.coverage_type" class="input-field"><option>RADIUS</option><option>POLYGON</option><option>ADMIN_REGION</option></select>
        <input v-model.number="areaForm.radius_km" type="number" min="1" max="500" class="input-field" placeholder="Radius km" />
        <input v-model.number="areaForm.center_lat" type="number" step="any" class="input-field" placeholder="Center latitude" />
        <input v-model.number="areaForm.center_lng" type="number" step="any" class="input-field" placeholder="Center longitude" />
        <input v-model.trim="areaForm.notes" class="input-field" placeholder="Coverage notes" />
        <button class="btn-primary">Create service area</button>
      </form>
      <div class="mt-5 grid gap-3 md:grid-cols-2">
        <article v-for="row in areas" :key="row.id" class="rounded-lg border border-white/5 bg-slate-950/30 p-4 text-sm">
          <div class="flex justify-between gap-3"><p class="font-medium text-white">{{ row.name }}</p><StatusBadge :status="row.status" /></div>
          <p class="mt-2 text-slate-400">{{ row.coverage_type }} · {{ row.radius_km || 'n/a' }} km</p>
          <p v-if="row.notes" class="mt-1 text-slate-300">{{ row.notes }}</p>
          <button class="btn-secondary mt-3" type="button" @click="toggleArea(row)">{{ row.status === 'ACTIVE' ? 'Deactivate' : 'Activate' }}</button>
        </article>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
definePageMeta({ layout: 'default', middleware: ['auth'] })
const { apiFetch } = useApi()
const branches = ref<any[]>([])
const areas = ref<any[]>([])
const error = ref('')
const branchMethods = ref('DELIVERY, INSTALLATION')
const branchForm = reactive({ company_id: '', name: '', country: 'Philippines', city: 'Cebu', radius_km: 30 })
const areaForm = reactive({ name: '', company_id: '', coverage_type: 'RADIUS', radius_km: 30, center_lat: null as number | null, center_lng: null as number | null, notes: '' })
async function load() {
  const [branchResult, areaResult] = await Promise.all([apiFetch<any>('/admin/cebu/branches'), apiFetch<any>('/admin/cebu/service-areas')])
  branches.value = branchResult.items; areas.value = areaResult.items
}
async function createBranch() {
  try {
    await apiFetch('/admin/cebu/branches', { method: 'POST', body: { ...branchForm, delivery_methods_json: branchMethods.value.split(',').map(v => v.trim()).filter(Boolean) } })
    Object.assign(branchForm, { company_id: '', name: '', country: 'Philippines', city: 'Cebu', radius_km: 30 }); await load()
  } catch (e: any) { error.value = e?.data?.detail || e?.message }
}
async function createArea() {
  try {
    await apiFetch('/admin/cebu/service-areas', { method: 'POST', body: { ...areaForm, company_id: areaForm.company_id || null } })
    Object.assign(areaForm, { name: '', company_id: '', coverage_type: 'RADIUS', radius_km: 30, center_lat: null, center_lng: null, notes: '' }); await load()
  } catch (e: any) { error.value = e?.data?.detail || e?.message }
}
async function toggleBranch(row: any) { try { await apiFetch(`/admin/cebu/branches/${row.id}`, { method: 'PATCH', body: { status: row.status === 'ACTIVE' ? 'INACTIVE' : 'ACTIVE' } }); await load() } catch (e: any) { error.value = e?.data?.detail || e?.message } }
async function toggleArea(row: any) { try { await apiFetch(`/admin/cebu/service-areas/${row.id}`, { method: 'PATCH', body: { status: row.status === 'ACTIVE' ? 'INACTIVE' : 'ACTIVE' } }); await load() } catch (e: any) { error.value = e?.data?.detail || e?.message } }
onMounted(() => load().catch((e: any) => { error.value = e?.data?.detail || e?.message }))
</script>
