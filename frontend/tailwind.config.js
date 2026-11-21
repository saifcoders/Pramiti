/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        ayurveda: {
          50: '#f6f7f2',
          100: '#eaede0',
          200: '#d6dcc5',
          300: '#bcc6a3',
          400: '#9eac7f',
          500: '#7e905f',
          600: '#637349',
          700: '#4e5a3a',
          800: '#404931',
          900: '#363d2b',
        },
        charaka: {
          light: '#fdf6e7',
          DEFAULT: '#d97706',
          dark: '#92400e',
        },
        sushruta: {
          light: '#eff6ff',
          DEFAULT: '#2563eb',
          dark: '#1e40af',
        },
        ashtanga: {
          light: '#f0fdf4',
          DEFAULT: '#16a34a',
          dark: '#166534',
        },
      },
    },
  },
  plugins: [],
}

