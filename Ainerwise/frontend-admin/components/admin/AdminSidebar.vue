<template>
  <aside
    class="admin-sidebar w-64 flex-shrink-0 hidden lg:flex flex-col overflow-y-auto z-10"
    :class="{ 'collapsed': collapsed }"
  >
    <!-- Logo -->
    <div class="px-5 py-5 border-b border-white/5">
      <NuxtLink to="/" class="flex items-center gap-3">
        <div class="w-8 h-8 rounded-lg bg-gradient-to-br from-cyan-400 to-blue-600 flex items-center justify-center shadow-[0_0_20px_rgba(6,182,212,0.4)]">
          <span class="text-white font-black text-sm">A</span>
        </div>
        <div>
          <span class="text-base font-bold text-white tracking-wide">{{ portal.shortName }}</span>
          <span class="block text-[10px] text-cyan-400/80 font-medium tracking-widest uppercase">{{ portal.name }}</span>
        </div>
      </NuxtLink>
    </div>

    <!-- Navigation (accordion: only the active section is expanded) -->
    <nav class="flex-1 py-4 px-3 space-y-1 overflow-y-auto scrollbar-thin">
      <div v-for="section in menuSections" :key="section.key">
        <button
          type="button"
          class="w-full flex items-center justify-between gap-2 px-3 py-2 rounded-lg text-[10px] font-bold uppercase tracking-[0.2em] transition-colors hover:bg-white/5"
          :class="openSection === section.key ? 'text-cyan-400' : 'text-slate-500 hover:text-slate-300'"
          @click="toggleSection(section.key)"
        >
          <span>{{ section.title }}</span>
          <svg
            class="w-3.5 h-3.5 flex-shrink-0 transition-transform duration-200"
            :class="openSection === section.key ? 'rotate-90' : ''"
            fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2.5"
          >
            <path stroke-linecap="round" stroke-linejoin="round" d="m8.25 4.5 7.5 7.5-7.5 7.5" />
          </svg>
        </button>
        <div v-show="openSection === section.key" class="mt-1 mb-2 space-y-0.5">
          <NuxtLink
            v-for="item in section.items"
            :key="item.to"
            :to="item.to"
            class="admin-nav-item group flex items-center gap-3 px-3 py-2 text-[13px] rounded-lg transition-all duration-200 text-slate-400 hover:text-white hover:bg-white/5"
            active-class="!text-cyan-400 !bg-cyan-500/10 shadow-[inset_0_0_0_1px_rgba(6,182,212,0.2)] font-medium"
          >
            <component :is="item.icon" class="w-4 h-4 flex-shrink-0 opacity-60 group-hover:opacity-100 transition-opacity" />
            <span>{{ item.label }}</span>
            <span v-if="item.badge" class="ml-auto text-[10px] bg-red-500/20 text-red-400 px-1.5 py-0.5 rounded-full font-medium">{{ item.badge }}</span>
          </NuxtLink>
        </div>
      </div>
    </nav>

    <!-- Footer -->
    <div class="px-4 py-3 border-t border-white/5">
      <div class="flex items-center gap-2">
        <div class="w-2 h-2 rounded-full bg-emerald-400 shadow-[0_0_6px_rgba(52,211,153,0.6)] animate-pulse"></div>
        <span class="text-[11px] text-slate-500">System Online</span>
      </div>
    </div>
  </aside>
</template>

<script setup lang="ts">
import { h } from 'vue'
const { t } = useI18n({ useScope: 'global' })
const { portal, isPathAllowed } = usePortalMode()

const collapsed = ref(false)

// Simple SVG icon components
const IconDashboard = () => h('svg', { xmlns: 'http://www.w3.org/2000/svg', fill: 'none', viewBox: '0 0 24 24', 'stroke-width': '1.5', stroke: 'currentColor' }, [h('path', { 'stroke-linecap': 'round', 'stroke-linejoin': 'round', d: 'M3.75 6A2.25 2.25 0 016 3.75h2.25A2.25 2.25 0 0110.5 6v2.25a2.25 2.25 0 01-2.25 2.25H6a2.25 2.25 0 01-2.25-2.25V6zM3.75 15.75A2.25 2.25 0 016 13.5h2.25a2.25 2.25 0 012.25 2.25V18a2.25 2.25 0 01-2.25 2.25H6A2.25 2.25 0 013.75 18v-2.25zM13.5 6a2.25 2.25 0 012.25-2.25H18A2.25 2.25 0 0120.25 6v2.25A2.25 2.25 0 0118 10.5h-2.25a2.25 2.25 0 01-2.25-2.25V6zM13.5 15.75a2.25 2.25 0 012.25-2.25H18a2.25 2.25 0 012.25 2.25V18A2.25 2.25 0 0118 20.25h-2.25A2.25 2.25 0 0113.5 18v-2.25z' })])
const IconLeads = () => h('svg', { xmlns: 'http://www.w3.org/2000/svg', fill: 'none', viewBox: '0 0 24 24', 'stroke-width': '1.5', stroke: 'currentColor' }, [h('path', { 'stroke-linecap': 'round', 'stroke-linejoin': 'round', d: 'M15 19.128a9.38 9.38 0 002.625.372 9.337 9.337 0 004.121-.952 4.125 4.125 0 00-7.533-2.493M15 19.128v-.003c0-1.113-.285-2.16-.786-3.07M15 19.128v.106A12.318 12.318 0 018.624 21c-2.331 0-4.512-.645-6.374-1.766l-.001-.109a6.375 6.375 0 0111.964-3.07M12 6.375a3.375 3.375 0 11-6.75 0 3.375 3.375 0 016.75 0zm8.25 2.25a2.625 2.625 0 11-5.25 0 2.625 2.625 0 015.25 0z' })])
const IconProject = () => h('svg', { xmlns: 'http://www.w3.org/2000/svg', fill: 'none', viewBox: '0 0 24 24', 'stroke-width': '1.5', stroke: 'currentColor' }, [h('path', { 'stroke-linecap': 'round', 'stroke-linejoin': 'round', d: 'M2.25 12.75V12A2.25 2.25 0 014.5 9.75h15A2.25 2.25 0 0121.75 12v.75m-8.69-6.44l-2.12-2.12a1.5 1.5 0 00-1.061-.44H4.5A2.25 2.25 0 002.25 6v12a2.25 2.25 0 002.25 2.25h15A2.25 2.25 0 0021.75 18V9a2.25 2.25 0 00-2.25-2.25h-5.379a1.5 1.5 0 01-1.06-.44z' })])
const IconQuote = () => h('svg', { xmlns: 'http://www.w3.org/2000/svg', fill: 'none', viewBox: '0 0 24 24', 'stroke-width': '1.5', stroke: 'currentColor' }, [h('path', { 'stroke-linecap': 'round', 'stroke-linejoin': 'round', d: 'M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m0 12.75h7.5m-7.5 3H12M10.5 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z' })])
const IconProduct = () => h('svg', { xmlns: 'http://www.w3.org/2000/svg', fill: 'none', viewBox: '0 0 24 24', 'stroke-width': '1.5', stroke: 'currentColor' }, [h('path', { 'stroke-linecap': 'round', 'stroke-linejoin': 'round', d: 'm21 7.5-9-5.25L3 7.5m18 0-9 5.25m9-5.25v9l-9 5.25M3 7.5l9 5.25M3 7.5v9l9 5.25' })])
const IconCategory = () => h('svg', { xmlns: 'http://www.w3.org/2000/svg', fill: 'none', viewBox: '0 0 24 24', 'stroke-width': '1.5', stroke: 'currentColor' }, [h('path', { 'stroke-linecap': 'round', 'stroke-linejoin': 'round', d: 'M9.568 3H5.25A2.25 2.25 0 003 5.25v4.318c0 .597.237 1.17.659 1.591l9.581 9.581c.699.699 1.78.872 2.607.33a18.095 18.095 0 005.223-5.223c.542-.827.369-1.908-.33-2.607L11.16 3.66A2.25 2.25 0 009.568 3z' })])
const IconVendor = () => h('svg', { xmlns: 'http://www.w3.org/2000/svg', fill: 'none', viewBox: '0 0 24 24', 'stroke-width': '1.5', stroke: 'currentColor' }, [h('path', { 'stroke-linecap': 'round', 'stroke-linejoin': 'round', d: 'M13.5 21v-7.5a.75.75 0 01.75-.75h3a.75.75 0 01.75.75V21m-4.5 0H2.36m11.14 0H18m0 0h3.64m-1.39 0V9.349m-16.5 11.65V9.35m0 0a3.001 3.001 0 003.75-.615A2.993 2.993 0 009.75 9.75c.896 0 1.7-.393 2.25-1.016a2.993 2.993 0 002.25 1.016c.896 0 1.7-.393 2.25-1.016a3.001 3.001 0 003.75.614m-16.5 0a3.004 3.004 0 01-.621-4.72L4.318 3.44A1.5 1.5 0 015.378 3h13.243a1.5 1.5 0 011.06.44l1.19 1.189a3 3 0 01-.621 4.72' })])
const IconSolution = () => h('svg', { xmlns: 'http://www.w3.org/2000/svg', fill: 'none', viewBox: '0 0 24 24', 'stroke-width': '1.5', stroke: 'currentColor' }, [h('path', { 'stroke-linecap': 'round', 'stroke-linejoin': 'round', d: 'M12 18v-5.25m0 0a6.01 6.01 0 001.5-.189m-1.5.189a6.01 6.01 0 01-1.5-.189m3.75 7.478a12.06 12.06 0 01-4.5 0m3.75 2.383a14.406 14.406 0 01-3 0M14.25 18v-.192c0-.983.658-1.823 1.508-2.316a7.5 7.5 0 10-7.517 0c.85.493 1.509 1.333 1.509 2.316V18' })])
const IconTicket = () => h('svg', { xmlns: 'http://www.w3.org/2000/svg', fill: 'none', viewBox: '0 0 24 24', 'stroke-width': '1.5', stroke: 'currentColor' }, [h('path', { 'stroke-linecap': 'round', 'stroke-linejoin': 'round', d: 'M16.5 6v.75m0 3v.75m0 3v.75m0 3V18m-9-5.25h5.25M7.5 15h3M3.375 5.25c-.621 0-1.125.504-1.125 1.125v3.026a2.999 2.999 0 010 5.198v3.026c0 .621.504 1.125 1.125 1.125h17.25c.621 0 1.125-.504 1.125-1.125v-3.026a2.999 2.999 0 010-5.198V6.375c0-.621-.504-1.125-1.125-1.125H3.375z' })])
const IconInquiry = () => h('svg', { xmlns: 'http://www.w3.org/2000/svg', fill: 'none', viewBox: '0 0 24 24', 'stroke-width': '1.5', stroke: 'currentColor' }, [h('path', { 'stroke-linecap': 'round', 'stroke-linejoin': 'round', d: 'M8.625 9.75a.375.375 0 11-.75 0 .375.375 0 01.75 0zm0 0H8.25m4.125 0a.375.375 0 11-.75 0 .375.375 0 01.75 0zm0 0H12m4.125 0a.375.375 0 11-.75 0 .375.375 0 01.75 0zm0 0h-.375m-13.5 3.01c0 1.6 1.123 2.994 2.707 3.227 1.087.16 2.185.283 3.293.369V21l4.184-4.183a1.14 1.14 0 01.778-.332 48.294 48.294 0 005.83-.498c1.585-.233 2.708-1.626 2.708-3.228V6.741c0-1.602-1.123-2.995-2.707-3.228A48.394 48.394 0 0012 3c-2.392 0-4.744.175-7.043.513C3.373 3.746 2.25 5.14 2.25 6.741v6.018z' })])
const IconUser = () => h('svg', { xmlns: 'http://www.w3.org/2000/svg', fill: 'none', viewBox: '0 0 24 24', 'stroke-width': '1.5', stroke: 'currentColor' }, [h('path', { 'stroke-linecap': 'round', 'stroke-linejoin': 'round', d: 'M15.75 6a3.75 3.75 0 11-7.5 0 3.75 3.75 0 017.5 0zM4.501 20.118a7.5 7.5 0 0114.998 0A17.933 17.933 0 0112 21.75c-2.676 0-5.216-.584-7.499-1.632z' })])
const IconCompany = () => h('svg', { xmlns: 'http://www.w3.org/2000/svg', fill: 'none', viewBox: '0 0 24 24', 'stroke-width': '1.5', stroke: 'currentColor' }, [h('path', { 'stroke-linecap': 'round', 'stroke-linejoin': 'round', d: 'M3.75 21h16.5M4.5 3h15M5.25 3v18m13.5-18v18M9 6.75h1.5m-1.5 3h1.5m-1.5 3h1.5m3-6H15m-1.5 3H15m-1.5 3H15M9 21v-3.375c0-.621.504-1.125 1.125-1.125h3.75c.621 0 1.125.504 1.125 1.125V21' })])
const IconAI = () => h('svg', { xmlns: 'http://www.w3.org/2000/svg', fill: 'none', viewBox: '0 0 24 24', 'stroke-width': '1.5', stroke: 'currentColor' }, [h('path', { 'stroke-linecap': 'round', 'stroke-linejoin': 'round', d: 'M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09zM18.259 8.715L18 9.75l-.259-1.035a3.375 3.375 0 00-2.455-2.456L14.25 6l1.036-.259a3.375 3.375 0 002.455-2.456L18 2.25l.259 1.035a3.375 3.375 0 002.455 2.456L21.75 6l-1.036.259a3.375 3.375 0 00-2.455 2.456zM16.894 20.567L16.5 21.75l-.394-1.183a2.25 2.25 0 00-1.423-1.423L13.5 18.75l1.183-.394a2.25 2.25 0 001.423-1.423l.394-1.183.394 1.183a2.25 2.25 0 001.423 1.423l1.183.394-1.183.394a2.25 2.25 0 00-1.423 1.423z' })])
const IconGear = () => h('svg', { xmlns: 'http://www.w3.org/2000/svg', fill: 'none', viewBox: '0 0 24 24', 'stroke-width': '1.5', stroke: 'currentColor' }, [h('path', { 'stroke-linecap': 'round', 'stroke-linejoin': 'round', d: 'M9.594 3.94c.09-.542.56-.94 1.11-.94h2.593c.55 0 1.02.398 1.11.94l.213 1.281c.063.374.313.686.645.87.074.04.147.083.22.127.324.196.72.257 1.075.124l1.217-.456a1.125 1.125 0 011.37.49l1.296 2.247a1.125 1.125 0 01-.26 1.431l-1.003.827c-.293.24-.438.613-.431.992a6.759 6.759 0 010 .255c-.007.378.138.75.43.99l1.005.828c.424.35.534.954.26 1.43l-1.298 2.247a1.125 1.125 0 01-1.369.491l-1.217-.456c-.355-.133-.75-.072-1.076.124a6.57 6.57 0 01-.22.128c-.331.183-.581.495-.644.869l-.213 1.28c-.09.543-.56.941-1.11.941h-2.594c-.55 0-1.02-.398-1.11-.94l-.213-1.281c-.062-.374-.312-.686-.644-.87a6.52 6.52 0 01-.22-.127c-.325-.196-.72-.257-1.076-.124l-1.217.456a1.125 1.125 0 01-1.369-.49l-1.297-2.247a1.125 1.125 0 01.26-1.431l1.004-.827c.292-.24.437-.613.43-.992a6.932 6.932 0 010-.255c.007-.378-.138-.75-.43-.99l-1.004-.828a1.125 1.125 0 01-.26-1.43l1.297-2.247a1.125 1.125 0 011.37-.491l1.216.456c.356.133.751.072 1.076-.124.072-.044.146-.087.22-.128.332-.183.582-.495.644-.869l.214-1.281z' })])
const IconEvent = () => h('svg', { xmlns: 'http://www.w3.org/2000/svg', fill: 'none', viewBox: '0 0 24 24', 'stroke-width': '1.5', stroke: 'currentColor' }, [h('path', { 'stroke-linecap': 'round', 'stroke-linejoin': 'round', d: 'M3.75 13.5l10.5-11.25L12 10.5h8.25L9.75 21.75 12 13.5H3.75z' })])
const IconCert = () => h('svg', { xmlns: 'http://www.w3.org/2000/svg', fill: 'none', viewBox: '0 0 24 24', 'stroke-width': '1.5', stroke: 'currentColor' }, [h('path', { 'stroke-linecap': 'round', 'stroke-linejoin': 'round', d: 'M9 12.75L11.25 15 15 9.75M21 12c0 1.268-.63 2.39-1.593 3.068a3.745 3.745 0 01-1.043 3.296 3.745 3.745 0 01-3.296 1.043A3.745 3.745 0 0112 21c-1.268 0-2.39-.63-3.068-1.593a3.746 3.746 0 01-3.296-1.043 3.745 3.745 0 01-1.043-3.296A3.745 3.745 0 013 12c0-1.268.63-2.39 1.593-3.068a3.745 3.745 0 011.043-3.296 3.746 3.746 0 013.296-1.043A3.746 3.746 0 0112 3c1.268 0 2.39.63 3.068 1.593a3.746 3.746 0 013.296 1.043 3.746 3.746 0 011.043 3.296A3.745 3.745 0 0121 12z' })])
const IconGlobe = () => h('svg', { xmlns: 'http://www.w3.org/2000/svg', fill: 'none', viewBox: '0 0 24 24', 'stroke-width': '1.5', stroke: 'currentColor' }, [h('path', { 'stroke-linecap': 'round', 'stroke-linejoin': 'round', d: 'M12 21a9.004 9.004 0 008.716-6.747M12 21a9.004 9.004 0 01-8.716-6.747M12 21c2.485 0 4.5-4.03 4.5-9S14.485 3 12 3m0 18c-2.485 0-4.5-4.03-4.5-9S9.515 3 12 3m0 0a8.997 8.997 0 017.843 4.582M12 3a8.997 8.997 0 00-7.843 4.582m15.686 0A11.953 11.953 0 0112 10.5c-2.998 0-5.74-1.1-7.843-2.918m15.686 0A8.959 8.959 0 0121 12c0 .778-.099 1.533-.284 2.253m0 0A17.919 17.919 0 0112 16.5c-3.162 0-6.133-.815-8.716-2.247m0 0A9.015 9.015 0 013 12c0-1.605.42-3.113 1.157-4.418' })])
const IconAudit = () => h('svg', { xmlns: 'http://www.w3.org/2000/svg', fill: 'none', viewBox: '0 0 24 24', 'stroke-width': '1.5', stroke: 'currentColor' }, [h('path', { 'stroke-linecap': 'round', 'stroke-linejoin': 'round', d: 'M12 6v6h4.5m4.5 0a9 9 0 11-18 0 9 9 0 0118 0z' })])
const IconShield = () => h('svg', { xmlns: 'http://www.w3.org/2000/svg', fill: 'none', viewBox: '0 0 24 24', 'stroke-width': '1.5', stroke: 'currentColor' }, [h('path', { 'stroke-linecap': 'round', 'stroke-linejoin': 'round', d: 'M9 12.75L11.25 15 15 9.75m-3-7.036A11.959 11.959 0 013.598 6 11.99 11.99 0 003 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.285z' })])
const IconPartner = () => h('svg', { xmlns: 'http://www.w3.org/2000/svg', fill: 'none', viewBox: '0 0 24 24', 'stroke-width': '1.5', stroke: 'currentColor' }, [h('path', { 'stroke-linecap': 'round', 'stroke-linejoin': 'round', d: 'M11.42 15.17l-5.1 3.04a1.5 1.5 0 01-2.18-1.584l.974-5.676-4.126-4.023a1.5 1.5 0 01.832-2.56l5.698-.828L9.99 1.064a1.5 1.5 0 012.688 0l2.548 5.164 5.698.828a1.5 1.5 0 01.832 2.56l-4.126 4.023.974 5.676a1.5 1.5 0 01-2.18 1.584l-5.1-3.04z' })])
const IconPkg = () => h('svg', { xmlns: 'http://www.w3.org/2000/svg', fill: 'none', viewBox: '0 0 24 24', 'stroke-width': '1.5', stroke: 'currentColor' }, [h('path', { 'stroke-linecap': 'round', 'stroke-linejoin': 'round', d: 'M20.25 7.5l-.625 10.632a2.25 2.25 0 01-2.247 2.118H6.622a2.25 2.25 0 01-2.247-2.118L3.75 7.5M10 11.25h4M3.375 7.5h17.25c.621 0 1.125-.504 1.125-1.125v-1.5c0-.621-.504-1.125-1.125-1.125H3.375c-.621 0-1.125.504-1.125 1.125v1.5c0 .621.504 1.125 1.125 1.125z' })])
const IconProposal = () => h('svg', { xmlns: 'http://www.w3.org/2000/svg', fill: 'none', viewBox: '0 0 24 24', 'stroke-width': '1.5', stroke: 'currentColor' }, [h('path', { 'stroke-linecap': 'round', 'stroke-linejoin': 'round', d: 'M3.75 3v11.25A2.25 2.25 0 006 16.5h2.25M3.75 3h-1.5m1.5 0h16.5m0 0h1.5m-1.5 0v11.25A2.25 2.25 0 0118 16.5h-2.25m-7.5 0h7.5m-7.5 0l-1 3m8.5-3l1 3m0 0l.5 1.5m-.5-1.5h-9.5m0 0l-.5 1.5M9 11.25v1.5M12 9v3.75m3-6v6' })])
const IconLink = () => h('svg', { xmlns: 'http://www.w3.org/2000/svg', fill: 'none', viewBox: '0 0 24 24', 'stroke-width': '1.5', stroke: 'currentColor' }, [h('path', { 'stroke-linecap': 'round', 'stroke-linejoin': 'round', d: 'M13.19 8.688a4.5 4.5 0 011.242 7.244l-4.5 4.5a4.5 4.5 0 01-6.364-6.364l1.757-1.757m13.35-.622l1.757-1.757a4.5 4.5 0 00-6.364-6.364l-4.5 4.5a4.5 4.5 0 001.242 7.244' })])
const IconPulse = () => h('svg', { xmlns: 'http://www.w3.org/2000/svg', fill: 'none', viewBox: '0 0 24 24', 'stroke-width': '1.5', stroke: 'currentColor' }, [h('path', { 'stroke-linecap': 'round', 'stroke-linejoin': 'round', d: 'M3.75 12h3.75l1.5-4.5 3 9 1.5-4.5h3.75' })])
const IconWrench = () => h('svg', { xmlns: 'http://www.w3.org/2000/svg', fill: 'none', viewBox: '0 0 24 24', 'stroke-width': '1.5', stroke: 'currentColor' }, [h('path', { 'stroke-linecap': 'round', 'stroke-linejoin': 'round', d: 'M11.42 15.17L17.25 21A2.652 2.652 0 0021 17.25l-5.877-5.877M11.42 15.17l2.496-3.03c.317-.384.74-.626 1.208-.766M11.42 15.17l-4.655 5.653a2.548 2.548 0 11-3.586-3.586l6.837-5.63m5.108-.233c.55-.164 1.163-.188 1.743-.14a4.5 4.5 0 004.486-6.336l-3.276 3.277a3.004 3.004 0 01-2.25-2.25l3.276-3.276a4.5 4.5 0 00-6.336 4.486c.091 1.076-.071 2.264-.904 2.95l-.102.085m-1.745 1.437L5.909 7.5H4.5L2.25 3.75l1.5-1.5L7.5 4.5v1.409l4.26 4.26m-1.745 1.437l1.745-1.437m6.615 8.206L15.75 15.75M4.867 19.125h.008v.008h-.008v-.008z' })])

const allMenuSections = computed(() => [
  {
    key: 'overview', title: t('admin.sectionOverview'),
    items: [
      { to: '/', label: t('admin.dashboard'), icon: IconDashboard },
    ],
  },
  {
    key: 'business', title: t('admin.sectionBusiness'),
    items: [
      { to: '/leads', label: t('admin.leads'), icon: IconLeads },
      { to: '/projects', label: t('admin.projects'), icon: IconProject },
      { to: '/quotes', label: t('admin.quotes'), icon: IconQuote },
      { to: '/proposals', label: t('admin.proposals'), icon: IconProposal },
      { to: '/tickets', label: t('admin.tickets'), icon: IconTicket },
      { to: '/inquiries', label: t('admin.inquiries'), icon: IconInquiry },
    ],
  },
  {
    key: 'catalog', title: t('admin.sectionCatalog'),
    items: [
      { to: '/products', label: t('admin.products'), icon: IconProduct },
      { to: '/store-orders', label: t('admin.storeOrders'), icon: IconPkg },
      { to: '/categories', label: t('admin.categories'), icon: IconCategory },
      { to: '/solutions', label: t('admin.solutions'), icon: IconSolution },
      { to: '/service-packages', label: t('admin.servicePackages'), icon: IconPkg },
      { to: '/compatibility', label: t('admin.compatibility'), icon: IconLink },
      { to: '/warranty-policies', label: t('admin.warrantyPolicies'), icon: IconShield },
    ],
  },
  {
    key: 'lifecycle', title: t('admin.sectionLifecycle'),
    items: [
      { to: '/monitoring-points', label: t('admin.monitoringPoints'), icon: IconPulse },
      { to: '/amc-contracts', label: t('admin.amcContracts'), icon: IconCert },
      { to: '/supplier-warranties', label: t('admin.supplierWarranties'), icon: IconShield },
      { to: '/customer-warranties', label: t('admin.customerWarranties'), icon: IconShield },
      { to: '/inventory', label: t('admin.spareInventory'), icon: IconPkg },
      { to: '/maintenance', label: t('admin.maintenance'), icon: IconWrench },
      { to: '/calibration', label: t('admin.calibration'), icon: IconCert },
    ],
  },
  {
    key: 'marketingIntegration', title: t('admin.sectionMarketingIntegration'),
    items: [
      { to: '/marketing/integration', label: t('admin.marketingIntegrationHub'), icon: IconLink },
      { to: '/marketing/briefs', label: t('admin.creativeBriefs'), icon: IconProposal },
      { to: '/marketing/clients', label: t('admin.integrationClients'), icon: IconShield },
      { to: '/marketing/imported-assets', label: t('admin.importedAssets'), icon: IconPkg },
    ],
  },
  {
    key: 'crm', title: t('admin.sectionCrm'),
    items: [
      { to: '/marketing', label: t('admin.marketingAutomation'), icon: IconEvent },
      { to: '/lifecycle-dashboard', label: t('admin.lifecycleDashboard'), icon: IconDashboard },
      { to: '/renewal-queue', label: t('admin.renewalQueue'), icon: IconEvent },
      { to: '/supplier-scorecards', label: t('admin.supplierScorecards'), icon: IconCert },
    ],
  },
  {
    key: 'finance', title: t('admin.sectionFinance'),
    items: [
      { to: '/project-finance', label: t('admin.projectFinance'), icon: IconQuote },
      { to: '/platform-fee-rules', label: t('admin.platformFeeRules'), icon: IconGear },
    ],
  },
  {
    key: 'network', title: t('admin.sectionNetwork'),
    items: [
      { to: '/vendors', label: t('admin.vendors'), icon: IconVendor },
      { to: '/service-partners', label: t('admin.servicePartners'), icon: IconPartner },
      { to: '/rfqs', label: t('admin.rfqs'), icon: IconPartner },
      { to: '/payment-plans', label: t('admin.paymentPlans'), icon: IconGear },
      { to: '/sites', label: t('admin.sitesAssets'), icon: IconCompany },
      { to: '/case-library', label: t('admin.caseLibrary'), icon: IconAI },
    ],
  },
  {
    key: 'users', title: t('admin.sectionUsers'),
    items: [
      { to: '/users', label: t('admin.users'), icon: IconUser },
      { to: '/companies', label: t('admin.companies'), icon: IconCompany },
    ],
  },
  {
    key: 'system', title: t('admin.sectionSystem'),
    items: [
      { to: '/agents', label: t('admin.aiEmployees'), icon: IconAI },
      { to: '/marketplace', label: t('admin.agentMarketplace'), icon: IconPkg },
      { to: '/agent-missions', label: t('admin.agentMissions'), icon: IconAI },
      { to: '/business-brain', label: t('admin.businessBrain'), icon: IconAI },
      { to: '/ai-runs', label: t('admin.aiRuns'), icon: IconAI },
      { to: '/ai-reviews', label: t('admin.aiReviews'), icon: IconAI },
      { to: '/knowledge', label: t('admin.knowledge'), icon: IconAI },
      { to: '/marketing-studio', label: t('admin.marketingStudio'), icon: IconAI },
      { to: '/documents', label: t('admin.documentCenter'), icon: IconGear },
      { to: '/integration-events', label: t('admin.events'), icon: IconEvent },
      { to: '/certifications', label: t('admin.certifications'), icon: IconCert },
      { to: '/regions', label: t('admin.regions'), icon: IconGlobe },
      { to: '/audit-logs', label: t('admin.auditLogs'), icon: IconAudit },
      { to: '/settings', label: t('admin.settings'), icon: IconGear },
    ],
  },
])

const menuSections = computed(() => allMenuSections.value
  .map(section => ({ ...section, items: section.items.filter(item => isPathAllowed(item.to)) }))
  .filter(section => section.items.length > 0))

// Accordion: keep only the section containing the current route expanded so the
// sidebar stays short and never needs scrolling after navigation.
const route = useRoute()
const openSection = ref<string | null>(null)

function sectionForPath(path: string): string | null {
  let best: { key: string; len: number } | null = null
  for (const section of menuSections.value) {
    for (const item of section.items) {
      const to = item.to as string
      const match = to === '/' ? path === '/' : (path === to || path.startsWith(to + '/'))
      if (match && (!best || to.length > best.len)) {
        best = { key: section.key, len: to.length }
      }
    }
  }
  return best?.key ?? null
}

function toggleSection(key: string) {
  openSection.value = openSection.value === key ? null : key
}

watch(
  () => route.path,
  (path) => {
    const section = sectionForPath(path)
    if (section) openSection.value = section
  },
  { immediate: true },
)
</script>

<style scoped>
.admin-sidebar {
  background: linear-gradient(180deg, rgba(15,23,42,0.98) 0%, rgba(10,15,30,0.99) 100%);
  border-right: 1px solid rgba(255,255,255,0.06);
  box-shadow: 4px 0 24px rgba(0,0,0,0.3);
}
.scrollbar-thin::-webkit-scrollbar { width: 4px; }
.scrollbar-thin::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.1); border-radius: 2px; }
.scrollbar-thin::-webkit-scrollbar-track { background: transparent; }
</style>
