import uuid
from datetime import datetime

from pydantic import BaseModel

from app.models.escrow import EscrowProvider, EscrowStatus


class EscrowResponse(BaseModel):
    id: uuid.UUID
    order_id: uuid.UUID
    provider: EscrowProvider
    provider_reference: str | None
    auth_amount_minor: int
    captured_amount_minor: int
    released_amount_minor: int
    refunded_amount_minor: int
    currency: str
    status: EscrowStatus
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
