<template>
  <div>
    <!-- Hero -->
    <section class="border-b border-slate-200 bg-white">
      <div class="mx-auto max-w-7xl px-4 py-12 sm:px-6 lg:px-8 lg:py-16">
        <h1 class="max-w-3xl text-3xl font-bold tracking-tight text-slate-900 lg:text-5xl">
          Good gear, second time around.
        </h1>
        <p class="mt-4 max-w-2xl text-lg leading-relaxed text-slate-600">
          Graded condition, checked serial numbers, and collection in person — no customs,
          no waiting. You pay the seller directly when you pick it up.
        </p>

        <div class="mt-8 flex flex-col gap-3 sm:flex-row">
          <div class="relative flex-1">
            <UIcon
              name="i-heroicons-magnifying-glass"
              class="pointer-events-none absolute left-4 top-1/2 h-5 w-5 -translate-y-1/2 text-slate-400"
            />
            <input
              v-model="filters.keyword"
              type="text"
              placeholder="What are you looking for? e.g. iPhone, drill, monitor"
              class="input !py-3.5 !pl-11 !text-base"
              @keyup.enter="reload"
            />
          </div>
          <button class="btn-primary !px-8 !py-3.5" @click="reload">Search</button>
        </div>

        <div class="mt-6 flex flex-wrap items-center gap-3 text-sm text-slate-500">
          <UIcon name="i-heroicons-shield-check" class="h-5 w-5 text-brand-600" />
          <span>Serial numbers logged</span>
          <span class="text-slate-300">·</span>
          <span>Address shared only when the seller approves you</span>
          <span class="text-slate-300">·</span>
          <span>Platform never holds your money</span>
        </div>
      </div>
    </section>

    <div class="mx-auto max-w-7xl gap-8 px-4 py-8 sm:px-6 lg:flex lg:px-8">
      <!-- Filters -->
      <aside class="mb-6 w-full flex-shrink-0 lg:mb-0 lg:w-60">
        <div class="card sticky top-24 p-5">
          <h2 class="mb-4 text-sm font-semibold text-slate-900">Filter</h2>

          <p class="label">Condition</p>
          <div class="mb-5 space-y-1.5">
            <button
              :class="chip(!filters.condition)"
              @click="setCondition('')"
            >Any condition</button>
            <button
              v-for="g in CONDITION_GRADES"
              :key="g.code"
              :class="chip(filters.condition === g.code)"
              @click="setCondition(g.code)"
            >
              <span :class="`grade grade-${g.code} mr-2`">{{ g.code }}</span>{{ g.label.split('—')[1] }}
            </button>
          </div>

          <label class="label" for="city">City</label>
          <input id="city" v-model="filters.city" class="input mb-4" placeholder="Beograd" @keyup.enter="reload" />

          <label class="label" for="pmax">Max price</label>
          <input id="pmax" v-model.number="maxPrice" type="number" min="0" class="input mb-4" placeholder="e.g. 500" @keyup.enter="reload" />

          <button class="btn-primary w-full" @click="reload">Apply</button>
          <button class="mt-2 w-full text-xs text-slate-400 hover:text-slate-600" @click="clearFilters">Clear all</button>
        </div>
      </aside>

      <!-- Results -->
      <section class="min-w-0 flex-1">
        <div class="mb-4 flex items-center justify-between gap-4">
          <p class="text-sm text-slate-500">
            <span v-if="!pending">{{ total }} item{{ total === 1 ? '' : 's' }}</span>
            <span v-else>Loading…</span>
          </p>
          <select v-model="filters.sort" class="input !w-auto !py-2" @change="reload">
            <option value="newest">Newest first</option>
            <option value="price_asc">Price: low to high</option>
            <option value="price_desc">Price: high to low</option>
            <option value="condition">Best condition</option>
          </select>
        </div>

        <div v-if="pending && !items.length" class="grid grid-cols-2 gap-4 md:grid-cols-3">
          <div v-for="i in 6" :key="i" class="card animate-pulse p-4">
            <div class="mb-3 aspect-square rounded-xl bg-slate-100"></div>
            <div class="mb-2 h-4 w-3/4 rounded bg-slate-200"></div>
            <div class="h-3 w-1/2 rounded bg-slate-100"></div>
          </div>
        </div>

        <div v-else-if="error" class="card p-8 text-center">
          <p class="font-semibold text-rose-700">Could not load listings</p>
          <p class="mt-1 text-sm text-slate-500">{{ error }}</p>
          <button class="btn-ghost mt-4" @click="reload">Try again</button>
        </div>

        <div v-else-if="!items.length" class="card p-12 text-center">
          <div class="mb-3 text-4xl">🔍</div>
          <p class="font-semibold text-slate-900">Nothing matches yet</p>
          <p class="mt-1 text-sm text-slate-500">
            Try a broader search — or
            <NuxtLink to="/sell" class="font-medium text-brand-700 hover:underline">list something yourself</NuxtLink>.
          </p>
        </div>

        <div v-else class="grid grid-cols-2 gap-4 md:grid-cols-3">
          <NuxtLink
            v-for="item in items"
            :key="item.id"
            :to="`/item/${item.id}`"
            class="card group overflow-hidden transition-all hover:border-brand-300 hover:shadow-md"
          >
            <div class="relative aspect-square overflow-hidden bg-slate-100">
              <img
                v-if="item.images?.[0]"
                :src="item.images[0]"
                :alt="item.title"
                class="h-full w-full object-cover transition-transform duration-300 group-hover:scale-105"
              />
              <div v-else class="flex h-full w-full items-center justify-center bg-gradient-to-br from-brand-50 to-slate-100">
                <UIcon name="i-heroicons-cube" class="h-10 w-10 text-brand-300" />
              </div>
              <span :class="`grade grade-${item.condition_grade} absolute left-3 top-3 shadow-sm`">
                {{ item.condition_grade }}
              </span>
            </div>
            <div class="p-4">
              <h3 class="line-clamp-2 text-sm font-semibold leading-tight text-slate-900 group-hover:text-brand-700">
                {{ item.title }}
              </h3>
              <p class="mt-2 text-lg font-bold text-slate-900">{{ money(item.price_minor, item.currency) }}</p>
              <p class="mt-1 flex items-center gap-1 text-xs text-slate-400">
                <UIcon name="i-heroicons-map-pin" class="h-3.5 w-3.5" />
                {{ item.pickup_city || 'Location on request' }}
              </p>
            </div>
          </NuxtLink>
        </div>

        <div v-if="hasNext" class="mt-8 text-center">
          <button class="btn-ghost" :disabled="pending" @click="loadMore">
            {{ pending ? 'Loading…' : 'Load more' }}
          </button>
        </div>
      </section>
    </div>
  </div>
</template>

<script setup lang="ts">
const api = useApi()
const money = useMoney()

const items = ref<any[]>([])
const total = ref(0)
const page = ref(1)
const hasNext = ref(false)
const pending = ref(true)
const error = ref('')
const maxPrice = ref<number | null>(null)

const filters = reactive({ keyword: '', condition: '', city: '', sort: 'newest' })

function chip(active: boolean) {
  return [
    'flex w-full items-center rounded-lg px-3 py-2 text-left text-sm transition-colors',
    active ? 'bg-brand-50 font-medium text-brand-700' : 'text-slate-600 hover:bg-slate-50',
  ]
}

function setCondition(code: string) {
  filters.condition = code
  reload()
}

function clearFilters() {
  filters.keyword = ''
  filters.condition = ''
  filters.city = ''
  maxPrice.value = null
  reload()
}

async function load(reset = false) {
  pending.value = true
  error.value = ''
  if (reset) {
    page.value = 1
    items.value = []
  }
  try {
    const params: Record<string, any> = { page: page.value, page_size: 24, sort: filters.sort }
    const session = useSessionId()
    if (session) params.session_id = session
    if (filters.keyword) params.keyword = filters.keyword
    if (filters.condition) params.condition = filters.condition
    if (filters.city) params.city = filters.city
    if (maxPrice.value) params.price_max_minor = Math.round(maxPrice.value * 100)

    const data = await api<any>('/secondhand/listings', { params })
    items.value = reset ? data.items : [...items.value, ...data.items]
    total.value = data.total
    hasNext.value = data.has_next
  } catch (err: any) {
    error.value = apiErrorMessage(err, 'Please try again')
  } finally {
    pending.value = false
  }
}

function reload() {
  load(true)
}

function loadMore() {
  page.value += 1
  load(false)
}

onMounted(() => load(true))
</script>
