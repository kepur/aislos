<template>
  <div class="min-h-screen overflow-hidden bg-slate-950 text-white">
    <header class="sticky top-0 z-50 border-b border-white/10 bg-slate-950/88 backdrop-blur-xl">
      <div class="flex h-14 items-center justify-between gap-3 px-4 pt-safe">
        <NuxtLink :to="localizedPath('/')" class="flex min-w-0 items-center gap-2">
          <div class="flex h-8 w-8 flex-none items-center justify-center rounded-xl bg-emerald-400 text-sm font-black text-slate-950">
            AW
          </div>
          <div class="min-w-0">
            <p class="truncate text-base font-black leading-none">AinerWise</p>
            <p class="truncate text-[10px] font-semibold uppercase tracking-[0.18em] text-emerald-200/80">
              {{ homeCopy.mobileSite }}
            </p>
          </div>
        </NuxtLink>

        <div class="flex items-center gap-1.5">
          <NuxtLink :to="localizedPath('/auth/login')" class="rounded-full border border-white/15 px-3 py-1.5 text-xs font-bold text-white/80">
            {{ homeCopy.signIn }}
          </NuxtLink>
          <NuxtLink :to="localizedPath('/auth/register?role=BUYER')" class="rounded-full bg-emerald-400 px-3 py-1.5 text-xs font-extrabold text-slate-950">
            {{ homeCopy.register }}
          </NuxtLink>
        </div>
      </div>

      <nav class="flex gap-2 overflow-x-auto px-4 pb-3 scrollbar-hide">
        <NuxtLink :to="marketPath" class="rounded-full border border-emerald-300/30 bg-emerald-300/10 px-3 py-1.5 text-xs font-bold text-emerald-100">
          {{ homeCopy.navMarket }}
        </NuxtLink>
        <a href="#brain" class="rounded-full border border-white/10 bg-white/5 px-3 py-1.5 text-xs font-bold text-white/80">
          {{ homeCopy.navBrain }}
        </a>
        <a href="#solutions" class="rounded-full border border-white/10 bg-white/5 px-3 py-1.5 text-xs font-bold text-white/80">
          {{ homeCopy.navSolutions }}
        </a>
        <a href="#products" class="rounded-full border border-white/10 bg-white/5 px-3 py-1.5 text-xs font-bold text-white/80">
          {{ homeCopy.navProducts }}
        </a>
      </nav>
    </header>

    <main>
      <section class="relative px-4 pb-10 pt-8">
        <div class="absolute inset-0 bg-[radial-gradient(circle_at_20%_10%,rgba(16,185,129,0.35),transparent_32%),radial-gradient(circle_at_85%_18%,rgba(56,189,248,0.24),transparent_30%),linear-gradient(135deg,#020617_0%,#07111f_55%,#06251f_100%)]"></div>
        <div class="absolute inset-0 opacity-35">
          <div class="absolute left-0 top-16 h-px w-full bg-emerald-300/30"></div>
          <div class="absolute left-8 top-0 h-full w-px bg-cyan-200/10"></div>
          <div class="absolute right-16 top-0 h-full w-px bg-emerald-200/10"></div>
          <div class="absolute -right-20 top-32 h-64 w-64 rounded-full border border-emerald-200/20"></div>
          <div class="absolute -left-24 bottom-10 h-72 w-72 rounded-full border border-cyan-200/15"></div>
        </div>

        <div class="relative">
          <div class="mb-5 flex flex-wrap gap-2">
            <span
              v-for="badge in heroBadges"
              :key="badge"
              class="rounded-full border border-emerald-300/20 bg-emerald-300/10 px-3 py-1.5 text-[11px] font-black uppercase tracking-[0.16em] text-emerald-100"
            >
              {{ badge }}
            </span>
          </div>

          <h1 class="text-[42px] font-black leading-[0.98] tracking-tight">
            {{ homeCopy.title }}
          </h1>
          <p class="mt-5 text-base leading-7 text-slate-300">
            {{ homeCopy.subtitle }}
          </p>

          <div class="mt-7 grid grid-cols-[1.15fr_1fr] gap-3">
            <NuxtLink :to="marketPath" class="rounded-2xl bg-emerald-400 px-4 py-4 text-center text-sm font-black text-slate-950 shadow-2xl shadow-emerald-950/40 active:scale-[0.99]">
              {{ homeCopy.primaryCta }}
            </NuxtLink>
            <NuxtLink :to="smartBuildingRequestPath" class="rounded-2xl border border-white/15 bg-white/10 px-4 py-4 text-center text-sm font-extrabold text-white backdrop-blur active:scale-[0.99]">
              {{ homeCopy.secondaryCta }}
            </NuxtLink>
          </div>

          <section id="brain" class="mt-8 overflow-hidden rounded-[2rem] border border-white/10 bg-slate-950/55 p-4 shadow-2xl shadow-black/30 backdrop-blur">
            <div class="relative min-h-[300px]">
              <div class="absolute inset-0 rounded-[1.5rem] bg-[linear-gradient(rgba(148,163,184,0.08)_1px,transparent_1px),linear-gradient(90deg,rgba(148,163,184,0.08)_1px,transparent_1px)] bg-[size:34px_34px]"></div>
              <div class="absolute left-1/2 top-1/2 h-28 w-28 -translate-x-1/2 -translate-y-1/2 rounded-full bg-emerald-400 shadow-[0_0_90px_rgba(16,185,129,0.55)]"></div>
              <div class="absolute left-1/2 top-1/2 h-44 w-44 -translate-x-1/2 -translate-y-1/2 rounded-full border border-emerald-300/20"></div>
              <div class="absolute left-1/2 top-1/2 h-64 w-64 -translate-x-1/2 -translate-y-1/2 rounded-full border border-cyan-300/10"></div>

              <div class="absolute left-1/2 top-1/2 flex h-28 w-28 -translate-x-1/2 -translate-y-1/2 flex-col items-center justify-center rounded-full text-center text-slate-950">
                <span class="text-[10px] font-black uppercase tracking-[0.16em]">AinerWise</span>
                <span class="mt-0.5 text-lg font-black">AI Brain</span>
              </div>

              <div
                v-for="node in brainNodes"
                :key="node.label"
                class="absolute rounded-2xl border border-white/10 bg-slate-900/80 px-3 py-2 text-xs font-extrabold text-white shadow-lg backdrop-blur"
                :class="node.className"
              >
                <span class="mr-1 text-emerald-300">●</span>{{ node.label }}
              </div>

              <div class="absolute bottom-4 left-4 right-4 rounded-2xl border border-emerald-200/10 bg-slate-950/85 p-4">
                <p class="text-[10px] font-black uppercase tracking-[0.2em] text-emerald-300">
                  {{ homeCopy.brainKicker }}
                </p>
                <h2 class="mt-1 text-xl font-black">{{ homeCopy.brainTitle }}</h2>
                <p class="mt-2 text-xs leading-5 text-slate-300">{{ homeCopy.brainText }}</p>
              </div>
            </div>
          </section>
        </div>
      </section>

      <section id="solutions" class="bg-slate-50 px-4 py-10 text-slate-950">
        <div class="mb-6">
          <p class="text-[11px] font-black uppercase tracking-[0.2em] text-emerald-600">{{ homeCopy.solutionKicker }}</p>
          <h2 class="mt-2 text-3xl font-black leading-tight">{{ homeCopy.solutionTitle }}</h2>
          <p class="mt-3 text-sm leading-6 text-slate-600">{{ homeCopy.solutionText }}</p>
        </div>

        <div class="space-y-3">
          <NuxtLink
            v-for="solution in solutionCards"
            :key="solution.title"
            :to="smartBuildingRequestPath"
            class="block rounded-3xl border border-slate-200 bg-white p-5 shadow-sm active:scale-[0.99]"
          >
            <div class="flex items-start justify-between gap-4">
              <div>
                <p class="text-[10px] font-black uppercase tracking-[0.16em] text-emerald-600">{{ solution.kicker }}</p>
                <h3 class="mt-2 text-lg font-black text-slate-950">{{ solution.title }}</h3>
                <p class="mt-2 text-sm leading-6 text-slate-600">{{ solution.text }}</p>
              </div>
              <span class="flex h-9 w-9 flex-none items-center justify-center rounded-full bg-slate-950 text-sm font-black text-white">→</span>
            </div>
          </NuxtLink>
        </div>
      </section>

      <section id="products" class="bg-white px-4 py-10 text-slate-950">
        <div class="mb-6 flex items-end justify-between gap-4">
          <div>
            <p class="text-[11px] font-black uppercase tracking-[0.2em] text-indigo-600">{{ homeCopy.productsKicker }}</p>
            <h2 class="mt-2 text-3xl font-black leading-tight">{{ homeCopy.productsTitle }}</h2>
          </div>
          <NuxtLink :to="marketPath" class="rounded-full bg-slate-950 px-4 py-2 text-xs font-black text-white">
            {{ homeCopy.openMarket }}
          </NuxtLink>
        </div>

        <div class="grid grid-cols-2 gap-3">
          <NuxtLink
            v-for="product in productCards"
            :key="product"
            :to="marketPath"
            class="rounded-3xl border border-slate-200 bg-slate-50 p-4 text-sm font-extrabold text-slate-900 active:scale-[0.99]"
          >
            <span class="mb-4 inline-flex h-10 w-10 items-center justify-center rounded-2xl bg-white text-lg shadow-sm">⌁</span>
            <span class="block leading-snug">{{ product }}</span>
          </NuxtLink>
        </div>
      </section>

      <section class="bg-slate-950 px-4 py-10">
        <div class="rounded-[2rem] border border-emerald-300/20 bg-emerald-300/10 p-5">
          <p class="text-[11px] font-black uppercase tracking-[0.2em] text-emerald-200">{{ homeCopy.marketSwitchKicker }}</p>
          <h2 class="mt-2 text-2xl font-black">{{ homeCopy.marketSwitchTitle }}</h2>
          <p class="mt-3 text-sm leading-6 text-slate-300">{{ homeCopy.marketSwitchText }}</p>
          <div class="mt-5 grid grid-cols-2 gap-3">
            <NuxtLink :to="marketPath" class="rounded-2xl bg-white px-4 py-3 text-center text-sm font-black text-slate-950">
              {{ homeCopy.market }}
            </NuxtLink>
            <NuxtLink :to="marketRequestPath" class="rounded-2xl border border-white/15 px-4 py-3 text-center text-sm font-black text-white">
              {{ homeCopy.generalRequest }}
            </NuxtLink>
          </div>
        </div>
      </section>
    </main>
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue";
import { useI18n } from "vue-i18n";
import { getLocalePrefixFromPath, withLocalePrefix } from "~/utils/localeRoutes";

definePageMeta({ layout: "default", middleware: [] });
useHead({
  title: "AinerWise Mobile",
  meta: [
    {
      name: "description",
      content: "AinerWise mobile official site for AI smart building, KNX solutions, products, procurement marketplace and local delivery.",
    },
  ],
});

const route = useRoute();
const { locale } = useI18n({ useScope: "global" });

const copyByLocale: Record<string, Record<string, string>> = {
  en: {
    mobileSite: "mobile official site",
    signIn: "Sign in",
    register: "Register",
    market: "Market",
    navBrain: "AI Brain",
    navSolutions: "Solutions",
    navProducts: "Products",
    navMarket: "Market",
    title: "AI smart building, products and delivery in one AinerWise experience.",
    subtitle: "The official mobile site explains the AI building brain, KNX + hardware solutions and smart living upgrades. The Market stays separate for product search, used options and supplier quotes.",
    heroBadges: "KNX + AI|Smart Building|Products + Delivery",
    primaryCta: "Shop Market",
    secondaryCta: "AI building request",
    brainKicker: "AinerWise AI Layer",
    brainTitle: "A focused AI brain for real buildings",
    brainText: "It connects rooms, devices, energy, security, service tasks and procurement so customers can start from one simple request.",
    solutionKicker: "Solutions",
    solutionTitle: "Designed for villas, small hotels and practical upgrades.",
    solutionText: "Official-site requests stay focused: fewer categories, clearer questions, better BOQ and RFQ output.",
    solutions: "Villa Smart Home|Rooms, lighting, shading, security and comfort in one plan|Small Hotel Upgrade|Room control, energy, CCTV, Wi-Fi and service packages|Energy + Security|Solar, meters, access, monitoring and maintenance",
    productsKicker: "Product paths",
    productsTitle: "Products are still the first conversion path.",
    products: "KNX devices|Smart panels|Sensors|CCTV|Energy meters|Service packages",
    openMarket: "Open",
    marketSwitchKicker: "Separate but connected",
    marketSwitchTitle: "Official site and Market are two mobile surfaces.",
    marketSwitchText: "AinerWise Official explains the vision. AinerWise Market sells, sources, lists used stock and posts broad AI procurement requests. Both write to AinerWise Core.",
    generalRequest: "General AI request",
  },
  zh: {
    mobileSite: "手机官网",
    signIn: "登录",
    register: "注册",
    market: "市场",
    navBrain: "AI 大脑",
    navSolutions: "解决方案",
    navProducts: "产品",
    navMarket: "Market",
    title: "AI 智能建筑、产品和交付，都在 AinerWise。",
    subtitle: "手机官网负责讲清楚 AI 建筑大脑、KNX + 硬件方案、智能生活升级。Market 单独负责商品搜索、二手/回收、供应商报价和通用采购需求。",
    heroBadges: "KNX + AI|智能建筑|产品 + 交付",
    primaryCta: "进入市场",
    secondaryCta: "AI 建筑评估",
    brainKicker: "AinerWise AI Layer",
    brainTitle: "面向真实建筑的 AI 大脑",
    brainText: "把房间、设备、能源、安防、服务任务和采购连接起来，让客户从一句需求开始，而不是理解一堆系统。",
    solutionKicker: "解决方案",
    solutionTitle: "先聚焦别墅、小酒店和真实改造场景。",
    solutionText: "官网入口的需求类别更少，追问更清晰，后续 BOQ 和 RFQ 质量更稳。",
    solutions: "Villa Smart Home|灯光、窗帘、安防、舒适度和场景联动|Small Hotel Upgrade|客房控制、节能、CCTV、Wi-Fi 和服务套餐|Energy + Security|光伏、电表、门禁、监控和维护",
    productsKicker: "产品路径",
    productsTitle: "客户最先看到的，仍然应该是产品。",
    products: "KNX 设备|智能面板|传感器|CCTV|能源电表|服务套餐",
    openMarket: "打开",
    marketSwitchKicker: "分开，但互通",
    marketSwitchTitle: "官网和 Market 是两个手机端界面。",
    marketSwitchText: "AinerWise 官网负责品牌和智能建筑认知；AinerWise Market 负责卖货、找货、发布二手/回收商品和通用 AI 采购需求。两边都写入 AinerWise Core。",
    generalRequest: "通用 AI 需求",
  },
  sr: {
    mobileSite: "mobilni zvanicni sajt",
    signIn: "Prijava",
    register: "Registracija",
    market: "Market",
    navBrain: "AI mozak",
    navSolutions: "Resenja",
    navProducts: "Proizvodi",
    navMarket: "Market",
    title: "AI pametna zgrada, proizvodi i isporuka u jednom AinerWise iskustvu.",
    subtitle: "Zvanicni mobilni sajt objasnjava AI mozak zgrade i KNX + hardver. Market je odvojen za pretragu proizvoda, polovne opcije i ponude dobavljaca.",
    heroBadges: "KNX + AI|Pametna zgrada|Proizvodi + isporuka",
    primaryCta: "Otvori Market",
    secondaryCta: "AI zahtev",
    brainKicker: "AinerWise AI Layer",
    brainTitle: "AI mozak za stvarne objekte",
    brainText: "Povezuje sobe, uredjaje, energiju, bezbednost, servis i nabavku iz jednog jednostavnog zahteva.",
    solutionKicker: "Resenja",
    solutionTitle: "Fokus na vile, male hotele i realne nadogradnje.",
    solutionText: "Zvanicni tok ima manje kategorija i jasnija pitanja za bolji BOQ i RFQ.",
    solutions: "Villa Smart Home|Rasveta, zavese, bezbednost i komfor|Small Hotel Upgrade|Kontrola soba, energija, CCTV, Wi-Fi i servis|Energy + Security|Solar, brojila, pristup, monitoring i odrzavanje",
    productsKicker: "Put proizvoda",
    productsTitle: "Proizvodi ostaju prvi put konverzije.",
    products: "KNX uredjaji|Smart paneli|Senzori|CCTV|Energetska brojila|Servis paketi",
    openMarket: "Otvori",
    marketSwitchKicker: "Odvojeno, povezano",
    marketSwitchTitle: "Zvanicni sajt i Market su dva mobilna interfejsa.",
    marketSwitchText: "Official objasnjava viziju. Market prodaje, trazi, lista polovnu opremu i prima sire AI zahteve. Oba pisu u AinerWise Core.",
    generalRequest: "Opsti AI zahtev",
  },
  pl: {
    mobileSite: "mobilna strona",
    signIn: "Zaloguj",
    register: "Rejestracja",
    market: "Market",
    navBrain: "AI Brain",
    navSolutions: "Rozwiązania",
    navProducts: "Produkty",
    navMarket: "Market",
    title: "AI smart building, produkty i dostawa w jednym AinerWise.",
    subtitle: "Mobilna strona oficjalna wyjaśnia AI brain i KNX + hardware. Market jest osobno dla produktów, używanych opcji i ofert dostawców.",
    heroBadges: "KNX + AI|Smart Building|Produkty + dostawa",
    primaryCta: "Otwórz Market",
    secondaryCta: "Zapytanie AI",
    brainKicker: "AinerWise AI Layer",
    brainTitle: "AI brain dla prawdziwych budynków",
    brainText: "Łączy pokoje, urządzenia, energię, bezpieczeństwo, serwis i zakupy z jednego prostego zapytania.",
    solutionKicker: "Rozwiązania",
    solutionTitle: "Najpierw wille, małe hotele i realne modernizacje.",
    solutionText: "Oficjalna ścieżka ma mniej kategorii i lepsze pytania, żeby BOQ i RFQ były stabilniejsze.",
    solutions: "Villa Smart Home|Oświetlenie, rolety, bezpieczeństwo i komfort|Small Hotel Upgrade|Pokoje, energia, CCTV, Wi-Fi i serwis|Energy + Security|Solar, liczniki, dostęp, monitoring i utrzymanie",
    productsKicker: "Produkty",
    productsTitle: "Produkty nadal są pierwszą ścieżką konwersji.",
    products: "KNX devices|Smart panels|Sensors|CCTV|Energy meters|Service packages",
    openMarket: "Otwórz",
    marketSwitchKicker: "Oddzielnie, ale razem",
    marketSwitchTitle: "Official i Market to dwa mobilne widoki.",
    marketSwitchText: "Official buduje zaufanie. Market sprzedaje, szuka, publikuje używane zasoby i obsługuje szerokie zapytania AI. Oba zapisują dane do AinerWise Core.",
    generalRequest: "Ogólne zapytanie AI",
  },
};

const homeCopy = computed(() => copyByLocale[locale.value] || copyByLocale.en);
const marketPath = computed(() => localizedPath("/marketplace"));
const marketRequestPath = computed(() => localizedPath("/buyer/post-request?mode=market"));
const smartBuildingRequestPath = computed(() => localizedPath("/buyer/post-request?mode=smart_building"));
const heroBadges = computed(() => splitCopy(homeCopy.value.heroBadges));
const productCards = computed(() => splitCopy(homeCopy.value.products));
const solutionCards = computed(() => splitCopy(homeCopy.value.solutions).reduce<Array<{ kicker: string; title: string; text: string }>>((items, value, index, list) => {
  if (index % 2 !== 0) return items;
  items.push({
    kicker: index === 0 ? "L2-L5" : index === 2 ? "L2-L4" : "L3-L5",
    title: value,
    text: list[index + 1] || "",
  });
  return items;
}, []));
const brainNodes = computed(() => [
  { label: homeCopy.value.navProducts, className: "left-3 top-8" },
  { label: "Rooms", className: "right-4 top-12" },
  { label: "Energy", className: "left-1 bottom-28" },
  { label: "CCTV", className: "right-2 bottom-28" },
]);

function splitCopy(value: string) {
  return String(value || "").split("|").map((item) => item.trim()).filter(Boolean);
}

function localizedPath(path: string) {
  const prefix = getLocalePrefixFromPath(route.path) || (import.meta.client ? localStorage.getItem("h5_locale_prefix") || "" : "");
  return prefix ? withLocalePrefix(path, prefix) : path;
}
</script>

<style scoped>
.scrollbar-hide::-webkit-scrollbar { display: none; }
.scrollbar-hide { -ms-overflow-style: none; scrollbar-width: none; }
</style>
