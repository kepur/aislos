<template>
  <div class="max-w-5xl mx-auto space-y-6">
    <div class="flex items-start justify-between gap-4">
      <div>
        <h1 class="text-2xl font-bold text-slate-900">Wallet & Escrow</h1>
        <p class="text-slate-500 mt-1">Create local-currency deposits and use verified balance for secure escrow.</p>
      </div>
      <UButton color="indigo" :loading="loading" @click="loadWallet">Refresh</UButton>
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-[1fr_360px] gap-6">
      <div class="space-y-6">
        <div class="grid grid-cols-1 sm:grid-cols-3 gap-6">
          <UCard class="bg-indigo-600 text-white">
            <p class="text-indigo-100 text-sm font-medium">Available Balance</p>
            <p class="text-3xl font-bold mt-2">{{ money(wallet?.available_balance_minor || 0, wallet?.currency || 'PHP') }}</p>
            <p class="mt-4 text-xs text-indigo-100">Verified deposit balance</p>
          </UCard>

          <UCard class="bg-white">
            <p class="text-slate-500 text-sm font-medium">Funds in Escrow</p>
            <p class="text-3xl font-bold text-slate-900 mt-2">{{ money(wallet?.locked_balance_minor || 0, wallet?.currency || 'PHP') }}</p>
            <div class="mt-4 flex items-center text-xs text-slate-500">
              <UIcon name="i-heroicons-lock-closed" class="mr-1" />
              Locked for active orders
            </div>
          </UCard>

          <UCard class="bg-white">
            <p class="text-slate-500 text-sm font-medium">Total Deposited</p>
            <p class="text-3xl font-bold text-slate-900 mt-2">{{ money(wallet?.total_deposited_minor || 0, wallet?.currency || 'PHP') }}</p>
            <div class="mt-4 flex items-center text-xs text-green-600">
              <UIcon name="i-heroicons-shield-check" class="mr-1" />
              Counts toward trust score
            </div>
          </UCard>
        </div>

        <UCard>
          <template #header>
            <div class="flex justify-between items-center">
              <h3 class="text-lg font-medium text-slate-900">Wallet Ledger</h3>
              <UBadge color="indigo" variant="subtle">{{ transactions.length }} records</UBadge>
            </div>
          </template>

          <UTable :columns="columns" :rows="transactionRows">
            <template #amount-data="{ row }">
              <span :class="row.direction === 'credit' ? 'text-green-600' : 'text-slate-900'" class="font-medium">
                {{ row.direction === 'credit' ? '+' : '-' }}{{ row.amount }}
              </span>
            </template>
            <template #status-data="{ row }">
              <UBadge :color="row.direction === 'credit' ? 'green' : 'yellow'" variant="subtle">{{ row.status }}</UBadge>
            </template>
          </UTable>
        </UCard>
      </div>

      <div class="space-y-6">
        <UCard>
          <template #header>
            <h3 class="text-lg font-medium text-slate-900">PHP Deposit</h3>
          </template>
          <form class="space-y-4" @submit.prevent="createDeposit">
            <UFormGroup label="Amount" required>
              <UInput v-model.number="depositAmount" type="number" min="1" placeholder="100" />
            </UFormGroup>
            <UFormGroup label="Payment Method" required>
              <USelect v-model="network" :options="['LOCAL_BANK', 'GCASH', 'MAYA']" />
            </UFormGroup>
            <UButton type="submit" color="indigo" block :loading="creating">Create Deposit Address</UButton>
          </form>
        </UCard>

        <UCard v-if="activeDeposit">
          <template #header>
            <div>
              <h3 class="text-lg font-medium text-slate-900">Submit Payment Reference</h3>
              <p class="text-xs text-slate-500 mt-1">Status: {{ activeDeposit.status }}</p>
            </div>
          </template>
          <div class="space-y-4">
            <div>
              <p class="text-xs font-semibold text-slate-500 uppercase">Payment Instruction</p>
              <p class="mt-1 break-all rounded-lg bg-slate-50 p-3 font-mono text-xs text-slate-700">{{ activeDeposit.deposit_address }}</p>
            </div>
            <UFormGroup label="Payment Reference">
              <UInput v-model="txHash" placeholder="Paste bank/e-wallet reference number" />
            </UFormGroup>
            <UButton color="green" block :loading="submittingTx" @click="submitTx">Submit for Admin Review</UButton>
          </div>
        </UCard>

        <UAlert v-if="message" :color="messageType" :title="message" />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
definePageMeta({ layout: 'buyer', middleware: ['auth'] })

type Wallet = {
  id: string
  currency: string
  available_balance_minor: number
  locked_balance_minor: number
  total_deposited_minor: number
}
type WalletTransaction = {
  id: string
  tx_type: string
  amount_delta_minor: number
  currency: string
  note?: string
  created_at: string
}
type WalletDeposit = {
  id: string
  amount_minor: number
  currency: string
  network: string
  deposit_address: string
  status: string
}

const config = useRuntimeConfig()
const authStore = useAuthStore()
const loading = ref(true)
const creating = ref(false)
const submittingTx = ref(false)
const wallet = ref<Wallet | null>(null)
const transactions = ref<WalletTransaction[]>([])
const activeDeposit = ref<WalletDeposit | null>(null)
const depositAmount = ref(100)
const network = ref('LOCAL_BANK')
const txHash = ref('')
const message = ref('')
const messageType = ref<'green' | 'red' | 'blue'>('blue')

const columns = [
  { key: 'date', label: 'Date' },
  { key: 'description', label: 'Description' },
  { key: 'amount', label: 'Amount' },
  { key: 'status', label: 'Status' },
]

const transactionRows = computed(() =>
  transactions.value.map((tx) => ({
    id: tx.id,
    date: new Date(tx.created_at).toLocaleString(),
    description: tx.note || tx.tx_type,
    amount: money(Math.abs(tx.amount_delta_minor), tx.currency),
    direction: tx.amount_delta_minor >= 0 ? 'credit' : 'debit',
    status: tx.tx_type,
  }))
)

function headers() {
  return { Authorization: `Bearer ${authStore.accessToken}` }
}

function money(minor: number, currency = 'PHP') {
  const value = (minor || 0) / 100
  if (currency === 'USDT') return `${value.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })} USDT`
  return new Intl.NumberFormat('en-PH', { style: 'currency', currency }).format(value)
}

async function loadWallet() {
  loading.value = true
  try {
    const data = await $fetch<{ wallets: Wallet[] }>(`${config.public.apiBase}/wallets/me`, { headers: headers() })
    wallet.value = data.wallets[0] || null
    transactions.value = await $fetch<WalletTransaction[]>(`${config.public.apiBase}/wallets/transactions`, { headers: headers() })
  } finally {
    loading.value = false
  }
}

async function createDeposit() {
  creating.value = true
  message.value = ''
  try {
    activeDeposit.value = await $fetch<WalletDeposit>(`${config.public.apiBase}/wallets/deposits`, {
      method: 'POST',
      body: {
        amount_minor: Math.round(Number(depositAmount.value || 0) * 100),
        currency: 'PHP',
        network: network.value,
        provider: network.value === 'LOCAL_BANK' ? 'MANUAL_BANK' : 'LOCAL_EWALLET',
        payment_method: network.value === 'LOCAL_BANK' ? 'PHP_MANUAL_BANK' : `PHP_${network.value}`,
      },
      headers: headers(),
    })
    messageType.value = 'blue'
    message.value = 'Payment instruction created. Submit your bank/e-wallet reference after transfer.'
  } catch (err: any) {
    messageType.value = 'red'
    message.value = err?.data?.detail || err?.message || 'Failed to create deposit.'
  } finally {
    creating.value = false
  }
}

async function submitTx() {
  if (!activeDeposit.value || !txHash.value.trim()) return
  submittingTx.value = true
  try {
    activeDeposit.value = await $fetch<WalletDeposit>(`${config.public.apiBase}/wallets/deposits/${activeDeposit.value.id}/submit-tx`, {
      method: 'POST',
      body: { tx_hash: txHash.value.trim() },
      headers: headers(),
    })
    messageType.value = 'green'
    message.value = 'Payment reference submitted. Admin finance review is pending.'
    txHash.value = ''
    await loadWallet()
  } catch (err: any) {
    messageType.value = 'red'
    message.value = err?.data?.detail || err?.message || 'Failed to submit tx_hash.'
  } finally {
    submittingTx.value = false
  }
}

onMounted(loadWallet)
</script>
