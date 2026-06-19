<!-- LocationPicker.vue — H5 可复用位置/区域选择组件
     Props:
       modelValue: { lat, lng, regionId, label } | null
       placeholder: string
     Emits:
       update:modelValue: { lat, lng, regionId, regionName, label }
-->
<template>
  <!-- Trigger button -->
  <button
    type="button"
    @click="open = true"
    class="flex items-center gap-2 w-full text-left bg-slate-100 rounded-xl px-4 py-3 text-sm transition-colors active:bg-slate-200"
  >
    <svg class="w-4 h-4 text-indigo-500 flex-shrink-0" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
      <path stroke-linecap="round" stroke-linejoin="round" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"/>
      <path stroke-linecap="round" stroke-linejoin="round" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z"/>
    </svg>
    <span :class="modelValue ? 'text-slate-900 font-medium' : 'text-slate-400'">
      {{ modelValue?.label || placeholder || 'Select location...' }}
    </span>
    <svg class="w-4 h-4 text-slate-400 ml-auto" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
      <path stroke-linecap="round" stroke-linejoin="round" d="M9 5l7 7-7 7"/>
    </svg>
  </button>

  <!-- Bottom Sheet Drawer -->
  <Teleport to="body">
    <Transition name="sheet">
      <div v-if="open" class="fixed inset-0 z-[200] flex flex-col justify-end">
        <!-- Backdrop -->
        <div class="absolute inset-0 bg-black/40 backdrop-blur-sm" @click="open = false" />

        <!-- Sheet -->
        <div class="relative bg-white rounded-t-3xl shadow-2xl max-h-[85vh] flex flex-col">
          <!-- Handle -->
          <div class="flex justify-center pt-3 pb-1">
            <div class="w-10 h-1 bg-slate-200 rounded-full" />
          </div>

          <!-- Header -->
          <div class="px-5 pb-3 flex items-center justify-between border-b border-slate-100">
            <h3 class="text-base font-bold text-slate-900">📍 Select Location</h3>
            <button @click="open = false" class="text-slate-400 p-1 hover:text-slate-600">
              <svg class="w-5 h-5" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12"/>
              </svg>
            </button>
          </div>

          <!-- Tabs -->
          <div class="flex gap-1 px-4 pt-3">
            <button
              v-for="tab in tabs"
              :key="tab.key"
              @click="activeTab = tab.key"
              :class="['flex-1 py-2 text-xs font-semibold rounded-xl transition-colors', activeTab === tab.key ? 'bg-indigo-600 text-white' : 'bg-slate-100 text-slate-500']"
            >{{ tab.label }}</button>
          </div>

          <!-- Content -->
          <div class="flex-1 overflow-y-auto px-4 py-3 space-y-2">

            <!-- GPS Tab -->
            <div v-if="activeTab === 'gps'" class="space-y-3">
              <p class="text-xs text-slate-500 text-center">Use your device's GPS to auto-detect your location.</p>
              <button
                @click="getGPS"
                :disabled="gpsLoading"
                class="w-full bg-indigo-600 text-white rounded-2xl py-4 font-semibold text-sm flex items-center justify-center gap-2 disabled:opacity-60 active:scale-95 transition-transform"
              >
                <svg v-if="!gpsLoading" class="w-5 h-5" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"/>
                </svg>
                <svg v-else class="w-5 h-5 animate-spin" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"/>
                </svg>
                {{ gpsLoading ? 'Detecting...' : '📡 Use My Current Location' }}
              </button>
              <div v-if="gpsResult" class="bg-green-50 border border-green-200 rounded-xl p-3 text-sm">
                <p class="font-semibold text-green-800">✓ Location detected</p>
                <p class="text-green-700 text-xs mt-1">{{ gpsResult.label }}</p>
                <button @click="confirmGPS" class="mt-3 w-full bg-green-600 text-white rounded-xl py-2 text-sm font-semibold">
                  Use This Location
                </button>
              </div>
              <div v-if="gpsError" class="bg-red-50 border border-red-100 rounded-xl p-3 text-xs text-red-700">
                ⚠️ {{ gpsError }}
              </div>
            </div>

            <!-- Region Tab -->
            <div v-if="activeTab === 'region'" class="space-y-2">
              <!-- Search -->
              <div class="relative">
                <input
                  v-model="regionSearch"
                  type="text"
                  placeholder="Search city or region..."
                  class="w-full bg-slate-100 rounded-xl px-4 py-2.5 text-sm outline-none pr-8"
                />
                <svg class="w-4 h-4 text-slate-400 absolute right-3 top-1/2 -translate-y-1/2" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M21 21l-4.35-4.35M17 11A6 6 0 115 11a6 6 0 0112 0z"/>
                </svg>
              </div>

              <div v-if="regionsLoading" class="flex justify-center py-6">
                <svg class="w-6 h-6 animate-spin text-slate-400" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"/>
                </svg>
              </div>

              <div v-else class="space-y-1">
                <button
                  v-for="region in filteredRegions"
                  :key="region.id"
                  @click="selectRegion(region)"
                  :class="[
                    'w-full flex items-center gap-3 px-4 py-3 rounded-xl text-left transition-colors active:scale-95 active:bg-indigo-50',
                    selectedRegionId === region.id ? 'bg-indigo-50 border border-indigo-200' : 'hover:bg-slate-50'
                  ]"
                >
                  <div class="w-8 h-8 rounded-lg bg-indigo-100 flex items-center justify-center text-sm flex-shrink-0">🏙️</div>
                  <div class="flex-1 min-w-0">
                    <p class="text-sm font-semibold text-slate-900">{{ region.name }}</p>
                    <p class="text-xs text-slate-400 truncate">{{ region.country }} · {{ region.region_type }}</p>
                  </div>
                  <div v-if="selectedRegionId === region.id" class="text-indigo-600">
                    <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                      <path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd"/>
                    </svg>
                  </div>
                </button>

                <div v-if="filteredRegions.length === 0" class="text-center py-6 text-slate-400 text-sm">
                  No regions found for "{{ regionSearch }}"
                </div>
              </div>
            </div>

            <!-- Manual Tab -->
            <div v-if="activeTab === 'manual'" class="space-y-3">
              <p class="text-xs text-slate-500">Enter coordinates manually or search by address.</p>
              <div>
                <label class="block text-xs text-slate-500 mb-1 font-medium">Address / Label</label>
                <input v-model="manualLabel" type="text" placeholder="e.g. Ayala Center Cebu" class="w-full bg-slate-100 rounded-xl px-4 py-2.5 text-sm outline-none" />
              </div>
              <div class="grid grid-cols-2 gap-2">
                <div>
                  <label class="block text-xs text-slate-500 mb-1 font-medium">Latitude</label>
                  <input v-model.number="manualLat" type="number" step="0.0001" placeholder="10.3157" class="w-full bg-slate-100 rounded-xl px-3 py-2.5 text-sm outline-none" />
                </div>
                <div>
                  <label class="block text-xs text-slate-500 mb-1 font-medium">Longitude</label>
                  <input v-model.number="manualLng" type="number" step="0.0001" placeholder="123.8854" class="w-full bg-slate-100 rounded-xl px-3 py-2.5 text-sm outline-none" />
                </div>
              </div>
              <button
                @click="confirmManual"
                :disabled="!manualLat || !manualLng"
                class="w-full bg-indigo-600 text-white rounded-2xl py-3 font-semibold text-sm disabled:opacity-40 active:scale-95 transition-transform"
              >
                Confirm Location
              </button>
            </div>
          </div>

          <!-- Clear button -->
          <div v-if="modelValue" class="px-4 pb-4 pt-2 border-t border-slate-100">
            <button
              @click="clearLocation"
              class="w-full py-2.5 rounded-xl text-sm text-slate-500 font-medium hover:bg-slate-50 flex items-center justify-center gap-2"
            >
              <svg class="w-4 h-4" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12"/>
              </svg>
              Clear location
            </button>
          </div>

          <!-- Safe area padding -->
          <div class="pb-safe" />
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup lang="ts">
interface Region {
  id: string
  name: string
  country: string
  region_type: string
  center_lat: number
  center_lng: number
  default_radius_km: number
}

interface LocationValue {
  lat: number
  lng: number
  regionId?: string
  regionName?: string
  label: string
}

const props = defineProps<{
  modelValue: LocationValue | null
  placeholder?: string
}>()

const emit = defineEmits<{
  'update:modelValue': [value: LocationValue | null]
}>()

const config = useRuntimeConfig()

const open = ref(false)
const activeTab = ref<'gps' | 'region' | 'manual'>('gps')
const tabs = [
  { key: 'gps', label: '📡 GPS' },
  { key: 'region', label: '🗺️ Region' },
  { key: 'manual', label: '✏️ Manual' },
] as const

// GPS
const gpsLoading = ref(false)
const gpsError = ref('')
const gpsResult = ref<LocationValue | null>(null)

// Region
const regions = ref<Region[]>([])
const regionsLoading = ref(false)
const regionSearch = ref('')
const selectedRegionId = ref<string | null>(props.modelValue?.regionId || null)

// Manual
const manualLat = ref<number | null>(null)
const manualLng = ref<number | null>(null)
const manualLabel = ref('')

const filteredRegions = computed(() => {
  if (!regionSearch.value.trim()) return regions.value
  const q = regionSearch.value.toLowerCase()
  return regions.value.filter(r =>
    r.name.toLowerCase().includes(q) || r.country.toLowerCase().includes(q)
  )
})

async function loadRegions() {
  if (regions.value.length) return
  regionsLoading.value = true
  try {
    const data = await $fetch<Region[]>(`${config.public.apiBase}/admin/regions`)
    regions.value = data
  } catch {
    // Fallback to common PH cities
    regions.value = [
      { id: 'cebu', name: 'Cebu City', country: 'Philippines', region_type: 'CITY', center_lat: 10.3157, center_lng: 123.8854, default_radius_km: 20 },
      { id: 'manila', name: 'Manila', country: 'Philippines', region_type: 'CITY', center_lat: 14.5995, center_lng: 120.9842, default_radius_km: 25 },
      { id: 'davao', name: 'Davao City', country: 'Philippines', region_type: 'CITY', center_lat: 7.0707, center_lng: 125.6087, default_radius_km: 25 },
      { id: 'quezon', name: 'Quezon City', country: 'Philippines', region_type: 'DISTRICT', center_lat: 14.6760, center_lng: 121.0437, default_radius_km: 15 },
      { id: 'lapu', name: 'Lapu-Lapu City', country: 'Philippines', region_type: 'CITY', center_lat: 10.3103, center_lng: 123.9494, default_radius_km: 15 },
      { id: 'mandaue', name: 'Mandaue City', country: 'Philippines', region_type: 'CITY', center_lat: 10.3236, center_lng: 123.9223, default_radius_km: 10 },
      { id: 'cagayan', name: 'Cagayan de Oro', country: 'Philippines', region_type: 'CITY', center_lat: 8.4542, center_lng: 124.6319, default_radius_km: 20 },
      { id: 'iloilo', name: 'Iloilo City', country: 'Philippines', region_type: 'CITY', center_lat: 10.7202, center_lng: 122.5621, default_radius_km: 20 },
      { id: 'bacolod', name: 'Bacolod City', country: 'Philippines', region_type: 'CITY', center_lat: 10.6840, center_lng: 122.9567, default_radius_km: 20 },
      { id: 'zamboanga', name: 'Zamboanga City', country: 'Philippines', region_type: 'CITY', center_lat: 6.9214, center_lng: 122.0790, default_radius_km: 20 },
    ]
  } finally {
    regionsLoading.value = false
  }
}

function getGPS() {
  if (!navigator.geolocation) {
    gpsError.value = 'GPS not supported on this device.'
    return
  }
  gpsLoading.value = true
  gpsError.value = ''
  gpsResult.value = null
  navigator.geolocation.getCurrentPosition(
    async (pos) => {
      const { latitude: lat, longitude: lng } = pos.coords
      // Reverse geocode via backend if available
      let label = `${lat.toFixed(4)}, ${lng.toFixed(4)}`
      try {
        const geo = await $fetch<any>(`${config.public.apiBase}/maps/reverse-geocode`, {
          params: { lat, lng }
        })
        label = geo.formatted_address || geo.address || label
      } catch {}
      gpsResult.value = { lat, lng, label }
      gpsLoading.value = false
    },
    (err) => {
      gpsError.value = err.code === 1
        ? 'Location permission denied. Please enable location access in your browser settings.'
        : 'Could not detect location. Please try again.'
      gpsLoading.value = false
    },
    { timeout: 10000, enableHighAccuracy: true }
  )
}

function confirmGPS() {
  if (!gpsResult.value) return
  emit('update:modelValue', gpsResult.value)
  open.value = false
}

function selectRegion(region: Region) {
  selectedRegionId.value = region.id
  const value: LocationValue = {
    lat: region.center_lat,
    lng: region.center_lng,
    regionId: region.id,
    regionName: region.name,
    label: `${region.name}, ${region.country}`,
  }
  emit('update:modelValue', value)
  open.value = false
}

function confirmManual() {
  if (!manualLat.value || !manualLng.value) return
  emit('update:modelValue', {
    lat: manualLat.value,
    lng: manualLng.value,
    label: manualLabel.value || `${manualLat.value.toFixed(4)}, ${manualLng.value.toFixed(4)}`,
  })
  open.value = false
}

function clearLocation() {
  selectedRegionId.value = null
  gpsResult.value = null
  emit('update:modelValue', null)
  open.value = false
}

// Load regions when tab switches
watch(activeTab, (tab) => {
  if (tab === 'region') loadRegions()
})

// Pre-load regions if starting on region tab
onMounted(() => {
  if (activeTab.value === 'region') loadRegions()
})
</script>

<style scoped>
.sheet-enter-active, .sheet-leave-active {
  transition: all 0.3s cubic-bezier(0.32, 0.72, 0, 1);
}
.sheet-enter-from, .sheet-leave-to {
  transform: translateY(100%);
  opacity: 0;
}
.pb-safe {
  padding-bottom: env(safe-area-inset-bottom, 16px);
}
</style>
