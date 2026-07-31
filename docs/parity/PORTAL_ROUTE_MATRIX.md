# Portal Route Matrix
Generated at: 2026-06-13T06:56:30.367984+00:00

| Target Portal | Physical Frontend | Roles | Source Entries | Representative Routes |
|---|---|---|---:|---|
| ai_supervisor_admin | frontend-admin | ai_supervisor, admin | 48 | /agent-missions, /agent-missions#exception_flow-L134, /agent-missions#exception_flow-L145, /agent-missions#exception_flow-L153, /agent-missions#exception_flow-L154 |
| ainerwise_core_api | backend | authenticated_via_grants | 591 | API only |
| ainerwise_core_data | backend | database_owner, owning_module_operator | 355 | migration:0001_initial, migration:0002_admin_extensions, migration:0003_trust_profiles, migration:0004_wallets_maps_p0, migration:0005_addresses_shipping_categories |
| automation_core | worker | system_worker, admin | 15 | worker:backup_tasks, worker:briefing_tasks, worker:event_consumers, worker:event_tasks, worker:ingestion_tasks |
| cebu_admin | frontend-admin | admin, finance_auditor, risk_operator | 582 | /cebu-admin/ad-campaigns, /cebu-admin/ad-campaigns#exception_flow-L103, /cebu-admin/ad-campaigns#exception_flow-L116, /cebu-admin/ad-campaigns#exception_flow-L119, /cebu-admin/ad-campaigns#exception_flow-L130 |
| cebu_buyer_h5 | frontend-h5 | buyer, customer_owner, customer_member | 314 | /, /#operation-L121, /#operation-L60, /auth/login, /auth/login#exception_flow-L176 |
| cebu_buyer_pc | frontend-pc | buyer, customer_owner, customer_member | 354 | /cebu/buyer/company-profile, /cebu/buyer/company-profile#exception_flow-L131, /cebu/buyer/company-profile#exception_flow-L144, /cebu/buyer/company-profile#exception_flow-L145, /cebu/buyer/company-profile#operation-L8 |
| cebu_public_pc | frontend-pc | anonymous_guest, buyer, supplier_operator | 103 | /cebu, /cebu#operation-L100, /cebu#operation-L36, /cebu/categories, /cebu/categories#exception_flow-L79 |
| cebu_trade_shared | backend | buyer, supplier_operator, finance_auditor | 70 | API only |
| consumer_h5 | frontend-h5 | customer_owner, customer_member, anonymous_guest | 1 | portal:consumer_h5 |
| consumer_pc | frontend-pc | customer_owner, customer_member, anonymous_guest | 518 | /, /#exception_flow-L309, /#exception_flow-L310, /#exception_flow-L316, /#exception_flow-L317 |
| crew_lead_h5 | frontend-h5 | crew_lead | 1 | portal:crew_lead_h5 |
| customer_h5 | frontend-h5 | customer_owner, customer_member | 423 | /, /#exception_flow-L176, /#operation-L54, /#state_machine-L155, /#state_machine-L156 |
| customer_pc | frontend-pc | customer_owner, customer_member | 104 | /portal, /portal#exception_flow-L160, /portal#exception_flow-L161, /portal#operation-L17, /portal#state_machine-L129 |
| developer_pc | frontend-pc | developer | 9 | /developers, /developers#exception_flow-L28, /developers/listings, /developers/listings#exception_flow-L19, /developers/listings#exception_flow-L47 |
| field_worker_h5 | frontend-h5 | crew_lead, installer_worker, electrician_worker, maintenance_worker | 74 | /field/tasks/:id, /field/tasks/:id#exception_flow-L108, /field/tasks/:id#exception_flow-L111, /field/tasks/:id#exception_flow-L112, /field/tasks/:id#exception_flow-L129 |
| frontend_admin | frontend-admin | admin, finance_auditor, project_manager | 1000 | /, /#exception_flow-L124, /#operation-L10, /#operation-L49, /#operation-L73 |
| identity_and_portal_core | backend | authenticated_via_membership_and_grants | 28 | model:PortalGrant, model:Workspace, model:WorkspaceMembership, role:ADMIN, role:AUDITOR |
| integration_boundary | backend | admin, system_integration | 22 | integration:009_integration_settings, integration:016_phase_e_esign_stripe, integration:026_marketing_integration_clients, integration:027_marketing_media_uploads, integration:033_legacy_bridge_identity |
| kiosk_h5 | frontend-h5 | kiosk_staff, anonymous_guest | 42 | /kiosk, /kiosk#exception_flow-L265, /kiosk#exception_flow-L291, /kiosk#exception_flow-L334, /kiosk#exception_flow-L337 |
| marketing_admin | frontend-admin | marketing_operator, admin | 210 | /marketing, /marketing#exception_flow-L251, /marketing#exception_flow-L261, /marketing#operation-L107, /marketing#operation-L108 |
| marketing_h5 | frontend-h5 | marketing_operator | 1 | portal:marketing_h5 |
| migration_control | operator | admin, devops_operator | 19 | Ainerwise/backend/scripts/create_demo_buyer.py, Ainerwise/backend/scripts/create_superadmin.py, Ainerwise/backend/scripts/phase_c_e2e.py, Ainerwise/backend/scripts/seed_data.py, Ainerwise/backend/scripts/seed_demo_environment.py |
| partner_company_h5 | frontend-h5 | partner_company_owner, partner_dispatcher | 94 | /partner, /partner#exception_flow-L111, /partner#exception_flow-L112, /partner#exception_flow-L80, /partner#exception_flow-L93 |
| partner_company_pc | frontend-pc | partner_company_owner, partner_dispatcher | 1 | portal:partner_company_pc |
| shared_auth | backend | anonymous_or_authenticated | 16 | API only |
| shared_h5_portals | frontend-h5 | portal_member | 18 | frontend_workflow:auth, frontend_workflow:intent, frontend_workflow:notification, frontend_workflow:offer, frontend_workflow:order |
| shared_pc_portals | frontend-pc | portal_member | 20 | frontend_workflow:app, frontend_workflow:auth, frontend_workflow:intent, frontend_workflow:notification, frontend_workflow:offer |
| supplier_h5 | frontend-h5 | supplier_operator | 209 | /supplier, /supplier#exception_flow-L1, /supplier#exception_flow-L18, /supplier#exception_flow-L19, /supplier#exception_flow-L8 |
| supplier_pc | frontend-pc | supplier_operator | 165 | /supplier-onboarding, /supplier/ads, /supplier/ads#exception_flow-L100, /supplier/ads#exception_flow-L101, /supplier/ads#exception_flow-L113 |

## Route Guard Notes

- Customer, Partner Company, Supplier, Field Worker, and Cebu Buyer must render distinct layouts, menus, and route allowlists even when they share a physical frontend.
- Any route listed here still needs membership, portal grant, workspace, region, and object-level verification before it can move to VERIFIED.
- Cebu public PC routes are intentionally isolated under the cebu portal family to avoid collapsing buyer and supplier flows into a generic consumer shell.
