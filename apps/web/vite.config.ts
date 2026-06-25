/// <reference types="vitest" />
import { sentryVitePlugin } from "@sentry/vite-plugin";
import tailwindcss from "@tailwindcss/vite";
import react from "@vitejs/plugin-react";
import { defineConfig, loadEnv, type UserConfig } from "vite";

type VitestUserConfig = UserConfig & {
  test: {
    environment: string;
    globals: boolean;
    setupFiles: string[];
  };
};

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), "");
  const canUploadSourceMaps = Boolean(
    env.SENTRY_AUTH_TOKEN && env.SENTRY_ORG && env.SENTRY_PROJECT
  );

  return {
    plugins: [
      react(),
      tailwindcss(),
      canUploadSourceMaps
        ? sentryVitePlugin({
            authToken: env.SENTRY_AUTH_TOKEN,
            org: env.SENTRY_ORG,
            project: env.SENTRY_PROJECT,
            release: { name: env.VITE_SENTRY_RELEASE || undefined },
            sourcemaps: { filesToDeleteAfterUpload: ["./dist/**/*.map"] }
          })
        : undefined
    ].filter(Boolean),
    build: {
      sourcemap: canUploadSourceMaps ? "hidden" : false
    },
    server: {
      port: 5173
    },
    test: {
      environment: "jsdom",
      globals: true,
      setupFiles: ["./src/test/setup.ts"]
    }
  } as VitestUserConfig;
});
