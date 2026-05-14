/**
 * Documenten E2E Tests — Luxis
 *
 * Tests document templates page: list, template visibility.
 * Auth is provided by storageState (setup project).
 */

import { test, expect } from "@playwright/test";

test.describe("Documenten", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/documenten");
    // Heading is now "Sjablonen"
    await expect(
      page.locator("h1").filter({ hasText: "Sjablonen" })
    ).toBeVisible({ timeout: 20000 });
  });

  test("DOC1: documents page loads with template tabs", async ({ page }) => {
    // Tabs for Word + HTML templates
    await expect(
      page.getByRole("button", { name: /Word-sjablonen/ })
    ).toBeVisible({ timeout: 10000 });
    await expect(
      page.getByRole("button", { name: /HTML Sjablonen/ })
    ).toBeVisible({ timeout: 10000 });

    // Subtitle reference to dossier-generatie
    await expect(
      page.getByText(/documentsjablonen|dossiergeneratie/i).first()
    ).toBeVisible();
  });
});
