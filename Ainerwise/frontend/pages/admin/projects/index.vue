<template>
  <div>
    <div class="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between mb-6">
      <div>
        <h1 class="text-2xl font-bold text-gray-900">Projects</h1>
        <p class="text-sm text-gray-500 mt-1">Manage active projects and their lifecycle.</p>
      </div>
      <div class="flex gap-2">
        <select v-model="statusFilter" class="input-field max-w-48" @change="loadProjects">
          <option value="">All statuses</option>
          <option v-for="s in statuses" :key="s" :value="s">{{ formatStatus(s) }}</option>
        </select>
        <NuxtLink to="/admin/projects/create" class="px-4 py-2 bg-primary-600 text-white text-sm font-medium rounded-lg hover:bg-primary-700">
          + New Project
        </NuxtLink>
      </div>
    </div>

    <div class="bg-white rounded-xl border overflow-hidden">
      <table class="w-full text-sm">
        <thead class="bg-gray-50 border-b">
          <tr>
            <th class="text-left px-4 py-3 font-medium text-gray-500">Title</th>
            <th class="text-left px-4 py-3 font-medium text-gray-500">Region</th>
            <th class="text-left px-4 py-3 font-medium text-gray-500">Status</th>
            <th class="text-left px-4 py-3 font-medium text-gray-500">Start Date</th>
            <th class="text-left px-4 py-3 font-medium text-gray-500">Delivery</th>
            <th class="text-left px-4 py-3 font-medium text-gray-500">Created</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="project in projects"
            :key="project.id"
            class="border-b hover:bg-gray-50 cursor-pointer"
            @click="$router.push(`/admin/projects/${project.id}`)"
          >
            <td class="px-4 py-3">
              <p class="font-medium text-gray-900">{{ project.title }}</p>
              <p class="text-xs text-gray-500 font-mono">{{ project.id.slice(0, 8) }}</p>
            </td>
            <td class="px-4 py-3 text-gray-600">{{ project.region || '-' }}</td>
            <td class="px-4 py-3"><StatusBadge :status="project.status" /></td>
            <td class="px-4 py-3 text-gray-600">{{ project.start_date || '-' }}</td>
            <td class="px-4 py-3 text-gray-600">{{ project.expected_delivery_date || '-' }}</td>
            <td class="px-4 py-3 text-gray-500 whitespace-nowrap">
              {{ new Date(project.created_at).toLocaleDateString() }}
            </td>
          </tr>
          <tr v-if="!projects.length">
            <td colspan="6" class="px-4 py-8 text-center text-gray-500">No projects found.</td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Pagination -->
    <div v-if="total > limit" class="mt-4 flex items-center justify-between text-sm">
      <p class="text-gray-500">Showing {{ skip + 1 }}-{{ Math.min(skip + limit, total) }} of {{ total }}</p>
      <div class="flex gap-2">
        <button
          class="px-3 py-1.5 rounded-lg border text-gray-600 hover:bg-gray-50 disabled:opacity-40"
          :disabled="skip === 0"
          @click="skip -= limit; loadProjects()"
        >
          Previous
        </button>
        <button
          class="px-3 py-1.5 rounded-lg border text-gray-600 hover:bg-gray-50 disabled:opacity-40"
          :disabled="skip + limit >= total"
          @click="skip += limit; loadProjects()"
        >
          Next
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
definePageMeta({ layout: 'admin', middleware: 'admin' })

const { apiFetch } = useApi()
const projects = ref<any[]>([])
const total = ref(0)
const skip = ref(0)
const limit = 20
const statusFilter = ref('')

const statuses = [
  'planning', 'site_survey', 'quotation_confirmed', 'procurement',
  'delivery', 'installation', 'testing', 'handover',
  'maintenance', 'closed',
]

function formatStatus(s: string) {
  return s.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())
}

async function loadProjects() {
  const params = new URLSearchParams()
  params.set('skip', String(skip.value))
  params.set('limit', String(limit))
  if (statusFilter.value) params.set('status', statusFilter.value)
  try {
    const res = await apiFetch<any>(`/projects?${params.toString()}`)
    projects.value = res.items || []
    total.value = res.total || 0
  } catch {
    projects.value = []
    total.value = 0
  }
}

onMounted(loadProjects)
</script>
