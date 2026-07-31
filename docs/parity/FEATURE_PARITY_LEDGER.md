# Feature Parity Ledger
Generated at: 2026-06-13T06:56:30.367984+00:00

This file is generated from the repository source tree. Edit the generator, then regenerate the ledger.

## Summary

| Source Project | Surface | Capability Type | Count | Status Mix |
|---|---|---:|---:|---|
| Ainerwise | Admin | exception_flow | 531 | READY_FOR_VERIFY:531 |
| Ainerwise | Admin | operation | 296 | READY_FOR_VERIFY:296 |
| Ainerwise | Admin | page | 100 | READY_FOR_VERIFY:100 |
| Ainerwise | Admin | state_machine | 272 | READY_FOR_VERIFY:272 |
| Ainerwise | Data | model | 147 | READY_FOR_VERIFY:147 |
| Ainerwise | Gap | planned_portal_gap | 6 | READY_FOR_VERIFY:6 |
| Ainerwise | H5 | exception_flow | 352 | READY_FOR_VERIFY:352 |
| Ainerwise | H5 | operation | 138 | READY_FOR_VERIFY:138 |
| Ainerwise | H5 | page | 85 | READY_FOR_VERIFY:85 |
| Ainerwise | H5 | state_machine | 116 | READY_FOR_VERIFY:116 |
| Ainerwise | Infrastructure | infrastructure | 11 | READY_FOR_VERIFY:11 |
| Ainerwise | Integration | integration | 17 | READY_FOR_VERIFY:17 |
| Ainerwise | Migration | migration | 60 | READY_FOR_VERIFY:60 |
| Ainerwise | Module | module | 14 | READY_FOR_VERIFY:14 |
| Ainerwise | PC | exception_flow | 307 | READY_FOR_VERIFY:307 |
| Ainerwise | PC | operation | 127 | READY_FOR_VERIFY:127 |
| Ainerwise | PC | page | 100 | READY_FOR_VERIFY:100 |
| Ainerwise | PC | state_machine | 96 | READY_FOR_VERIFY:96 |
| Ainerwise | Permission | permission_model | 3 | READY_FOR_VERIFY:3 |
| Ainerwise | Role | role | 13 | READY_FOR_VERIFY:13 |
| Ainerwise | Runtime API | api | 691 | READY_FOR_VERIFY:691 |
| Ainerwise | Script | script | 18 | READY_FOR_VERIFY:18 |
| Ainerwise | Service | service | 59 | READY_FOR_VERIFY:59 |
| Ainerwise | Task | task | 15 | READY_FOR_VERIFY:15 |
| Ainerwise | Workflow | frontend_workflow | 38 | READY_FOR_VERIFY:38 |
| Ainerwise | Workflow | workflow | 4 | READY_FOR_VERIFY:4 |
| CebuProjects | API | api | 265 | TODO:265 |
| CebuProjects | Admin | admin_view | 24 | TODO:24 |
| CebuProjects | Admin | exception_flow | 102 | TODO:102 |
| CebuProjects | Admin | operation | 125 | TODO:125 |
| CebuProjects | Admin | state_machine | 106 | TODO:106 |
| CebuProjects | Admin API | api | 4 | TODO:4 |
| CebuProjects | Data | model | 133 | TODO:133 |
| CebuProjects | H5 | exception_flow | 120 | TODO:120 |
| CebuProjects | H5 | operation | 161 | TODO:161 |
| CebuProjects | H5 | page | 41 | TODO:41 |
| CebuProjects | H5 | state_machine | 108 | TODO:108 |
| CebuProjects | Infrastructure | infrastructure | 8 | TODO:8 |
| CebuProjects | Integration | integration | 1 | TODO:1 |
| CebuProjects | Migration | migration | 15 | TODO:15 |
| CebuProjects | PC | exception_flow | 201 | TODO:201 |
| CebuProjects | PC | operation | 194 | TODO:194 |
| CebuProjects | PC | page | 59 | TODO:59 |
| CebuProjects | PC | state_machine | 201 | TODO:201 |
| CebuProjects | Role | role | 12 | TODO:12 |
| CebuProjects | Script | script | 1 | TODO:1 |
| CebuProjects | Service | service | 15 | TODO:15 |
| CebuProjects | Workflow | frontend_workflow | 11 | TODO:11 |

## Cebu Baseline Guards

| Source Project | Surface | Capability Type | Expected | Actual | Result |
|---|---|---:|---:|---:|---|
| CebuProjects | PC | page | 59 | 59 | PASS |
| CebuProjects | H5 | page | 41 | 41 | PASS |
| CebuProjects | Admin | admin_view | 24 | 24 | PASS |

## Portal Coverage Snapshot

| Target Portal | Source Entries | Source Projects |
|---|---:|---|
| admin_cebu | 1 | Ainerwise |
| ai_solution_core | 4 | Ainerwise |
| ai_supervisor_admin | 48 | Ainerwise |
| ainerwise_core_api | 591 | Ainerwise |
| ainerwise_core_data | 355 | Ainerwise, CebuProjects |
| automation_core | 15 | Ainerwise |
| cebu_admin | 582 | CebuProjects |
| cebu_buyer_h5 | 314 | CebuProjects |
| cebu_buyer_pc | 354 | CebuProjects |
| cebu_domain::ai_service | 1 | CebuProjects |
| cebu_domain::audit_service | 1 | CebuProjects |
| cebu_domain::backup_service | 1 | CebuProjects |
| cebu_domain::company_service | 1 | CebuProjects |
| cebu_domain::escrow_service | 1 | CebuProjects |
| cebu_domain::maps_config_service | 1 | CebuProjects |
| cebu_domain::marketplace_service | 1 | CebuProjects |
| cebu_domain::matching_service | 1 | CebuProjects |
| cebu_domain::notification_service | 1 | CebuProjects |
| cebu_domain::payment_service | 1 | CebuProjects |
| cebu_domain::project_ai_service | 1 | CebuProjects |
| cebu_domain::ranking_service | 1 | CebuProjects |
| cebu_domain::shipping_service | 1 | CebuProjects |
| cebu_domain::trust_service | 1 | CebuProjects |
| cebu_domain::wallet_service | 1 | CebuProjects |
| cebu_public_pc | 103 | CebuProjects |
| cebu_trade_shared | 70 | CebuProjects |
| consumer_h5 | 1 | Ainerwise |
| consumer_pc | 518 | Ainerwise |
| core_domain::acceptance | 1 | Ainerwise |
| core_domain::access | 1 | Ainerwise |
| core_domain::agent_runtime | 1 | Ainerwise |
| core_domain::agent_team | 1 | Ainerwise |
| core_domain::ai_agent | 1 | Ainerwise |
| core_domain::ai_analysis | 1 | Ainerwise |
| core_domain::ai_graph | 1 | Ainerwise |
| core_domain::amc | 1 | Ainerwise |
| core_domain::api | 4 | Ainerwise |
| core_domain::audit | 1 | Ainerwise |
| core_domain::backup_service | 1 | Ainerwise |
| core_domain::briefing | 1 | Ainerwise |
| core_domain::cases | 1 | Ainerwise |
| core_domain::commerce_messaging | 1 | Ainerwise |
| core_domain::commerce_settlement | 1 | Ainerwise |
| core_domain::commerce_trade | 1 | Ainerwise |
| core_domain::commerce_trust | 1 | Ainerwise |
| core_domain::consult | 1 | Ainerwise |
| core_domain::demo_bootstrap | 1 | Ainerwise |
| core_domain::demo_mode | 1 | Ainerwise |
| core_domain::documents | 1 | Ainerwise |
| core_domain::ecosystem | 1 | Ainerwise |
| core_domain::embeddings | 1 | Ainerwise |
| core_domain::esign | 1 | Ainerwise |
| core_domain::event_bus | 1 | Ainerwise |
| core_domain::factorypulse | 1 | Ainerwise |
| core_domain::field_service | 1 | Ainerwise |
| core_domain::finance | 1 | Ainerwise |
| core_domain::generate | 1 | Ainerwise |
| core_domain::knowledge | 1 | Ainerwise |
| core_domain::legacy_cutover | 1 | Ainerwise |
| core_domain::legacy_identity | 1 | Ainerwise |
| core_domain::legacy_migration | 1 | Ainerwise |
| core_domain::lifecycle_alerts | 1 | Ainerwise |
| core_domain::lifecycle_automation | 1 | Ainerwise |
| core_domain::lifecycle_lines | 1 | Ainerwise |
| core_domain::marketing_automation | 1 | Ainerwise |
| core_domain::marketing_briefs | 1 | Ainerwise |
| core_domain::marketing_reporting | 1 | Ainerwise |
| core_domain::models | 3 | Ainerwise |
| core_domain::notification_templates | 1 | Ainerwise |
| core_domain::partner_dispatch | 1 | Ainerwise |
| core_domain::partner_score | 1 | Ainerwise |
| core_domain::payments | 1 | Ainerwise |
| core_domain::portal_access | 1 | Ainerwise |
| core_domain::portal_policy | 1 | Ainerwise |
| core_domain::pricing | 1 | Ainerwise |
| core_domain::privacy | 1 | Ainerwise |
| core_domain::procurement_ai | 1 | Ainerwise |
| core_domain::procurement_analyze | 1 | Ainerwise |
| core_domain::procurement_boq | 1 | Ainerwise |
| core_domain::procurement_confidence | 1 | Ainerwise |
| core_domain::procurement_facts | 1 | Ainerwise |
| core_domain::procurement_packages | 1 | Ainerwise |
| core_domain::procurement_projects | 1 | Ainerwise |
| core_domain::procurement_rfq | 1 | Ainerwise |
| core_domain::project_access | 1 | Ainerwise |
| core_domain::quote_pdf | 1 | Ainerwise |
| core_domain::rate_limit | 1 | Ainerwise |
| core_domain::recurring_revenue | 1 | Ainerwise |
| core_domain::renewal_queue | 1 | Ainerwise |
| core_domain::rfq | 1 | Ainerwise |
| core_domain::schemas | 3 | Ainerwise |
| core_domain::service | 3 | Ainerwise |
| core_domain::spare_parts | 1 | Ainerwise |
| core_domain::storageguard | 1 | Ainerwise |
| core_domain::support_agent | 1 | Ainerwise |
| core_domain::warranty | 1 | Ainerwise |
| crew_lead_h5 | 1 | Ainerwise |
| customer_h5 | 423 | Ainerwise |
| customer_pc | 104 | Ainerwise |
| developer_pc | 9 | Ainerwise |
| field_worker_h5 | 74 | Ainerwise |
| frontend_admin | 1000 | Ainerwise |
| identity_and_portal_core | 28 | Ainerwise, CebuProjects |
| integration_boundary | 22 | Ainerwise, CebuProjects |
| kiosk_h5 | 42 | Ainerwise |
| marketing_admin | 210 | Ainerwise |
| marketing_h5 | 1 | Ainerwise |
| migration_control | 19 | Ainerwise, CebuProjects |
| partner_company_h5 | 94 | Ainerwise |
| partner_company_pc | 1 | Ainerwise |
| shared_auth | 16 | Ainerwise, CebuProjects |
| shared_h5_portals | 18 | Ainerwise, CebuProjects |
| shared_pc_portals | 20 | Ainerwise, CebuProjects |
| shared_platform_infrastructure | 19 | Ainerwise, CebuProjects |
| supplier_h5 | 209 | Ainerwise, CebuProjects |
| supplier_pc | 165 | CebuProjects |

## Immediate Gaps

- Cebu legacy entries remain TODO until route, API, object permission, and parity evidence are mapped and independently verified.
- Existing Ainerwise entries are conservatively seeded as READY_FOR_VERIFY; this is not VERIFIED evidence.
- VERIFIED is rejected unless status-overrides.json contains repeatable independent verification evidence.
- Portal route ownership, shared auth, compatibility APIs, worker/offline capabilities, automation tasks, and external integrations remain dependent on follow-up implementation packages.
