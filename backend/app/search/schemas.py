"""Search module schemas — response models for global search."""

from pydantic import BaseModel


class SearchResultItem(BaseModel):
    """A single search result."""

    id: str
    type: str  # "case", "contact", "document"
    title: str
    subtitle: str
    href: str


class SearchResponse(BaseModel):
    """Global search response."""

    query: str
    results: list[SearchResultItem]
    total: int
