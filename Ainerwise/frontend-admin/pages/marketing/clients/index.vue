<template>
  <div class="space-y-6">
    <div class="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
      <div>
        <h1 class="admin-page-title">{{ $t('marketingIntegration.clientsTitle') }}</h1>
        <p class="admin-page-desc">{{ $t('marketingIntegration.clientsDesc') }}</p>
      </div>
      <div class="flex gap-2">
        <NuxtLink to="/marketing/integration" class="action-button">{{ $t('common.back') }}</NuxtLink>
        <NuxtLink to="/marketing/clients/new" class="action-button primary">+ {{ $t('marketingIntegration.newClient') }}</NuxtLink>
      </div>
    </div>

    <ClientSecretBanner :secret="revealedSecret" @dismiss="revealedSecret = null" />

    <div v-if="error" class="rounded-xl border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-200">
      {{ error }}
    </div>

    <div class="admin-card p-0 overflow-hidden">
      <table class="admin-table w-full text-sm">
        <thead>
          <tr class="border-b border-white/5 bg-white/[0.02]">
            <th class="text-left py-3 px-4">{{ $t('marketingIntegration.clientName') }}</th>
            <th class="text-left py-3 px-4">Key prefix</th>
            <th class="text-left py-3 px-4">{{ $t('common.status') }}</th>
            <th class="text-left py-3 px-4">Scopes</th>
            <th class="text-left py-3 px-4">{{ $t('common.actions') }}</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="client in clients" :key="client.id" class="border-b border-white/[0.03]">
            <td class="px-4 py-3 font-medium text-slate-200">{{ client.name }}</td>
            <td class="px-4 py-3 text-slate-400 font-mono text-xs">{{ client.key_prefix }}…</td>
            <td class="px-4 py-3"><StatusBadge :status="client.status" /></td>
            <td class="px-4 py-3 text-xs text-slate-500">{{ client.scopes_json.join(', ') }}</td>
            <td class="px-4 py-3 whitespace-nowrap">
              <div class="flex flex-wrap gap-2">
                <button
                  v-if="client.status === 'active'"
                  class="text-xs px-2 py-1 rounded border border-amber-500/40 text-amber-300"
                  :disabled="busy"
                  @click="suspend(client.id)"
                >
                  {{ $t('marketingIntegration.suspend') }}
                </button>
                <button
                  v-if="client.status !== 'revoked'"
                  class="text-xs px-2 py-1 rounded border border-red-500/40 text-red-300"
                  :disabled="busy"
                  @click="revoke(client.id)"
                >
                  {{ $t('marketingIntegration.revoke') }}
                </button>
                <button
                  v-if="client.status === 'active'"
                  class="text-xs px-2 py-1 rounded border border-cyan-500/40 text-cyan-300"
                  :disabled="busy"
                  @click="rotate(client.id)"
                >
                  {{ $t('marketingIntegration.rotateSecret') }}
                </button>
              </div>
            </td>
          </tr>
          <tr v-if="!clients.length">
            <td colspan="5" class="px-4 py-10 text-center text-slate-500">{{ $t('common.noData') }}</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { IntegrationClient } from '~/composables/useMarketingIntegration'

definePageMeta({ layout: 'default' })

const {
  listIntegrationClients,
  suspendIntegrationClient,
  revokeIntegrationClient,
  rotateIntegrationSecret,
} = useMarketingIntegration()

const clients = ref<IntegrationClient[]>([])
const revealedSecret = ref<string | null>(null)
const busy = ref(false)
const error = ref('')

async function load() {
  error.value = ''
  const res = await listIntegrationClients()
  clients.value = res.items
}

async function suspend(id: string) {
  if (!confirm('Suspend this client?')) return
  busy.value = true
  try {
    await suspendIntegrationClient(id)
    await load()
  } catch (e: any) {
    error.value = e?.data?.detail || e?.message
  } finally {
    busy.value = false
  }
}

async function revoke(id: string) {
  if (!confirm('Revoke this client? This cannot be undone.')) return
  busy.value = true
  try {
    await revokeIntegrationClient(id)
    await load()
  } catch (e: any) {
    error.value = e?.data?.detail || e?.message
  } finally {
    busy.value = false
  }
}

async function rotate(id: string) {
  if (!confirm('Rotate secret? Old secret stops working immediately.')) return
  busy.value = true
  revealedSecret.value = null
  try {
    const created = await rotateIntegrationSecret(id)
    revealedSecret.value = created.client_secret
    await load()
  } catch (e: any) {
    error.value = e?.data?.detail || e?.message
  } finally {
    busy.value = false
  }
}

onMounted(load)
</script>
