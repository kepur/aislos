import autoprefixer from "autoprefixer";
import { fileURLToPath } from "node:url";

const tailwindColorsAlias = fileURLToPath(new URL("./tailwind-colors.mjs", import.meta.url));

const tailwindTheme = {
  extend: {
    colors: {
      primary: {
        50: "#eef2ff",
        100: "#e0e7ff",
        200: "#c7d2fe",
        300: "#a5b4fc",
        400: "#818cf8",
        500: "#6366f1",
        600: "#4f46e5",
        700: "#4338ca",
        800: "#3730a3",
        900: "#312e81",
        950: "#1e1b4b",
      },
      success: "#16a34a",
      warning: "#d97706",
      danger: "#dc2626",
    },
    spacing: {
      "safe-bottom": "var(--safe-area-bottom)",
    },
    fontFamily: {
      sans: ["Inter", "-apple-system", "BlinkMacSystemFont", "Segoe UI", "sans-serif"],
    },
    borderRadius: {
      "2xl": "1rem",
      "3xl": "1.5rem",
    },
    boxShadow: {
      card: "0 1px 3px 0 rgb(0 0 0 / 0.1), 0 1px 2px -1px rgb(0 0 0 / 0.1)",
      "card-hover": "0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1)",
      bottom: "0 -2px 8px 0 rgb(0 0 0 / 0.08)",
    },
  },
};

export default defineNuxtConfig({
  compatibilityDate: "2024-11-01",
  devtools: { enabled: false },

  app: {
    pageTransition: false,
    layoutTransition: false
  },

  appConfig: {
    ui: {
      primary: "indigo",
      gray: "slate",
      colors: ["primary", "indigo", "slate", "green", "red", "yellow", "blue", "purple", "gray"],
    },
  },

  alias: {
    "#tailwind-config/theme/colors": tailwindColorsAlias,
  },

  devServer: {
    port: 3399,
  },

  modules: [
    "@pinia/nuxt",
    "@nuxt/ui",
    "@vueuse/nuxt",
  ],

  ui: {
    disableGlobalStyles: true,
  },

  css: ["~/assets/css/compiled.css", "~/assets/css/nuxt-ui-fallback.css"],

  tailwindcss: {
    cssPath: false,
    configPath: "tailwind.config.cjs",
    config: {
      content: [
        "./app.vue",
        "./components/**/*.{vue,js,ts}",
        "./layouts/**/*.vue",
        "./pages/**/*.vue",
        "./plugins/**/*.{js,ts}",
        "./stores/**/*.{js,ts}",
        "./node_modules/@nuxt/ui/dist/runtime/**/*.{vue,js,mjs}",
      ],
      safelist: [
        "relative",
        "absolute",
        "inset-y-0",
        "start-0",
        "end-0",
        "flex",
        "items-center",
        "pointer-events-none",
        "ps-7",
        "ps-8",
        "ps-9",
        "ps-10",
        "ps-11",
        "ps-12",
        "pe-7",
        "pe-8",
        "pe-9",
        "pe-10",
        "pe-11",
        "pe-12",
        "px-2",
        "px-2.5",
        "px-3",
        "px-3.5",
        "h-4",
        "h-5",
        "h-6",
        "w-4",
        "w-5",
        "w-6",
        "form-input",
        "form-select",
        "form-checkbox",
      ],
      theme: tailwindTheme,
    },
    disableHMR: true,
    exposeConfig: false,
    viewer: false,
  },

  runtimeConfig: {
    public: {
      apiBase: process.env.NUXT_PUBLIC_API_BASE || "http://localhost:8088",
      appName: process.env.NUXT_PUBLIC_APP_NAME || "ProcurePing",
      appDomain: process.env.NUXT_PUBLIC_APP_DOMAIN || "procureping.local",
    },
  },

  vite: {
    css: {
      postcss: {
        plugins: [autoprefixer()],
      },
    },
  },

  typescript: {
    strict: true,
  },
});
