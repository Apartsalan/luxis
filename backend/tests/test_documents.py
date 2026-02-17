"""Tests for the documents module — template CRUD, document generation."""

import uuid

import pytest
from httpx import AsyncClient

from app.relations.models import Contact

# ── Template CRUD ────────────────────────────────────────────────────────────


SAMPLE_TEMPLATE = {
    "name": "Test 14-dagenbrief",
    "description": "Standaard 14-dagenbrief voor incassozaken",
    "template_type": "14_dagenbrief",
    "content": (
        "<h1>14-dagenbrief</h1>"
        "<p>Zaaknummer: {{ zaak.zaaknummer }}</p>"
        "<p>Client: {{ client.naam }}</p>"
        "<p>Wederpartij: {{ wederpartij.naam }}</p>"
        "<p>Hoofdsom: {{ financieel.total_principal | currency }}</p>"
        "<p>Datum: {{ vandaag | datum }}</p>"
    ),
}


@pytest.mark.asyncio
async def test_create_template(
    client: AsyncClient, auth_headers: dict
):
    """Creating a template should return 201."""
    response = await client.post(
        "/api/documents/templates",
        json=SAMPLE_TEMPLATE,
        headers=auth_headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Test 14-dagenbrief"
    assert data["template_type"] == "14_dagenbrief"
    assert "{{ zaak.zaaknummer }}" in data["content"]


@pytest.mark.asyncio
async def test_create_template_invalid_jinja(
    client: AsyncClient, auth_headers: dict
):
    """Template with invalid Jinja2 syntax should return 400."""
    payload = {
        "name": "Broken template",
        "template_type": "test",
        "content": "{% if unclosed %}",
    }
    response = await client.post(
        "/api/documents/templates",
        json=payload,
        headers=auth_headers,
    )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_list_templates(
    client: AsyncClient, auth_headers: dict
):
    """List templates should work."""
    # Create two templates
    await client.post(
        "/api/documents/templates",
        json=SAMPLE_TEMPLATE,
        headers=auth_headers,
    )
    await client.post(
        "/api/documents/templates",
        json={**SAMPLE_TEMPLATE, "name": "Sommatie", "template_type": "sommatie"},
        headers=auth_headers,
    )

    # List all
    response = await client.get(
        "/api/documents/templates", headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 2

    # Filter by type
    response = await client.get(
        "/api/documents/templates?template_type=sommatie",
        headers=auth_headers,
    )
    data = response.json()
    assert all(t["template_type"] == "sommatie" for t in data)


@pytest.mark.asyncio
async def test_get_template(
    client: AsyncClient, auth_headers: dict
):
    """Get template by ID should return full content."""
    create_response = await client.post(
        "/api/documents/templates",
        json=SAMPLE_TEMPLATE,
        headers=auth_headers,
    )
    template_id = create_response.json()["id"]

    response = await client.get(
        f"/api/documents/templates/{template_id}",
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["content"] == SAMPLE_TEMPLATE["content"]


@pytest.mark.asyncio
async def test_update_template(
    client: AsyncClient, auth_headers: dict
):
    """Updating a template should work."""
    create_response = await client.post(
        "/api/documents/templates",
        json=SAMPLE_TEMPLATE,
        headers=auth_headers,
    )
    template_id = create_response.json()["id"]

    response = await client.put(
        f"/api/documents/templates/{template_id}",
        json={"name": "Aangepaste brief"},
        headers=auth_headers,
    )
    assert response.status_code == 200
    assert response.json()["name"] == "Aangepaste brief"


@pytest.mark.asyncio
async def test_delete_template(
    client: AsyncClient, auth_headers: dict
):
    """Deleting a template should soft-delete it."""
    create_response = await client.post(
        "/api/documents/templates",
        json=SAMPLE_TEMPLATE,
        headers=auth_headers,
    )
    template_id = create_response.json()["id"]

    response = await client.delete(
        f"/api/documents/templates/{template_id}",
        headers=auth_headers,
    )
    assert response.status_code == 204


@pytest.mark.asyncio
async def test_get_template_not_found(
    client: AsyncClient, auth_headers: dict
):
    """Non-existent template should return 404."""
    fake_id = str(uuid.uuid4())
    response = await client.get(
        f"/api/documents/templates/{fake_id}",
        headers=auth_headers,
    )
    assert response.status_code == 404


# ── Document Generation ──────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_generate_document(
    client: AsyncClient,
    auth_headers: dict,
    test_company: Contact,
    test_person: Contact,
):
    """Generating a document from a template should render correctly."""
    # Create a case first
    case_payload = {
        "case_type": "incasso",
        "description": "Test vordering",
        "client_id": str(test_company.id),
        "opposing_party_id": str(test_person.id),
        "date_opened": "2026-02-17",
    }
    case_response = await client.post(
        "/api/cases", json=case_payload, headers=auth_headers
    )
    case_id = case_response.json()["id"]

    # Create a template
    template_response = await client.post(
        "/api/documents/templates",
        json=SAMPLE_TEMPLATE,
        headers=auth_headers,
    )
    template_id = template_response.json()["id"]

    # Generate document
    gen_payload = {
        "template_id": template_id,
        "title": "14-dagenbrief voor Test zaak",
    }
    response = await client.post(
        f"/api/documents/cases/{case_id}/generate",
        json=gen_payload,
        headers=auth_headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "14-dagenbrief voor Test zaak"
    assert data["document_type"] == "14_dagenbrief"
    assert data["content_html"] is not None
    # Check rendered content contains case number
    assert "2026-" in data["content_html"]
    assert "Acme B.V." in data["content_html"]


@pytest.mark.asyncio
async def test_list_case_documents(
    client: AsyncClient,
    auth_headers: dict,
    test_company: Contact,
):
    """List documents for a case should work."""
    # Create case
    case_response = await client.post(
        "/api/cases",
        json={
            "case_type": "incasso",
            "client_id": str(test_company.id),
            "date_opened": "2026-02-17",
        },
        headers=auth_headers,
    )
    case_id = case_response.json()["id"]

    # Create template & generate doc
    template_response = await client.post(
        "/api/documents/templates",
        json=SAMPLE_TEMPLATE,
        headers=auth_headers,
    )
    template_id = template_response.json()["id"]

    await client.post(
        f"/api/documents/cases/{case_id}/generate",
        json={"template_id": template_id},
        headers=auth_headers,
    )

    # List documents
    response = await client.get(
        f"/api/documents/cases/{case_id}",
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1


@pytest.mark.asyncio
async def test_delete_generated_document(
    client: AsyncClient,
    auth_headers: dict,
    test_company: Contact,
):
    """Deleting a generated document should soft-delete it."""
    # Create case
    case_response = await client.post(
        "/api/cases",
        json={
            "case_type": "incasso",
            "client_id": str(test_company.id),
            "date_opened": "2026-02-17",
        },
        headers=auth_headers,
    )
    case_id = case_response.json()["id"]

    # Create template & generate
    template_response = await client.post(
        "/api/documents/templates",
        json=SAMPLE_TEMPLATE,
        headers=auth_headers,
    )
    template_id = template_response.json()["id"]

    gen_response = await client.post(
        f"/api/documents/cases/{case_id}/generate",
        json={"template_id": template_id},
        headers=auth_headers,
    )
    doc_id = gen_response.json()["id"]

    # Delete
    response = await client.delete(
        f"/api/documents/{doc_id}",
        headers=auth_headers,
    )
    assert response.status_code == 204
