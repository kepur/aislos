import uuid

from fastapi import APIRouter, HTTPException, status

from app.api.deps import AdminUser, DB
from app.crud.product import crud_product_category
from app.schemas.product import ProductCategoryCreate, ProductCategoryRead

router = APIRouter(prefix="/product-categories", tags=["product-categories"])


@router.get("", response_model=list[ProductCategoryRead])
async def list_categories(db: DB):
    return await crud_product_category.get_tree(db)


@router.post("", response_model=ProductCategoryRead, status_code=status.HTTP_201_CREATED)
async def create_category(data: ProductCategoryCreate, db: DB, admin: AdminUser):
    return await crud_product_category.create(db, obj_in=data.model_dump())


@router.put("/{id}", response_model=ProductCategoryRead)
async def update_category(id: uuid.UUID, data: ProductCategoryCreate, db: DB, admin: AdminUser):
    cat = await crud_product_category.get(db, id)
    if not cat:
        raise HTTPException(status_code=404, detail="Category not found")
    return await crud_product_category.update(db, db_obj=cat, obj_in=data.model_dump(exclude_unset=True))
