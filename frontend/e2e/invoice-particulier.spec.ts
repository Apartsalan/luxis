/**
 * S166 punt 1 — Particulier-naam auto-invullen in wederpartij.
 *
 * Bij een factuur van een particulier geeft de parser de naam soms terug in
 * debtor_contact_person (de persoon/t.a.v.) terwijl debtor_name leeg is. De wizard
 * moet dan tóch de wederpartij-naam invullen. We mocken de AI-parse + de relaties-
 * zoekopdracht zodat de test deterministisch is (geen AI-call, geen afhankelijkheid
 * van bestaande relaties). Auth via storageState (setup-project).
 */

import { test, expect } from "@playwright/test";

// Particulier: geen handels-/bedrijfsnaam (debtor_name = null), naam in contact_person.
const PARTICULIER_PARSE = {
  debtor_name: null,
  debtor_contact_person: "Jan Jansen",
  debtor_type: "person",
  debtor_address: "Hoofdstraat 12",
  debtor_postcode: "1234 AB",
  debtor_city: "Amsterdam",
  debtor_postal_address: null,
  debtor_postal_postcode: null,
  debtor_postal_city: null,
  debtor_kvk: null,
  debtor_email: "jan.jansen@example.nl",
  creditor_name: "Acme B.V.",
  creditor_contact_person: null,
  creditor_type: "company",
  creditor_address: null,
  creditor_postcode: null,
  creditor_city: null,
  creditor_postal_address: null,
  creditor_postal_postcode: null,
  creditor_postal_city: null,
  creditor_kvk: "12345678",
  creditor_btw: null,
  creditor_email: null,
  invoice_number: "2026-001",
  invoice_date: "2026-01-01",
  due_date: "2026-01-15",
  principal_amount: 500.0,
  description: "Onbetaalde factuur",
  confidence: {},
  model: "test-mock",
};

const EMPTY_RELATIONS = {
  items: [],
  total: 0,
  page: 1,
  per_page: 5,
  pages: 0,
};

test.describe("Factuur-upload particulier (S166 punt 1)", () => {
  test("particulier-naam wordt automatisch in de wederpartij gezet", async ({
    page,
  }) => {
    // Mock de AI-parse (deterministisch particulier-resultaat).
    await page.route("**/api/ai-agent/parse-invoice", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify(PARTICULIER_PARSE),
      });
    });
    // Mock de relaties-zoeklijst (leeg → geen auto-match, nieuwe-relatie-form opent
    // voor-ingevuld). Alleen de zoek-lijst (met querystring), niet /api/relations/{id}.
    await page.route(/\/api\/relations\?/, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify(EMPTY_RELATIONS),
      });
    });

    await page.goto("/zaken/nieuw");
    await expect(
      page.locator("h1").filter({ hasText: "Nieuw dossier" })
    ).toBeVisible({ timeout: 15000 });

    // Upload een dummy-PDF — de inhoud doet er niet toe, de parse is gemockt.
    // De eerste file-input op de pagina is de InvoiceUploadZone bovenaan (de tweede
    // is de per-vordering upload in stap 3).
    const fileInput = page
      .locator('input[type="file"][accept="application/pdf"]')
      .first();
    await fileInput.setInputFiles({
      name: "factuur.pdf",
      mimeType: "application/pdf",
      buffer: Buffer.from("%PDF-1.4\n% test invoice\n"),
    });

    // Parse klaar → succes-status.
    await expect(page.getByText(/velden ingevuld/)).toBeVisible({
      timeout: 15000,
    });

    // Debiteurtype is automatisch op B2C (particulier) gezet.
    await expect(page.locator("#debiteurtype")).toHaveValue("b2c");

    // Naar stap 2 (Partijen).
    await page.getByRole("button", { name: /Volgende/ }).click();

    // Kern van de fix: de wederpartij-naam is automatisch ingevuld met de
    // particulier-naam (voorheen bleef dit veld leeg omdat debtor_name null was).
    await expect(page.locator("#wederpartij-zoeken")).toHaveValue("Jan Jansen", {
      timeout: 10000,
    });
  });
});
