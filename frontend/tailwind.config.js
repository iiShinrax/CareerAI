/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#12141C",
        surface: "#1B1E29",
        surface2: "#232735",
        paper: "#F1EEE4",
        muted: "#8B90A3",
        line: "#2E3241",
        amber: "#F0A84B",
        teal: "#5FD3C4",
        coral: "#E8646B",
      },
      fontFamily: {
        display: ["'Instrument Serif'", "Georgia", "serif"],
        sans: ["'IBM Plex Sans'", "system-ui", "sans-serif"],
        mono: ["'IBM Plex Mono'", "ui-monospace", "monospace"],
      },
      borderRadius: {
        sm: "4px",
      },
    },
  },
  plugins: [],
};
