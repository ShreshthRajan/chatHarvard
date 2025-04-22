/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./src/**/*.{js,jsx,ts,tsx}"],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        // Harvard colors - refined for elegance with warmer, more sophisticated tone
        'harvard-crimson': '#A51C30',  // Original harvard crimson (for reference)
        'harvard-dark': '#8A1729',
        'harvard-light': '#F7E7E9',
        
        // Chat colors - refined for elegance
        'chat-user': '#FFFFFF',
        'chat-assistant': '#F9F9FB', 
        'chat-border': '#E5E7EB',
        
        // Dark mode elegant Claude-inspired theme with warm undertones
        'dark': {
          '50': '#191919',     // Background darkest
          '100': '#1A1A1D',    // Background dark
          '200': '#252529',    // Card background
          '300': '#2D2D31',    // Input background
          '400': '#3F3F43',    // Border colors
          '500': '#64646B',    // Muted text
          '600': '#9798A1',    // Secondary text
          '700': '#CDCDD4',    // Primary text
          '800': '#E6E6EB',    // Headings
          '900': '#F5F5F8',    // Emphasized text
        },
        
        // Accent colors - new more sophisticated palette
        'accent': {
          'primary': '#9A4E5F',      // Softer, more sophisticated crimson (was #B33245)
          'secondary': '#C27F8C',    // Light muted crimson
          'tertiary': '#7A3A49',     // Deep muted crimson
          'success': '#106A4E',      // Green
          'warning': '#B86E00',      // Amber
          'info': '#4B6A97',         // Blue
          'error': '#9A4E5F',        // Error red
        },
        
        'gray': {
          50: '#F9F9FB',
          100: '#F5F5F8',
          200: '#E6E6EB',
          300: '#CDCDD4',
          400: '#9798A1',
          500: '#64646B',
          600: '#49494D',
          700: '#343437',
          800: '#252529',
          900: '#1A1A1D',
        },
      },
      boxShadow: {
        'card': '0 4px 8px -2px rgba(0, 0, 0, 0.03), 0 2px 4px -1px rgba(0, 0, 0, 0.02)',
        'card-dark': '0 4px 8px rgba(0, 0, 0, 0.08)',
        'hover': '0 8px 16px -4px rgba(0, 0, 0, 0.05), 0 4px 8px -2px rgba(0, 0, 0, 0.03)',
        'hover-dark': '0 8px 12px rgba(0, 0, 0, 0.12)',
        'dropdown': '0 2px 5px rgba(0, 0, 0, 0.05), 0 1px 2px rgba(0, 0, 0, 0.03)',
        'dropdown-dark': '0 4px 8px rgba(0, 0, 0, 0.12)',
        'glow': '0 0 15px rgba(179, 50, 69, 0.10)',
        'glow-dark': '0 0 15px rgba(179, 50, 69, 0.05)',
        'subtle': '0 1px 3px rgba(0,0,0,0.03)',
        'subtle-dark': '0 1px 3px rgba(0,0,0,0.06)',
      },
      borderRadius: {
        'xl': '0.75rem',
        '2xl': '1rem',
        '3xl': '1.5rem',
        '4xl': '2rem',
      },
      animation: {
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'shimmer': 'shimmer 2.5s ease-in-out infinite',
        'fade-in': 'fadeIn 0.4s ease-out forwards',
        'slide-up': 'slideUp 0.4s ease-out',
        'slide-in-right': 'slideInRight 0.4s ease-out',
      },
      typography: {
        DEFAULT: {
          css: {
            color: '#49494D',
            letterSpacing: '-0.011em',
            lineHeight: '1.6',
            fontWeight: '300',
            a: {
              color: '#B33245',
              '&:hover': {
                color: '#8A1729',
              },
              fontWeight: '400',
            },
            h1: {
              color: '#1A1A1D',
              fontWeight: '400',
              letterSpacing: '-0.021em',
            },
            h2: {
              color: '#1A1A1D',
              fontWeight: '400',
              letterSpacing: '-0.021em',
            },
            h3: {
              color: '#1A1A1D',
              fontWeight: '400',
              letterSpacing: '-0.021em',
            },
            strong: {
              color: '#1A1A1D',
              fontWeight: '500',
            },
            code: {
              color: '#49494D',
              backgroundColor: '#F5F5F8',
              paddingLeft: '0.25rem',
              paddingRight: '0.25rem',
              paddingTop: '0.125rem',
              paddingBottom: '0.125rem',
              borderRadius: '0.25rem',
              fontWeight: '300',
            },
            pre: {
              backgroundColor: '#F5F5F8',
              color: '#49494D',
              borderRadius: '0.5rem',
              border: '1px solid #E6E6EB',
            },
            p: {
              marginTop: '0.75rem',
              marginBottom: '0.75rem',
            },
            ul: {
              marginTop: '0.75rem',
              marginBottom: '0.75rem',
              paddingLeft: '1.5rem',
            },
            ol: {
              marginTop: '0.75rem',
              marginBottom: '0.75rem',
              paddingLeft: '1.5rem',
            },
            blockquote: {
              fontStyle: 'italic',
              borderLeftColor: '#E6E6EB',
              color: '#64646B',
              fontWeight: '300',
            },
          },
        },
        dark: {
          css: {
            color: '#CDCDD4',
            a: {
              color: '#D6697A',
              '&:hover': {
                color: '#B33245',
              },
            },
            h1: {
              color: '#E6E6EB',
            },
            h2: {
              color: '#E6E6EB',
            },
            h3: {
              color: '#E6E6EB',
            },
            strong: {
              color: '#E6E6EB',
            },
            code: {
              color: '#CDCDD4',
              backgroundColor: '#2D2D31',
              borderColor: '#3F3F43',
            },
            pre: {
              backgroundColor: '#2D2D31',
              color: '#CDCDD4',
              borderColor: '#3F3F43',
            },
            blockquote: {
              borderLeftColor: '#3F3F43',
              color: '#9798A1',
            },
          },
        },
      },
      transitionProperty: {
        'height': 'height',
        'spacing': 'margin, padding',
        'width': 'width',
        'colors': 'color, background-color, border-color, text-decoration-color, fill, stroke',
        'glow': 'box-shadow, border-color',
      },
      keyframes: {
        shimmer: {
          '0%': { backgroundPosition: '-200% 0' },
          '100%': { backgroundPosition: '200% 0' },
        },
        fadeIn: {
          '0%': { opacity: '0', transform: 'translateY(8px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
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
      fontSize: {
        'xs': ['0.75rem', { lineHeight: '1.1rem', letterSpacing: '-0.01em' }],
        'sm': ['0.875rem', { lineHeight: '1.25rem', letterSpacing: '-0.01em' }],
        'base': ['1rem', { lineHeight: '1.6rem', letterSpacing: '-0.011em' }],
        'lg': ['1.125rem', { lineHeight: '1.75rem', letterSpacing: '-0.015em' }],
        'xl': ['1.25rem', { lineHeight: '1.9rem', letterSpacing: '-0.018em' }],
        '2xl': ['1.5rem', { lineHeight: '2.15rem', letterSpacing: '-0.021em' }],
        '3xl': ['1.875rem', { lineHeight: '2.35rem', letterSpacing: '-0.024em' }],
        '4xl': ['2.25rem', { lineHeight: '2.5rem', letterSpacing: '-0.027em' }],
      },
      spacing: {
        '4.5': '1.125rem',
        '18': '4.5rem',
      },
      opacity: {
        '85': '0.85',
        '95': '0.95',
      },
      backdropBlur: {
        xs: '2px',
      },
      maxWidth: {
        '8xl': '88rem',
        '9xl': '96rem',
      },
    },
  },
  plugins: [
    require('@tailwindcss/forms')({
      strategy: 'class',
    }),
    function ({ addBase, theme }) {
      addBase({
        // Fine-tune default focus styles
        'a:focus-visible, button:focus-visible, input:focus-visible, select:focus-visible, textarea:focus-visible': {
          outline: 'none',
          boxShadow: `0 0 0 2px ${theme('colors.accent.primary')}, 0 0 0 4px rgba(179, 50, 69, 0.3)`,
          borderRadius: '0.375rem',
        },
        // Improved scrollbar styling
        '*::-webkit-scrollbar': {
          width: '5px',
          height: '5px',
        },
        '*::-webkit-scrollbar-track': {
          background: 'transparent',
        },
        '*::-webkit-scrollbar-thumb': {
          backgroundColor: theme('colors.gray.300'),
          borderRadius: '9999px',
        },
        // Enhanced smooth scrolling
        'html': {
          scrollBehavior: 'smooth',
        },
      });
    },
  ],
}