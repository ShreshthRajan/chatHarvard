/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./src/**/*.{js,jsx,ts,tsx}"],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        // Harvard colors - updated to be more elegant
        'harvard-crimson': '#A51C30',  // Keep original harvard crimson
        'harvard-dark': '#8A1A29',
        'harvard-light': '#F7E7E9',
        
        // Chat colors - more professional and elegant
        'chat-user': '#F8F9FA',
        'chat-assistant': '#F5F5F6', 
        'chat-border': '#E5E7EB',
        
        // Dark mode elegant theme - more like Claude.ai with grey-brown tones
        'dark': {
          '50': '#1E1E20',     // Background darkest
          '100': '#242426',    // Background dark
          '200': '#2A2A2C',    // Card background
          '300': '#323235',    // Input background
          '400': '#45454A',    // Border colors
          '500': '#6E6E76',    // Muted text
          '600': '#9A9AA5',    // Secondary text
          '700': '#CDCDD4',    // Primary text
          '800': '#E8E8ED',    // Headings
          '900': '#F6F6F8',    // Emphasized text
        },
        
        // Accent colors - updated to be more elegant
        'accent': {
          'primary': '#8B6C5C',      // Elegant brown
          'secondary': '#D2BDB0',    // Light brown
          'tertiary': '#614C3F',     // Deep brown
          'success': '#2B9074',      // Green
          'warning': '#D4A970',      // Amber
          'info': '#5E8AA9',         // Blue
          'error': '#A87979',        // Muted red
        },
        
        'gray': {
          50: '#F9FAFB',
          100: '#F3F4F6',
          200: '#E5E7EB',
          300: '#D1D5DB',
          400: '#9CA3AF',
          500: '#6B7280',
          600: '#4B5563',
          700: '#374151',
          800: '#1F2937',
          900: '#111827',
        },
      },
      boxShadow: {
        'card': '0 8px 12px -3px rgba(0, 0, 0, 0.05), 0 4px 6px -2px rgba(0, 0, 0, 0.025)',
        'card-dark': '0 8px 12px rgba(0, 0, 0, 0.12)',
        'hover': '0 16px 20px -5px rgba(0, 0, 0, 0.08), 0 8px 10px -5px rgba(0, 0, 0, 0.03)',
        'hover-dark': '0 8px 12px rgba(0, 0, 0, 0.15)',
        'dropdown': '0 4px 6px -1px rgba(0, 0, 0, 0.08), 0 2px 4px -1px rgba(0, 0, 0, 0.05)',
        'dropdown-dark': '0 4px 8px rgba(0, 0, 0, 0.15)',
        'glow': '0 0 15px rgba(139, 108, 92, 0.15)',
        'glow-dark': '0 0 15px rgba(139, 108, 92, 0.08)',
        'subtle': '0 2px 5px rgba(0,0,0,0.04)',
        'subtle-dark': '0 2px 5px rgba(0,0,0,0.08)',
      },
      borderRadius: {
        'xl': '0.75rem',
        '2xl': '1rem',
        '3xl': '1.5rem',
        '4xl': '2rem',
      },
      animation: {
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'shimmer': 'shimmer 2s infinite',
        'fade-in': 'fadeIn 0.3s ease-in-out',
        'slide-up': 'slideUp 0.4s ease-out',
        'slide-in-right': 'slideInRight 0.4s ease-out',
      },
      typography: {
        DEFAULT: {
          css: {
            color: '#374151',
            a: {
              color: '#8B6C5C',
              '&:hover': {
                color: '#614C3F',
              },
            },
            h1: {
              color: '#1F2937',
            },
            h2: {
              color: '#1F2937',
            },
            h3: {
              color: '#1F2937',
            },
            strong: {
              color: '#1F2937',
            },
            code: {
              color: '#1F2937',
              backgroundColor: '#F3F4F6',
              paddingLeft: '0.25rem',
              paddingRight: '0.25rem',
              paddingTop: '0.125rem',
              paddingBottom: '0.125rem',
              borderRadius: '0.25rem',
            },
            pre: {
              backgroundColor: '#F3F4F6',
              color: '#1F2937',
            },
          },
        },
        dark: {
          css: {
            color: '#CDCDD4',
            a: {
              color: '#D2BDB0',
              '&:hover': {
                color: '#8B6C5C',
              },
            },
            h1: {
              color: '#E8E8ED',
            },
            h2: {
              color: '#E8E8ED',
            },
            h3: {
              color: '#E8E8ED',
            },
            strong: {
              color: '#E8E8ED',
            },
            code: {
              color: '#E8E8ED',
              backgroundColor: '#323235',
            },
            pre: {
              backgroundColor: '#323235',
              color: '#E8E8ED',
            },
          },
        },
      },
      transitionProperty: {
        'height': 'height',
        'spacing': 'margin, padding',
        'width': 'width',
        'colors': 'color, background-color, border-color, text-decoration-color, fill, stroke',
      },
      keyframes: {
        shimmer: {
          '0%': { backgroundPosition: '-200% 0' },
          '100%': { backgroundPosition: '200% 0' },
        },
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideUp: {
          '0%': { transform: 'translateY(10px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },
        slideInRight: {
          '0%': { transform: 'translateX(10px)', opacity: '0' },
          '100%': { transform: 'translateX(0)', opacity: '1' },
        },
      },
      fontFamily: {
        sans: [
          'Inter',
          'ui-sans-serif',
          'system-ui',
          '-apple-system',
          'BlinkMacSystemFont',
          'Segoe UI',
          'Roboto',
          'Helvetica Neue',
          'Arial',
          'sans-serif',
        ],
      },
    },
  },
  plugins: [
    require('@tailwindcss/forms'),
  ],
}