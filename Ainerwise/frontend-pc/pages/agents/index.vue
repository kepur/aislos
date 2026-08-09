<template>
  <div class="section-padding">
    <div class="container-main">
      <!-- Store first, developer onboarding after: most visitors come to find
           an agent, not to publish one. The two used to be separate top-level
           nav entries for 49 and 133 lines of page. -->
      <header class="flex flex-col gap-5 lg:flex-row lg:items-end lg:justify-between">
        <div class="max-w-2xl">
          <p class="text-xs font-bold uppercase tracking-[0.25em] ws-accent">{{ $t('agents.eyebrow') }}</p>
          <h1 class="mt-3 text-4xl font-bold ws-title">{{ $t('agents.title') }}</h1>
          <p class="mt-3 ws-muted">{{ $t('agents.subtitle') }}</p>
        </div>
        <div class="flex flex-wrap gap-2">
          <button
            v-for="tab in tabs"
            :key="tab.key"
            type="button"
            class="ws-chip !px-4 !py-2 !text-sm"
            :class="{ 'ws-chip-active': activeTab === tab.key }"
            @click="activeTab = tab.key"
          >{{ tab.label }}</button>
        </div>
      </header>

      <!-- Agent store -->
      <section v-show="activeTab === 'store'" class="mt-10">
        <div v-if="listings.length" class="grid gap-5 md:grid-cols-2 xl:grid-cols-3">
          <article v-for="listing in listings" :key="listing.id" class="pc-card flex flex-col gap-4">
            <div class="flex items-start justify-between gap-3">
              <div class="min-w-0">
                <h2 class="text-lg font-semibold ws-title">{{ listing.name }}</h2>
                <p class="mt-0.5 text-xs ws-accent">{{ listing.role_title || $t('agents.aiEmployee') }}</p>
              </div>
              <span class="shrink-0 rounded-full bg-emerald-500/15 px-2 py-1 text-[10px] font-semibold text-emerald-700 dark:text-emerald-300">
                {{ $t('agents.reviewed') }}
              </span>
            </div>
            <p class="line-clamp-3 text-sm ws-muted">{{ listing.description || $t('agents.fallbackDesc') }}</p>
            <div v-if="listing.workflows?.length" class="flex flex-wrap gap-1">
              <span
                v-for="workflow in listing.workflows"
                :key="workflow"
                class="rounded px-2 py-1 font-mono text-[10px] ws-soft ws-faint"
              >{{ workflow }}</span>
            </div>
            <div class="mt-auto flex items-center justify-between border-t ws-hairline pt-4">
              <span class="font-semibold ws-title">{{ priceLabel(listing) }}</span>
              <button class="btn-primary !px-4 !py-2 text-sm" @click="install(listing)">
                {{ $t('agents.install') }}
              </button>
            </div>
          </article>
        </div>
        <p v-else class="mt-10 text-center text-sm ws-muted">{{ $t('agents.emptyStore') }}</p>

        <div v-if="isLoggedIn && installations.length" class="mt-12">
          <h2 class="text-xl font-semibold ws-title">{{ $t('agents.myAgents') }}</h2>
          <div class="mt-4 grid gap-3 md:grid-cols-2">
            <div
              v-for="item in installations"
              :key="item.id"
              class="pc-card flex items-center justify-between gap-4 !p-4"
            >
              <div class="min-w-0">
                <p class="truncate font-medium ws-title">{{ item.name }}</p>
                <p class="truncate text-xs ws-muted">
                  {{ $t('agents.installMeta', { status: item.status, workspace: item.workspace_id }) }}
                </p>
              </div>
              <button v-if="item.status === 'installed'" class="text-xs text-red-400" @click="uninstall(item)">
                {{ $t('agents.uninstall') }}
              </button>
            </div>
          </div>
        </div>
      </section>

      <!-- Developer onboarding -->
      <section v-show="activeTab === 'build'" class="mt-10 grid gap-10 lg:grid-cols-[1.1fr_.9fr] lg:items-start">
        <div>
          <h2 class="text-2xl font-bold ws-title">{{ $t('agents.buildTitle') }}</h2>
          <p class="mt-4 ws-muted">{{ $t('agents.buildSubtitle') }}</p>
          <div class="mt-8 grid gap-4">
            <article v-for="step in buildSteps" :key="step.title" class="pc-card flex gap-4 !p-5">
              <span class="font-mono text-sm ws-accent">{{ step.index }}</span>
              <div>
                <h3 class="font-semibold ws-title">{{ step.title }}</h3>
                <p class="mt-1 text-sm ws-muted">{{ step.body }}</p>
              </div>
            </article>
          </div>
          <NuxtLink to="/developers/listings" class="btn-primary mt-8 inline-block">
            {{ $t('agents.submitAgent') }}
          </NuxtLink>
        </div>

        <div class="pc-card">
          <div class="flex items-center justify-between">
            <h3 class="font-semibold ws-title">
              {{ $t('agents.manifestTitle', { version: manifest.manifest_version || '1.0' }) }}
            </h3>
            <span class="text-xs text-emerald-600 dark:text-emerald-300">{{ $t('agents.governed') }}</span>
          </div>
          <pre class="mt-5 overflow-x-auto rounded-lg p-4 text-xs ws-sunken ws-muted">{{ JSON.stringify(manifest.example || {}, null, 2) }}</pre>
        </div>
      </section>

      <p v-if="message" class="mt-6 text-sm text-emerald-600 dark:text-emerald-300">{{ message }}</p>
      <p v-if="error" class="mt-6 text-sm text-red-400">{{ error }}</p>
    </div>
  </div>
</template>

<script setup lang="ts">
const { t } = useI18n()
const { apiFetch } = useApi()
const { isLoggedIn } = useAuth()
const { activeWorkspaceId, loadAccess } = usePortalManifest()

const activeTab = ref<'store' | 'build'>('store')
const listings = ref<any[]>([])
const installations = ref<any[]>([])
const manifest = ref<any>({})
const message = ref('')
const error = ref('')

const tabs = computed(() => [
  { key: 'store' as const, label: t('agents.tabStore') },
  { key: 'build' as const, label: t('agents.tabBuild') },
])

const buildSteps = computed(() => [
  { index: '01', title: t('agents.step1Title'), body: t('agents.step1Desc') },
  { index: '02', title: t('agents.step2Title'), body: t('agents.step2Desc') },
  { index: '03', title: t('agents.step3Title'), body: t('agents.step3Desc') },
])

function priceLabel(listing: any) {
  if (listing.price_monthly == null) return t('agents.included')
  return t('agents.perMonth', { price: listing.price_monthly, currency: listing.currency })
}

async function loadInstallations() {
  if (!isLoggedIn.value || !activeWorkspaceId.value) return
  const res = await apiFetch<any>(`/marketplace/installations/my?workspace_id=${activeWorkspaceId.value}`)
  installations.value = res.items || []
}

async function install(listing: any) {
  if (!isLoggedIn.value) return navigateTo('/login?redirect=/agents')
  if (!activeWorkspaceId.value) {
    error.value = t('agents.selectWorkspaceInstall')
    return
  }
  try {
    await apiFetch(`/marketplace/listings/${listing.id}/install`, {
      method: 'POST',
      body: { workspace_id: activeWorkspaceId.value },
    })
    message.value = t('agents.installedOk', { name: listing.name })
    await loadInstallations()
  } catch (e: any) {
    error.value = e?.data?.detail || t('agents.installFailed')
  }
}

async function uninstall(item: any) {
  await apiFetch(`/marketplace/installations/${item.id}/uninstall`, { method: 'POST' })
  await loadInstallations()
}

onMounted(async () => {
  const [listingRes, manifestRes] = await Promise.allSettled([
    apiFetch<any>('/marketplace/listings'),
    apiFetch<any>('/developer/sdk/manifest'),
  ])
  if (listingRes.status === 'fulfilled') listings.value = listingRes.value.items || []
  if (manifestRes.status === 'fulfilled') manifest.value = manifestRes.value || {}
  if (isLoggedIn.value) {
    await loadAccess()
    await loadInstallations()
  }
})
</script>
