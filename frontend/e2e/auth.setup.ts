/**
 * Auth Setup — Playwright
 *
 * Logs in once via the real login form and saves storageState
 * (localStorage tokens) for use by all authenticated test specs.
 */

import { test as setup, expect } from "@playwright/test";

const authFile = "e2e/.auth/user.json";

setup("authenticate", async ({ page }) => {
  await page.goto("/login");

  await page.locator("#email").fill("lisanne@kestinglegal.nl");
  await page.locator("#password").fill("testpassword123");
  await page.getByRole("button", { name: "Inloggen" }).click();

  // Wait for dashboard to load (confirms login succeeded)
  await expect(
    page.getByRole("heading", { level: 1 })
  ).toContainText(/Goede(morgen|middag|navond)/, { timeout: 20000 });

  // Save the authenticated state (localStorage with tokens)
  await page.context().storageState({ path: authFile });
});
