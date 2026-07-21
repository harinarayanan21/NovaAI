/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        sidebar: {
          bg: "#171717",
          hover: "#212121",
          active: "#2a2a2a",
        },
        chat: {
          bg: "#212121",
          user: "#2f2f2f",
          ai: "#171717",
        },
        accent: {
          DEFAULT: "#10a37f",
          hover: "#0e8c6d",
        },
      },
      animation: {
        "pulse-dot": "pulseDot 1.4s infinite ease-in-out",
      },
      keyframes: {
        pulseDot: {
          "0%, 80%, 100%": { opacity: "0.3", transform: "scale(0.8)" },
          "40%": { opacity: "1", transform: "scale(1)" },
        },
      },
    },
  },
  plugins: [],
};
