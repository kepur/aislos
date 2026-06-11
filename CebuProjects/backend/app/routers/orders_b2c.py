from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import uuid

from app.core.database import get_db
from app.core.deps import get_current_user, require_roles
from app.models.catalog import CatalogItem
from app.models.order import Order, OrderStatus
from app.models.user import User, UserRole
from app.models.intent import Intent, IntentStatus
from app.models.offer import Offer, OfferStatus
from app.schemas.order import OrderCreateFromCatalog, OrderResponse
from app.routers.orders import _enrich_order

router = APIRouter(tags=["Orders B2C"])

@router.post("/orders", response_model=OrderResponse)
async def create_b2c_order(
    req: OrderCreateFromCatalog,
    user: User = Depends(require_roles(UserRole.BUYER)),
    db: AsyncSession = Depends(get_db)
):
    # 1. Fetch catalog item
    item_res = await db.execute(select(CatalogItem).where(CatalogItem.id == req.catalog_item_id))
    item = item_res.scalar_one_or_none()
    if not item:
        raise HTTPException(404, "Catalog item not found")
    if item.status.value != "ACTIVE":
        raise HTTPException(400, "Item is not active")
    if req.qty < (item.min_order_qty or 1):
        raise HTTPException(400, f"Minimum order quantity is {item.min_order_qty}")
    if item.stock_qty < req.qty:
        raise HTTPException(400, f"Insufficient stock. Available: {item.stock_qty}")

    # 2. Deduct stock
    item.stock_qty -= req.qty
    item.order_count = (item.order_count or 0) + 1

    # 3. Create dummy intent and offer to satisfy DB constraints
    intent = Intent(
        id=uuid.uuid4(),
        buyer_id=user.id,
        category_id=item.category_id,
        title=f"B2C Direct Order: {item.title}",
        qty=req.qty,
        unit=item.unit,
        currency=item.currency,
        status=IntentStatus.CLOSED,
        attrs_jsonb={"b2c_direct_buy": True, "catalog_item_id": str(item.id)}
    )
    db.add(intent)

    total_minor = item.price_minor * req.qty

    offer = Offer(
        id=uuid.uuid4(),
        intent_id=intent.id,
        supplier_id=item.company_id, # Wait, who is the supplier user? Usually it's company owner. Offer model requires supplier_id which is User ID! Let's check Offer model.
        # Actually Offer model has supplier_id which maps to users.id. But we only have company_id. 
        # We need to find the company owner.
    )
