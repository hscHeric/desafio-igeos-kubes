import { defineConfig, loadEnv } from "vite";

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, ".", "");
  return {
    base: "/consumer/",
    server: {
      host: "127.0.0.1",
      port: 5174,
      strictPort: true,
      proxy: {
        "/api/consumer": {
          target: env.API_PROXY_TARGET || "http://127.0.0.1:8002",
          changeOrigin: true,
          rewrite: (path) => path.replace(/^\/api\/consumer/, ""),
        },
      },
    },
    preview: { host: "127.0.0.1", port: 4174, strictPort: true },
  };
});
