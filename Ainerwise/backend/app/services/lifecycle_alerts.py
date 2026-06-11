"""Lifecycle due-date / low-stock queries (FI.3.6).

Feeds the admin lifecycle dashboard (FI.6.4) and notifications (FI.8.x):
low stock, expiring consumables, warranty expiry, calibration due, and AMC
renewal due.
"""
from __future__ import annotations

from datetime import date, timedelta
from typing import Any

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.lifecycle import (
    AMCContract,
    CustomerWarranty,
    InventoryItem,
    MaintenanceSchedule,
    MonitoringPoint,
)


async def low_stock_items(db: AsyncSession, *, limit: int = 100) -> list[InventoryItem]:
    """Items where available stock (quantity - reserved) is at or below reorder level."""
    result = await db.execute(
        select(InventoryItem)
        .where((InventoryItem.quantity - InventoryItem.reserved_quantity) <= InventoryItem.reorder_level)
        .order_by(InventoryItem.quantity)
        .limit(limit)
    )
    return list(result.scalars().all())


async def expiring_consumables(db: AsyncSession, *, within_days: int = 60, limit: int = 100) -> list[InventoryItem]:
    cutoff = date.today() + timedelta(days=within_days)
    result = await db.execute(
        select(InventoryItem)
        .where(InventoryItem.expiry_date.is_not(None), InventoryItem.expiry_date <= cutoff)
        .order_by(InventoryItem.expiry_date)
        .limit(limit)
    )
    return list(result.scalars().all())


async def warranty_expiring(db: AsyncSession, *, within_days: int = 90, limit: int = 100) -> list[CustomerWarranty]:
    cutoff = date.today() + timedelta(days=within_days)
    result = await db.execute(
        select(CustomerWarranty)
        .where(CustomerWarranty.end_date.is_not(None), CustomerWarranty.end_date <= cutoff)
        .order_by(CustomerWarranty.end_date)
        .limit(limit)
    )
    return list(result.scalars().all())


async def calibration_due(db: AsyncSession, *, within_days: int = 60, limit: int = 100) -> list[MonitoringPoint]:
    cutoff = date.today() + timedelta(days=within_days)
    result = await db.execute(
        select(MonitoringPoint)
        .where(MonitoringPoint.next_calibration_at.is_not(None), MonitoringPoint.next_calibration_at <= cutoff)
        .order_by(MonitoringPoint.next_calibration_at)
        .limit(limit)
    )
    return list(result.scalars().all())


async def amc_renewal_due(db: AsyncSession, *, within_days: int = 90, limit: int = 100) -> list[AMCContract]:
    cutoff = date.today() + timedelta(days=within_days)
    result = await db.execute(
        select(AMCContract)
        .where(
            or_(
                AMCContract.renewal_status == "renewal_due",
                (AMCContract.end_date.is_not(None)) & (AMCContract.end_date <= cutoff),
            )
        )
        .order_by(AMCContract.end_date)
        .limit(limit)
    )
    return list(result.scalars().all())


async def maintenance_due(db: AsyncSession, *, within_days: int = 30, limit: int = 100) -> list[MaintenanceSchedule]:
    cutoff = date.today() + timedelta(days=within_days)
    result = await db.execute(
        select(MaintenanceSchedule)
        .where(
            MaintenanceSchedule.due_date.is_not(None),
            MaintenanceSchedule.due_date <= cutoff,
            MaintenanceSchedule.status.notin_(["done", "skipped"]),
        )
        .order_by(MaintenanceSchedule.due_date)
        .limit(limit)
    )
    return list(result.scalars().all())


async def lifecycle_alert_summary(db: AsyncSession) -> dict[str, Any]:
    """Aggregate counts + items for the admin lifecycle dashboard."""
    low = await low_stock_items(db)
    expiring = await expiring_consumables(db)
    warranty = await warranty_expiring(db)
    calibration = await calibration_due(db)
    amc = await amc_renewal_due(db)
    maintenance = await maintenance_due(db)
    return {
        "low_stock": {"count": len(low), "items": low},
        "expiring_consumables": {"count": len(expiring), "items": expiring},
        "warranty_expiring": {"count": len(warranty), "items": warranty},
        "calibration_due": {"count": len(calibration), "items": calibration},
        "amc_renewal_due": {"count": len(amc), "items": amc},
        "maintenance_due": {"count": len(maintenance), "items": maintenance},
    }
