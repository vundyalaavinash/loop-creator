/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        base: "#000000",
        surface: "#0A0A0A",
        elevated: "#111111",
        "accent-teal": "#01C7B1",
        "accent-purple": "#9B6DFF",
        primary: "#FFFFFF",
        muted: "#6B7280",
        "border-color": "#1E1E1E",
      },
      fontFamily: {
        mono: ["JetBrains Mono", "monospace"],
        sans: ["Inter", "sans-serif"],
      },
    },
  },
  plugins: [],
};
