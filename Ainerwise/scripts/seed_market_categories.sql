-- AISLOS Market — real EU Smart Living / Smart Building category set.
-- Idempotent: re-runnable, skips existing slugs. Run:
--   docker compose exec -T postgres psql -U ainerwise -d ainerwise -f - < scripts/seed_market_categories.sql
INSERT INTO trade_category_schemas (id, slug, name, version, schema_json, status)
SELECT gen_random_uuid(), v.slug, v.name, 1, '{}'::jsonb, 'active'
FROM (VALUES
  ('knx',                 'KNX & Building Automation'),
  ('smart-home',          'Smart Home Automation'),
  ('solar-pv',            'Solar & PV'),
  ('energy-storage',      'Energy Storage & Batteries'),
  ('energy-management',   'Energy Management'),
  ('ev-charging',         'EV Charging'),
  ('security-cctv',       'Security & CCTV'),
  ('access-control',      'Access Control'),
  ('smart-locks',         'Smart Locks'),
  ('lighting',            'Smart Lighting'),
  ('hvac-climate',        'HVAC & Climate'),
  ('shading-blinds',      'Blinds & Shading'),
  ('av-multiroom',        'Audio / Video / Multiroom'),
  ('networking-it',       'Networking & IT'),
  ('sensors-iot',         'Sensors & IoT'),
  ('fire-safety',         'Fire & Safety')
) AS v(slug, name)
WHERE NOT EXISTS (SELECT 1 FROM trade_category_schemas c WHERE c.name = v.name)
ON CONFLICT (slug) DO NOTHING;
