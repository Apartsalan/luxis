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
      page.locator("h1").filter({ hasText: "Instellingen" })
    ).toBeVisible({ timeout: 20000 });
  });

  test("S1: settings page shows all tab buttons", async ({ page }) => {
    // Settings page uses a sidebar nav with tab buttons.
    // Scope to <main> to avoid matching identically-named buttons in the
    // header (e.g. notification bell with aria-label="Meldingen").
    const settingsNav = page.locator("main nav");

    const expectedTabs = [
      "Profiel",
      "Kantoor",
      "Modules",
      "Team",
      "Workflow",
      "Meldingen",
      "Sjablonen",
      "Weergave",
    ];

    for (const tab of expectedTabs) {
      await expect(
        settingsNav.getByRole("button", { name: tab, exact: true })
      ).toBeVisible({ timeout: 10000 });
    }
  });

  test("S2: Kantoor tab shows tenant name and KvK number", async ({ page }) => {
    // Switch to Kantoor tab
    await page.locator("main nav").getByRole("button", { name: "Kantoor", exact: true }).click({ force: true });

    // Kantoor heading
    await expect(
      page.getByRole("heading", { name: "Kantoorgegevens" })
    ).toBeVisible({ timeout: 10000 });

    // Tenant name is in an input with id="settings-office-name"
    await expect(page.locator("#settings-office-name")).toHaveValue(/Kesting Legal/i, {
      timeout: 10000,
    });

    // KvK number in input
    await expect(page.locator("#settings-kvk-number")).toHaveValue(/88601536/, {
      timeout: 10000,
    });
  });

  test("S3: Profiel tab shows current user name", async ({ page }) => {
    // Profile tab is active by default
    await expect(
      page.getByRole("heading", { name: "Persoonlijke gegevens" })
    ).toBeVisible({ timeout: 10000 });

    // Full name input should have a value (e2e user = "E2E Test User")
    await expect(page.locator("#settings-full-name")).toHaveValue(/E2E/, {
      timeout: 10000,
    });
  });
});
