"""Seed a normalized StorageGuard lifecycle demo dataset.

Run from the backend container or backend directory:
    python -m scripts.seed_lifecycle_demo

The seed is idempotent: rerunning it updates the named demo records instead of
adding duplicates. It complements create_demo_buyer.py, which owns the public
buyer-facing project_plan_json used by both PC and H5 portals.
"""
import asyncio
import sys
from datetime import date

sys.path.insert(0, "/app")

from sqlalchemy import func, select

from app.db.session import async_session_factory
from app.models.finance import PlatformFeeRule, ProjectFinance
from app.models.lead import Lead
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
from app.models.product import Product, ProductCategory
from app.models.project import Project
from app.models.ticket import Ticket
from app.models.user import Company, User
from app.services.finance import compute_finance
from scripts.create_demo_buyer import (
    DEMO_EMAIL,
    STORAGEGUARD_PROJECT_TITLE,
    main as ensure_demo_buyer,
)


SUPPLIER_NAME = "StorageGuard Demo Supply"
CATEGORY_SLUG = "storageguard-monitoring"
WAREHOUSE = "Belgrade Service Locker"


def apply_values(record, values):
    for key, value in values.items():
        setattr(record, key, value)
    return record


async def one(db, model, *conditions):
    result = await db.execute(select(model).where(*conditions))
    return result.scalar_one_or_none()


async def ensure_company(db):
    supplier = await one(db, Company, Company.name == SUPPLIER_NAME)
    values = {
        "type": "vendor",
        "country": "China",
        "city": "Shenzhen",
        "verification_status": "verified",
        "contact_info": {
            "email": "storageguard-demo-supplier@example.com",
            "note": "Demo supplier record only",
        },
        "description": "Demo OEM supplier for the StorageGuard lifecycle walkthrough.",
    }
    if supplier:
        return apply_values(supplier, values)
    supplier = Company(name=SUPPLIER_NAME, **values)
    db.add(supplier)
    await db.flush()
    return supplier


async def ensure_category(db):
    category = await one(db, ProductCategory, ProductCategory.slug == CATEGORY_SLUG)
    values = {
        "name": "StorageGuard Monitoring",
        "icon": "thermometer",
        "sort_order": 70,
    }
    if category:
        return apply_values(category, values)
    category = ProductCategory(slug=CATEGORY_SLUG, **values)
    db.add(category)
    await db.flush()
    return category


async def ensure_products(db, supplier, category):
    product_defs = [
        {
            "slug": "storageguard-edge-gateway-demo",
            "name": "StorageGuard Edge Gateway",
            "public_name": "StorageGuard Edge Gateway",
            "internal_model": "SG-GW-4G-RS485-DEMO",
            "description": "Local-buffering gateway for cold-chain alert delivery.",
            "specs_json": {"uplink": ["Ethernet", "4G"], "protocols": ["LoRa", "Modbus", "MQTT"]},
            "cost_price": 185.0,
            "list_price": 420.0,
            "warranty_years": 3,
            "recurring_revenue_types_json": ["saas", "alarm_monitoring", "annual_inspection"],
            "expected_lifetime_months": 72,
            "replacement_margin_percent": 45.0,
            "required_for_compliance": True,
            "report_template_available": True,
            "amc_required": True,
            "amc_recommended": True,
            "service_dependency_level": "high",
        },
        {
            "slug": "storageguard-temp-humidity-node-demo",
            "name": "Cold Room Temperature and Humidity Node",
            "public_name": "Cold Room Temperature and Humidity Monitoring Point",
            "internal_model": "SG-TH-LORA-IP65-DEMO",
            "description": "Calibratable temperature and humidity sensing node.",
            "specs_json": {"rating": "IP65", "protocol": "LoRa", "battery": "replaceable"},
            "cost_price": 48.0,
            "list_price": 128.0,
            "warranty_years": 3,
            "recurring_revenue_types_json": ["calibration", "battery_replacement", "report_export"],
            "consumable_cycle_months": 18,
            "calibration_cycle_months": 12,
            "expected_lifetime_months": 60,
            "replacement_margin_percent": 52.0,
            "required_for_compliance": True,
            "report_template_available": True,
            "amc_required": True,
            "amc_recommended": True,
            "service_dependency_level": "high",
        },
        {
            "slug": "storageguard-door-sensor-demo",
            "name": "Cold Room Door Event Sensor",
            "public_name": "Cold Room Door Event Sensor",
            "internal_model": "SG-DOOR-LORA-DEMO",
            "description": "Battery-powered door event sensor for audit trails.",
            "specs_json": {"protocol": "LoRa", "battery": "replaceable"},
            "cost_price": 26.0,
            "list_price": 76.0,
            "warranty_years": 3,
            "recurring_revenue_types_json": ["battery_replacement", "report_export"],
            "consumable_cycle_months": 18,
            "expected_lifetime_months": 60,
            "replacement_margin_percent": 48.0,
            "required_for_compliance": True,
            "report_template_available": True,
            "amc_required": False,
            "amc_recommended": True,
            "service_dependency_level": "medium",
        },
        {
            "slug": "storageguard-outage-monitor-demo",
            "name": "StorageGuard Power Outage Alert Node",
            "public_name": "StorageGuard Power Outage Alert Node",
            "internal_model": "SG-POWER-ALERT-DEMO",
            "description": "Power availability node for outage alerts and escalation.",
            "specs_json": {"protocol": "LoRa", "backup_power": "internal battery"},
            "cost_price": 38.0,
            "list_price": 96.0,
            "warranty_years": 3,
            "recurring_revenue_types_json": ["alarm_monitoring", "annual_inspection"],
            "consumable_cycle_months": 24,
            "expected_lifetime_months": 60,
            "replacement_margin_percent": 46.0,
            "required_for_compliance": True,
            "report_template_available": True,
            "amc_required": False,
            "amc_recommended": True,
            "service_dependency_level": "medium",
        },
    ]
    products = {}
    shared = {
        "owner_company_id": supplier.id,
        "supplier_id": supplier.id,
        "source_type": "official",
        "category_id": category.id,
        "brand": "AinerWise StorageGuard",
        "currency": "EUR",
        "moq": 1,
        "lead_time_days": 21,
        "service_available": True,
        "service_term_years_json": [3, 5, 8],
        "solution_line": "storageguard",
        "status": "published",
    }
    for item in product_defs:
        slug = item["slug"]
        product = await one(db, Product, Product.slug == slug)
        values = {**shared, **item}
        if product:
            apply_values(product, values)
        else:
            product = Product(**values)
            db.add(product)
            await db.flush()
        products[slug] = product
    return products


async def ensure_supplier_warranties(db, supplier, products):
    for product in products.values():
        warranty = await one(
            db,
            SupplierWarranty,
            SupplierWarranty.supplier_id == supplier.id,
            SupplierWarranty.product_id == product.id,
        )
        values = {
            "warranty_years": 3,
            "warranty_type": "replacement",
            "shipping_responsibility": "shared",
            "response_time_days": 7,
            "replacement_policy": "Supplier replacement after remote diagnosis. AinerWise demo reserve may be used first.",
            "spare_parts_available": True,
            "firmware_support": True,
            "remote_debug_support": True,
            "api_protocol_support": True,
            "warranty_region_limit": "Serbia",
            "notes": "Demo supplier warranty. On-site labor is not included.",
        }
        if warranty:
            apply_values(warranty, values)
        else:
            db.add(SupplierWarranty(supplier_id=supplier.id, product_id=product.id, **values))


async def ensure_customer_warranty(db, project, customer):
    warranty = await one(db, CustomerWarranty, CustomerWarranty.project_id == project.id)
    values = {
        "customer_id": customer.id,
        "warranty_model": "managed",
        "start_date": date(2026, 1, 15),
        "end_date": date(2029, 1, 14),
        "included_devices_json": [
            "StorageGuard Edge Gateway",
            "Temperature and humidity monitoring nodes",
            "Door event sensors",
            "Power outage alert nodes",
        ],
        "excluded_devices_json": ["Third-party network equipment", "Damage caused by misuse"],
        "included_labor": False,
        "included_remote_support": True,
        "included_on_site_visits_per_year": 0,
        "spare_parts_included": False,
        "max_claims_per_year": 4,
        "notes": "Three-year remote assurance. On-site visits and non-hardware-fault labor are quoted separately.",
    }
    if warranty:
        return apply_values(warranty, values)
    warranty = CustomerWarranty(project_id=project.id, **values)
    db.add(warranty)
    return warranty


async def ensure_amc(db, project, customer):
    amc = await one(
        db,
        AMCContract,
        AMCContract.project_id == project.id,
        AMCContract.package == "compliance",
    )
    values = {
        "customer_id": customer.id,
        "pricing_mode": "point_based",
        "start_date": date(2026, 1, 15),
        "end_date": date(2027, 1, 14),
        "renewal_status": "active",
        "coverage_json": {
            "monitoring_points": 24,
            "remote_support": True,
            "monthly_compliance_report": True,
            "annual_calibration_plan": True,
            "alarm_escalation": ["Telegram", "email", "phone after 15 minutes"],
        },
        "exclusions_json": ["On-site attendance", "Third-party network faults", "Customer-caused damage"],
        "included_visits_per_year": 0,
        "response_target_hours": 4,
        "recurring_fee": 3600.0,
        "currency": "EUR",
        "notes": "Compliance AMC demo. On-site work is quoted separately unless added by contract.",
    }
    if amc:
        return apply_values(amc, values)
    amc = AMCContract(project_id=project.id, package="compliance", **values)
    db.add(amc)
    return amc


async def ensure_monitoring_point(db, project, product, **values):
    point = await one(
        db,
        MonitoringPoint,
        MonitoringPoint.project_id == project.id,
        MonitoringPoint.device_name == values["device_name"],
        MonitoringPoint.point_type == values["point_type"],
    )
    shared = {
        "product_id": product.id,
        "solution_line": "storageguard",
        "status": "active",
    }
    if point:
        return apply_values(point, {**shared, **values})
    point = MonitoringPoint(project_id=project.id, **shared, **values)
    db.add(point)
    await db.flush()
    return point


async def ensure_monitoring_points(db, project, products):
    sensor = products["storageguard-temp-humidity-node-demo"]
    door_sensor = products["storageguard-door-sensor-demo"]
    power_sensor = products["storageguard-outage-monitor-demo"]
    points = []
    rooms = ["Chiller Room A", "Chiller Room B", "Chiller Room C", "Freezer 1"]

    for room in rooms:
        for index in range(1, 4):
            is_freezer = room == "Freezer 1"
            points.append(
                await ensure_monitoring_point(
                    db,
                    project,
                    sensor,
                    site=room,
                    device_name=f"{room} Temperature {index}",
                    point_type="temperature",
                    unit="C",
                    threshold_min=-22.0 if is_freezer else 2.0,
                    threshold_max=-16.0 if is_freezer else 8.0,
                    calibration_cycle_months=12,
                    last_calibrated_at=date(2025, 6, 10),
                    next_calibration_at=date(2026, 5, 20) if room == "Freezer 1" and index == 1 else date(2027, 1, 15),
                    notes="Demo compliance monitoring point.",
                )
            )

    for room in rooms[:3]:
        for index in range(1, 3):
            points.append(
                await ensure_monitoring_point(
                    db,
                    project,
                    sensor,
                    site=room,
                    device_name=f"{room} Humidity {index}",
                    point_type="humidity",
                    unit="%RH",
                    threshold_min=30.0,
                    threshold_max=75.0,
                    calibration_cycle_months=12,
                    last_calibrated_at=date(2025, 6, 10),
                    next_calibration_at=date(2026, 6, 10) if room == "Chiller Room A" and index == 1 else date(2027, 1, 15),
                    notes="Demo compliance monitoring point.",
                )
            )

    for room in rooms:
        points.append(
            await ensure_monitoring_point(
                db,
                project,
                door_sensor,
                site=room,
                device_name=f"{room} Door",
                point_type="door",
                unit="event",
                notes="Door-open event logging for the monthly compliance report.",
            )
        )

    for site in ["Main Distribution Board", "Backup Power Feed"]:
        points.append(
            await ensure_monitoring_point(
                db,
                project,
                power_sensor,
                site=site,
                device_name=site,
                point_type="power",
                unit="state",
                notes="Outage alert and escalation demo point.",
            )
        )
    return points


async def ensure_inventory_item(db, supplier, project, product, name, **values):
    item = await one(
        db,
        InventoryItem,
        InventoryItem.name == name,
        InventoryItem.location == WAREHOUSE,
    )
    shared = {
        "product_id": product.id if product else None,
        "supplier_id": supplier.id,
        "reserved_for_project_id": project.id,
        "location": WAREHOUSE,
        "currency": "EUR",
        "last_checked_at": date(2026, 6, 1),
    }
    if item:
        return apply_values(item, {**shared, **values})
    item = InventoryItem(name=name, **shared, **values)
    db.add(item)
    await db.flush()
    return item


async def ensure_stock_movement(db, item, project, user, movement_type, quantity, reference, unit_cost):
    movement = await one(
        db,
        StockMovement,
        StockMovement.inventory_item_id == item.id,
        StockMovement.reference == reference,
        StockMovement.movement_type == movement_type,
    )
    values = {
        "quantity": quantity,
        "project_id": project.id,
        "unit_cost": unit_cost,
        "notes": "Demo stock movement.",
        "created_by": user.id,
    }
    if movement:
        return apply_values(movement, values)
    movement = StockMovement(
        inventory_item_id=item.id,
        movement_type=movement_type,
        reference=reference,
        **values,
    )
    db.add(movement)
    return movement


async def ensure_inventory(db, supplier, project, user, products):
    inventory_defs = [
        ("Edge gateway reserve", products["storageguard-edge-gateway-demo"], 1, 1, 1, 2, 185.0, None),
        ("Temperature and humidity node reserve", products["storageguard-temp-humidity-node-demo"], 8, 3, 3, 5, 48.0, None),
        ("Door sensor reserve", products["storageguard-door-sensor-demo"], 3, 2, 2, 4, 26.0, None),
        ("StorageGuard sensor battery pack", None, 20, 8, 10, 15, 4.5, date(2026, 6, 20)),
    ]
    items = []
    for name, product, quantity, reserved, minimum, reorder, cost, expiry in inventory_defs:
        item = await ensure_inventory_item(
            db,
            supplier,
            project,
            product,
            name,
            quantity=quantity,
            reserved_quantity=reserved,
            min_stock_level=minimum,
            reorder_level=reorder,
            cost=cost,
            expiry_date=expiry,
            notes="Demo lifecycle reserve stock; reorder threshold intentionally exercises dashboard alerts.",
        )
        items.append(item)
        await ensure_stock_movement(db, item, project, user, "inbound", quantity, f"DEMO-IN-{item.name}", cost)
        await ensure_stock_movement(db, item, project, user, "reserve", reserved, f"DEMO-RESERVE-{item.name}", cost)
    return items


async def ensure_maintenance_task(db, project, point, **values):
    task = await one(
        db,
        MaintenanceSchedule,
        MaintenanceSchedule.project_id == project.id,
        MaintenanceSchedule.device_name == values["device_name"],
        MaintenanceSchedule.task_type == values["task_type"],
    )
    shared = {"monitoring_point_id": point.id if point else None}
    if task:
        return apply_values(task, {**shared, **values})
    task = MaintenanceSchedule(project_id=project.id, **shared, **values)
    db.add(task)
    return task


async def ensure_maintenance(db, project, points):
    by_name = {point.device_name: point for point in points}
    await ensure_maintenance_task(
        db,
        project,
        by_name["Freezer 1 Temperature 1"],
        device_name="Freezer 1 Temperature 1",
        task_type="calibration",
        due_date=date(2026, 5, 20),
        frequency_months=12,
        status="due",
        cost=45.0,
        covered_by_amc=True,
        notes="Overdue demo task to exercise lifecycle alerting.",
    )
    await ensure_maintenance_task(
        db,
        project,
        by_name["Chiller Room A Humidity 1"],
        device_name="Chiller Room A Humidity 1",
        task_type="calibration",
        due_date=date(2026, 6, 10),
        frequency_months=12,
        status="scheduled",
        cost=45.0,
        covered_by_amc=True,
        notes="Upcoming demo calibration.",
    )
    await ensure_maintenance_task(
        db,
        project,
        None,
        device_name="StorageGuard Edge Gateway",
        task_type="inspection",
        due_date=date(2026, 6, 5),
        frequency_months=12,
        status="scheduled",
        cost=75.0,
        covered_by_amc=True,
        notes="Remote gateway health inspection.",
    )
    await ensure_maintenance_task(
        db,
        project,
        None,
        device_name="Monthly HACCP Compliance Summary",
        task_type="report_review",
        due_date=date(2026, 6, 7),
        frequency_months=1,
        status="scheduled",
        cost=40.0,
        covered_by_amc=True,
        notes="Monthly report QA before customer delivery.",
    )


async def ensure_calibration_record(db, project, point, result, notes):
    calibration = await one(
        db,
        CalibrationRecord,
        CalibrationRecord.project_id == project.id,
        CalibrationRecord.monitoring_point_id == point.id,
        CalibrationRecord.calibration_date == date(2025, 6, 10),
    )
    values = {
        "next_due_date": date(2026, 6, 10),
        "calibration_method": "Reference probe comparison",
        "technician": "Demo Calibration Partner",
        "result": result,
        "notes": notes,
    }
    if calibration:
        return apply_values(calibration, values)
    calibration = CalibrationRecord(
        project_id=project.id,
        monitoring_point_id=point.id,
        calibration_date=date(2025, 6, 10),
        **values,
    )
    db.add(calibration)
    return calibration


async def ensure_calibrations(db, project, points):
    by_name = {point.device_name: point for point in points}
    await ensure_calibration_record(
        db,
        project,
        by_name["Chiller Room A Temperature 1"],
        "pass",
        "Demo certificate reference: SG-CAL-2025-001.",
    )
    await ensure_calibration_record(
        db,
        project,
        by_name["Freezer 1 Temperature 1"],
        "adjusted",
        "Demo certificate reference: SG-CAL-2025-002. Offset corrected during calibration.",
    )


async def ensure_finance(db, project, customer):
    finance = await one(db, ProjectFinance, ProjectFinance.project_id == project.id)
    values = {
        "customer_id": customer.id,
        "solution_line": "storageguard",
        "currency": "EUR",
        "contract_total": 12400.0,
        "hardware_revenue": 6800.0,
        "design_fee": 900.0,
        "installation_fee": 1800.0,
        "integration_fee": 1000.0,
        "platform_fee": 800.0,
        "project_management_fee": 1100.0,
        "amc_fee_year_1": 3600.0,
        "amc_fee_annual": 3600.0,
        "consumable_revenue_estimate": 420.0,
        "calibration_revenue_estimate": 720.0,
        "report_revenue_estimate": 600.0,
        "alarm_monitoring_revenue_estimate": 480.0,
        "supplier_cost": 3900.0,
        "shipping_cost": 420.0,
        "customs_cost": 300.0,
        "local_installer_cost": 1200.0,
        "labor_cost": 850.0,
        "travel_cost": 180.0,
        "spare_parts_cost": 700.0,
        "warranty_reserve_cost": 300.0,
        "annual_service_cost": 1400.0,
        "notes": "Demo StorageGuard economics. Supplier cost and margin are admin-only.",
    }
    values.update(compute_finance(values))
    if finance:
        return apply_values(finance, values)
    finance = ProjectFinance(project_id=project.id, **values)
    db.add(finance)
    return finance


async def ensure_platform_fee_rule(db):
    rule = await one(db, PlatformFeeRule, PlatformFeeRule.name == "StorageGuard medium project demo")
    values = {
        "solution_line": "storageguard",
        "project_size_band": "medium",
        "fee_type": "hybrid",
        "percentage": 0.05,
        "fixed_fee": 180.0,
        "min_fee": 500.0,
        "max_fee": 1800.0,
        "is_active": True,
        "notes": "Demo fee rule for StorageGuard projects.",
    }
    if rule:
        return apply_values(rule, values)
    rule = PlatformFeeRule(name="StorageGuard medium project demo", **values)
    db.add(rule)
    return rule


async def ensure_ticket(db, project, customer, user, point, **values):
    ticket = await one(
        db,
        Ticket,
        Ticket.project_id == project.id,
        Ticket.title == values["title"],
    )
    shared = {
        "buyer_company_id": customer.id,
        "buyer_user_id": user.id,
        "monitoring_point_id": point.id if point else None,
    }
    if ticket:
        return apply_values(ticket, {**shared, **values})
    ticket = Ticket(project_id=project.id, **shared, **values)
    db.add(ticket)
    return ticket


async def ensure_tickets(db, project, customer, user, points):
    by_name = {point.device_name: point for point in points}
    await ensure_ticket(
        db,
        project,
        customer,
        user,
        by_name["Freezer 1 Temperature 1"],
        issue_type="alarm_follow_up",
        priority="high",
        title="Freezer 1 temperature excursion follow-up",
        description="Sample alert review after a 41-minute temperature excursion.",
        status="open",
        affected_device="Freezer 1 Temperature 1",
        warranty_related=False,
        amc_covered=True,
        is_paid_service=False,
        coverage_type="amc",
        estimated_cost=0.0,
    )
    await ensure_ticket(
        db,
        project,
        customer,
        user,
        by_name["Chiller Room B Door"],
        issue_type="device_replacement",
        priority="medium",
        title="Door sensor replacement - Chiller Room B",
        description="Sample supplier-warranty replacement coordinated from reserve stock.",
        status="in_progress",
        affected_device="Chiller Room B Door",
        warranty_related=True,
        amc_covered=False,
        is_paid_service=False,
        coverage_type="managed_warranty",
        estimated_cost=0.0,
    )
    await ensure_ticket(
        db,
        project,
        customer,
        user,
        None,
        issue_type="on_site_request",
        priority="low",
        title="Requested extra on-site network inspection",
        description="Sample paid on-site request outside hardware fault and AMC coverage.",
        status="open",
        affected_device="Third-party site network",
        warranty_related=False,
        amc_covered=False,
        is_paid_service=True,
        coverage_type="paid_service",
        estimated_cost=180.0,
    )


async def update_lead(db, project):
    if not project.lead_id:
        return
    lead = await one(db, Lead, Lead.id == project.lead_id)
    if lead:
        apply_values(
            lead,
            {
                "recurring_revenue_score": 92,
                "estimated_arr": 5820.0,
                "estimated_ltv": 25360.0,
                "monitoring_points_count": 24,
                "compliance_risk_level": "high",
                "consumable_potential": "medium",
                "amc_potential": "high",
            },
        )


async def print_summary(db):
    model_counts = [
        ("products", Product),
        ("supplier warranties", SupplierWarranty),
        ("customer warranties", CustomerWarranty),
        ("AMC contracts", AMCContract),
        ("monitoring points", MonitoringPoint),
        ("inventory items", InventoryItem),
        ("stock movements", StockMovement),
        ("maintenance tasks", MaintenanceSchedule),
        ("calibration records", CalibrationRecord),
        ("project finances", ProjectFinance),
        ("platform fee rules", PlatformFeeRule),
        ("tickets", Ticket),
    ]
    print("Lifecycle demo ensured:")
    for label, model in model_counts:
        count = await db.scalar(select(func.count()).select_from(model))
        print(f"  {label}: {count}")


async def main():
    await ensure_demo_buyer()
    async with async_session_factory() as db:
        user = await one(db, User, User.email == DEMO_EMAIL)
        if not user or not user.company_id:
            raise RuntimeError("Demo buyer company was not created")
        customer = await one(db, Company, Company.id == user.company_id)
        project = await one(
            db,
            Project,
            Project.buyer_company_id == user.company_id,
            Project.title == STORAGEGUARD_PROJECT_TITLE,
        )
        if not customer or not project:
            raise RuntimeError("StorageGuard demo project was not created")

        supplier = await ensure_company(db)
        category = await ensure_category(db)
        products = await ensure_products(db, supplier, category)
        await ensure_supplier_warranties(db, supplier, products)
        await ensure_customer_warranty(db, project, customer)
        await ensure_amc(db, project, customer)
        points = await ensure_monitoring_points(db, project, products)
        await ensure_inventory(db, supplier, project, user, products)
        await ensure_maintenance(db, project, points)
        await ensure_calibrations(db, project, points)
        await ensure_finance(db, project, customer)
        await ensure_platform_fee_rule(db)
        await ensure_tickets(db, project, customer, user, points)
        await update_lead(db, project)
        await db.commit()
        await print_summary(db)


if __name__ == "__main__":
    asyncio.run(main())
