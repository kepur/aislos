import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.models.wallet import DepositStatus, WalletStatus, WalletTransactionType


class WalletResponse(BaseModel):
    id: uuid.UUID
    owner_user_id: uuid.UUID
    currency: str
    available_balance_minor: int
    locked_balance_minor: int
    total_deposited_minor: int
    status: WalletStatus
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class WalletMeResponse(BaseModel):
    wallets: list[WalletResponse]


class WalletTransactionResponse(BaseModel):
    id: uuid.UUID
    wallet_id: uuid.UUID
    owner_user_id: uuid.UUID
    tx_type: WalletTransactionType
    amount_delta_minor: int
    available_balance_after_minor: int
    locked_balance_after_minor: int
    currency: str
    reference_type: str | None
    reference_id: uuid.UUID | None
    note: str | None
    metadata_json: dict | None
    created_at: datetime

    model_config = {"from_attributes": True}


class DepositCreateRequest(BaseModel):
    amount_minor: int = Field(gt=0)
    currency: str = "PHP"
    network: str = "LOCAL_BANK"
    provider: str = "MANUAL_BANK"
    payment_method: str = "PHP_MANUAL_BANK"
    quote_id: uuid.UUID | None = None
    source_currency: str | None = None
    target_currency: str | None = None


class DepositSubmitTxRequest(BaseModel):
    tx_hash: str = Field(min_length=8, max_length=255)
    confirmations: int = Field(default=0, ge=0)
    submitter_note: str | None = None


class DepositAdminDecisionRequest(BaseModel):
    confirmations: int = Field(default=1, ge=0)
    admin_note: str | None = None


class WalletDepositResponse(BaseModel):
    id: uuid.UUID
    wallet_id: uuid.UUID
    owner_user_id: uuid.UUID
    amount_minor: int
    currency: str
    network: str
    provider: str
    payment_method: str
    quote_id: uuid.UUID | None
    source_currency: str | None
    target_currency: str | None
    deposit_address: str
    tx_hash: str | None
    confirmations: int
    status: DepositStatus
    submitter_note: str | None
    admin_note: str | None
    verified_by: uuid.UUID | None
    verified_at: datetime | None
    rejected_by: uuid.UUID | None
    rejected_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
