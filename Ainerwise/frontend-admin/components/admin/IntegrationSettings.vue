<template>
  <div class="admin-card xl:col-span-2">
    <h2 class="admin-section-title">Integrations</h2>
    <p class="mt-1 text-sm text-gray-500">Configure notifications, text AI, and the low-latency realtime voice provider. Text AI and voice are separate integrations so each can use the best provider.</p>

    <div class="mt-5 grid grid-cols-1 lg:grid-cols-2 gap-5">
      <div v-for="cat in cats" :key="cat.key" class="rounded-xl border p-4">
        <div class="flex items-center justify-between gap-2">
          <h3 class="font-bold text-gray-800">{{ cat.title }}</h3>
          <label class="inline-flex items-center gap-2 text-xs text-gray-600">
            <input type="checkbox" v-model="state[cat.key].is_enabled" class="rounded" /> Enabled
          </label>
        </div>
        <p class="mt-1 text-[11px] text-gray-400">{{ cat.desc }}</p>

        <div class="mt-3 space-y-2.5">
          <div v-for="f in cat.fields" :key="f.key">
            <label class="block text-[11px] font-medium text-gray-600 mb-0.5">
              {{ f.label }}
              <span v-if="f.secret && state[cat.key].config[f.key + '_set']" class="text-emerald-600">(set — leave blank to keep)</span>
            </label>
            <textarea v-if="f.type === 'textarea'" v-model="state[cat.key].form[f.key]" rows="2" class="input-field text-sm" :placeholder="f.placeholder || ''"></textarea>
            <label v-else-if="f.type === 'checkbox'" class="inline-flex items-center gap-2 text-sm text-gray-600">
              <input type="checkbox" v-model="state[cat.key].form[f.key]" class="rounded" /> {{ f.placeholder || 'Yes' }}
            </label>
            <input v-else :type="f.secret ? 'password' : f.type === 'number' ? 'number' : 'text'"
              v-model="state[cat.key].form[f.key]" class="input-field text-sm"
              :placeholder="f.secret && state[cat.key].config[f.key + '_set'] ? '••••••••' : (f.placeholder || '')" />
          </div>
        </div>

        <div class="mt-4 flex items-center gap-2">
          <button @click="save(cat.key)" :disabled="busy[cat.key]" class="px-3 py-1.5 bg-primary-600 text-white text-xs font-medium rounded-lg hover:bg-primary-700 disabled:opacity-50">
            {{ busy[cat.key] === 'save' ? 'Saving...' : 'Save' }}
          </button>
          <button @click="test(cat.key)" :disabled="busy[cat.key]" class="px-3 py-1.5 border text-xs font-medium rounded-lg text-gray-700 hover:bg-gray-50 disabled:opacity-50">
            {{ busy[cat.key] === 'test' ? 'Testing...' : 'Test' }}
          </button>
        </div>
        <p v-if="result[cat.key]" class="mt-2 text-[11px]" :class="result[cat.key].ok ? 'text-emerald-600' : 'text-red-600'">{{ result[cat.key].msg }}</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
const { apiFetch } = useApi()

const cats = [
  { key: 'smtp', title: 'Email (SMTP)', desc: 'Outgoing email for notifications and reports.', fields: [
    { key: 'host', label: 'SMTP Host', placeholder: 'smtp.example.com' },
    { key: 'port', label: 'Port', type: 'number', placeholder: '587' },
    { key: 'username', label: 'Username', placeholder: 'user@example.com' },
    { key: 'password', label: 'Password', secret: true },
    { key: 'from_email', label: 'From Email', placeholder: 'noreply@example.com' },
    { key: 'from_name', label: 'From Name', placeholder: 'AinerWise' },
    { key: 'use_tls', label: 'Use STARTTLS', type: 'checkbox' },
    { key: 'use_ssl', label: 'Use SSL', type: 'checkbox' },
  ]},
  { key: 'telegram', title: 'Telegram Bot', desc: 'Admin alerts + /leads bot commands.', fields: [
    { key: 'bot_token', label: 'Bot Token', secret: true },
    { key: 'admin_chat_id', label: 'Admin Chat ID', placeholder: '-100123...' },
    { key: 'webhook_url', label: 'Webhook URL (optional)', placeholder: 'https://.../api/v1/telegram/webhook' },
  ]},
  { key: 'ai', title: 'AI Agent (OpenAI-compatible)', desc: 'Powers the conversational facility assessment.', fields: [
    { key: 'base_url', label: 'API Base URL', placeholder: 'https://api.openai.com/v1' },
    { key: 'api_key', label: 'API Key', secret: true },
    { key: 'model', label: 'Model', placeholder: 'gpt-4o-mini' },
    { key: 'temperature', label: 'Temperature', type: 'number', placeholder: '0.3' },
    { key: 'system_prompt', label: 'Extra System Prompt (optional)', type: 'textarea' },
  ]},
  { key: 'voice', title: 'Realtime Voice', desc: 'Low-latency speech-to-speech for Experience Center kiosks. Separate from the text AI provider.', fields: [
    { key: 'provider', label: 'Provider', placeholder: 'openai-realtime' },
    { key: 'base_url', label: 'API Base URL', placeholder: 'https://api.openai.com/v1' },
    { key: 'webrtc_url', label: 'WebRTC SDP URL', placeholder: 'https://api.openai.com/v1/realtime/calls' },
    { key: 'api_key', label: 'API Key', secret: true },
    { key: 'model', label: 'Realtime Model', placeholder: 'gpt-realtime' },
    { key: 'voice', label: 'Voice', placeholder: 'alloy' },
    { key: 'transcription_model', label: 'Transcription Model', placeholder: 'gpt-4o-mini-transcribe' },
  ]},
]

const state = reactive<Record<string, any>>({})
const busy = reactive<Record<string, string | false>>({})
const result = reactive<Record<string, any>>({})
cats.forEach((c) => { state[c.key] = { is_enabled: false, config: {}, form: {} }; busy[c.key] = false })

async function load() {
  try {
    const res = await apiFetch<any>('/admin/integrations')
    for (const item of res.items || []) {
      const s = state[item.category]
      if (!s) continue
      s.is_enabled = item.is_enabled
      s.config = item.config || {}
      // prefill non-secret fields
      s.form = {}
      for (const [k, v] of Object.entries(item.config || {})) {
        if (!k.endsWith('_set')) s.form[k] = v
      }
    }
  } catch {}
}

function buildConfig(key: string) {
  const cat = cats.find((c) => c.key === key)!
  const cfg: Record<string, any> = {}
  for (const f of cat.fields) {
    const v = state[key].form[f.key]
    if (f.secret) { if (v) cfg[f.key] = v }  // only send secret if typed
    else if (f.type === 'number') { if (v !== '' && v != null) cfg[f.key] = Number(v) }
    else if (f.type === 'checkbox') cfg[f.key] = !!v
    else if (v !== undefined) cfg[f.key] = v
  }
  return cfg
}

async function save(key: string) {
  busy[key] = 'save'; result[key] = null
  try {
    const res = await apiFetch<any>(`/admin/integrations/${key}`, { method: 'PUT', body: { is_enabled: state[key].is_enabled, config: buildConfig(key) } })
    state[key].config = res.config || {}
    // clear typed secrets after save
    const cat = cats.find((c) => c.key === key)!
    cat.fields.filter((f) => f.secret).forEach((f) => { state[key].form[f.key] = '' })
    result[key] = { ok: true, msg: 'Saved.' }
  } catch (e: any) {
    result[key] = { ok: false, msg: e?.data?.detail || 'Save failed' }
  } finally { busy[key] = false }
}

async function test(key: string) {
  busy[key] = 'test'; result[key] = null
  try {
    let body: any = undefined
    if (key === 'smtp') {
      const to = prompt('Send test email to:')
      if (!to) { busy[key] = false; return }
      body = { to }
    }
    const res = await apiFetch<any>(`/admin/integrations/${key}/test`, { method: 'POST', body })
    const ok = res.ok || res.sent
    result[key] = { ok, msg: ok ? 'Test succeeded ✓' : `Test failed: ${res.reason || res.error || 'unknown'}` }
  } catch (e: any) {
    result[key] = { ok: false, msg: e?.data?.detail || 'Test failed' }
  } finally { busy[key] = false }
}

onMounted(load)
</script>
