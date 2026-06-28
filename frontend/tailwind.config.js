/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        bgDark: "var(--bg-main)",
        bgPanel: "var(--bg-card)",
        borderGlow: "var(--border-glow)",
        textMain: "var(--text-main)",
        textMuted: "var(--text-muted)",
        borderDim: "var(--border-dim)",
        riskLow: "#10b981",      // Green
        riskMod: "#f59e0b",      // Amber
        riskHigh: "#f97316",     // Orange
        riskExtreme: "#ef4444"   // Red
      },
      fontFamily: {
        sans: ['var(--font-sans)', 'sans-serif'],
      },
      boxShadow: {
        'glass': 'var(--shadow-base)',
        'neon-blue': '0 0 15px rgba(59, 130, 246, 0.35)',
        'neon-red': '0 0 15px rgba(239, 68, 68, 0.35)'
      }
    },
  },
  plugins: [],
}
