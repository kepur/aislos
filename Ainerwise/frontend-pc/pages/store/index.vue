<template>
  <div class="section-padding">
    <div class="container-main">
      <div class="flex flex-col gap-6 lg:flex-row lg:items-end lg:justify-between mb-10">
        <div>
          <p class="text-xs font-bold tracking-[0.25em] text-primary-400 uppercase">Ainerwise Store</p>
          <h1 class="mt-3 text-4xl font-bold text-white">Solution-ready products, reviewed before purchase.</h1>
          <p class="mt-3 max-w-3xl text-slate-400">
            Build a request from verified products. No card is charged: our team checks compatibility, delivery,
            installation and lifecycle support before issuing a formal quote.
          </p>
        </div>
        <NuxtLink v-if="isLoggedIn" to="/store/orders" class="btn-secondary text-center">My requests</NuxtLink>
      </div>

      <div class="grid gap-8 xl:grid-cols-[1fr_360px]">
        <div>
          <input v-model="search" class="input-field mb-5" placeholder="Search Store catalog" />
          <div class="grid gap-5 md:grid-cols-2">
            <article v-for="product in filteredProducts" :key="product.id" class="glass-panel p-5">
              <div class="flex items-start justify-between gap-4">
                <div>
                  <p class="text-xs text-primary-300">{{ product.brand || 'Ainerwise verified' }}</p>
                  <h2 class="mt-1 text-lg font-semibold text-white">{{ product.public_name || product.name }}</h2>
                </div>
                <span class="rounded-full border border-emerald-400/30 px-2 py-1 text-[10px] text-emerald-300">
                  {{ product.status }}
                </span>
              </div>
              <p class="mt-3 line-clamp-3 text-sm text-slate-400">{{ product.description || 'Project-grade product with local review and support.' }}</p>
              <div class="mt-5 flex items-center justify-between">
                <span class="text-xl font-bold text-primary-300">{{ money(product.list_price, product.currency) }} ref.</span>
                <button class="btn-primary !px-4 !py-2 text-sm" @click="add(product)">Add request</button>
              </div>
            </article>
          </div>
          <p v-if="!filteredProducts.length" class="glass-panel p-8 text-center text-slate-400">No Store products match this search.</p>
        </div>

        <aside class="glass-panel p-5 h-fit xl:sticky xl:top-24">
          <div class="flex items-center justify-between">
            <h2 class="text-lg font-semibold text-white">Request basket</h2>
            <span class="text-xs text-slate-400">{{ cart.length }} items</span>
          </div>
          <div v-if="cart.length" class="mt-5 space-y-4">
            <div v-for="item in cart" :key="item.product.id" class="border-b border-white/10 pb-4">
              <p class="text-sm font-medium text-white">{{ item.product.public_name || item.product.name }}</p>
              <div class="mt-2 flex items-center justify-between gap-3">
                <input v-model.number="item.quantity" type="number" min="1" max="1000" class="input-field !w-20" />
                <span class="text-sm text-slate-300">{{ money(item.product.list_price * item.quantity, item.product.currency) }}</span>
                <button class="text-xs text-red-300" @click="remove(item.product.id)">Remove</button>
              </div>
            </div>
            <textarea v-model="notes" rows="3" class="input-field" placeholder="Site, delivery or installation notes"></textarea>
            <div class="flex items-center justify-between text-sm">
              <span class="text-slate-400">Reference subtotal</span>
              <b class="text-white">{{ money(subtotal, cart[0]?.product.currency || 'EUR') }}</b>
            </div>
            <p class="rounded-lg border border-amber-400/20 bg-amber-400/5 p-3 text-xs text-amber-200">
              No payment is taken. This submits a review request, not a final order.
            </p>
            <button class="btn-primary w-full" :disabled="submitting" @click="submit">
              {{ submitting ? 'Submitting...' : 'Submit for review' }}
            </button>
          </div>
          <p v-else class="mt-5 text-sm text-slate-400">Add products to start a reviewed Store request.</p>
          <p v-if="message" class="mt-4 text-sm text-emerald-300">{{ message }}</p>
          <p v-if="error" class="mt-4 text-sm text-red-300">{{ error }}</p>
        </aside>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
const { apiFetch } = useApi()
const { isLoggedIn } = useAuth()
const products = ref<any[]>([])
const cart = ref<any[]>([])
const search = ref('')
const notes = ref('')
const submitting = ref(false)
const message = ref('')
const error = ref('')

const filteredProducts = computed(() => {
  const term = search.value.toLowerCase().trim()
  return products.value.filter((p) => !term || `${p.name} ${p.brand || ''} ${p.description || ''}`.toLowerCase().includes(term))
})
const subtotal = computed(() => cart.value.reduce((sum, item) => sum + Number(item.product.list_price) * item.quantity, 0))
function money(value: number, currency = 'EUR') {
  return new Intl.NumberFormat('en', { style: 'currency', currency }).format(Number(value || 0))
}
function add(product: any) {
  const existing = cart.value.find((item) => item.product.id === product.id)
  if (existing) existing.quantity += 1
  else cart.value.push({ product, quantity: Math.max(1, product.moq || 1) })
}
function remove(id: string) {
  cart.value = cart.value.filter((item) => item.product.id !== id)
}
async function submit() {
  if (!isLoggedIn.value) return navigateTo('/login?redirect=/store')
  submitting.value = true
  error.value = ''
  message.value = ''
  try {
    const order = await apiFetch<any>('/store/orders', {
      method: 'POST',
      body: { items: cart.value.map((item) => ({ product_id: item.product.id, quantity: item.quantity })), notes: notes.value },
    })
    message.value = `Request ${order.id.slice(0, 8)} submitted. No payment was taken.`
    cart.value = []
    notes.value = ''
  } catch (e: any) {
    error.value = e?.data?.detail || 'Could not submit request'
  } finally {
    submitting.value = false
  }
}
onMounted(async () => {
  const res = await apiFetch<any>('/store/catalog')
  products.value = res.items || []
})
</script>
