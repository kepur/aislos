<template>
  <div class="px-4 py-4 space-y-4">
    <h1 class="text-lg font-bold text-slate-800">{{ $t('contact.title') }}</h1>

    <!-- Contact info -->
    <div class="space-y-2">
      <div class="bg-white rounded-xl p-4 flex items-center gap-3 border border-slate-100 shadow-sm">
        <div class="w-10 h-10 bg-blue-50 rounded-lg flex items-center justify-center flex-shrink-0">
          <span class="text-lg">📍</span>
        </div>
        <div>
          <p class="text-xs font-semibold text-slate-400 uppercase">Location</p>
          <p class="text-sm text-slate-700">Belgrade, Serbia</p>
        </div>
      </div>
      <div class="bg-white rounded-xl p-4 flex items-center gap-3 border border-slate-100 shadow-sm">
        <div class="w-10 h-10 bg-blue-50 rounded-lg flex items-center justify-center flex-shrink-0">
          <span class="text-lg">📧</span>
        </div>
        <div>
          <p class="text-xs font-semibold text-slate-400 uppercase">Email</p>
          <p class="text-sm text-slate-700">info@ainerwise.com</p>
        </div>
      </div>
    </div>

    <!-- Contact form -->
    <form @submit.prevent="handleSubmit" class="bg-white rounded-2xl p-5 border border-slate-100 shadow-sm space-y-4">
      <h2 class="text-sm font-bold text-slate-800">Send a Message</h2>
      <div>
        <label class="block text-[10px] font-semibold text-slate-400 mb-1 uppercase tracking-wider">Name</label>
        <input v-model="form.name" type="text" required
          class="w-full text-sm border border-slate-200 rounded-xl px-3 py-2.5 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-300" />
      </div>
      <div>
        <label class="block text-[10px] font-semibold text-slate-400 mb-1 uppercase tracking-wider">Email</label>
        <input v-model="form.email" type="email" required
          class="w-full text-sm border border-slate-200 rounded-xl px-3 py-2.5 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-300" />
      </div>
      <div>
        <label class="block text-[10px] font-semibold text-slate-400 mb-1 uppercase tracking-wider">Message</label>
        <textarea v-model="form.message" rows="4" required
          class="w-full text-sm border border-slate-200 rounded-xl px-3 py-2.5 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-300 resize-none"></textarea>
      </div>
      <button type="submit" :disabled="sending"
        class="w-full text-sm font-semibold bg-blue-500 text-white py-2.5 rounded-xl shadow-sm disabled:opacity-50">
        {{ sending ? 'Sending...' : 'Send Message' }}
      </button>
      <p v-if="sent" class="text-sm text-emerald-500 font-medium text-center">Message sent successfully!</p>
    </form>
  </div>
</template>

<script setup lang="ts">
const { apiFetch } = useApi()
const form = reactive({ name: '', email: '', message: '' })
const sending = ref(false)
const sent = ref(false)

async function handleSubmit() {
  sending.value = true
  try {
    await apiFetch('/contact', { method: 'POST', body: form })
    sent.value = true
    Object.assign(form, { name: '', email: '', message: '' })
  } catch {}
  finally { sending.value = false }
}
</script>
