/**
 * Dashboard E2E Tests — Luxis
 *
 * Tests dashboard page load, greeting, KPI cards, and navigation.
 * Auth is provided by storageState (setup project).
 */

import { test, expect } from "@playwright/test";

test.describe("Dashboard", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/");
    // Wait for the authenticated dashboard to load
    await expect(
      page.getByRole("heading", { level: 1 })
    ).toContainText(/Goede(morgen|middag|navond)/, { timeout: 20000 });
  });

  test("D1: dashboard shows greeting with user name", async ({ page }) => {
    const heading = page.getByRole("heading", { level: 1 });

    // Should contain the user's first name
    await expect(heading).toContainText("Lisanne");

    // Date should be visible somewhere on the page
    const dateRegex = /\d{1,2}\s+(januari|februari|maart|april|mei|juni|juli|augustus|september|oktober|november|december)\s+\d{4}/;
    await expect(page.getByText(dateRegex).first()).toBeVisible();
  });

  test("D2: KPI cards are visible with values", async ({ page }) => {
    // Scope to main content area (avoid matching sidebar nav items)
    const main = page.locator("main");
    await expect(main.getByText("Actieve dossiers")).toBeVisible({
      timeout: 10000,
    });
    await expect(main.getByText("Relaties")).toBeVisible();
  });

  test("D3: Nieuw dossier button navigates to create page", async ({
    page,
  }) => {
    const button = page.getByRole("link", { name: /Nieuw dossier/ });
    await expect(button).toBeVisible({ timeout: 10000 });
    await button.click();

    await page.waitForURL("**/zaken/nieuw", { timeout: 10000 });
  });
});
