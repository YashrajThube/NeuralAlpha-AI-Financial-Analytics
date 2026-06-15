/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,jsx}",
  ],
  theme: {
    extend: {
      colors: {
        'brand-purple': '#7C3AED',
        'brand-blue': '#3B82F6',
        'brand-cyan': '#06B6D4',
      },
      fontFamily: {
        sora: ['Sora', 'sans-serif'],
        'dm-sans': ['DM Sans', 'sans-serif'],
      },
    },
  },
  plugins: [],
}
