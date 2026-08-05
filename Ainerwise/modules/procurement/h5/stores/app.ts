import { defineStore } from "pinia";
import {
  FALLBACK_PAYMENT_POLICIES,
  currencyOptionLabel,
  normalizeCurrencyCode,
  normalizePaymentPolicy,
} from "~/utils/currencyPolicy";

type SelectOption = {
  code: string;
  label: string;
};

type AppState = {
  currency: string;
  regionCountry: string;
  enabledCurrencies: string[];
  marketLocalizationConfig: Record<string, any> | null;
  paymentRegionConfig: Record<string, any> | null;
};

function readCookie(name: string) {
  if (!import.meta.client) return "";
  const found = document.cookie
    .split(";")
    .map((item) => item.trim())
    .find((item) => item.startsWith(`${name}=`));
  return found ? decodeURIComponent(found.slice(name.length + 1)) : "";
}

export const useAppStore = defineStore("app", {
  state: (): AppState => ({
    currency: "EUR",
    regionCountry: "RS",
    enabledCurrencies: ["EUR", "RSD", "PLN", "BAM", "USD"],
    marketLocalizationConfig: null,
    paymentRegionConfig: null,
  }),

  getters: {
    allCurrencyOptions: (): SelectOption[] =>
      [
        "USD",
        "PHP",
        "EUR",
        "RSD",
        "PLN",
        "BAM",
        "RON",
        "JPY",
        "CNY",
        "SGD",
        "HKD",
        "AUD",
        "GBP",
        "CAD",
        "KRW",
        "AED",
        "INR",
        "THB",
        "USDT",
      ].map((code) => ({ code, label: currencyOptionLabel(code) })),

    regionOptions(state): SelectOption[] {
      const configured = (state.marketLocalizationConfig?.supported_regions || [])
        .map((region: any) => ({
          code: String(region.code || "").toUpperCase().slice(0, 2),
          label: String(region.name || region.label || region.code || "").trim(),
        }))
        .filter((region: SelectOption) => region.code && region.label);
      if (configured.length) return configured;
      return Object.values(FALLBACK_PAYMENT_POLICIES).map((policy) => ({
        code: policy.country_code,
        label: policy.country_name,
      }));
    },

    paymentPolicy(state) {
      return normalizePaymentPolicy(state.paymentRegionConfig, state.regionCountry);
    },

    currencyOptions(state): SelectOption[] {
      const policy = normalizePaymentPolicy(state.paymentRegionConfig, state.regionCountry);
      const enabled = new Set(
        policy.settlement_currencies?.length
          ? policy.settlement_currencies
          : state.enabledCurrencies?.length
            ? state.enabledCurrencies
            : [policy.default_settlement_currency]
      );
      return this.allCurrencyOptions.filter((option: SelectOption) => enabled.has(option.code));
    },

    localCurrency(state): string {
      return normalizePaymentPolicy(state.paymentRegionConfig, state.regionCountry).local_currency;
    },

    defaultSettlementCurrency(state): string {
      return normalizePaymentPolicy(state.paymentRegionConfig, state.regionCountry).default_settlement_currency;
    },
  },

  actions: {
    hydrate() {
      if (!import.meta.client) return;
      this.regionCountry = String(
        localStorage.getItem("pp_region_country") ||
          readCookie("pp_region_country") ||
          this.regionCountry ||
          "RS"
      )
        .toUpperCase()
        .slice(0, 2);
      this.currency = normalizeCurrencyCode(
        localStorage.getItem("pp_currency") || readCookie("pp_currency") || this.currency,
        this.defaultSettlementCurrency
      );
    },

    persist() {
      if (!import.meta.client) return;
      localStorage.setItem("pp_currency", this.currency);
      localStorage.setItem("pp_region_country", this.regionCountry);
      const maxAge = 60 * 60 * 24 * 365;
      document.cookie = `pp_currency=${encodeURIComponent(this.currency)}; Path=/; Max-Age=${maxAge}; SameSite=Lax`;
      document.cookie = `pp_region_country=${encodeURIComponent(this.regionCountry)}; Path=/; Max-Age=${maxAge}; SameSite=Lax`;
    },

    setCurrency(curr: string) {
      const normalized = normalizeCurrencyCode(curr, this.defaultSettlementCurrency);
      if (this.currencyOptions.some((option: SelectOption) => option.code === normalized)) {
        this.currency = normalized;
        this.persist();
      }
    },

    async setRegionCountry(country: string) {
      const normalized = String(country || this.regionCountry || "RS").toUpperCase().slice(0, 2);
      this.regionCountry = normalized;
      this.persist();
      await this.fetchPaymentRegionConfig(normalized);
    },

    async fetchPaymentRegionConfig(country = this.regionCountry || "RS") {
      this.regionCountry = String(country || "RS").toUpperCase().slice(0, 2);
      try {
        const config = useRuntimeConfig();
        const data = await $fetch<Record<string, any>>(`${config.public.apiBase}/payments/region-config`, {
          query: { country: this.regionCountry },
        });
        const policy = normalizePaymentPolicy(data, this.regionCountry);
        this.paymentRegionConfig = policy;
        this.enabledCurrencies = policy.settlement_currencies?.length
          ? policy.settlement_currencies
          : policy.enabled_currencies;
        if (!this.enabledCurrencies.includes(this.currency)) {
          this.currency = this.enabledCurrencies.includes(policy.default_settlement_currency)
            ? policy.default_settlement_currency
            : this.enabledCurrencies[0];
        }
      } catch {
        const policy = normalizePaymentPolicy(null, this.regionCountry);
        this.paymentRegionConfig = policy;
        this.enabledCurrencies = policy.settlement_currencies || policy.enabled_currencies;
        if (!this.enabledCurrencies.includes(this.currency)) {
          this.currency = this.enabledCurrencies.includes(policy.default_settlement_currency)
            ? policy.default_settlement_currency
            : this.enabledCurrencies[0];
        }
      }
      this.persist();
    },

    async fetchMarketLocalizationConfig() {
      try {
        const config = useRuntimeConfig();
        this.marketLocalizationConfig = await $fetch<Record<string, any>>(
          `${config.public.apiBase}/localization/config`
        );
      } catch {
        this.marketLocalizationConfig = null;
      }
    },
  },
});
