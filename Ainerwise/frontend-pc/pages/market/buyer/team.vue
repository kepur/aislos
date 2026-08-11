<template>
  <section class="mx-auto max-w-3xl space-y-6">
    <div class="flex flex-wrap items-center justify-between gap-3">
      <div>
        <p class="text-xs font-bold uppercase tracking-[0.2em] text-indigo-300">{{ $t('portal.team.membership') }}</p>
        <h1 class="mt-1 text-2xl font-bold text-white">买家团队</h1>
        <p class="mt-1 text-sm text-slate-400">可代表你公司账户访问与操作的成员。</p>
      </div>
      <button class="btn-secondary" :title="inviteHint" @click="showInviteHint = !showInviteHint">邀请成员</button>
    </div>

    <p v-if="showInviteHint" class="pc-card border-indigo-500/30 text-sm text-slate-300">{{ inviteHint }}</p>

    <div class="grid grid-cols-3 gap-4">
      <div class="pc-card"><p class="text-sm text-slate-400">成员总数</p><p class="mt-1 text-2xl font-bold text-white">{{ items.length }}</p></div>
      <div class="pc-card"><p class="text-sm text-slate-400">活跃</p><p class="mt-1 text-2xl font-bold text-emerald-300">{{ activeCount }}</p></div>
      <div class="pc-card"><p class="text-sm text-slate-400">{{ $t('portal.team.roleOwner') }}</p><p class="mt-1 text-2xl font-bold text-indigo-300">{{ ownerCount }}</p></div>
    </div>

    <div class="pc-card !p-0">
      <div v-if="loading" class="space-y-2 p-4">
        <div v-for="i in 3" :key="i" class="h-14 animate-pulse rounded-xl bg-white/5"></div>
      </div>
      <div v-else-if="!items.length" class="py-12 text-center text-slate-400">
        <div class="text-4xl">👥</div>
        <p class="mt-2 text-sm">还没有团队成员。</p>
      </div>
      <div v-else>
        <div v-for="m in items" :key="m.id" class="flex items-center gap-4 border-b border-white/5 p-4 last:border-0">
          <div class="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-indigo-500/15 text-sm font-medium text-indigo-200">{{ initials(m) }}</div>
          <div class="min-w-0 flex-1">
            <p class="truncate text-sm font-semibold text-white">{{ m.full_name || m.display_name || '未命名' }}</p>
            <p class="truncate text-xs text-slate-500">{{ m.email }}</p>
          </div>
          <span :class="['rounded-full px-2 py-0.5 text-xs', isOwner(m) ? 'bg-indigo-500/15 text-indigo-300' : 'bg-white/10 text-slate-300']">{{ roleLabel(m.role) }}</span>
          <span :class="['rounded-full px-2 py-0.5 text-xs', (m.is_active ?? m.status === 'ACTIVE') ? 'bg-emerald-500/15 text-emerald-300' : 'bg-amber-500/15 text-amber-300']">{{ (m.is_active ?? m.status === 'ACTIVE') ? '活跃' : '停用' }}</span>
        </div>
      </div>
    </div>

    <p v-if="error" class="pc-card text-sm text-red-300">{{ error }}</p>
  </section>
</template>

<script setup lang="ts">
definePageMeta({ layout: 'procurement', middleware: ['auth'], alias: ['/buyer/team'] })

const { listBuyerTeam } = useCommerce()
const items = ref<any[]>([])
const error = ref('')
const loading = ref(true)
const showInviteHint = ref(false)
const inviteHint = '邀请新成员由公司 Owner 在账户后台 / 管理员处办理；本工作台展示当前公司 workspace 的成员。'

const activeCount = computed(() => items.value.filter(m => m.is_active ?? m.status === 'ACTIVE').length)
const ownerCount = computed(() => items.value.filter(isOwner).length)

function isOwner(m: any) {
  return /owner/i.test(String(m.role || ''))
}
const { t } = useI18n()
function roleLabel(role?: string) {
  const r = String(role || '').toLowerCase()
  if (r.includes('owner')) return t('portal.team.roleOwner')
  if (r.includes('manager')) return t('portal.team.roleManager')
  if (r.includes('member')) return t('portal.team.roleMember')
  return role || t('portal.team.roleMember')
}
function initials(m: any) {
  const n = String(m.full_name || m.display_name || m.email || '?').trim()
  return n.slice(0, 1).toUpperCase()
}

onMounted(async () => {
  try {
    items.value = (await listBuyerTeam()).items || []
  } catch (e: any) {
    error.value = e?.data?.detail || e?.message || '加载团队失败'
  } finally {
    loading.value = false
  }
})
</script>
