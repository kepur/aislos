"""Seed initial data. Run: python -m scripts.seed_data"""
import asyncio
import sys
sys.path.insert(0, "/app")

from sqlalchemy import select
from app.db.session import async_session_factory
from app.models.product import Product, ProductCategory
from app.models.solution import Solution
from app.models.service import ServicePackage
from app.models.region import Region


CATEGORIES = [
    ("KNX Devices", "knx-devices", "mdi-chip", 1),
    ("Gateways", "gateways", "mdi-router", 2),
    ("Sensors", "sensors", "mdi-thermometer", 3),
    ("Smart Panels", "smart-panels", "mdi-tablet-dashboard", 4),
    ("CCTV", "cctv", "mdi-cctv", 5),
    ("Access Control", "access-control", "mdi-door-closed-lock", 6),
    ("Network Devices", "network-devices", "mdi-lan", 7),
    ("HVAC Controllers", "hvac-controllers", "mdi-air-conditioner", 8),
    ("Energy Meters", "energy-meters", "mdi-meter-electric", 9),
    ("Solar Monitoring", "solar-monitoring", "mdi-solar-panel", 10),
    ("Lighting Control", "lighting-control", "mdi-lightbulb-on", 11),
    ("Home Assistant Compatible", "home-assistant-compatible", "mdi-home-assistant", 12),
    ("Service Packages", "service-packages-cat", "mdi-wrench", 13),
    ("Industrial Automation", "industrial-automation", "mdi-factory", 14),
    ("PLC / SCADA Gateways", "plc-scada-gateways", "mdi-lan-connect", 15),
    ("Machine Energy Monitoring", "machine-energy-monitoring", "mdi-chart-line", 16),
]

PROJECT_PRICE_NOTE = (
    "Device price is only a reference. Final project pricing includes design, "
    "installation, commissioning, spare parts reserve, support period, site survey, "
    "supplier confirmation, and signed contract."
)

PRODUCTS = [
    {
        "name": "Solar / Battery / EV Energy Gateway",
        "slug": "solar-energy-gateway",
        "category_slug": "solar-monitoring",
        "brand": "Huawei Digital Power / Sungrow class",
        "description": "Gateway layer for inverter, battery, EV charger, meter, tariff, and building load visualization.",
        "source_type": "official",
        "list_price": 690,
        "currency": "EUR",
        "moq": 1,
        "lead_time_days": 21,
        "warranty_years": 3,
        "service_available": True,
        "service_term_years_json": [5, 8, 10],
        "project_pricing_mode": "device_reference_plus_project_service",
        "service_pricing_note": PROJECT_PRICE_NOTE,
        "supply_tier": "China first-tier energy ecosystem: Huawei Digital Power, Sungrow, LONGi class",
        "supplier_ecosystem_json": ["Huawei Digital Power", "Sungrow", "LONGi", "BYD / CATL class"],
        "price_options_json": [
            {"label": "Device reference", "value": "EUR 690", "note": "Reference hardware price, not final project quote"},
            {"label": "Project supply + commissioning", "value": "Request project quote", "note": "Depends on quantity, site, installation, and support term"},
        ],
        "lifecycle_pricing_json": [
            {"years": 5, "label": "5-year energy monitoring", "annual_fee": 520, "note": "Inverter, meter, EV and alert review"},
            {"years": 8, "label": "8-year commercial energy support", "annual_fee": 780, "note": "Annual optimization and spare gateway planning"},
            {"years": 10, "label": "10-year energy lifecycle", "annual_fee": 1150, "note": "Custom enterprise support and upgrade roadmap"},
        ],
        "protocol_json": ["Modbus TCP", "Modbus RTU", "MQTT"],
        "scenario_tags_json": ["energy", "factory", "villa", "office", "ev"],
        "intelligence_level_min": 3,
        "intelligence_level_max": 5,
        "feature_status": "project_dependent",
        "risk_level": "medium",
        "status": "active",
    },
    {
        "name": "PoE AI CCTV Camera",
        "slug": "ai-cctv-poe-camera",
        "category_slug": "cctv",
        "brand": "Hikvision / Dahua class supplier",
        "description": "Service-ready IP camera with ONVIF/RTSP support for smart security, video AI projects, and local NVR integration.",
        "source_type": "supplier",
        "list_price": 165,
        "currency": "EUR",
        "moq": 4,
        "lead_time_days": 18,
        "warranty_years": 2,
        "service_available": True,
        "service_term_years_json": [5, 8],
        "project_pricing_mode": "device_reference_plus_project_service",
        "service_pricing_note": PROJECT_PRICE_NOTE,
        "supply_tier": "China first-tier CCTV ecosystem, not low-cost generic hardware",
        "supplier_ecosystem_json": ["Hikvision / Dahua class", "China Tier-1 OEM/ODM"],
        "price_options_json": [
            {"label": "Device reference", "value": "EUR 165", "note": "Reference hardware price, not final project quote"},
            {"label": "Project supply + commissioning", "value": "Request project quote", "note": "Depends on camera count, network, NVR, and support term"},
        ],
        "lifecycle_pricing_json": [
            {"years": 5, "label": "5-year CCTV maintenance", "annual_fee": 220, "note": "Camera health, NVR checks, firmware planning"},
            {"years": 8, "label": "8-year security lifecycle", "annual_fee": 340, "note": "Spare unit reserve and long-term replacement plan"},
        ],
        "protocol_json": ["ONVIF", "RTSP", "PoE"],
        "scenario_tags_json": ["hotel", "school", "factory", "apartment", "cctv"],
        "intelligence_level_min": 2,
        "intelligence_level_max": 5,
        "feature_status": "available_now",
        "risk_level": "low",
        "status": "active",
    },
    {
        "name": "Industrial PLC / Modbus / OPC UA Gateway",
        "slug": "industrial-plc-gateway",
        "category_slug": "plc-scada-gateways",
        "brand": "Verified Industrial Supplier",
        "description": "Factory data gateway for machine status, power usage, alarms, compressed air, and maintenance workflows.",
        "source_type": "supplier",
        "list_price": 880,
        "currency": "EUR",
        "moq": 1,
        "lead_time_days": 28,
        "warranty_years": 2,
        "service_available": True,
        "service_term_years_json": [5, 8, 10],
        "project_pricing_mode": "device_reference_plus_project_service",
        "service_pricing_note": PROJECT_PRICE_NOTE,
        "supply_tier": "China first-tier industrial gateway / automation ecosystem",
        "supplier_ecosystem_json": ["China Tier-1 OEM/ODM", "Industrial gateway suppliers", "Edge AI partners"],
        "price_options_json": [
            {"label": "Device reference", "value": "EUR 880", "note": "Reference hardware price, not final plant integration quote"},
            {"label": "Factory pilot line", "value": "Request project quote", "note": "Depends on protocols, machines, OT safety, and support term"},
        ],
        "lifecycle_pricing_json": [
            {"years": 5, "label": "5-year factory gateway support", "annual_fee": 850, "note": "OT gateway health, alarm rules, backup"},
            {"years": 8, "label": "8-year industrial lifecycle", "annual_fee": 1280, "note": "SLA planning, spare gateway, protocol change support"},
            {"years": 10, "label": "10-year factory support", "annual_fee": 1800, "note": "Custom plant-level lifecycle contract"},
        ],
        "protocol_json": ["Modbus", "OPC UA", "MQTT", "Ethernet/IP options"],
        "scenario_tags_json": ["factory", "warehouse", "production-line", "energy"],
        "intelligence_level_min": 3,
        "intelligence_level_max": 5,
        "feature_status": "project_dependent",
        "risk_level": "medium",
        "status": "active",
    },
    {
        "name": "Local AI Building Edge Box",
        "slug": "edge-ai-building-box",
        "category_slug": "network-devices",
        "brand": "AinerWise Official / China edge compute supply chain",
        "description": "Edge compute box for local AI workflows, building data collection, dashboards, automation logic, and privacy-sensitive deployments.",
        "source_type": "official",
        "currency": "EUR",
        "moq": 1,
        "lead_time_days": 30,
        "warranty_years": 3,
        "service_available": True,
        "service_term_years_json": [5, 8, 10],
        "project_pricing_mode": "project_based_quote",
        "service_pricing_note": PROJECT_PRICE_NOTE,
        "supply_tier": "AinerWise local AI / China first-tier edge compute supply chain",
        "supplier_ecosystem_json": ["Huawei class edge infrastructure", "Xiaomi ecosystem", "China Tier-1 OEM/ODM"],
        "price_options_json": [
            {"label": "Project-based estimate", "value": "Request quote", "note": "Local AI hardware and workflow design require engineering review"},
        ],
        "lifecycle_pricing_json": [
            {"years": 5, "label": "5-year AI operations support", "annual_fee": 680, "note": "Model workflow updates, backup, monitoring"},
            {"years": 8, "label": "8-year AI lifecycle", "annual_fee": 980, "note": "Hardware refresh planning and priority engineering review"},
            {"years": 10, "label": "10-year enterprise support", "annual_fee": 1450, "note": "Custom long-term AI operations contract"},
        ],
        "protocol_json": ["MQTT", "REST", "Modbus TCP", "ONVIF"],
        "scenario_tags_json": ["villa", "office", "school", "factory", "local-ai"],
        "intelligence_level_min": 4,
        "intelligence_level_max": 5,
        "feature_status": "advanced_custom",
        "risk_level": "medium",
        "status": "active",
    },
    # IND.8 — industrial capability products with protocol/machine tags.
    {
        "name": "Non-Invasive Machine Energy Meter",
        "slug": "machine-energy-meter",
        "category_slug": "machine-energy-monitoring",
        "brand": "Verified Industrial Supplier",
        "description": "Split-core CT machine energy meter for non-invasive current, power, and run/stop monitoring per machine.",
        "source_type": "supplier",
        "list_price": 240,
        "currency": "EUR",
        "moq": 4,
        "lead_time_days": 21,
        "warranty_years": 2,
        "service_available": True,
        "service_term_years_json": [5, 8],
        "project_pricing_mode": "device_reference_plus_project_service",
        "service_pricing_note": PROJECT_PRICE_NOTE,
        "supply_tier": "China first-tier industrial metering ecosystem",
        "protocol_json": ["Modbus RTU", "Modbus TCP", "MQTT"],
        "scenario_tags_json": ["factory", "machine-meter", "production-line", "energy"],
        "solution_line": "factorypulse",
        "recurring_revenue_types_json": ["saas", "report_export", "algorithm_subscription"],
        "expected_lifetime_months": 96,
        "amc_recommended": True,
        "service_dependency_level": "medium",
        "intelligence_level_min": 3,
        "intelligence_level_max": 5,
        "feature_status": "project_dependent",
        "risk_level": "medium",
        "status": "active",
    },
    {
        "name": "VFD / Motor & Compressor Monitoring Module",
        "slug": "vfd-motor-monitor",
        "category_slug": "machine-energy-monitoring",
        "brand": "Verified Industrial Supplier",
        "description": "Monitoring module for VFDs, motors, compressors, and chillers: energy, vibration, temperature, and run hours for predictive maintenance.",
        "source_type": "supplier",
        "list_price": 420,
        "currency": "EUR",
        "moq": 2,
        "lead_time_days": 28,
        "warranty_years": 2,
        "service_available": True,
        "service_term_years_json": [5, 8],
        "project_pricing_mode": "device_reference_plus_project_service",
        "service_pricing_note": PROJECT_PRICE_NOTE,
        "supply_tier": "China first-tier industrial automation ecosystem",
        "protocol_json": ["Modbus", "OPC UA", "MQTT"],
        "scenario_tags_json": ["factory", "vfd", "motor", "compressor", "chiller", "predictive-maintenance"],
        "solution_line": "factorypulse",
        "recurring_revenue_types_json": ["algorithm_subscription", "annual_inspection", "report_export"],
        "calibration_cycle_months": 24,
        "expected_lifetime_months": 84,
        "amc_recommended": True,
        "service_dependency_level": "high",
        "intelligence_level_min": 3,
        "intelligence_level_max": 5,
        "feature_status": "project_dependent",
        "risk_level": "high",
        "status": "active",
    },
    {
        "name": "PLC / SCADA & Robot OPC-UA Connector",
        "slug": "plc-scada-robot-opcua-connector",
        "category_slug": "plc-scada-gateways",
        "brand": "Verified Industrial Supplier",
        "description": "OT connector bridging PLC, SCADA, MES, and robot controllers over OPC-UA / Modbus / Ethernet/IP into the AinerWise platform with OT/IT isolation.",
        "source_type": "supplier",
        "list_price": 980,
        "currency": "EUR",
        "moq": 1,
        "lead_time_days": 30,
        "warranty_years": 2,
        "service_available": True,
        "service_term_years_json": [5, 8, 10],
        "project_pricing_mode": "project_based_quote",
        "service_pricing_note": PROJECT_PRICE_NOTE,
        "supply_tier": "China first-tier industrial gateway / OT ecosystem",
        "protocol_json": ["OPC UA", "Modbus", "Ethernet/IP", "PROFINET options", "MQTT"],
        "scenario_tags_json": ["factory", "plc", "scada", "mes", "robot", "ot-network"],
        "solution_line": "factorypulse",
        "recurring_revenue_types_json": ["saas", "algorithm_subscription", "annual_inspection"],
        "expected_lifetime_months": 96,
        "amc_required": True,
        "amc_recommended": True,
        "service_dependency_level": "high",
        "intelligence_level_min": 3,
        "intelligence_level_max": 5,
        "feature_status": "advanced_custom",
        "risk_level": "high",
        "status": "active",
    },
]

SOLUTIONS = [
    {
        "title": "Smart Hotel Room Control",
        "slug": "smart-hotel",
        "category": "hospitality",
        "icon": "mdi-bed",
        "description": "Complete smart hotel room automation including guest detection, lighting scenes, HVAC control, and energy optimization. Designed for hotels seeking to reduce energy costs while improving guest experience.",
        "target_scenarios_json": ["Hotels", "Boutique Hotels", "Serviced Apartments", "Resorts"],
        "pain_points_json": ["High energy bills", "Poor guest experience", "Manual room management", "No centralized control"],
        "budget_tiers_json": {
            "budget": {"label": "Budget", "description": "Basic smart switches + sensors", "starting_from": 500},
            "standard": {"label": "Standard", "description": "KNX lighting + HVAC + guest detection", "starting_from": 2000},
            "premium": {"label": "Premium", "description": "Full KNX + BMS integration + energy dashboard", "starting_from": 5000},
        },
        "delivery_flow_json": ["Site Assessment", "Design", "Procurement", "Installation", "Commissioning", "Training", "Handover"],
    },
    {
        "title": "Smart Villa & Apartment Retrofit",
        "slug": "smart-villa",
        "category": "residential",
        "icon": "mdi-home-modern",
        "description": "Transform existing villas and apartments with smart lighting, climate control, security, and energy monitoring. Non-invasive retrofit solutions that work with existing wiring.",
        "target_scenarios_json": ["Villas", "Apartments", "Residential Complexes", "Vacation Homes"],
        "pain_points_json": ["Outdated wiring", "No automation", "Energy waste", "Security concerns"],
        "budget_tiers_json": {
            "budget": {"label": "Budget", "description": "WiFi switches + Home Assistant", "starting_from": 300},
            "standard": {"label": "Standard", "description": "Zigbee/Z-Wave mesh + scenes + energy monitor", "starting_from": 1500},
            "premium": {"label": "Premium", "description": "KNX retrofit + full automation", "starting_from": 4000},
        },
        "delivery_flow_json": ["Consultation", "Site Survey", "Design", "Procurement", "Installation", "Setup", "Training"],
    },
    {
        "title": "CCTV & Access Control",
        "slug": "cctv-access-control",
        "category": "security",
        "icon": "mdi-cctv",
        "description": "Professional surveillance and access control systems for commercial and residential properties. IP cameras, NVR, door access, intercom, and remote monitoring solutions.",
        "target_scenarios_json": ["Commercial Buildings", "Shops", "Offices", "Residential", "Parking"],
        "pain_points_json": ["No surveillance", "Outdated analog system", "No remote access", "Poor coverage"],
        "budget_tiers_json": {
            "budget": {"label": "Budget", "description": "4-8 cameras + NVR + basic access", "starting_from": 800},
            "standard": {"label": "Standard", "description": "8-16 cameras + smart NVR + card access", "starting_from": 2500},
            "premium": {"label": "Premium", "description": "AI cameras + biometric access + integration", "starting_from": 6000},
        },
        "delivery_flow_json": ["Site Assessment", "Design", "Procurement", "Installation", "Configuration", "Testing", "Handover"],
    },
    {
        "title": "KNX Lighting & Scene Automation",
        "slug": "knx-lighting",
        "category": "automation",
        "icon": "mdi-lightbulb-group",
        "description": "Professional KNX-based lighting control with scene management, daylight harvesting, presence detection, and integration with building management systems.",
        "target_scenarios_json": ["New Construction", "Renovation", "Commercial Spaces", "High-End Residential"],
        "pain_points_json": ["Manual light switches", "No scene control", "Energy waste from lights", "Complex wiring"],
        "budget_tiers_json": {
            "budget": {"label": "Budget", "description": "Basic KNX dimmers + switches per room", "starting_from": 1000},
            "standard": {"label": "Standard", "description": "Full scenes + presence + daylight", "starting_from": 3000},
            "premium": {"label": "Premium", "description": "BMS integration + visualization + scheduling", "starting_from": 7000},
        },
        "delivery_flow_json": ["Consultation", "KNX Design", "Procurement", "Wiring", "Programming", "Commissioning", "Training"],
    },
    {
        "title": "Solar & Energy Monitoring",
        "slug": "solar-energy-monitoring",
        "category": "energy",
        "icon": "mdi-solar-power",
        "description": "Real-time solar production monitoring, energy consumption tracking, and performance optimization dashboards. Compatible with major inverter brands.",
        "target_scenarios_json": ["Solar Installations", "Commercial Buildings", "Industrial", "Residential with PV"],
        "pain_points_json": ["No visibility into solar production", "Unknown energy waste", "No fault alerts", "No ROI tracking"],
        "budget_tiers_json": {
            "budget": {"label": "Budget", "description": "Inverter monitoring + basic dashboard", "starting_from": 300},
            "standard": {"label": "Standard", "description": "Multi-meter + consumption + production comparison", "starting_from": 1200},
            "premium": {"label": "Premium", "description": "Full BMS + battery + grid + AI optimization", "starting_from": 3500},
        },
        "delivery_flow_json": ["Assessment", "Design", "Hardware Install", "Software Setup", "Dashboard Config", "Training"],
    },
    {
        "title": "Factory Automation & Industrial Energy Brain",
        "slug": "factory-industrial-energy-brain",
        "category": "industrial",
        "icon": "mdi-factory",
        "description": "Industrial smart-building layer for factories, warehouses, and manufacturing plants. Connects machine energy monitoring, PLC/SCADA, Modbus, BACnet, MQTT, OPC-UA gateways, compressed air, chillers, motors, VFDs, robots, PV/battery, OT network visibility, safety boundaries, and lifecycle maintenance.",
        "target_scenarios_json": ["Factories", "Warehouses", "Manufacturing Plants", "Industrial Parks", "Food Processing", "Assembly Lines"],
        "pain_points_json": ["Hidden machine energy waste", "Siloed PLC/SCADA data", "No machine-level metering", "Peak demand penalties", "Production downtime", "Weak OT/IT visibility", "No predictive maintenance"],
        "budget_tiers_json": {
            "budget": {"label": "Budget", "description": "Selected machine meters + OT gateway + essential alerts", "starting_from": 30000},
            "standard": {"label": "Standard", "description": "Line-level energy + PLC/SCADA integration + compressor/chiller schedules", "starting_from": 100000},
            "premium": {"label": "Premium AI", "description": "AI anomaly detection + predictive maintenance + production energy intelligence", "starting_from": 300000},
        },
        "delivery_flow_json": ["Industrial Intake", "OT/IT Safety Review", "Site Survey", "Protocol Verification", "Pilot Line", "Dashboard & Alerts", "Lifecycle SLA"],
    },
    {
        "title": "StorageGuard — Cold Chain & Storage Compliance Monitoring",
        "slug": "storageguard",
        "category": "storage",
        "icon": "mdi-thermometer-alert",
        "description": (
            "24/7 temperature and humidity compliance monitoring for cold chain and "
            "precision storage. StorageGuard turns cold rooms, freezers, pharmacy "
            "fridges, and food warehouses into monitorable, auditable, and serviceable "
            "facilities: continuous monitoring, door-event logging, power-outage alerts, "
            "audit-ready reports, annual calibration, sensor battery replacement, and an "
            "annual Compliance Maintenance Contract."
        ),
        "target_scenarios_json": [
            "Pharmaceutical Warehouses", "Food Cold Storage", "Supermarket Cold Chain",
            "Central Kitchens", "Hotel Cold Rooms", "Laboratories", "Vaccine / Medical Storage",
        ],
        "pain_points_json": [
            "Product loss from undetected temperature excursions",
            "No audit trail for inspectors (HACCP / GDP)",
            "Power failures discovered too late",
            "Manual paper logs that are easy to miss or fake",
            "No calibration record or alerting workflow",
        ],
        "budget_tiers_json": {
            "starter": {"label": "Compliance Starter", "description": "Single cold room: gateway + temperature/humidity + door + outage alert.", "starting_from": 1900},
            "standard": {"label": "Multi-Room Compliance", "description": "Several rooms with audit reports, calibration plan, and alert routing.", "starting_from": 6500},
            "enterprise": {"label": "Enterprise / Multi-Site", "description": "Many rooms or sites with SLA, spare pool, and Compliance AMC.", "starting_from": 18000},
        },
        "delivery_flow_json": [
            "Facility Assessment", "Point & Threshold Design", "Install & Commission",
            "Report & Alert Setup", "First-Year Support", "Annual Calibration", "Compliance AMC",
        ],
        "lifecycle_content_json": {
            "headline": "Cold Room Compliance Monitoring Package — sold as a serviceable outcome, not a sensor.",
            "monitoring_points": [
                {"name": "Temperature & Humidity", "detail": "Continuous 24/7 readings per room with high/low thresholds."},
                {"name": "Cold Room Door Events", "detail": "Door open/close logging and door-ajar alerts."},
                {"name": "Power Outage Detection", "detail": "Backup-powered alert so failures are caught immediately."},
                {"name": "Multi-Room / Multi-Site", "detail": "One dashboard across rooms, freezers, and locations."},
            ],
            "alert_channels": ["SMS", "Telegram", "Email", "Phone call escalation", "In-app"],
            "reports": [
                "Monthly compliance summary (sample until customer-specific reporting is configured)",
                "Annual audit-ready report for HACCP / GDP inspections",
                "Calibration certificates per sensor",
            ],
            "calibration_consumables": [
                "Annual sensor calibration with certificate",
                "Sensor battery replacement",
                "Probe replacement on lifecycle schedule",
            ],
            "recurring_charges": [
                "Platform & monitoring fee",
                "Compliance report fee",
                "Annual calibration fee",
                "Consumables (batteries / probes)",
                "Alarm monitoring / watch service",
                "Annual Maintenance Contract (Compliance AMC)",
            ],
            "amc_options": [
                {"name": "Basic", "detail": "Remote alarm watch + annual check."},
                {"name": "Compliance", "detail": "Reports + calibration + probe checks + maintenance record."},
                {"name": "Commercial", "detail": "Multi-room monitoring + priority response + spare pool."},
            ],
            "service_boundary": (
                "AinerWise provides system-level monitoring, support coordination, and "
                "lifecycle service. Hardware follows the original supplier warranty unless a "
                "managed warranty or fast-replacement plan is purchased. On-site visits are "
                "quoted separately."
            ),
        },
    },
    {
        "title": "KitchenGuard — Commercial Kitchen Safety Monitoring",
        "slug": "kitchenguard", "category": "kitchen", "solution_line": "kitchenguard", "icon": "mdi-stove",
        "description": "Gas, CO, water-leak, smoke and temperature safety monitoring for commercial and central kitchens, with automatic gas cut-off, alarm escalation, annual inspection certificates, and AMC.",
        "target_scenarios_json": ["Hotel kitchens", "Restaurant chains", "Central kitchens", "Food courts", "Catering"],
        "pain_points_json": ["Gas / CO / fire risk", "Insurance & inspection requirements", "Water leaks under appliances", "No alarm escalation"],
        "budget_tiers_json": {"starter": {"label": "Single Kitchen", "description": "Gas/CO + leak + alarm setup", "starting_from": 1800}, "standard": {"label": "Multi-Kitchen", "description": "Cut-off valve + annual inspection", "starting_from": 6000}, "enterprise": {"label": "Chain / Multi-Site", "description": "SLA + alarm watch + AMC", "starting_from": 16000}},
        "delivery_flow_json": ["Safety Assessment", "Sensor & Valve Design", "Install & Commission", "Alarm Setup", "Annual Inspection", "AMC"],
        "lifecycle_content_json": {
            "headline": "Commercial Kitchen Safety Package — monitored safety and inspection certificates, not just detectors.",
            "monitoring_points": [{"name": "Combustible Gas & CO", "detail": "Per-zone gas leak and carbon monoxide detection."}, {"name": "Water Leak & Temperature", "detail": "Leak detection and abnormal-temperature alerts."}, {"name": "Gas Cut-off Interlock", "detail": "Automatic gas valve cut-off on alarm where a valve exists."}],
            "alert_channels": ["SMS", "Telegram", "Phone call escalation", "Property / maintenance"],
            "reports": ["Annual safety inspection certificate", "Maintenance records", "Alarm event log"],
            "calibration_consumables": ["Annual gas/CO sensor calibration", "Sensor replacement on lifecycle schedule"],
            "recurring_charges": ["Annual safety inspection", "Alarm watch service", "Sensor calibration", "Annual Maintenance Contract"],
            "amc_options": [{"name": "Basic", "detail": "Remote alarm watch + annual check."}, {"name": "Compliance", "detail": "Inspection certificate + calibration + valve test."}],
            "service_boundary": "AinerWise provides monitoring, alarm coordination and inspection. Hardware follows supplier warranty; on-site visits are quoted separately.",
        },
    },
    {
        "title": "AquaGuard — Water & Effluent Compliance Monitoring",
        "slug": "aquaguard", "category": "water", "solution_line": "aquaguard", "icon": "mdi-water-percent",
        "description": "pH, conductivity, turbidity, COD and temperature monitoring for effluent, process and pool water, with environmental compliance reports, probe calibration/replacement, and partner-led delivery.",
        "target_scenarios_json": ["Factory effluent", "Food & beverage", "Pharmaceutical", "Hotel pools", "Process water"],
        "pain_points_json": ["Environmental fines", "Mandatory discharge records", "Probe drift & maintenance", "Manual sampling"],
        "budget_tiers_json": {"starter": {"label": "Single Outfall", "description": "pH/EC + reporting", "starting_from": 4000}, "standard": {"label": "Multi-Parameter", "description": "COD/turbidity + calibration plan", "starting_from": 12000}, "enterprise": {"label": "Regulated Site", "description": "Auto-sampling + SLA + AMC", "starting_from": 30000}},
        "delivery_flow_json": ["Compliance Assessment", "Probe & Sampling Design", "Partner Install", "Reporting Setup", "Calibration Plan", "AMC"],
        "lifecycle_content_json": {
            "headline": "Water & Effluent Compliance Package — calibrated probes, audit-ready reports, and consumables, delivered with professional partners.",
            "monitoring_points": [{"name": "pH / Conductivity", "detail": "Continuous water-quality monitoring per point."}, {"name": "Turbidity / COD", "detail": "Discharge-quality and load monitoring."}, {"name": "Discharge Alarms", "detail": "Out-of-range and abnormal-discharge alerts."}],
            "alert_channels": ["SMS", "Telegram", "Email", "Regulator-ready log"],
            "reports": ["Monthly environmental compliance report", "Calibration certificates", "Discharge event log"],
            "calibration_consumables": ["Probe calibration with certificate", "Calibration fluid", "Probe replacement on lifecycle schedule"],
            "recurring_charges": ["Probe replacement", "Calibration fluid & service", "Compliance reporting", "Alarm watch", "Annual Maintenance Contract"],
            "amc_options": [{"name": "Compliance", "detail": "Reports + calibration + probe maintenance."}, {"name": "Commercial", "detail": "Multi-point + priority response + partner dispatch."}],
            "service_boundary": "AquaGuard requires professional partner support for calibration and environmental delivery. Hardware follows supplier warranty; on-site visits are quoted separately.",
        },
    },
    {
        "title": "EnergyGuard — Solar, Storage & Energy Monitoring",
        "slug": "energyguard", "category": "energy", "solution_line": "energyguard", "icon": "mdi-solar-power-variant",
        "description": "Solar, battery, EV and load monitoring with peak-tariff optimization, battery-health insight, monthly AI energy reports, and remote operations.",
        "target_scenarios_json": ["Commercial solar", "Battery storage", "EV fleets", "Industrial energy", "Multi-site energy"],
        "pain_points_json": ["Peak-demand charges", "Blind battery health", "Uncoordinated EV charging", "Missed inverter alarms"],
        "budget_tiers_json": {"starter": {"label": "Monitoring", "description": "Inverter + meter dashboard", "starting_from": 4500}, "standard": {"label": "Optimization", "description": "Battery + EV + tariff + reports", "starting_from": 14500}, "enterprise": {"label": "Remote Ops", "description": "Multi-site + SLA + optimization", "starting_from": 32000}},
        "delivery_flow_json": ["Energy Audit", "Meter Integration", "Dashboard", "Alert Rules", "Monthly Reports", "Remote Ops"],
        "lifecycle_content_json": {
            "headline": "Energy Monitoring & Optimization Package — health reports, optimization and remote operations, not just a dashboard.",
            "monitoring_points": [{"name": "Solar & Inverter", "detail": "Generation, inverter health and alarms."}, {"name": "Battery & Load", "detail": "Battery SOC/health and key-load metering."}, {"name": "EV & Tariff", "detail": "EV charging coordination and peak-tariff logic."}],
            "alert_channels": ["Email", "Telegram", "In-app"],
            "reports": ["Monthly AI energy report", "Battery health report", "Optimization recommendations"],
            "calibration_consumables": ["Meter health checks", "Gateway lifecycle planning"],
            "recurring_charges": ["Platform & reporting", "Energy optimization advisory", "Remote operations", "Annual Maintenance Contract"],
            "amc_options": [{"name": "Basic", "detail": "Monitoring + monthly report."}, {"name": "Commercial", "detail": "Optimization + remote ops + priority response."}],
            "service_boundary": "AinerWise provides monitoring, reporting and remote operations. Hardware follows supplier warranty; on-site visits are quoted separately.",
        },
    },
    {
        "title": "FactoryPulse — Non-Invasive OEE & Predictive Maintenance",
        "slug": "factorypulse", "category": "industrial", "solution_line": "factorypulse", "icon": "mdi-factory",
        "description": "Non-invasive machine energy and run/stop monitoring, OEE dashboards, PLC/SCADA/robot integration, energy reports, predictive-maintenance algorithms, and point expansion as a recurring service.",
        "target_scenarios_json": ["Old factories", "Machining & injection", "Packaging lines", "Process plants", "Industrial parks"],
        "pain_points_json": ["Hidden machine energy", "Unplanned downtime", "Siloed PLC/SCADA data", "No predictive maintenance"],
        "budget_tiers_json": {"starter": {"label": "Visibility", "description": "Machine meters + OT gateway", "starting_from": 15000}, "standard": {"label": "OEE", "description": "Line energy + PLC/SCADA + dashboard", "starting_from": 48000}, "premium": {"label": "Premium AI", "description": "Anomaly + predictive maintenance + edge AI", "starting_from": 98000}},
        "delivery_flow_json": ["OT/IT Safety Review", "Protocol Audit", "Pilot Line", "OEE Dashboard", "Algorithm Subscription", "Expansion & SLA"],
        "lifecycle_content_json": {
            "headline": "Non-Invasive OEE & Energy Package — algorithm subscription, point expansion and SLA, recurring by design.",
            "monitoring_points": [{"name": "Machine Energy & Run/Stop", "detail": "Non-invasive per-machine current and uptime."}, {"name": "Compressor / Chiller / Motors", "detail": "Utility and VFD energy + vibration/temperature."}, {"name": "PLC / SCADA / Robot", "detail": "OT-isolated protocol integration."}],
            "alert_channels": ["Email", "Telegram", "SCADA / dashboard"],
            "reports": ["OEE dashboard", "Monthly energy report", "Predictive-maintenance alerts"],
            "calibration_consumables": ["Sensor health checks", "VFD/probe lifecycle planning"],
            "recurring_charges": ["OEE algorithm subscription", "Monitoring point expansion", "Energy reporting", "Annual Maintenance Contract"],
            "amc_options": [{"name": "Commercial", "detail": "OEE + maintenance + spare priority."}, {"name": "Premium", "detail": "Predictive maintenance + edge AI + SLA."}],
            "service_boundary": "Industrial integration requires OT/IT safety review and engineering. Hardware follows supplier warranty; on-site visits are quoted separately.",
        },
    },
    {
        "title": "AssetPulse — High-Value Asset & Tool Tracking",
        "slug": "assetpulse", "category": "asset", "solution_line": "assetpulse", "icon": "mdi-tag-multiple",
        "description": "BLE/UWB/LoRa tag tracking for tools and high-value assets with geofence alerts, inventory, and multi-site reports — sold as a tag subscription and recurring service.",
        "target_scenarios_json": ["Construction sites", "Hospitals", "Warehouses", "Factories", "Equipment rental"],
        "pain_points_json": ["Lost tools & assets", "Slow inventory", "No geofence alerts", "Tag battery attrition"],
        "budget_tiers_json": {"starter": {"label": "Pilot", "description": "Tags + gateways + dashboard", "starting_from": 3000}, "standard": {"label": "Site", "description": "Geofence + inventory + reports", "starting_from": 9000}, "enterprise": {"label": "Multi-Site", "description": "Tag subscription + multi-site reports", "starting_from": 22000}},
        "delivery_flow_json": ["Asset Survey", "Tag & Gateway Plan", "Install", "Geofence & Inventory", "Tag Subscription", "Multi-Site Reports"],
        "lifecycle_content_json": {
            "headline": "Asset Tracking Package — tag subscription, replacement and geofence service, recurring by design.",
            "monitoring_points": [{"name": "Asset Tags", "detail": "BLE/UWB/LoRa tags on tools and assets."}, {"name": "Geofence & Zones", "detail": "Boundary and zone alerts."}, {"name": "Inventory", "detail": "Automated count and last-seen location."}],
            "alert_channels": ["App", "Email", "Telegram"],
            "reports": ["Asset inventory report", "Geofence event log", "Multi-site utilization"],
            "calibration_consumables": ["Tag battery replacement", "Tag replacement on attrition"],
            "recurring_charges": ["Tag subscription (per tag)", "Tag replacement", "Geofence alert service", "Multi-site management"],
            "amc_options": [{"name": "Basic", "detail": "Tracking + inventory."}, {"name": "Commercial", "detail": "Geofence + multi-site reports + priority."}],
            "service_boundary": "AinerWise provides tracking and reporting. Tags follow supplier warranty; on-site visits are quoted separately.",
        },
    },
    {
        "title": "AgriBrain — Greenhouse & Farm Intelligence (Future-Ready)",
        "slug": "agribrain", "category": "agriculture", "solution_line": "agribrain", "icon": "mdi-sprout",
        "description": "Future-ready environmental monitoring for greenhouses, farms and irrigation: soil, climate, water and fertilizer insight with seasonal service. Bounded as future expansion until delivery partners and demand are validated.",
        "target_scenarios_json": ["Greenhouses", "Farms", "Irrigation", "Agritech pilots"],
        "pain_points_json": ["Water & fertilizer waste", "Manual labor", "No environmental insight"],
        "budget_tiers_json": {"future": {"label": "Future-Ready", "description": "Concept and pilot scope; engineering review required"}},
        "delivery_flow_json": ["Concept", "Pilot Scope", "Partner Validation", "Seasonal Service"],
        "lifecycle_content_json": {
            "headline": "AgriBrain is a future-ready expansion line, kept bounded until delivery partners and demand are validated.",
            "monitoring_points": [{"name": "Soil & Climate", "detail": "Soil moisture, temperature, humidity, light."}, {"name": "Water & Fertilizer", "detail": "Irrigation and fertigation insight."}],
            "alert_channels": ["App", "SMS"],
            "reports": ["Seasonal environmental summary (concept)"],
            "calibration_consumables": ["Sensor maintenance", "Seasonal calibration"],
            "recurring_charges": ["Sensor maintenance", "Seasonal service", "Water/fertilizer optimization advisory"],
            "amc_options": [{"name": "Seasonal", "detail": "Seasonal maintenance and advisory (concept)."}],
            "service_boundary": "Concept/future-ready line. Scope, delivery and pricing require partner validation and engineering review.",
        },
    },
    {
        "title": "Remote Maintenance & Support",
        "slug": "remote-maintenance",
        "category": "service",
        "icon": "mdi-remote-desktop",
        "description": "Ongoing remote monitoring, maintenance, firmware updates, and technical support for installed smart building systems. Annual service plans with guaranteed response times.",
        "target_scenarios_json": ["Existing Installations", "Hotels", "Commercial Buildings", "Multi-Site"],
        "pain_points_json": ["No ongoing support", "Outdated firmware", "Slow issue resolution", "System degradation"],
        "budget_tiers_json": {
            "budget": {"label": "Basic", "description": "Remote monitoring + email support", "starting_from": 50},
            "standard": {"label": "Standard", "description": "Monitoring + phone support + annual check", "starting_from": 150},
            "premium": {"label": "Premium", "description": "24/7 monitoring + priority response + spare parts", "starting_from": 400},
        },
        "delivery_flow_json": ["Assessment", "Setup Remote Access", "Configure Monitoring", "Define SLA", "Activate"],
    },
]

SERVICE_PACKAGES = [
    {
        "name": "Included Remote Assurance",
        "slug": "basic-support",
        "years": 3,
        "description": "Included with qualifying delivered projects: practical remote support without bundling costly site visits.",
        "included_services_json": ["Remote diagnosis and technical consultation", "Handover documentation and configuration records", "Supplier warranty coordination", "Remote configuration backup guidance"],
        "sla_json": {"response_hours": 48, "on_site_visits": 0, "remote_sessions": -1},
        "price_rule_json": {"billing": "included_with_qualifying_project", "remote_support": "reasonable_use", "on_site": "quoted_separately", "term_label": "3 years included"},
        "public_visible": True,
        "sort_order": 1,
    },
    {
        "name": "Lifecycle Care Plan",
        "slug": "standard-3yr",
        "years": 1,
        "description": "A renewable annual plan for customers who want proactive remote maintenance and clearer lifecycle planning.",
        "included_services_json": ["Scheduled remote health review", "Configuration backup audit", "Compatibility and upgrade advice", "Spare parts pool planning", "Priority remote response"],
        "sla_json": {"response_hours": 24, "on_site_visits": 0, "remote_sessions": 12},
        "price_rule_json": {"billing": "annual_paid_plan", "on_site": "quoted_separately", "term_label": "Annual paid plan"},
        "public_visible": True,
        "sort_order": 2,
    },
    {
        "name": "Managed SLA Plan",
        "slug": "lifecycle-5yr",
        "years": 1,
        "description": "A custom plan for business-critical sites that need agreed response targets, monitoring strategy, and local dispatch coordination.",
        "included_services_json": ["Agreed SLA response targets", "Monitoring and maintenance calendar", "Dedicated spare parts strategy", "Local partner dispatch coordination", "Quarterly service summary"],
        "sla_json": {"response_hours": 4, "on_site_visits": 0, "remote_sessions": -1},
        "price_rule_json": {"billing": "custom_quote", "on_site": "retainer_or_visit_pack", "term_label": "Custom SLA quote"},
        "public_visible": True,
        "sort_order": 3,
    },
    {
        "name": "Commercial Support 8 Years",
        "slug": "commercial-8yr",
        "years": 8,
        "description": "8-year commercial support for hotels and commercial buildings with guaranteed uptime.",
        "included_services_json": ["24/7 monitoring", "Unlimited remote support", "6 on-site visits/year", "Critical spare parts on-site", "Annual system optimization", "Energy efficiency review"],
        "sla_json": {"response_hours": 4, "on_site_visits": 6, "remote_sessions": -1},
        "public_visible": False,
        "sort_order": 4,
    },
    {
        "name": "Premium Enterprise 10 Years",
        "slug": "premium-10yr",
        "years": 10,
        "description": "10-year premium enterprise support with dedicated account manager and SLA guarantees.",
        "included_services_json": ["Dedicated account manager", "24/7 priority monitoring", "Unlimited on-site visits", "Full spare parts coverage", "Quarterly optimization", "Energy saving review", "Technology upgrade consultation"],
        "sla_json": {"response_hours": 2, "on_site_visits": -1, "remote_sessions": -1},
        "public_visible": False,
        "sort_order": 5,
    },
]

REGIONS = [
    {"code": "RS", "name": "Serbia", "currency_code": "EUR", "language_codes_json": ["en", "sr"], "is_active": True, "timezone": "Europe/Belgrade"},
    {"code": "PL", "name": "Poland", "currency_code": "PLN", "language_codes_json": ["en", "pl"], "is_active": False, "timezone": "Europe/Warsaw"},
    {"code": "NZ", "name": "New Zealand", "currency_code": "NZD", "language_codes_json": ["en"], "is_active": False, "timezone": "Pacific/Auckland"},
    {"code": "AU", "name": "Australia", "currency_code": "AUD", "language_codes_json": ["en"], "is_active": False, "timezone": "Australia/Sydney"},
]


async def main():
    async with async_session_factory() as db:
        for name, slug, icon, order in CATEGORIES:
            existing = await db.execute(select(ProductCategory).where(ProductCategory.slug == slug))
            if not existing.scalar_one_or_none():
                db.add(ProductCategory(name=name, slug=slug, icon=icon, sort_order=order))

        await db.flush()
        category_rows = await db.execute(select(ProductCategory))
        category_by_slug = {category.slug: category for category in category_rows.scalars().all()}

        for product_data in PRODUCTS:
            existing = await db.execute(select(Product).where(Product.slug == product_data["slug"]))
            if existing.scalar_one_or_none():
                continue
            data = product_data.copy()
            category_slug = data.pop("category_slug")
            category = category_by_slug.get(category_slug)
            if category:
                data["category_id"] = category.id
            db.add(Product(**data))

        for sol_data in SOLUTIONS:
            existing = await db.execute(select(Solution).where(Solution.slug == sol_data["slug"]))
            if not existing.scalar_one_or_none():
                db.add(Solution(**sol_data, public_visible=True))

        for pkg_data in SERVICE_PACKAGES:
            existing = await db.execute(select(ServicePackage).where(ServicePackage.slug == pkg_data["slug"]))
            existing_pkg = existing.scalar_one_or_none()
            if existing_pkg:
                for key, value in pkg_data.items():
                    setattr(existing_pkg, key, value)
            else:
                db.add(ServicePackage(**pkg_data))

        for reg_data in REGIONS:
            existing = await db.execute(select(Region).where(Region.code == reg_data["code"]))
            if not existing.scalar_one_or_none():
                db.add(Region(**reg_data))

        await db.commit()
        print("Seed data ensured successfully")


if __name__ == "__main__":
    asyncio.run(main())
