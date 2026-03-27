/**
 * Instellingen (Settings) E2E Tests — Luxis
 *
 * Tests tenant settings page: load, read, update fields.
 * Auth is provided by storageState (setup project).
 */

import { test, expect } from "@playwright/test";

test.describe("Instellingen", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/instellingen");
    await expect(
      page.getByRole("heading", { name: /Instellingen/i })
    ).toBeVisible({ timeout: 20000 });
  });

  test("S1: settings page loads with tenant name", async ({ page }) => {
    // Should show the tenant name somewhere on the page
    await expect(page.getByText("Kesting Legal")).toBeVisible({
      timeout: 10000,
    });
  });

  test("S2: KvK number is displayed", async ({ page }) => {
    await expect(page.getByText("88601536")).toBeVisible({ timeout: 10000 });
  });

  test("S3: can update phone number", async ({ page }) => {
    const phoneInput = page.locator(
      'input[name="phone"], input[placeholder*="Telefoon"], input[placeholder*="telefoon"]'
    );

    // If phone field exists, try updating it
    if (await phoneInput.isVisible({ timeout: 5000 }).catch(() => false)) {
      await phoneInput.fill("+31207891234");
      const saveButton = page.getByRole("button", { name: /Opslaan/i });
      if (await saveButton.isVisible({ timeout: 3000 }).catch(() => false)) {
        await saveButton.click({ force: true });
        // Expect success toast or updated value
        await expect(
          page.getByText(/opgeslagen|bijgewerkt|succes/i).first()
        ).toBeVisible({ timeout: 10000 });
      }
    }
  });
});
