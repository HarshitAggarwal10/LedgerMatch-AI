import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Dev server proxies /api straight to the FastAPI backend on :8000, so the
// React app can just call fetch("/api/...") the same way in dev and in the
// production build (where FastAPI serves the built dist/ directly).
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/api": {
        target: "http://127.0.0.1:8000",
        changeOrigin: true,
      },
    },
  },
});
