<template>
  <div class="min-h-screen flex bg-slate-50 text-slate-900">
    <!-- Sidebar Navigation -->
    <aside class="w-64 bg-slate-900 border-r border-slate-800 hidden md:flex flex-col sticky top-0 h-screen text-slate-300">
      <div class="h-16 flex items-center px-6 border-b border-slate-800">
        <NuxtLink to="/" class="text-xl font-bold text-white tracking-tight flex items-center">
          <UIcon name="i-heroicons-globe-europe-africa" class="w-6 h-6 text-indigo-400 mr-2" />
          {{ $config.public.appName }}
        </NuxtLink>
        <div class="ml-2 px-2 py-0.5 bg-indigo-500/20 text-indigo-300 text-[10px] font-bold rounded">{{ appStore.t('layout.supplierBadge') }}</div>
      </div>
      
      <div :key="supplierNavRenderKey" class="flex-grow py-6 px-4 overflow-y-auto">
        <NuxtLink
          to="/marketplace"
          class="mb-6 flex items-center justify-between rounded-2xl border border-emerald-500/20 bg-gradient-to-r from-emerald-500/10 to-cyan-500/10 px-4 py-3 transition hover:border-emerald-400/40 hover:bg-emerald-500/15"
        >
          <div>
            <p class="text-[11px] font-semibold uppercase tracking-[0.16em] text-emerald-300">Shopping Flow</p>
            <p class="mt-1 text-sm font-semibold text-white">Back to Marketplace</p>
            <p class="mt-1 text-xs text-slate-300">Jump back to live demand and product discovery anytime.</p>
          </div>
          <UIcon name="i-heroicons-globe-alt" class="h-5 w-5 flex-shrink-0 text-emerald-300" />
        </NuxtLink>

        <nav class="space-y-1">
          <NuxtLink
            v-for="item in mainNav"
            :key="item.to"
            :to="item.to"
            custom
            v-slot="{ href, navigate, isActive }"
          >
            <a
              :href="href"
              :aria-current="isActive ? 'page' : undefined"
              class="flex items-center px-3 py-2 text-sm font-medium rounded-md transition-colors"
              :class="navItemClass(isActive)"
              @click="navigate"
            >
              <UIcon :name="item.icon" class="mr-3 w-5 h-5" :class="navIconClass(isActive)" />
              {{ item.label }}
              <UBadge v-if="item.badge" :color="item.badgeColor || 'indigo'" size="sm" class="ml-auto">{{ item.badge }}</UBadge>
            </a>
          </NuxtLink>
        </nav>

        <div class="mt-8">
          <h3 class="px-3 text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2">{{ appStore.t('layout.catalogRules') }}</h3>
          <nav class="space-y-1">
            <NuxtLink
              v-for="item in catalogNav"
              :key="item.to"
              :to="item.to"
              custom
              v-slot="{ href, navigate, isActive }"
            >
              <a
                :href="href"
                :aria-current="isActive ? 'page' : undefined"
                class="flex items-center px-3 py-2 text-sm font-medium rounded-md transition-colors"
                :class="navItemClass(isActive)"
                @click="navigate"
              >
                <UIcon :name="item.icon" class="mr-3 w-5 h-5" :class="navIconClass(isActive)" />
                {{ item.label }}
              </a>
            </NuxtLink>
          </nav>
        </div>

        <div class="mt-8">
          <h3 class="px-3 text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2">{{ appStore.t('layout.business') }}</h3>
          <nav class="space-y-1">
            <NuxtLink
              v-for="item in businessNav"
              :key="item.to"
              :to="item.to"
              custom
              v-slot="{ href, navigate, isActive }"
            >
              <a
                :href="href"
                :aria-current="isActive ? 'page' : undefined"
                class="flex items-center px-3 py-2 text-sm font-medium rounded-md transition-colors"
                :class="navItemClass(isActive)"
                @click="navigate"
              >
                <UIcon :name="item.icon" class="mr-3 w-5 h-5" :class="navIconClass(isActive)" />
                {{ item.label }}
              </a>
            </NuxtLink>
          </nav>
        </div>
      </div>
      
      <div class="p-4 border-t border-slate-800 bg-slate-900">
        <UDropdown :items="userMenuItems" :popper="{ placement: 'top-start' }">
          <button class="flex w-full items-center rounded-2xl border border-transparent px-2 py-2 text-left transition hover:border-slate-700 hover:bg-slate-800/70">
            <UAvatar src="https://i.pravatar.cc/150?u=supplierco" alt="Supplier" />
            <div class="ml-3 min-w-0 flex-1 overflow-hidden">
              <p class="truncate text-sm font-medium text-white">{{ authStore.displayName }}</p>
              <div class="mt-0.5 flex items-center text-xs text-green-400">
                <UIcon name="i-heroicons-shield-check" class="mr-1 h-3 w-3" />
                {{ appStore.t('layout.verifiedSupplier') }}
              </div>
            </div>
            <UIcon name="i-heroicons-chevron-up-down" class="h-4 w-4 flex-shrink-0 text-slate-400" />
          </button>
        </UDropdown>
      </div>
    </aside>

    <!-- Main Content Area -->
    <div class="flex-1 flex flex-col overflow-hidden">
      <!-- Top Header -->
      <header class="h-16 bg-white border-b border-slate-200 flex items-center justify-between px-6 z-10">
        <div class="flex items-center gap-3 min-w-0">
          <UButton
            to="/marketplace"
            color="emerald"
            variant="soft"
            icon="i-heroicons-globe-alt"
            size="sm"
            class="hidden lg:inline-flex whitespace-nowrap"
          >
            Marketplace
          </UButton>
          <h2 class="text-lg font-semibold text-slate-800 hidden sm:block">{{ appStore.t('layout.supplierPortal') }}</h2>
        </div>
        
        <div class="flex items-center space-x-4">
          <ClientOnly>
            <div class="hidden lg:flex items-center space-x-2 border-r border-slate-200 pr-4">
              <USelect v-model="appStore.language" :options="appStore.languageOptions" option-attribute="label" value-attribute="code" size="sm" class="w-28" variant="none" @update:model-value="appStore.setLanguage" />
              <USelect v-model="appStore.currency" :options="appStore.currencyOptions" option-attribute="label" value-attribute="code" size="sm" class="w-36" variant="none" @update:model-value="appStore.setCurrency" />
            </div>
          </ClientOnly>
          <div class="flex items-center text-sm font-medium text-green-600 bg-green-50 px-3 py-1.5 rounded-full border border-green-100">
            <div class="w-2 h-2 rounded-full bg-green-500 mr-2 animate-pulse"></div>
            {{ appStore.t('layout.onlinePings') }}
          </div>
          
          <div class="relative" ref="notifRef">
            <UButton
              color="gray"
              variant="ghost"
              icon="i-heroicons-bell"
              aria-label="Notifications"
              class="relative"
              @click="toggleNotif"
            >
              <span v-if="unreadCount > 0" class="absolute top-0 right-0 block h-2 w-2 rounded-full bg-red-400 ring-2 ring-white" />
            </UButton>

            <Transition name="notif">
              <div
                v-if="showNotif"
                class="absolute right-0 mt-2 w-80 bg-white border border-slate-200 rounded-2xl shadow-xl z-50 overflow-hidden"
              >
                <div class="flex items-center justify-between px-4 py-3 border-b border-slate-100">
                  <h4 class="text-sm font-semibold text-slate-900">
                    Notifications
                    <UBadge v-if="unreadCount > 0" color="red" size="xs" class="ml-2">{{ unreadCount }}</UBadge>
                  </h4>
                  <button
                    v-if="unreadCount > 0"
                    class="text-xs text-indigo-600 hover:underline"
                    @click.stop="markAllRead"
                  >
                    Mark all read
                  </button>
                </div>

                <div class="max-h-72 overflow-y-auto divide-y divide-slate-50">
                  <div v-if="notifLoading" class="py-8 text-center text-xs text-slate-400">
                    Loading...
                  </div>
                  <div v-else-if="notifications.length === 0" class="py-10 text-center text-slate-400">
                    <div class="text-3xl mb-2">🔔</div>
                    <p class="text-xs">No notifications yet</p>
                  </div>
                  <button
                    v-for="n in notifications"
                    :key="n.id"
                    :class="['w-full text-left px-4 py-3 hover:bg-slate-50 transition-colors', !n.read_at ? 'bg-indigo-50' : '']"
                    @click="openNotification(n)"
                  >
                    <div class="flex items-start gap-3">
                      <span class="text-lg flex-shrink-0">{{ notifIcon(n.notification_type) }}</span>
                      <div class="flex-1 min-w-0">
                        <p class="text-xs font-semibold text-slate-900 leading-snug">{{ notificationTitle(n) }}</p>
                        <p class="text-xs text-slate-500 mt-0.5 line-clamp-2">{{ n.body }}</p>
                        <p class="text-[10px] text-slate-400 mt-1">{{ timeAgo(n.created_at) }}</p>
                      </div>
                      <div v-if="!n.read_at" class="w-2 h-2 rounded-full bg-indigo-500 flex-shrink-0 mt-1" />
                    </div>
                  </button>
                </div>

                <div class="border-t border-slate-100 px-4 py-2">
                  <NuxtLink to="/supplier/notifications" class="text-xs text-indigo-600 hover:underline" @click="showNotif = false">
                    View all notifications →
                  </NuxtLink>
                </div>
              </div>
            </Transition>
          </div>
          
          <UDropdown :items="userMenuItems" :popper="{ placement: 'bottom-end' }">
            <UButton color="white" variant="ghost" trailing-icon="i-heroicons-chevron-down-20-solid" class="hidden sm:flex">
              {{ appStore.t('layout.myBusiness') }}
            </UButton>
          </UDropdown>
        </div>
      </header>

      <!-- Page Content -->
      <main class="flex-1 overflow-y-auto bg-slate-50 p-6">
        <slot />
      </main>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useAppStore } from '~/stores/app'
import { useAuthStore } from '~/stores/auth'

const appStore = useAppStore()
const authStore = useAuthStore()
const config = useRuntimeConfig()
const route = useRoute()

interface Notification {
  id: string
  subject: string | null
  body: string
  notification_type: string
  read_at: string | null
  created_at: string
}

const mainNav = computed(() => [
  { to: '/supplier/dashboard', icon: 'i-heroicons-presentation-chart-line', label: appStore.t('supplier.nav.dashboard') },
  { to: '/supplier/inbox', icon: 'i-heroicons-inbox-arrow-down', label: appStore.t('supplier.nav.inbox'), badge: '12', badgeColor: 'indigo' },
  { to: '/supplier/offers', icon: 'i-heroicons-document-text', label: appStore.t('supplier.nav.offers') },
  { to: '/supplier/orders', icon: 'i-heroicons-truck', label: appStore.t('supplier.nav.orders'), badge: '2', badgeColor: 'red' },
  { to: '/supplier/messages', icon: 'i-heroicons-chat-bubble-left-right', label: appStore.t('supplier.nav.messages') },
])

const catalogNav = computed(() => [
  { to: '/supplier/catalog', icon: 'i-heroicons-rectangle-group', label: appStore.t('supplier.nav.catalog') },
  { to: '/supplier/triggers', icon: 'i-heroicons-bolt', label: appStore.t('supplier.nav.triggers') },
])

const businessNav = computed(() => [
  { to: '/supplier/payouts', icon: 'i-heroicons-banknotes', label: appStore.t('supplier.nav.payouts') },
  { to: '/supplier/reviews', icon: 'i-heroicons-star', label: appStore.t('supplier.nav.reviews') },
  { to: '/supplier/settings', icon: 'i-heroicons-cog-8-tooth', label: appStore.t('supplier.nav.settings') },
])

const userMenuItems = computed(() => [
  [
    { label: appStore.t('layout.companyProfile'), icon: 'i-heroicons-building-office', click: () => navigateTo('/supplier/settings') },
    { label: 'Ship-from Addresses', icon: 'i-heroicons-map-pin', click: () => navigateTo('/supplier/settings#addresses') },
    { label: 'Notification Settings', icon: 'i-heroicons-bell-alert', click: () => navigateTo('/supplier/settings#notifications') },
    { label: appStore.t('layout.team'), icon: 'i-heroicons-users', click: () => navigateTo('/supplier/team') },
  ],
  [{ label: appStore.t('layout.logout'), icon: 'i-heroicons-arrow-right-on-rectangle', click: handleLogout }],
])

const currentSupplierPath = computed(() => normalizePath(route.path))
const supplierNavRenderKey = computed(() => `supplier-nav:${currentSupplierPath.value}`)
const showNotif = ref(false)
const notifLoading = ref(false)
const notifications = ref<Notification[]>([])
const notifRef = ref<HTMLElement | null>(null)
const unreadCount = computed(() => notifications.value.filter(n => !n.read_at).length)

function normalizePath(path: string) {
  return path.replace(/\/+$/, '') || '/'
}

function navItemClass(isActive: boolean) {
  return isActive
    ? 'text-white bg-indigo-500/20 ring-1 ring-indigo-400/40'
    : 'text-slate-300 hover:text-white hover:bg-slate-800/70'
}

function navIconClass(isActive: boolean) {
  return isActive ? 'text-indigo-300' : 'text-slate-400'
}

const handleLogout = async () => {
  await authStore.logout()
  navigateTo('/login')
}

function toggleNotif() {
  showNotif.value = !showNotif.value
  if (showNotif.value) loadNotifications()
}

async function loadNotifications() {
  if (!authStore.accessToken) return
  notifLoading.value = true
  try {
    const data = await $fetch<Notification[]>(`${config.public.apiBase}/notifications/my`, {
      headers: { Authorization: `Bearer ${authStore.accessToken}` },
    })
    notifications.value = data ?? []
  } catch {
    notifications.value = []
  } finally {
    notifLoading.value = false
  }
}

async function markRead(n: Notification) {
  if (n.read_at || !authStore.accessToken) return
  try {
    await $fetch(`${config.public.apiBase}/notifications/${n.id}/read`, {
      method: 'POST',
      headers: { Authorization: `Bearer ${authStore.accessToken}` },
    })
    n.read_at = new Date().toISOString()
  } catch {}
}

async function markAllRead() {
  if (!authStore.accessToken) return
  try {
    await $fetch(`${config.public.apiBase}/notifications/read-all`, {
      method: 'POST',
      headers: { Authorization: `Bearer ${authStore.accessToken}` },
    })
    notifications.value.forEach(n => { if (!n.read_at) n.read_at = new Date().toISOString() })
  } catch {}
}

async function openNotification(n: Notification) {
  await markRead(n)
  showNotif.value = false
  const target = notificationTarget(n.notification_type)
  if (target) navigateTo(target)
}

function notificationTitle(n: Notification) {
  return n.subject || notificationTypeLabel(n.notification_type)
}

function notificationTypeLabel(type: string) {
  const labels: Record<string, string> = {
    NEW_INTENT_FOR_SUPPLIER: 'New matching request',
    OFFER_AWARDED_SUPPLIER: 'Offer awarded',
    ORDER_ACCEPTED_SUPPLIER: 'Order accepted',
    DELIVERY_UPDATED_SUPPLIER: 'Delivery updated',
    DISPUTE_OPENED: 'Dispute opened',
    MESSAGE_RECEIVED: 'New message',
    ADMIN_TEST: 'Admin notification',
  }
  return labels[type] || type.replaceAll('_', ' ').toLowerCase().replace(/^\w/, c => c.toUpperCase())
}

function notificationTarget(type: string) {
  const targets: Record<string, string> = {
    NEW_INTENT_FOR_SUPPLIER: '/supplier/inbox',
    OFFER_AWARDED_SUPPLIER: '/supplier/orders',
    ORDER_ACCEPTED_SUPPLIER: '/supplier/payouts',
    DELIVERY_UPDATED_SUPPLIER: '/supplier/orders',
    DISPUTE_OPENED: '/supplier/orders',
    MESSAGE_RECEIVED: '/supplier/messages',
  }
  return targets[type] || '/supplier/notifications'
}

function notifIcon(type: string): string {
  const map: Record<string, string> = {
    NEW_INTENT_FOR_SUPPLIER: '📥',
    OFFER_AWARDED_SUPPLIER: '🏆',
    ORDER_ACCEPTED_SUPPLIER: '✅',
    DELIVERY_UPDATED_SUPPLIER: '🚚',
    DISPUTE_OPENED: '⚠️',
    MESSAGE_RECEIVED: '💬',
    ADMIN_TEST: '🔔',
  }
  return map[type] || '🔔'
}

function timeAgo(dateStr: string): string {
  const diff = Date.now() - new Date(dateStr).getTime()
  const mins = Math.floor(diff / 60000)
  if (mins < 1) return 'just now'
  if (mins < 60) return `${mins}m ago`
  const hrs = Math.floor(mins / 60)
  if (hrs < 24) return `${hrs}h ago`
  return `${Math.floor(hrs / 24)}d ago`
}

function handleOutsideClick(e: MouseEvent) {
  if (notifRef.value && !notifRef.value.contains(e.target as Node)) {
    showNotif.value = false
  }
}

onMounted(() => {
  loadNotifications()
  document.addEventListener('click', handleOutsideClick)
})

onUnmounted(() => {
  document.removeEventListener('click', handleOutsideClick)
})
</script>

<style scoped>
.notif-enter-active, .notif-leave-active { transition: all 0.15s ease; }
.notif-enter-from, .notif-leave-to { opacity: 0; transform: translateY(-6px) scale(0.98); }
</style>
