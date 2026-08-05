<template>
  <div class="min-h-screen flex flex-col bg-slate-50 text-slate-900">
    <header class="bg-white border-b border-slate-200 sticky top-0 z-50">
      <div class="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        <div class="flex items-center space-x-8">
          <NuxtLink :to="localizedPath('/')" class="text-2xl font-bold text-indigo-600 tracking-tight">
            {{ $config.public.appName }}
          </NuxtLink>
          <nav :key="topNavRenderKey" class="hidden md:flex space-x-8 text-sm font-medium">
            <NuxtLink
              v-for="item in topNav"
              :key="`${topNavRenderKey}:${item.to}`"
              :to="localizedPath(item.to)"
              custom
              v-slot="{ href, navigate }"
            >
              <a
                :href="href"
                :aria-current="isTopNavActive(item) ? 'page' : undefined"
                class="whitespace-nowrap hover:text-indigo-600 transition-colors"
                :class="topNavClass(item)"
                @click="handleTopNavClick($event, navigate, item.to)"
              >
                {{ item.label }}
              </a>
            </NuxtLink>
          </nav>
        </div>

        <div class="flex items-center space-x-4">
          <ClientOnly>
            <div class="hidden lg:flex items-center border-r border-slate-200 pr-3">
              <USelect v-model="appStore.language" :options="shortLanguageOptions" option-attribute="label" value-attribute="code" variant="none" size="sm" class="w-20" @update:model-value="switchLanguage" />
            </div>
          </ClientOnly>
          <a
            :href="$config.public.aislosSiteUrl"
            :title="appStore.t('layout.ainerwiseSite')"
            class="hidden sm:inline-flex items-center gap-1.5 whitespace-nowrap rounded-full border border-indigo-200 bg-indigo-50 px-3 py-1.5 text-sm font-semibold text-indigo-700 transition-colors hover:border-indigo-300 hover:bg-indigo-100"
          >
            <span aria-hidden="true">←</span> {{ appStore.t('layout.ainerwiseSite') }}
          </a>
          <ClientOnly>
            <div v-if="!authStore.isLoggedIn">
              <NuxtLink :to="localizedPath('/login')" class="text-sm font-medium text-slate-600 hover:text-indigo-600">{{ appStore.t('auth.login') }}</NuxtLink>
            </div>
            <div v-else class="flex items-center space-x-4">
              <NuxtLink :to="dashboardPath" class="text-sm font-medium text-indigo-600 hover:text-indigo-500">{{ appStore.t('layout.dashboard') }}</NuxtLink>
              <UButton size="xs" color="gray" variant="ghost" @click="handleLogout">{{ appStore.t('auth.logout') }}</UButton>
            </div>
            <template #fallback>
              <NuxtLink :to="localizedPath('/login')" class="text-sm font-medium text-slate-600 hover:text-indigo-600">{{ appStore.t('auth.login') }}</NuxtLink>
            </template>
          </ClientOnly>
          <UButton :to="localizedPath('/post-request')" color="indigo" variant="solid">{{ appStore.t('action.postRequest') }}</UButton>
        </div>
      </div>
    </header>

    <main class="flex-grow pt-16">
      <slot />
    </main>

    <!-- Minimal Footer -->
    <footer class="bg-slate-900 text-slate-300 py-12">
      <div class="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 grid grid-cols-1 md:grid-cols-4 gap-8">
        <div>
          <h3 class="text-white text-lg font-bold mb-4">{{ $config.public.appName }}</h3>
          <p class="text-sm">The reverse marketplace for professional buyers and verified suppliers.</p>
        </div>
        <div>
          <h4 class="text-white font-semibold mb-4">{{ appStore.t('footer.buyers') }}</h4>
          <ul class="space-y-2 text-sm">
            <li><NuxtLink :to="localizedPath('/post-request')" class="hover:text-white">{{ appStore.t('footer.postRequest') }}</NuxtLink></li>
            <li><NuxtLink :to="localizedPath('/how-it-works')" class="hover:text-white">{{ appStore.t('nav.how') }}</NuxtLink></li>
            <li><NuxtLink :to="localizedPath('/how-it-works')" class="hover:text-white">{{ appStore.t('footer.escrow') }}</NuxtLink></li>
          </ul>
        </div>
        <div>
          <h4 class="text-white font-semibold mb-4">{{ appStore.t('footer.suppliers') }}</h4>
          <ul class="space-y-2 text-sm">
            <li><NuxtLink :to="localizedPath('/register-supplier')" class="hover:text-white">{{ appStore.t('footer.becomeSupplier') }}</NuxtLink></li>
            <li><NuxtLink :to="localizedPath('/pricing')" class="hover:text-white">{{ appStore.t('footer.pricing') }}</NuxtLink></li>
            <li><NuxtLink :to="localizedPath('/trust-safety')" class="hover:text-white">{{ appStore.t('footer.verification') }}</NuxtLink></li>
          </ul>
        </div>
        <div>
          <h4 class="text-white font-semibold mb-4">{{ appStore.t('footer.settings') }}</h4>
          <ClientOnly>
            <div class="flex flex-wrap gap-2">
              <USelect v-model="appStore.language" :options="appStore.languageOptions" option-attribute="label" value-attribute="code" placeholder="Language" class="w-full max-w-[190px]" @update:model-value="switchLanguage" />
              <USelect v-model="appStore.currency" :options="appStore.currencyOptions" option-attribute="label" value-attribute="code" placeholder="Currency" class="w-full max-w-[230px]" @update:model-value="appStore.setCurrency" />
            </div>
          </ClientOnly>
        </div>
      </div>
      <div class="container mx-auto px-4 mt-8 pt-8 border-t border-slate-800 text-sm flex justify-between">
        <p>&copy; {{ new Date().getFullYear() }} {{ $config.public.appName }}. All rights reserved.</p>
        <div class="space-x-4">
          <NuxtLink :to="localizedPath('/')" class="hover:text-white">{{ appStore.t('footer.terms') }}</NuxtLink>
          <NuxtLink :to="localizedPath('/')" class="hover:text-white">{{ appStore.t('footer.privacy') }}</NuxtLink>
        </div>
      </div>
    </footer>
  </div>
</template>

<script setup lang="ts">
import { useAppStore } from '~/stores/app'
import { useAuthStore } from '~/stores/auth'
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { LANGUAGE_TO_URI_LOCALE_PREFIX, stripLocalePrefix } from '~/utils/localeRoutes'

const appStore = useAppStore()
const authStore = useAuthStore()
const route = useRoute()
const router = useRouter()

type TopNavItem = {
  to: string
  label: string
  exact?: boolean
}

const topNav = computed(() => [
  { to: '/how-it-works', label: appStore.t('nav.how') },
  { to: '/marketplace', label: appStore.t('nav.marketplace') },
  { to: '/categories', label: appStore.t('nav.categories') },
  { to: '/buyer/projects', label: appStore.t('nav.aiProjects') },
])

const currentTopPath = ref(normalizePath(route.path))
const topNavRenderKey = computed(() => `top-nav:${currentTopPath.value}`)

// Header shows compact URI-style codes (EN/CN/RS…); full names stay in the footer.
const shortLanguageOptions = computed(() =>
  appStore.languageOptions.map((option) => ({
    code: option.code,
    label: (LANGUAGE_TO_URI_LOCALE_PREFIX[String(option.code)] || String(option.code)).toUpperCase(),
  }))
)

watch(
  () => route.fullPath,
  () => {
    currentTopPath.value = normalizePath(route.path)
  },
  { immediate: true }
)

let removeAfterEach: (() => void) | undefined

onMounted(() => {
  currentTopPath.value = normalizePath(window.location.pathname)
  removeAfterEach = router.afterEach((to) => {
    currentTopPath.value = normalizePath(to.path)
  })
})

onBeforeUnmount(() => {
  removeAfterEach?.()
})

const dashboardPath = computed(() => {
  if (authStore.isAdmin) return localizedPath('/admin/dashboard')
  if (authStore.isSupplier) return localizedPath('/supplier/dashboard')
  return localizedPath('/buyer/dashboard')
})

function normalizePath(path: string) {
  return stripLocalePrefix(path).replace(/\/+$/, '') || '/'
}

function localizedPath(path: string) {
  return appStore.localizedPath(path)
}

function isTopNavActive(item: TopNavItem) {
  const target = normalizePath(item.to)
  return item.exact
    ? currentTopPath.value === target
    : currentTopPath.value === target || currentTopPath.value.startsWith(`${target}/`)
}

function topNavClass(item: TopNavItem) {
  return isTopNavActive(item)
    ? 'font-semibold text-indigo-600'
    : 'text-slate-600'
}

function handleTopNavClick(event: MouseEvent, navigate: (event?: MouseEvent) => Promise<void> | void, to: string) {
  if (
    event.button === 0 &&
    !event.defaultPrevented &&
    !event.metaKey &&
    !event.altKey &&
    !event.ctrlKey &&
    !event.shiftKey
  ) {
    currentTopPath.value = normalizePath(to)
  }
  navigate(event)
}

function switchLanguage(lang: string) {
  appStore.setLanguage(lang)
  const target = appStore.localizedPath(route.fullPath, lang)
  if (target !== route.fullPath) navigateTo(target)
}

const handleLogout = async () => {
  await authStore.logout()
  navigateTo(localizedPath('/'))
}
</script>
