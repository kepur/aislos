import uuid

from fastapi import APIRouter, HTTPException, Query, status
from slugify import slugify

from app.api.deps import AdminUser, DB
from app.core.product_catalog import PUBLIC_PRODUCT_STATUSES
from app.crud.product import crud_product
from app.schemas.product import ProductCreate, ProductRead, ProductStatusUpdate, ProductUpdate
from app.services.audit import log_action
from app.services.event_bus import emit_event

router = APIRouter(prefix="/products", tags=["products"])

PRODUCT_SURFACE_SOURCE_TYPES = {
    "official": ["official", "official_recommended", "featured", "recycled_official"],
    "market": ["market", "marketplace", "supplier", "vendor", "official_recommended"],
    "recycled": ["enterprise_recycled", "official_recycled", "recycled_official", "refurbished"],
}


@router.get("")
async def list_products(
    db: DB,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    category_id: uuid.UUID | None = None,
    search: str | None = None,
    surface: str | None = Query(
        default=None,
        description="Product surface: official, market, recycled, or all. Defaults to all public products.",
    ),
):
    normalized_surface = (surface or "all").strip().lower()
    if normalized_surface not in {"all", *PRODUCT_SURFACE_SOURCE_TYPES.keys()}:
        raise HTTPException(status_code=422, detail="surface must be official, market, recycled, or all")
    items, total = await crud_product.get_public(
        db,
        skip=skip,
        limit=limit,
        category_id=category_id,
        search=search,
        source_types=PRODUCT_SURFACE_SOURCE_TYPES.get(normalized_surface),
    )
    return {
        "items": [ProductRead.model_validate(i) for i in items],
        "total": total,
        "surface": normalized_surface,
    }


@router.get("/admin/all")
async def list_all_products(
    db: DB,
    admin: AdminUser,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=200),
):
    items, total = await crud_product.get_multi(db, skip=skip, limit=limit)
    return {"items": [ProductRead.model_validate(i) for i in items], "total": total}


@router.get("/admin/{id}", response_model=ProductRead)
async def get_admin_product(id: uuid.UUID, db: DB, admin: AdminUser):
    product = await crud_product.get(db, id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


@router.get("/{slug_or_id}", response_model=ProductRead)
async def get_product(slug_or_id: str, db: DB):
    # Try UUID first, then slug
    try:
        uid = uuid.UUID(slug_or_id)
        product = await crud_product.get(db, uid)
    except ValueError:
        product = await crud_product.get_by_slug(db, slug_or_id)
    if not product or product.status not in PUBLIC_PRODUCT_STATUSES:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


@router.post("", response_model=ProductRead, status_code=status.HTTP_201_CREATED)
async def create_product(data: ProductCreate, db: DB, admin: AdminUser):
    obj = data.model_dump()
    if not obj.get("slug"):
        obj["slug"] = slugify(obj["name"])
    product = await crud_product.create_in_transaction(db, obj_in=obj)
    if product.status in {"pending", "draft"}:
        await emit_event(
            db,
            event_type="product.submitted",
            payload={
                "product_id": str(product.id),
                "name": product.name,
                "brand": product.brand,
                "status": product.status,
                "source_type": product.source_type,
            },
            aggregate_type="product",
            aggregate_id=product.id,
            target_channel="telegram_admin",
        )
    await db.commit()
    await db.refresh(product)
    return product


@router.put("/{id}", response_model=ProductRead)
async def update_product(id: uuid.UUID, data: ProductUpdate, db: DB, admin: AdminUser):
    product = await crud_product.get(db, id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return await crud_product.update(db, db_obj=product, obj_in=data.model_dump(exclude_unset=True))


@router.patch("/{id}/status", response_model=ProductRead)
async def update_product_status(id: uuid.UUID, data: ProductStatusUpdate, db: DB, admin: AdminUser):
    product = await crud_product.get(db, id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    old_status = product.status
    result = await crud_product.update(db, db_obj=product, obj_in={"status": data.status})
    await log_action(
        db, actor_user_id=admin.id, action="status_change",
        entity_type="product", entity_id=id,
        before={"status": old_status}, after={"status": data.status},
    )
    return result
