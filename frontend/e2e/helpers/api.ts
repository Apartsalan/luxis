/**
 * E2E API Helpers — Luxis
 *
 * Direct backend API calls for seeding and cleaning up test data.
 * Uses http://localhost:8000 (bypasses Next.js proxy).
 */

import { type APIRequestContext } from "@playwright/test";

const API_URL = "http://localhost:8000";

function authHeaders(token: string) {
  return { Authorization: `Bearer ${token}` };
}

/**
 * Create a contact (relation) via the backend API.
 */
export async function createContact(
  request: APIRequestContext,
  token: string,
  data: {
    contact_type: "company" | "person";
    name?: string;
    first_name?: string;
    last_name?: string;
    email?: string;
    phone?: string;
    kvk_number?: string;
    visit_city?: string;
  }
): Promise<{ id: string; name: string }> {
  const res = await request.post(`${API_URL}/api/relations`, {
    headers: authHeaders(token),
    data,
  });
  if (!res.ok()) {
    throw new Error(`Create contact failed: ${res.status()} ${await res.text()}`);
  }
  return res.json();
}

/**
 * Delete a contact by ID (soft delete).
 */
export async function deleteContact(
  request: APIRequestContext,
  token: string,
  id: string
): Promise<void> {
  const res = await request.delete(`${API_URL}/api/relations/${id}`, {
    headers: authHeaders(token),
  });
  if (!res.ok() && res.status() !== 404) {
    throw new Error(`Delete contact failed: ${res.status()}`);
  }
}

/**
 * Create a case (dossier) via the backend API.
 */
export async function createCase(
  request: APIRequestContext,
  token: string,
  data: {
    case_type: string;
    client_id: string;
    date_opened?: string;
    description?: string;
    opposing_party_id?: string;
    interest_type?: string;
  }
): Promise<{ id: string; case_number: string; status: string }> {
  const res = await request.post(`${API_URL}/api/cases`, {
    headers: authHeaders(token),
    data: {
      date_opened: new Date().toISOString().split("T")[0],
      ...data,
    },
  });
  if (!res.ok()) {
    throw new Error(`Create case failed: ${res.status()} ${await res.text()}`);
  }
  return res.json();
}

/**
 * Delete a case by ID (soft delete).
 */
export async function deleteCase(
  request: APIRequestContext,
  token: string,
  id: string
): Promise<void> {
  const res = await request.delete(`${API_URL}/api/cases/${id}`, {
    headers: authHeaders(token),
  });
  if (!res.ok() && res.status() !== 404) {
    throw new Error(`Delete case failed: ${res.status()}`);
  }
}

/**
 * Update a case's status via the backend API.
 */
export async function updateCaseStatus(
  request: APIRequestContext,
  token: string,
  id: string,
  newStatus: string,
  note?: string
): Promise<{ id: string; status: string }> {
  const res = await request.post(`${API_URL}/api/cases/${id}/status`, {
    headers: authHeaders(token),
    data: { new_status: newStatus, note: note ?? null },
  });
  if (!res.ok()) {
    throw new Error(`Update case status failed: ${res.status()} ${await res.text()}`);
  }
  return res.json();
}
