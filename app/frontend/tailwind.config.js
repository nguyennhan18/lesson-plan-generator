/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: '#141414',
        'on-primary': '#ffffff',
        ink: {
          DEFAULT: '#141414',
          soft: '#262626'
        },
        canvas: {
          DEFAULT: '#ffffff',
          soft: '#f3f3f3'
        },
        field: '#f0f0f0',
        hairline: {
          DEFAULT: '#e0e0e0',
          soft: '#f0f0f0'
        },
        accent: {
          DEFAULT: '#0066ff'
        },
        'text-muted': '#707070',
        'text-faint': '#adadad',
        // Preserve cyber mapping for any legacy classes while defaulting to monochrome
        cyber: {
          dark: '#ffffff',
          card: '#ffffff',
          border: '#e0e0e0',
          cyan: '#0066ff',
          indigo: '#141414',
          emerald: '#10b981',
          amber: '#f59e0b',
          rose: '#ef4444'
        }
      },
      borderRadius: {
        'sm': '16px',
        'md': '24px',
        'full': '9999px',
        'squircle': '30%'
      },
      fontFamily: {
        sans: ['Inter', 'Saans', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'Roboto', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace']
      }
    },
  },
  plugins: [],
}
