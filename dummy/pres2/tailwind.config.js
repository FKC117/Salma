module.exports = {
  content: ["./pages/*.{html,js}", "./index.html", "./js/*.js"],
  theme: {
    extend: {
      colors: {
        // Primary Colors
        primary: {
          DEFAULT: "#2563EB", // blue-600
          50: "#EFF6FF", // blue-50
          100: "#DBEAFE", // blue-100
          500: "#3B82F6", // blue-500
          600: "#2563EB", // blue-600
          700: "#1D4ED8", // blue-700
        },
        // Secondary Colors
        secondary: {
          DEFAULT: "#64748B", // slate-500
          400: "#94A3B8", // slate-400
          500: "#64748B", // slate-500
          600: "#475569", // slate-600
        },
        // Accent Colors
        accent: {
          DEFAULT: "#10B981", // emerald-500
          400: "#34D399", // emerald-400
          500: "#10B981", // emerald-500
          600: "#059669", // emerald-600
        },
        // Background Colors
        background: {
          DEFAULT: "#0F172A", // slate-900
          800: "#1E293B", // slate-800
          900: "#0F172A", // slate-900
        },
        // Surface Colors
        surface: {
          DEFAULT: "#1E293B", // slate-800
          700: "#334155", // slate-700
          800: "#1E293B", // slate-800
        },
        // Text Colors
        'text-primary': "#F8FAFC", // slate-50
        'text-secondary': "#CBD5E1", // slate-300
        'text-muted': "#94A3B8", // slate-400
        // Status Colors
        success: {
          DEFAULT: "#22C55E", // green-500
          400: "#4ADE80", // green-400
          500: "#22C55E", // green-500
          600: "#16A34A", // green-600
        },
        warning: {
          DEFAULT: "#F59E0B", // amber-500
          400: "#FBBF24", // amber-400
          500: "#F59E0B", // amber-500
          600: "#D97706", // amber-600
        },
        error: {
          DEFAULT: "#EF4444", // red-500
          400: "#F87171", // red-400
          500: "#EF4444", // red-500
          600: "#DC2626", // red-600
        },
        // Border Colors
        border: {
          DEFAULT: "#334155", // slate-700
          light: "#475569", // slate-600
        },
      },
      fontFamily: {
        sans: ['Inter', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
      fontSize: {
        'clamp-sm': 'clamp(0.875rem, 2vw, 1rem)',
        'clamp-base': 'clamp(1rem, 2.5vw, 1.125rem)',
        'clamp-lg': 'clamp(1.125rem, 3vw, 1.25rem)',
        'clamp-xl': 'clamp(1.25rem, 3.5vw, 1.5rem)',
      },
      animation: {
        'loading-shimmer': 'loading-shimmer 1.5s infinite',
      },
      keyframes: {
        'loading-shimmer': {
          '0%': { 'background-position': '-200% 0' },
          '100%': { 'background-position': '200% 0' },
        },
      },
      backdropBlur: {
        xs: '2px',
      },
      boxShadow: {
        'medical': '0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06)',
        'medical-lg': '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)',
      },
      transitionTimingFunction: {
        'medical': 'cubic-bezier(0.4, 0, 0.2, 1)',
      },
      transitionDuration: {
        '150': '150ms',
        '200': '200ms',
        '300': '300ms',
      },
    },
  },
  plugins: [],
}