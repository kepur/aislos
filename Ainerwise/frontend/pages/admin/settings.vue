<template>
  <div>
    <h1 class="text-2xl font-bold text-gray-900 mb-6">{{ $t('admin.settings') }}</h1>
    <div class="bg-white rounded-xl border p-6">
      <p class="text-gray-500">Platform settings configuration coming in Phase 3+.</p>
      <ul class="mt-4 space-y-2 text-sm text-gray-600">
        <li>Platform fee rules</li>
        <li>Telegram bot configuration</li>
        <li>Language management</li>
        <li>Region configuration</li>
      </ul>
    </div>
  </div>
</template>

<script setup lang="ts">
definePageMeta({ layout: 'admin', middleware: 'admin' })
</script>
