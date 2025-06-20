/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'brand-primary': {
          light: '#60A5FA', // blue-400
          DEFAULT: '#3B82F6', // blue-500
          dark: '#2563EB',  // blue-600
        },
        'brand-secondary': {
          light: '#F472B6', // pink-400
          DEFAULT: '#EC4899', // pink-500
          dark: '#DB2777',  // pink-600
        },
        'brand-accent': {
          light: '#A78BFA', // violet-400
          DEFAULT: '#8B5CF6', // violet-500
          dark: '#7C3AED',  // violet-600
        },
        'brand-background': '#F3F4F6', // gray-100
        'brand-surface': '#FFFFFF',    // white (for cards, inputs)
        'brand-text-primary': '#1F2937',    // gray-800
        'brand-text-secondary': '#4B5563', // gray-600
      },
      backgroundImage: theme => ({
        'gradient-theme': `linear-gradient(to right, ${theme('colors.brand-primary.DEFAULT')}, ${theme('colors.brand-accent.DEFAULT')})`,
      })
    },
  },
  plugins: [],
}
