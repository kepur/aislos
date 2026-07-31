<template>
  <div class="mx-auto max-w-3xl px-4 py-10 sm:px-6 lg:px-8">
    <h1 class="text-3xl font-bold tracking-tight text-slate-900">List an item</h1>
    <p class="mt-2 text-slate-600">Honest condition sells faster. Buyers see the grade and any faults up front.</p>

    <ClientOnly>
      <div v-if="!auth.isLoggedIn" class="card mt-8 p-8 text-center">
        <p class="font-semibold text-slate-900">Sign in to list an item</p>
        <NuxtLink to="/login?redirect=/sell" class="btn-primary mt-4">Sign in</NuxtLink>
      </div>

      <form v-else class="mt-8 space-y-6" @submit.prevent="submit">
        <!-- Basics -->
        <section class="card p-6">
          <h2 class="mb-4 font-semibold text-slate-900">The item</h2>
          <div class="space-y-4">
            <div>
              <label class="label" for="title">Title <span class="text-rose-500">*</span></label>
              <input id="title" v-model="form.title" class="input" required placeholder="e.g. iPhone 13 Pro 128GB, Graphite" />
            </div>
            <div>
              <label class="label" for="desc">Description</label>
              <textarea id="desc" v-model="form.description" rows="4" class="input"
                placeholder="What's included, why you're selling, anything a buyer should know." />
            </div>
            <div class="grid gap-4 sm:grid-cols-2">
              <div>
                <label class="label" for="price">Price ({{ currency }}) <span class="text-rose-500">*</span></label>
                <input id="price" v-model.number="price" type="number" min="0" step="0.01" class="input" required placeholder="450" />
              </div>
              <div>
                <label class="label" for="year">Year bought</label>
                <input id="year" v-model.number="form.purchase_year" type="number" min="1980" :max="thisYear" class="input" :placeholder="String(thisYear - 2)" />
              </div>
            </div>
          </div>
        </section>

        <!-- Condition -->
        <section class="card p-6">
          <h2 class="mb-1 font-semibold text-slate-900">Condition</h2>
          <p class="mb-4 text-sm text-slate-500">Grade it honestly — disputes almost always come from an over-graded item.</p>

          <div class="grid gap-2 sm:grid-cols-2">
            <button
              v-for="g in CONDITION_GRADES"
              :key="g.code"
              type="button"
              class="flex items-start gap-3 rounded-xl border p-3 text-left transition-colors"
              :class="form.condition_grade === g.code ? 'border-brand-400 bg-brand-50' : 'border-slate-200 hover:border-slate-300'"
              @click="form.condition_grade = g.code"
            >
              <span :class="`grade grade-${g.code} mt-0.5`">{{ g.code }}</span>
              <span>
                <span class="block text-sm font-medium text-slate-900">{{ g.label.split('—')[1].trim() }}</span>
                <span class="block text-xs text-slate-500">{{ g.hint }}</span>
              </span>
            </button>
          </div>

          <div class="mt-4 grid gap-4 sm:grid-cols-2">
            <div>
              <label class="label" for="warranty">Warranty left (months)</label>
              <input id="warranty" v-model.number="form.warranty_left_months" type="number" min="0" class="input" placeholder="0" />
            </div>
            <label class="flex cursor-pointer items-center gap-2 self-end pb-2.5">
              <input v-model="form.original_packaging" type="checkbox" class="h-4 w-4 rounded border-slate-300 text-brand-600" />
              <span class="text-sm text-slate-700">Has original packaging</span>
            </label>
          </div>

          <div class="mt-4">
            <label class="label">Faults to declare</label>
            <div v-for="(d, i) in form.defects" :key="i" class="mb-2 flex gap-2">
              <input v-model="d.type" class="input !w-36" placeholder="Type" />
              <input v-model="d.note" class="input flex-1" placeholder="e.g. small scratch on the back" />
              <button type="button" class="px-2 text-slate-400 hover:text-rose-600" @click="form.defects.splice(i, 1)">
                <UIcon name="i-heroicons-x-mark" class="h-5 w-5" />
              </button>
            </div>
            <button type="button" class="text-sm font-medium text-brand-700 hover:underline" @click="form.defects.push({ type: '', note: '' })">
              + Add a fault
            </button>
          </div>
        </section>

        <!-- Provenance -->
        <section class="card p-6">
          <h2 class="mb-1 font-semibold text-slate-900">Provenance</h2>
          <p class="mb-4 text-sm text-slate-500">
            A recorded serial protects you and the buyer, and is expected for higher-value goods in the EU.
          </p>
          <div class="grid gap-4 sm:grid-cols-[160px_1fr]">
            <div>
              <label class="label" for="stype">ID type</label>
              <select id="stype" v-model="form.serial_type" class="input">
                <option value="NONE">None</option>
                <option value="SERIAL">Serial</option>
                <option value="IMEI">IMEI</option>
                <option value="VIN">VIN</option>
              </select>
            </div>
            <div>
              <label class="label" for="sno">Number</label>
              <input id="sno" v-model="form.serial_no" class="input" :disabled="form.serial_type === 'NONE'" placeholder="Only buyers you approve will see this" />
            </div>
          </div>
        </section>

        <!-- Pickup -->
        <section class="card p-6">
          <h2 class="mb-1 font-semibold text-slate-900">Collection</h2>
          <div class="mb-4 rounded-xl bg-brand-50 p-3 text-xs leading-relaxed text-brand-800">
            <strong>Your address stays private.</strong> Buyers only see the city and area. The full address and
            phone go to a specific buyer after you approve their request — and you can withdraw it at any time.
          </div>

          <div class="space-y-4">
            <div>
              <label class="label" for="mode">How will it change hands?</label>
              <select id="mode" v-model="form.fulfillment_mode" class="input">
                <option v-for="f in FULFILLMENT_MODES" :key="f.code" :value="f.code">{{ f.label }}</option>
              </select>
            </div>
            <div class="grid gap-4 sm:grid-cols-3">
              <div>
                <label class="label" for="country">Country</label>
                <input id="country" v-model="form.pickup_country" maxlength="2" class="input uppercase" placeholder="RS" />
              </div>
              <div>
                <label class="label" for="city">City <span class="text-rose-500">*</span></label>
                <input id="city" v-model="form.pickup_city" class="input" required placeholder="Beograd" />
              </div>
              <div>
                <label class="label" for="area">Area</label>
                <input id="area" v-model="form.pickup_area" class="input" placeholder="Novi Beograd" />
              </div>
            </div>
            <div>
              <label class="label" for="addr">Full address <span class="text-slate-400">(private)</span></label>
              <input id="addr" v-model="form.pickup_address" class="input" placeholder="Street, number, flat" />
            </div>
            <div class="grid gap-4 sm:grid-cols-2">
              <div>
                <label class="label" for="phone">Phone <span class="text-slate-400">(private)</span></label>
                <input id="phone" v-model="form.contact_phone" class="input" placeholder="+381 …" />
              </div>
              <div>
                <label class="label" for="pnote">Collection note <span class="text-slate-400">(private)</span></label>
                <input id="pnote" v-model="form.pickup_note" class="input" placeholder="e.g. weekdays after 18:00" />
              </div>
            </div>
          </div>
        </section>

        <p v-if="error" class="rounded-xl bg-rose-50 p-4 text-sm text-rose-700">{{ error }}</p>

        <div class="flex items-center gap-3">
          <button type="submit" class="btn-primary" :disabled="busy">
            {{ busy ? 'Publishing…' : 'Publish listing' }}
          </button>
          <NuxtLink to="/" class="btn-ghost">Cancel</NuxtLink>
        </div>
      </form>
    </ClientOnly>
  </div>
</template>

<script setup lang="ts">
const auth = useAuthStore()
const api = useApi()
const router = useRouter()
const config = useRuntimeConfig()

const thisYear = new Date().getFullYear()
const currency = (config.public.defaultCurrency as string) || 'EUR'
const price = ref<number | null>(null)
const busy = ref(false)
const error = ref('')

const form = reactive({
  title: '',
  description: '',
  purchase_year: null as number | null,
  condition_grade: 'B',
  warranty_left_months: null as number | null,
  original_packaging: false,
  defects: [] as Array<{ type: string; note: string }>,
  serial_type: 'NONE',
  serial_no: '',
  fulfillment_mode: 'SELLER_PICKUP',
  pickup_country: (config.public.defaultCountry as string) || 'RS',
  pickup_city: '',
  pickup_area: '',
  pickup_address: '',
  pickup_note: '',
  contact_phone: '',
})

async function submit() {
  busy.value = true
  error.value = ''
  try {
    const created = await api<any>('/secondhand/listings', {
      method: 'POST',
      body: {
        ...form,
        price_minor: Math.round((price.value || 0) * 100),
        currency,
        serial_no: form.serial_type === 'NONE' ? null : form.serial_no || null,
        defects: form.defects.filter((d) => d.type || d.note),
        pickup_country: (form.pickup_country || '').toUpperCase().slice(0, 2),
      },
    })
    router.push(`/item/${created.id}`)
  } catch (err: any) {
    error.value = apiErrorMessage(err, 'Could not publish the listing')
  } finally {
    busy.value = false
  }
}

onMounted(() => auth.hydrate())
</script>
