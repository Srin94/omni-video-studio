/** @type {import('tailwindcss').Config} */
export default {
  darkMode: "class",
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      fontFamily: {
        sans: ["'Space Grotesk'", "system-ui", "sans-serif"],
        mono: ["'IBM Plex Mono'", "monospace"],
      },
      colors: {
        ink: {
          950: "#070A12",
          900: "#0B0F1A",
          850: "#0F1524",
          800: "#141B2E",
          700: "#1E2740",
          600: "#2A3657",
        },
        brand: {
          DEFAULT: "#38BDF8",
          glow: "#22D3EE",
        },
      },
      boxShadow: {
        glow: "0 0 32px rgba(56,189,248,0.25)",
      },
    },
  },
  plugins: [],
};
