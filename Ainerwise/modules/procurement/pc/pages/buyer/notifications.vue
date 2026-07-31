<template>
  <div class="space-y-6">
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-2xl font-bold text-slate-900">Notifications</h1>
        <p class="text-sm text-slate-500 mt-1">Buyer alerts for new offers, order updates, disputes, and messages.</p>
      </div>
      <div class="flex gap-2">
        <UButton color="gray" variant="outline" icon="i-heroicons-arrow-path" :loading="loading" @click="loadNotifications">
          Refresh
        </UButton>
        <UButton color="indigo" variant="soft" :disabled="unreadCount === 0" @click="markAllRead">
          Mark all read
        </UButton>
      </div>
    </div>

    <UCard>
      <div v-if="loading" class="py-12 text-center text-sm text-slate-400">Loading notifications...</div>
      <div v-else-if="notifications.length === 0" class="py-16 text-center text-slate-400">
        <div class="text-4xl mb-2">🔔</div>
        <p class="text-sm">No notifications yet.</p>
      </div>
      <div v-else class="divide-y divide-slate-100">
        <button
          v-for="n in notifications"
          :key="n.id"
          :class="['w-full text-left px-4 py-4 hover:bg-slate-50 transition-colors', !n.read_at ? 'bg-indigo-50' : '']"
          @click="openNotification(n)"
        >
          <div class="flex items-start gap-4">
            <div class="w-10 h-10 rounded-xl bg-white border border-slate-200 flex items-center justify-center text-lg flex-shrink-0">
              {{ notifIcon(n.notification_type) }}
            </div>
            <div class="min-w-0 flex-1">
              <div class="flex items-center gap-2">
                <p class="font-semibold text-slate-900">{{ notificationTitle(n) }}</p>
                <UBadge v-if="!n.read_at" color="indigo" variant="subtle" size="xs">New</UBadge>
              </div>
              <p class="text-sm text-slate-600 mt-1">{{ n.body }}</p>
              <p class="text-xs text-slate-400 mt-2">{{ timeAgo(n.created_at) }}</p>
            </div>
          </div>
        </button>
      </div>
    </UCard>
  </div>
</template>

<script setup lang="ts">
definePageMeta({ layout: 'buyer', middleware: ['auth'] })

const authStore = useAuthStore()
const config = useRuntimeConfig()

interface Notification {
  id: string
  subject: string | null
  body: string
  notification_type: string
  read_at: string | null
  created_at: string
}

const loading = ref(false)
const notifications = ref<Notification[]>([])
const unreadCount = computed(() => notifications.value.filter(n => !n.read_at).length)

async function loadNotifications() {
  loading.value = true
  try {
    notifications.value = await $fetch<Notification[]>(`${config.public.apiBase}/notifications/my`, {
      headers: { Authorization: `Bearer ${authStore.accessToken}` },
    })
  } catch {
    notifications.value = []
  } finally {
    loading.value = false
  }
}

async function markRead(n: Notification) {
  if (n.read_at) return
  try {
    await $fetch(`${config.public.apiBase}/notifications/${n.id}/read`, {
      method: 'POST',
      headers: { Authorization: `Bearer ${authStore.accessToken}` },
    })
    n.read_at = new Date().toISOString()
  } catch {}
}

async function markAllRead() {
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
  navigateTo(notificationTarget(n.notification_type))
}

function notificationTitle(n: Notification) {
  return n.subject || notificationTypeLabel(n.notification_type)
}

function notificationTypeLabel(type: string) {
  const labels: Record<string, string> = {
    NEW_OFFER_FOR_BUYER: 'New offer received',
    OFFER_UPDATED_BUYER: 'Offer updated',
    ORDER_CREATED_BUYER: 'Order created',
    DELIVERY_UPDATED_BUYER: 'Delivery updated',
    DISPUTE_OPENED: 'Dispute opened',
    MESSAGE_RECEIVED: 'New message',
    ADMIN_TEST: 'Admin notification',
  }
  return labels[type] || type.replaceAll('_', ' ').toLowerCase().replace(/^\w/, c => c.toUpperCase())
}

function notificationTarget(type: string) {
  const targets: Record<string, string> = {
    NEW_OFFER_FOR_BUYER: '/buyer/requests',
    OFFER_UPDATED_BUYER: '/buyer/requests',
    ORDER_CREATED_BUYER: '/buyer/orders',
    DELIVERY_UPDATED_BUYER: '/buyer/orders',
    DISPUTE_OPENED: '/buyer/disputes',
    MESSAGE_RECEIVED: '/buyer/messages',
  }
  return targets[type] || '/buyer/dashboard'
}

function notifIcon(type: string): string {
  const map: Record<string, string> = {
    NEW_OFFER_FOR_BUYER: '📨',
    OFFER_UPDATED_BUYER: '✏️',
    ORDER_CREATED_BUYER: '🧾',
    DELIVERY_UPDATED_BUYER: '🚚',
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

onMounted(loadNotifications)
</script>
