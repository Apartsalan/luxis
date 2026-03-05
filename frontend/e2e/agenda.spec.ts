/**
 * Agenda (Calendar) E2E Tests — Luxis
 *
 * Tests the agenda page: calendar display, event creation via dialog,
 * and event deletion. Tests are sequential.
 * Auth is provided by storageState (setup project).
 */

import { test, expect } from "@playwright/test";
import { loginViaApi } from "./helpers/auth";
import {
  createCalendarEvent,
  deleteCalendarEvent,
} from "./helpers/api";

// Store IDs across tests (workers=1, sequential execution guaranteed)
let authToken = "";
let eventId = "";

test.describe("Agenda", () => {
  test.beforeAll(async ({ request }) => {
    const { accessToken } = await loginViaApi(request);
    authToken = accessToken;
  });

  test.afterAll(async ({ request }) => {
    if (eventId) {
      await deleteCalendarEvent(request, authToken, eventId).catch(() => {});
    }
  });

  test("A1: agenda page loads with calendar and controls", async ({
    page,
  }) => {
    await page.goto("/agenda");

    // Page heading
    await expect(
      page.locator("h1").filter({ hasText: "Agenda" })
    ).toBeVisible({ timeout: 15000 });

    // Subtitle
    await expect(
      page.getByText("Overzicht van taken en afspraken")
    ).toBeVisible();

    // "Nieuw event" button
    await expect(
      page.getByRole("button", { name: /Nieuw event/ })
    ).toBeVisible();

    // Navigation: "Vandaag" button
    await expect(
      page.getByRole("button", { name: /Vandaag/ })
    ).toBeVisible();

    // View mode toggles (exact match to avoid "Vorige maand"/"Volgende maand")
    await expect(
      page.getByRole("button", { name: "Maand", exact: true })
    ).toBeVisible();
    await expect(
      page.getByRole("button", { name: "Week", exact: true })
    ).toBeVisible();

    // Day name headers (calendar grid)
    await expect(page.getByText("ma").first()).toBeVisible();
  });

  test("A2: create event via dialog", async ({ page }) => {
    test.setTimeout(60000);
    await page.goto("/agenda");
    await page.waitForLoadState("domcontentloaded");

    // Wait for page to load
    await expect(
      page.locator("h1").filter({ hasText: "Agenda" })
    ).toBeVisible({ timeout: 15000 });

    // Click "Nieuw event"
    await page.getByRole("button", { name: /Nieuw event/ }).click({ force: true });

    // Wait for dialog to appear (the dialog heading "Nieuw event")
    await expect(
      page.locator("h2").filter({ hasText: "Nieuw event" })
    ).toBeVisible({ timeout: 5000 });

    // Fill in the title
    const titleInput = page.getByPlaceholder(/Bijv\. Overleg met/);
    await titleInput.fill("E2E Test Afspraak");

    // Submit the form (button text is "Opslaan" or "Aanmaken")
    await page.getByRole("button", { name: /Opslaan|Aanmaken/ }).click({ force: true });

    // Dialog should close
    await expect(
      page.locator("h2").filter({ hasText: "Nieuw event" })
    ).not.toBeVisible({ timeout: 10000 });

    // Click on today's date number to open the day detail panel
    // Today is highlighted — find it by the special styling or just look for the date
    const todayNum = new Date().getDate().toString();
    // The today cell has special styling — click on it
    await page.locator(`[class*="bg-primary"]`).filter({ hasText: todayNum }).first().click({ force: true });

    // The day detail panel should show our event
    await expect(
      page.getByText("E2E Test Afspraak").first()
    ).toBeVisible({ timeout: 10000 });
  });

  test("A3: create and delete event via API + verify on page", async ({
    page,
    request,
  }) => {
    test.setTimeout(60000);

    // Seed an event via API for today
    const now = new Date();
    const startTime = new Date(now);
    startTime.setHours(14, 0, 0, 0);
    const endTime = new Date(now);
    endTime.setHours(15, 0, 0, 0);

    const event = await createCalendarEvent(request, authToken, {
      title: "E2E Verwijder Test",
      start_time: startTime.toISOString(),
      end_time: endTime.toISOString(),
      event_type: "meeting",
    });
    eventId = event.id;

    // Navigate to agenda
    await page.goto("/agenda");
    await page.waitForLoadState("domcontentloaded");

    await expect(
      page.locator("h1").filter({ hasText: "Agenda" })
    ).toBeVisible({ timeout: 15000 });

    // Click on today's date to open day detail panel
    const todayNum = new Date().getDate().toString();
    await page.locator(`[class*="bg-primary"]`).filter({ hasText: todayNum }).first().click({ force: true });

    // Verify event is in the detail panel
    await expect(
      page.getByText("E2E Verwijder Test").first()
    ).toBeVisible({ timeout: 10000 });

    // Delete the event via API
    await deleteCalendarEvent(request, authToken, eventId);
    eventId = "";

    // Reload and verify event is gone
    await page.reload();
    await expect(
      page.locator("h1").filter({ hasText: "Agenda" })
    ).toBeVisible({ timeout: 15000 });

    // Event should no longer appear
    await expect(
      page.getByText("E2E Verwijder Test")
    ).not.toBeVisible({ timeout: 5000 });
  });
});
