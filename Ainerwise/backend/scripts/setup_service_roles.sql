-- Service role setup for the AinerWise OS permission matrix (Phase A).
--
--   service                  public      ai          channels
--   backend (ainerwise)      owner/rw    owner/rw    owner/rw
--   ainerwise_orchestrator   read-only   read-write  read-only
--   ainerwise_gateway        none        none        read-write
--
-- Idempotent: safe to re-run after every migration that adds tables.
-- (GRANT ... ON ALL TABLES only covers existing tables; ALTER DEFAULT
-- PRIVILEGES covers tables the `ainerwise` role creates later.)
--
-- Usage (dev):
--   docker compose exec -T postgres psql -U ainerwise -d ainerwise \
--     -v orchestrator_password='change_me_orch' -v gateway_password='change_me_gw' \
--     < backend/scripts/setup_service_roles.sql
--
-- Run AFTER `alembic upgrade head` so the ai/channels schemas exist.

\set ON_ERROR_STOP on

\if :{?orchestrator_password}
\else
\set orchestrator_password 'ainerwise_orchestrator_dev'
\endif
\if :{?gateway_password}
\else
\set gateway_password 'ainerwise_gateway_dev'
\endif

SELECT format('CREATE ROLE ainerwise_orchestrator LOGIN PASSWORD %L', :'orchestrator_password')
WHERE NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'ainerwise_orchestrator')
\gexec

SELECT format('CREATE ROLE ainerwise_gateway LOGIN PASSWORD %L', :'gateway_password')
WHERE NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'ainerwise_gateway')
\gexec

SELECT format('GRANT CONNECT ON DATABASE %I TO ainerwise_orchestrator, ainerwise_gateway', current_database())
\gexec

-- orchestrator: read business data, own the ai schema contents, observe channels
GRANT USAGE ON SCHEMA public, ai, channels TO ainerwise_orchestrator;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO ainerwise_orchestrator;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA ai TO ainerwise_orchestrator;
GRANT SELECT ON ALL TABLES IN SCHEMA channels TO ainerwise_orchestrator;
ALTER DEFAULT PRIVILEGES FOR ROLE ainerwise IN SCHEMA public
    GRANT SELECT ON TABLES TO ainerwise_orchestrator;
ALTER DEFAULT PRIVILEGES FOR ROLE ainerwise IN SCHEMA ai
    GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO ainerwise_orchestrator;
ALTER DEFAULT PRIVILEGES FOR ROLE ainerwise IN SCHEMA channels
    GRANT SELECT ON TABLES TO ainerwise_orchestrator;

-- gateway: channels schema only, no business or ai access
GRANT USAGE ON SCHEMA channels TO ainerwise_gateway;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA channels TO ainerwise_gateway;
ALTER DEFAULT PRIVILEGES FOR ROLE ainerwise IN SCHEMA channels
    GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO ainerwise_gateway;
