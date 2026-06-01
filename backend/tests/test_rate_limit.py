"""Tests for the rate-limit client-IP key function (AUDIT-H3).

The login limiter keys on the client IP. The previous key function trusted the
FIRST X-Forwarded-For entry, which the client fully controls — rotating it gave
every request a "new IP" and bypassed the limit. Behind a single trusted proxy
(Caddy) that appends the real peer IP, the LAST entry is the trustworthy one.
"""

from types import SimpleNamespace

from app.middleware.rate_limit import _get_real_client_ip


def _request(xff: str | None = None, peer: str = "203.0.113.5"):
    headers = {}
    if xff is not None:
        headers["X-Forwarded-For"] = xff
    return SimpleNamespace(
        headers=headers,
        client=SimpleNamespace(host=peer),
    )


def test_uses_last_xff_entry_behind_proxy():
    # Caddy appended the real peer (203.0.113.5) after the client-sent value.
    assert _get_real_client_ip(_request("9.9.9.9, 203.0.113.5")) == "203.0.113.5"


def test_spoofed_prefix_does_not_change_key():
    """Rotating the client-controlled prefix must NOT change the rate-limit key."""
    key_a = _get_real_client_ip(_request("1.1.1.1, 203.0.113.5"))
    key_b = _get_real_client_ip(_request("2.2.2.2, 203.0.113.5"))
    key_c = _get_real_client_ip(_request("3.3.3.3, 203.0.113.5"))
    assert key_a == key_b == key_c == "203.0.113.5"


def test_falls_back_to_peer_when_no_xff():
    assert _get_real_client_ip(_request(xff=None, peer="198.51.100.7")) == "198.51.100.7"


def test_handles_whitespace_in_chain():
    assert _get_real_client_ip(_request("9.9.9.9,  203.0.113.9")) == "203.0.113.9"
