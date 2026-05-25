import { defineConfig } from "@playwright/test";

export default defineConfig({
  testDir: "./real-sites",
  timeout: 90_000,
  fullyParallel: false,
  retries: 1,
  reporter: [["list"], ["html", { outputFolder: "test-results/real-dom-report", open: "never" }]],
  use: {
    actionTimeout: 15_000,
    navigationTimeout: 45_000,
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
    video: "retain-on-failure",
  },
  projects: [
    {
      name: "chromium-extension-real-dom",
      use: {
        browserName: "chromium",
        headless: false,
      },
    },
  ],
});
