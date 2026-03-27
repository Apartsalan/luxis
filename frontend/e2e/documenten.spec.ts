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
    await expect(
      page.getByRole("heading", { name: /Document/i })
    ).toBeVisible({ timeout: 20000 });
  });

  test("DOC1: documents page loads", async ({ page }) => {
    // Page should show some content — either templates list or empty state
    const hasTemplates = await page
      .getByText(/template|sjabloon/i)
      .first()
      .isVisible({ timeout: 5000 })
      .catch(() => false);
    const hasEmpty = await page
      .getByText(/geen.*document|nog geen/i)
      .first()
      .isVisible({ timeout: 3000 })
      .catch(() => false);

    expect(hasTemplates || hasEmpty).toBeTruthy();
  });
});
