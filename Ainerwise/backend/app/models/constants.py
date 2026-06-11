"""Shared taxonomy / enum-like constants for the lifecycle LTV platform.

Status and category fields are stored as String columns (see ARCHITECTURE.md)
and validated at the application level. These tuples are the canonical source of
truth shared by models, schemas, and services.
"""

# FI.2.1 — Solution-line taxonomy. Front-of-house brand stories; back-of-house
# recurring-revenue carriers. StorageGuard is the first sellable vertical.
SOLUTION_LINES = (
    "buildingbrain",
    "energyguard",
    "storageguard",
    "aquaguard",
    "kitchenguard",
    "assetpulse",
    "factorypulse",
    "agribrain",
)

# How a product earns recurring revenue (a product may carry several).
RECURRING_REVENUE_TYPES = (
    "none",
    "saas",
    "calibration",
    "consumable",
    "battery_replacement",
    "annual_inspection",
    "report_export",
    "alarm_monitoring",
    "algorithm_subscription",
    "tag_subscription",
)

SERVICE_DEPENDENCY_LEVELS = ("low", "medium", "high")

# Customer-facing warranty coverage model (FI.2.6).
WARRANTY_MODELS = ("pass_through", "managed", "fast_replacement", "premium_amc")

# Supplier-side warranty policy (FI.2.5).
WARRANTY_TYPES = ("repair", "replacement", "parts_only", "return_to_factory")
SHIPPING_RESPONSIBILITY = ("supplier", "ainerwise", "customer", "shared")

# AMC contracts (FI.2.7).
AMC_PACKAGES = ("basic", "compliance", "commercial", "premium", "enterprise")
AMC_PRICING_MODES = ("percentage", "point_based", "site_based", "service_level")
AMC_RENEWAL_STATUSES = ("active", "renewal_due", "renewed", "lapsed", "cancelled")

# Monitoring points (FI.2.8).
MONITORING_POINT_TYPES = (
    "temperature",
    "humidity",
    "door",
    "power",
    "ph",
    "conductivity",
    "turbidity",
    "cod",
    "gas",
    "co",
    "smoke",
    "water_leak",
    "vibration",
    "current",
    "energy",
    "asset_tag",
    "other",
)
MONITORING_POINT_STATUSES = ("active", "inactive", "fault", "maintenance")

# Inventory & stock movements (FI.2.9).
STOCK_MOVEMENT_TYPES = ("inbound", "outbound", "reserve", "release", "adjustment")

# Maintenance & calibration (FI.2.10).
MAINTENANCE_TASK_TYPES = (
    "inspection",
    "calibration",
    "battery_replace",
    "probe_replace",
    "firmware_update",
    "report_review",
)
MAINTENANCE_STATUSES = ("scheduled", "due", "in_progress", "done", "skipped")
CALIBRATION_RESULTS = ("pass", "fail", "adjusted")

# Ticket coverage resolution (FI.2.4 / FI.3.5).
TICKET_COVERAGE_TYPES = ("pass_through_warranty", "managed_warranty", "amc", "paid_service")

# Lead qualification bands (FI.2.3 / FI.6.2).
POTENTIAL_LEVELS = ("low", "medium", "high")
COMPLIANCE_RISK_LEVELS = ("none", "low", "medium", "high")
