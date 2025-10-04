module.exports = {
  content: ["./pages/*.{html,js}", "./index.html", "./js/*.js"],
  theme: {
    extend: {
      colors: {
        primary: {
          DEFAULT: "#4cafef", // blue-400
          hover: "#38bdf8", // blue-400 hover
        },
        secondary: {
          DEFAULT: "#2d5aa0", // blue-700
          hover: "#1e40af", // blue-800
        },
        accent: {
          DEFAULT: "#00d4aa", // teal-400
          hover: "#14b8a6", // teal-500
        },
        background: "#1e1e1e", // gray-900
        surface: {
          DEFAULT: "#2a2a2a", // gray-800
          hover: "#374151", // gray-700
        },
        text: {
          primary: "#d0d0d0", // gray-300
          secondary: "#a0a0a0", // gray-400
          muted: "#6b7280", // gray-500
        },
        success: {
          DEFAULT: "#00d4aa", // teal-400
          bg: "#134e4a", // teal-900
        },
        warning: {
          DEFAULT: "#ffa726", // orange-400
          bg: "#451a03", // orange-950
        },
        error: {
          DEFAULT: "#ef5350", // red-400
          bg: "#450a0a", // red-950
        },
        border: {
          DEFAULT: "#404040", // gray-700
          light: "#525252", // gray-600
          focus: "#4cafef", // blue-400
        },
      },
      fontFamily: {
        sans: ['Inter', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
      fontSize: {
        'xs': '0.75rem',
        'sm': '0.875rem',
        'base': '1rem',
        'lg': '1.125rem',
        'xl': '1.25rem',
        '2xl': '1.5rem',
        '3xl': '1.875rem',
      },
      fontWeight: {
        normal: '400',
        medium: '500',
        semibold: '600',
      },
      borderRadius: {
        'message': '8px',
        'input': '6px',
      },
      boxShadow: {
        'default': '0 2px 8px rgba(0, 0, 0, 0.3)',
        'hover': '0 4px 12px rgba(0, 0, 0, 0.4)',
        'focus': '0 0 0 3px rgba(76, 175, 239, 0.2)',
      },
      animation: {
        'pulse-slow': 'pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'fade-in': 'fadeIn 150ms ease-out',
        'slide-up': 'slideUp 200ms ease-out',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideUp: {
          '0%': { transform: 'translateY(10px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },
      },
      transitionDuration: {
        '150': '150ms',
        '200': '200ms',
        '300': '300ms',
      },
      transitionTimingFunction: {
        'ease-out-custom': 'cubic-bezier(0.25, 0.46, 0.45, 0.94)',
      },
      spacing: {
        '18': '4.5rem',
        '88': '22rem',
      },
    },
  },
  plugins: [],
}