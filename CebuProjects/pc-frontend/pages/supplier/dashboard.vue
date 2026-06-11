<template>
  <div class="space-y-6">
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-2xl font-bold text-slate-900">{{ appStore.t('supplier.dashboard.title') }}</h1>
        <p class="text-sm text-slate-500 mt-1">{{ appStore.t('supplier.dashboard.subtitle') }}</p>
      </div>
      <div class="flex space-x-3 flex-wrap gap-2">
        <UButton to="/marketplace" color="gray" variant="outline" icon="i-heroicons-globe-alt">Browse Market</UButton>
        <UButton color="white" variant="solid" class="shadow-sm">{{ appStore.t('action.viewPublicProfile') }}</UButton>
        <UButton to="/supplier/inbox" color="indigo" icon="i-heroicons-inbox-arrow-down" class="shadow-md">{{ appStore.t('action.viewPings') }}</UButton>
      </div>
    </div>

    <!-- KPI Cards Grid -->
    <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
      <UCard class="bg-white" :ui="{ body: { padding: 'p-4 sm:p-5' } }">
        <div class="flex flex-col">
          <dt class="text-sm font-medium text-slate-500 mb-1">{{ appStore.t('supplier.dashboard.newPings') }}</dt>
          <dd class="text-2xl font-bold text-indigo-600">12</dd>
        </div>
      </UCard>
      
      <UCard class="bg-white" :ui="{ body: { padding: 'p-4 sm:p-5' } }">
        <div class="flex flex-col">
          <dt class="text-sm font-medium text-slate-500 mb-1">{{ appStore.t('supplier.dashboard.activeOffers') }}</dt>
          <dd class="text-2xl font-bold text-slate-900">24</dd>
        </div>
      </UCard>

      <UCard class="bg-white border-green-200" :ui="{ body: { padding: 'p-4 sm:p-5' } }">
        <div class="flex flex-col">
          <dt class="text-sm font-medium text-green-600 mb-1">{{ appStore.t('supplier.dashboard.awardedOrders') }}</dt>
          <dd class="text-2xl font-bold text-slate-900">3</dd>
        </div>
      </UCard>

      <UCard class="bg-white" :ui="{ body: { padding: 'p-4 sm:p-5' } }">
        <div class="flex flex-col">
          <dt class="text-sm font-medium text-slate-500 mb-1">{{ appStore.t('supplier.dashboard.pendingDelivery') }}</dt>
          <dd class="text-2xl font-bold text-slate-900">5</dd>
        </div>
      </UCard>

      <UCard class="bg-white" :ui="{ body: { padding: 'p-4 sm:p-5' } }">
        <div class="flex flex-col">
          <dt class="text-sm font-medium text-slate-500 mb-1">{{ appStore.t('supplier.dashboard.escrowPayout') }}</dt>
          <dd class="text-2xl font-bold text-slate-900">$12,450</dd>
        </div>
      </UCard>

      <UCard class="bg-white" :ui="{ body: { padding: 'p-4 sm:p-5' } }">
        <div class="flex flex-col">
          <dt class="text-sm font-medium text-slate-500 mb-1">{{ appStore.t('supplier.dashboard.responseSla') }}</dt>
          <dd class="text-2xl font-bold text-green-500">&lt; 15 mins</dd>
        </div>
      </UCard>

      <UCard class="bg-white" :ui="{ body: { padding: 'p-4 sm:p-5' } }">
        <div class="flex flex-col">
          <dt class="text-sm font-medium text-slate-500 mb-1">{{ appStore.t('supplier.dashboard.rating') }}</dt>
          <dd class="text-2xl font-bold text-slate-900 flex items-center">
            4.9 <UIcon name="i-heroicons-star" class="w-5 h-5 text-yellow-400 ml-1" />
          </dd>
        </div>
      </UCard>

      <UCard class="bg-white" :ui="{ body: { padding: 'p-4 sm:p-5' } }">
        <div class="flex flex-col">
          <dt class="text-sm font-medium text-slate-500 mb-1">{{ appStore.t('supplier.dashboard.disputeRate') }}</dt>
          <dd class="text-2xl font-bold text-green-500">0.5%</dd>
        </div>
      </UCard>
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <!-- New Matched Requests / Pings -->
      <UCard class="flex flex-col">
        <template #header>
          <div class="flex justify-between items-center">
            <div class="flex items-center space-x-2">
              <div class="w-2 h-2 bg-indigo-500 rounded-full"></div>
              <h3 class="text-lg font-medium text-slate-900">{{ appStore.t('supplier.dashboard.recentPings') }}</h3>
            </div>
            <UButton variant="ghost" color="indigo" size="sm" to="/supplier/inbox">{{ appStore.t('action.viewAll') }}</UButton>
          </div>
        </template>
        
        <div class="space-y-4">
          <div v-for="ping in pings" :key="ping.id" class="border border-slate-200 rounded-lg p-4 hover:border-indigo-300 transition-colors">
            <div class="flex justify-between items-start mb-2">
              <div>
                <h4 class="font-bold text-slate-900">{{ ping.title }}</h4>
                <div class="flex items-center text-xs text-slate-500 mt-1">
                  <UIcon name="i-heroicons-map-pin" class="w-3 h-3 mr-1" /> {{ ping.distance }} {{ appStore.t('supplier.dashboard.away') }}
                  <span class="mx-2">•</span>
                  <UIcon name="i-heroicons-clock" class="w-3 h-3 mr-1" /> {{ ping.timeAgo }}
                </div>
              </div>
              <UBadge v-if="ping.preFunded" color="green" size="xs" variant="subtle">{{ appStore.t('supplier.dashboard.preFunded') }}</UBadge>
            </div>
            <div class="flex justify-between items-center mt-4">
              <div class="text-sm font-medium text-slate-700">{{ appStore.t('supplier.dashboard.budget') }}: {{ ping.budget }}</div>
              <UButton size="sm" color="indigo" variant="soft" to="/supplier/inbox">{{ appStore.t('action.quoteNow') }}</UButton>
            </div>
          </div>
        </div>
      </UCard>

      <!-- Orders Requiring Action -->
      <UCard class="flex flex-col">
        <template #header>
          <div class="flex justify-between items-center">
            <div class="flex items-center space-x-2">
              <div class="w-2 h-2 bg-orange-500 rounded-full"></div>
              <h3 class="text-lg font-medium text-slate-900">{{ appStore.t('supplier.dashboard.actionRequired') }}</h3>
            </div>
          </div>
        </template>
        
        <div class="space-y-4">
          <div class="bg-orange-50 border border-orange-200 rounded-lg p-4 flex items-start">
            <UIcon name="i-heroicons-truck" class="w-6 h-6 text-orange-500 mr-3 mt-0.5" />
            <div class="flex-1">
              <h4 class="font-bold text-orange-900">{{ appStore.t('supplier.dashboard.deliveryProof') }}</h4>
              <p class="text-sm text-orange-800 mt-1">{{ appStore.t('supplier.dashboard.deliveryProofDesc') }}</p>
              <div class="mt-3">
                <UButton size="sm" color="orange" variant="solid">{{ appStore.t('action.uploadProof') }}</UButton>
              </div>
            </div>
          </div>

          <div class="bg-blue-50 border border-blue-200 rounded-lg p-4 flex items-start">
            <UIcon name="i-heroicons-chat-bubble-left-ellipsis" class="w-6 h-6 text-blue-500 mr-3 mt-0.5" />
            <div class="flex-1">
              <h4 class="font-bold text-blue-900">{{ appStore.t('supplier.dashboard.unreadMessage') }}</h4>
              <p class="text-sm text-blue-800 mt-1">{{ appStore.t('supplier.dashboard.unreadMessageDesc') }}</p>
              <div class="mt-3">
                <UButton size="sm" color="blue" variant="solid" to="/supplier/messages">{{ appStore.t('action.reply') }}</UButton>
              </div>
            </div>
          </div>
        </div>
      </UCard>
    </div>
  </div>
</template>

<script setup lang="ts">
definePageMeta({
  layout: 'supplier',
  middleware: ['supplier']
})

const appStore = useAppStore()

const pings = [
  { id: 1, title: '500 bags Portland Cement', distance: '4.2 km', timeAgo: '5 mins ago', preFunded: true, budget: '$2,000 - $2,500' },
  { id: 2, title: '1000m Copper Wire 12 AWG', distance: '1.5 km', timeAgo: '12 mins ago', preFunded: false, budget: 'Open' },
  { id: 3, title: 'Commercial AC Unit 5HP', distance: '8.0 km', timeAgo: '45 mins ago', preFunded: true, budget: '$1,500 Max' }
]
</script>
