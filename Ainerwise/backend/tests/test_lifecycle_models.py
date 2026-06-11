"""Tests for the lifecycle data foundation (FI.2.1 - FI.2.11).

Covers the solution_line taxonomy, the public privacy boundary on product
schemas, model/table registration, schema validation, and an ORM round-trip
against the database (rolled back so it leaves no residue).
"""
import asyncio
from datetime import date

from app.db.session import async_session_factory, engine
from app.models import (
    AMCContract,
    CalibrationRecord,
    CustomerWarranty,
    InventoryItem,
    MaintenanceSchedule,
    MonitoringPoint,
    StockMovement,
    SupplierWarranty,
)
from app.models.base_model import Base
from app.models.constants import RECURRING_REVENUE_TYPES, SOLUTION_LINES
from app.schemas.product import ProductCreate, ProductRead, ProductUpdate
from app.schemas import lifecycle as lschemas


# --- FI.2.1 taxonomy --------------------------------------------------------

def test_solution_line_taxonomy():
    assert SOLUTION_LINES == (
        "buildingbrain", "energyguard", "storageguard", "aquaguard",
        "kitchenguard", "assetpulse", "factorypulse", "agribrain",
    )
    assert "storageguard" in SOLUTION_LINES
    assert "calibration" in RECURRING_REVENUE_TYPES


# --- FI.2.2 privacy boundary on product schemas -----------------------------

def test_product_read_hides_supplier_and_margin():
    read_fields = set(ProductRead.model_fields)
    for sensitive in ("internal_model", "supplier_id", "cost_price", "replacement_margin_percent"):
        assert sensitive not in read_fields, f"{sensitive} must not be in public ProductRead"
    # but public lifecycle fields are exposed
    assert "solution_line" in read_fields
    assert "amc_recommended" in read_fields


def test_product_admin_schemas_expose_sensitive_fields():
    for schema in (ProductCreate, ProductUpdate):
        fields = set(schema.model_fields)
        assert "internal_model" in fields
        assert "supplier_id" in fields
        assert "replacement_margin_percent" in fields
        assert "solution_line" in fields


# --- FI.2.5 - FI.2.10 model/table registration ------------------------------

def test_lifecycle_tables_registered():
    expected = {
        "supplier_warranties",
        "customer_warranties",
        "amc_contracts",
        "monitoring_points",
        "inventory_items",
        "stock_movements",
        "maintenance_schedules",
        "calibration_records",
    }
    assert expected.issubset(set(Base.metadata.tables))


def test_lifecycle_schemas_validate():
    lschemas.SupplierWarrantyCreate(warranty_years=3, warranty_type="replacement")
    lschemas.CustomerWarrantyCreate(warranty_model="managed", start_date=date(2026, 1, 1))
    lschemas.AMCContractCreate(package="compliance", pricing_mode="point_based", recurring_fee=1200.0)
    lschemas.MonitoringPointCreate(point_type="temperature", unit="C", threshold_min=2, threshold_max=8)
    lschemas.InventoryItemCreate(name="Temp probe", quantity=10, min_stock_level=2)
    lschemas.StockMovementCreate(inventory_item_id=_uuid(), movement_type="inbound", quantity=5)
    lschemas.MaintenanceScheduleCreate(task_type="calibration", frequency_months=12)
    lschemas.CalibrationRecordCreate(result="pass", calibration_date=date(2026, 5, 1))


def _uuid():
    import uuid
    return uuid.uuid4()


# --- FI.2.11 ORM round-trip (rolled back) -----------------------------------

def test_lifecycle_orm_roundtrip():
    async def _run():
        # Each asyncio.run() uses a fresh loop; dispose the shared engine pool so
        # connections aren't reused across loops (avoids cross-test failures).
        await engine.dispose()
        async with async_session_factory() as db:
            amc = AMCContract(package="compliance", pricing_mode="point_based", recurring_fee=1500.0)
            point = MonitoringPoint(
                solution_line="storageguard", point_type="temperature", unit="C",
                threshold_min=2, threshold_max=8, calibration_cycle_months=12,
            )
            inv = InventoryItem(name="Spare probe", quantity=12, min_stock_level=3, reorder_level=5)
            db.add_all([amc, point, inv])
            await db.flush()

            move = StockMovement(inventory_item_id=inv.id, movement_type="inbound", quantity=12)
            sched = MaintenanceSchedule(
                monitoring_point_id=point.id, task_type="calibration",
                due_date=date(2027, 1, 1), frequency_months=12, covered_by_amc=True,
            )
            cal = CalibrationRecord(
                monitoring_point_id=point.id, calibration_date=date(2026, 1, 1),
                next_due_date=date(2027, 1, 1), result="pass",
            )
            sw = SupplierWarranty(warranty_years=2, warranty_type="replacement", spare_parts_available=True)
            cw = CustomerWarranty(warranty_model="managed", included_remote_support=True)
            db.add_all([move, sched, cal, sw, cw])
            await db.flush()

            # All rows got UUIDs and FK links resolved.
            assert amc.id and point.id and inv.id
            assert move.inventory_item_id == inv.id
            assert sched.monitoring_point_id == point.id
            assert cal.monitoring_point_id == point.id
            # Server defaults / python defaults applied.
            assert amc.renewal_status == "active"
            assert point.status == "active"
            assert sched.covered_by_amc is True

            await db.rollback()  # leave no residue

    asyncio.run(_run())
