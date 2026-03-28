"""Exact Online API provider — OAuth 2.0 + REST API client.

Handles authentication and all API communication with Exact Online.
Netherlands region: start.exactonline.nl
"""

import base64
import logging
from dataclasses import dataclass
from urllib.parse import urlencode

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

BASE_URL = "https://start.exactonline.nl"
AUTH_PATH = "/api/oauth2/auth"
TOKEN_PATH = "/api/oauth2/token"
API_BASE = "/api/v1"


@dataclass
class ExactTokens:
    access_token: str
    refresh_token: str
    expires_in: int


class ExactOnlineProvider:
    """OAuth 2.0 + REST API client for Exact Online (NL region)."""

    def __init__(self):
        self.client_id = settings.exact_online_client_id
        self.client_secret = settings.exact_online_client_secret
        self.redirect_uri = settings.exact_online_redirect_uri

    # ── OAuth ────────────────────────────────────────────────────────────────

    def get_authorize_url(self, state: str) -> str:
        """Build the OAuth authorization URL."""
        params = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "response_type": "code",
            "state": state,
            "force_login": "0",
        }
        return f"{BASE_URL}{AUTH_PATH}?{urlencode(params)}"

    async def exchange_code(self, code: str) -> ExactTokens:
        """Exchange authorization code for tokens.

        Exact Online requires Basic auth header for token exchange.
        """
        auth_header = base64.b64encode(
            f"{self.client_id}:{self.client_secret}".encode()
        ).decode()

        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{BASE_URL}{TOKEN_PATH}",
                data={
                    "grant_type": "authorization_code",
                    "code": code,
                    "redirect_uri": self.redirect_uri,
                },
                headers={
                    "Authorization": f"Basic {auth_header}",
                    "Content-Type": "application/x-www-form-urlencoded",
                },
            )
            resp.raise_for_status()
            data = resp.json()

        return ExactTokens(
            access_token=data["access_token"],
            refresh_token=data["refresh_token"],
            expires_in=data.get("expires_in", 600),
        )

    async def refresh_access_token(self, refresh_token: str) -> ExactTokens:
        """Refresh an expired access token.

        Exact Online rotates refresh tokens — always store the new one.
        """
        auth_header = base64.b64encode(
            f"{self.client_id}:{self.client_secret}".encode()
        ).decode()

        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{BASE_URL}{TOKEN_PATH}",
                data={
                    "grant_type": "refresh_token",
                    "refresh_token": refresh_token,
                },
                headers={
                    "Authorization": f"Basic {auth_header}",
                    "Content-Type": "application/x-www-form-urlencoded",
                },
            )
            resp.raise_for_status()
            data = resp.json()

        return ExactTokens(
            access_token=data["access_token"],
            refresh_token=data["refresh_token"],
            expires_in=data.get("expires_in", 600),
        )

    # ── REST API ─────────────────────────────────────────────────────────────

    async def api_get(
        self,
        access_token: str,
        division: int,
        endpoint: str,
        params: dict | None = None,
    ) -> dict:
        """GET request to Exact Online REST API.

        All responses are JSON wrapped in a 'd' key (OData v3).
        """
        url = f"{BASE_URL}{API_BASE}/{division}/{endpoint}"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/json",
        }

        async with httpx.AsyncClient() as client:
            resp = await client.get(url, headers=headers, params=params or {})
            if resp.status_code == 429:
                logger.warning("Exact Online rate limit bereikt, wacht...")
                raise ExactRateLimitError("Rate limit exceeded")
            resp.raise_for_status()
            return resp.json()

    async def api_post(
        self,
        access_token: str,
        division: int,
        endpoint: str,
        data: dict,
    ) -> dict:
        """POST request to Exact Online REST API."""
        url = f"{BASE_URL}{API_BASE}/{division}/{endpoint}"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient() as client:
            resp = await client.post(url, headers=headers, json=data)
            if resp.status_code == 429:
                logger.warning("Exact Online rate limit bereikt, wacht...")
                raise ExactRateLimitError("Rate limit exceeded")
            resp.raise_for_status()
            return resp.json()

    # ── Convenience methods ──────────────────────────────────────────────────

    async def get_current_me(self, access_token: str) -> dict:
        """GET /api/v1/current/Me — returns user info including CurrentDivision."""
        url = f"{BASE_URL}{API_BASE}/current/Me"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/json",
        }
        async with httpx.AsyncClient() as client:
            resp = await client.get(url, headers=headers, params={"$select": "CurrentDivision,FullName,Email,DivisionCustomerName"})
            resp.raise_for_status()
            data = resp.json()

        # OData v3 wrapping: d.results[0]
        results = data.get("d", {}).get("results", [])
        if not results:
            raise ValueError("Geen divisie gevonden in Exact Online account")
        return results[0]

    async def get_vat_codes(self, access_token: str, division: int) -> list[dict]:
        """Fetch VAT codes from Exact Online."""
        data = await self.api_get(
            access_token, division, "vat/VATCodes",
            params={"$select": "Code,Description,Percentage", "$top": "100"},
        )
        return data.get("d", {}).get("results", [])

    async def get_gl_accounts(self, access_token: str, division: int) -> list[dict]:
        """Fetch general ledger accounts (revenue/expense types)."""
        data = await self.api_get(
            access_token, division, "financial/GLAccounts",
            params={
                "$select": "ID,Code,Description",
                "$filter": "Type eq 'R' or Type eq 'C'",  # Revenue or Cost
                "$top": "500",
            },
        )
        return data.get("d", {}).get("results", [])

    async def get_journals(self, access_token: str, division: int) -> list[dict]:
        """Fetch journals (sales, bank, etc.)."""
        data = await self.api_get(
            access_token, division, "financial/Journals",
            params={"$select": "Code,Description,Type", "$top": "100"},
        )
        return data.get("d", {}).get("results", [])

    # ── Sales Invoice ────────────────────────────────────────────────────────

    async def create_sales_invoice(
        self, access_token: str, division: int, invoice_data: dict
    ) -> dict:
        """Create a sales invoice in Exact Online."""
        data = await self.api_post(
            access_token, division, "salesinvoice/SalesInvoices", invoice_data
        )
        return data.get("d", {})

    # ── Accounts (Debtors) ───────────────────────────────────────────────────

    async def create_account(
        self, access_token: str, division: int, account_data: dict
    ) -> dict:
        """Create a CRM account (debtor) in Exact Online."""
        data = await self.api_post(
            access_token, division, "crm/Accounts", account_data
        )
        return data.get("d", {})

    async def find_account_by_name(
        self, access_token: str, division: int, name: str
    ) -> dict | None:
        """Find an account by name."""
        safe_name = name.replace("'", "''")
        data = await self.api_get(
            access_token, division, "crm/Accounts",
            params={
                "$filter": f"Name eq '{safe_name}'",
                "$select": "ID,Code,Name",
                "$top": "1",
            },
        )
        results = data.get("d", {}).get("results", [])
        return results[0] if results else None

    # ── Bank Entries ─────────────────────────────────────────────────────────

    async def create_bank_entry(
        self, access_token: str, division: int, entry_data: dict
    ) -> dict:
        """Create a bank entry (payment booking) in Exact Online."""
        data = await self.api_post(
            access_token, division, "financialtransaction/BankEntries", entry_data
        )
        return data.get("d", {})


class ExactRateLimitError(Exception):
    """Raised when Exact Online returns 429 Too Many Requests."""

    pass
