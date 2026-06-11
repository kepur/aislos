<template>
  <div class="space-y-4">
    <p class="text-sm text-slate-500">{{ $t('notifications.desc') }}</p>

    <div class="card overflow-hidden">
      <table class="w-full">
        <thead><tr>
          <th class="table-th">{{ $t('notifications.templateKey') }}</th>
          <th class="table-th">{{ $t('notifications.channel') }}</th>
          <th class="table-th">{{ $t('notifications.subject') }}</th>
          <th class="table-th">{{ $t('common.active') }}</th>
          <th class="table-th">{{ $t('common.actions') }}</th>
        </tr></thead>
        <tbody>
          <tr v-if="loading"><td colspan="5" class="table-td text-center py-10 text-slate-400">{{ $t('common.loading') }}</td></tr>
          <tr v-else-if="!templates.length"><td colspan="5" class="table-td text-center py-10 text-slate-400">{{ $t('notifications.noTemplates') }}</td></tr>
          <tr v-for="tpl in templates" :key="tpl.template_key" class="hover:bg-slate-50">
            <td class="table-td font-mono text-xs">{{ tpl.template_key }}</td>
            <td class="table-td"><span class="badge badge-blue">{{ tpl.channel || 'EMAIL' }}</span></td>
            <td class="table-td text-sm">{{ tpl.subject || '—' }}</td>
            <td class="table-td">
              <span :class="tpl.active ? 'badge-green' : 'badge-red'" class="badge">{{ tpl.active ? $t('common.yes') : $t('common.no') }}</span>
            </td>
            <td class="table-td">
              <div class="flex gap-1">
                <button class="btn btn-secondary py-1 px-2 text-xs" @click="edit(tpl)">{{ $t('common.edit') }}</button>
                <button class="btn badge-blue py-1 px-2 text-xs" @click="test(tpl.template_key)">{{ $t('common.test') }}</button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Edit Modal -->
    <div v-if="editing" class="fixed inset-0 bg-black/40 z-50 flex items-center justify-center p-4" @click.self="editing=null">
      <div class="bg-white rounded-2xl w-full max-w-lg p-6 space-y-4">
        <h3 class="font-bold text-lg text-slate-900">{{ $t('common.edit') }}: {{ editing.template_key }}</h3>
        <div>
          <label class="text-xs font-medium text-slate-600">{{ $t('notifications.subject') }}</label>
          <input v-model="editing.subject" class="input" />
        </div>
        <div>
          <label class="text-xs font-medium text-slate-600">{{ $t('notifications.body') }}</label>
          <textarea v-model="editing.body" class="input font-mono text-xs" rows="8"></textarea>
        </div>
        <div v-if="editing.variables_hint" class="text-xs text-slate-400">
          <p class="font-medium">{{ $t('notifications.variables') }}</p>
          <p>{{ editing.variables_hint }}</p>
        </div>
        <div>
          <label class="text-xs font-medium text-slate-600">{{ $t('notifications.channel') }}</label>
          <select v-model="editing.channel" class="input">
            <option value="EMAIL">Email</option>
            <option value="SMS">SMS</option>
            <option value="IN_APP">In-App</option>
            <option value="PUSH">Push</option>
            <option value="TELEGRAM">Telegram</option>
          </select>
        </div>
        <div class="flex items-center gap-2">
          <input type="checkbox" v-model="editing.active" id="tpl-active" class="rounded" />
          <label for="tpl-active" class="text-sm text-slate-700">{{ $t('common.active') }}</label>
        </div>
        <div class="flex gap-3">
          <button class="btn btn-secondary flex-1" @click="editing=null">{{ $t('common.cancel') }}</button>
          <button class="btn btn-primary flex-1" @click="save">{{ $t('common.save') }}</button>
        </div>
      </div>
    </div>

    <div v-if="testResult" class="card p-4 border-green-200 bg-green-50">
      <p class="text-sm text-green-800 font-medium">{{ testResult }}</p>
      <button class="text-xs text-green-600 underline mt-1" @click="testResult=''">{{ $t('common.dismiss') }}</button>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { api } from '@/utils/api'

const loading = ref(true)
const templates = ref([])
const editing = ref(null)
const testResult = ref('')

async function load() {
  loading.value = true
  try {
    templates.value = await api.get('/admin/notification-templates').then(r => r.data)
  } catch { templates.value = [] }
  loading.value = false
}

function edit(tpl) {
  editing.value = { ...tpl }
}

async function save() {
  try {
    await api.put(`/admin/notification-templates/${editing.value.template_key}`, {
      subject: editing.value.subject,
      body: editing.value.body,
      active: editing.value.active
    })
    await load()
    editing.value = null
  } catch (e) { alert(e.response?.data?.detail || 'Failed') }
}

async function test(key) {
  const tpl = templates.value.find(t => t.template_key === key)
  const channel = tpl?.channel || 'EMAIL'
  try {
    const { data } = await api.post(`/admin/notifications/test?channel=${channel}`)
    testResult.value = data.message || data.detail || `Test sent for ${channel}`
  } catch (e) { alert(e.response?.data?.detail || 'Failed') }
}

onMounted(load)
</script>
