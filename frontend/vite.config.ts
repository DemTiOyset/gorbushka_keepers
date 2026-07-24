import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// During local development the API proxy forwards /api/* to the FastAPI backend.
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/api": {
        target: "http://localhost:8000",
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, ""),
      },
    },
  },
});
