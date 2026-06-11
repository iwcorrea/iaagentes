/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        brand: {
          dark: '#0f172a',
          accent: '#3b82f6',
          surface: '#1e293b',
          border: '#334155'
        }
      }
    },
  },
  plugins: [],
}