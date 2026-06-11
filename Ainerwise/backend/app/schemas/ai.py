import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel

from app.schemas.base import BaseSchema


class KnowledgeDocumentRead(BaseSchema):
    id: uuid.UUID
    region_id: uuid.UUID | None = None
    source_type: str
    title: str
    lang: str | None = None
    minio_key: str | None = None
    product_id: uuid.UUID | None = None
    status: str
    meta_json: dict | None = None
    chunk_count: int = 0
    created_at: datetime
    updated_at: datetime


class KnowledgeTextCreate(BaseModel):
    title: str
    content: str
    source_type: str = "faq"
    lang: str | None = None
    product_id: uuid.UUID | None = None


class DocumentChunkRead(BaseSchema):
    id: uuid.UUID
    chunk_index: int
    content: str


class AIReviewRead(BaseSchema):
    id: uuid.UUID
    run_id: uuid.UUID | None = None
    target_type: str
    target_id: uuid.UUID | None = None
    draft_json: dict | None = None
    status: str
    reviewed_by: uuid.UUID | None = None
    reviewed_at: datetime | None = None
    review_notes: str | None = None
    created_at: datetime
    updated_at: datetime


class AIReviewDecision(BaseModel):
    notes: str | None = None


class ConversationRead(BaseSchema):
    id: uuid.UUID
    channel: str
    visitor_id: str | None = None
    lead_id: uuid.UUID | None = None
    status: str
    lang: str | None = None
    created_at: datetime
    updated_at: datetime


class ConversationMessageRead(BaseSchema):
    id: uuid.UUID
    role: str
    content: str | None = None
    created_at: datetime


class ChatRequest(BaseModel):
    message: str
    conversation_id: uuid.UUID | None = None
    visitor_id: str | None = None
    lang: str | None = None


class ChatResponse(BaseModel):
    configured: bool
    conversation_id: uuid.UUID | None = None
    answer: str | None = None
    sources: list[dict[str, Any]] = []
    products: list[dict[str, Any]] = []
    similar_cases: list[dict[str, Any]] = []
    lead_created: bool = False
    disclaimer: str | None = None
