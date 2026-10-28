import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// vite.config.ts исполняется в Node, поэтому `process.env` здесь доступен в рантайме.
// Но без `@types/node` TypeScript не знает про глобал `process`. Эта локальная
// ambient-декларация убирает ошибку редактора, не добавляя лишнюю зависимость.
declare const process: {
    env: Record<string, string | undefined>;
};

// Цель прокси API:
//   локально на хосте (make dev-frontend)  → http://localhost:8000
//   в Docker-контейнере (make up, override) → http://backend:8000
// Берём из переменной окружения, по умолчанию localhost.
const apiProxyTarget =
    process.env.VITE_API_PROXY_TARGET ?? "http://localhost:8000";

export default defineConfig({
    plugins: [react()],
    server: {
        host: true, // слушать 0.0.0.0 — нужно для доступа из Docker-контейнера
        port: 5173,
        proxy: {
            "/api": {
                target: apiProxyTarget,
                changeOrigin: true,
                rewrite: (path) => path.replace(/^\/api/, ""),
            },
        },
    },
});
