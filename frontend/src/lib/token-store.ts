/**
 * Centralized token store for JWT access & refresh tokens (SEC-19).
 *
 * All token reads/writes go through this module so that:
 * 1. There is a single place to audit token handling
 * 2. Future migration to httpOnly cookies only requires changing this file
 * 3. Token keys are not scattered as magic strings across the codebase
 */

const ACCESS_KEY = "luxis_access_token";
const REFRESH_KEY = "luxis_refresh_token";

export const tokenStore = {
  getAccess(): string | null {
    return localStorage.getItem(ACCESS_KEY);
  },

  getRefresh(): string | null {
    return localStorage.getItem(REFRESH_KEY);
  },

  setTokens(access: string, refresh?: string): void {
    localStorage.setItem(ACCESS_KEY, access);
    if (refresh) {
      localStorage.setItem(REFRESH_KEY, refresh);
    }
  },

  clear(): void {
    localStorage.removeItem(ACCESS_KEY);
    localStorage.removeItem(REFRESH_KEY);
  },
};
