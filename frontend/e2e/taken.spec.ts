/**
 * Taken (Tasks) E2E Tests — Luxis
 *
 * Tests the taken page: list, create task via form, and mark as complete.
 * Tests are sequential.
 * Auth is provided by storageState (setup project).
 */

import { test, expect } from "@playwright/test";
import { loginViaApi } from "./helpers/auth";
import {
  createContact,
  deleteContact,
  createCase,
  deleteCase,
  createWorkflowTask,
  deleteWorkflowTask,
} from "./helpers/api";

// Store IDs across tests (workers=1, sequential execution guaranteed)
let authToken = "";
let userId = "";
let clientId = "";
let caseId = "";
let caseNumber = "";
let taskId = "";

test.describe("Taken", () => {
  test.beforeAll(async ({ request }) => {
    const { accessToken, userId: uid } = await loginViaApi(request);
    authToken = accessToken;
    userId = uid;

    // Seed a client and case (tasks require a case)
    const client = await createContact(request, authToken, {
      contact_type: "company",
      name: "E2E TakenClient B.V.",
      email: "e2e-takenclient@test.nl",
    });
    clientId = client.id;

    const caseData = await createCase(request, authToken, {
      case_type: "advies",
      client_id: clientId,
      description: "E2E taken test dossier",
    });
    caseId = caseData.id;
    caseNumber = caseData.case_number;
  });

  test.afterAll(async ({ request }) => {
    if (taskId) {
      await deleteWorkflowTask(request, authToken, taskId).catch(() => {});
    }
    if (caseId) {
      await deleteCase(request, authToken, caseId).catch(() => {});
    }
    if (clientId) {
      await deleteContact(request, authToken, clientId).catch(() => {});
    }
  });

  test("T1: taken page loads with heading and controls", async ({ page }) => {
    await page.goto("/taken");

    // Page heading
    await expect(
      page.locator("h1").filter({ hasText: "Mijn Taken" })
    ).toBeVisible({ timeout: 15000 });

    // "Nieuwe taak" button
    await expect(
      page.getByRole("button", { name: /Nieuwe taak/ })
    ).toBeVisible();

    // Filter buttons (exact match to avoid matching "Markeer als afgerond" buttons)
    await expect(
      page.getByRole("button", { name: "Openstaand", exact: true })
    ).toBeVisible();
    await expect(
      page.getByRole("button", { name: "Alles", exact: true })
    ).toBeVisible();
    await expect(
      page.getByRole("button", { name: "Afgerond", exact: true })
    ).toBeVisible();
  });

  test("T2: create a task via the form", async ({ page }) => {
    test.setTimeout(60000);
    await page.goto("/taken");
    await page.waitForLoadState("domcontentloaded");

    // Wait for page to load
    await expect(
      page.locator("h1").filter({ hasText: "Mijn Taken" })
    ).toBeVisible({ timeout: 15000 });

    // Click "Nieuwe taak"
    await page.getByRole("button", { name: /Nieuwe taak/ }).click({ force: true });

    // Wait for form to appear
    await expect(
      page.locator("h3").filter({ hasText: "Nieuwe taak" })
    ).toBeVisible({ timeout: 5000 });

    // Select the seeded case from the dossier dropdown
    const caseSelect = page.locator("select").filter({ hasText: "Selecteer een dossier" }).first();
    const option = caseSelect.locator("option").filter({ hasText: caseNumber });
    const optionValue = await option.getAttribute("value");
    await caseSelect.selectOption(optionValue!);

    // Fill in the title
    const titleInput = page.getByPlaceholder(/Bijv\. Bel debiteur/);
    await titleInput.fill("E2E Test Taak");

    // Submit
    await page.getByRole("button", { name: "Aanmaken" }).click({ force: true });

    // Toast notification
    await expect(page.getByText("Taak aangemaakt")).toBeVisible({
      timeout: 5000,
    });

    // Task should appear in the list
    await expect(
      page.getByText("E2E Test Taak").first()
    ).toBeVisible({ timeout: 10000 });
  });

  test("T3: complete a task", async ({ page, request }) => {
    test.setTimeout(60000);

    // Seed a task via API assigned to the current user
    const today = new Date().toISOString().split("T")[0];
    const task = await createWorkflowTask(request, authToken, {
      case_id: caseId,
      task_type: "custom",
      title: "E2E Afrond Taak",
      due_date: today,
      assigned_to_id: userId,
    });
    taskId = task.id;

    // Navigate to taken page
    await page.goto("/taken");
    await page.waitForLoadState("domcontentloaded");

    await expect(
      page.locator("h1").filter({ hasText: "Mijn Taken" })
    ).toBeVisible({ timeout: 15000 });

    // Task should be visible
    await expect(
      page.getByText("E2E Afrond Taak").first()
    ).toBeVisible({ timeout: 10000 });

    // Click the complete button within the specific task card
    // Each task card has class "group" — filter to the one containing our task title
    const taskLink = page.getByRole("link", { name: "E2E Afrond Taak" });
    const taskCard = page.locator("div.group").filter({ has: taskLink });
    await taskCard.locator("button[title='Markeer als afgerond']").click({ force: true });

    // Toast notification
    await expect(page.getByText("Taak afgerond")).toBeVisible({
      timeout: 5000,
    });

    // Task should disappear from the "Openstaand" view after data refetch
    await expect(taskLink).not.toBeVisible({ timeout: 10000 });

    // Mark as cleaned up (completed tasks still exist but test data is done)
    taskId = "";
  });
});
