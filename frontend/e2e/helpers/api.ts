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
