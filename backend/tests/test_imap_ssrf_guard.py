"""SEC-29 wachter: IMAP-hostvalidatie blokkeert interne/metadata-adressen.

De oude lijst miste 169.254.0.0/16 (cloud-metadata) en IPv4-mapped IPv6 omzeilde de
IPv4-ranges. Publieke adressen blijven toegestaan.
"""

import pytest

from app.email.oauth_router import _is_blocked_host


@pytest.mark.parametrize(
    "host",
    [
        "127.0.0.1",
        "10.1.2.3",
        "192.168.1.1",
        "172.16.0.9",
        "169.254.169.254",  # cloud-metadata
        "::ffff:127.0.0.1",  # IPv4-mapped IPv6 loopback
        "localhost",
        "db",
        "backend",
    ],
)
def test_blocked_hosts(host):
    assert _is_blocked_host(host) is True


@pytest.mark.parametrize("host", ["8.8.8.8", "1.1.1.1"])
def test_public_hosts_allowed(host):
    assert _is_blocked_host(host) is False
