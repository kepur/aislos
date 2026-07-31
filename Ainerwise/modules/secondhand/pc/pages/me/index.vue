<template>
  <div class="mx-auto max-w-5xl px-4 py-10 sm:px-6 lg:px-8">
    <ClientOnly>
      <div v-if="!auth.isLoggedIn" class="card p-12 text-center">
        <p class="font-semibold text-slate-900">Sign in to see your items and deals</p>
        <NuxtLink to="/login?redirect=/me" class="btn-primary mt-4">Sign in</NuxtLink>
      </div>

      <div v-else>
        <div class="mb-8 flex flex-wrap items-center justify-between gap-4">
          <div>
            <h1 class="text-3xl font-bold tracking-tight text-slate-900">{{ auth.displayName }}</h1>
            <p class="mt-1 text-slate-500">Your listings, address requests and collections.</p>
          </div>
          <NuxtLink to="/sell" class="btn-primary whitespace-nowrap">List an item</NuxtLink>
        </div>

        <div class="mb-6 flex gap-1 border-b border-slate-200">
          <button
            v-for="t in tabs"
            :key="t.key"
            class="border-b-2 px-4 py-2.5 text-sm font-medium transition-colors"
            :class="tab === t.key ? 'border-brand-600 text-brand-700' : 'border-transparent text-slate-500 hover:text-slate-800'"
            @click="tab = t.key"
          >
            {{ t.label }}
            <span v-if="t.count" class="ml-1.5 rounded-full bg-slate-100 px-1.5 text-xs">{{ t.count }}</span>
          </button>
        </div>

        <!-- Selling -->
        <div v-if="tab === 'listings'" class="space-y-4">
          <p v-if="!listings.length" class="card p-10 text-center text-slate-500">
            You have not listed anything yet.
          </p>
          <div v-for="l in listings" :key="l.id" class="card p-5">
            <div class="flex flex-wrap items-start justify-between gap-4">
              <div class="min-w-0">
                <div class="flex items-center gap-2">
                  <span :class="`grade grade-${l.condition_grade}`">{{ l.condition_grade }}</span>
                  <NuxtLink :to="`/item/${l.id}`" class="font-semibold text-slate-900 hover:text-brand-700">{{ l.title }}</NuxtLink>
                  <span v-if="l.status === 'sold'" class="rounded-full bg-slate-200 px-2 py-0.5 text-xs font-bold text-slate-600">SOLD</span>
                </div>
                <p class="mt-1 text-sm text-slate-500">
                  {{ money(l.price_minor, l.currency) }} · {{ l.pickup_city || '—' }}
                </p>
              </div>
              <button class="btn-ghost !py-2 text-sm" @click="toggleRequests(l.id)">
                {{ openListing === l.id ? 'Hide' : 'Address requests' }}
              </button>
            </div>

            <!-- Disclosure queue -->
            <div v-if="openListing === l.id" class="mt-5 border-t border-slate-100 pt-5">
              <p v-if="!requests.length" class="text-sm text-slate-400">No one has asked for your address yet.</p>
              <div v-for="r in requests" :key="r.id" class="mb-2 flex flex-wrap items-center justify-between gap-3 rounded-xl bg-slate-50 p-3">
                <div class="min-w-0">
                  <p class="text-sm font-medium text-slate-900">{{ r.buyer_name }}</p>
                  <p v-if="r.message" class="text-xs text-slate-500">“{{ r.message }}”</p>
                  <p class="mt-0.5 text-xs text-slate-400">
                    {{ statusLabel(r.status) }}
                    <span v-if="r.disclosed_fields?.length"> · shared: {{ r.disclosed_fields.join(', ') }}</span>
                  </p>
                </div>
                <div class="flex gap-2">
                  <button
                    v-if="r.status !== 'granted'"
                    class="btn-primary !px-3 !py-1.5 text-xs"
                    :disabled="busy"
                    @click="grant(r.id)"
                  >Share address</button>
                  <button
                    v-else
                    class="btn-ghost !px-3 !py-1.5 text-xs !text-rose-600"
                    :disabled="busy"
                    @click="revoke(r.id)"
                  >Withdraw</button>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Buying -->
        <div v-else-if="tab === 'buying'" class="space-y-3">
          <p v-if="!deals.buying.length" class="card p-10 text-center text-slate-500">
            Nothing reserved yet. <NuxtLink to="/" class="font-medium text-brand-700 hover:underline">Browse items</NuxtLink>
          </p>
          <NuxtLink
            v-for="d in deals.buying"
            :key="d.id"
            :to="`/item/${d.listing_id}`"
            class="card flex flex-wrap items-center justify-between gap-4 p-5 transition-colors hover:border-brand-300"
          >
            <div>
              <p class="font-semibold text-slate-900">{{ money(d.agreed_price_minor, d.currency) }}</p>
              <p class="mt-0.5 text-sm text-slate-500">{{ dealLabel(d) }}</p>
            </div>
            <span class="rounded-full px-3 py-1 text-xs font-semibold" :class="dealClass(d.status)">
              {{ dealStatusLabel(d.status) }}
            </span>
          </NuxtLink>
        </div>

        <!-- Sold -->
        <div v-else class="space-y-3">
          <p v-if="!deals.selling.length" class="card p-10 text-center text-slate-500">No sales yet.</p>
          <div v-for="d in deals.selling" :key="d.id" class="card flex flex-wrap items-center justify-between gap-4 p-5">
            <div>
              <p class="font-semibold text-slate-900">{{ money(d.agreed_price_minor, d.currency) }}</p>
              <p class="mt-0.5 text-sm text-slate-500">{{ dealLabel(d) }}</p>
            </div>
            <span class="rounded-full px-3 py-1 text-xs font-semibold" :class="dealClass(d.status)">
              {{ dealStatusLabel(d.status) }}
            </span>
          </div>
        </div>
      </div>
    </ClientOnly>
  </div>
</template>

<script setup lang="ts">
const auth = useAuthStore()
const api = useApi()
const money = useMoney()

const listings = ref<any[]>([])
const deals = ref<{ buying: any[]; selling: any[] }>({ buying: [], selling: [] })
const requests = ref<any[]>([])
const openListing = ref<string | null>(null)
const tab = ref('listings')
const busy = ref(false)

const tabs = computed(() => [
  { key: 'listings', label: 'My listings', count: listings.value.length },
  { key: 'buying', label: 'Buying', count: deals.value.buying.length },
  { key: 'selling', label: 'Sold', count: deals.value.selling.length },
])

function statusLabel(s: string) {
  return { requested: 'Waiting for you', granted: 'Address shared', revoked: 'Withdrawn' }[s] || s
}
function dealStatusLabel(s: string) {
  return { reserved: 'Reserved', picked_up: 'Collected', cancelled: 'Cancelled' }[s] || s
}
function dealClass(s: string) {
  return {
    reserved: 'bg-amber-100 text-amber-700',
    picked_up: 'bg-emerald-100 text-emerald-700',
    cancelled: 'bg-slate-100 text-slate-500',
  }[s] || 'bg-slate-100 text-slate-500'
}
function dealLabel(d: any) {
  if (d.status === 'picked_up' && d.picked_up_at) {
    return `Collected ${new Date(d.picked_up_at).toLocaleDateString()}${d.payment_method ? ` · paid ${d.payment_method.toLowerCase().replace('_', ' ')}` : ''}`
  }
  return `Created ${new Date(d.created_at).toLocaleDateString()}`
}

async function loadAll() {
  const [mine, myDeals] = await Promise.all([
    api<any>('/secondhand/me/listings').catch(() => ({ items: [] })),
    api<any>('/secondhand/me/deals').catch(() => ({ buying: [], selling: [] })),
  ])
  listings.value = mine.items || []
  deals.value = myDeals
}

async function toggleRequests(listingId: string) {
  if (openListing.value === listingId) {
    openListing.value = null
    return
  }
  openListing.value = listingId
  const data = await api<any>(`/secondhand/listings/${listingId}/disclosures`).catch(() => ({ items: [] }))
  requests.value = data.items || []
}

async function act(fn: () => Promise<any>) {
  busy.value = true
  try {
    await fn()
    if (openListing.value) {
      const id = openListing.value
      openListing.value = null
      await toggleRequests(id)
    }
  } finally {
    busy.value = false
  }
}

const grant = (id: string) =>
  act(() => api(`/secondhand/disclosures/${id}/grant`, { method: 'POST', body: { fields: ['address', 'phone', 'note'] } }))

const revoke = (id: string) => act(() => api(`/secondhand/disclosures/${id}/revoke`, { method: 'POST' }))

onMounted(async () => {
  auth.hydrate()
  await nextTick()
  if (auth.isLoggedIn) await loadAll()
})
</script>
