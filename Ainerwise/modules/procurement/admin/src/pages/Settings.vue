<template>
  <div class="space-y-4">
    <p class="text-sm text-slate-500">Changes are saved immediately on blur or toggle.</p>

    <div class="card p-5 flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
      <div>
        <p class="text-sm font-semibold text-slate-900">Demo Mode</p>
        <p class="mt-1 text-sm text-slate-500">
          Shows buyer/supplier demo credentials on PC and H5 login pages. When disabled, demo account login is blocked by the backend.
        </p>
      </div>
      <button
        class="w-14 h-8 rounded-full relative transition-colors flex-shrink-0"
        :class="demoSetting?.value === 'true' ? 'bg-primary-600' : 'bg-slate-200'"
        :disabled="!demoSetting"
        @click="demoSetting && toggle(demoSetting)"
      >
        <span class="absolute top-1 w-6 h-6 bg-white rounded-full shadow transition-all"
          :class="demoSetting?.value === 'true' ? 'left-7' : 'left-1'" />
      </button>
    </div>

    <div class="card overflow-hidden">
      <table class="w-full">
        <thead>
          <tr>
            <th class="table-th w-64">Key</th>
            <th class="table-th">Description</th>
            <th class="table-th w-48">Value</th>
            <th class="table-th w-24">Updated</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="loading"><td colspan="4" class="table-td text-center py-10 text-slate-400">Loading…</td></tr>
          <tr v-for="s in settings" :key="s.key" class="hover:bg-slate-50">
            <td class="table-td font-mono text-xs font-semibold text-slate-700">{{ s.key }}</td>
            <td class="table-td text-slate-500 text-xs">{{ s.description || '—' }}</td>
            <td class="table-td">
              <!-- Boolean toggle -->
              <template v-if="s.value === 'true' || s.value === 'false'">
                <button
                  class="w-11 h-6 rounded-full relative transition-colors"
                  :class="s.value === 'true' ? 'bg-primary-600' : 'bg-slate-200'"
                  @click="toggle(s)"
                >
                  <span class="absolute top-0.5 w-5 h-5 bg-white rounded-full shadow transition-all"
                    :class="s.value === 'true' ? 'left-[22px]' : 'left-0.5'" />
                </button>
              </template>
              <!-- Text input -->
              <template v-else>
                <input v-model="s._draft" class="input py-1 text-xs" @blur="save(s)" @keyup.enter="save(s)" />
              </template>
            </td>
            <td class="table-td text-xs text-slate-400">{{ fmtDate(s.updated_at) }}</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup>
import { computed, ref, onMounted } from 'vue'
import { api, fmtDate } from '@/utils/api'

const loading = ref(true)
const settings = ref([])
const demoSetting = computed(() => settings.value.find(s => s.key === 'DEMO_MODE'))

async function save(s) {
  const val = s._draft ?? s.value
  if (val === s.value) return
  try {
    const { data } = await api.put(`/admin/settings/${s.key}`, { value: val })
    s.value = data.value
    s._draft = data.value
    s.updated_at = data.updated_at
  } catch (e) {
    alert(e.response?.data?.detail || 'Save failed')
    s._draft = s.value
  }
}

async function toggle(s) {
  s._draft = s.value === 'true' ? 'false' : 'true'
  await save(s)
}

onMounted(async () => {
  const data = await api.get('/admin/settings').then(r => r.data)
  settings.value = data.map(s => ({ ...s, _draft: s.value }))
  loading.value = false
})
</script>
