import type { Config } from "tailwindcss";

export default <Partial<Config>>{
  content: [
    "./components/**/*.{js,vue,ts}",
    "./composables/**/*.{js,ts}",
    "./layouts/**/*.vue",
    "./pages/**/*.vue",
    "./plugins/**/*.{js,ts}",
    "./stores/**/*.{js,ts}",
    "./app.vue",
    "./error.vue",
  ],
  theme: {
    extend: {
      colors: {
        // 2Hands identity: warm teal — deliberately distinct from
        // AISLOS Market's indigo so the two storefronts never look alike.
        brand: {
          50: "#eefbf7",
          100: "#d5f5eb",
          200: "#aeead8",
          300: "#79d9c0",
          400: "#43c0a3",
          500: "#1fa588",
          600: "#12856f",
          700: "#116b5b",
          800: "#12554a",
          900: "#12473f",
          950: "#042925",
        },
      },
    },
  },
};
