<template>
  <div class="space-y-6">
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-2xl font-bold text-slate-900">⚖️ Ranking Configuration</h1>
        <p class="text-sm text-slate-500 mt-1">Configure weight profiles used by the AI supplier matching system.</p>
      </div>
      <UButton icon="i-heroicons-arrow-path" color="gray" variant="ghost" :loading="loading" @click="loadProfiles">
        Refresh
      </UButton>
    </div>

    <!-- Active profile notice -->
    <UAlert
      icon="i-heroicons-information-circle"
      color="indigo"
      variant="soft"
      title="Live Updates"
      description="Changes to weights take effect immediately for all new ranking requests. Running requests are not affected."
    />

    <!-- Summary overview -->
    <UCard>
      <template #header>
        <h3 class="text-base font-semibold text-slate-900">Live Weight Summary (All Sort Modes)</h3>
      </template>
      <div v-if="summary" class="overflow-x-auto">
        <table class="w-full text-sm">
          <thead>
            <tr class="text-left border-b border-slate-100">
              <th class="pb-2 font-medium text-slate-500 pr-6">Mode</th>
              <th class="pb-2 font-medium text-slate-500 pr-4">Category</th>
              <th class="pb-2 font-medium text-slate-500 pr-4">Trust</th>
              <th class="pb-2 font-medium text-slate-500 pr-4">Distance</th>
              <th class="pb-2 font-medium text-slate-500 pr-4">Deal Rate</th>
              <th class="pb-2 font-medium text-slate-500 pr-4">Stock</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(w, mode) in summary" :key="mode" class="border-b border-slate-50 hover:bg-slate-50">
              <td class="py-2 pr-6 font-semibold text-slate-800 capitalize">{{ mode }}</td>
              <td class="py-2 pr-4 text-slate-600">{{ pct(w.category_match || w.category) }}</td>
              <td class="py-2 pr-4 text-slate-600">{{ pct(w.trust) }}</td>
              <td class="py-2 pr-4 text-slate-600">{{ pct(w.distance) }}</td>
              <td class="py-2 pr-4 text-slate-600">{{ pct(w.deal_rate) }}</td>
              <td class="py-2 pr-4 text-slate-600">{{ pct(w.stock) }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </UCard>

    <!-- Profile cards -->
    <div class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
      <UCard
        v-for="profile in profiles"
        :key="profile.id"
        :class="profile.is_default ? 'ring-2 ring-indigo-400' : ''"
      >
        <template #header>
          <div class="flex items-center justify-between gap-2">
            <div>
              <p class="font-semibold text-slate-900 flex items-center gap-2">
                {{ profile.name }}
                <UBadge v-if="profile.is_default" color="indigo" variant="subtle" size="xs">Default</UBadge>
              </p>
              <p class="text-xs text-slate-400 mt-0.5">{{ profile.description }}</p>
            </div>
            <UButton
              size="xs"
              color="indigo"
              variant="ghost"
              icon="i-heroicons-pencil-square"
              @click="editProfile(profile)"
            />
          </div>
        </template>

        <!-- Weight visualization -->
        <div class="space-y-2">
          <div v-for="(val, key) in profile.weights" :key="key" class="flex items-center gap-2">
            <span class="text-xs text-slate-500 w-24 flex-shrink-0 capitalize">{{ key.replace('_', ' ') }}</span>
            <div class="flex-1 bg-slate-100 rounded-full h-2 overflow-hidden">
              <div
                class="h-2 rounded-full bg-indigo-500 transition-all duration-300"
                :style="{ width: `${Math.min(val * 100, 100)}%` }"
              />
            </div>
            <span class="text-xs font-mono text-slate-700 w-10 text-right">{{ pct(val) }}</span>
          </div>
        </div>

        <div class="mt-3 pt-3 border-t border-slate-100 flex items-center justify-between">
          <span class="text-xs text-slate-400">Total weight: <span :class="Math.abs(profile.total_weight - 1) < 0.05 ? 'text-green-600 font-semibold' : 'text-red-500 font-semibold'">{{ pct(profile.total_weight) }}</span></span>
          <UButton
            v-if="!['default','cost','trust','distance','delivery'].includes(profile.id)"
            size="xs"
            color="red"
            variant="ghost"
            icon="i-heroicons-trash"
            @click="deleteProfile(profile.id)"
          />
        </div>
      </UCard>
    </div>

    <!-- Edit Modal -->
    <UModal v-model="showEditModal">
      <UCard>
        <template #header>
          <h3 class="text-lg font-semibold">Edit: {{ editingProfile?.name }}</h3>
          <p class="text-xs text-slate-400 mt-1">Adjust weights (they should sum to 1.0 ± 5%)</p>
        </template>

        <div v-if="editForm" class="space-y-4">
          <div v-for="(val, key) in editForm" :key="key" class="flex items-center gap-3">
            <label class="text-sm text-slate-700 w-28 flex-shrink-0 capitalize">{{ String(key).replace('_', ' ') }}</label>
            <input
              type="range"
              min="0"
              max="0.8"
              step="0.01"
              :value="val"
              @input="editForm[key] = parseFloat(($event.target as HTMLInputElement).value)"
              class="flex-1"
            />
            <span class="text-sm font-mono text-slate-700 w-12 text-right">{{ pct(val) }}</span>
          </div>

          <div class="pt-2 flex items-center justify-between">
            <span class="text-xs font-medium" :class="Math.abs(totalEditWeight - 1) < 0.05 ? 'text-green-600' : 'text-red-500'">
              Sum: {{ pct(totalEditWeight) }} {{ Math.abs(totalEditWeight - 1) < 0.05 ? '✓' : '⚠ should be ~100%' }}
            </span>
            <div class="flex gap-2">
              <UButton color="gray" variant="ghost" @click="showEditModal = false">Cancel</UButton>
              <UButton color="indigo" :loading="saving" @click="saveProfile">Save Changes</UButton>
            </div>
          </div>
        </div>
      </UCard>
    </UModal>
  </div>
</template>

<script setup lang="ts">
definePageMeta({ layout: 'admin', middleware: ['admin'] })

const config = useRuntimeConfig()
const authStore = useAuthStore()
const toast = useToast()

const loading = ref(false)
const saving = ref(false)
const profiles = ref<any[]>([])
const summary = ref<any>(null)
const showEditModal = ref(false)
const editingProfile = ref<any>(null)
const editForm = ref<Record<string, number>>({})

const totalEditWeight = computed(() =>
  Object.values(editForm.value).reduce((a, b) => a + b, 0)
)

function pct(v: number | undefined | null): string {
  if (v == null) return '0%'
  return `${Math.round(v * 100)}%`
}

async function loadProfiles() {
  loading.value = true
  try {
    const [p, s] = await Promise.all([
      $fetch<any[]>(`${config.public.apiBase}/ranking/profiles`, {
        headers: { Authorization: `Bearer ${authStore.accessToken}` },
      }),
      $fetch<any>(`${config.public.apiBase}/admin/ranking/summary`, {
        headers: { Authorization: `Bearer ${authStore.accessToken}` },
      }),
    ])
    profiles.value = p
    summary.value = s
  } catch (e: any) {
    toast.add({ title: 'Failed to load ranking profiles', color: 'red' })
  } finally {
    loading.value = false
  }
}

function editProfile(profile: any) {
  editingProfile.value = profile
  editForm.value = { ...profile.weights }
  showEditModal.value = true
}

async function saveProfile() {
  if (!editingProfile.value) return
  saving.value = true
  try {
    await $fetch(`${config.public.apiBase}/ranking/profiles/${editingProfile.value.id}`, {
      method: 'PATCH',
      body: { weights: editForm.value },
      headers: { Authorization: `Bearer ${authStore.accessToken}` },
    })
    toast.add({ title: 'Weights updated successfully!', color: 'green' })
    showEditModal.value = false
    await loadProfiles()
  } catch (e: any) {
    toast.add({ title: e?.data?.detail || 'Update failed', color: 'red' })
  } finally {
    saving.value = false
  }
}

async function deleteProfile(profileId: string) {
  try {
    await $fetch(`${config.public.apiBase}/ranking/profiles/${profileId}`, {
      method: 'DELETE',
      headers: { Authorization: `Bearer ${authStore.accessToken}` },
    })
    toast.add({ title: 'Profile deleted', color: 'green' })
    await loadProfiles()
  } catch (e: any) {
    toast.add({ title: e?.data?.detail || 'Delete failed', color: 'red' })
  }
}

onMounted(() => loadProfiles())
</script>
