<template>
  <div>
    <div class="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between mb-6">
      <div>
        <h1 class="admin-page-title">Sites & Assets</h1>
        <p class="admin-page-desc">Installed-device registry per customer building. Tickets and maintenance link to assets.</p>
      </div>
    </div>

    <div class="admin-panel p-4 mb-6">
      <h2 class="font-medium text-gray-900 mb-3">New site</h2>
      <div class="grid gap-2 md:grid-cols-4">
        <input v-model="siteForm.name" placeholder="Site name" class="input-field md:col-span-2" />
        <input v-model="siteForm.city" placeholder="City" class="input-field" />
        <input v-model="siteForm.country" placeholder="Country" class="input-field" />
        <input v-model="siteForm.address" placeholder="Address" class="input-field md:col-span-2" />
      </div>
      <button class="btn-primary text-sm px-4 py-2 mt-3" :disabled="busy || !siteForm.name" @click="createSite">Create site</button>
    </div>

    <div class="grid gap-4 md:grid-cols-2">
      <div class="admin-panel">
        <h2 class="font-medium text-gray-900 px-4 pt-4">Sites</h2>
        <table class="admin-table w-full text-sm mt-2">
          <tbody>
            <tr v-for="s in sites" :key="s.id" class="border-b cursor-pointer hover:bg-gray-50"
                :class="{ 'bg-gray-50': selected?.id === s.id }" @click="openSite(s.id)">
              <td class="px-4 py-3">
                <p class="font-medium text-gray-900">{{ s.name }}</p>
                <p class="text-xs text-gray-500">{{ [s.city, s.country].filter(Boolean).join(', ') }}</p>
              </td>
            </tr>
            <tr v-if="!sites.length">
              <td class="px-4 py-8 text-center text-gray-500">No sites yet.</td>
            </tr>
          </tbody>
        </table>
      </div>

      <div class="admin-panel p-4">
        <template v-if="selected">
          <h2 class="font-medium text-gray-900 mb-3">Assets — {{ selected.site.name }}</h2>
          <div class="grid gap-2 mb-3">
            <input v-model="assetForm.name" placeholder="Asset name (e.g. KNX gateway)" class="input-field" />
            <div class="grid grid-cols-3 gap-2">
              <input v-model="assetForm.floor" placeholder="Floor" class="input-field" />
              <input v-model="assetForm.room" placeholder="Room" class="input-field" />
              <input v-model="assetForm.serial_no" placeholder="Serial no" class="input-field" />
            </div>
            <button class="btn-primary text-sm px-4 py-2" :disabled="busy || !assetForm.name" @click="createAsset">Add asset</button>
          </div>
          <div class="space-y-1 text-sm">
            <div v-for="a in selected.assets" :key="a.id" class="flex items-center justify-between border-b py-2">
              <div>
                <span class="font-medium text-gray-900">{{ a.name }}</span>
                <span class="text-xs text-gray-500 ml-2">{{ [a.floor, a.room].filter(Boolean).join(' / ') }}</span>
                <span v-if="a.serial_no" class="text-xs text-gray-400 ml-2 font-mono">{{ a.serial_no }}</span>
              </div>
              <StatusBadge :status="a.status" />
            </div>
            <p v-if="!selected.assets.length" class="text-gray-500 py-4">No assets registered.</p>
          </div>
        </template>
        <p v-else class="text-sm text-gray-500">Select a site to manage its assets.</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
definePageMeta({ layout: 'default' })

const { apiFetch } = useApi()
const sites = ref<any[]>([])
const selected = ref<any>(null)
const busy = ref(false)
const siteForm = ref<any>({ name: '', city: '', country: '', address: '' })
const assetForm = ref<any>({ name: '', floor: '', room: '', serial_no: '' })

async function load() {
  const res = await apiFetch<any>('/admin/sites')
  sites.value = res.items || []
}

async function openSite(id: string) {
  selected.value = await apiFetch<any>(`/admin/sites/${id}/assets`)
}

async function createSite() {
  busy.value = true
  try {
    await apiFetch('/admin/sites', { method: 'POST', body: siteForm.value })
    siteForm.value = { name: '', city: '', country: '', address: '' }
    await load()
  } finally {
    busy.value = false
  }
}

async function createAsset() {
  busy.value = true
  try {
    await apiFetch('/admin/assets', {
      method: 'POST',
      body: { site_id: selected.value.site.id, ...assetForm.value },
    })
    assetForm.value = { name: '', floor: '', room: '', serial_no: '' }
    await openSite(selected.value.site.id)
  } finally {
    busy.value = false
  }
}

onMounted(load)
</script>
