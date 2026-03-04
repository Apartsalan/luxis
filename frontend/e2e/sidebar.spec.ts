/**
 * Sidebar E2E Tests — Luxis
 *
 * Tests sidebar navigation items, click navigation, and collapse/expand.
 * Auth is provided by storageState (setup project).
 */

import { test, expect } from "@playwright/test";

test.describe("Sidebar Navigation", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/");
    // Wait for dashboard to confirm auth
    await expect(
      page.getByRole("heading", { level: 1 })
    ).toContainText(/Goede(morgen|middag|navond)/, { timeout: 20000 });
  });

  test("S1: sidebar shows all core navigation items", async ({ page }) => {
    const coreItems = [
      "Dashboard",
      "Mijn Taken",
      "Relaties",
      "Dossiers",
      "Documenten",
      "Instellingen",
    ];

    for (const item of coreItems) {
      await expect(
        page.getByRole("link", { name: item, exact: true })
      ).toBeVisible({ timeout: 10000 });
    }
  });

  test("S2: clicking sidebar items navigates correctly", async ({ page }) => {
    // Click Relaties
    await page.getByRole("link", { name: "Relaties", exact: true }).click();
    await page.waitForURL("**/relaties", { timeout: 10000 });
    // Use h1 specifically to avoid matching sidebar section heading
    await expect(page.locator("h1").filter({ hasText: "Relaties" })).toBeVisible({
      timeout: 10000,
    });

    // Click Dossiers
    await page.getByRole("link", { name: "Dossiers", exact: true }).click();
    await page.waitForURL("**/zaken", { timeout: 10000 });
    await expect(page.locator("h1").filter({ hasText: "Dossiers" })).toBeVisible({
      timeout: 10000,
    });
  });

  test("S3: sidebar collapse and expand works", async ({ page }) => {
    // Verify sidebar text is visible initially
    await expect(
      page.getByRole("link", { name: "Relaties", exact: true })
    ).toBeVisible({ timeout: 10000 });

    // Click collapse button
    const collapseBtn = page.getByTitle("Menu inklappen");
    if (await collapseBtn.isVisible()) {
      await collapseBtn.click({ force: true });

      // Wait for animation
      await page.waitForTimeout(500);

      // Sidebar text labels should be hidden when collapsed
      await expect(
        page.locator("nav").getByText("Relaties", { exact: true })
      ).toBeHidden();

      // Click expand button (force: true to avoid Next.js dev overlay interception)
      const expandBtn = page.getByTitle("Menu uitklappen");
      await expandBtn.click({ force: true });

      await page.waitForTimeout(500);

      // Text should be visible again
      await expect(
        page.getByRole("link", { name: "Relaties", exact: true })
      ).toBeVisible();
    }
  });
});
