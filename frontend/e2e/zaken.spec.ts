/**
 * Zaken (Cases) CRUD E2E Tests — Luxis
 *
 * Tests the full case lifecycle: list, create, detail with tabs,
 * edit, status change, and delete. Tests are sequential.
 * Auth is provided by storageState (setup project).
 */

import { test, expect } from "@playwright/test";
import { loginViaApi } from "./helpers/auth";
import {
  createContact,
  deleteContact,
  createCase,
  deleteCase,
  updateCaseStatus,
} from "./helpers/api";

// Store IDs across tests (workers=1, sequential execution guaranteed)
let authToken = "";
let clientId = "";
let caseId = "";

test.describe("Zaken CRUD", () => {
  test.beforeAll(async ({ request }) => {
    const { accessToken } = await loginViaApi(request);
    authToken = accessToken;

    // Seed a client contact for case creation
    const client = await createContact(request, authToken, {
      contact_type: "company",
      name: "E2E ZaakClient B.V.",
      email: "e2e-zaakclient@test.nl",
    });
    clientId = client.id;
  });

  test.afterAll(async ({ request }) => {
    if (caseId) {
      await deleteCase(request, authToken, caseId).catch(() => {});
    }
    if (clientId) {
      await deleteContact(request, authToken, clientId).catch(() => {});
    }
  });

  test("Z1: zaken list page loads with table UI elements", async ({
    page,
  }) => {
    await page.goto("/zaken");

    // Page heading
    await expect(
      page.locator("h1").filter({ hasText: "Dossiers" })
    ).toBeVisible({ timeout: 15000 });

    // "Nieuw dossier" button
    await expect(
      page.getByRole("link", { name: /Nieuw dossier/ })
    ).toBeVisible();

    // Search input
    await expect(
      page.getByPlaceholder(/Zoek op dossiernummer/)
    ).toBeVisible();

    // Type filter
    await expect(page.locator("select").first()).toBeVisible();
  });

  test("Z2: 'Nieuw dossier' navigates to /zaken/nieuw", async ({ page }) => {
    await page.goto("/zaken");
    await page.waitForLoadState("domcontentloaded");

    await expect(
      page.getByRole("link", { name: /Nieuw dossier/ })
    ).toBeVisible({ timeout: 15000 });

    await page.getByRole("link", { name: /Nieuw dossier/ }).click();
    await page.waitForURL("**/zaken/nieuw", { timeout: 10000 });

    // Verify form page loaded
    await expect(
      page.locator("h1").filter({ hasText: "Nieuw dossier" })
    ).toBeVisible({ timeout: 10000 });
  });

  test("Z3: create a new case via form", async ({ page }) => {
    test.setTimeout(60000);
    await page.goto("/zaken/nieuw");
    await page.waitForLoadState("domcontentloaded");

    // Wait for the form to be ready
    await expect(
      page.locator("h1").filter({ hasText: "Nieuw dossier" })
    ).toBeVisible({ timeout: 15000 });

    // Change case type to "advies" (for 7-tab detail page)
    await page
      .locator("label:has-text('Dossiertype') ~ select")
      .first()
      .selectOption("advies");

    // Search for client
    const clientSearchInput = page.getByPlaceholder("Zoek een client...");
    await clientSearchInput.fill("E2E ZaakClient");

    // Wait for dropdown results and click the matching contact
    const clientOption = page.locator("button", {
      hasText: "E2E ZaakClient B.V.",
    });
    await clientOption.first().click({ timeout: 10000 });

    // Verify client is selected (shown as a badge, not the search input)
    await expect(page.getByText("E2E ZaakClient B.V.")).toBeVisible();

    // Submit
    await page.getByRole("button", { name: "Dossier aanmaken" }).click();

    // Wait for redirect to detail page (UUID in URL)
    await page.waitForURL(/\/zaken\/[a-f0-9-]+$/, { timeout: 30000 });

    // Extract case ID from URL
    caseId = page.url().split("/zaken/")[1];

    // Case number should be visible in the h1
    await expect(page.locator("h1").first()).toBeVisible({ timeout: 10000 });

    // Toast notification
    await expect(page.getByText("Dossier aangemaakt")).toBeVisible({
      timeout: 5000,
    });
  });

  test("Z4: detail page loads with case info", async ({ page }) => {
    test.skip(!caseId, "Z3 must create a case first");

    await page.goto(`/zaken/${caseId}`);
    await page.waitForLoadState("domcontentloaded");

    // Case number visible in h1 (format: YYYY-NNNNN)
    await expect(page.locator("h1").first()).toContainText(/\d{4}-\d+/, {
      timeout: 15000,
    });

    // Status badge "Nieuw" should be visible
    await expect(page.getByText("Nieuw").first()).toBeVisible();

    // Client name should be visible somewhere on the page
    await expect(page.getByText("E2E ZaakClient B.V.").first()).toBeVisible({
      timeout: 5000,
    });
  });

  test("Z5: 7 tabs visible on detail page (non-incasso)", async ({ page }) => {
    test.skip(!caseId, "Z3 must create a case first");

    await page.goto(`/zaken/${caseId}`);
    await page.waitForLoadState("domcontentloaded");

    // Wait for page to load
    await expect(page.locator("h1").first()).toContainText(/\d{4}-\d+/, {
      timeout: 15000,
    });

    // Check all 7 tabs for non-incasso case
    const expectedTabs = [
      "Overzicht",
      "Taken",
      "Facturen",
      "Documenten",
      "Correspondentie",
      "Activiteiten",
      "Partijen",
    ];

    for (const tabLabel of expectedTabs) {
      await expect(
        page.getByRole("button", { name: tabLabel })
      ).toBeVisible();
    }

    // Incasso-specific tabs should NOT be visible
    const incassoOnlyTabs = [
      "Vorderingen",
      "Betalingen",
      "Financieel",
      "Derdengelden",
    ];
    for (const tabLabel of incassoOnlyTabs) {
      await expect(
        page.getByRole("button", { name: tabLabel })
      ).not.toBeVisible();
    }
  });

  test("Z6: edit case description via detail page", async ({ page }) => {
    test.skip(!caseId, "Z3 must create a case first");

    await page.goto(`/zaken/${caseId}`);
    await page.waitForLoadState("domcontentloaded");

    // Wait for detail page
    await expect(page.locator("h1").first()).toContainText(/\d{4}-\d+/, {
      timeout: 15000,
    });

    // Click "Bewerken" button
    await page.getByRole("button", { name: /Bewerken/ }).click();

    // Fill in description textarea
    const descriptionField = page.getByPlaceholder(
      "Korte omschrijving van het dossier..."
    );
    await descriptionField.fill("E2E test beschrijving");

    // Click "Opslaan" (first match — the edit form's save button)
    await page.getByRole("button", { name: /Opslaan/ }).first().click();

    // Verify edit succeeded: description visible + back to view mode (Bewerken button returns)
    await expect(page.getByText("E2E test beschrijving")).toBeVisible({
      timeout: 10000,
    });
    await expect(
      page.getByRole("button", { name: /Bewerken/ })
    ).toBeVisible();
  });

  test("Z7: change case status", async ({ page, request }) => {
    test.skip(!caseId, "Z3 must create a case first");

    // Change status via API (workflow transition: nieuw → herinnering)
    await updateCaseStatus(request, authToken, caseId, "herinnering");

    // Navigate to detail page and verify badge
    await page.goto(`/zaken/${caseId}`);
    await page.waitForLoadState("domcontentloaded");

    await expect(page.locator("h1").first()).toContainText(/\d{4}-\d+/, {
      timeout: 15000,
    });

    // Status badge should show "Herinnering"
    await expect(page.getByText("Herinnering").first()).toBeVisible({
      timeout: 5000,
    });
  });

  test("Z8: delete case via detail page", async ({ page }) => {
    test.skip(!caseId, "Z3 must create a case first");

    await page.goto(`/zaken/${caseId}`);
    await page.waitForLoadState("domcontentloaded");

    await expect(page.locator("h1").first()).toContainText(/\d{4}-\d+/, {
      timeout: 15000,
    });

    // Register dialog handler BEFORE clicking delete
    page.on("dialog", (dialog) => dialog.accept());

    // Click delete button (Trash2 icon with title "Verwijderen")
    await page.getByTitle("Verwijderen").click({ force: true });

    // Should redirect to zaken list
    await page.waitForURL("**/zaken", { timeout: 10000 });

    // Toast should confirm deletion
    await expect(page.getByText("Dossier verwijderd")).toBeVisible({
      timeout: 5000,
    });

    // Mark as cleaned up so afterAll doesn't try to delete again
    caseId = "";
  });
});
