<template>
  <div v-if="product" class="section-padding">
    <div class="container-main">
      <NuxtLink to="/products" class="text-sm text-primary-400 hover:underline">&larr; {{ $t('products.title') }}</NuxtLink>

      <div class="mt-6 grid grid-cols-1 lg:grid-cols-2 gap-12">
        <!-- Image -->
        <div class="aspect-square glass-panel p-2 flex items-center justify-center overflow-hidden border-white/20">
          <img v-if="product.images_json?.[0]" :src="product.images_json[0]" :alt="product.name" class="w-full h-full object-cover rounded-lg" />
          <span v-else class="text-slate-600 text-6xl">&#128247;</span>
        </div>

        <!-- Info -->
        <div class="glass-panel p-8">
          <div class="flex items-center gap-2 mb-3">
            <StatusBadge v-if="product.source_type === 'official'" status="verified" :label="$t('products.official')" />
            <StatusBadge v-if="product.service_available" status="active" :label="$t('products.serviceAvailable')" />
          </div>
          <h1 class="text-2xl font-bold text-white">{{ product.name }}</h1>
          <p v-if="product.brand" class="text-slate-400 mt-1">{{ product.brand }}</p>
          <p class="mt-4 text-slate-300">{{ product.description }}</p>

          <div class="mt-6 space-y-3 text-sm border-t border-b border-white/10 py-4">
            <div v-if="product.list_price" class="flex justify-between"><span class="text-slate-400">Price</span><span class="font-bold text-primary-400">&euro;{{ product.list_price }}</span></div>
            <div class="flex justify-between"><span class="text-slate-400">{{ $t('products.moq') }}</span><span class="text-white">{{ product.moq }}</span></div>
            <div v-if="product.lead_time_days" class="flex justify-between"><span class="text-slate-400">{{ $t('products.leadTime') }}</span><span class="text-white">{{ product.lead_time_days }} days</span></div>
            <div v-if="product.warranty_years" class="flex justify-between"><span class="text-slate-400">{{ $t('products.warranty') }}</span><span class="text-white">{{ product.warranty_years }} years</span></div>
            <div class="flex justify-between"><span class="text-slate-400">Currency</span><span class="text-white">{{ product.currency }}</span></div>
          </div>

          <!-- Specs -->
          <div v-if="product.specs_json && Object.keys(product.specs_json).length" class="mt-6">
            <h3 class="font-semibold text-white mb-3">{{ $t('products.specifications') }}</h3>
            <table class="w-full text-sm">
              <tr v-for="(val, key) in product.specs_json" :key="key" class="border-b border-white/10">
                <td class="py-2 text-slate-400 pr-4">{{ key }}</td>
                <td class="py-2 text-white">{{ val }}</td>
              </tr>
            </table>
          </div>

          <div class="mt-8 flex gap-4">
            <button @click="showInquiryModal = true" class="bg-primary-600 text-white px-6 py-3 rounded-lg font-medium hover:bg-primary-500 transition-colors duration-200 shadow-[0_0_15px_rgba(14,165,233,0.3)]">{{ $t('products.requestQuote') }}</button>
            <button class="border border-primary-500 text-primary-400 px-6 py-3 rounded-lg font-medium hover:bg-white/5 transition-colors duration-200">{{ $t('products.addToProject') }}</button>
          </div>
        </div>
      </div>
    </div>

    <!-- Inquiry Modal -->
    <div v-if="showInquiryModal" class="fixed inset-0 bg-slate-950/80 backdrop-blur-sm flex items-center justify-center z-50 p-4" @click.self="showInquiryModal = false">
      <div class="glass-panel max-w-md w-full p-6 border-primary-500/30 shadow-[0_0_20px_rgba(14,165,233,0.2)]">
        <div class="flex items-start justify-between mb-4">
          <h2 class="text-lg font-bold text-white">Inquire About Product</h2>
          <button @click="showInquiryModal = false" class="text-slate-400 hover:text-white text-xl">&times;</button>
        </div>
        
        <form v-if="!inquirySuccess" @submit.prevent="submitInquiry" class="space-y-4">
          <p class="text-sm text-slate-300">Product: <span class="font-bold">{{ product.name }}</span></p>
          
          <div v-if="!isLoggedIn">
            <label class="block text-xs font-medium text-slate-400 mb-1">Name</label>
            <input v-model="inquiryForm.contact_name" type="text" class="input-field bg-white/5 border-white/10 text-white placeholder-slate-500" required>
          </div>
          
          <div v-if="!isLoggedIn">
            <label class="block text-xs font-medium text-slate-400 mb-1">Email</label>
            <input v-model="inquiryForm.contact_email" type="email" class="input-field bg-white/5 border-white/10 text-white placeholder-slate-500" required>
          </div>
          
          <div>
            <label class="block text-xs font-medium text-slate-400 mb-1">Phone (Optional)</label>
            <input v-model="inquiryForm.contact_phone" type="text" class="input-field bg-white/5 border-white/10 text-white placeholder-slate-500">
          </div>
          
          <div>
            <label class="block text-xs font-medium text-slate-400 mb-1">Estimated Quantity</label>
            <input v-model="inquiryForm.quantity" type="number" min="1" class="input-field bg-white/5 border-white/10 text-white placeholder-slate-500" required>
          </div>
          
          <div>
            <label class="block text-xs font-medium text-slate-400 mb-1">Message / Requirements</label>
            <textarea v-model="inquiryForm.message" rows="3" class="input-field bg-white/5 border-white/10 text-white placeholder-slate-500" required></textarea>
          </div>
          
          <button type="submit" class="w-full bg-primary-600 text-white py-2 rounded font-medium hover:bg-primary-500 transition shadow-[0_0_10px_rgba(14,165,233,0.3)]">
            Submit Inquiry
          </button>
        </form>
        
        <div v-else class="text-center py-8">
          <div class="w-16 h-16 bg-emerald-500/20 text-emerald-400 rounded-full flex items-center justify-center mx-auto mb-4 text-3xl">✓</div>
          <h3 class="text-xl font-bold text-white mb-2">Inquiry Sent!</h3>
          <p class="text-slate-300 text-sm">Thank you for your interest. Our vendor or support team will contact you shortly.</p>
          <button @click="showInquiryModal = false" class="mt-6 border border-white/20 text-white px-6 py-2 rounded hover:bg-white/10 transition">Close</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
const route = useRoute()
const { apiFetch } = useApi()
const { isLoggedIn } = useAuth()

const product = ref<any>(null)
const showInquiryModal = ref(false)
const inquirySuccess = ref(false)

const inquiryForm = ref({
  product_id: '',
  contact_name: '',
  contact_email: '',
  contact_phone: '',
  quantity: 1,
  message: ''
})

onMounted(async () => {
  try {
    product.value = await apiFetch<any>(`/products/${route.params.slug}`)
    inquiryForm.value.product_id = product.value.id
    if (product.value.moq) {
      inquiryForm.value.quantity = product.value.moq
    }
  } catch {}
})

async function submitInquiry() {
  try {
    // Determine endpoint based on auth status (public vs authenticated)
    const endpoint = isLoggedIn.value ? '/inquiries' : '/inquiries/public'
    await apiFetch(endpoint, {
      method: 'POST',
      body: inquiryForm.value
    })
    inquirySuccess.value = true
  } catch (e: any) {
    console.error('Inquiry failed:', e)
    alert('Failed to submit inquiry. Please try again.')
  }
}

watch(showInquiryModal, (val) => {
  if (!val) {
    setTimeout(() => {
      inquirySuccess.value = false
      inquiryForm.value.message = ''
      // keep other fields intact for convenience
    }, 300)
  }
})
</script>
