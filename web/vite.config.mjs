import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  build: {
    outDir: "dist/client",
  },
  optimizeDeps: {
    include: ["react", "react-dom/client"],
  },
  server: {
    host: "0.0.0.0",
    allowedHosts: ["terminal.local", "127.0.0.1", "localhost"],
    proxy: {
      "/api": "http://127.0.0.1:8766",
    },
    warmup: {
      clientFiles: ["./src/main.tsx"],
    },
  },
  test: {
    environment: "jsdom",
    include: ["src/**/*.test.ts", "src/**/*.test.tsx"],
    pool: "vmThreads",
    maxWorkers: 1,
    setupFiles: "./src/test/setup.ts",
  },
  plugins: [react()],
});
