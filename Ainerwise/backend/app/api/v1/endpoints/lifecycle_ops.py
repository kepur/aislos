"""Lifecycle operations endpoints (FI.3.2 - FI.3.7).

Admin-only helpers built on the lifecycle data layer:
- AMC catalog + pricing quote (FI.3.1, FI.3.2)
- spare-kit recommendation + fast-replacement rules (FI.3.3, FI.3.4)
- warranty coverage evaluator (FI.3.5)
- due-date / low-stock alert summary (FI.3.6)
- contract-boundary template (FI.3.7)
"""
import uuid

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.api.deps import AdminUser, DB
from app.crud.ticket import crud_ticket
from app.schemas import lifecycle as ls
from app.schemas.ticket import TicketRead
from app.services import amc, lifecycle_alerts, spare_parts, warranty

router = APIRouter(tags=["lifecycle-ops"])


# --- FI.3.1 / FI.3.2 AMC catalog + pricing ---------------------------------

@router.get("/amc-catalog")
async def get_amc_catalog(admin: AdminUser):
    return {"baseline": amc.BASELINE_REMOTE_ASSURANCE, "catalog": amc.AMC_CATALOG}


class AMCQuoteRequest(BaseModel):
    mode: str  # percentage | point_based | site_based | service_level
    solution_line: str | None = None
    project_value: float | None = None
    points: dict[str, int] | None = None
    sites: int | None = None
    site_fee: float | None = None
    base_fee: float | None = None
    tier: str | None = None


@router.post("/amc-catalog/quote")
async def quote_amc(data: AMCQuoteRequest, admin: AdminUser):
    return amc.amc_annual_fee(
        mode=data.mode, solution_line=data.solution_line, project_value=data.project_value,
        points=data.points, sites=data.sites, site_fee=data.site_fee, base_fee=data.base_fee,
        tier=data.tier,
    )


# --- FI.3.3 / FI.3.4 spare parts -------------------------------------------

class SpareKitItem(BaseModel):
    category: str
    qty: int
    unit_cost: float | None = None


class SpareKitRequest(BaseModel):
    items: list[SpareKitItem]
    plan: str = "customer_owned"


@router.post("/spare-kit/recommend")
async def recommend_spare_kit(data: SpareKitRequest, admin: AdminUser):
    return spare_parts.recommend_spare_kit([i.model_dump() for i in data.items], plan=data.plan)


@router.get("/fast-replacement-plan")
async def get_fast_replacement_plan(admin: AdminUser):
    return spare_parts.FAST_REPLACEMENT_PLAN


# --- FI.3.5 warranty coverage evaluator ------------------------------------

class CoverageRequest(BaseModel):
    cause: str | None = None
    amc_covered: bool = False
    within_supplier_warranty: bool = False
    managed_warranty: bool = False
    fast_replacement: bool = False


@router.post("/warranty/evaluate-coverage")
async def evaluate_coverage(data: CoverageRequest, admin: AdminUser):
    return warranty.evaluate_coverage(**data.model_dump())


class TicketCoverageRequest(BaseModel):
    cause: str | None = None
    within_supplier_warranty: bool = False
    managed_warranty: bool = False
    fast_replacement: bool = False
    persist: bool = True


@router.post("/tickets/{ticket_id}/evaluate-coverage")
async def evaluate_ticket_coverage(ticket_id: uuid.UUID, data: TicketCoverageRequest, db: DB, admin: AdminUser):
    ticket = await crud_ticket.get(db, ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    result = warranty.evaluate_coverage(
        cause=data.cause,
        amc_covered=bool(ticket.amc_covered),
        within_supplier_warranty=data.within_supplier_warranty,
        managed_warranty=data.managed_warranty,
        fast_replacement=data.fast_replacement,
    )
    if data.persist:
        await crud_ticket.update(db, db_obj=ticket, obj_in={
            "coverage_type": result["coverage_type"],
            "is_paid_service": result["customer_pays"],
            "warranty_related": result["coverage_type"] in ("pass_through_warranty", "managed_warranty"),
        })
    return {"ticket": TicketRead.model_validate(ticket), "coverage": result}


# --- FI.3.7 contract-boundary template -------------------------------------

@router.get("/contract-boundary-template")
async def get_contract_boundary_template(admin: AdminUser):
    return amc.CONTRACT_BOUNDARY_TEMPLATE


# --- FI.3.6 lifecycle alert summary ----------------------------------------

_ALERT_SCHEMAS = {
    "low_stock": ls.InventoryItemRead,
    "expiring_consumables": ls.InventoryItemRead,
    "warranty_expiring": ls.CustomerWarrantyRead,
    "calibration_due": ls.MonitoringPointRead,
    "amc_renewal_due": ls.AMCContractRead,
    "maintenance_due": ls.MaintenanceScheduleRead,
}


@router.get("/lifecycle/alerts")
async def get_lifecycle_alerts(db: DB, admin: AdminUser):
    summary = await lifecycle_alerts.lifecycle_alert_summary(db)
    serialized = {}
    for key, block in summary.items():
        schema = _ALERT_SCHEMAS[key]
        serialized[key] = {
            "count": block["count"],
            "items": [schema.model_validate(i) for i in block["items"]],
        }
    return serialized
