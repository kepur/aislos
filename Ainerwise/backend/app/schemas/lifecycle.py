"""Pydantic schemas for the lifecycle data foundation (FI.2.5 - FI.2.11).

Read / Create / Update for warranty, AMC, monitoring points, inventory, stock
movements, maintenance schedules, and calibration records. CRUD endpoints that
consume these are built in FI.2.12.
"""
import uuid
from datetime import date, datetime

from app.schemas.base import BaseSchema


# --- FI.2.5 Supplier Warranty ----------------------------------------------

class SupplierWarrantyBase(BaseSchema):
    supplier_id: uuid.UUID | None = None
    product_id: uuid.UUID | None = None
    warranty_years: int | None = None
    warranty_type: str | None = None
    shipping_responsibility: str | None = None
    response_time_days: int | None = None
    replacement_policy: str | None = None
    spare_parts_available: bool = False
    firmware_support: bool = False
    remote_debug_support: bool = False
    api_protocol_support: bool = False
    warranty_region_limit: str | None = None
    notes: str | None = None


class SupplierWarrantyCreate(SupplierWarrantyBase):
    pass


class SupplierWarrantyUpdate(BaseSchema):
    supplier_id: uuid.UUID | None = None
    product_id: uuid.UUID | None = None
    warranty_years: int | None = None
    warranty_type: str | None = None
    shipping_responsibility: str | None = None
    response_time_days: int | None = None
    replacement_policy: str | None = None
    spare_parts_available: bool | None = None
    firmware_support: bool | None = None
    remote_debug_support: bool | None = None
    api_protocol_support: bool | None = None
    warranty_region_limit: str | None = None
    notes: str | None = None


class SupplierWarrantyRead(SupplierWarrantyBase):
    id: uuid.UUID
    created_at: datetime


# --- FI.2.6 Customer Warranty ----------------------------------------------

class CustomerWarrantyBase(BaseSchema):
    project_id: uuid.UUID | None = None
    customer_id: uuid.UUID | None = None
    warranty_model: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    included_devices_json: list | None = None
    excluded_devices_json: list | None = None
    included_labor: bool = False
    included_remote_support: bool = True
    included_on_site_visits_per_year: int | None = None
    spare_parts_included: bool = False
    max_claims_per_year: int | None = None
    notes: str | None = None


class CustomerWarrantyCreate(CustomerWarrantyBase):
    pass


class CustomerWarrantyUpdate(BaseSchema):
    project_id: uuid.UUID | None = None
    customer_id: uuid.UUID | None = None
    warranty_model: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    included_devices_json: list | None = None
    excluded_devices_json: list | None = None
    included_labor: bool | None = None
    included_remote_support: bool | None = None
    included_on_site_visits_per_year: int | None = None
    spare_parts_included: bool | None = None
    max_claims_per_year: int | None = None
    notes: str | None = None


class CustomerWarrantyRead(CustomerWarrantyBase):
    id: uuid.UUID
    created_at: datetime


# --- FI.2.7 AMC Contract ----------------------------------------------------

class AMCContractBase(BaseSchema):
    project_id: uuid.UUID | None = None
    customer_id: uuid.UUID | None = None
    package: str | None = None
    pricing_mode: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    renewal_status: str = "active"
    coverage_json: dict | None = None
    exclusions_json: list | None = None
    included_visits_per_year: int | None = None
    response_target_hours: int | None = None
    recurring_fee: float | None = None
    currency: str = "EUR"
    notes: str | None = None


class AMCContractCreate(AMCContractBase):
    pass


class AMCContractUpdate(BaseSchema):
    project_id: uuid.UUID | None = None
    customer_id: uuid.UUID | None = None
    package: str | None = None
    pricing_mode: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    renewal_status: str | None = None
    coverage_json: dict | None = None
    exclusions_json: list | None = None
    included_visits_per_year: int | None = None
    response_target_hours: int | None = None
    recurring_fee: float | None = None
    currency: str | None = None
    notes: str | None = None


class AMCContractRead(AMCContractBase):
    id: uuid.UUID
    created_at: datetime


# --- FI.2.8 Monitoring Point -----------------------------------------------

class MonitoringPointBase(BaseSchema):
    project_id: uuid.UUID | None = None
    product_id: uuid.UUID | None = None
    solution_line: str | None = None
    site: str | None = None
    device_name: str | None = None
    point_type: str | None = None
    unit: str | None = None
    threshold_min: float | None = None
    threshold_max: float | None = None
    calibration_cycle_months: int | None = None
    last_calibrated_at: date | None = None
    next_calibration_at: date | None = None
    status: str = "active"
    notes: str | None = None


class MonitoringPointCreate(MonitoringPointBase):
    pass


class MonitoringPointUpdate(BaseSchema):
    project_id: uuid.UUID | None = None
    product_id: uuid.UUID | None = None
    solution_line: str | None = None
    site: str | None = None
    device_name: str | None = None
    point_type: str | None = None
    unit: str | None = None
    threshold_min: float | None = None
    threshold_max: float | None = None
    calibration_cycle_months: int | None = None
    last_calibrated_at: date | None = None
    next_calibration_at: date | None = None
    status: str | None = None
    notes: str | None = None


class MonitoringPointRead(MonitoringPointBase):
    id: uuid.UUID
    created_at: datetime


# --- FI.2.9 Inventory Item + Stock Movement --------------------------------

class InventoryItemBase(BaseSchema):
    product_id: uuid.UUID | None = None
    supplier_id: uuid.UUID | None = None
    reserved_for_project_id: uuid.UUID | None = None
    name: str | None = None
    location: str | None = None
    quantity: int = 0
    reserved_quantity: int = 0
    min_stock_level: int = 0
    reorder_level: int = 0
    cost: float | None = None
    currency: str = "EUR"
    expiry_date: date | None = None
    last_checked_at: date | None = None
    notes: str | None = None


class InventoryItemCreate(InventoryItemBase):
    pass


class InventoryItemUpdate(BaseSchema):
    product_id: uuid.UUID | None = None
    supplier_id: uuid.UUID | None = None
    reserved_for_project_id: uuid.UUID | None = None
    name: str | None = None
    location: str | None = None
    quantity: int | None = None
    reserved_quantity: int | None = None
    min_stock_level: int | None = None
    reorder_level: int | None = None
    cost: float | None = None
    currency: str | None = None
    expiry_date: date | None = None
    last_checked_at: date | None = None
    notes: str | None = None


class InventoryItemRead(InventoryItemBase):
    id: uuid.UUID
    created_at: datetime


class StockMovementBase(BaseSchema):
    inventory_item_id: uuid.UUID
    movement_type: str
    quantity: int = 0
    project_id: uuid.UUID | None = None
    reference: str | None = None
    unit_cost: float | None = None
    notes: str | None = None
    created_by: uuid.UUID | None = None


class StockMovementCreate(StockMovementBase):
    pass


class StockMovementRead(StockMovementBase):
    id: uuid.UUID
    created_at: datetime


# --- FI.2.10 Maintenance Schedule + Calibration Record ---------------------

class MaintenanceScheduleBase(BaseSchema):
    project_id: uuid.UUID | None = None
    monitoring_point_id: uuid.UUID | None = None
    device_name: str | None = None
    task_type: str | None = None
    due_date: date | None = None
    frequency_months: int | None = None
    assigned_to: uuid.UUID | None = None
    status: str = "scheduled"
    cost: float | None = None
    covered_by_amc: bool = False
    notes: str | None = None


class MaintenanceScheduleCreate(MaintenanceScheduleBase):
    pass


class MaintenanceScheduleUpdate(BaseSchema):
    project_id: uuid.UUID | None = None
    monitoring_point_id: uuid.UUID | None = None
    device_name: str | None = None
    task_type: str | None = None
    due_date: date | None = None
    frequency_months: int | None = None
    assigned_to: uuid.UUID | None = None
    status: str | None = None
    cost: float | None = None
    covered_by_amc: bool | None = None
    notes: str | None = None


class MaintenanceScheduleRead(MaintenanceScheduleBase):
    id: uuid.UUID
    created_at: datetime


class CalibrationRecordBase(BaseSchema):
    monitoring_point_id: uuid.UUID | None = None
    project_id: uuid.UUID | None = None
    calibration_date: date | None = None
    next_due_date: date | None = None
    calibration_method: str | None = None
    certificate_file_id: uuid.UUID | None = None
    technician: str | None = None
    result: str | None = None
    notes: str | None = None


class CalibrationRecordCreate(CalibrationRecordBase):
    pass


class CalibrationRecordUpdate(BaseSchema):
    monitoring_point_id: uuid.UUID | None = None
    project_id: uuid.UUID | None = None
    calibration_date: date | None = None
    next_due_date: date | None = None
    calibration_method: str | None = None
    certificate_file_id: uuid.UUID | None = None
    technician: str | None = None
    result: str | None = None
    notes: str | None = None


class CalibrationRecordRead(CalibrationRecordBase):
    id: uuid.UUID
    created_at: datetime
