<template>
  <div class="min-h-screen flex bg-slate-50 text-slate-900 font-sans">
    <!-- Admin Sidebar (Dense Navigation) -->
    <aside class="w-64 bg-slate-900 text-slate-300 border-r border-slate-800 flex flex-col sticky top-0 h-screen overflow-hidden">
      <div class="h-16 flex items-center px-4 border-b border-slate-800">
        <NuxtLink to="/admin/dashboard" class="text-xl font-bold text-white tracking-tight flex items-center">
          <UIcon name="i-heroicons-server-stack" class="w-6 h-6 text-indigo-400 mr-2" />
          {{ $config.public.appName }}
        </NuxtLink>
      </div>
      
      <!-- Staff Role Indicator -->
      <div class="px-4 py-3 border-b border-slate-800 bg-slate-800/50 flex items-center">
        <div class="w-8 h-8 rounded-full bg-indigo-500 text-white flex items-center justify-center font-bold text-sm">SA</div>
        <div class="ml-3">
          <div class="text-xs text-white font-medium">Super Admin</div>
          <div class="text-[10px] text-slate-400 flex items-center mt-0.5">
            <span class="w-1.5 h-1.5 rounded-full bg-green-400 mr-1.5"></span>
            Production Environment
          </div>
        </div>
      </div>
      
      <div class="flex-grow overflow-y-auto custom-scrollbar py-4">
        <nav class="space-y-0.5 px-2">
          <NuxtLink to="/admin/dashboard" class="flex items-center px-2 py-1.5 text-sm font-medium rounded-md text-white bg-slate-800">
            <UIcon name="i-heroicons-chart-pie" class="mr-3 w-5 h-5 text-indigo-400" />
            Dashboard
          </NuxtLink>
        </nav>
        
        <div class="mt-6">
          <h3 class="px-4 text-[10px] font-semibold text-slate-500 uppercase tracking-wider mb-1">Marketplace Operations</h3>
          <nav class="space-y-0.5 px-2">
            <NuxtLink to="/admin/intents" class="flex items-center px-2 py-1.5 text-sm font-medium rounded-md hover:text-white hover:bg-slate-800 transition-colors">
              <UIcon name="i-heroicons-document-magnifying-glass" class="mr-3 w-4 h-4 text-slate-400" />
              Buyer Intents
            </NuxtLink>
            <NuxtLink to="/admin/offers" class="flex items-center px-2 py-1.5 text-sm font-medium rounded-md hover:text-white hover:bg-slate-800 transition-colors">
              <UIcon name="i-heroicons-currency-dollar" class="mr-3 w-4 h-4 text-slate-400" />
              Offers
            </NuxtLink>
            <NuxtLink to="/admin/orders" class="flex items-center px-2 py-1.5 text-sm font-medium rounded-md hover:text-white hover:bg-slate-800 transition-colors">
              <UIcon name="i-heroicons-truck" class="mr-3 w-4 h-4 text-slate-400" />
              Orders & Escrow
            </NuxtLink>
            <NuxtLink to="/admin/disputes" class="flex items-center justify-between px-2 py-1.5 text-sm font-medium rounded-md hover:text-white hover:bg-slate-800 transition-colors">
              <div class="flex items-center">
                <UIcon name="i-heroicons-exclamation-triangle" class="mr-3 w-4 h-4 text-red-400" />
                Dispute Center
              </div>
              <UBadge color="red" size="sm" variant="solid" class="scale-75">4</UBadge>
            </NuxtLink>
          </nav>
        </div>

        <div class="mt-6">
          <h3 class="px-4 text-[10px] font-semibold text-slate-500 uppercase tracking-wider mb-1">User Management</h3>
          <nav class="space-y-0.5 px-2">
            <NuxtLink to="/admin/users" class="flex items-center px-2 py-1.5 text-sm font-medium rounded-md hover:text-white hover:bg-slate-800 transition-colors">
              <UIcon name="i-heroicons-users" class="mr-3 w-4 h-4 text-slate-400" />
              All Users
            </NuxtLink>
            <NuxtLink to="/admin/verifications" class="flex items-center justify-between px-2 py-1.5 text-sm font-medium rounded-md hover:text-white hover:bg-slate-800 transition-colors">
              <div class="flex items-center">
                <UIcon name="i-heroicons-shield-check" class="mr-3 w-4 h-4 text-slate-400" />
                KYB Verifications
              </div>
              <UBadge color="indigo" size="sm" variant="solid" class="scale-75">12</UBadge>
            </NuxtLink>
            <NuxtLink to="/admin/risk" class="flex items-center px-2 py-1.5 text-sm font-medium rounded-md hover:text-white hover:bg-slate-800 transition-colors">
              <UIcon name="i-heroicons-shield-exclamation" class="mr-3 w-4 h-4 text-slate-400" />
              Risk Flags
            </NuxtLink>
          </nav>
        </div>

        <div class="mt-6">
          <h3 class="px-4 text-[10px] font-semibold text-slate-500 uppercase tracking-wider mb-1">System</h3>
          <nav class="space-y-0.5 px-2">
            <NuxtLink to="/admin/categories" class="flex items-center px-2 py-1.5 text-sm font-medium rounded-md hover:text-white hover:bg-slate-800 transition-colors">
              <UIcon name="i-heroicons-rectangle-group" class="mr-3 w-4 h-4 text-slate-400" />
              Categories & Schema
            </NuxtLink>
            <NuxtLink to="/admin/ranking" class="flex items-center px-2 py-1.5 text-sm font-medium rounded-md hover:text-white hover:bg-slate-800 transition-colors">
              <UIcon name="i-heroicons-adjustments-horizontal" class="mr-3 w-4 h-4 text-slate-400" />
              Ranking Config
            </NuxtLink>
            <NuxtLink to="/admin/pricing-intel" class="flex items-center px-2 py-1.5 text-sm font-medium rounded-md hover:text-white hover:bg-slate-800 transition-colors">
              <UIcon name="i-heroicons-light-bulb" class="mr-3 w-4 h-4 text-slate-400" />
              Pricing Intel
            </NuxtLink>
            <NuxtLink to="/admin/audit" class="flex items-center px-2 py-1.5 text-sm font-medium rounded-md hover:text-white hover:bg-slate-800 transition-colors">
              <UIcon name="i-heroicons-clipboard-document-check" class="mr-3 w-4 h-4 text-slate-400" />
              Audit Logs
            </NuxtLink>
            <NuxtLink to="/admin/settings" class="flex items-center px-2 py-1.5 text-sm font-medium rounded-md hover:text-white hover:bg-slate-800 transition-colors">
              <UIcon name="i-heroicons-cog" class="mr-3 w-4 h-4 text-slate-400" />
              Platform Settings
            </NuxtLink>
          </nav>
        </div>
      </div>
    </aside>

    <!-- Main Content Area -->
    <div class="flex-1 flex flex-col h-screen overflow-hidden bg-slate-50">
      <!-- Top Header -->
      <header class="h-16 bg-white border-b border-slate-200 flex items-center justify-between px-6 z-10 shadow-sm">
        <div class="flex items-center w-full max-w-xl">
          <!-- Global Search -->
          <UInput icon="i-heroicons-magnifying-glass" placeholder="Search orders, users, intent IDs..." size="sm" class="w-full" :ui="{ rounded: 'rounded-md' }" />
        </div>
        
        <div class="flex items-center space-x-4">
          <div class="hidden lg:flex items-center space-x-2 border-r border-slate-200 pr-4">
            <USelect v-model="appStore.language" :options="appStore.languageOptions" option-attribute="label" value-attribute="code" size="sm" class="w-28" variant="none" @change="appStore.setLanguage" />
            <USelect v-model="appStore.currency" :options="appStore.currencyOptions" option-attribute="label" value-attribute="code" size="sm" class="w-36" variant="none" @change="appStore.setCurrency" />
          </div>
          <div class="text-xs font-mono text-slate-500 bg-slate-100 px-2 py-1 rounded hidden lg:block">
            UTC: {{ new Date().toISOString().substring(11, 16) }}
          </div>
          
          <UButton color="gray" variant="ghost" icon="i-heroicons-bell" aria-label="Alerts" />
          
          <UDropdown :items="[
            [{ label: 'Admin Settings', icon: 'i-heroicons-cog' }],
            [{ label: 'Sign out', icon: 'i-heroicons-arrow-right-on-rectangle' }]
          ]" :popper="{ placement: 'bottom-end' }">
            <UButton color="white" variant="ghost" trailing-icon="i-heroicons-chevron-down-20-solid">
              Admin Ops
            </UButton>
          </UDropdown>
        </div>
      </header>

      <!-- Page Content -->
      <main class="flex-1 overflow-y-auto p-6">
        <slot />
      </main>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useAppStore } from '~/stores/app'

const appStore = useAppStore()
</script>

<style scoped>
.custom-scrollbar::-webkit-scrollbar {
  width: 4px;
}
.custom-scrollbar::-webkit-scrollbar-track {
  background: transparent;
}
.custom-scrollbar::-webkit-scrollbar-thumb {
  background: #475569;
  border-radius: 4px;
}
</style>
