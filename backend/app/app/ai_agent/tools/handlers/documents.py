"""Document tool handlers — generate, list, get templates."""

from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.ai_agent.tools import serialize
from app.documents import service as documents_service
from app.documents.schemas import GenerateDocumentRequest


async def handle_document_generate(
    *,
    db: AsyncSession,
    tenant_id: uuid.UUID,
    user_id: uuid.UUID,
    case_id: str,
    template_id: str,
    title: str | None = None,
) -> dict:
    """Generate a document from a template for a case."""
    data = GenerateDocumentRequest(
        template_id=uuid.UUID(template_id),
        title=title,
    )
    doc = await documents_service.generate_document(
        db, tenant_id, uuid.UUID(case_id), user_id, data
    )
    return {
        "id": serialize(doc.id),
        "title": doc.title,
        "document_type": doc.document_type,
        "file_path": doc.file_path,
        "created": True,
    }


async def handle_document_list(
    *,
    db: AsyncSession,
    tenant_id: uuid.UUID,
    user_id: uuid.UUID,
    case_id: str,
) -> dict:
    """List all generated documents for a case."""
    docs = await documents_service.list_generated_documents(db, tenant_id, uuid.UUID(case_id))
    return {
        "items": [
            {
                "id": serialize(d.id),
                "title": d.title,
                "document_type": d.document_type,
                "file_path": d.file_path,
                "created_at": serialize(d.created_at),
            }
            for d in docs
        ],
        "count": len(docs),
    }


async def handle_template_list(
    *,
    db: AsyncSession,
    tenant_id: uuid.UUID,
    user_id: uuid.UUID,
    template_type: str | None = None,
) -> dict:
    """List available document templates."""
    templates = await documents_service.list_templates(db, tenant_id, template_type=template_type)
    return {
        "items": [
            {
                "id": serialize(t.id),
                "name": t.name,
                "template_type": t.template_type,
                "description": t.description,
                "is_active": t.is_active,
            }
            for t in templates
        ],
        "count": len(templates),
    }
