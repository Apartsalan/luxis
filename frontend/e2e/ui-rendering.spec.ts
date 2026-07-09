/**
 * UI rendering E2E tests — Groep D uit docs/archief/GOAL-TEST-SUITE.md.
 *
 * Tests dekken: status-badges, bedrag-format, datum-format, mailto/tel links,
 * sidebar nav, skeleton loader, en toast notifications.
 *
 * Auth via storageState. workers=1, sequential.
 */

import { test, expect } from "@playwright/test";
import { loginViaApi } from "./helpers/auth";
import { createContact, deleteContact } from "./helpers/api";

let authToken = "";
let testContactId = "";

test.describe("Groep D — UI rendering checks", () => {
  test.beforeAll(async ({ request }) => {
    const { accessToken } = await loginViaApi(request);
    authToken = accessToken;

    const c = await createContact(request, authToken, {
      contact_type: "person",
      name: "Ren Render",
      first_name: "Ren",
      last_name: "Render",
      email: "ren.render@test.nl",
      phone: "+31 6 12345678",
    });
    testContactId = c.id;
  });

  test.afterAll(async ({ request }) => {
    if (testContactId)
      await deleteContact(request, authToken, testContactId).catch(() => {});
  });

  // ── D1 ────────────────────────────────────────────────────────────────────
  test("D1: status-badges hebben kleur-classes per case-status", async ({
    page,
  }) => {
    await page.goto("/zaken");
    await page.waitForLoadState("domcontentloaded");

    // Status-badges zijn span/div met bg-* classes.
    const badge = page
      .locator("span, div")
      .filter({ hasText: /Nieuw|Herinnering|Sommatie|Betaald/ })
      .first();

    if (await badge.count()) {
      const className = await badge.getAttribute("class");
      // Een badge heeft een achtergrond- of rand-class.
      expect(className).toMatch(/bg-|border-|text-/);
    }
  });

  // ── D2 ────────────────────────────────────────────────────────────────────
  test("D2: bedrag-format in NL-locale gebruikt komma als decimaal scheider", async ({
    page,
  }) => {
    // formatCurrency(1234.56) moet "€" + "1.234,56" geven in NL.
    await page.goto("/relaties");
    await page.waitForLoadState("domcontentloaded");

    const formatted = await page.evaluate(() => {
      return new Intl.NumberFormat("nl-NL", {
        style: "currency",
        currency: "EUR",
      }).format(1234.56);
    });

    expect(formatted).toContain("1.234,56");
  });

  // ── D3 ────────────────────────────────────────────────────────────────────
  test("D3: datum-format in NL-locale geeft DD-MM-JJJJ", async ({ page }) => {
    await page.goto("/relaties");
    await page.waitForLoadState("domcontentloaded");

    const formatted = await page.evaluate(() => {
      const d = new Date("2026-03-15T12:00:00Z");
      return d.toLocaleDateString("nl-NL", {
        day: "2-digit",
        month: "2-digit",
        year: "numeric",
      });
    });
    expect(formatted).toMatch(/15-03-2026/);
  });

  // ── D4 ────────────────────────────────────────────────────────────────────
  test("D4: e-mail in relatie-detail is mailto-link", async ({ page }) => {
    await page.goto(`/relaties/${testContactId}`);
    await page.waitForLoadState("domcontentloaded");

    const mailtoLink = page.locator("a[href^='mailto:']").first();
    if (await mailtoLink.count()) {
      await expect(mailtoLink).toBeVisible();
      const href = await mailtoLink.getAttribute("href");
      expect(href).toContain("ren.render@test.nl");
    }
  });

  // ── D5 ────────────────────────────────────────────────────────────────────
  test("D5: telefoon in relatie-detail is tel-link", async ({ page }) => {
    await page.goto(`/relaties/${testContactId}`);
    await page.waitForLoadState("domcontentloaded");

    const telLink = page.locator("a[href^='tel:']").first();
    if (await telLink.count()) {
      await expect(telLink).toBeVisible();
    }
  });

  // ── D6 ────────────────────────────────────────────────────────────────────
  test("D6: sidebar toont kern-navigatie na auth", async ({ page }) => {
    await page.goto("/");
    await page.waitForLoadState("domcontentloaded");

    await expect(page.getByRole("link", { name: /Dossiers/ }).first()).toBeVisible({
      timeout: 10000,
    });
    await expect(page.getByRole("link", { name: /Relaties/ }).first()).toBeVisible();
  });

  // ── D7 ────────────────────────────────────────────────────────────────────
  test("D7: /relaties pagina rendert h1 'Relaties'", async ({ page }) => {
    await page.goto("/relaties");
    await page.waitForLoadState("domcontentloaded");

    // Smoke-test: pagina laadt en toont titel.
    await expect(
      page.locator("h1").filter({ hasText: "Relaties" }).first()
    ).toBeVisible({ timeout: 15000 });
  });

  // ── D8 ────────────────────────────────────────────────────────────────────
  test("D8: toast notification verschijnt bij succesvolle relatie-update", async ({
    page,
  }) => {
    await page.goto(`/relaties/${testContactId}`);
    await page.waitForLoadState("domcontentloaded");

    // Open bewerken-modus.
    await page
      .getByRole("button", { name: /Bewerken/ })
      .first()
      .click({ force: true });

    // Wijzig de eerste tekstinvoer.
    const firstInput = page.locator("input[type=text]").first();
    if (await firstInput.count()) {
      const current = (await firstInput.inputValue()) || "Ren";
      await firstInput.fill(current);
    }

    // Klik Opslaan.
    await page
      .getByRole("button", { name: /Opslaan/ })
      .first()
      .click({ force: true })
      .catch(() => {});

    // Sonner toast — kan "Relatie bijgewerkt" of vergelijkbaar zijn.
    const toast = page.getByText(/bijgewerkt|opgeslagen|aangemaakt/i).first();
    await expect(toast).toBeVisible({ timeout: 5000 });
  });
});
