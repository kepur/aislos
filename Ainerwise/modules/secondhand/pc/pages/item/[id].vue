<template>
  <div class="mx-auto max-w-6xl px-4 py-8 sm:px-6 lg:px-8">
    <NuxtLink to="/" class="mb-6 inline-flex items-center gap-1.5 text-sm text-slate-500 hover:text-brand-700">
      <UIcon name="i-heroicons-arrow-left" class="h-4 w-4" /> Back to browse
    </NuxtLink>

    <div v-if="pending" class="card animate-pulse p-8">
      <div class="h-64 rounded-xl bg-slate-100"></div>
    </div>

    <div v-else-if="loadError" class="card p-12 text-center">
      <p class="font-semibold text-rose-700">{{ loadError }}</p>
      <NuxtLink to="/" class="btn-ghost mt-4">Back to browse</NuxtLink>
    </div>

    <div v-else-if="item" class="grid gap-8 lg:grid-cols-[1.1fr_1fr]">
      <!-- Gallery + condition -->
      <div>
        <div class="card overflow-hidden">
          <div class="aspect-[4/3] bg-slate-100">
            <img v-if="activeImage" :src="activeImage" :alt="item.title" class="h-full w-full object-cover" />
            <div v-else class="flex h-full w-full items-center justify-center bg-gradient-to-br from-brand-50 to-slate-100">
              <UIcon name="i-heroicons-cube" class="h-16 w-16 text-brand-300" />
            </div>
          </div>
        </div>

        <div v-if="item.images?.length > 1" class="mt-3 flex gap-2">
          <button
            v-for="(img, i) in item.images"
            :key="i"
            class="h-16 w-16 overflow-hidden rounded-lg border-2 transition-colors"
            :class="activeImage === img ? 'border-brand-500' : 'border-transparent'"
            @click="activeImage = img"
          >
            <img :src="img" class="h-full w-full object-cover" alt="" />
          </button>
        </div>

        <!-- Condition & provenance -->
        <div class="card mt-6 p-6">
          <h2 class="mb-4 font-semibold text-slate-900">Condition &amp; history</h2>
          <dl class="grid grid-cols-2 gap-4 text-sm">
            <div>
              <dt class="text-slate-500">Grade</dt>
              <dd class="mt-1 flex items-center gap-2">
                <span :class="`grade grade-${item.condition_grade}`">{{ item.condition_grade }}</span>
                <span class="text-slate-700">{{ gradeLabel }}</span>
              </dd>
            </div>
            <div v-if="item.purchase_year">
              <dt class="text-slate-500">Bought in</dt>
              <dd class="mt-1 font-medium text-slate-900">{{ item.purchase_year }}</dd>
            </div>
            <div v-if="item.warranty_left_months">
              <dt class="text-slate-500">Warranty left</dt>
              <dd class="mt-1 font-medium text-slate-900">{{ item.warranty_left_months }} months</dd>
            </div>
            <div>
              <dt class="text-slate-500">Original packaging</dt>
              <dd class="mt-1 font-medium text-slate-900">{{ item.original_packaging ? 'Yes' : 'No' }}</dd>
            </div>
            <div v-if="item.has_serial" class="col-span-2">
              <dt class="text-slate-500">Provenance</dt>
              <dd class="mt-1 flex items-center gap-1.5 font-medium text-emerald-700">
                <UIcon name="i-heroicons-shield-check" class="h-4 w-4" />
                {{ item.serial_type }} recorded with the platform
              </dd>
            </div>
          </dl>

          <p v-if="item.usage_note" class="mt-4 border-t border-slate-100 pt-4 text-sm text-slate-600">
            {{ item.usage_note }}
          </p>

          <div v-if="item.defects?.length" class="mt-4 border-t border-slate-100 pt-4">
            <p class="mb-2 text-sm font-medium text-slate-700">Declared faults</p>
            <ul class="space-y-1.5">
              <li v-for="(d, i) in item.defects" :key="i" class="flex gap-2 text-sm text-slate-600">
                <UIcon name="i-heroicons-exclamation-triangle" class="mt-0.5 h-4 w-4 flex-shrink-0 text-amber-500" />
                <span><span v-if="d.type" class="font-medium">{{ d.type }}:</span> {{ d.note }}</span>
              </li>
            </ul>
          </div>
        </div>

        <div v-if="item.description" class="card mt-6 p-6">
          <h2 class="mb-3 font-semibold text-slate-900">Description</h2>
          <p class="whitespace-pre-line text-sm leading-relaxed text-slate-600">{{ item.description }}</p>
        </div>
      </div>

      <!-- Buy panel -->
      <div>
        <div class="card sticky top-24 p-6">
          <span v-if="item.status === 'sold'" class="mb-3 inline-block rounded-full bg-slate-200 px-3 py-1 text-xs font-bold text-slate-600">SOLD</span>
          <h1 class="text-2xl font-bold leading-tight text-slate-900">{{ item.title }}</h1>
          <p class="mt-3 text-3xl font-bold text-slate-900">{{ money(item.price_minor, item.currency) }}</p>

          <div class="mt-4 space-y-2 text-sm text-slate-600">
            <p class="flex items-center gap-2">
              <UIcon name="i-heroicons-map-pin" class="h-4 w-4 text-slate-400" />
              {{ [item.pickup_area, item.pickup_city, item.pickup_country].filter(Boolean).join(', ') || 'Location shared after approval' }}
            </p>
            <p class="flex items-center gap-2">
              <UIcon name="i-heroicons-truck" class="h-4 w-4 text-slate-400" />
              {{ fulfillmentLabel }}
            </p>
            <p v-if="item.seller_name" class="flex items-center gap-2">
              <UIcon name="i-heroicons-user" class="h-4 w-4 text-slate-400" />
              {{ item.seller_name }}
            </p>
          </div>

          <hr class="my-6 border-slate-100" />

          <!-- Sold -->
          <div v-if="item.status === 'sold'" class="rounded-xl bg-slate-50 p-4 text-sm text-slate-600">
            This item has been sold.
            <NuxtLink to="/" class="font-medium text-brand-700 hover:underline">Browse similar items</NuxtLink>
          </div>

          <!-- Not signed in -->
          <div v-else-if="!auth.isLoggedIn">
            <p class="mb-3 text-sm text-slate-600">Sign in to contact the seller and arrange collection.</p>
            <NuxtLink :to="`/login?redirect=/item/${route.params.id}`" class="btn-primary w-full">Sign in to continue</NuxtLink>
          </div>

          <!-- Own listing -->
          <div v-else-if="state?.role === 'seller'" class="rounded-xl bg-brand-50 p-4 text-sm text-brand-800">
            This is your listing.
            <NuxtLink to="/me" class="font-medium underline">Manage it and review address requests</NuxtLink>
          </div>

          <!-- Buyer flow -->
          <div v-else class="space-y-4">
            <!-- Step 1: request -->
            <div v-if="state?.status === 'none' || state?.status === 'revoked'">
              <div class="mb-3 rounded-xl bg-slate-50 p-3 text-xs leading-relaxed text-slate-500">
                The seller's exact address stays hidden until they approve you. They can withdraw it later.
              </div>
              <textarea
                v-model="message"
                rows="2"
                class="input mb-3"
                placeholder="Optional message — e.g. “Could I collect this evening?”"
              />
              <button class="btn-primary w-full" :disabled="busy" @click="requestAddress">
                {{ busy ? 'Sending…' : 'Ask seller for pickup address' }}
              </button>
            </div>

            <!-- Step 2: waiting -->
            <div v-else-if="state?.status === 'requested'" class="rounded-xl bg-amber-50 p-4">
              <p class="flex items-center gap-2 text-sm font-medium text-amber-800">
                <UIcon name="i-heroicons-clock" class="h-5 w-5" /> Waiting for the seller to approve
              </p>
              <p class="mt-1 text-xs text-amber-700">You'll see the pickup address here once they do.</p>
            </div>

            <!-- Step 3: granted -->
            <template v-else-if="state?.status === 'granted'">
              <div class="rounded-xl border border-brand-200 bg-brand-50 p-4">
                <p class="mb-2 flex items-center gap-2 text-sm font-semibold text-brand-800">
                  <UIcon name="i-heroicons-check-badge" class="h-5 w-5" /> Seller approved you
                </p>
                <dl class="space-y-2 text-sm">
                  <div v-if="pickup?.pickup_address">
                    <dt class="text-xs text-brand-700">Pickup address</dt>
                    <dd class="font-medium text-slate-900">{{ pickup.pickup_address }}</dd>
                  </div>
                  <div v-if="pickup?.contact_phone">
                    <dt class="text-xs text-brand-700">Phone</dt>
                    <dd class="font-medium text-slate-900">{{ pickup.contact_phone }}</dd>
                  </div>
                  <div v-if="pickup?.pickup_note">
                    <dt class="text-xs text-brand-700">Note</dt>
                    <dd class="text-slate-700">{{ pickup.pickup_note }}</dd>
                  </div>
                </dl>
                <p class="mt-3 text-xs text-brand-700">Please keep this private — it was shared with you only.</p>
              </div>

              <!-- Reserve / confirm -->
              <div v-if="!state.deal">
                <button class="btn-primary w-full" :disabled="busy" @click="reserve">
                  {{ busy ? 'Reserving…' : 'Reserve this item' }}
                </button>
                <p class="mt-2 text-center text-xs text-slate-400">Holds it while you arrange collection.</p>
              </div>

              <div v-else-if="state.deal.status === 'reserved'" class="space-y-3">
                <div class="rounded-xl bg-slate-50 p-3 text-sm text-slate-600">
                  Reserved for you at <strong>{{ money(state.deal.agreed_price_minor, state.deal.currency) }}</strong>.
                  Pay the seller directly when you collect.
                </div>
                <select v-model="payMethod" class="input">
                  <option value="CASH">Paid in cash</option>
                  <option value="BANK_TRANSFER">Paid by bank transfer</option>
                  <option value="OTHER">Paid another way</option>
                </select>
                <input v-model="payRef" class="input" placeholder="Reference (optional) — e.g. transfer ID" />
                <button class="btn-primary w-full" :disabled="busy" @click="confirmPickup">
                  {{ busy ? 'Saving…' : "I've collected it" }}
                </button>
                <button class="w-full text-xs text-slate-400 hover:text-rose-600" :disabled="busy" @click="cancelDeal">
                  Cancel reservation
                </button>
              </div>

              <div v-else-if="state.deal.status === 'picked_up'" class="rounded-xl bg-emerald-50 p-4 text-sm text-emerald-800">
                <p class="flex items-center gap-2 font-semibold">
                  <UIcon name="i-heroicons-check-circle" class="h-5 w-5" /> Collected
                </p>
                <p class="mt-1 text-xs">Recorded on {{ new Date(state.deal.picked_up_at).toLocaleDateString() }}. Enjoy it!</p>
              </div>
            </template>
          </div>

          <p v-if="actionError" class="mt-3 text-sm text-rose-600">{{ actionError }}</p>

          <p class="mt-6 border-t border-slate-100 pt-4 text-xs leading-relaxed text-slate-400">
            2Hands never holds your money. You pay the seller directly at collection — we keep the record.
          </p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
const route = useRoute()
const auth = useAuthStore()
const api = useApi()
const money = useMoney()

const item = ref<any>(null)
const state = ref<any>(null)
const pickup = ref<any>(null)
const activeImage = ref<string | null>(null)
const pending = ref(true)
const busy = ref(false)
const loadError = ref('')
const actionError = ref('')
const message = ref('')
const payMethod = ref('CASH')
const payRef = ref('')

const gradeLabel = computed(
  () => CONDITION_GRADES.find((g) => g.code === item.value?.condition_grade)?.label.split('—')[1]?.trim() || ''
)
const fulfillmentLabel = computed(
  () => FULFILLMENT_MODES.find((f) => f.code === item.value?.fulfillment_mode)?.label || 'Collect from seller'
)

async function loadItem() {
  pending.value = true
  try {
    item.value = await api<any>(`/secondhand/listings/${route.params.id}`)
    activeImage.value = item.value.images?.[0] || null
  } catch (err: any) {
    loadError.value = apiErrorMessage(err, 'This listing is no longer available')
  } finally {
    pending.value = false
  }
}

async function loadState() {
  if (!auth.isLoggedIn) {
    state.value = null
    return
  }
  try {
    state.value = await api<any>(`/secondhand/listings/${route.params.id}/my-disclosure`)
    if (state.value?.status === 'granted' || state.value?.role === 'seller') {
      pickup.value = await api<any>(`/secondhand/listings/${route.params.id}/pickup-details`)
    }
  } catch {
    state.value = { role: 'buyer', status: 'none' }
  }
}

async function act(fn: () => Promise<any>) {
  busy.value = true
  actionError.value = ''
  try {
    await fn()
    await Promise.all([loadItem(), loadState()])
  } catch (err: any) {
    actionError.value = apiErrorMessage(err)
  } finally {
    busy.value = false
  }
}

const requestAddress = () =>
  act(() =>
    api(`/secondhand/listings/${route.params.id}/disclosure-request`, {
      method: 'POST',
      body: { message: message.value || null },
    })
  )

const reserve = () =>
  act(() => api(`/secondhand/listings/${route.params.id}/reserve`, { method: 'POST', body: {} }))

const confirmPickup = () =>
  act(() =>
    api(`/secondhand/deals/${state.value.deal.id}/confirm-pickup`, {
      method: 'POST',
      body: { payment_method: payMethod.value, payment_reference: payRef.value || null },
    })
  )

const cancelDeal = () =>
  act(() => api(`/secondhand/deals/${state.value.deal.id}/cancel`, { method: 'POST' }))

onMounted(async () => {
  auth.hydrate()
  await loadItem()
  await loadState()
})
</script>
