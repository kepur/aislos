<template>
  <div class="min-h-screen bg-white">
    <!-- Top Bar -->
    <header class="sticky top-0 z-50 bg-white/95 backdrop-blur border-b border-slate-100">
      <div class="flex items-center justify-between px-4 h-14 pt-safe">
        <div class="flex items-center gap-2">
          <div class="w-8 h-8 bg-primary-600 rounded-lg flex items-center justify-center">
            <span class="text-white font-bold text-sm">PP</span>
          </div>
          <span class="font-bold text-primary-900 text-lg">ProcurePing</span>
        </div>
        <div class="flex items-center gap-3">
          <button type="button" class="text-slate-500 text-sm flex items-center gap-1">
            <svg class="w-4 h-4" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
              <path stroke-linecap="round" stroke-linejoin="round" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
            </svg>
            Cebu
          </button>
          <NuxtLink to="/auth/login">
            <button type="button" class="text-sm font-semibold text-primary-600 px-3 py-1.5 rounded-lg border border-primary-200 active:bg-primary-50">
              Sign in
            </button>
          </NuxtLink>
        </div>
      </div>
    </header>

    <!-- Hero -->
    <section class="relative bg-gradient-to-br from-primary-900 via-primary-800 to-primary-700 px-6 pt-12 pb-16 overflow-hidden">
      <!-- Background decoration -->
      <div class="absolute inset-0 opacity-10">
        <div class="absolute top-0 right-0 w-64 h-64 bg-white rounded-full -translate-y-1/2 translate-x-1/2"></div>
        <div class="absolute bottom-0 left-0 w-48 h-48 bg-white rounded-full translate-y-1/2 -translate-x-1/2"></div>
      </div>

      <div class="relative">
        <div class="inline-flex items-center gap-1.5 bg-white/20 text-white/90 text-xs font-medium px-3 py-1.5 rounded-full mb-4">
          <svg class="w-3.5 h-3.5 text-green-300" fill="currentColor" viewBox="0 0 20 20">
            <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd" />
          </svg>
          Escrow protected marketplace
        </div>

        <h1 class="text-3xl font-extrabold text-white leading-tight mb-3">
          Tell suppliers what you need.
        </h1>
        <p class="text-primary-200 text-base leading-relaxed mb-8">
          Post a request, compare verified offers, and pay safely with escrow.
        </p>

        <!-- Quick Search -->
        <div class="bg-white rounded-2xl p-4 shadow-xl">
          <p class="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-2">What are you looking for?</p>
          <input
            v-model="searchQuery"
            type="text"
            placeholder="500 bags of cement, iPhone 15, laptop…"
            class="w-full text-slate-800 text-sm outline-none placeholder:text-slate-400 mb-3"
            @focus="goToPostRequest"
          />
          <NuxtLink to="/auth/register?role=BUYER">
            <button type="button" class="btn-primary text-sm py-3">
              Post Request — It's Free
            </button>
          </NuxtLink>
        </div>
      </div>
    </section>

    <!-- How it Works -->
    <section class="px-6 py-10">
      <h2 class="text-xl font-bold text-slate-900 mb-1">How ProcurePing works</h2>
      <p class="text-sm text-slate-500 mb-6">Reverse marketplace — suppliers come to you</p>

      <div class="space-y-4">
        <div v-for="step in steps" :key="step.num" class="flex gap-4">
          <div class="flex-shrink-0 w-10 h-10 rounded-full flex items-center justify-center text-sm font-bold"
               :class="step.color">
            {{ step.num }}
          </div>
          <div>
            <h3 class="font-semibold text-slate-800 text-sm">{{ step.title }}</h3>
            <p class="text-xs text-slate-500 leading-relaxed mt-0.5">{{ step.desc }}</p>
          </div>
        </div>
      </div>
    </section>

    <!-- Trust Section -->
    <section class="mx-4 mb-6 bg-gradient-to-br from-green-50 to-emerald-50 rounded-2xl p-5 border border-green-100">
      <div class="flex items-start gap-3 mb-4">
        <div class="w-10 h-10 bg-green-600 rounded-xl flex items-center justify-center flex-shrink-0">
          <svg class="w-5 h-5 text-white" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
          </svg>
        </div>
        <div>
          <h3 class="font-bold text-green-900 text-sm">Escrow Protection</h3>
          <p class="text-xs text-green-700 mt-0.5 leading-relaxed">
            Your payment is held safely until you confirm delivery. Funds only release when you're satisfied.
          </p>
        </div>
      </div>
      <div class="grid grid-cols-3 gap-3">
        <div v-for="trust in trustPoints" :key="trust.label" class="text-center">
          <div class="text-2xl font-extrabold text-green-700">{{ trust.value }}</div>
          <div class="text-[10px] text-green-600 font-medium leading-tight">{{ trust.label }}</div>
        </div>
      </div>
    </section>

    <!-- Categories Quick Access -->
    <section class="px-4 mb-8">
      <h2 class="text-base font-bold text-slate-900 mb-3">Popular Categories</h2>
      <div class="grid grid-cols-3 gap-3">
        <button type="button"
          v-for="cat in categories"
          :key="cat.slug"
          class="bg-white rounded-xl p-3 text-center shadow-card active:scale-95 transition-transform"
          @click="goToPostWithCategory(cat.slug)"
        >
          <div class="text-2xl mb-1">{{ cat.emoji }}</div>
          <div class="text-xs font-medium text-slate-700 leading-tight">{{ cat.name }}</div>
        </button>
      </div>
    </section>

    <!-- CTA -->
    <section class="px-4 pb-12">
      <div class="bg-primary-600 rounded-2xl p-6 text-center">
        <h3 class="text-lg font-bold text-white mb-2">Are you a supplier?</h3>
        <p class="text-primary-200 text-sm mb-4">
          Get pinged when buyers need what you supply. No cold calls — only qualified leads.
        </p>
        <NuxtLink to="/auth/register?role=SUPPLIER_ADMIN">
          <button type="button" class="bg-white text-primary-700 font-semibold px-6 py-3 rounded-xl text-sm w-full active:bg-primary-50">
            Join as Supplier
          </button>
        </NuxtLink>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
definePageMeta({ layout: "default", middleware: [] });
useHead({ title: "Reverse Procurement Marketplace" });

const searchQuery = ref("");
const router = useRouter();

const steps = [
  { num: 1, title: "Post what you need", desc: "Describe your requirement, quantity, location, and budget.", color: "bg-primary-100 text-primary-700" },
  { num: 2, title: "Suppliers compete", desc: "Verified suppliers submit competitive offers directly to you.", color: "bg-amber-100 text-amber-700" },
  { num: 3, title: "Compare & choose", desc: "Review offers by price, delivery speed, and supplier rating.", color: "bg-green-100 text-green-700" },
  { num: 4, title: "Pay with escrow", desc: "Your money is protected until you confirm safe delivery.", color: "bg-primary-100 text-primary-700" },
];

const trustPoints = [
  { value: "100%", label: "Escrow Protected" },
  { value: "24h", label: "Supplier Response" },
  { value: "KYC", label: "Verified Suppliers" },
];

const categories = [
  { slug: "construction", name: "Construction", emoji: "🏗️" },
  { slug: "it-office", name: "IT & Office", emoji: "💻" },
  { slug: "automotive", name: "Automotive", emoji: "🚗" },
  { slug: "food-bev", name: "Food & Bev", emoji: "🍽️" },
  { slug: "industrial", name: "Industrial", emoji: "⚙️" },
  { slug: "medical", name: "Medical", emoji: "🏥" },
];

function goToPostRequest() {
  router.push("/auth/login?redirect=/buyer/post-request");
}

function goToPostWithCategory(slug: string) {
  router.push(`/auth/login?redirect=/buyer/post-request?category=${slug}`);
}
</script>
