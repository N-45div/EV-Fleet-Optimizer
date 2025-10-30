/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        background: "#060b1a",
        card: "#0f172a",
        accent: "#5f43f1",
        accentSecondary: "#3d8bd3",
        muted: "#94a3b8",
      },
      boxShadow: {
        glow: "0 10px 50px rgba(95,67,241,0.35)",
      },
    },
  },
  plugins: [],
};
