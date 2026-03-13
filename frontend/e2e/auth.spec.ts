/**
 * Auth E2E Tests — Luxis
 *
 * Tests login form, invalid credentials, session persistence, and logout.
 */

import { test, expect } from "@playwright/test";

/** Login via the real login form — most reliable approach */
async function loginViaForm(page: import("@playwright/test").Page) {
  await page.goto("/login");
  await page.locator("#email").fill("lisanne@kestinglegal.nl");
  await page.locator("#password").fill("testpassword123");
  await page.getByRole("button", { name: "Inloggen" }).click();
  // Wait for redirect away from /login first, then verify dashboard
  await page.waitForURL(/^(?!.*\/login)/, { timeout: 20000 });
  await expect(
    page.getByRole("link", { name: /Dossiers/ })
  ).toBeVisible({ timeout: 10000 });
}

test.describe("Authentication", () => {
  test("A1: successful login redirects to dashboard", async ({ page }) => {
    await page.goto("/login");

    await page.locator("#email").fill("lisanne@kestinglegal.nl");
    await page.locator("#password").fill("testpassword123");
    await page.getByRole("button", { name: "Inloggen" }).click();

    // Wait for redirect away from /login
    await page.waitForURL(/^(?!.*\/login)/, { timeout: 20000 });

    // Verify dashboard loaded (sidebar visible = authenticated)
    await expect(
      page.getByRole("link", { name: /Dossiers/ })
    ).toBeVisible({ timeout: 10000 });

    // Token should be stored in localStorage
    const token = await page.evaluate(() =>
      localStorage.getItem("luxis_access_token")
    );
    expect(token).toBeTruthy();
  });

  test("A2: invalid credentials shows error message", async ({ page }) => {
    await page.goto("/login");

    await page.locator("#email").fill("lisanne@kestinglegal.nl");
    await page.locator("#password").fill("wrongpassword");
    await page.getByRole("button", { name: "Inloggen" }).click();

    // Error message should appear
    await expect(
      page.getByText(/Onjuist e-mailadres|Incorrect email/)
    ).toBeVisible({ timeout: 10000 });

    // Should stay on login page
    expect(page.url()).toContain("/login");
  });

  test("A3: session persists after page reload", async ({ page }) => {
    // Login via the real form (most reliable)
    await loginViaForm(page);

    // Reload the page
    await page.reload();
    await page.waitForLoadState("domcontentloaded");

    // Should still show dashboard (not redirected to login)
    await expect(
      page.getByRole("link", { name: /Dossiers/ })
    ).toBeVisible({ timeout: 10000 });
  });

  test("A4: logout clears session and redirects to login", async ({
    page,
  }) => {
    // Login via the real form
    await loginViaForm(page);

    // Click logout button
    await page.getByTitle("Uitloggen").click();

    // Should redirect to login
    await page.waitForURL("**/login", { timeout: 10000 });

    // Token should be removed
    const token = await page.evaluate(() =>
      localStorage.getItem("luxis_access_token")
    );
    expect(token).toBeNull();
  });
});
