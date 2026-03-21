"""Rate limiting middleware — protects auth endpoints from brute-force attacks."""

from slowapi import Limiter
from starlette.requests import Request


def _get_real_client_ip(request: Request) -> str:
    """Extract the real client IP, respecting X-Forwarded-For behind Caddy proxy."""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        # First IP in the chain is the real client
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "127.0.0.1"


limiter = Limiter(key_func=_get_real_client_ip)
