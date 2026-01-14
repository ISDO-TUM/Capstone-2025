/** @type {import('tailwindcss').Config} */
export default {
  darkMode: ["class"],
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Match old design system
        primary: {
          DEFAULT: "#007bff",
          dark: "#0056b3",
          light: "#4f8cff",
        },
        text: {
          primary: "#1a237e",
          secondary: "#222",
          muted: "#495057",
          light: "#6c757d",
        },
        background: {
          DEFAULT: "#f7fafd",
          start: "#e3e9f0",
        },
        success: "#28a745",
        warning: "#ffc107",
        error: "#dc3545",
      },
      borderRadius: {
        lg: "18px",
        xl: "24px",
        "2xl": "28px",
        "3xl": "32px",
      },
      backdropBlur: {
        xs: "2px",
      },
      boxShadow: {
        glass: "0 8px 32px 0 rgba(31, 38, 135, 0.10)",
        "glass-lg": "0 16px 48px 0 rgba(0,123,255,0.18)",
        "glass-sm": "0 2px 12px 0 rgba(0,0,0,0.06)",
        "glass-focus": "0 4px 24px 0 rgba(0,123,255,0.10)",
      },
      animation: {
        "fade-in": "fadeIn 0.4s ease-out",
        "slide-up": "slideUp 0.4s ease-out",
        "scale-in": "scaleIn 0.2s ease-out",
      },
      keyframes: {
        fadeIn: {
          "0%": { opacity: "0" },
          "100%": { opacity: "1" },
        },
        slideUp: {
          "0%": { transform: "translateY(20px)", opacity: "0" },
          "100%": { transform: "translateY(0)", opacity: "1" },
        },
        scaleIn: {
          "0%": { transform: "scale(0.95)", opacity: "0" },
          "100%": { transform: "scale(1)", opacity: "1" },
        },
      },
    },
  },
  plugins: [],
}
