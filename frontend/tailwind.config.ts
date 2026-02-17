import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        // Luxis brand palette — professional law firm aesthetic
        navy: {
          50: "#f0f3f9",
          100: "#d9e0f0",
          200: "#b3c1e1",
          300: "#8da2d2",
          400: "#6783c3",
          500: "#1a365d",
          600: "#162d4d",
          700: "#12243d",
          800: "#0e1b2e",
          900: "#0a121e",
        },
        cream: {
          50: "#fefdfb",
          100: "#fdf9f3",
          200: "#faf3e7",
          300: "#f5e8d0",
          400: "#f0dcb9",
        },
        gold: {
          50: "#fdf8ef",
          100: "#f9edcf",
          200: "#f3db9f",
          300: "#edc96f",
          400: "#c9a84c",
          500: "#a58738",
        },
      },
    },
  },
  plugins: [],
};

export default config;
