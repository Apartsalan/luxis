/**
 * Tijdregistratie (Time Entries) E2E Tests — Luxis
 *
 * Tests time entry lifecycle: page load, create, verify in table,
 * inline edit, and delete. Tests are sequential.
 * Auth is provided by storageState (setup project).
 */

import { test, expect } from "@playwright/test";
import { loginViaApi } from "./helpers/auth";
import {
  createContact,
  deleteContact,
  createCase,
  deleteCase,
  deleteTimeEntry,
} from "./helpers/api";

let authToken = "";
let clientId = "";
let caseId = "";
let caseNumber = "";
let timeEntryId = "";

test.describe("Tijdregistratie CRUD", () => {
  test.beforeAll(async ({ request }) => {
    const { accessToken } = await loginViaApi(request);
    authToken = accessToken;

    const client = await createContact(request, authToken, {
      contact_type: "company",
      name: "E2E UrenClient B.V.",
      email: "e2e-uren@test.nl",
    });
    clientId = client.id;

    const zaak = await createCase(request, authToken, {
      case_type: "advies",
      client_id: clientId,
    });
    caseId = zaak.id;
    caseNumber = zaak.case_number;
  });

  test.afterAll(async ({ request }) => {
    if (timeEntryId) {
      await deleteTimeEntry(request, authToken, timeEntryId).catch(() => {});
    }
    if (caseId) {
      await deleteCase(request, authToken, caseId).catch(() => {});
    }
    if (clientId) {
      await deleteContact(request, authToken, clientId).catch(() => {});
    }
  });

  test("T1: uren page loads with UI elements", async ({ page }) => {
    await page.goto("/uren");

    // Page heading
    await expect(
      page.locator("h1").filter({ hasText: "Urenregistratie" })
    ).toBeVisible({ timeout: 15000 });

    // "Nieuwe registratie" button
    await expect(
      page.getByRole("button", { name: /Nieuwe registratie/ })
    ).toBeVisible();

    // Stopwatch card
    await expect(page.getByText("Stopwatch")).toBeVisible();

    // Week navigation — "Deze week" button
    await expect(
      page.getByRole("button", { name: /Deze week/ })
    ).toBeVisible();
  });

  test("T2: create time entry via form", async ({ page }) => {
    test.setTimeout(60000);
    await page.goto("/uren");
    await page.waitForLoadState("domcontentloaded");

    await expect(
      page.locator("h1").filter({ hasText: "Urenregistratie" })
    ).toBeVisible({ timeout: 15000 });

    // Open new entry form
    await page
      .getByRole("button", { name: /Nieuwe registratie/ })
      .click({ force: true });

    // Wait for form to appear
    await expect(page.getByPlaceholder("Wat heb je gedaan?")).toBeVisible({
      timeout: 5000,
    });

    // Select case via CaseSelector (custom dropdown)
    // The form's CaseSelector button says "Selecteer dossier..."
    await page
      .getByRole("button", { name: /Selecteer dossier/ })
      .last()
      .click({ force: true });

    // Search for case in the dropdown popover
    await page.getByPlaceholder(/Zoek/).last().fill(caseNumber);

    // Click matching case
    await page
      .locator("button")
      .filter({ hasText: caseNumber })
      .first()
      .click({ force: true, timeout: 10000 });

    // Fill duration: 1 hour 30 minutes
    await page.getByPlaceholder("uur").last().fill("1");
    await page.getByPlaceholder("min").last().fill("30");

    // Select activity type — label isn't a proper <label>, use combobox role
    // First combobox is the filter (Alle typen), second is the form's activity
    await page.getByRole("combobox").last().selectOption("Onderzoek");

    // Fill description
    await page
      .getByPlaceholder("Wat heb je gedaan?")
      .fill("E2E test onderzoek werkzaamheden");

    // Submit
    await page
      .getByRole("button", { name: /^Opslaan$/ })
      .click({ force: true });

    // Toast
    await expect(page.getByText("Tijdregistratie opgeslagen")).toBeVisible({
      timeout: 5000,
    });
  });

  test("T3: entry appears in table with correct data", async ({ page }) => {
    await page.goto("/uren");
    await page.waitForLoadState("domcontentloaded");

    await expect(
      page.locator("h1").filter({ hasText: "Urenregistratie" })
    ).toBeVisible({ timeout: 15000 });

    // Wait for entries to load
    await expect(
      page.getByText("E2E test onderzoek werkzaamheden").first()
    ).toBeVisible({ timeout: 10000 });

    // Case number visible
    await expect(page.getByText(caseNumber).first()).toBeVisible();

    // Duration "1:30" visible
    await expect(page.getByText("1:30").first()).toBeVisible();

    // Billable badge "Ja"
    await expect(page.getByText("Ja").first()).toBeVisible();
  });

  test("T4: edit time entry inline", async ({ page }) => {
    await page.goto("/uren");
    await page.waitForLoadState("domcontentloaded");

    await expect(
      page.locator("h1").filter({ hasText: "Urenregistratie" })
    ).toBeVisible({ timeout: 15000 });

    // Wait for the entry to appear
    await expect(
      page.getByText("E2E test onderzoek werkzaamheden").first()
    ).toBeVisible({ timeout: 10000 });

    // Click the edit button
    await page
      .getByRole("button", { name: "Bewerken" })
      .first()
      .click({ force: true });

    // Description should now be an editable input
    const descInput = page.locator('input[type="text"]').first();
    await expect(descInput).toBeVisible({ timeout: 5000 });
    await descInput.clear();
    await descInput.fill("E2E gewijzigde omschrijving");

    // Click save button (appears in edit mode)
    await page
      .getByRole("button", { name: /Opslaan/ })
      .first()
      .click({ force: true });

    // Toast
    await expect(page.getByText("Bijgewerkt")).toBeVisible({ timeout: 5000 });

    // New description visible
    await expect(page.getByText("E2E gewijzigde omschrijving")).toBeVisible();
  });

  test("T5: delete time entry", async ({ page }) => {
    await page.goto("/uren");
    await page.waitForLoadState("domcontentloaded");

    await expect(
      page.locator("h1").filter({ hasText: "Urenregistratie" })
    ).toBeVisible({ timeout: 15000 });

    // Wait for the entry (with updated description from T4)
    await expect(
      page.getByText("E2E gewijzigde omschrijving")
    ).toBeVisible({ timeout: 10000 });

    // Register dialog handler just in case
    page.on("dialog", (dialog) => dialog.accept());

    // Click the delete button (only one entry exists)
    await page
      .getByRole("button", { name: "Verwijderen" })
      .first()
      .click({ force: true });

    // Toast
    await expect(page.getByText("Verwijderd")).toBeVisible({ timeout: 5000 });

    // Entry should no longer be visible
    await expect(
      page.getByText("E2E gewijzigde omschrijving")
    ).not.toBeVisible({ timeout: 5000 });

    // Mark as cleaned up
    timeEntryId = "";
  });
});
