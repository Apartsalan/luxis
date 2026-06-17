/**
 * JWT-aware fetch wrapper for the Luxis API.
 * Automatically attaches the access token and handles token refresh.
 */

import { tokenStore } from "@/lib/token-store";

// Use relative URL so requests go through Next.js rewrite proxy to the backend
const API_URL = "";

// Mutex: reuse a single in-flight refresh promise to avoid race conditions
let refreshPromise: Promise<string | null> | null = null;

async function refreshAccessToken(): Promise<string | null> {
  if (refreshPromise) return refreshPromise;

  refreshPromise = (async () => {
    const refreshToken = tokenStore.getRefresh();
    if (!refreshToken) return null;

    try {
      const response = await fetch(`${API_URL}/api/auth/refresh`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ refresh_token: refreshToken }),
      });

      if (!response.ok) return null;

      const data = await response.json();
      tokenStore.setTokens(data.access_token, data.refresh_token);
      return data.access_token;
    } catch {
      return null;
    }
  })();

  try {
    return await refreshPromise;
  } finally {
    refreshPromise = null;
  }
}

export async function api(path: string, options: RequestInit = {}): Promise<Response> {
  const token = tokenStore.getAccess();

  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string>),
  };

  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  let response = await fetch(`${API_URL}${path}`, {
    ...options,
    headers,
  });

  // If 401, try to refresh the token and retry once
  if (response.status === 401 && token) {
    const newToken = await refreshAccessToken();
    if (newToken) {
      headers["Authorization"] = `Bearer ${newToken}`;
      response = await fetch(`${API_URL}${path}`, {
        ...options,
        headers,
      });
    } else {
      // Refresh failed — redirect to login
      tokenStore.clear();
      window.location.href = "/login";
    }
  }

  return response;
}

/**
 * Haal een leesbare melding uit een FastAPI-foutbody.
 *
 * `detail` kan een string zijn (onze eigen HTTPExceptions) óf een array van
 * Pydantic-validatiefouten (HTTP 422). Zonder deze helper levert
 * `new Error(body.detail)` op een 422 de tekst "[object Object]" op, omdat de
 * array/het object als string wordt weergegeven. Pydantic plakt "Value error, "
 * vóór eigen ValueError-meldingen — die strippen we eraf.
 */
export function parseApiError(body: unknown, fallback: string): string {
  const detail = (body as { detail?: unknown } | null)?.detail;
  if (typeof detail === "string" && detail.trim()) return detail;
  if (Array.isArray(detail)) {
    const msgs = detail
      .map((e) =>
        e && typeof e === "object" && "msg" in e
          ? String((e as { msg: unknown }).msg).replace(/^Value error,\s*/i, "")
          : null
      )
      .filter((m): m is string => Boolean(m));
    if (msgs.length) return Array.from(new Set(msgs)).join(" · ");
  }
  return fallback;
}
