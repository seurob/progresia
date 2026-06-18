/// <reference types="vitest" />
import tailwindcss from "@tailwindcss/vite";
import react from "@vitejs/plugin-react";
import { defineConfig, type UserConfig } from "vite";

type VitestUserConfig = UserConfig & {
  test: {
    environment: string;
    globals: boolean;
    setupFiles: string[];
  };
};

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    port: 5173
  },
  test: {
    environment: "jsdom",
    globals: true,
    setupFiles: ["./src/test/setup.ts"]
  }
} as VitestUserConfig);
