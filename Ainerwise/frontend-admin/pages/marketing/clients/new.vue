<template>
  <div class="space-y-6 max-w-xl">
    <div class="flex items-center justify-between">
      <div>
        <h1 class="admin-page-title">{{ $t('marketingIntegration.newClient') }}</h1>
        <p class="admin-page-desc">{{ $t('marketingIntegration.newClientDesc') }}</p>
      </div>
      <NuxtLink to="/marketing/clients" class="action-button">{{ $t('common.cancel') }}</NuxtLink>
    </div>

    <ClientSecretBanner v-if="createdSecret" :secret="createdSecret" @dismiss="goToList" />

    <form v-if="!createdSecret" class="admin-card p-5 space-y-4" @submit.prevent="submit">
      <label class="block">
        <span class="text-[10px] uppercase tracking-wider text-slate-500">{{ $t('marketingIntegration.clientName') }}</span>
        <input v-model="name" required class="mt-1 w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-sm text-slate-200" />
      </label>

      <fieldset class="space-y-2">
        <legend class="text-[10px] uppercase tracking-wider text-slate-500">Scopes</legend>
        <label v-for="scope in INTEGRATION_SCOPES" :key="scope" class="flex items-center gap-2 text-sm text-slate-300">
          <input v-model="scopes" type="checkbox" :value="scope" class="rounded" />
          {{ scope }}
        </label>
      </fieldset>

      <div v-if="error" class="text-sm text-red-400">{{ error }}</div>

      <button type="submit" class="action-button primary w-full" :disabled="busy || !scopes.length">
        {{ busy ? $t('common.loading') : $t('common.create') }}
      </button>
    </form>

    <div v-else class="admin-card p-5 text-center">
      <p class="text-sm text-slate-400">{{ $t('marketingIntegration.secretSavedHint') }}</p>
      <button type="button" class="action-button mt-4" @click="goToList">{{ $t('marketingIntegration.goToClients') }}</button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { INTEGRATION_SCOPES } from '~/composables/useMarketingIntegration'

definePageMeta({ layout: 'default' })

const { createIntegrationClient } = useMarketingIntegration()

const name = ref('')
const scopes = ref<string[]>([...INTEGRATION_SCOPES])
const busy = ref(false)
const error = ref('')
const createdSecret = ref<string | null>(null)

async function submit() {
  busy.value = true
  error.value = ''
  try {
    const created = await createIntegrationClient({ name: name.value, scopes: scopes.value })
    createdSecret.value = created.client_secret
  } catch (e: any) {
    error.value = e?.data?.detail || e?.message || 'Create failed'
  } finally {
    busy.value = false
  }
}

function goToList() {
  navigateTo('/marketing/clients')
}
</script>
