<template>
  <div class="min-h-screen flex bg-slate-50 text-slate-900">
    <!-- Sidebar Navigation -->
    <aside class="w-64 bg-white border-r border-slate-200 hidden md:flex flex-col sticky top-0 h-screen">
      <div class="h-16 flex items-center px-6 border-b border-slate-200">
        <NuxtLink to="/" class="text-xl font-bold text-indigo-600 tracking-tight">
          {{ $config.public.appName }}
        </NuxtLink>
      </div>
      
      <div :key="buyerNavRenderKey" class="flex-grow py-6 px-4 overflow-y-auto">
        <div class="mb-8">
          <UButton block color="indigo" variant="solid" size="lg" to="/post-request" class="shadow-md">
            <template #leading>
              <UIcon name="i-heroicons-plus-circle" class="w-5 h-5" />
            </template>
            {{ appStore.t('action.postRequest') }}
          </UButton>
        </div>

        <nav class="space-y-1">
          <NuxtLink
            v-for="item in mainNav"
            :key="`${buyerNavRenderKey}:${item.to}`"
            :to="item.to"
            custom
            v-slot="{ href, navigate }"
          >
            <a
              :href="href"
              :aria-current="isActive(item.to) ? 'page' : undefined"
              class="flex items-center px-3 py-2 text-sm font-medium rounded-md transition-colors"
              :class="navItemClass(isActive(item.to))"
              @click="handleNavClick($event, navigate, item.to)"
            >
              <UIcon :name="item.icon" class="mr-3 w-5 h-5" :class="navIconClass(isActive(item.to))" />
              {{ item.label }}
              <UBadge v-if="item.badge" color="red" size="sm" class="ml-auto">{{ item.badge }}</UBadge>
            </a>
          </NuxtLink>
        </nav>

        <div class="mt-8">
          <h3 class="px-3 text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2">{{ appStore.t('layout.settings') }}</h3>
          <nav class="space-y-1">
            <NuxtLink
              v-for="item in settingsNav"
              :key="`${buyerNavRenderKey}:${item.to}`"
              :to="item.to"
              custom
              v-slot="{ href, navigate }"
            >
              <a
                :href="href"
                :aria-current="isActive(item.to) ? 'page' : undefined"
                class="flex items-center px-3 py-2 text-sm font-medium rounded-md transition-colors"
                :class="navItemClass(isActive(item.to))"
                @click="handleNavClick($event, navigate, item.to)"
              >
                <UIcon :name="item.icon" class="mr-3 w-5 h-5" :class="navIconClass(isActive(item.to))" />
                {{ item.label }}
              </a>
            </NuxtLink>
          </nav>
        </div>

        <!-- Business section: only BUSINESS account_type -->
        <div v-if="accountCtx?.account_type === 'BUSINESS'" class="mt-8">
          <h3 class="px-3 text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2">{{ appStore.t('layout.business') }}</h3>
          <nav class="space-y-1">
            <NuxtLink
              to="/buyer/company-profile"
              :key="`${buyerNavRenderKey}:company-profile`"
              custom
              v-slot="{ href, navigate }"
            >
              <a
                :href="href"
                :aria-current="isActive('/buyer/company-profile') ? 'page' : undefined"
                class="flex items-center px-3 py-2 text-sm font-medium rounded-md transition-colors"
                :class="navItemClass(isActive('/buyer/company-profile'))"
                @click="handleNavClick($event, navigate, '/buyer/company-profile')"
              >
                <UIcon name="i-heroicons-building-office" class="mr-3 w-5 h-5" :class="navIconClass(isActive('/buyer/company-profile'))" />
                {{ appStore.t('layout.companyProfile') }}
              </a>
            </NuxtLink>
            <NuxtLink
              to="/buyer/team"
              :key="`${buyerNavRenderKey}:team`"
              custom
              v-slot="{ href, navigate }"
            >
              <a
                :href="href"
                :aria-current="isActive('/buyer/team') ? 'page' : undefined"
                class="flex items-center px-3 py-2 text-sm font-medium rounded-md transition-colors"
                :class="navItemClass(isActive('/buyer/team'))"
                @click="handleNavClick($event, navigate, '/buyer/team')"
              >
                <UIcon name="i-heroicons-users" class="mr-3 w-5 h-5" :class="navIconClass(isActive('/buyer/team'))" />
                {{ appStore.t('layout.team') }}
              </a>
            </NuxtLink>
          </nav>
        </div>
      </div>
      
      <div class="p-4 border-t border-slate-200">
        <ClientOnly>
          <UDropdown :items="userMenuItems" :popper="{ placement: 'top-start' }">
            <button class="flex w-full items-center rounded-2xl border border-transparent px-2 py-2 text-left transition hover:border-slate-200 hover:bg-slate-50">
              <UAvatar src="https://i.pravatar.cc/150?u=buyer" alt="Buyer Avatar" />
              <div class="ml-3 min-w-0 flex-1">
                <p class="truncate text-sm font-medium text-slate-700">{{ authStore.displayName }}</p>
                <p class="text-xs font-medium text-slate-500">{{ appStore.t('layout.buyerAccount') }}</p>
              </div>
              <UIcon name="i-heroicons-chevron-up-down" class="h-4 w-4 flex-shrink-0 text-slate-400" />
            </button>
          </UDropdown>
          <template #fallback>
            <div class="flex items-center">
              <div class="h-8 w-8 rounded-full bg-slate-100" />
              <div class="ml-3 h-4 w-24 rounded bg-slate-100" />
            </div>
          </template>
        </ClientOnly>
      </div>
    </aside>

    <!-- Main Content Area -->
    <div class="flex-1 flex flex-col overflow-hidden">
      <!-- Top Header -->
      <header class="h-16 bg-white border-b border-slate-200 flex items-center justify-between px-6 z-10">
        <div class="flex items-center gap-3 flex-1 min-w-0">
          <UInput icon="i-heroicons-magnifying-glass" :placeholder="appStore.t('layout.searchBuyer')" class="w-full max-w-md hidden sm:block" />
        </div>
        
        <div class="flex items-center space-x-4">
          <ClientOnly>
            <div class="hidden md:flex items-center space-x-2 border-r border-slate-200 pr-4 mr-2">
              <USelect v-model="appStore.language" :options="appStore.languageOptions" option-attribute="label" value-attribute="code" size="sm" class="w-36" @update:model-value="appStore.setLanguage" />
              <USelect v-model="appStore.currency" :options="appStore.currencyOptions" option-attribute="label" value-attribute="code" size="sm" class="w-36" @update:model-value="appStore.setCurrency" />
            </div>
          </ClientOnly>

          <!-- Notification Bell -->
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

            <!-- Notification Dropdown -->
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
                    @click="markAllRead"
                  >
                    Mark all read
                  </button>
                </div>

                <div class="max-h-72 overflow-y-auto divide-y divide-slate-50">
                  <div v-if="notifLoading" class="py-8 text-center text-xs text-slate-400">
                    Loading...
                  </div>
                  <div
                    v-else-if="notifications.length === 0"
                    class="py-10 text-center text-slate-400"
                  >
                    <div class="text-3xl mb-2">🔔</div>
                    <p class="text-xs">No notifications yet</p>
                  </div>
                  <button
                    v-for="n in notifications"
                    :key="n.id"
                    @click="markRead(n)"
                    :class="['w-full text-left px-4 py-3 hover:bg-slate-50 transition-colors', !n.read_at ? 'bg-indigo-50' : '']"
                  >
                    <div class="flex items-start gap-3">
                      <span class="text-lg flex-shrink-0">{{ notifIcon(n.notification_type) }}</span>
                      <div class="flex-1 min-w-0">
                        <p class="text-xs font-semibold text-slate-900 leading-snug">{{ n.title }}</p>
                        <p class="text-xs text-slate-500 mt-0.5 line-clamp-2">{{ n.body }}</p>
                        <p class="text-[10px] text-slate-400 mt-1">{{ timeAgo(n.created_at) }}</p>
                      </div>
                      <div v-if="!n.read_at" class="w-2 h-2 rounded-full bg-indigo-500 flex-shrink-0 mt-1" />
                    </div>
                  </button>
                </div>

                <div class="border-t border-slate-100 px-4 py-2">
                  <NuxtLink to="/buyer/notifications" class="text-xs text-indigo-600 hover:underline" @click="showNotif = false">
                    View all notifications →
                  </NuxtLink>
                </div>
              </div>
            </Transition>
          </div>
          
          <!-- User Dropdown -->
          <ClientOnly>
            <UDropdown :items="userMenuItems" :popper="{ placement: 'bottom-end' }">
              <UButton color="white" variant="ghost" trailing-icon="i-heroicons-chevron-down-20-solid" class="hidden sm:flex">
                {{ authStore.displayName }}
              </UButton>
            </UDropdown>
          </ClientOnly>
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
const router = useRouter()

// ─── Account context ───────────────────────────────
interface AccountCtx { account_type: string; kyb_status?: string }
const accountCtx = ref<AccountCtx | null>(null)

async function loadAccountCtx() {
  if (!authStore.accessToken) return
  try {
    accountCtx.value = await $fetch<AccountCtx>(`${config.public.apiBase}/auth/me/account-context`, {
      headers: { Authorization: `Bearer ${authStore.accessToken}` }
    })
  } catch {}
}

// ─── Navigation ────────────────────────────────────
const mainNav = computed(() => [
  { to: '/buyer/dashboard', icon: 'i-heroicons-home', label: appStore.t('buyer.nav.dashboard') },
  { to: '/buyer/requests', icon: 'i-heroicons-clipboard-document-list', label: appStore.t('buyer.nav.requests') },
  { to: '/buyer/projects', icon: 'i-heroicons-cpu-chip', label: 'AI Projects' },
  { to: '/buyer/orders', icon: 'i-heroicons-shopping-cart', label: appStore.t('buyer.nav.orders') },
  { to: '/buyer/messages', icon: 'i-heroicons-chat-bubble-left-right', label: appStore.t('buyer.nav.messages'), badge: unreadCount.value > 0 ? String(unreadCount.value) : undefined },
  { to: '/buyer/disputes', icon: 'i-heroicons-exclamation-triangle', label: appStore.t('buyer.nav.disputes') },
  { to: '/buyer/ideal-list', icon: 'i-heroicons-heart', label: appStore.t('buyer.nav.idealList') },
])

const settingsNav = computed(() => [
  { to: '/buyer/settings', icon: 'i-heroicons-cog-8-tooth', label: appStore.t('buyer.nav.settings') },
  { to: '/buyer/wallet', icon: 'i-heroicons-wallet', label: appStore.t('buyer.nav.wallet') },
])

// ─── User dropdown items ────────────────────────────
const userMenuItems = computed(() => {
  const items: any[] = []

  const profileGroup: any[] = [
    { label: 'My Profile', icon: 'i-heroicons-user-circle', click: () => navigateTo('/buyer/settings') },
    { label: 'Delivery Addresses', icon: 'i-heroicons-map-pin', click: () => navigateTo('/buyer/settings#addresses') },
    { label: 'Notification Settings', icon: 'i-heroicons-bell-alert', click: () => navigateTo('/buyer/settings#notifications') },
  ]
  if (accountCtx.value?.account_type === 'BUSINESS') {
    profileGroup.push(
      { label: appStore.t('layout.companyProfile'), icon: 'i-heroicons-building-office', click: () => navigateTo('/buyer/company-profile') },
      { label: appStore.t('layout.team'), icon: 'i-heroicons-users', click: () => navigateTo('/buyer/team') },
    )
  }
  items.push(profileGroup)
  items.push([{ label: appStore.t('layout.logout'), icon: 'i-heroicons-arrow-right-on-rectangle', click: handleLogout }])
  return items
})

const currentBuyerPath = ref(normalizePath(route.path))
const buyerNavRenderKey = computed(() => `buyer-nav:${currentBuyerPath.value}`)

watch(
  () => route.fullPath,
  () => {
    currentBuyerPath.value = normalizePath(route.path)
  },
  { immediate: true }
)

let removeAfterEach: (() => void) | undefined

function normalizePath(path: string) {
  return path.replace(/\/+$/, '') || '/'
}

function isActive(path: string) {
  const current = currentBuyerPath.value
  const target = normalizePath(path)
  return current === target || current.startsWith(target + '/')
}

function navItemClass(active: boolean) {
  return active
    ? 'text-indigo-700 bg-indigo-50'
    : 'text-slate-700 hover:text-slate-900 hover:bg-slate-100'
}

function navIconClass(active: boolean) {
  return active ? 'text-indigo-600' : 'text-slate-500'
}

function handleNavClick(event: MouseEvent, navigate: (event?: MouseEvent) => Promise<void> | void, to: string) {
  if (
    event.button === 0 &&
    !event.defaultPrevented &&
    !event.metaKey &&
    !event.altKey &&
    !event.ctrlKey &&
    !event.shiftKey
  ) {
    currentBuyerPath.value = normalizePath(to)
  }
  navigate(event)
}

const handleLogout = async () => {
  await authStore.logout()
  navigateTo('/login')
}

// ─── Notifications ──────────────────────────────────
interface Notification {
  id: string
  title: string
  body: string
  notification_type: string
  read_at: string | null
  created_at: string
}

const showNotif = ref(false)
const notifLoading = ref(false)
const notifications = ref<Notification[]>([])
const notifRef = ref<HTMLElement | null>(null)

const unreadCount = computed(() => notifications.value.filter(n => !n.read_at).length)

function toggleNotif() {
  showNotif.value = !showNotif.value
  if (showNotif.value) loadNotifications()
}

async function loadNotifications() {
  notifLoading.value = true
  try {
    const data = await $fetch<Notification[]>(`${config.public.apiBase}/notifications/my`, {
      params: { page_size: 20 },
      headers: { Authorization: `Bearer ${authStore.accessToken}` }
    })
    notifications.value = data ?? []
  } catch {}
  finally { notifLoading.value = false }
}

async function markRead(n: Notification) {
  if (n.read_at) return
  try {
    await $fetch(`${config.public.apiBase}/notifications/${n.id}/read`, {
      method: 'POST',
      headers: { Authorization: `Bearer ${authStore.accessToken}` }
    })
    n.read_at = new Date().toISOString()
  } catch {}
}

async function markAllRead() {
  try {
    await $fetch(`${config.public.apiBase}/notifications/read-all`, {
      method: 'POST',
      headers: { Authorization: `Bearer ${authStore.accessToken}` }
    })
    notifications.value.forEach(n => { if (!n.read_at) n.read_at = new Date().toISOString() })
  } catch {}
}

function notifIcon(type: string): string {
  const map: Record<string, string> = {
    PING_RECEIVED: '🔔',
    OFFER_RECEIVED: '💰',
    ORDER_FUNDED: '🔒',
    ORDER_SHIPPED: '🚚',
    ORDER_DELIVERED: '📦',
    ESCROW_RELEASED: '✅',
    DISPUTE_OPENED: '⚠️',
    MESSAGE_RECEIVED: '💬',
    KYB_APPROVED: '🏆',
    KYB_REJECTED: '❌',
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

// Close dropdown on outside click
function handleOutsideClick(e: MouseEvent) {
  if (notifRef.value && !notifRef.value.contains(e.target as Node)) {
    showNotif.value = false
  }
}

// ─── Init ───────────────────────────────────────────
onMounted(() => {
  currentBuyerPath.value = normalizePath(window.location.pathname)
  removeAfterEach = router.afterEach((to) => {
    currentBuyerPath.value = normalizePath(to.path)
  })
  loadAccountCtx()
  loadNotifications()
  document.addEventListener('click', handleOutsideClick)
})

onUnmounted(() => {
  removeAfterEach?.()
  document.removeEventListener('click', handleOutsideClick)
})
</script>

<style scoped>
.notif-enter-active, .notif-leave-active { transition: all 0.15s ease; }
.notif-enter-from, .notif-leave-to { opacity: 0; transform: translateY(-6px) scale(0.98); }
</style>
