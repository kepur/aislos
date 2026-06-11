from app.crud.base import CRUDBase
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

crud_supplier_warranty = CRUDBase[SupplierWarranty](SupplierWarranty)
crud_customer_warranty = CRUDBase[CustomerWarranty](CustomerWarranty)
crud_amc_contract = CRUDBase[AMCContract](AMCContract)
crud_monitoring_point = CRUDBase[MonitoringPoint](MonitoringPoint)
crud_inventory_item = CRUDBase[InventoryItem](InventoryItem)
crud_stock_movement = CRUDBase[StockMovement](StockMovement)
crud_maintenance_schedule = CRUDBase[MaintenanceSchedule](MaintenanceSchedule)
crud_calibration_record = CRUDBase[CalibrationRecord](CalibrationRecord)
