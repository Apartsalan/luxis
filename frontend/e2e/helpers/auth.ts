/**
 * E2E Auth Helpers — Luxis
 *
 * Shared authentication utilities for all E2E test specs.
 * Handles login via API and token injection into localStorage.
 */

import { type Page, type APIRequestContext } from "@playwright/test";

const API_URL = "http://localhost:8000";
const DEFAULT_EMAIL = "lisanne@kestinglegal.nl";
const DEFAULT_PASSWORD = "testpassword123";

/**
 * Login via backend API and return tokens.
 */
export async function loginViaApi(
  request: APIRequestContext,
  email = DEFAULT_EMAIL,
  password = DEFAULT_PASSWORD
): Promise<{ accessToken: string; refreshToken: string }> {
  const res = await request.post(`${API_URL}/api/auth/login`, {
    data: { email, password },
  });
  if (!res.ok()) {
    throw new Error(`Login failed: ${res.status()} ${await res.text()}`);
  }
  const body = await res.json();
  return {
    accessToken: body.access_token,
    refreshToken: body.refresh_token,
  };
}

/**
 * Set auth tokens in the page's localStorage.
 * Page must already be navigated to some URL on the same origin.
 */
export async function setAuthTokens(
  page: Page,
  accessToken: string,
  refreshToken?: string
): Promise<void> {
  await page.evaluate(
    ({ at, rt }) => {
      localStorage.setItem("luxis_access_token", at);
      if (rt) localStorage.setItem("luxis_refresh_token", rt);
    },
    { at: accessToken, rt: refreshToken }
  );
}

/**
 * Login via API, inject tokens, and navigate to the target URL.
 * Combines loginViaApi + setAuthTokens + page.goto in one call.
 */
export async function authenticateAndGoto(
  page: Page,
  request: APIRequestContext,
  targetUrl: string
): Promise<void> {
  const { accessToken, refreshToken } = await loginViaApi(request);

  // Navigate to login page first to establish the origin for localStorage
  await page.goto("/login");
  await setAuthTokens(page, accessToken, refreshToken);

  // Navigate to target URL
  await page.goto(targetUrl);

  // Wait for auth to resolve — the dashboard layout either shows content
  // or redirects to /login. Wait until we're NOT on the login page.
  await page.waitForFunction(
    () => !window.location.pathname.includes("/login"),
    { timeout: 20000 }
  );
  await page.waitForLoadState("domcontentloaded");
}
