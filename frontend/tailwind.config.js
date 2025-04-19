/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./src/**/*.{js,jsx,ts,tsx}"],
  theme: {
    extend: {
      colors: {
        'harvard-crimson': '#8B0000',
        'harvard-dark': '#6D0000',
        'harvard-light': '#F1F6FF',
        'chat-user': '#EEF3FD',
        'chat-assistant': '#FAFAFA',
        'chat-border': '#DDE7F2',
      },
    },
  },
  plugins: [],
};