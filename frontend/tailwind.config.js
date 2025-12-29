/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{vue,js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        ios: {
          bg: "#000000",
          card: "#1C1C1E",
          card2: "#2C2C2E",
          blue: "#0A84FF",
          gray: "#8E8E93",
          red: "#FF453A",
          green: "#30D158",
          orange: "#FF9F0A",
          separator: "#38383A",
        },
      },
      fontFamily: {
        ailab: [
          "Inter",
          "Noto Sans SC",
          "system-ui",
          "-apple-system",
          "BlinkMacSystemFont",
          "Segoe UI",
          "sans-serif",
        ],
        display: [
          "Inter",
          "Noto Sans SC",
          "system-ui",
          "-apple-system",
          "BlinkMacSystemFont",
          "Segoe UI",
          "sans-serif",
        ],
      },
      borderWidth: {
        3: "3px",
      },
    },
  },
  plugins: [],
}
