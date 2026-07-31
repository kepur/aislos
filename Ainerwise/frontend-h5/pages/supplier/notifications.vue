<template>
  <div class="p-4 space-y-4">
    <div class="flex items-center justify-between">
      <h1 class="text-xl font-semibold text-gray-900">通知</h1>
      <button class="text-sm text-primary-600" :disabled="!items.length" @click="readAll">
        全部已读
      </button>
    </div>
    <p v-if="error" class="text-sm text-red-600">{{ error }}</p>
    <p v-if="loading" class="text-sm text-gray-500">加载中…</p>
    <ul v-else class="space-y-2">
      <li
        v-for="n in items"
        :key="n.id"
        class="rounded-lg border p-3 bg-white"
        :class="n.status === 'unread' ? 'border-primary-200' : ''"
        @click="markOne(n)"
      >
        <p class="font-medium text-sm">{{ n.title }}</p>
        <p class="text-xs text-gray-500 mt-1">{{ n.body }}</p>
        <p class="text-xs text-gray-400 mt-1">{{ n.event_type }}</p>
      </li>
      <li v-if="!items.length" class="text-sm text-gray-500">暂无通知</li>
    </ul>
  </div>
</template>

<script setup lang="ts">
definePageMeta({ layout: 'default', middleware: ['auth'] })

const { listNotifications, markRead, markAllRead } = useCommerce()
const items = ref<any[]>([])
const loading = ref(true)
const error = ref('')

async function load() {
  loading.value = true
  error.value = ''
  try {
    const res = await listNotifications()
    items.value = res.items
  } catch (e: any) {
    error.value = e?.data?.detail || e?.message || 'Load failed'
  } finally {
    loading.value = false
  }
}

async function markOne(n: any) {
  if (n.status !== 'unread') return
  error.value = ''
  try {
    await markRead(n.id)
    n.status = 'read'
  } catch (e: any) {
    error.value = e?.data?.detail || e?.message || 'Failed to mark notification as read'
  }
}

async function readAll() {
  try {
    await markAllRead()
    await load()
  } catch (e: any) {
    error.value = e?.data?.detail || e?.message || 'Failed'
  }
}

onMounted(load)
</script>
