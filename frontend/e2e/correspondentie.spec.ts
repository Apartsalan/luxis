/**
 * Correspondentie E2E Tests — Luxis
 *
 * Tests the correspondentie (email triage) page:
 * heading, search, sync button, and empty/list state.
 * Auth is provided by storageState (setup project).
 */

import { test, expect } from "@playwright/test";

test.describe("Correspondentie", () => {
  test("C1: correspondentie page loads with heading and controls", async ({
    page,
  }) => {
    await page.goto("/correspondentie");

    // Page heading — renamed to "Mail"
    await expect(
      page.locator("h1").filter({ hasText: "Mail" })
    ).toBeVisible({ timeout: 15000 });

    // Tab buttons
    await expect(
      page.getByRole("button", { name: /Alle e-mails/ })
    ).toBeVisible();
    await expect(
      page.getByRole("button", { name: /Ongesorteerd/ })
    ).toBeVisible();

    // Search input
    await expect(
      page.getByPlaceholder(/Zoek op afzender, onderwerp/)
    ).toBeVisible();

    // Sync inbox button
    await expect(
      page.getByRole("button", { name: /Sync inbox/ })
    ).toBeVisible();
  });

  test("C2: shows empty state or email list", async ({ page }) => {
    await page.goto("/correspondentie");

    // Wait for page to load
    await expect(
      page.locator("h1").filter({ hasText: "Mail" })
    ).toBeVisible({ timeout: 15000 });

    // Switch to "Ongesorteerd" tab to check the EmptyState component
    await page.getByRole("button", { name: /Ongesorteerd/ }).click({ force: true });

    // Either:
    // - Empty state "Alles gesorteerd" (no unsorted emails)
    // - Email list rendered (at least one card)
    const emptyState = page.getByText("Alles gesorteerd");
    const emailCount = page.getByText(/e-mails?$/i);

    await expect(
      emptyState.or(emailCount)
    ).toBeVisible({ timeout: 10000 });
  });
});
