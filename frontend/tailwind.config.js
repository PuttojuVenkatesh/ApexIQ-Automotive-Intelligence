/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx,ts,tsx}'],
  theme: {
    extend: {
      colors: {
        bg: '#0b0e14',
        surface: '#13161f',
        card: '#161b2a',
        border: '#1e2435',
        amber: {
          DEFAULT: '#f59e0b',
          hover: '#d97706',
          light: '#fbbf24',
        },
        orange: {
          label: '#f97316',
        },
        green: {
          rag: '#10b981',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'Fira Code', 'monospace'],
      },
      clipPath: {
        chamfer: 'polygon(8px 0%, 100% 0%, 100% calc(100% - 8px), calc(100% - 8px) 100%, 0% 100%, 0% 8px)',
      },
    },
  },
  plugins: [],
};
