<template>
  <div class="agents-page">
    <!-- Hero: the roster is the product, so the count and the roles lead. -->
    <header class="agents-hero">
      <div class="mx-auto max-w-7xl px-4 py-14 sm:px-6 lg:px-8">
        <div class="grid gap-10 lg:grid-cols-[1.15fr_.85fr] lg:items-center">
          <div>
            <p class="text-xs font-bold uppercase tracking-[0.24em] ws-accent">{{ $t('agents.eyebrow') }}</p>
            <h1 class="mt-3 text-4xl font-bold leading-[1.08] ws-title lg:text-5xl">{{ $t('agents.title') }}</h1>
            <p class="mt-4 max-w-xl leading-7 ws-muted">{{ $t('agents.subtitle') }}</p>

            <div class="mt-8 flex flex-wrap gap-2">
              <button
                v-for="tab in tabs"
                :key="tab.key"
                type="button"
                class="agents-tab"
                :class="{ 'agents-tab--on': activeTab === tab.key }"
                @click="activeTab = tab.key"
              >
                <UIcon :name="tab.icon" class="h-4 w-4" />
                {{ tab.label }}
              </button>
            </div>
          </div>

          <!-- Roster preview doubles as the visual: real agent roles, not an
               abstract illustration. -->
          <div class="agents-orbit">
            <div v-for="(agent, i) in listings.slice(0, 5)" :key="agent.id" class="agents-orbit__chip" :style="orbitStyle(i)">
              <span class="agents-orbit__dot"></span>
              {{ agent.role_title || agent.name }}
            </div>
            <div class="agents-orbit__core">
              <p class="text-2xl font-bold ws-title">{{ listings.length }}</p>
              <p class="mt-0.5 text-[11px] font-semibold uppercase tracking-[0.14em] ws-faint">
                {{ $t('agents.reviewedAgents') }}
              </p>
            </div>
          </div>
        </div>
      </div>
    </header>

    <section class="mx-auto max-w-7xl px-4 pb-20 sm:px-6 lg:px-8">
      <!-- Store -->
      <div v-show="activeTab === 'store'">
        <div v-if="listings.length" class="grid gap-5 md:grid-cols-2 xl:grid-cols-3">
          <article v-for="agent in listings" :key="agent.id" class="agent-card">
            <div class="agent-card__head">
              <div class="agent-card__avatar">{{ (agent.name || '?').charAt(0) }}</div>
              <div class="min-w-0 flex-1">
                <h2 class="truncate text-base font-bold ws-title">{{ agent.name }}</h2>
                <p class="truncate text-xs ws-accent">{{ agent.role_title || $t('agents.aiEmployee') }}</p>
              </div>
              <span class="agent-card__seal">
                <UIcon name="i-heroicons-shield-check" class="h-3 w-3" />
                {{ $t('agents.reviewed') }}
              </span>
            </div>

            <p class="agent-card__desc">{{ agent.description || $t('agents.fallbackDesc') }}</p>

            <div v-if="agent.workflows?.length" class="agent-card__flows">
              <span v-for="workflow in agent.workflows.slice(0, 4)" :key="workflow" class="agent-flow">{{ workflow }}</span>
              <span v-if="agent.workflows.length > 4" class="agent-flow agent-flow--more">
                +{{ agent.workflows.length - 4 }}
              </span>
            </div>

            <div class="agent-card__foot">
              <div>
                <p class="text-sm font-bold ws-title">{{ priceLabel(agent) }}</p>
                <p class="text-[11px] ws-faint">{{ $t('agents.perWorkspace') }}</p>
              </div>
              <button class="agent-install" @click="install(agent)">
                {{ $t('agents.install') }}
                <UIcon name="i-heroicons-arrow-right" class="h-3.5 w-3.5" />
              </button>
            </div>
          </article>
        </div>
        <p v-else class="pc-card py-16 text-center text-sm ws-muted">{{ $t('agents.emptyStore') }}</p>

        <div v-if="isLoggedIn && installations.length" class="mt-14">
          <h2 class="text-lg font-bold ws-title">{{ $t('agents.myAgents') }}</h2>
          <div class="mt-4 grid gap-3 md:grid-cols-2">
            <div v-for="item in installations" :key="item.id" class="pc-card flex items-center justify-between gap-4 !p-4">
              <div class="flex min-w-0 items-center gap-3">
                <span class="agent-card__avatar !h-9 !w-9 !text-sm">{{ (item.name || '?').charAt(0) }}</span>
                <div class="min-w-0">
                  <p class="truncate text-sm font-semibold ws-title">{{ item.name }}</p>
                  <p class="truncate text-xs ws-faint">
                    {{ $t('agents.installMeta', { status: item.status, workspace: item.workspace_id }) }}
                  </p>
                </div>
              </div>
              <button v-if="item.status === 'installed'" class="text-xs text-red-500 hover:underline" @click="uninstall(item)">
                {{ $t('agents.uninstall') }}
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- Developer onboarding -->
      <div v-show="activeTab === 'build'" class="grid gap-10 lg:grid-cols-[1fr_1fr] lg:items-start">
        <div>
          <h2 class="text-2xl font-bold ws-title">{{ $t('agents.buildTitle') }}</h2>
          <p class="mt-3 leading-7 ws-muted">{{ $t('agents.buildSubtitle') }}</p>

          <ol class="mt-8 space-y-0">
            <li v-for="(step, i) in buildSteps" :key="step.title" class="build-step">
              <div class="build-step__marker">
                <span class="build-step__num">{{ step.index }}</span>
                <span v-if="i < buildSteps.length - 1" class="build-step__line"></span>
              </div>
              <div class="pb-8">
                <h3 class="font-bold ws-title">{{ step.title }}</h3>
                <p class="mt-1.5 text-sm leading-6 ws-muted">{{ step.body }}</p>
              </div>
            </li>
          </ol>

          <NuxtLink to="/developers/listings" class="btn-primary inline-flex items-center gap-2">
            {{ $t('agents.submitAgent') }}
            <UIcon name="i-heroicons-arrow-right" class="h-4 w-4" />
          </NuxtLink>
        </div>

        <div class="manifest-panel">
          <div class="manifest-panel__bar">
            <span class="manifest-dot manifest-dot--r"></span>
            <span class="manifest-dot manifest-dot--y"></span>
            <span class="manifest-dot manifest-dot--g"></span>
            <p class="ml-2 font-mono text-xs ws-faint">
              {{ $t('agents.manifestTitle', { version: manifest.manifest_version || '1.0' }) }}
            </p>
            <span class="ml-auto inline-flex items-center gap-1 text-[11px] font-semibold text-emerald-600 dark:text-emerald-400">
              <UIcon name="i-heroicons-lock-closed" class="h-3 w-3" />
              {{ $t('agents.governed') }}
            </span>
          </div>
          <pre class="manifest-panel__code">{{ JSON.stringify(manifest.example || {}, null, 2) }}</pre>
        </div>
      </div>

      <p v-if="message" class="mt-6 text-sm text-emerald-600 dark:text-emerald-400">{{ message }}</p>
      <p v-if="error" class="mt-6 text-sm text-red-500">{{ error }}</p>
    </section>
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
  { key: 'store' as const, icon: 'i-heroicons-squares-2x2', label: t('agents.tabStore') },
  { key: 'build' as const, icon: 'i-heroicons-code-bracket', label: t('agents.tabBuild') },
])

const buildSteps = computed(() => [
  { index: '01', title: t('agents.step1Title'), body: t('agents.step1Desc') },
  { index: '02', title: t('agents.step2Title'), body: t('agents.step2Desc') },
  { index: '03', title: t('agents.step3Title'), body: t('agents.step3Desc') },
])

// Fan the preview chips out down the right-hand side.
function orbitStyle(index: number) {
  const offsets = [
    { top: '4%', right: '6%' },
    { top: '26%', right: '30%' },
    { top: '50%', right: '2%' },
    { top: '70%', right: '26%' },
    { top: '88%', right: '10%' },
  ]
  return offsets[index] || {}
}

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

<style scoped>
.agents-hero {
  border-bottom: 1px solid var(--card-border);
  background:
    radial-gradient(circle at 82% 20%, var(--accent-soft), transparent 46%),
    linear-gradient(180deg, var(--surface-sunken), transparent);
}

.agents-tab {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  border-radius: 999px;
  border: 1px solid var(--hairline-soft);
  background: var(--card-bg);
  padding: 0.6rem 1.15rem;
  font-size: 0.9rem;
  font-weight: 600;
  color: var(--text-muted);
  transition: all 0.16s ease;
}
.agents-tab:hover { border-color: var(--accent); color: var(--accent); }
.agents-tab--on {
  border-color: var(--accent);
  background: var(--accent);
  color: var(--accent-contrast);
}

/* Roster preview */
.agents-orbit {
  position: relative;
  display: none;
  min-height: 20rem;
}
@media (min-width: 1024px) { .agents-orbit { display: block; } }
.agents-orbit__core {
  position: absolute;
  left: 8%;
  top: 38%;
  border-radius: 1.25rem;
  border: 1px solid var(--card-border);
  background: var(--card-bg);
  padding: 1.1rem 1.5rem;
  text-align: center;
  box-shadow: 0 16px 40px rgba(2, 6, 23, 0.1);
}
.agents-orbit__chip {
  position: absolute;
  display: inline-flex;
  align-items: center;
  gap: 0.45rem;
  border-radius: 999px;
  border: 1px solid var(--hairline-soft);
  background: var(--card-bg);
  padding: 0.4rem 0.85rem;
  font-size: 0.78rem;
  font-weight: 600;
  color: var(--text-muted);
  white-space: nowrap;
  box-shadow: 0 6px 18px rgba(2, 6, 23, 0.06);
}
.agents-orbit__dot {
  width: 0.4rem;
  height: 0.4rem;
  border-radius: 999px;
  background: var(--accent);
}

/* Agent cards */
.agent-card {
  display: flex;
  flex-direction: column;
  gap: 0.9rem;
  border-radius: 1.1rem;
  border: 1px solid var(--card-border);
  background: var(--card-bg);
  padding: 1.2rem;
  transition: border-color 0.18s ease, transform 0.18s ease, box-shadow 0.18s ease;
}
.agent-card:hover {
  border-color: var(--accent);
  transform: translateY(-2px);
  box-shadow: 0 14px 34px rgba(2, 6, 23, 0.1);
}
.agent-card__head { display: flex; align-items: center; gap: 0.75rem; }
.agent-card__avatar {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 2.5rem;
  height: 2.5rem;
  flex: none;
  border-radius: 0.8rem;
  background: var(--accent);
  color: var(--accent-contrast);
  font-weight: 800;
}
.agent-card__seal {
  display: inline-flex;
  align-items: center;
  gap: 0.25rem;
  flex: none;
  border-radius: 999px;
  background: rgba(16, 185, 129, 0.14);
  padding: 0.2rem 0.5rem;
  font-size: 0.65rem;
  font-weight: 700;
  color: #047857;
}
:global(.dark) .agent-card__seal { color: #6ee7b7; }

.agent-card__desc {
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
  font-size: 0.85rem;
  line-height: 1.6;
  color: var(--text-muted);
}
.agent-card__flows { display: flex; flex-wrap: wrap; gap: 0.3rem; }
.agent-flow {
  border-radius: 0.4rem;
  background: var(--surface-soft);
  padding: 0.15rem 0.45rem;
  font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
  font-size: 0.66rem;
  color: var(--text-faint);
}
.agent-flow--more { color: var(--accent); }

.agent-card__foot {
  margin-top: auto;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
  border-top: 1px solid var(--hairline-soft);
  padding-top: 0.9rem;
}
.agent-install {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  border-radius: 999px;
  background: var(--accent);
  padding: 0.45rem 0.95rem;
  font-size: 0.8rem;
  font-weight: 700;
  color: var(--accent-contrast);
  transition: filter 0.16s ease, transform 0.16s ease;
}
.agent-install:hover { filter: brightness(1.08); transform: translateX(1px); }

/* Build steps */
.build-step { display: flex; gap: 1rem; }
.build-step__marker { position: relative; display: flex; flex-direction: column; align-items: center; }
.build-step__num {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 2rem;
  height: 2rem;
  flex: none;
  border-radius: 999px;
  border: 1px solid var(--accent);
  background: var(--accent-soft);
  font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
  font-size: 0.72rem;
  font-weight: 700;
  color: var(--accent);
}
.build-step__line { flex: 1; width: 1px; background: var(--hairline-soft); }

/* Manifest panel styled as an editor pane */
.manifest-panel {
  overflow: hidden;
  border-radius: 1rem;
  border: 1px solid var(--card-border);
  background: var(--card-bg);
  box-shadow: 0 16px 40px rgba(2, 6, 23, 0.08);
}
.manifest-panel__bar {
  display: flex;
  align-items: center;
  gap: 0.35rem;
  border-bottom: 1px solid var(--hairline-soft);
  background: var(--surface-soft);
  padding: 0.7rem 0.9rem;
}
.manifest-dot { width: 0.6rem; height: 0.6rem; border-radius: 999px; }
.manifest-dot--r { background: #f87171; }
.manifest-dot--y { background: #fbbf24; }
.manifest-dot--g { background: #34d399; }
.manifest-panel__code {
  overflow-x: auto;
  margin: 0;
  padding: 1.1rem;
  font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
  font-size: 0.76rem;
  line-height: 1.7;
  color: var(--text-muted);
}
</style>
