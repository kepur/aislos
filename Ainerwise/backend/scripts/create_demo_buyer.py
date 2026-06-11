"""Create demo buyer account and smart building demo leads.

Run from backend container or backend directory:
    python -m scripts.create_demo_buyer
"""
import asyncio
import sys

sys.path.insert(0, "/app")

from sqlalchemy import select

from app.core.security import hash_password
from app.db.session import async_session_factory
from app.models.lead import Lead
from app.models.project import Project
from app.models.user import Company, User


DEMO_EMAIL = "demo@ainerwise.com"
DEMO_PASSWORD = "demo123"


# --- FI.1.7 StorageGuard demo buyer project --------------------------------
# A live, monitored StorageGuard project the demo buyer can open to see the
# full sellable lifecycle story: points, compliance risk, initial cost, ARR,
# AMC plan, calibration due date, alert flow, and a sample report preview.
STORAGEGUARD_PROJECT_TITLE = "Food Cold Storage Compliance — Belgrade DC"

STORAGEGUARD_DEMO_PLAN = {
    "solution_line": "storageguard",
    "sample": True,
    "disclaimer": (
        "Sample StorageGuard demo project for sales walkthrough. Figures are "
        "estimate-only until a site survey and signed contract. Hardware follows "
        "supplier warranty; on-site visits are quoted separately."
    ),
    "scenario": "Food distribution centre: 3 chilled rooms + 1 freezer monitored for HACCP compliance.",
    "monitoring_points": {
        "total": 24,
        "temperature_humidity": 18,
        "door_events": 4,
        "outage_alert": 2,
    },
    "compliance": {
        "grade": "food_haccp",
        "risk_level": "high",
        "risk_note": "Chilled stock at risk on any >30 min excursion; inspectors require an audit trail.",
    },
    "economics": {
        "currency": "EUR",
        "initial_cost_min": 6800,
        "initial_cost_max": 12400,
        "arr_min": 2900,
        "arr_max": 6600,
        "amc_plan": "Compliance AMC",
        "recommended_contract_years": 3,
    },
    "calibration": {
        "cycle_months": 12,
        "last_calibrated": "2026-01-15",
        "next_due": "2027-01-15",
    },
    "alert_flow": [
        "Sensor detects out-of-range, door-ajar, or power outage",
        "Edge gateway buffers locally and sends to the platform",
        "Telegram + email alert to the site manager",
        "Phone-call escalation if unacknowledged within 15 minutes",
        "Event logged for the monthly compliance report",
    ],
    "report_preview": {
        "title": "Monthly Compliance Summary",
        "period": "May 2026",
        "sample": True,
        "rooms": [
            {"name": "Chiller Room A", "target": "2–8°C", "compliance_pct": 99.8, "excursions": 1, "max_excursion_min": 22},
            {"name": "Chiller Room B", "target": "2–8°C", "compliance_pct": 100.0, "excursions": 0, "max_excursion_min": 0},
            {"name": "Freezer 1", "target": "-18°C", "compliance_pct": 99.5, "excursions": 2, "max_excursion_min": 41},
        ],
        "door_events": 156,
        "outage_events": 1,
        "alerts_sent": 4,
        "calibration_status": "Valid until 2027-01-15",
    },
}


DEMO_LEADS = [
    {
        "project_type": "Future Smart Villa",
        "country": "Serbia",
        "city": "Belgrade",
        "budget_range": "15k_50k",
        "systems_needed_json": ["KNX", "Home Assistant", "CCTV", "Energy Monitoring", "EV Charging", "Offline AI"],
        "description": "Demo villa project with identity-aware access, room scenes, solar visibility, EV charging, and local AI upgrade path.",
        "site_info_json": {
            "area": "320",
            "rooms": "Living, kitchen, 4 bedrooms, 3 bathrooms, garage, garden",
            "floors": "2",
            "existing_systems": "Fiber internet, basic CCTV, no KNX yet",
        },
        "ai_analysis_json": {
            "disclaimer": "AI estimate only. Final quote requires manual review, customer meeting, site survey, supplier confirmation, and signed contract.",
            "classification": {"project_class": "Smart Villa / Future Home", "estimated_complexity": "medium-high"},
            "completeness": {"score": 82, "missing_fields": ["drawings", "electrical_panel_photos"]},
            "recommended_status": "matched",
            "recommended_next_action": "Review Standard and Premium AI paths, then request Phase-1 Proposal.",
            "lead_score": 78,
        },
    },
    {
        "project_type": "AI School Campus",
        "country": "Serbia",
        "city": "Novi Sad",
        "budget_range": "50k_100k",
        "systems_needed_json": ["CCTV", "Access Control", "HVAC", "Energy Monitoring", "Network"],
        "description": "Demo campus with classroom CO2, security zones, network monitoring, and solar reporting.",
        "site_info_json": {
            "area": "5200",
            "rooms": "32 classrooms, lab rooms, library, admin, gym",
            "floors": "3",
            "existing_systems": "Analog CCTV, separate HVAC controls, no central dashboard",
        },
        "ai_analysis_json": {
            "disclaimer": "AI estimate only. Final quote requires manual review, customer meeting, site survey, supplier confirmation, and signed contract.",
            "classification": {"project_class": "School Campus", "estimated_complexity": "high"},
            "completeness": {"score": 76, "missing_fields": ["network_topology", "camera_layout"]},
            "recommended_status": "matched",
            "recommended_next_action": "Schedule facility interview and Phase-1 Proposal for campus architecture.",
            "lead_score": 85,
        },
    },
    {
        "project_type": "Smart Apartment Building",
        "country": "Serbia",
        "city": "Belgrade",
        "budget_range": "15k_50k",
        "systems_needed_json": ["Access Control", "CCTV", "Energy Monitoring", "Maintenance"],
        "description": "Demo property project for common area lighting, visitor access, parking, meters, and monthly maintenance reports.",
        "site_info_json": {
            "area": "2800",
            "rooms": "24 units plus lobby, corridors, garage",
            "floors": "6",
            "existing_systems": "Door intercom, limited CCTV, shared utility meters",
        },
    },
    {
        "project_type": "Enterprise Office AI Brain",
        "country": "Poland",
        "city": "Warsaw",
        "budget_range": "50k_100k",
        "systems_needed_json": ["HVAC", "Lighting", "Access Control", "Network", "Offline AI"],
        "description": "Demo office project with meeting room scenes, visitor management, IT room monitoring, and daily facility AI summary.",
        "site_info_json": {
            "area": "4100",
            "rooms": "Open office, 12 meeting rooms, IT room, reception",
            "floors": "4",
            "existing_systems": "IP access control, enterprise Wi-Fi, no BMS integration",
        },
    },
    {
        "project_type": "Solar + Storage Energy Site",
        "country": "Serbia",
        "city": "Subotica",
        "budget_range": "15k_50k",
        "systems_needed_json": ["Solar", "Energy Monitoring", "Battery", "EV Charging"],
        "description": "Demo energy site with inverter monitoring, battery SOC, EV charging, load priority, and monthly AI energy report.",
        "site_info_json": {
            "area": "Commercial roof 900 sqm",
            "rooms": "Main load panel, office, warehouse",
            "floors": "1",
            "existing_systems": "Solar inverter installed, no battery yet",
        },
    },
    {
        "project_type": "Smart Hotel Room Control",
        "country": "Serbia",
        "city": "Kopaonik",
        "budget_range": "50k_100k",
        "systems_needed_json": ["KNX", "HVAC", "Lighting", "Access Control", "Remote Maintenance"],
        "description": "Demo hotel project with guest room welcome mode, away energy saving, housekeeping access, and room device health.",
        "site_info_json": {
            "area": "48 rooms",
            "rooms": "Guest rooms, lobby, corridors, service rooms",
            "floors": "5",
            "existing_systems": "Card locks, standalone thermostats, basic CCTV",
        },
    },
]


async def ensure_storageguard_project(db, user):
    """Idempotently ensure the StorageGuard demo lead + project exist."""
    from app.models.lifecycle import AMCContract

    existing = await db.execute(
        select(Project).where(
            Project.buyer_company_id == user.company_id,
            Project.title == STORAGEGUARD_PROJECT_TITLE,
        )
    )
    existing_project = existing.scalar_one_or_none()
    if existing_project:
        # Backfill lifecycle records for an already-seeded demo project.
        has_amc = await db.execute(
            select(AMCContract).where(AMCContract.project_id == existing_project.id).limit(1)
        )
        if has_amc.scalar_one_or_none():
            return False
        await _seed_storageguard_lifecycle(db, project=existing_project, company_id=user.company_id)
        return True

    lead = Lead(
        buyer_company_id=user.company_id,
        buyer_user_id=user.id,
        contact_name="Demo Customer",
        contact_email=DEMO_EMAIL,
        contact_phone="+381 demo",
        language="en",
        status="converted",
        project_type="Cold Chain / Storage (StorageGuard)",
        country="Serbia",
        city="Belgrade",
        budget_range="6k_18k",
        systems_needed_json=[
            "StorageGuard", "Temperature & Humidity Monitoring", "Door Sensors",
            "Outage Alerts", "Compliance Reports", "Calibration", "Alarm Monitoring",
        ],
        description="Demo StorageGuard cold-chain compliance project for a food distribution centre.",
        solution_line="storageguard",
        monitoring_points_count=24,
        compliance_risk_level="high",
        amc_potential="high",
        consumable_potential="medium",
        estimated_arr=4750,
        site_info_json={
            "category_key": "storage",
            "storage_type": "3 chilled rooms + 1 freezer",
            "temperature_humidity": "2-8°C chilled, -18°C frozen",
            "compliance_use": "Food HACCP, monthly audit reports",
            "monitoring_points": "24",
            "alert_channels": "Telegram, email, phone escalation",
            "calibration_cycle": "annual, 3-year service term",
        },
    )
    db.add(lead)
    await db.flush()

    project = Project(
        lead_id=lead.id,
        buyer_company_id=user.company_id,
        title=STORAGEGUARD_PROJECT_TITLE,
        status="maintenance",
        region="Serbia",
        project_plan_json=STORAGEGUARD_DEMO_PLAN,
        team_json=[
            {"name": "AinerWise Support", "role": "Remote compliance monitoring"},
            {"name": "Local Partner", "role": "On-site calibration (quoted separately)"},
        ],
        notes="Sample StorageGuard lifecycle project for demo walkthrough.",
    )
    db.add(project)
    await db.flush()

    await _seed_storageguard_lifecycle(db, project=project, company_id=user.company_id)
    return True


async def _seed_storageguard_lifecycle(db, *, project, company_id):
    """Seed AMC, warranty, monitoring points, calibration, and maintenance so the
    buyer portal lifecycle workspace (FI.5) shows real data for the demo."""
    from datetime import date

    from app.models.lifecycle import (
        AMCContract,
        CalibrationRecord,
        CustomerWarranty,
        MaintenanceSchedule,
        MonitoringPoint,
    )

    db.add(AMCContract(
        project_id=project.id,
        customer_id=company_id,
        package="compliance",
        pricing_mode="point_based",
        start_date=date(2026, 1, 15),
        end_date=date(2027, 1, 14),
        renewal_status="active",
        coverage_json={
            "includes": ["Compliance reports", "Annual calibration", "Probe checks", "Alarm watch"],
            "excludes": ["Unscheduled on-site emergency"],
        },
        exclusions_json=["Physical damage", "Water ingress", "Lightning"],
        included_visits_per_year=2,
        response_target_hours=24,
        recurring_fee=3000,
        currency="EUR",
        notes="Compliance AMC for cold-chain monitoring (demo).",
    ))

    db.add(CustomerWarranty(
        project_id=project.id,
        customer_id=company_id,
        warranty_model="managed",
        start_date=date(2026, 1, 15),
        end_date=date(2028, 1, 14),
        included_devices_json=["Monitoring gateway", "Temperature/humidity probes", "Door sensors"],
        excluded_devices_json=["Customer-supplied router"],
        included_labor=True,
        included_remote_support=True,
        included_on_site_visits_per_year=1,
        spare_parts_included=False,
        max_claims_per_year=4,
        notes="AinerWise Managed Warranty: single support window; hardware follows supplier warranty.",
    ))

    points = [
        ("Chiller Room A", "Probe A1", "temperature", "°C", 2, 8),
        ("Chiller Room A", "Door A", "door", "", None, None),
        ("Chiller Room B", "Probe B1", "temperature", "°C", 2, 8),
        ("Freezer 1", "Probe F1", "temperature", "°C", -25, -18),
    ]
    mp_objs = []
    for site, device, ptype, unit, tmin, tmax in points:
        mp = MonitoringPoint(
            project_id=project.id, solution_line="storageguard", site=site,
            device_name=device, point_type=ptype, unit=unit,
            threshold_min=tmin, threshold_max=tmax,
            calibration_cycle_months=12,
            last_calibrated_at=date(2026, 1, 15), next_calibration_at=date(2027, 1, 15),
            status="active",
        )
        mp_objs.append(mp)
        db.add(mp)
    await db.flush()

    db.add(CalibrationRecord(
        project_id=project.id, monitoring_point_id=mp_objs[0].id,
        calibration_date=date(2026, 1, 15), next_due_date=date(2027, 1, 15),
        calibration_method="Reference probe comparison", technician="AinerWise Field Eng.",
        result="pass", notes="Annual calibration certificate (demo).",
    ))

    db.add(MaintenanceSchedule(
        project_id=project.id, monitoring_point_id=mp_objs[0].id,
        device_name="Probe A1", task_type="calibration",
        due_date=date(2027, 1, 15), frequency_months=12,
        status="scheduled", covered_by_amc=True,
        notes="Next annual calibration (covered by Compliance AMC).",
    ))


# FI.7.1 / FI.7.2 — lightweight KitchenGuard + AquaGuard demo projects.
EXTRA_DEMO_PROJECTS = [
    {
        "title": "Hotel Kitchen Safety — Belgrade",
        "solution_line": "kitchenguard",
        "plan": {
            "solution_line": "kitchenguard", "sample": True,
            "scenario": "Hotel with 2 kitchens monitored for gas, CO and water-leak safety.",
            "monitoring_points": {"total": 10, "gas_co": 6, "water_leak": 3, "cutoff": 1},
            "economics": {"currency": "EUR", "initial_cost_min": 4200, "initial_cost_max": 9000, "arr_min": 1800, "arr_max": 4200, "amc_plan": "Compliance AMC", "recommended_contract_years": 3},
            "disclaimer": "Sample KitchenGuard demo project. Estimate-only until site survey and contract.",
        },
    },
    {
        "title": "Factory Effluent Compliance — Novi Sad",
        "solution_line": "aquaguard",
        "plan": {
            "solution_line": "aquaguard", "sample": True,
            "scenario": "Factory effluent: 2 outfalls monitored for pH, COD and turbidity compliance.",
            "monitoring_points": {"total": 6, "ph_ec": 2, "cod_turbidity": 4},
            "economics": {"currency": "EUR", "initial_cost_min": 9000, "initial_cost_max": 22000, "arr_min": 3600, "arr_max": 9000, "amc_plan": "Compliance AMC", "recommended_contract_years": 3},
            "disclaimer": "Sample AquaGuard demo project (partner-led). Estimate-only until site survey and contract.",
        },
    },
]


async def ensure_extra_demo_projects(db, user) -> int:
    created = 0
    for spec in EXTRA_DEMO_PROJECTS:
        existing = await db.execute(
            select(Project).where(
                Project.buyer_company_id == user.company_id,
                Project.title == spec["title"],
            )
        )
        if existing.scalar_one_or_none():
            continue
        db.add(Project(
            buyer_company_id=user.company_id,
            title=spec["title"],
            status="maintenance",
            region="Serbia",
            project_plan_json=spec["plan"],
            notes=f"Sample {spec['solution_line']} demo project for portal walkthrough.",
        ))
        created += 1
    return created


async def main():
    async with async_session_factory() as db:
        user_result = await db.execute(select(User).where(User.email == DEMO_EMAIL))
        user = user_result.scalar_one_or_none()

        if user is None:
            company = Company(
                name="AinerWise Demo Customer",
                type="buyer",
                country="Serbia",
                city="Belgrade",
                verification_status="verified",
                contact_info={"email": DEMO_EMAIL},
            )
            db.add(company)
            await db.flush()

            user = User(
                email=DEMO_EMAIL,
                password_hash=hash_password(DEMO_PASSWORD),
                full_name="Demo Customer",
                role="buyer",
                language="en",
                country="Serbia",
                company_id=company.id,
                is_active=True,
            )
            db.add(user)
            await db.flush()

        # Ensure the StorageGuard demo project exists regardless of whether the
        # earlier smart-building demo leads were already seeded.
        storageguard_added = await ensure_storageguard_project(db, user)
        await ensure_extra_demo_projects(db, user)

        existing_leads = await db.execute(
            select(Lead).where(
                Lead.buyer_user_id == user.id,
                Lead.solution_line.is_(None),
            )
        )
        if existing_leads.scalars().first():
            await db.commit()
            note = " (+ StorageGuard demo project)" if storageguard_added else ""
            print(f"Demo buyer already exists: {DEMO_EMAIL} / {DEMO_PASSWORD}{note}")
            return

        for item in DEMO_LEADS:
            db.add(
                Lead(
                    buyer_company_id=user.company_id,
                    buyer_user_id=user.id,
                    contact_name="Demo Customer",
                    contact_email=DEMO_EMAIL,
                    contact_phone="+381 demo",
                    language="en",
                    status="matched",
                    **item,
                )
            )

        await db.commit()
        print(f"Demo buyer created: {DEMO_EMAIL} / {DEMO_PASSWORD}")


if __name__ == "__main__":
    asyncio.run(main())
