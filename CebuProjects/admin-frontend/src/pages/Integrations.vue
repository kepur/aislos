<template>
  <div class="space-y-6">
    <p class="text-sm text-slate-500">{{ $t('integrations.desc') }}</p>

    <!-- Maps / Geolocation -->
    <section class="card p-5 space-y-4 border-l-4 border-green-400">
      <div class="flex items-center justify-between">
        <h3 class="font-bold text-slate-900 flex items-center gap-2"><span>🗺️</span> Maps & Geolocation</h3>
        <label class="flex items-center gap-2 cursor-pointer">
          <input type="checkbox" v-model="maps.maps_enabled" class="rounded" />
          <span class="text-sm text-slate-700">Enabled</span>
        </label>
      </div>
      <p class="text-xs text-slate-500">Configure map provider for address autocomplete and geocoding. Use LOCAL (built-in Cebu city data) or Google Maps API.</p>
      <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label class="text-xs font-medium text-slate-600">Provider</label>
          <select v-model="maps.provider" class="input">
            <option value="LOCAL">Local (Built-in)</option>
            <option value="GOOGLE">Google Maps</option>
          </select>
        </div>
        <div>
          <label class="text-xs font-medium text-slate-600">Region</label>
          <input v-model="maps.google_maps_region" class="input" placeholder="PH" maxlength="2" />
        </div>
        <div>
          <label class="text-xs font-medium text-slate-600">Google Maps API Key</label>
          <input v-model="maps.google_maps_api_key" type="password" class="input" :placeholder="mapsKeyPlaceholder" :disabled="maps.provider !== 'GOOGLE'" />
          <p v-if="maps.google_maps_api_key_masked && !maps.google_maps_api_key" class="text-xs text-slate-400 mt-1">Current: {{ maps.google_maps_api_key_masked }}</p>
        </div>
        <div>
          <label class="text-xs font-medium text-slate-600">Language</label>
          <input v-model="maps.google_maps_language" class="input" placeholder="en" maxlength="5" :disabled="maps.provider !== 'GOOGLE'" />
        </div>
        <div>
          <label class="text-xs font-medium text-slate-600">Cache TTL (seconds)</label>
          <input v-model="maps.maps_cache_ttl_seconds" type="number" min="0" class="input" />
        </div>
        <div class="flex items-end gap-2">
          <button class="btn btn-secondary text-sm" :disabled="testingMaps || maps.provider !== 'GOOGLE'" @click="testMaps">
            {{ testingMaps ? 'Testing…' : 'Test Connection' }}
          </button>
        </div>
      </div>
      <div v-if="mapsTestResult" class="text-xs px-3 py-2 rounded-lg" :class="mapsTestResult.ok ? 'bg-green-50 text-green-700' : 'bg-red-50 text-red-700'">
        {{ mapsTestResult.ok ? '✅ Google Maps API connected' : '❌ Connection failed' }}
        <span v-if="mapsTestResult.error">: {{ mapsTestResult.error }}</span>
        <span v-if="mapsTestResult.google_status"> · status: {{ mapsTestResult.google_status }}</span>
      </div>
    </section>

    <!-- AI Provider -->
    <section class="card p-5 space-y-4 border-l-4 border-purple-400">
      <div class="flex items-center justify-between">
        <h3 class="font-bold text-slate-900 flex items-center gap-2"><span>🤖</span> {{ $t('ai.title') }}</h3>
        <label class="flex items-center gap-2 cursor-pointer">
          <input type="checkbox" v-model="cfg.ai_enabled" class="rounded" />
          <span class="text-sm text-slate-700">{{ $t('ai.enable') }}</span>
        </label>
      </div>
      <p class="text-xs text-slate-500">{{ $t('ai.desc') }}</p>
      <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label class="text-xs font-medium text-slate-600">{{ $t('ai.provider') }}</label>
          <select v-model="cfg.ai_provider" class="input">
            <option value="openai">OpenAI</option>
            <option value="openai_compatible">OpenAI-compatible</option>
            <option value="deepseek">DeepSeek (OpenAI-compatible)</option>
            <option value="anthropic">Anthropic Claude</option>
            <option value="azure">Azure OpenAI</option>
          </select>
        </div>
        <div>
          <label class="text-xs font-medium text-slate-600">{{ $t('ai.model') }}</label>
          <input v-model="cfg.ai_model" class="input" :placeholder="modelPlaceholder" />
        </div>
        <div>
          <label class="text-xs font-medium text-slate-600">API Token</label>
          <input v-model="cfg.ai_api_key" type="password" class="input" placeholder="sk-..., deepseek token, or provider token" />
        </div>
        <div>
          <label class="text-xs font-medium text-slate-600">{{ $t('ai.baseUrl') }}</label>
          <input v-model="cfg.ai_base_url" class="input" placeholder="https://api.openai.com/v1 or https://api.deepseek.com" />
        </div>
        <div>
          <label class="text-xs font-medium text-slate-600">{{ $t('ai.confidence') }}</label>
          <input v-model="cfg.ai_confidence_threshold" type="number" min="0" max="1" step="0.05" class="input" />
        </div>
        <div class="flex items-end">
          <div class="flex gap-2">
            <button class="btn btn-secondary text-sm" :disabled="testingAi" @click="testAI">
            {{ testingAi ? $t('ai.analyzing') : $t('ai.test') }}
            </button>
            <button class="btn btn-primary text-sm" :disabled="saving" @click="saveAIProvider">
              Save Provider
            </button>
          </div>
        </div>
      </div>
      <div v-if="aiTestResult" class="text-xs px-3 py-2 rounded-lg" :class="aiTestResult.ok ? 'bg-green-50 text-green-700' : 'bg-red-50 text-red-700'">
        {{ aiTestResult.ok ? $t('ai.testSuccess') : $t('ai.testFailed') }}
        <span v-if="aiTestResult.error">: {{ aiTestResult.error }}</span>
        <span v-if="aiTestResult.model"> ({{ aiTestResult.model }})</span>
      </div>
      <div class="grid grid-cols-1 md:grid-cols-3 gap-4 pt-2 border-t border-slate-100">
        <label class="flex items-center gap-2 cursor-pointer">
          <input type="checkbox" v-model="cfg.ai_kyc_enabled" class="rounded" :disabled="!cfg.ai_enabled" />
          <span class="text-sm text-slate-700">{{ $t('ai.enableKyc') }}</span>
        </label>
        <label class="flex items-center gap-2 cursor-pointer">
          <input type="checkbox" v-model="cfg.ai_fraud_enabled" class="rounded" :disabled="!cfg.ai_enabled" />
          <span class="text-sm text-slate-700">{{ $t('ai.enableFraud') }}</span>
        </label>
        <label class="flex items-center gap-2 cursor-pointer">
          <input type="checkbox" v-model="cfg.ai_moderation_enabled" class="rounded" :disabled="!cfg.ai_enabled" />
          <span class="text-sm text-slate-700">{{ $t('ai.enableModeration') }}</span>
        </label>
      </div>
      <div class="pt-4 border-t border-slate-100 space-y-3">
        <div class="flex items-center justify-between">
          <div>
            <h4 class="text-sm font-bold text-slate-800">AI Project Forge</h4>
            <p class="text-xs text-slate-500">Provider, token, base URL, project analysis, multimodal extraction, and report editing run only on backend.</p>
          </div>
          <label class="flex items-center gap-2 cursor-pointer">
            <input type="checkbox" v-model="cfg.ai_project_estimation_enabled" class="rounded" :disabled="!cfg.ai_enabled" />
            <span class="text-sm text-slate-700">Enable Project AI</span>
          </label>
        </div>
        <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label class="text-xs font-medium text-slate-600">Project model</label>
            <input v-model="cfg.ai_project_model" class="input" placeholder="leave blank to use main AI model" />
          </div>
          <div>
            <label class="text-xs font-medium text-slate-600">Prompt version</label>
            <input v-model="cfg.ai_project_prompt_version" class="input" placeholder="v1" />
          </div>
          <div>
            <label class="text-xs font-medium text-slate-600">Max files / MB</label>
            <div class="grid grid-cols-2 gap-2">
              <input v-model="cfg.ai_project_max_files" class="input" type="number" min="1" />
              <input v-model="cfg.ai_project_max_file_size_mb" class="input" type="number" min="1" />
            </div>
          </div>
        </div>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <label class="flex items-center gap-2 cursor-pointer">
            <input type="checkbox" v-model="cfg.ai_multimodal_enabled" class="rounded" :disabled="!cfg.ai_enabled || !cfg.ai_project_estimation_enabled" />
            <span class="text-sm text-slate-700">Enable multimodal file/image analysis</span>
          </label>
          <div>
            <label class="text-xs font-medium text-slate-600">Multimodal model</label>
            <input v-model="cfg.ai_multimodal_model" class="input" placeholder="e.g. gpt-4o, qwen-vl, provider model" />
          </div>
        </div>
      </div>

      <div class="pt-4 border-t border-slate-100">
        <div class="flex items-center justify-between mb-3">
          <div>
            <h4 class="text-sm font-bold text-slate-800">AI Providers</h4>
            <p class="text-xs text-slate-500">Saved backend AI providers. Keep multiple providers here, then select one as active for Project Forge and other AI tasks.</p>
          </div>
          <span class="text-xs rounded-full bg-slate-100 px-2 py-1 text-slate-500">{{ aiProviders.length }} saved</span>
        </div>
        <div v-if="aiProviders.length" class="overflow-x-auto rounded-xl border border-slate-200">
          <table class="min-w-full text-sm">
            <thead class="bg-slate-50 text-xs text-slate-500">
              <tr>
                <th class="px-3 py-2 text-left">Provider</th>
                <th class="px-3 py-2 text-left">Model</th>
                <th class="px-3 py-2 text-left">Project Model</th>
                <th class="px-3 py-2 text-left">Base URL</th>
                <th class="px-3 py-2 text-left">Status</th>
                <th class="px-3 py-2 text-right">Actions</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="provider in aiProviders" :key="provider.id" class="border-t border-slate-100">
                <td class="px-3 py-2 font-semibold text-slate-800">
                  {{ provider.provider }}
                  <span v-if="provider.active" class="ml-2 rounded-full bg-green-50 px-2 py-0.5 text-xs text-green-700">active</span>
                </td>
                <td class="px-3 py-2 text-slate-600">{{ provider.model || '—' }}</td>
                <td class="px-3 py-2 text-slate-600">{{ provider.project_model || '—' }}</td>
                <td class="px-3 py-2 text-slate-500">{{ provider.base_url || 'default' }}</td>
                <td class="px-3 py-2">
                  <span class="rounded-full px-2 py-0.5 text-xs font-semibold" :class="provider.status === 'CONNECTED' ? 'bg-green-50 text-green-700' : provider.status === 'FAILED' ? 'bg-red-50 text-red-700' : 'bg-slate-100 text-slate-500'">
                    {{ provider.status || 'UNKNOWN' }}
                  </span>
                  <span v-if="provider.last_checked_at" class="ml-2 text-xs text-slate-400">{{ provider.last_checked_at }}</span>
                </td>
                <td class="px-3 py-2 text-right">
                  <button class="text-xs font-semibold text-indigo-600 mr-3" @click="useAIProvider(provider)">Use</button>
                  <button class="text-xs font-semibold text-red-500" @click="removeAIProvider(provider.id)">Remove</button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
        <p v-else class="rounded-xl border border-dashed border-slate-200 p-4 text-sm text-slate-400">No saved AI providers yet. Fill the provider fields above, test if needed, then click Save Provider.</p>
      </div>
    </section>

    <!-- Payment Gateway -->
    <section class="card p-5 space-y-4">
      <h3 class="font-bold text-slate-900 flex items-center gap-2"><span>💳</span> {{ $t('integrations.paymentGateway') }}</h3>
      <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label class="text-xs font-medium text-slate-600">{{ $t('integrations.provider') }}</label>
          <select v-model="cfg.payment_provider" class="input">
            <option value="paymongo">PayMongo</option>
            <option value="xendit">Xendit</option>
            <option value="stripe">Stripe</option>
          </select>
        </div>
        <div>
          <label class="text-xs font-medium text-slate-600">{{ $t('integrations.apiKey') }}</label>
          <input v-model="cfg.payment_secret_key" type="password" class="input" placeholder="sk_live_..." />
        </div>
        <div>
          <label class="text-xs font-medium text-slate-600">{{ $t('integrations.publicKey') }}</label>
          <input v-model="cfg.payment_public_key" class="input" placeholder="pk_live_..." />
        </div>
        <div>
          <label class="text-xs font-medium text-slate-600">{{ $t('integrations.webhookSecret') }}</label>
          <input v-model="cfg.payment_webhook_secret" type="password" class="input" placeholder="whsec_..." />
        </div>
      </div>
    </section>

    <!-- Email Service -->
    <section class="card p-5 space-y-4">
      <h3 class="font-bold text-slate-900 flex items-center gap-2"><span>📧</span> {{ $t('integrations.emailService') }}</h3>
      <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label class="text-xs font-medium text-slate-600">{{ $t('integrations.provider') }}</label>
          <select v-model="cfg.email_provider" class="input">
            <option value="smtp">SMTP</option>
            <option value="sendgrid">SendGrid</option>
            <option value="ses">Amazon SES</option>
          </select>
        </div>
        <div>
          <label class="text-xs font-medium text-slate-600">{{ $t('integrations.smtpHost') }}</label>
          <input v-model="cfg.email_host" class="input" placeholder="smtp.gmail.com or SG.xxx" />
        </div>
        <div>
          <label class="text-xs font-medium text-slate-600">{{ $t('integrations.smtpPort') }}</label>
          <input v-model="cfg.email_port" class="input" placeholder="587" />
        </div>
        <div>
          <label class="text-xs font-medium text-slate-600">{{ $t('integrations.fromAddress') }}</label>
          <input v-model="cfg.email_from" class="input" placeholder="noreply@procureping.com" />
        </div>
        <div>
          <label class="text-xs font-medium text-slate-600">{{ $t('integrations.username') }}</label>
          <input v-model="cfg.email_username" class="input" />
        </div>
        <div>
          <label class="text-xs font-medium text-slate-600">{{ $t('integrations.passwordKey') }}</label>
          <input v-model="cfg.email_password" type="password" class="input" />
        </div>
      </div>
    </section>

    <!-- Telegram Bot -->
    <section class="card p-5 space-y-4">
      <h3 class="font-bold text-slate-900 flex items-center gap-2"><span>🤖</span> {{ $t('integrations.telegram') }}</h3>
      <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label class="text-xs font-medium text-slate-600">{{ $t('integrations.botToken') }}</label>
          <input v-model="cfg.telegram_bot_token" type="password" class="input" placeholder="123456:ABC-..." />
        </div>
        <div>
          <label class="text-xs font-medium text-slate-600">{{ $t('integrations.adminChatId') }}</label>
          <input v-model="cfg.telegram_admin_chat_id" class="input" placeholder="-100123456789" />
        </div>
        <div>
          <label class="text-xs font-medium text-slate-600">{{ $t('integrations.webhookUrl') }}</label>
          <input v-model="cfg.telegram_webhook_url" class="input" placeholder="https://api.procureping.com/webhooks/telegram" />
        </div>
        <div class="flex items-center gap-2 pt-5">
          <input type="checkbox" v-model="cfg.telegram_enabled" id="tg-enabled" class="rounded" />
          <label for="tg-enabled" class="text-sm text-slate-700">{{ $t('integrations.enableTelegram') }}</label>
        </div>
      </div>
    </section>

    <!-- Logistics / Carriers -->
    <section class="card p-5 space-y-4">
      <h3 class="font-bold text-slate-900 flex items-center gap-2"><span>🚚</span> {{ $t('integrations.logistics') }}</h3>
      <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label class="text-xs font-medium text-slate-600">{{ $t('integrations.defaultCarrier') }}</label>
          <select v-model="cfg.logistics_default_carrier" class="input">
            <option value="">—</option>
            <option value="j&t">J&T Express</option>
            <option value="lbc">LBC</option>
            <option value="grab">Grab Express</option>
            <option value="lalamove">Lalamove</option>
            <option value="custom">Custom / Self-arrange</option>
          </select>
        </div>
        <div>
          <label class="text-xs font-medium text-slate-600">{{ $t('integrations.trackingApiKey') }}</label>
          <input v-model="cfg.logistics_api_key" type="password" class="input" />
        </div>
        <div>
          <label class="text-xs font-medium text-slate-600">{{ $t('integrations.trackingWebhook') }}</label>
          <input v-model="cfg.logistics_webhook_url" class="input" />
        </div>
        <div class="flex items-center gap-2 pt-5">
          <input type="checkbox" v-model="cfg.logistics_auto_tracking" id="log-auto" class="rounded" />
          <label for="log-auto" class="text-sm text-slate-700">{{ $t('integrations.autoTracking') }}</label>
        </div>
      </div>
    </section>

    <!-- Save -->
    <div class="flex justify-end gap-3">
      <button class="btn btn-secondary" @click="load">{{ $t('common.reset') }}</button>
      <button class="btn btn-primary" :disabled="saving" @click="save">{{ saving ? $t('integrations.saving') : $t('integrations.saveAll') }}</button>
    </div>
    <p v-if="saveMsg" class="text-sm text-green-600 text-right">{{ saveMsg }}</p>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { api } from '@/utils/api'

const { t } = useI18n()
const saving = ref(false)
const saveMsg = ref('')
const testingAi = ref(false)
const aiTestResult = ref(null)
const testingMaps = ref(false)
const mapsTestResult = ref(null)
const aiProviders = ref([])

const maps = reactive({
  provider: 'LOCAL',
  google_maps_api_key: '',
  google_maps_api_key_masked: '',
  google_maps_region: 'PH',
  google_maps_language: 'en',
  maps_cache_ttl_seconds: 86400,
  maps_enabled: true,
})

const mapsKeyPlaceholder = computed(() => maps.provider === 'GOOGLE' ? 'AIza...' : '(not needed for LOCAL)')

const cfg = reactive({
  // AI
  ai_enabled: false,
  ai_provider: 'openai',
  ai_model: 'gpt-4o-mini',
  ai_api_key: '',
  ai_base_url: '',
  ai_confidence_threshold: '0.7',
  ai_kyc_enabled: false,
  ai_fraud_enabled: false,
  ai_moderation_enabled: false,
  ai_project_estimation_enabled: false,
  ai_project_model: '',
  ai_multimodal_enabled: false,
  ai_multimodal_model: '',
  ai_project_prompt_version: 'v1',
  ai_project_max_files: '10',
  ai_project_max_file_size_mb: '10',
  // Payment
  payment_provider: 'paymongo',
  payment_secret_key: '',
  payment_public_key: '',
  payment_webhook_secret: '',
  // Email
  email_provider: 'smtp',
  email_host: '',
  email_port: '587',
  email_from: '',
  email_username: '',
  email_password: '',
  // Telegram
  telegram_bot_token: '',
  telegram_admin_chat_id: '',
  telegram_webhook_url: '',
  telegram_enabled: false,
  // Logistics
  logistics_default_carrier: '',
  logistics_api_key: '',
  logistics_webhook_url: '',
  logistics_auto_tracking: false,
})

const modelPlaceholder = computed(() => {
  return { openai: 'gpt-4o-mini', openai_compatible: 'provider-model', deepseek: 'deepseek-v4-pro', anthropic: 'claude-sonnet-4-6', azure: 'gpt-4o' }[cfg.ai_provider] || 'gpt-4o-mini'
})

function normalizeAIForm() {
  const base = String(cfg.ai_base_url || '').trim()
  if (base.includes('api.deepseek.com')) {
    cfg.ai_provider = 'deepseek'
    cfg.ai_base_url = base.replace(/\/+$/, '')
  } else if (cfg.ai_provider === 'deepseek') {
    cfg.ai_base_url = base ? base.replace(/\/+$/, '') : 'https://api.deepseek.com'
  }
  if (cfg.ai_provider === 'deepseek' && (!cfg.ai_model || cfg.ai_model === 'gpt-4o-mini')) {
    cfg.ai_model = 'deepseek-v4-pro'
  }
  if (cfg.ai_provider === 'deepseek' && (!cfg.ai_project_model || cfg.ai_project_model === 'gpt-4o-mini')) {
    cfg.ai_project_model = cfg.ai_model || 'deepseek-v4-pro'
  }
}

async function load() {
  try {
    const [settingsRes, mapsRes] = await Promise.all([
      api.get('/admin/settings'),
      api.get('/admin/maps/config').catch(() => null),
    ])
    const settings = Array.isArray(settingsRes.data) ? settingsRes.data : []
    for (const s of settings) {
      if (s.key in cfg) {
        if (typeof cfg[s.key] === 'boolean') {
          cfg[s.key] = s.value === 'true' || s.value === true
        } else {
          cfg[s.key] = s.value ?? ''
        }
      }
      if (s.key === 'ai_providers_json') {
        try {
          const parsed = typeof s.value === 'string' ? JSON.parse(s.value || '[]') : s.value
          aiProviders.value = Array.isArray(parsed) ? parsed : []
        } catch {
          aiProviders.value = []
        }
      }
    }
    if (mapsRes?.data) {
      const m = mapsRes.data
      maps.provider = m.provider || 'LOCAL'
      maps.google_maps_api_key_masked = m.google_maps_api_key_masked || ''
      maps.google_maps_region = m.google_maps_region || 'PH'
      maps.google_maps_language = m.google_maps_language || 'en'
      maps.maps_cache_ttl_seconds = m.maps_cache_ttl_seconds ?? 86400
      maps.maps_enabled = m.maps_enabled ?? true
    }
    normalizeAIForm()
  } catch {}
}

async function save() {
  saving.value = true
  saveMsg.value = ''
  try {
    normalizeAIForm()
    const settingsPromises = Object.entries(cfg).map(([key, value]) =>
      api.put(`/admin/settings/${key}`, { value: typeof value === 'boolean' ? String(value) : String(value ?? '') })
    )
    settingsPromises.push(api.put('/admin/settings/ai_providers_json', { value: JSON.stringify(aiProviders.value) }))
    const mapsPayload = { ...maps }
    if (!mapsPayload.google_maps_api_key) delete mapsPayload.google_maps_api_key
    delete mapsPayload.google_maps_api_key_masked
    const mapsPromise = api.put('/admin/maps/config', mapsPayload)
    await Promise.all([...settingsPromises, mapsPromise])
    saveMsg.value = t('integrations.saved')
    setTimeout(() => saveMsg.value = '', 3000)
  } catch (e) {
    alert(e.response?.data?.detail || 'Failed to save')
  }
  saving.value = false
}

async function testAI() {
  testingAi.value = true
  aiTestResult.value = null
  try {
    normalizeAIForm()
    const aiKeys = [
      'ai_enabled','ai_provider','ai_model','ai_api_key','ai_base_url','ai_confidence_threshold',
      'ai_kyc_enabled','ai_fraud_enabled','ai_moderation_enabled',
      'ai_project_estimation_enabled','ai_project_model','ai_multimodal_enabled','ai_multimodal_model',
      'ai_project_prompt_version','ai_project_max_files','ai_project_max_file_size_mb',
    ]
    await Promise.all(aiKeys.map(k =>
      api.put(`/admin/settings/${k}`, { value: typeof cfg[k] === 'boolean' ? String(cfg[k]) : String(cfg[k] ?? '') })
    ))
    const { data } = await api.post('/admin/ai/test')
    aiTestResult.value = data
    markActiveProviderStatus(data?.ok ? 'CONNECTED' : 'FAILED')
  } catch (e) {
    aiTestResult.value = { ok: false, error: e.response?.data?.detail || e.message }
    markActiveProviderStatus('FAILED')
  }
  testingAi.value = false
}

function currentProviderPayload(status = 'UNKNOWN') {
  normalizeAIForm()
  const now = new Date().toISOString().slice(0, 19).replace('T', ' ')
  const existing = aiProviders.value.find(p =>
    p.provider === cfg.ai_provider &&
    p.model === cfg.ai_model &&
    (p.base_url || '') === (cfg.ai_base_url || '')
  )
  return {
    id: existing?.id || (crypto?.randomUUID ? crypto.randomUUID() : `ai_${Date.now()}`),
    provider: cfg.ai_provider,
    model: cfg.ai_model,
    api_key_masked: cfg.ai_api_key ? 'configured' : existing?.api_key_masked || '',
    base_url: cfg.ai_base_url,
    confidence_threshold: cfg.ai_confidence_threshold,
    project_enabled: cfg.ai_project_estimation_enabled,
    project_model: cfg.ai_project_model,
    multimodal_enabled: cfg.ai_multimodal_enabled,
    multimodal_model: cfg.ai_multimodal_model,
    prompt_version: cfg.ai_project_prompt_version,
    max_files: cfg.ai_project_max_files,
    max_file_size_mb: cfg.ai_project_max_file_size_mb,
    status,
    active: true,
    last_checked_at: status === 'UNKNOWN' ? existing?.last_checked_at || '' : now,
  }
}

async function persistAIProviders() {
  await api.put('/admin/settings/ai_providers_json', { value: JSON.stringify(aiProviders.value) })
}

async function saveAIProvider() {
  saving.value = true
  try {
    normalizeAIForm()
    const payload = currentProviderPayload(aiTestResult.value?.ok ? 'CONNECTED' : 'UNKNOWN')
    aiProviders.value = aiProviders.value
      .filter(p => p.id !== payload.id)
      .map(p => ({ ...p, active: false }))
    aiProviders.value.unshift(payload)
    await persistAIProviders()
    await save()
  } catch (e) {
    alert(e.response?.data?.detail || 'Failed to save AI provider')
  }
  saving.value = false
}

function markActiveProviderStatus(status) {
  const payload = currentProviderPayload(status)
  const idx = aiProviders.value.findIndex(p => p.id === payload.id)
  if (idx >= 0) {
    aiProviders.value[idx] = { ...aiProviders.value[idx], status, last_checked_at: payload.last_checked_at }
  }
}

async function useAIProvider(provider) {
  cfg.ai_provider = provider.provider || 'openai'
  cfg.ai_model = provider.model || ''
  cfg.ai_base_url = provider.base_url || ''
  cfg.ai_project_estimation_enabled = !!provider.project_enabled
  cfg.ai_project_model = provider.project_model || ''
  cfg.ai_multimodal_enabled = !!provider.multimodal_enabled
  cfg.ai_multimodal_model = provider.multimodal_model || ''
  cfg.ai_project_prompt_version = provider.prompt_version || 'v1'
  cfg.ai_project_max_files = provider.max_files || '10'
  cfg.ai_project_max_file_size_mb = provider.max_file_size_mb || '10'
  aiProviders.value = aiProviders.value.map(p => ({ ...p, active: p.id === provider.id }))
  await persistAIProviders()
}

async function removeAIProvider(id) {
  aiProviders.value = aiProviders.value.filter(p => p.id !== id)
  await persistAIProviders()
}

async function testMaps() {
  testingMaps.value = true
  mapsTestResult.value = null
  try {
    const payload = { provider: maps.provider, google_maps_region: maps.google_maps_region, google_maps_language: maps.google_maps_language }
    if (maps.google_maps_api_key) payload.google_maps_api_key = maps.google_maps_api_key
    const { data } = await api.post('/admin/maps/test-connection', payload)
    mapsTestResult.value = data
  } catch (e) {
    mapsTestResult.value = { ok: false, error: e.response?.data?.detail || e.message }
  }
  testingMaps.value = false
}

onMounted(load)
</script>
