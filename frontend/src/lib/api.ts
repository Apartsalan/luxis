/**
 * JWT-aware fetch wrapper for the Luxis API.
 * Automatically attaches the access token and handles token refresh.
 */

// Use relative URL so requests go through Next.js rewrite proxy to the backend
const API_URL = "";

// Mutex: reuse a single in-flight refresh promise to avoid race conditions
let refreshPromise: Promise<string | null> | null = null;

async function refreshAccessToken(): Promise<string | null> {
  if (refreshPromise) return refreshPromise;

  refreshPromise = (async () => {
    const refreshToken = localStorage.getItem("luxis_refresh_token");
    if (!refreshToken) return null;

    try {
      const response = await fetch(`${API_URL}/api/auth/refresh`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ refresh_token: refreshToken }),
      });

      if (!response.ok) return null;

      const data = await response.json();
      localStorage.setItem("luxis_access_token", data.access_token);
      localStorage.setItem("luxis_refresh_token", data.refresh_token);
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
  const token = localStorage.getItem("luxis_access_token");

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
      localStorage.removeItem("luxis_access_token");
      localStorage.removeItem("luxis_refresh_token");
      window.location.href = "/login";
    }
  }

  return response;
}
