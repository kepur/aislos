import uuid
from datetime import datetime

from pydantic import BaseModel, Field, model_validator

from app.models.transaction_review import ReviewTargetType, TransactionChannel


Rating = int | None


class SellerReviewCreate(BaseModel):
    transaction_channel: TransactionChannel = TransactionChannel.ONLINE
    product_quality_rating: int = Field(ge=1, le=5)
    logistics_rating: Rating = Field(default=None, ge=1, le=5)
    communication_rating: int = Field(ge=1, le=5)
    comment: str | None = Field(default=None, max_length=2000)

    @model_validator(mode="after")
    def validate_channel_dimensions(self):
        if self.transaction_channel == TransactionChannel.ONLINE and self.logistics_rating is None:
            raise ValueError("logistics_rating is required for online transactions")
        if self.transaction_channel == TransactionChannel.OFFLINE:
            self.logistics_rating = None
        return self


class BuyerReviewCreate(BaseModel):
    transaction_channel: TransactionChannel = TransactionChannel.ONLINE
    buyer_rating: int = Field(ge=1, le=5)
    communication_rating: int = Field(ge=1, le=5)
    comment: str | None = Field(default=None, max_length=2000)


class TransactionReviewResponse(BaseModel):
    id: uuid.UUID
    order_id: uuid.UUID
    reviewer_id: uuid.UUID
    reviewee_user_id: uuid.UUID | None
    reviewee_company_id: uuid.UUID | None
    target_type: ReviewTargetType
    transaction_channel: TransactionChannel
    product_quality_rating: int | None
    logistics_rating: int | None
    communication_rating: int | None
    buyer_rating: int | None
    overall_rating: int
    comment: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class ReviewSummaryResponse(BaseModel):
    total_reviews: int
    average_overall_rating: float
    average_product_quality_rating: float | None = None
    average_logistics_rating: float | None = None
    average_communication_rating: float | None = None
    average_buyer_rating: float | None = None
    online_reviews: int
    offline_reviews: int
    reviews: list[TransactionReviewResponse]
