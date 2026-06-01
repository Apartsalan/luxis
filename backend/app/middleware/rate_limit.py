"""Rate limiting middleware — protects auth endpoints from brute-force attacks."""

from slowapi import Limiter
from starlette.requests import Request


def _get_real_client_ip(request: Request) -> str:
    """Extract the real client IP for rate-limiting, resistant to XFF spoofing.

    AUDIT-H3: the previous version took the FIRST X-Forwarded-For entry, which a
    client controls completely — rotating it bypassed the login rate-limit. In
    production exactly one trusted proxy (Caddy) sits in front of the app and
    APPENDS the real peer IP to X-Forwarded-For, so the LAST entry is the IP
    Caddy actually observed and the client cannot forge it. In dev there is no
    proxy and no XFF, so we fall back to the direct peer address.

    NB: this is only correct for a single trusted proxy. If another proxy/CDN is
    ever added in front of Caddy, take the Nth-from-last entry instead.
    """
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[-1].strip()
    return request.client.host if request.client else "127.0.0.1"


limiter = Limiter(key_func=_get_real_client_ip)
