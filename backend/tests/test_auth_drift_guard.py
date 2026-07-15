"""Auth drift-guard — every HTTP route must require authentication.

Mirror of the RLS drift-guard (``test_rls_isolation.py``): the RLS test proves
no tenant table ships without row protection; this test proves no route ships
without ``get_current_user`` in its dependency tree.

Why this exists: auth is enforced per-endpoint (a ``Depends(get_current_user)``
or ``require_role(...)`` in each signature), not by a router-wide guard. That is
correct today (301 routes, 8 deliberately public), but nothing stops a future
route from silently forgetting the dependency — the exact failure mode behind
the worst "vibe-coded" data leaks (Tea App, Base44, 170 Lovable apps).

The check walks the *real* FastAPI dependency tree, so it also catches auth added
indirectly via ``require_role`` (which itself depends on ``get_current_user``).

To add a new public route: add it to ``PUBLIC_ROUTES`` below with a one-line
reason. If you can't justify it, it isn't public — add the dependency instead.
"""

from fastapi.routing import APIRoute

from app.dependencies import get_current_user
from app.main import app

# (METHOD, PATH) pairs that are intentionally reachable without a JWT.
# Every entry needs a reason — an unexplained public route is a bug.
PUBLIC_ROUTES = {
    ("POST", "/api/auth/login"),           # issues the token — can't require one
    ("POST", "/api/auth/refresh"),         # trades a valid refresh token for access
    ("POST", "/api/auth/forgot-password"),  # unauthenticated by definition (rate-limited 3/h)
    ("POST", "/api/auth/reset-password"),   # uses a signed reset token, not a session (5/h)
    ("GET", "/api/email/oauth/callback"),          # OAuth return: signed+single-use state param
    ("GET", "/api/email/oauth/callback/outlook"),  # OAuth return: signed+single-use state param
    ("GET", "/api/exact-online/callback"),         # OAuth return: signed+single-use state param
    ("GET", "/health"),                    # liveness probe for the deploy health-gate
}


def _flat_calls(dependant):
    """All dependency callables in a route's tree, recursively."""
    calls = [dependant.call]
    for sub in dependant.dependencies:
        calls.extend(_flat_calls(sub))
    return calls


def _real_routes():
    for route in app.routes:
        if not isinstance(route, APIRoute):
            continue
        for method in route.methods or []:
            if method in ("HEAD", "OPTIONS"):
                continue
            yield method, route.path, route


def test_every_route_requires_auth_or_is_allowlisted():
    """No route may be public unless it is in PUBLIC_ROUTES."""
    unprotected = []
    for method, path, route in _real_routes():
        if get_current_user in _flat_calls(route.dependant):
            continue
        if (method, path) not in PUBLIC_ROUTES:
            unprotected.append(f"{method} {path}")

    assert not unprotected, (
        "Route(s) reachable without authentication and not in PUBLIC_ROUTES:\n  "
        + "\n  ".join(sorted(unprotected))
        + "\n\nAdd Depends(get_current_user)/require_role, or (if truly public) "
        "add it to PUBLIC_ROUTES with a reason."
    )


def test_allowlist_has_no_stale_entries():
    """Every PUBLIC_ROUTES entry must still match a real, still-public route.

    Guards the reverse drift: a public route gets protected or renamed, but its
    allowlist entry lingers and would mask a genuinely-public future route at
    that same path.
    """
    live_public = {
        (method, path)
        for method, path, route in _real_routes()
        if get_current_user not in _flat_calls(route.dependant)
    }
    stale = PUBLIC_ROUTES - live_public
    assert not stale, f"Stale PUBLIC_ROUTES entries (no longer public routes): {sorted(stale)}"


def test_guard_detects_an_unprotected_route():
    """Control assertion (red→green proof): a route WITHOUT the dependency is
    seen as unprotected. If this ever passes trivially, the detection is broken.
    """
    from fastapi import FastAPI

    probe = FastAPI()

    @probe.get("/wide-open")
    async def _wide_open():
        return {"leaked": True}

    route = next(r for r in probe.routes if isinstance(r, APIRoute))
    assert get_current_user not in _flat_calls(route.dependant)
