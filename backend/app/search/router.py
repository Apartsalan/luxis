"""Search module router — Global search endpoint."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import User
from app.database import get_db
from app.dependencies import get_current_user
from app.search import service
from app.search.schemas import SearchResponse

router = APIRouter(prefix="/api/search", tags=["search"])


@router.get("", response_model=SearchResponse)
async def search(
    q: str = Query(..., min_length=1, max_length=200, description="Zoekterm"),
    limit: int = Query(default=10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> SearchResponse:
    """Global search across cases, contacts, and documents."""
    results = await service.global_search(db, user.tenant_id, q, limit)
    return SearchResponse(
        query=q,
        results=results,
        total=len(results),
    )
