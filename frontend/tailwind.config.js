/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        brand: {
          50: "#eefdf3",
          100: "#d6fadf",
          500: "#16a34a",
          600: "#15803d",
          700: "#166534",
        },
        alert: {
          500: "#dc2626",
          600: "#b91c1c",
        },
      },
    },
  },
  plugins: [],
};
