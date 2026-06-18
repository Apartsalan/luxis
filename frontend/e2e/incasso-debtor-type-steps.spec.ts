/**
 * S166 punt 4a (+ punt 3) — incassostap-dropdown loopt mee met het debiteurtype.
 *
 * Een B2C-dossier toont de 14-dagenbrief en NIET de B2B-only faillissement-stappen;
 * een B2B-dossier andersom. Tevens: een nieuw B2C-dossier start automatisch op de
 * 14-dagenbrief (debtor-aware initiële stap in create_case).
 *
 * Vereist dat de tenant de pipeline-stappen heeft (seed/migratie S166). Auth via
 * storageState (setup-project); cases worden direct via de backend-API geseed.
 */

import { test, expect } from "@playwright/test";
import { loginViaApi } from "./helpers/auth";
import { createContact, deleteContact, deleteCase } from "./helpers/api";

const API_URL = "http://localhost:8000";

let token = "";
let clientId = "";
const caseIds: string[] = [];

async function createIncassoCase(
  request: import("@playwright/test").APIRequestContext,
  debtorType: "b2b" | "b2c"
): Promise<string> {
  const res = await request.post(`${API_URL}/api/cases`, {
    headers: { Authorization: `Bearer ${token}` },
    data: {
      case_type: "incasso",
      client_id: clientId,
      debtor_type: debtorType,
      interest_type: "statutory",
      date_opened: new Date().toISOString().split("T")[0],
    },
  });
  if (!res.ok()) {
    throw new Error(`Create case failed: ${res.status()} ${await res.text()}`);
  }
  const body = await res.json();
  caseIds.push(body.id);
  return body.id;
}

test.describe("Incassostap-dropdown per debiteurtype (S166 punt 4a + 3)", () => {
  test.beforeAll(async ({ request }) => {
    const { accessToken } = await loginViaApi(request);
    token = accessToken;
    const client = await createContact(request, token, {
      contact_type: "company",
      name: "E2E Stappen Client B.V.",
      email: "e2e-stappen-client@test.nl",
    });
    clientId = client.id;
  });

  test.afterAll(async ({ request }) => {
    for (const id of caseIds) {
      await deleteCase(request, token, id).catch(() => {});
    }
    if (clientId) await deleteContact(request, token, clientId).catch(() => {});
  });

  test("B2C-dossier: 14-dagenbrief wél, faillissement niet — en start op 14-dagenbrief", async ({
    page,
    request,
  }) => {
    const id = await createIncassoCase(request, "b2c");
    await page.goto(`/zaken/${id}`);

    // De incassostap-selector (herkenbaar aan de "Niet toegewezen"-optie) is zichtbaar.
    const stepSelect = page
      .locator("select")
      .filter({ has: page.locator('option', { hasText: "Niet toegewezen" }) });
    await expect(stepSelect).toBeVisible({ timeout: 15000 });

    // B2C ziet de 14-dagenbrief, niet de B2B-only faillissement-stap.
    await expect(
      stepSelect.locator("option", { hasText: "14-dagenbrief" })
    ).toHaveCount(1);
    await expect(
      stepSelect.locator("option", { hasText: "Verzoekschrift faillissement" })
    ).toHaveCount(0);

    // Punt 3: een nieuw B2C-dossier start op de 14-dagenbrief.
    const selectedLabel = await stepSelect
      .locator("option:checked")
      .textContent();
    expect(selectedLabel?.trim()).toBe("14-dagenbrief");
  });

  test("B2B-dossier: faillissement wél, 14-dagenbrief niet", async ({
    page,
    request,
  }) => {
    const id = await createIncassoCase(request, "b2b");
    await page.goto(`/zaken/${id}`);

    const stepSelect = page
      .locator("select")
      .filter({ has: page.locator('option', { hasText: "Niet toegewezen" }) });
    await expect(stepSelect).toBeVisible({ timeout: 15000 });

    await expect(
      stepSelect.locator("option", { hasText: "Verzoekschrift faillissement" })
    ).toHaveCount(1);
    await expect(
      stepSelect.locator("option", { hasText: "14-dagenbrief" })
    ).toHaveCount(0);
  });
});
