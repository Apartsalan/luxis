/**
 * Relaties (Contacts) CRUD E2E Tests — Luxis
 *
 * Tests the full contact lifecycle: list, create company, create person,
 * edit, and delete. Tests are sequential (R4 depends on R2, R5 on R3).
 * Auth is provided by storageState (setup project).
 */

import { test, expect } from "@playwright/test";
import { loginViaApi } from "./helpers/auth";
import { deleteContact } from "./helpers/api";

// Store IDs across tests (workers=1, sequential execution guaranteed)
let authToken = "";
let companyId = "";
let personId = "";

test.describe("Relaties CRUD", () => {
  test.beforeAll(async ({ request }) => {
    const { accessToken } = await loginViaApi(request);
    authToken = accessToken;
  });

  // Clean up created contacts after all tests
  test.afterAll(async ({ request }) => {
    if (companyId) {
      await deleteContact(request, authToken, companyId).catch(() => {});
    }
    if (personId) {
      await deleteContact(request, authToken, personId).catch(() => {});
    }
  });

  test("R1: relaties list page loads with UI elements", async ({ page }) => {
    await page.goto("/relaties");

    // Page heading
    await expect(
      page.locator("h1").filter({ hasText: "Relaties" })
    ).toBeVisible({ timeout: 15000 });

    // "Nieuwe relatie" button
    await expect(
      page.getByRole("link", { name: /Nieuwe relatie/ })
    ).toBeVisible();

    // Filter buttons
    await expect(page.getByRole("button", { name: "Alle" })).toBeVisible();
    await expect(
      page.getByRole("button", { name: "Bedrijven" })
    ).toBeVisible();
    await expect(
      page.getByRole("button", { name: "Personen" })
    ).toBeVisible();

    // Search input
    await expect(
      page.getByPlaceholder(/Zoek op naam/)
    ).toBeVisible();
  });

  test("R2: create a company contact", async ({ page }) => {
    test.setTimeout(60000);
    await page.goto("/relaties");
    await page.waitForLoadState("domcontentloaded");

    // Click "Nieuwe relatie"
    await page.getByRole("link", { name: /Nieuwe relatie/ }).click();
    await page.waitForURL("**/relaties/nieuw", { timeout: 10000 });

    // Select "Bedrijf" (default, but click to be explicit)
    await page.getByRole("button", { name: "Bedrijf" }).click();

    // Fill company name (label not connected via htmlFor, use placeholder)
    await page.getByPlaceholder("Acme B.V.").fill("E2E Testbedrijf B.V.");

    // Fill optional fields (find input after the label text)
    await page.locator("label:has-text('E-mail') + input").first().fill("e2e-bedrijf@test.nl");
    await page.locator("label:has-text('Telefoon') + input").first().fill("020-1234567");

    // Submit
    await page.getByRole("button", { name: "Opslaan" }).click();

    // Wait for redirect to detail page (UUID in URL, not "nieuw")
    await page.waitForURL(/\/relaties\/[a-f0-9-]+$/, { timeout: 30000 });

    // Extract the contact ID from URL
    companyId = page.url().split("/relaties/")[1];

    // Company name should be visible in the h1 on detail page
    await expect(
      page.locator("h1").filter({ hasText: "E2E Testbedrijf B.V." })
    ).toBeVisible({ timeout: 10000 });

    // Toast notification
    await expect(page.getByText("Relatie aangemaakt")).toBeVisible({
      timeout: 5000,
    });
  });

  test("R3: create a person contact", async ({ page }) => {
    test.setTimeout(60000);
    await page.goto("/relaties/nieuw");
    await page.waitForLoadState("domcontentloaded");

    // Wait for the form to be ready
    await expect(page.getByRole("button", { name: "Persoon" })).toBeVisible({
      timeout: 15000,
    });

    // Select "Persoon"
    await page.getByRole("button", { name: "Persoon" }).click();

    // Fill person name fields (labels not connected via htmlFor)
    await page.locator("label:has-text('Voornaam') + input").fill("Jan");
    await page.locator("label:has-text('Achternaam') + input").fill("E2ETestpersoon");

    // Submit
    await page.getByRole("button", { name: "Opslaan" }).click();

    // Wait for redirect to detail page (UUID in URL, not "nieuw")
    await page.waitForURL(/\/relaties\/[a-f0-9-]+$/, { timeout: 30000 });

    // Extract person ID
    personId = page.url().split("/relaties/")[1];

    // Person name should be visible in the h1
    await expect(
      page.locator("h1").filter({ hasText: "Jan E2ETestpersoon" })
    ).toBeVisible({ timeout: 10000 });

    // Toast notification
    await expect(page.getByText("Relatie aangemaakt")).toBeVisible({
      timeout: 5000,
    });
  });

  test("R4: edit an existing company contact", async ({ page }) => {
    test.skip(!companyId, "R2 must create a company first");

    await page.goto(`/relaties/${companyId}`);
    await page.waitForLoadState("domcontentloaded");

    // Verify we're on the right page
    await expect(
      page.locator("h1").filter({ hasText: "E2E Testbedrijf B.V." })
    ).toBeVisible({ timeout: 10000 });

    // Click "Bewerken"
    await page.getByRole("button", { name: /Bewerken/ }).click();

    // Edit form should appear — find the email input in edit mode and change it
    const emailInput = page.locator("label:has-text('E-mail') + input").first();
    await emailInput.clear();
    await emailInput.fill("updated-e2e@test.nl");

    // Click save (the button with Check icon + "Opslaan" text in edit mode)
    await page.getByRole("button", { name: /Opslaan/ }).click();

    // Toast should confirm update
    await expect(page.getByText("Relatie bijgewerkt")).toBeVisible({
      timeout: 10000,
    });

    // Updated email should be visible on the page
    await expect(page.getByText("updated-e2e@test.nl")).toBeVisible({
      timeout: 5000,
    });
  });

  test("R5: delete a person contact", async ({ page }) => {
    test.skip(!personId, "R3 must create a person first");

    await page.goto(`/relaties/${personId}`);
    await page.waitForLoadState("domcontentloaded");

    // Verify we're on the right page
    await expect(
      page.locator("h1").filter({ hasText: "Jan E2ETestpersoon" })
    ).toBeVisible({ timeout: 10000 });

    // Register dialog handler BEFORE clicking delete
    page.on("dialog", (dialog) => dialog.accept());

    // Click delete button
    await page.getByTitle("Verwijderen").click();

    // Should redirect to relaties list
    await page.waitForURL("**/relaties", { timeout: 10000 });

    // Toast should confirm deletion
    await expect(page.getByText("Relatie verwijderd")).toBeVisible({
      timeout: 5000,
    });

    // Mark as cleaned up so afterAll doesn't try to delete again
    personId = "";
  });
});
