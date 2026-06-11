<template>
  <div>
    <!-- Hero Section -->
    <section class="bg-indigo-900 text-white py-20 lg:py-32 relative overflow-hidden">
      <!-- Decorative background -->
      <div class="absolute inset-0 bg-[url('https://www.transparenttextures.com/patterns/cubes.png')] opacity-10"></div>
      <div class="absolute inset-0 bg-gradient-to-b from-indigo-900/50 to-indigo-900"></div>
      
      <div class="container mx-auto px-4 relative z-10 grid lg:grid-cols-2 gap-12 items-center">
        <div>
          <h1 class="text-4xl lg:text-6xl font-bold tracking-tight mb-6 leading-tight">
            Post what you need. <br />
            <span class="text-indigo-300">Verified suppliers compete with offers.</span>
          </h1>
          <p class="text-lg lg:text-xl text-indigo-100 mb-8 max-w-2xl leading-relaxed">
            A safer reverse marketplace with escrow protection, supplier verification, and side-by-side offer comparison. Designed for global procurement and fast sourcing.
          </p>
          <div class="flex flex-col sm:flex-row gap-4">
            <UButton size="xl" color="white" variant="solid" to="/post-request" class="justify-center px-8 text-indigo-900 font-semibold shadow-lg hover:shadow-xl transition-shadow">
              Post a Request
            </UButton>
            <UButton size="xl" color="indigo" variant="outline" class="justify-center px-8 border-indigo-400 text-white hover:bg-indigo-800" to="/supplier-onboarding">
              Become a Supplier
            </UButton>
          </div>
          
          <div class="mt-10 flex items-center space-x-6 text-sm text-indigo-200">
            <div class="flex items-center"><UIcon name="i-heroicons-shield-check" class="w-5 h-5 mr-2 text-green-400" /> Escrow Protected</div>
            <div class="flex items-center"><UIcon name="i-heroicons-badge-check" class="w-5 h-5 mr-2 text-blue-400" /> Verified Suppliers</div>
          </div>
        </div>
        
        <!-- Quick Request Panel -->
        <div class="bg-white rounded-2xl shadow-2xl p-6 lg:p-8 text-slate-900 max-w-md mx-auto w-full">
          <h3 class="text-2xl font-semibold mb-6">What are you looking for?</h3>
          <form @submit.prevent class="hero-quick-search space-y-4">
            <!-- Category -->
            <div class="space-y-1">
              <label class="block text-sm font-medium text-slate-700">Category</label>
              <select v-model="heroForm.category"
                class="w-full rounded-lg border border-slate-200 bg-white px-3 py-3 text-sm text-slate-800 shadow-sm focus:border-indigo-400 focus:outline-none focus:ring-2 focus:ring-indigo-200 appearance-none">
                <option value="">Select category</option>
                <option>Construction Materials</option>
                <option>Marine Parts</option>
                <option>Auto Parts</option>
                <option>IT / Electronics</option>
                <option>Office Supplies</option>
              </select>
            </div>

            <!-- Budget row -->
            <div class="grid grid-cols-2 gap-4">
              <div class="space-y-1">
                <label class="block text-sm font-medium text-slate-700">Min Budget</label>
                <div class="relative">
                  <span class="pointer-events-none absolute left-3 top-1/2 z-10 flex -translate-y-1/2 items-center text-sm text-slate-400">$</span>
                  <input v-model="heroForm.budgetMin" type="number" placeholder="0" min="0"
                    class="w-full rounded-lg border border-slate-200 bg-white py-3 pl-8 pr-3 text-sm text-slate-800 shadow-sm focus:border-indigo-400 focus:outline-none focus:ring-2 focus:ring-indigo-200" />
                </div>
              </div>
              <div class="space-y-1">
                <label class="block text-sm font-medium text-slate-700">Max Budget</label>
                <div class="relative">
                  <span class="pointer-events-none absolute left-3 top-1/2 z-10 flex -translate-y-1/2 items-center text-sm text-slate-400">$</span>
                  <input v-model="heroForm.budgetMax" type="number" placeholder="Max" min="0"
                    class="w-full rounded-lg border border-slate-200 bg-white py-3 pl-8 pr-3 text-sm text-slate-800 shadow-sm focus:border-indigo-400 focus:outline-none focus:ring-2 focus:ring-indigo-200" />
                </div>
              </div>
            </div>

            <!-- Delivery Location -->
            <div class="space-y-1">
              <label class="block text-sm font-medium text-slate-700">Delivery Location</label>
              <div class="relative">
                <span class="pointer-events-none absolute left-3 top-1/2 z-10 flex -translate-y-1/2 items-center">
                  <svg class="w-4 h-4 text-slate-400" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                    <path stroke-linecap="round" stroke-linejoin="round" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
                  </svg>
                </span>
                <input v-model="heroForm.location" type="text" placeholder="Enter city or area"
                  class="w-full rounded-lg border border-slate-200 bg-white py-3 pl-10 pr-3 text-sm text-slate-800 shadow-sm focus:border-indigo-400 focus:outline-none focus:ring-2 focus:ring-indigo-200" />
              </div>
            </div>

            <!-- Search Radius -->
            <div class="space-y-2">
              <div class="flex items-center justify-between">
                <label class="block text-sm font-medium text-slate-700">Search Radius</label>
                <span class="text-sm font-semibold text-indigo-600">{{ heroForm.radius }} km</span>
              </div>
              <input v-model="heroForm.radius" type="range" min="1" max="200" step="1"
                class="range-input w-full h-2 rounded-full bg-slate-200 appearance-none cursor-pointer accent-indigo-600" />
              <div class="flex justify-between text-xs text-slate-400">
                <span>1 km</span>
                <span>200 km</span>
              </div>
            </div>

            <UButton type="submit" color="indigo" block size="xl" class="mt-6 text-white shadow-md" @click="handleHeroSearch">
              Find Suppliers
            </UButton>
          </form>
        </div>
      </div>
    </section>

    <!-- How it works -->
    <section class="py-20 bg-white">
      <div class="container mx-auto px-4">
        <div class="text-center mb-16">
          <h2 class="text-3xl font-bold text-slate-900 mb-4">How ProcurePing Works</h2>
          <p class="text-lg text-slate-600 max-w-2xl mx-auto">The secure reverse marketplace that saves you time and protects your money.</p>
        </div>
        
        <div class="grid md:grid-cols-5 gap-8 relative">
          <div class="hidden md:block absolute top-1/2 left-0 w-full h-0.5 bg-indigo-100 -translate-y-1/2 z-0"></div>
          
          <div class="relative z-10 flex flex-col items-center text-center bg-white p-4">
            <div class="w-16 h-16 rounded-full bg-indigo-100 text-indigo-600 flex items-center justify-center mb-4 shadow-sm border-4 border-white">
              <UIcon name="i-heroicons-pencil-square" class="w-8 h-8" />
            </div>
            <h4 class="font-semibold text-slate-900 mb-2">1. Post Request</h4>
            <p class="text-sm text-slate-600">Describe what you need, set budget & location.</p>
          </div>
          
          <div class="relative z-10 flex flex-col items-center text-center bg-white p-4">
            <div class="w-16 h-16 rounded-full bg-indigo-100 text-indigo-600 flex items-center justify-center mb-4 shadow-sm border-4 border-white">
              <UIcon name="i-heroicons-envelope-open" class="w-8 h-8" />
            </div>
            <h4 class="font-semibold text-slate-900 mb-2">2. Receive Offers</h4>
            <p class="text-sm text-slate-600">Verified suppliers ping you with exact quotes.</p>
          </div>
          
          <div class="relative z-10 flex flex-col items-center text-center bg-white p-4">
            <div class="w-16 h-16 rounded-full bg-indigo-100 text-indigo-600 flex items-center justify-center mb-4 shadow-sm border-4 border-white">
              <UIcon name="i-heroicons-scale" class="w-8 h-8" />
            </div>
            <h4 class="font-semibold text-slate-900 mb-2">3. Compare & Select</h4>
            <p class="text-sm text-slate-600">Compare by price, distance, and supplier rating.</p>
          </div>
          
          <div class="relative z-10 flex flex-col items-center text-center bg-white p-4">
            <div class="w-16 h-16 rounded-full bg-indigo-100 text-indigo-600 flex items-center justify-center mb-4 shadow-sm border-4 border-white">
              <UIcon name="i-heroicons-lock-closed" class="w-8 h-8" />
            </div>
            <h4 class="font-semibold text-slate-900 mb-2">4. Escrow Checkout</h4>
            <p class="text-sm text-slate-600">Funds are held safely until you confirm delivery.</p>
          </div>
          
          <div class="relative z-10 flex flex-col items-center text-center bg-white p-4">
            <div class="w-16 h-16 rounded-full bg-green-100 text-green-600 flex items-center justify-center mb-4 shadow-sm border-4 border-white">
              <UIcon name="i-heroicons-check-badge" class="w-8 h-8" />
            </div>
            <h4 class="font-semibold text-slate-900 mb-2">5. Confirm Delivery</h4>
            <p class="text-sm text-slate-600">Inspect the items, click confirm, payout released.</p>
          </div>
        </div>
      </div>
    </section>

    <!-- Categories -->
    <section class="py-20 bg-slate-50">
      <div class="container mx-auto px-4">
        <div class="flex justify-between items-end mb-10">
          <div>
            <h2 class="text-3xl font-bold text-slate-900 mb-2">Popular Categories</h2>
            <p class="text-slate-600">Find exactly what you need from specialized suppliers.</p>
          </div>
          <UButton variant="ghost" color="indigo" trailing-icon="i-heroicons-arrow-right">View All</UButton>
        </div>
        
        <div class="grid grid-cols-2 md:grid-cols-4 gap-6">
          <div v-for="cat in ['Construction', 'Marine', 'Auto Parts', 'IT & Electronics', 'Home & Office', 'Industrial', 'Services', 'Custom Requests']" :key="cat" class="bg-white rounded-xl p-6 border border-slate-200 hover:border-indigo-300 hover:shadow-lg transition-all cursor-pointer group">
            <div class="w-12 h-12 bg-slate-100 rounded-lg mb-4 flex items-center justify-center group-hover:bg-indigo-50 group-hover:text-indigo-600 text-slate-500 transition-colors">
              <UIcon name="i-heroicons-cube" class="w-6 h-6" />
            </div>
            <h4 class="font-semibold text-slate-900">{{ cat }}</h4>
          </div>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { reactive } from 'vue'
import { useRouter } from 'vue-router'

// Landing Page
const router = useRouter()

const heroForm = reactive({
  category: '',
  budgetMin: '',
  budgetMax: '',
  location: '',
  radius: 25,
})

function handleHeroSearch() {
  const q = new URLSearchParams()
  if (heroForm.category) q.set('category', heroForm.category)
  if (heroForm.budgetMin) q.set('budget_min', String(Number(heroForm.budgetMin) * 100))
  if (heroForm.budgetMax) q.set('budget_max', String(Number(heroForm.budgetMax) * 100))
  if (heroForm.location) q.set('location', heroForm.location)
  if (heroForm.radius !== 25) q.set('radius', String(heroForm.radius))
  router.push(`/marketplace?${q.toString()}`)
}
</script>

<style scoped>
.hero-quick-search .range-input {
  -webkit-appearance: none;
  appearance: none;
  background: transparent;
}

.hero-quick-search .range-input::-webkit-slider-runnable-track {
  height: 0.5rem;
  border-radius: 999px;
  background: #cbd5e1;
}

.hero-quick-search .range-input::-webkit-slider-thumb {
  -webkit-appearance: none;
  appearance: none;
  width: 1rem;
  height: 1rem;
  margin-top: -0.25rem;
  border-radius: 999px;
  border: 2px solid #ffffff;
  background: #4f46e5;
  box-shadow: 0 1px 4px rgb(15 23 42 / 0.28);
}

.hero-quick-search .range-input::-moz-range-track {
  height: 0.5rem;
  border-radius: 999px;
  background: #cbd5e1;
}

.hero-quick-search .range-input::-moz-range-thumb {
  width: 1rem;
  height: 1rem;
  border-radius: 999px;
  border: 2px solid #ffffff;
  background: #4f46e5;
  box-shadow: 0 1px 4px rgb(15 23 42 / 0.28);
}
</style>
