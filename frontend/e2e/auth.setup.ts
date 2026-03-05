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

  // Wait for redirect to dashboard (away from /login)
  await page.waitForURL(/^(?!.*\/login)/, { timeout: 20000 });

  // Confirm dashboard loaded (sidebar link only visible when authenticated)
  await expect(
    page.getByRole("link", { name: /Dossiers/ })
  ).toBeVisible({ timeout: 10000 });

  // Save the authenticated state (localStorage with tokens)
  await page.context().storageState({ path: authFile });
});
