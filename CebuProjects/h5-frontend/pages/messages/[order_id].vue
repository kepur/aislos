<template>
  <div class="min-h-screen bg-slate-100 flex flex-col">
    <div class="bg-white border-b border-slate-100 px-4 h-14 flex items-center gap-3 sticky top-0 z-40 pt-safe">
      <button type="button" class="text-slate-600 p-1 -ml-1" @click="$router.back()">
        <svg class="w-6 h-6" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" d="M15 19l-7-7 7-7" />
        </svg>
      </button>
      <div class="flex-1">
        <p class="font-semibold text-slate-900 text-sm">Order Chat</p>
        <p class="text-xs text-slate-500">#{{ orderId.slice(0, 8).toUpperCase() }}</p>
      </div>
    </div>

    <!-- Messages -->
    <div ref="chatContainer" class="flex-1 overflow-y-auto p-4 space-y-3 pb-24">
      <div v-if="loading" class="text-center py-8 text-slate-400 text-sm">Loading messages…</div>
      <div v-else-if="messages.length === 0" class="empty-state py-10">
        <p class="text-slate-500 text-sm">No messages yet. Say hello!</p>
      </div>
      <div
        v-for="msg in messages"
        :key="msg.id"
        class="flex"
        :class="msg.sender_id === authStore.user?.id ? 'justify-end' : 'justify-start'"
      >
        <div
          class="max-w-[78%] px-4 py-2.5 rounded-2xl text-sm leading-relaxed"
          :class="msg.sender_id === authStore.user?.id
            ? 'bg-primary-600 text-white rounded-br-sm'
            : 'bg-white text-slate-800 shadow-card rounded-bl-sm'"
        >
          <p>{{ msg.body }}</p>
          <p class="text-[10px] mt-1 opacity-60">{{ formatRelativeTime(msg.created_at) }}</p>
        </div>
      </div>
    </div>

    <!-- Input -->
    <div class="fixed bottom-0 left-0 right-0 bg-white border-t border-slate-100 px-4 py-3 flex gap-3" style="padding-bottom: calc(12px + var(--safe-area-bottom))">
      <input
        v-model="messageText"
        type="text"
        placeholder="Type a message…"
        class="flex-1 bg-slate-100 rounded-xl px-4 py-2.5 text-sm outline-none"
        @keyup.enter="sendMessage"
      />
      <button type="button"
        class="w-10 h-10 bg-primary-600 text-white rounded-xl flex items-center justify-center flex-shrink-0 active:bg-primary-700 disabled:opacity-50"
        :disabled="!messageText.trim() || sending"
        @click="sendMessage"
      >
        <svg class="w-5 h-5" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
        </svg>
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { Message } from "~/types";

definePageMeta({ layout: "default", middleware: ["auth"] });
useHead({ title: "Order Chat" });

const route = useRoute();
const authStore = useAuthStore();
const config = useRuntimeConfig();
const { formatRelativeTime } = useApiUtils();

const orderId = route.params.order_id as string;
const messages = ref<Message[]>([]);
const messageText = ref("");
const loading = ref(true);
const sending = ref(false);
const chatContainer = ref<HTMLDivElement>();

async function loadMessages() {
  try {
    messages.value = await $fetch<Message[]>(`${config.public.apiBase}/threads/order/${orderId}/messages`, {
      headers: { Authorization: `Bearer ${authStore.accessToken}` },
    });
    nextTick(() => {
      if (chatContainer.value) chatContainer.value.scrollTop = chatContainer.value.scrollHeight;
    });
  } finally {
    loading.value = false;
  }
}

async function sendMessage() {
  const body = messageText.value.trim();
  if (!body || sending.value) return;
  sending.value = true;
  try {
    const msg = await $fetch<Message>(`${config.public.apiBase}/threads/order/${orderId}/messages`, {
      method: "POST",
      body: { body },
      headers: { Authorization: `Bearer ${authStore.accessToken}` },
    });
    messages.value.push(msg);
    messageText.value = "";
    nextTick(() => {
      if (chatContainer.value) chatContainer.value.scrollTop = chatContainer.value.scrollHeight;
    });
  } finally {
    sending.value = false;
  }
}

onMounted(loadMessages);
</script>
