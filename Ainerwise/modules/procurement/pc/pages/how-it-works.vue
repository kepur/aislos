<template>
  <div>
    <!-- ===== Hero ===== -->
    <section class="bg-indigo-900 text-white py-16 lg:py-24 relative overflow-hidden">
      <div class="absolute inset-0 bg-gradient-to-b from-indigo-900/40 to-indigo-900"></div>
      <div class="mx-auto max-w-4xl px-4 sm:px-6 lg:px-8 relative z-10 text-center">
        <p class="text-xs font-bold uppercase tracking-widest text-indigo-300 mb-4">How it works</p>
        <h1 class="text-3xl lg:text-5xl font-bold tracking-tight mb-6 leading-tight">
          From idea to installed, on one AI platform
        </h1>
        <p class="text-lg text-indigo-100 max-w-2xl mx-auto leading-relaxed">
          <strong class="text-white">AinerWise</strong> is the AI brain that helps you design a smart-building solution.
          <strong class="text-white">AISLOS Market</strong> is the engine that sources it, gets verified suppliers to
          compete, and follows the job through delivery and lifecycle service. Same system — two faces.
        </p>
        <div class="mt-8 flex flex-col sm:flex-row gap-3 justify-center">
          <UButton size="lg" color="white" variant="solid" :to="appStore.localizedPath('/buyer/projects')" class="justify-center px-6 text-indigo-900 font-semibold">
            Start an AI Project
          </UButton>
          <UButton size="lg" color="indigo" variant="outline" :to="appStore.localizedPath('/post-request')" class="justify-center px-6 border-indigo-400 text-white hover:bg-indigo-800">
            Post a Requirement
          </UButton>
        </div>
      </div>
    </section>

    <!-- ===== One platform, two faces (AinerWise × Market loop) ===== -->
    <section class="py-16 lg:py-20 bg-white">
      <div class="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div class="text-center mb-12">
          <h2 class="text-3xl font-bold text-slate-900 mb-3">One platform, two faces</h2>
          <p class="text-lg text-slate-600 max-w-2xl mx-auto">
            AinerWise and AISLOS Market run on the same AISLOS operating system. Your project flows
            through three stages — and the data never leaves the platform.
          </p>
        </div>

        <div class="relative grid lg:grid-cols-3 gap-6 lg:gap-8">
          <!-- Stage 1 -->
          <div class="group relative flex flex-col overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm transition-all hover:-translate-y-1 hover:shadow-xl">
            <div class="h-1.5 w-full bg-gradient-to-r from-sky-500 to-indigo-500"></div>
            <div class="p-7 flex flex-col flex-1">
              <div class="flex items-center gap-3 mb-4">
                <span class="w-11 h-11 rounded-xl bg-gradient-to-br from-sky-500 to-indigo-600 text-white flex items-center justify-center font-bold text-lg shadow-md shadow-indigo-200">1</span>
                <div>
                  <p class="text-xs font-semibold uppercase tracking-wider text-indigo-500">AinerWise · 官网</p>
                  <h3 class="text-lg font-bold text-slate-900">Design &amp; assess</h3>
                </div>
              </div>
              <p class="text-sm text-slate-600 leading-relaxed mb-4">
                Talk to the AI Building Brain. Pick a scenario (villa, hotel, office, factory, solar site) and a target
                intelligence level. The AI turns your goals into a structured smart-building blueprint.
              </p>
              <ul class="mt-auto space-y-2.5 text-sm text-slate-700">
                <li class="flex items-start gap-2.5"><span class="mt-0.5 flex h-5 w-5 flex-shrink-0 items-center justify-center rounded-full bg-indigo-50 text-[11px] text-indigo-600">✓</span> AI assessment &amp; chat</li>
                <li class="flex items-start gap-2.5"><span class="mt-0.5 flex h-5 w-5 flex-shrink-0 items-center justify-center rounded-full bg-indigo-50 text-[11px] text-indigo-600">✓</span> KNX · Energy · Security · Service map</li>
                <li class="flex items-start gap-2.5"><span class="mt-0.5 flex h-5 w-5 flex-shrink-0 items-center justify-center rounded-full bg-indigo-50 text-[11px] text-indigo-600">✓</span> Solution blueprint &amp; budget range</li>
              </ul>
            </div>
          </div>

          <!-- Stage 2 -->
          <div class="group relative flex flex-col overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm transition-all hover:-translate-y-1 hover:shadow-xl">
            <div class="h-1.5 w-full bg-gradient-to-r from-indigo-500 to-violet-500"></div>
            <div class="p-7 flex flex-col flex-1">
              <div class="flex items-center gap-3 mb-4">
                <span class="w-11 h-11 rounded-xl bg-gradient-to-br from-indigo-500 to-violet-600 text-white flex items-center justify-center font-bold text-lg shadow-md shadow-violet-200">2</span>
                <div>
                  <p class="text-xs font-semibold uppercase tracking-wider text-violet-500">AISLOS Market</p>
                  <h3 class="text-lg font-bold text-slate-900">Source &amp; build</h3>
                </div>
              </div>
              <p class="text-sm text-slate-600 leading-relaxed mb-4">
                The blueprint becomes a procurement list. Post it as an RFQ and verified suppliers compete with
                real offers. Compare, award, and track the order into a live project — all in one place.
              </p>
              <ul class="mt-auto space-y-2.5 text-sm text-slate-700">
                <li class="flex items-start gap-2.5"><span class="mt-0.5 flex h-5 w-5 flex-shrink-0 items-center justify-center rounded-full bg-violet-50 text-[11px] text-violet-600">✓</span> AI procurement list (BOQ)</li>
                <li class="flex items-start gap-2.5"><span class="mt-0.5 flex h-5 w-5 flex-shrink-0 items-center justify-center rounded-full bg-violet-50 text-[11px] text-violet-600">✓</span> RFQ · supplier bidding · compare</li>
                <li class="flex items-start gap-2.5"><span class="mt-0.5 flex h-5 w-5 flex-shrink-0 items-center justify-center rounded-full bg-violet-50 text-[11px] text-violet-600">✓</span> Award · order · project tracking</li>
              </ul>
            </div>
          </div>

          <!-- Stage 3 -->
          <div class="group relative flex flex-col overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm transition-all hover:-translate-y-1 hover:shadow-xl">
            <div class="h-1.5 w-full bg-gradient-to-r from-emerald-500 to-teal-500"></div>
            <div class="p-7 flex flex-col flex-1">
              <div class="flex items-center gap-3 mb-4">
                <span class="w-11 h-11 rounded-xl bg-gradient-to-br from-emerald-500 to-teal-600 text-white flex items-center justify-center font-bold text-lg shadow-md shadow-emerald-200">3</span>
                <div>
                  <p class="text-xs font-semibold uppercase tracking-wider text-emerald-600">AinerWise · lifecycle</p>
                  <h3 class="text-lg font-bold text-slate-900">Operate &amp; service</h3>
                </div>
              </div>
              <p class="text-sm text-slate-600 leading-relaxed mb-4">
                Delivered equipment becomes registered assets. Maintenance, firmware updates, inspections and AI
                reports keep the building serviceable — and feed the next project back into the brain.
              </p>
              <ul class="mt-auto space-y-2.5 text-sm text-slate-700">
                <li class="flex items-start gap-2.5"><span class="mt-0.5 flex h-5 w-5 flex-shrink-0 items-center justify-center rounded-full bg-emerald-50 text-[11px] text-emerald-600">✓</span> Asset registry</li>
                <li class="flex items-start gap-2.5"><span class="mt-0.5 flex h-5 w-5 flex-shrink-0 items-center justify-center rounded-full bg-emerald-50 text-[11px] text-emerald-600">✓</span> Maintenance &amp; lifecycle service</li>
                <li class="flex items-start gap-2.5"><span class="mt-0.5 flex h-5 w-5 flex-shrink-0 items-center justify-center rounded-full bg-emerald-50 text-[11px] text-emerald-600">✓</span> AI reports → new requirements</li>
              </ul>
            </div>
          </div>
        </div>

        <p class="text-center text-sm text-slate-500 mt-8">
          The loop closes: <span class="font-semibold text-slate-700">assess → source → operate → assess again.</span>
          AinerWise is the customer-facing brain; AISLOS Market is the sourcing &amp; fulfillment engine.
        </p>
      </div>
    </section>

    <!-- ===== Buyer journey (detailed) ===== -->
    <section class="py-16 lg:py-20 bg-slate-50">
      <div class="mx-auto max-w-5xl px-4 sm:px-6 lg:px-8">
        <div class="text-center mb-12">
          <h2 class="text-3xl font-bold text-slate-900 mb-3">For buyers — step by step</h2>
          <p class="text-lg text-slate-600 max-w-2xl mx-auto">From a rough idea to an awarded, tracked, serviced project.</p>
        </div>

        <ol class="space-y-4">
          <li v-for="(step, i) in buyerSteps" :key="i" class="flex gap-5 rounded-xl bg-white border border-slate-200 p-5 hover:border-indigo-300 hover:shadow-sm transition-all">
            <span class="shrink-0 w-10 h-10 rounded-full bg-indigo-100 text-indigo-600 flex items-center justify-center font-bold">{{ i + 1 }}</span>
            <div>
              <h4 class="font-semibold text-slate-900 mb-1" v-html="step.title"></h4>
              <p class="text-sm text-slate-600 leading-relaxed" v-html="step.body"></p>
            </div>
          </li>
        </ol>
      </div>
    </section>

    <!-- ===== Supplier journey ===== -->
    <section class="py-16 lg:py-20 bg-white">
      <div class="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div class="text-center mb-12">
          <h2 class="text-3xl font-bold text-slate-900 mb-3">For suppliers</h2>
          <p class="text-lg text-slate-600 max-w-2xl mx-auto">Get verified once, then receive matched requests and win work on merit.</p>
        </div>
        <div class="grid md:grid-cols-4 gap-6">
          <div v-for="(s, i) in supplierSteps" :key="i" class="rounded-xl border border-slate-200 p-6 text-center">
            <div class="w-12 h-12 mx-auto rounded-full bg-emerald-100 text-emerald-600 flex items-center justify-center font-bold mb-4">{{ i + 1 }}</div>
            <h4 class="font-semibold text-slate-900 mb-1" v-html="s.title"></h4>
            <p class="text-sm text-slate-600">{{ s.body }}</p>
          </div>
        </div>
        <div class="text-center mt-10">
          <UButton color="emerald" variant="soft" :to="appStore.localizedPath('/supplier-onboarding')">Become a verified supplier</UButton>
        </div>
      </div>
    </section>

    <!-- ===== Trust & governance (honest by design) ===== -->
    <section class="surface-dark py-16 lg:py-20 bg-slate-900 text-white">
      <div class="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div class="text-center mb-12">
          <h2 class="text-3xl font-bold mb-3">How we keep it safe &amp; honest</h2>
          <p class="text-lg text-slate-300 max-w-2xl mx-auto">The AI assists. People decide. Money stays with you.</p>
        </div>
        <div class="grid md:grid-cols-3 gap-6">
          <div v-for="(g, i) in governance" :key="i" class="rounded-xl border border-white/10 bg-white/5 p-6">
            <h4 class="font-semibold text-white mb-2">{{ g.title }}</h4>
            <p class="text-sm text-slate-300 leading-relaxed">{{ g.body }}</p>
          </div>
        </div>
      </div>
    </section>

    <!-- ===== CTA band ===== -->
    <section class="py-16 bg-indigo-600 text-white">
      <div class="mx-auto max-w-4xl px-4 sm:px-6 lg:px-8 text-center">
        <h2 class="text-2xl lg:text-3xl font-bold mb-4">Ready to start?</h2>
        <p class="text-indigo-100 mb-8">Describe your project and let the AI draft a procurement list — or jump straight to posting a requirement.</p>
        <div class="flex flex-col sm:flex-row gap-3 justify-center items-center">
          <UButton size="lg" color="white" variant="solid" :to="appStore.localizedPath('/buyer/projects')" class="justify-center px-6 text-indigo-700 font-semibold">
            Start an AI Project
          </UButton>
          <UButton size="lg" color="indigo" variant="outline" :to="appStore.localizedPath('/post-request')" class="justify-center px-6 border-indigo-300 text-white hover:bg-indigo-700">
            Post a Requirement
          </UButton>
          <a :href="aislosSiteUrl" class="inline-flex items-center justify-center px-6 py-2.5 rounded-md text-sm font-medium text-indigo-100 hover:text-white transition-colors">
            ← Back to AinerWise 官网
          </a>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
definePageMeta({ layout: 'default' })

const appStore = useAppStore()
const aislosSiteUrl = useRuntimeConfig().public.aislosSiteUrl as string

const buyerSteps = [
  {
    title: 'Describe your project — AI drafts the list',
    body: 'Open AI Projects, describe what you are building and upload any documents. The AI turns it into a structured procurement list (BOQ) you can edit. It recommends — you stay in control.',
  },
  {
    title: 'Post it as a requirement (RFQ)',
    body: 'Publish the list as a requirement. Verified suppliers in your region are matched and invited to compete. No public price list — suppliers bid for your specific job.',
  },
  {
    title: 'Compare offers side by side',
    body: 'Offers come back with price, lead time, specs and supplier rating. The AI can rank and flag risks, but the choice is always yours.',
  },
  {
    title: 'Award and create the order',
    body: 'Pick the offer you want and award it. An order and a project workspace are created automatically so everything stays in one thread.',
  },
  {
    title: 'Milestones &amp; payment records — your money stays yours',
    body: 'A payment plan is recorded as milestones. AISLOS Market does not hold or escrow your funds — you pay suppliers directly and confirm each milestone. The platform keeps the ledger and the paper trail.',
  },
  {
    title: 'Project → asset → lifecycle service',
    body: 'As work is delivered, items become registered assets. Maintenance, inspections and AI reports keep the building serviceable long after handover.',
  },
]

const supplierSteps = [
  { title: 'Get verified', body: 'Submit your company and credentials once. Verification builds buyer trust.' },
  { title: 'Receive matched RFQs', body: 'Requirements that fit your categories and region land in your inbox.' },
  { title: 'Submit a competitive offer', body: 'Quote price, lead time and specs. Win on merit, not on ad spend.' },
  { title: 'Fulfill &amp; get rated', body: 'Deliver, log milestones, and grow your rating for the next job.' },
]

const governance = [
  {
    title: 'AI recommends, people decide',
    body: 'The AI drafts lists, ranks offers and flags risk — but it never auto-awards, auto-signs or releases anything. Every important decision needs a human.',
  },
  {
    title: 'No custody of your money',
    body: 'We are records-first. Payments are tracked as milestones in a ledger; the platform never holds, escrows or transfers customer funds. You pay suppliers directly.',
  },
  {
    title: 'Reviewed &amp; region-isolated',
    body: 'Important AI outputs go through admin review before they matter, verified suppliers are vetted, and your data is isolated by region.',
  },
]

useHead({
  title: 'How it works — AISLOS Market',
  meta: [{ name: 'description', content: 'How AISLOS Market and AinerWise work together: assess with AI, source from verified suppliers, operate for the building lifecycle.' }],
})
</script>
