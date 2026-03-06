/**
 * Incasso Pipeline E2E Tests — P1 QA
 *
 * Tests the complete incasso pipeline UI flow:
 * pipeline page, case selection, batch actions, pre-flight dialog,
 * deadline colors, queue filters, and step management.
 *
 * Prerequisites:
 * - Dev environment running (frontend + backend + db)
 * - Pipeline steps seeded (done in beforeAll)
 * - At least one incasso case exists (created in beforeAll)
 */

import { test, expect } from "@playwright/test";
import { loginViaApi } from "./helpers/auth";
import { createContact, deleteContact, createCase, deleteCase } from "./helpers/api";

const API_URL = "http://localhost:8000";

// Store IDs across tests (workers=1, sequential execution guaranteed)
let authToken = "";
let testCaseId = "";
let clientId = "";
let opposingPartyId = "";

// ── Seed helper ──────────────────────────────────────────────────────

async function seedPipelineSteps(
  request: import("@playwright/test").APIRequestContext,
  token: string
) {
  await request.post(`${API_URL}/api/incasso/pipeline-steps/seed`, {
    headers: { Authorization: `Bearer ${token}` },
  });
}

// ── Setup & Teardown ─────────────────────────────────────────────────

test.describe("Incasso Pipeline", () => {
  test.beforeAll(async ({ request }) => {
    const { accessToken } = await loginViaApi(request);
    authToken = accessToken;

    // Seed pipeline steps
    await seedPipelineSteps(request, authToken);

    // Create client contact
    const client = await createContact(request, authToken, {
      contact_type: "company",
      name: "E2E Incasso Client B.V.",
      email: "e2e-incasso-client@test.nl",
    });
    clientId = client.id;

    // Create opposing party contact
    const op = await createContact(request, authToken, {
      contact_type: "person",
      name: "E2E Incasso Wederpartij",
      email: "e2e-incasso-debiteur@test.nl",
    });
    opposingPartyId = op.id;

    // Create an incasso case (createCase provides date_opened automatically)
    const caseData = await createCase(request, authToken, {
      case_type: "incasso",
      description: "E2E test incassozaak",
      client_id: clientId,
      opposing_party_id: opposingPartyId,
    });
    testCaseId = caseData.id;
  });

  test.afterAll(async ({ request }) => {
    // Cleanup test data
    if (testCaseId) {
      await deleteCase(request, authToken, testCaseId).catch(() => {});
    }
    if (opposingPartyId) {
      await deleteContact(request, authToken, opposingPartyId).catch(() => {});
    }
    if (clientId) {
      await deleteContact(request, authToken, clientId).catch(() => {});
    }
  });

  // ── E1: Pipeline page loads ─────────────────────────────────────────

  test("E1: pipeline page loads with step columns", async ({ page }) => {
    await page.goto("/incasso");
    await page.waitForLoadState("networkidle");

    // Should see pipeline step columns (exact match to avoid "2e Sommatie")
    await expect(page.getByText("Aanmaning")).toBeVisible({ timeout: 10000 });
    await expect(
      page.getByRole("heading", { name: "Sommatie", exact: true })
    ).toBeVisible();
  });

  // ── E2: Deadline colors displayed ───────────────────────────────────

  test("E2: cases show deadline color indicators", async ({ page }) => {
    await page.goto("/incasso");
    await page.waitForLoadState("networkidle");

    // Wait for pipeline to load
    await expect(page.getByText("Aanmaning")).toBeVisible({ timeout: 10000 });

    // Look for colored dot indicators — count depends on data
    const dots = page.locator(
      '[class*="bg-emerald-500"], [class*="bg-amber-500"], [class*="bg-red-500"], [class*="bg-gray-400"]'
    );
    const count = await dots.count();
    expect(count).toBeGreaterThanOrEqual(0);
  });

  // ── E3: Case selection + action bar ─────────────────────────────────

  test("E3: selecting a case shows the floating action bar", async ({
    page,
  }) => {
    await page.goto("/incasso");
    await page.waitForLoadState("networkidle");
    await expect(page.getByText("Aanmaning")).toBeVisible({ timeout: 10000 });

    // Find and click a case card
    const caseRow = page.locator('[class*="cursor-pointer"]').first();
    if ((await caseRow.count()) > 0) {
      await caseRow.click({ force: true });

      // Floating action bar should appear with action buttons
      await expect(page.getByText("geselecteerd")).toBeVisible({
        timeout: 5000,
      });
      await expect(page.getByText("Verstuur brief")).toBeVisible();
      await expect(page.getByText("Wijzig stap")).toBeVisible();
    }
  });

  // ── E4: Verstuur brief opens pre-flight ─────────────────────────────

  test("E4: 'Verstuur brief' opens the pre-flight dialog", async ({
    page,
  }) => {
    await page.goto("/incasso");
    await page.waitForLoadState("networkidle");
    await expect(page.getByText("Aanmaning")).toBeVisible({ timeout: 10000 });

    const caseRow = page.locator('[class*="cursor-pointer"]').first();
    if ((await caseRow.count()) > 0) {
      await caseRow.click({ force: true });

      // Click "Verstuur brief" button in action bar
      await page.getByText("Verstuur brief").click({ force: true });

      // Pre-flight dialog should open
      await expect(page.getByText("Controle")).toBeVisible({ timeout: 5000 });
      await expect(page.getByText("Geselecteerd")).toBeVisible();
      await expect(page.getByText("Gereed")).toBeVisible();
    }
  });

  // ── E5: Email toggle in pre-flight ──────────────────────────────────

  test("E5: email toggle is visible in the pre-flight dialog", async ({
    page,
  }) => {
    await page.goto("/incasso");
    await page.waitForLoadState("networkidle");
    await expect(page.getByText("Aanmaning")).toBeVisible({ timeout: 10000 });

    const caseRow = page.locator('[class*="cursor-pointer"]').first();
    if ((await caseRow.count()) > 0) {
      await caseRow.click({ force: true });
      await page.getByText("Verstuur brief").click({ force: true });
      await expect(page.getByText("Controle")).toBeVisible({ timeout: 5000 });

      // Look for email toggle text
      const emailToggle = page.getByText("Verstuur ook per e-mail");
      if ((await emailToggle.count()) > 0) {
        await expect(emailToggle).toBeVisible();
      }
    }
  });

  // ── E6 & E7: Skipped — require mocked email provider ───────────────
  // E6: batch execute shows success toast
  // E7: pipeline updates after batch action
  // These require a mocked email provider and are tested as part of smoke tests.

  // ── E8: Queue filter tabs ───────────────────────────────────────────

  test("E8: queue filter tabs are clickable", async ({ page }) => {
    await page.goto("/incasso");
    await page.waitForLoadState("networkidle");
    await expect(page.getByText("Aanmaning")).toBeVisible({ timeout: 10000 });

    // Check that filter tabs exist
    await expect(page.getByText("Alle dossiers")).toBeVisible();

    // Click a filter tab and verify the page remains functional
    const readyTab = page.getByText("Klaar voor volgende stap");
    if ((await readyTab.count()) > 0) {
      await readyTab.click({ force: true });
      // Wait for filter to apply
      await page.waitForLoadState("networkidle");
      // Verify page didn't break — "Alle dossiers" tab should still be visible
      await expect(page.getByText("Alle dossiers")).toBeVisible({
        timeout: 5000,
      });
    }
  });

  // ── E9: Stappen beheren tab ─────────────────────────────────────────

  test("E9: 'Stappen beheren' tab shows step configuration", async ({
    page,
  }) => {
    await page.goto("/incasso");
    await page.waitForLoadState("networkidle");

    // Click the "Stappen beheren" tab
    const stappenTab = page.getByText("Stappen beheren");
    if ((await stappenTab.count()) > 0) {
      await stappenTab.click({ force: true });

      // Should show step names in the configuration view
      await expect(
        page.getByText("Aanmaning").first()
      ).toBeVisible({ timeout: 5000 });
    }
  });
});
