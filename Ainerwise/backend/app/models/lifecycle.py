"""Lifecycle data foundation models (FI.2.5 - FI.2.10).

Relational records for warranty, AMC, monitoring points, spare-parts inventory,
maintenance schedules, and calibration. JSONB is used only for genuinely
flexible policy details (coverage, exclusions, device lists); everything that
needs to be queried (dates, quantities, statuses, levels) is a real column.
"""
import uuid
from datetime import date

from sqlalchemy import Boolean, Date, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base_model import Base, TimestampMixin, UUIDMixin


class SupplierWarranty(Base, UUIDMixin, TimestampMixin):
    """FI.2.5 — Device-level warranty offered by a supplier to AinerWise."""
    __tablename__ = "supplier_warranties"

    supplier_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("companies.id"), nullable=True
    )
    product_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("products.id"), nullable=True
    )
    warranty_years: Mapped[int | None] = mapped_column(Integer)
    warranty_type: Mapped[str | None] = mapped_column(String(50))  # repair|replacement|parts_only|return_to_factory
    shipping_responsibility: Mapped[str | None] = mapped_column(String(50))  # supplier|ainerwise|customer|shared
    response_time_days: Mapped[int | None] = mapped_column(Integer)
    replacement_policy: Mapped[str | None] = mapped_column(Text)
    spare_parts_available: Mapped[bool] = mapped_column(Boolean, default=False)
    firmware_support: Mapped[bool] = mapped_column(Boolean, default=False)
    remote_debug_support: Mapped[bool] = mapped_column(Boolean, default=False)
    api_protocol_support: Mapped[bool] = mapped_column(Boolean, default=False)
    warranty_region_limit: Mapped[str | None] = mapped_column(String(255))
    notes: Mapped[str | None] = mapped_column(Text)


class CustomerWarranty(Base, UUIDMixin, TimestampMixin):
    """FI.2.6 — Coverage AinerWise provides to a customer on a project."""
    __tablename__ = "customer_warranties"

    project_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id"), nullable=True
    )
    customer_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("companies.id"), nullable=True
    )
    warranty_model: Mapped[str | None] = mapped_column(String(50))  # pass_through|managed|fast_replacement|premium_amc
    start_date: Mapped[date | None] = mapped_column(Date)
    end_date: Mapped[date | None] = mapped_column(Date)
    included_devices_json: Mapped[list | None] = mapped_column(JSONB)
    excluded_devices_json: Mapped[list | None] = mapped_column(JSONB)
    included_labor: Mapped[bool] = mapped_column(Boolean, default=False)
    included_remote_support: Mapped[bool] = mapped_column(Boolean, default=True)
    included_on_site_visits_per_year: Mapped[int | None] = mapped_column(Integer)
    spare_parts_included: Mapped[bool] = mapped_column(Boolean, default=False)
    max_claims_per_year: Mapped[int | None] = mapped_column(Integer)
    notes: Mapped[str | None] = mapped_column(Text)


class AMCContract(Base, UUIDMixin, TimestampMixin):
    """FI.2.7 — Annual Maintenance Contract: the recurring-revenue core."""
    __tablename__ = "amc_contracts"

    project_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id"), nullable=True
    )
    customer_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("companies.id"), nullable=True
    )
    package: Mapped[str | None] = mapped_column(String(50))  # basic|compliance|commercial|premium|enterprise
    pricing_mode: Mapped[str | None] = mapped_column(String(50))  # percentage|point_based|site_based|service_level
    start_date: Mapped[date | None] = mapped_column(Date)
    end_date: Mapped[date | None] = mapped_column(Date)
    renewal_status: Mapped[str] = mapped_column(String(50), default="active", nullable=False)
    coverage_json: Mapped[dict | None] = mapped_column(JSONB)
    exclusions_json: Mapped[list | None] = mapped_column(JSONB)
    included_visits_per_year: Mapped[int | None] = mapped_column(Integer)
    response_target_hours: Mapped[int | None] = mapped_column(Integer)
    recurring_fee: Mapped[float | None] = mapped_column(Float)
    currency: Mapped[str] = mapped_column(String(10), default="EUR")
    notes: Mapped[str | None] = mapped_column(Text)


class MonitoringPoint(Base, UUIDMixin, TimestampMixin):
    """FI.2.8 — A single monitored point (temperature, door, probe, tag, ...)."""
    __tablename__ = "monitoring_points"

    project_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id"), nullable=True
    )
    product_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("products.id"), nullable=True
    )
    solution_line: Mapped[str | None] = mapped_column(String(50))
    site: Mapped[str | None] = mapped_column(String(255))
    device_name: Mapped[str | None] = mapped_column(String(255))
    point_type: Mapped[str | None] = mapped_column(String(100))  # temperature|humidity|door|ph|...
    unit: Mapped[str | None] = mapped_column(String(50))
    threshold_min: Mapped[float | None] = mapped_column(Float)
    threshold_max: Mapped[float | None] = mapped_column(Float)
    calibration_cycle_months: Mapped[int | None] = mapped_column(Integer)
    last_calibrated_at: Mapped[date | None] = mapped_column(Date)
    next_calibration_at: Mapped[date | None] = mapped_column(Date)
    status: Mapped[str] = mapped_column(String(50), default="active", nullable=False)
    notes: Mapped[str | None] = mapped_column(Text)


class InventoryItem(Base, UUIDMixin, TimestampMixin):
    """FI.2.9 — Spare-parts / consumable stock record."""
    __tablename__ = "inventory_items"

    product_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("products.id"), nullable=True
    )
    supplier_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("companies.id"), nullable=True
    )
    reserved_for_project_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id"), nullable=True
    )
    name: Mapped[str | None] = mapped_column(String(500))
    location: Mapped[str | None] = mapped_column(String(255))
    quantity: Mapped[int] = mapped_column(Integer, default=0)
    reserved_quantity: Mapped[int] = mapped_column(Integer, default=0)
    min_stock_level: Mapped[int] = mapped_column(Integer, default=0)
    reorder_level: Mapped[int] = mapped_column(Integer, default=0)
    cost: Mapped[float | None] = mapped_column(Float)
    currency: Mapped[str] = mapped_column(String(10), default="EUR")
    expiry_date: Mapped[date | None] = mapped_column(Date)
    last_checked_at: Mapped[date | None] = mapped_column(Date)
    notes: Mapped[str | None] = mapped_column(Text)


class StockMovement(Base, UUIDMixin, TimestampMixin):
    """FI.2.9 — Inbound/outbound/reservation history for an inventory item."""
    __tablename__ = "stock_movements"

    inventory_item_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("inventory_items.id"), nullable=False
    )
    movement_type: Mapped[str] = mapped_column(String(50), nullable=False)  # inbound|outbound|reserve|release|adjustment
    quantity: Mapped[int] = mapped_column(Integer, default=0)
    project_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id"), nullable=True
    )
    reference: Mapped[str | None] = mapped_column(String(255))
    unit_cost: Mapped[float | None] = mapped_column(Float)
    notes: Mapped[str | None] = mapped_column(Text)
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )


class MaintenanceSchedule(Base, UUIDMixin, TimestampMixin):
    """FI.2.10 — Inspection / calibration / replacement task with due dates."""
    __tablename__ = "maintenance_schedules"

    project_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id"), nullable=True
    )
    monitoring_point_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("monitoring_points.id"), nullable=True
    )
    asset_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("assets.id"), nullable=True, index=True
    )
    device_name: Mapped[str | None] = mapped_column(String(255))
    task_type: Mapped[str | None] = mapped_column(String(50))  # inspection|calibration|battery_replace|...
    due_date: Mapped[date | None] = mapped_column(Date)
    frequency_months: Mapped[int | None] = mapped_column(Integer)
    assigned_to: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )
    status: Mapped[str] = mapped_column(String(50), default="scheduled", nullable=False)
    cost: Mapped[float | None] = mapped_column(Float)
    covered_by_amc: Mapped[bool] = mapped_column(Boolean, default=False)
    notes: Mapped[str | None] = mapped_column(Text)
    completion_json: Mapped[dict | None] = mapped_column(JSONB)  # photos/devices/tests at completion


class CalibrationRecord(Base, UUIDMixin, TimestampMixin):
    """FI.2.10 — Completed calibration with certificate, for audit traceability."""
    __tablename__ = "calibration_records"

    monitoring_point_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("monitoring_points.id"), nullable=True
    )
    project_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id"), nullable=True
    )
    calibration_date: Mapped[date | None] = mapped_column(Date)
    next_due_date: Mapped[date | None] = mapped_column(Date)
    calibration_method: Mapped[str | None] = mapped_column(String(255))
    certificate_file_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("file_assets.id"), nullable=True
    )
    technician: Mapped[str | None] = mapped_column(String(255))
    result: Mapped[str | None] = mapped_column(String(50))  # pass|fail|adjusted
    notes: Mapped[str | None] = mapped_column(Text)
