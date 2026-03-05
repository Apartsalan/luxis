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

    // Page heading
    await expect(
      page.locator("h1").filter({ hasText: "Correspondentie" })
    ).toBeVisible({ timeout: 15000 });

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
      page.locator("h1").filter({ hasText: "Correspondentie" })
    ).toBeVisible({ timeout: 15000 });

    // Either:
    // - Empty state: "Alles gesorteerd" or "Alle e-mails zijn gesorteerd"
    // - Email list: at least one email item (has direction icons)
    const emptyState = page.getByText("Alles gesorteerd");
    const emailList = page.getByText(/ongesorteerde e-mail/);
    const allSorted = page.getByText("Alle e-mails zijn gesorteerd");

    // One of these should be visible within 10 seconds
    await expect(
      emptyState.or(emailList).or(allSorted)
    ).toBeVisible({ timeout: 10000 });
  });
});
