/**
 * Mobiele overloop-wachter (skill breed-testen — fout-SOORT: pagina breder dan
 * het scherm). Loopt alle vaste routes af op telefoon (390) én tablet (820) en
 * eist dat de pagina niet horizontaal scrollt. Elke toekomstige brede pagina
 * valt hierop, niet pas als een gebruiker het meldt.
 *
 * Detailpagina's (met dynamische id's) staan hier niet: ze delen dezelfde
 * componenten als de lijst-/formulierroutes die wél gedekt zijn.
 */

import { test, expect } from "@playwright/test";

const ROUTES = [
  "/",
  "/zaken",
  "/zaken/nieuw",
  "/relaties",
  "/incasso",
  "/followup",
  "/correspondentie",
  "/agenda",
  "/taken",
  "/betalingen",
  "/derdengelden",
  "/uren",
  "/facturen",
  "/rapportages",
  "/intake",
  "/instellingen",
];

const WIDTHS = [
  { label: "telefoon", width: 390, height: 844 },
  { label: "tablet", width: 820, height: 1180 },
];

for (const { label, width, height } of WIDTHS) {
  test.describe(`geen horizontale overloop — ${label} (${width}px)`, () => {
    for (const route of ROUTES) {
      test(`${route}`, async ({ page }) => {
        await page.setViewportSize({ width, height });
        await page.goto(route);
        // Wacht tot de app-shell staat (header aanwezig).
        await page.waitForLoadState("networkidle");

        const { scrollWidth, clientWidth } = await page.evaluate(() => ({
          scrollWidth: document.documentElement.scrollWidth,
          clientWidth: document.documentElement.clientWidth,
        }));

        // 2px marge voor sub-pixel afronding.
        expect(
          scrollWidth,
          `${route} scrollt horizontaal op ${label}: scrollWidth=${scrollWidth} > clientWidth=${clientWidth}`
        ).toBeLessThanOrEqual(clientWidth + 2);
      });
    }
  });
}
