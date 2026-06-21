/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        base: "#1C1C1C",
        surface: "#242424",
        elevated: "#2E2E2E",
        "accent-teal": "#01C7B1",
        "accent-purple": "#9B6DFF",
        primary: "#F0F0F0",
        muted: "#8A8A8A",
        "border-color": "#383838",
      },
      fontFamily: {
        mono: ["JetBrains Mono", "monospace"],
        sans: ["Inter", "sans-serif"],
      },
    },
  },
  plugins: [],
};
