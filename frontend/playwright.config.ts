import { defineConfig, devices } from "@playwright/test";

export default defineConfig({
  testDir: "./e2e",
  fullyParallel: false,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: 1,
  reporter: "html",
  use: {
    baseURL: "http://localhost:3000",
    trace: "on-first-retry",
    screenshot: "only-on-failure",
  },
  projects: [
    // Setup project: logs in once and saves auth state
    {
      name: "setup",
      testMatch: /auth\.setup\.ts/,
    },
    // Auth spec tests login/logout flows — no stored auth needed
    {
      name: "auth",
      testMatch: /auth\.spec\.ts/,
      use: { ...devices["Desktop Chrome"] },
    },
    // All other specs use the stored auth state
    {
      name: "chromium",
      testIgnore: /auth\.(spec|setup)\.ts|mobile-overflow\.spec\.ts/,
      use: {
        ...devices["Desktop Chrome"],
        storageState: "e2e/.auth/user.json",
      },
      dependencies: ["setup"],
    },
    // Mobiele wachter: telefoon-viewport + touch, controleert horizontale overloop
    // op alle routes (fout-SOORT-wachter uit skill breed-testen). De spec wisselt
    // zelf tussen 390 (telefoon) en 820 (tablet) per route.
    {
      name: "mobile",
      testMatch: /mobile-overflow\.spec\.ts/,
      use: {
        ...devices["Desktop Chrome"],
        viewport: { width: 390, height: 844 },
        isMobile: true,
        hasTouch: true,
        storageState: "e2e/.auth/user.json",
      },
      dependencies: ["setup"],
    },
  ],
  webServer: {
    command: "npm run dev",
    url: "http://localhost:3000",
    reuseExistingServer: true,
    timeout: 30_000,
  },
});
