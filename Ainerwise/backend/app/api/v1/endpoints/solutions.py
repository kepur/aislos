import uuid

from fastapi import APIRouter, HTTPException, Query, status
from slugify import slugify

from app.api.deps import AdminUser, CurrentUser, DB
from app.crud.solution import crud_solution
from app.schemas.solution import SolutionCreate, SolutionRead, SolutionUpdate

router = APIRouter(prefix="/solutions", tags=["solutions"])


@router.get("", response_model=list[SolutionRead])
async def list_solutions(db: DB):
    items = await crud_solution.get_public(db)
    return items


@router.get("/{slug_or_id}", response_model=SolutionRead)
async def get_solution(slug_or_id: str, db: DB):
    # Try UUID first, then slug
    try:
        uid = uuid.UUID(slug_or_id)
        sol = await crud_solution.get(db, uid)
    except ValueError:
        sol = await crud_solution.get_by_slug(db, slug_or_id)
    if not sol:
        raise HTTPException(status_code=404, detail="Solution not found")
    return sol


@router.post("", response_model=SolutionRead, status_code=status.HTTP_201_CREATED)
async def create_solution(data: SolutionCreate, db: DB, admin: AdminUser):
    obj = data.model_dump()
    if not obj.get("slug"):
        obj["slug"] = slugify(obj["title"])
    return await crud_solution.create(db, obj_in=obj)


@router.put("/{id}", response_model=SolutionRead)
async def update_solution(id: uuid.UUID, data: SolutionUpdate, db: DB, admin: AdminUser):
    sol = await crud_solution.get(db, id)
    if not sol:
        raise HTTPException(status_code=404, detail="Solution not found")
    return await crud_solution.update(db, db_obj=sol, obj_in=data.model_dump(exclude_unset=True))


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_solution(id: uuid.UUID, db: DB, admin: AdminUser):
    deleted = await crud_solution.delete(db, id=id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Solution not found")
