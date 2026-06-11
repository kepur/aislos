<template>
  <div class="space-y-6 h-full flex flex-col">
    <div class="flex items-center justify-between mb-2">
      <h1 class="text-2xl font-bold text-slate-900">Message Center</h1>
    </div>

    <div class="rounded-2xl border border-amber-200 bg-gradient-to-r from-amber-50 via-white to-orange-50 px-5 py-4 shadow-sm">
      <div class="flex items-start gap-3">
        <div class="mt-0.5 rounded-full bg-amber-100 p-2 text-amber-700">
          <UIcon name="i-heroicons-shield-check" class="h-5 w-5" />
        </div>
        <div>
          <p class="text-sm font-semibold text-slate-900">Keep deal and delivery discussions in-site</p>
          <p class="mt-1 text-sm text-slate-600">
            Email and Telegram can remind you to come back, but the binding record for disputes, proof, and order history stays inside this chat thread.
          </p>
        </div>
      </div>
    </div>

    <div class="flex-1 flex bg-white border border-slate-200 rounded-lg overflow-hidden min-h-[600px] h-[70vh]">
      <!-- Contacts Sidebar -->
      <div class="w-1/3 border-r border-slate-200 flex flex-col bg-slate-50">
        <div class="p-4 border-b border-slate-200 bg-white">
          <div class="relative max-w-sm">
          <span class="absolute inset-y-0 left-3 flex items-center pointer-events-none"><svg class="w-4 h-4 text-slate-400" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" /></svg></span>
          <input type="text" placeholder="Search messages..."
            class="w-full rounded-lg border border-slate-200 bg-white pl-9 pr-4 py-2 text-sm text-slate-800 shadow-sm focus:border-indigo-400 focus:outline-none focus:ring-2 focus:ring-indigo-200" />
        </div>
        </div>
        <div class="flex-1 overflow-y-auto">
          <div 
            v-for="contact in contacts" 
            :key="contact.id"
            @click="selectContact(contact)"
            class="p-4 border-b border-slate-100 cursor-pointer transition-colors"
            :class="activeContact.id === contact.id ? 'bg-indigo-50 border-l-4 border-l-indigo-600' : 'bg-white hover:bg-slate-50 border-l-4 border-l-transparent'"
          >
            <div class="flex justify-between items-start">
              <h4 class="font-medium text-slate-900">{{ contact.name }}</h4>
              <span class="text-xs text-slate-500">{{ contact.lastTime }}</span>
            </div>
            <p class="text-sm text-slate-600 truncate mt-1">{{ contact.lastMessage }}</p>
          </div>
        </div>
      </div>

      <!-- Chat Area -->
      <div class="flex-1 flex flex-col relative bg-white">
        <!-- Chat Header -->
        <div class="p-4 border-b border-slate-200 flex justify-between items-center bg-white shadow-sm z-10">
          <div class="flex items-center">
            <UAvatar :src="`https://i.pravatar.cc/150?u=${activeContact.id}`" class="mr-3" />
            <h3 class="font-medium text-slate-900">{{ activeContact.name }}</h3>
          </div>
          <UButton size="xs" color="gray" variant="ghost" :to="`/buyer/orders/${activeContact.orderId}`">
            View Order #{{ activeContact.orderId }}
          </UButton>
        </div>
        
        <!-- Chat Messages -->
        <div class="flex-1 p-4 overflow-y-auto space-y-4 bg-slate-50 flex flex-col" id="chat-container">
          <div v-for="(msg, index) in activeContact.messages" :key="index" class="flex flex-col" :class="msg.sender === 'me' ? 'items-end' : 'items-start'">
            <div 
              class="rounded-lg px-4 py-2 max-w-md shadow-sm"
              :class="msg.sender === 'me' ? 'bg-indigo-600 text-white rounded-tr-none' : 'bg-white border border-slate-200 text-slate-900 rounded-tl-none'"
            >
              <p class="whitespace-pre-wrap">{{ msg.text }}</p>
            </div>
            <span class="text-[10px] text-slate-400 mt-1">{{ msg.time }}</span>
          </div>
        </div>
        
        <!-- Chat Input -->
        <form @submit.prevent="sendMessage" class="p-4 border-t border-slate-200 bg-white">
          <div class="flex space-x-2">
            <UInput 
              v-model="newMessage" 
              class="flex-1" 
              placeholder="Type your message here..." 
              autocomplete="off"
            />
            <UButton type="submit" color="indigo" icon="i-heroicons-paper-airplane" :disabled="!newMessage.trim()">Send</UButton>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, nextTick } from 'vue'
import type { Message } from '~/types'

definePageMeta({ layout: 'buyer' })

const contacts = ref([
  {
    id: 'sup1',
    name: 'Global Build Supply Co.',
    lastTime: '10:42 AM',
    lastMessage: 'Can we deliver this on Tuesday instead?',
    orderId: 'ORD-82910',
    messages: [
      { text: 'Hi, is it possible to change the delivery date to Monday?', sender: 'me', time: '10:30 AM' },
      { text: 'Can we deliver this on Tuesday instead? Monday is a public holiday in our region.', sender: 'them', time: '10:42 AM' }
    ]
  },
  {
    id: 'sup2',
    name: 'TechWholesale Inc',
    lastTime: 'Yesterday',
    lastMessage: 'We have updated the shipping tracking number.',
    orderId: 'ORD-81105',
    messages: [
      { text: 'When will the laptops be shipped?', sender: 'me', time: 'Yesterday 2:00 PM' },
      { text: 'We have updated the shipping tracking number. Please check the order details.', sender: 'them', time: 'Yesterday 4:15 PM' }
    ]
  }
])

const activeContact = ref(contacts.value[0])
const newMessage = ref('')
const config = useRuntimeConfig()
const authStore = useAuthStore()

function selectContact(contact: typeof contacts.value[number]) {
  activeContact.value = contact
  loadMessages()
}

async function loadMessages() {
  if (!authStore.accessToken) return
  try {
    const rows = await $fetch<Message[]>(`${config.public.apiBase}/threads/order/${activeContact.value.orderId}/messages`, {
      headers: { Authorization: `Bearer ${authStore.accessToken}` },
    })
    if (!rows.length) return
    activeContact.value.messages = rows.map((msg) => ({
      text: msg.body,
      sender: msg.sender_id === authStore.user?.id ? 'me' : 'them',
      time: new Date(msg.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    }))
  } catch {
    // Keep seeded local conversation when the demo order has no backend thread.
  }
}

const sendMessage = async () => {
  if (!newMessage.value.trim()) return
  
  const now = new Date()
  const timeString = now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
  const body = newMessage.value

  if (authStore.accessToken) {
    try {
      const msg = await $fetch<Message>(`${config.public.apiBase}/threads/order/${activeContact.value.orderId}/messages`, {
        method: 'POST',
        body: { body },
        headers: { Authorization: `Bearer ${authStore.accessToken}` },
      })
      activeContact.value.messages.push({
        text: msg.body,
        sender: msg.sender_id === authStore.user?.id ? 'me' : 'them',
        time: new Date(msg.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      })
    } catch {
      activeContact.value.messages.push({
        text: body,
        sender: 'me',
        time: timeString
      })
    }
  } else {
    activeContact.value.messages.push({
      text: body,
      sender: 'me',
      time: timeString
    })
  }

  activeContact.value.lastMessage = body
  activeContact.value.lastTime = timeString
  newMessage.value = ''

  await nextTick()
  const container = document.getElementById('chat-container')
  if (container) {
    container.scrollTop = container.scrollHeight
  }

  if (authStore.accessToken) return

  // Simulate auto-reply
  setTimeout(async () => {
    activeContact.value.messages.push({
      text: 'Received your message. I will check with my team and get back to you shortly.',
      sender: 'them',
      time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    })
    await nextTick()
    if (container) container.scrollTop = container.scrollHeight
  }, 1500)
}

onMounted(loadMessages)
</script>
