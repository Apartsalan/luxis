"""SEC-27 wachter: een gedeactiveerd kantoor verliest toegang.

get_current_user checkte alleen user.is_active; de gebruikers van een geschorst
kantoor bleven daardoor volledig ingelogd. Deze wachter bewijst dat een actief
kantoor toegang heeft en een gedeactiveerd kantoor 401 krijgt.
"""

import pytest


@pytest.mark.asyncio
async def test_active_tenant_allows_access(client, auth_headers):
    r = await client.get("/api/auth/me", headers=auth_headers)
    assert r.status_code == 200


@pytest.mark.asyncio
async def test_inactive_tenant_blocks_access(client, db, test_tenant, auth_headers):
    # Actief → toegang.
    assert (await client.get("/api/auth/me", headers=auth_headers)).status_code == 200

    # Kantoor deactiveren.
    test_tenant.is_active = False
    db.add(test_tenant)
    await db.commit()

    # Zelfde geldige token → nu geweigerd.
    r = await client.get("/api/auth/me", headers=auth_headers)
    assert r.status_code == 401
    assert "actief" in r.json()["detail"].lower()
