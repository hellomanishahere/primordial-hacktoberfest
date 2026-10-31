/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        charcoal: {
          50: '#f6f6f7',
          100: '#e2e3e5',
          200: '#c4c6ca',
          300: '#9fa2a8',
          400: '#7b7f87',
          500: '#61656d',
          600: '#4d5057',
          700: '#3f4147',
          800: '#35373b',
          900: '#2d2f33',
          950: '#1a1b1e',
        },
        accent: {
          DEFAULT: '#3b82f6',
          hover: '#2563eb',
          light: '#60a5fa',
          dark: '#1d4ed8',
        },
      },
    },
  },
  plugins: [],
};

