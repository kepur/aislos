"""Admin CRUD endpoints for the lifecycle data foundation (FI.2.12).

Exposes the warranty / AMC / monitoring-point / inventory / maintenance /
calibration tables built in FI.2.* so the admin app can manage them. All routes
are admin-only. A small factory keeps the eight near-identical CRUD surfaces
consistent; stock movements are append-only history (no update route).
"""
import uuid

from fastapi import APIRouter, HTTPException, Query

from app.api.deps import AdminUser, DB
from app.crud.base import CRUDBase
from app.crud.lifecycle import (
    crud_amc_contract,
    crud_calibration_record,
    crud_customer_warranty,
    crud_inventory_item,
    crud_maintenance_schedule,
    crud_monitoring_point,
    crud_stock_movement,
    crud_supplier_warranty,
)
from app.models.base_model import Base
from app.models.lifecycle import (
    AMCContract,
    CalibrationRecord,
    CustomerWarranty,
    InventoryItem,
    MaintenanceSchedule,
    MonitoringPoint,
    StockMovement,
    SupplierWarranty,
)
from app.schemas import lifecycle as s

router = APIRouter(tags=["lifecycle"])

# Optional list filters applied only when the model actually has the column.
_FILTER_FIELDS = ("project_id", "product_id", "supplier_id", "monitoring_point_id", "inventory_item_id")


def _register_crud(prefix: str, crud: CRUDBase, model: type[Base], read, create, update) -> None:
    sub = APIRouter(prefix=prefix)

    @sub.get("")
    async def list_items(
        db: DB,
        admin: AdminUser,
        skip: int = Query(0, ge=0),
        limit: int = Query(50, ge=1, le=200),
        project_id: uuid.UUID | None = None,
        product_id: uuid.UUID | None = None,
        supplier_id: uuid.UUID | None = None,
        monitoring_point_id: uuid.UUID | None = None,
        inventory_item_id: uuid.UUID | None = None,
        status: str | None = None,
    ):
        local = locals()
        filters = []
        for field in _FILTER_FIELDS:
            value = local.get(field)
            if value is not None and hasattr(model, field):
                filters.append(getattr(model, field) == value)
        if status is not None and hasattr(model, "status"):
            filters.append(model.status == status)
        items, total = await crud.get_multi(db, skip=skip, limit=limit, filters=filters or None)
        return {"items": [read.model_validate(i) for i in items], "total": total}

    @sub.get("/{id}", response_model=read)
    async def get_item(id: uuid.UUID, db: DB, admin: AdminUser):
        obj = await crud.get(db, id)
        if not obj:
            raise HTTPException(status_code=404, detail="Not found")
        return obj

    @sub.post("", response_model=read, status_code=201)
    async def create_item(data: create, db: DB, admin: AdminUser):
        return await crud.create(db, obj_in=data.model_dump())

    if update is not None:
        @sub.put("/{id}", response_model=read)
        async def update_item(id: uuid.UUID, data: update, db: DB, admin: AdminUser):
            obj = await crud.get(db, id)
            if not obj:
                raise HTTPException(status_code=404, detail="Not found")
            return await crud.update(db, db_obj=obj, obj_in=data.model_dump(exclude_unset=True))

    @sub.delete("/{id}")
    async def delete_item(id: uuid.UUID, db: DB, admin: AdminUser):
        ok = await crud.delete(db, id=id)
        if not ok:
            raise HTTPException(status_code=404, detail="Not found")
        return {"ok": True}

    router.include_router(sub)


_register_crud(
    "/supplier-warranties", crud_supplier_warranty, SupplierWarranty,
    s.SupplierWarrantyRead, s.SupplierWarrantyCreate, s.SupplierWarrantyUpdate,
)
_register_crud(
    "/customer-warranties", crud_customer_warranty, CustomerWarranty,
    s.CustomerWarrantyRead, s.CustomerWarrantyCreate, s.CustomerWarrantyUpdate,
)
_register_crud(
    "/amc-contracts", crud_amc_contract, AMCContract,
    s.AMCContractRead, s.AMCContractCreate, s.AMCContractUpdate,
)
_register_crud(
    "/monitoring-points", crud_monitoring_point, MonitoringPoint,
    s.MonitoringPointRead, s.MonitoringPointCreate, s.MonitoringPointUpdate,
)
_register_crud(
    "/inventory-items", crud_inventory_item, InventoryItem,
    s.InventoryItemRead, s.InventoryItemCreate, s.InventoryItemUpdate,
)
_register_crud(
    "/maintenance-schedules", crud_maintenance_schedule, MaintenanceSchedule,
    s.MaintenanceScheduleRead, s.MaintenanceScheduleCreate, s.MaintenanceScheduleUpdate,
)
_register_crud(
    "/calibration-records", crud_calibration_record, CalibrationRecord,
    s.CalibrationRecordRead, s.CalibrationRecordCreate, s.CalibrationRecordUpdate,
)
# Stock movements are append-only history: no update route.
_register_crud(
    "/stock-movements", crud_stock_movement, StockMovement,
    s.StockMovementRead, s.StockMovementCreate, None,
)
