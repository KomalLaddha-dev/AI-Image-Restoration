import type { Config } from 'tailwindcss';

const config: Config = {
  darkMode: 'class',
  content: [
    './index.html',
    './src/**/*.{js,ts,jsx,tsx}',
  ],
  theme: {
    extend: {
      colors: {
        canvas: {
          DEFAULT: '#fbf9f5', // Warm gallery off-white (light mode)
          dark: '#141416',    // Soft charcoal (dark mode, not pure black)
        },
        surface: {
          DEFAULT: '#ffffff',
          dark: '#1c1c1f',
          subtle: '#f4f0e8',
          'subtle-dark': '#242428',
          hover: '#ece6d8',
          'hover-dark': '#2c2c32',
        },
        'accent-sepia': {
          DEFAULT: '#c49746',
          hover: '#b08435',
          light: '#dfb76c',
          faint: 'rgba(196, 151, 70, 0.12)',
        },
        'accent-green': {
          DEFAULT: '#2e6948',
          hover: '#245439',
          light: '#3f8d62',
          faint: 'rgba(46, 105, 72, 0.12)',
        },
        'accent-brown': {
          DEFAULT: '#7c4a27',
          hover: '#663b1d',
          light: '#9e6136',
          faint: 'rgba(124, 74, 39, 0.12)',
        },
        ink: {
          DEFAULT: '#18181b', // High-contrast neutral text
          muted: '#666670',
          faint: '#9ca3af',
          dark: '#f4f4f6',
          'muted-dark': '#a1a1aa',
          'faint-dark': '#71717a',
        },
        border: {
          light: 'rgba(0, 0, 0, 0.08)',
          'light-subtle': 'rgba(0, 0, 0, 0.04)',
          dark: 'rgba(255, 255, 255, 0.10)',
          'dark-subtle': 'rgba(255, 255, 255, 0.05)',
        },
      },
      fontFamily: {
        heading: ['"Source Serif 4"', 'Lora', 'Georgia', 'serif'],
        body: ['Inter', 'ui-sans-serif', 'system-ui', 'sans-serif'],
      },
      spacing: {
        '18': '4.5rem',
        '22': '5.5rem',
        '26': '6.5rem',
        '30': '7.5rem',
        '34': '8.5rem',
        '38': '9.5rem',
      },
      animation: {
        'ken-burns': 'ken-burns 24s ease-in-out infinite alternate',
      },
      keyframes: {
        'ken-burns': {
          '0%': { transform: 'scale(1.0) translate(0, 0)' },
          '50%': { transform: 'scale(1.06) translate(-1%, -0.8%)' },
          '100%': { transform: 'scale(1.0) translate(0, 0)' },
        },
      },
    },
  },
  plugins: [],
};

export default config;
