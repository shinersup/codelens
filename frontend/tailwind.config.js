/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        surface: {
          0: '#0a0a0f',
          1: '#0f1017',
          2: '#14151f',
          3: '#1a1b28',
          4: '#21222f',
          5: '#282938',
        },
        accent: {
          cyan: '#00e5ff',
          green: '#39ff85',
          amber: '#ffb300',
          red: '#ff4d6a',
          purple: '#b388ff',
          blue: '#448aff',
        },
        txt: {
          primary: '#e8eaed',
          secondary: '#9aa0a6',
          muted: '#5f6368',
        },
      },
      fontFamily: {
        display: ['"JetBrains Mono"', 'monospace'],
        body: ['"IBM Plex Sans"', 'sans-serif'],
        mono: ['"JetBrains Mono"', '"Fira Code"', 'monospace'],
      },
      boxShadow: {
        glow: '0 0 20px rgba(0, 229, 255, 0.15)',
        'glow-green': '0 0 20px rgba(57, 255, 133, 0.15)',
        'glow-red': '0 0 20px rgba(255, 77, 106, 0.15)',
        'glow-amber': '0 0 20px rgba(255, 179, 0, 0.15)',
      },
      animation: {
        'fade-in': 'fadeIn 0.5s ease-out',
        'slide-up': 'slideUp 0.4s ease-out',
        'pulse-slow': 'pulse 3s ease-in-out infinite',
        'scan': 'scan 2s ease-in-out infinite',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideUp: {
          '0%': { opacity: '0', transform: 'translateY(12px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        scan: {
          '0%, 100%': { opacity: '0.4' },
          '50%': { opacity: '1' },
        },
      },
    },
  },
  plugins: [],
};
