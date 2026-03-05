/**
 * Facturen (Invoices) E2E Tests — Luxis
 *
 * Tests the invoice lifecycle: list, create, detail, approve, send,
 * payment registration, and delete. Tests are sequential.
 * Auth is provided by storageState (setup project).
 */

import { test, expect } from "@playwright/test";
import { loginViaApi } from "./helpers/auth";
import {
  createContact,
  deleteContact,
  createCase,
  deleteCase,
  createInvoice,
  deleteInvoice,
} from "./helpers/api";

let authToken = "";
let clientId = "";
let caseId = "";
let invoiceId = "";
let deleteTestInvoiceId = "";

test.describe("Facturen CRUD", () => {
  test.beforeAll(async ({ request }) => {
    const { accessToken } = await loginViaApi(request);
    authToken = accessToken;

    const client = await createContact(request, authToken, {
      contact_type: "company",
      name: "E2E FactuurClient B.V.",
      email: "e2e-factuur@test.nl",
    });
    clientId = client.id;

    const zaak = await createCase(request, authToken, {
      case_type: "advies",
      client_id: clientId,
    });
    caseId = zaak.id;
  });

  test.afterAll(async ({ request }) => {
    if (invoiceId) {
      await deleteInvoice(request, authToken, invoiceId).catch(() => {});
    }
    if (deleteTestInvoiceId) {
      await deleteInvoice(request, authToken, deleteTestInvoiceId).catch(
        () => {}
      );
    }
    if (caseId) {
      await deleteCase(request, authToken, caseId).catch(() => {});
    }
    if (clientId) {
      await deleteContact(request, authToken, clientId).catch(() => {});
    }
  });

  test("F1: facturen list page loads with UI elements", async ({ page }) => {
    await page.goto("/facturen");

    // Page heading
    await expect(
      page.locator("h1").filter({ hasText: "Facturen" })
    ).toBeVisible({ timeout: 15000 });

    // "Nieuwe factuur" button
    await expect(
      page.getByRole("link", { name: /Nieuwe factuur/ })
    ).toBeVisible();

    // Search input
    await expect(
      page.getByPlaceholder(/Zoek op factuurnummer/)
    ).toBeVisible();
  });

  test("F2: create invoice via form", async ({ page }) => {
    test.setTimeout(60000);
    await page.goto("/facturen/nieuw");
    await page.waitForLoadState("domcontentloaded");

    await expect(
      page.locator("h1").filter({ hasText: "Nieuwe factuur" })
    ).toBeVisible({ timeout: 15000 });

    // Search and select relatie
    await page.getByPlaceholder("Zoek relatie...").fill("E2E FactuurClient");
    const clientOption = page.locator("button", {
      hasText: "E2E FactuurClient B.V.",
    });
    await clientOption.first().click({ timeout: 10000 });

    // Verify relatie is selected (name is in the input value)
    await expect(page.getByPlaceholder("Zoek relatie...")).toHaveValue(
      /E2E FactuurClient/
    );

    // Fill first invoice line (quantity defaults to 1)
    await page
      .getByPlaceholder("Omschrijving")
      .first()
      .fill("E2E juridische werkzaamheden");
    await page.getByPlaceholder("0.00").first().fill("500");

    // Submit
    await page
      .getByRole("button", { name: "Factuur aanmaken" })
      .click({ force: true });

    // Wait for redirect to detail page
    await page.waitForURL(/\/facturen\/[a-f0-9-]+$/, { timeout: 30000 });
    invoiceId = page.url().split("/facturen/")[1];

    // Toast
    await expect(page.getByText("Factuur aangemaakt")).toBeVisible({
      timeout: 5000,
    });
  });

  test("F3: detail page shows invoice info", async ({ page }) => {
    test.skip(!invoiceId, "F2 must create an invoice first");

    await page.goto(`/facturen/${invoiceId}`);
    await page.waitForLoadState("domcontentloaded");

    // Invoice number visible in header
    await expect(page.locator("h1").first()).toBeVisible({ timeout: 15000 });

    // Status badge "Concept"
    await expect(page.getByText("Concept").first()).toBeVisible();

    // Contact name visible
    await expect(
      page.getByText("E2E FactuurClient B.V.").first()
    ).toBeVisible({ timeout: 5000 });

    // Line description visible
    await expect(
      page.getByText("E2E juridische werkzaamheden")
    ).toBeVisible();
  });

  test("F4: approve invoice (concept → goedgekeurd)", async ({ page }) => {
    test.skip(!invoiceId, "F2 must create an invoice first");

    await page.goto(`/facturen/${invoiceId}`);
    await page.waitForLoadState("domcontentloaded");
    await expect(page.locator("h1").first()).toBeVisible({ timeout: 15000 });

    // Click approve button
    await page
      .getByRole("button", { name: /Goedkeuren/ })
      .click({ force: true });

    // Toast
    await expect(page.getByText("Factuur goedgekeurd")).toBeVisible({
      timeout: 5000,
    });

    // Badge changes
    await expect(page.getByText("Goedgekeurd").first()).toBeVisible({
      timeout: 5000,
    });
  });

  test("F5: send invoice (goedgekeurd → verzonden)", async ({ page }) => {
    test.skip(!invoiceId, "F4 must approve first");

    await page.goto(`/facturen/${invoiceId}`);
    await page.waitForLoadState("domcontentloaded");
    await expect(page.locator("h1").first()).toBeVisible({ timeout: 15000 });

    // Click send button
    await page
      .getByRole("button", { name: /Verzenden/ })
      .click({ force: true });

    // Toast
    await expect(
      page.getByText("Factuur gemarkeerd als verzonden")
    ).toBeVisible({ timeout: 5000 });

    // Badge changes
    await expect(page.getByText("Verzonden").first()).toBeVisible({
      timeout: 5000,
    });
  });

  test("F6: register payment on sent invoice", async ({ page }) => {
    test.skip(!invoiceId, "F5 must send first");
    test.setTimeout(60000);

    await page.goto(`/facturen/${invoiceId}`);
    await page.waitForLoadState("domcontentloaded");
    await expect(page.locator("h1").first()).toBeVisible({ timeout: 15000 });

    // Wait for payment section to be visible (only on sent+ invoices)
    await expect(
      page.getByRole("heading", { name: "Betalingen" })
    ).toBeVisible({ timeout: 10000 });

    // Open payment form
    await page
      .getByRole("button", { name: /Betaling registreren/ })
      .click({ force: true });

    // Fill amount (500 + 21% BTW = 605) — labels aren't <label> elements
    // The payment form's spinbutton is the only one visible on this page
    await page.getByRole("spinbutton").fill("605");

    // Method defaults to "Bankoverschrijving", date to today — no changes needed

    // Submit — toggle button is first, form submit is last
    await page
      .getByRole("button", { name: /Betaling registreren/ })
      .last()
      .click({ force: true });

    // Toast
    await expect(page.getByText("Betaling geregistreerd")).toBeVisible({
      timeout: 5000,
    });
  });

  test("F7: delete concept invoice", async ({ page, request }) => {
    // Create a separate concept invoice via API for deletion test
    const inv = await createInvoice(request, authToken, {
      contact_id: clientId,
      lines: [
        {
          description: "Te verwijderen regel",
          quantity: "1",
          unit_price: "100.00",
        },
      ],
    });
    deleteTestInvoiceId = inv.id;

    await page.goto(`/facturen/${deleteTestInvoiceId}`);
    await page.waitForLoadState("domcontentloaded");
    await expect(page.locator("h1").first()).toBeVisible({ timeout: 15000 });

    // Register dialog handler before clicking delete
    page.on("dialog", (dialog) => dialog.accept());

    // Click delete button (first one = header, second = line)
    await page.getByTitle("Verwijderen").first().click({ force: true });

    // Should redirect to facturen list
    await page.waitForURL("**/facturen", { timeout: 10000 });

    // Toast
    await expect(page.getByText("Factuur verwijderd")).toBeVisible({
      timeout: 5000,
    });

    deleteTestInvoiceId = "";
  });
});
