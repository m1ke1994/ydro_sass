/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{vue,js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        brand: {
          50: '#f5f3ff',
          100: '#ede9fe',
          200: '#ddd6fe',
          300: '#c4b5fd',
          400: '#a78bfa',
          500: '#8b5cf6',
          600: '#7c3aed',
          700: '#6d28d9',
          800: '#5b21b6',
          900: '#4c1d95',
        },
      },
      boxShadow: {
        soft: '0 12px 32px rgba(15, 23, 42, 0.08)',
      },
      backgroundImage: {
        'sidebar-gradient': 'linear-gradient(180deg, #0f172a 0%, #0b1120 35%, #111827 100%)',
      },
    },
  },
  plugins: [],
}
