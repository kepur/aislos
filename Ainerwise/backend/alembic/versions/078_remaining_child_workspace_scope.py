"""Bind remaining AI, Marketing, Field and Delivery child rows to Workspaces.

Revision ID: 078
Revises: 077
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "078"
down_revision: Union[str, None] = "077"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

DEFAULT_WORKSPACE_ID = "00000000-0000-4000-8000-000000000001"

WORKSPACE_COLUMNS = (
    ("ai", "messages", "ai_messages"),
    ("ai", "agent_runs", "ai_agent_runs"),
    ("ai", "memories", "ai_memories"),
    ("channels", "channel_threads", "channels_channel_threads"),
    (None, "publish_jobs", "publish_jobs"),
    (None, "marketing_creative_brief_versions", "marketing_creative_brief_versions"),
    (None, "marketing_media_uploads", "marketing_media_uploads"),
    (None, "crew_memberships", "crew_memberships"),
    (None, "field_tasks", "field_tasks"),
    (None, "task_assignments", "task_assignments"),
    (None, "agent_missions", "agent_missions"),
    (None, "agent_mission_tasks", "agent_mission_tasks"),
    (None, "bom_items", "bom_items"),
)

FIELD_NOT_NULL_TABLES = ("crew_memberships", "field_tasks", "task_assignments")


def _table(schema: str | None, table: str) -> str:
    return f"{schema}.{table}" if schema else table


def _add_workspace_column(schema: str | None, table: str, prefix: str) -> None:
    op.add_column(
        table,
        sa.Column("workspace_id", postgresql.UUID(as_uuid=True), nullable=True),
        schema=schema,
    )
    op.create_foreign_key(
        f"fk_{prefix}_workspace_id",
        table,
        "workspaces",
        ["workspace_id"],
        ["id"],
        source_schema=schema,
    )
    op.create_index(f"ix_{prefix}_workspace_id", table, ["workspace_id"], schema=schema)


def _drop_workspace_column(schema: str | None, table: str, prefix: str) -> None:
    op.drop_index(f"ix_{prefix}_workspace_id", table_name=table, schema=schema)
    op.drop_constraint(f"fk_{prefix}_workspace_id", table, type_="foreignkey", schema=schema)
    op.drop_column(table, "workspace_id", schema=schema)


def _assert_none(conn, query: str, message: str) -> None:
    if conn.execute(sa.text(query)).first():
        raise RuntimeError(message)


def _ensure_default_workspace(conn) -> None:
    conn.execute(
        sa.text(
            """
            INSERT INTO workspaces (id, name, slug, status)
            VALUES (:id, 'Default Workspace', 'default', 'active')
            ON CONFLICT (slug) DO NOTHING
            """
        ),
        {"id": DEFAULT_WORKSPACE_ID},
    )


def _default_workspace_sql() -> str:
    return "(SELECT id FROM workspaces WHERE slug = 'default' AND status = 'active' LIMIT 1)"


def _backfill_ai_children(conn) -> None:
    default_workspace = _default_workspace_sql()
    conn.execute(sa.text(f"UPDATE ai.conversations SET workspace_id = {default_workspace} WHERE workspace_id IS NULL"))
    conn.execute(
        sa.text(
            """
            UPDATE ai.messages AS child
            SET workspace_id = parent.workspace_id
            FROM ai.conversations AS parent
            WHERE parent.id = child.conversation_id
            """
        )
    )
    conn.execute(
        sa.text(
            """
            UPDATE ai.agent_runs AS child
            SET workspace_id = parent.workspace_id
            FROM ai.conversations AS parent
            WHERE parent.id = child.conversation_id
              AND child.conversation_id IS NOT NULL
            """
        )
    )
    conn.execute(
        sa.text(
            """
            UPDATE ai.memories AS child
            SET workspace_id = parent.workspace_id
            FROM ai.conversations AS parent
            WHERE parent.id = child.source_conversation_id
              AND child.source_conversation_id IS NOT NULL
            """
        )
    )
    conn.execute(
        sa.text(
            """
            UPDATE channels.channel_threads AS child
            SET workspace_id = parent.workspace_id
            FROM ai.conversations AS parent
            WHERE parent.id = child.conversation_id
              AND child.conversation_id IS NOT NULL
            """
        )
    )
    _assert_none(
        conn,
        """
        SELECT child.id
        FROM ai.messages AS child
        JOIN ai.conversations AS parent ON parent.id = child.conversation_id
        WHERE child.workspace_id IS NOT NULL
          AND parent.workspace_id IS NOT NULL
          AND child.workspace_id <> parent.workspace_id
        LIMIT 1
        """,
        "Cannot bind AI messages: Message and Conversation use different Workspaces.",
    )


def _backfill_marketing_children(conn) -> None:
    default_workspace = _default_workspace_sql()
    conn.execute(
        sa.text(f"UPDATE marketing_assets SET workspace_id = {default_workspace} WHERE workspace_id IS NULL")
    )
    conn.execute(
        sa.text(
            f"""
            UPDATE marketing_creative_briefs
            SET workspace_id = {default_workspace}
            WHERE workspace_id IS NULL
            """
        )
    )
    conn.execute(
        sa.text(
            """
            UPDATE marketing_media_requests AS request
            SET workspace_id = brief.workspace_id
            FROM marketing_creative_brief_versions AS version
            JOIN marketing_creative_briefs AS brief ON brief.id = version.brief_id
            WHERE version.id = request.brief_version_id
              AND request.workspace_id IS NULL
            """
        )
    )
    conn.execute(
        sa.text(
            f"""
            UPDATE marketing_media_requests
            SET workspace_id = {default_workspace}
            WHERE workspace_id IS NULL
            """
        )
    )
    conn.execute(
        sa.text(
            """
            UPDATE publish_jobs AS child
            SET workspace_id = asset.workspace_id
            FROM marketing_assets AS asset
            WHERE asset.id = child.asset_id
            """
        )
    )
    conn.execute(
        sa.text(
            """
            UPDATE marketing_creative_brief_versions AS child
            SET workspace_id = brief.workspace_id
            FROM marketing_creative_briefs AS brief
            WHERE brief.id = child.brief_id
            """
        )
    )
    conn.execute(
        sa.text(
            """
            UPDATE marketing_media_uploads AS child
            SET workspace_id = request.workspace_id
            FROM marketing_media_requests AS request
            WHERE request.id = child.media_request_id
            """
        )
    )
    _assert_none(
        conn,
        """
        SELECT child.id
        FROM publish_jobs AS child
        JOIN marketing_assets AS asset ON asset.id = child.asset_id
        WHERE child.workspace_id IS NOT NULL
          AND asset.workspace_id IS NOT NULL
          AND child.workspace_id <> asset.workspace_id
        LIMIT 1
        """,
        "Cannot bind publish jobs: Job and Marketing Asset use different Workspaces.",
    )
    _assert_none(
        conn,
        """
        SELECT child.id
        FROM marketing_creative_brief_versions AS child
        JOIN marketing_creative_briefs AS brief ON brief.id = child.brief_id
        WHERE child.workspace_id IS NOT NULL
          AND brief.workspace_id IS NOT NULL
          AND child.workspace_id <> brief.workspace_id
        LIMIT 1
        """,
        "Cannot bind creative brief versions: Version and Brief use different Workspaces.",
    )
    _assert_none(
        conn,
        """
        SELECT child.id
        FROM marketing_media_uploads AS child
        JOIN marketing_media_requests AS request ON request.id = child.media_request_id
        WHERE child.workspace_id IS NOT NULL
          AND request.workspace_id IS NOT NULL
          AND child.workspace_id <> request.workspace_id
        LIMIT 1
        """,
        "Cannot bind media uploads: Upload and Media Request use different Workspaces.",
    )


def _backfill_field_children(conn) -> None:
    conn.execute(
        sa.text(
            """
            UPDATE crew_memberships AS child
            SET workspace_id = crew.workspace_id
            FROM partner_crews AS crew
            WHERE crew.id = child.crew_id
            """
        )
    )
    conn.execute(
        sa.text(
            """
            UPDATE field_tasks AS child
            SET workspace_id = package.workspace_id
            FROM work_packages AS package
            WHERE package.id = child.work_package_id
            """
        )
    )
    conn.execute(
        sa.text(
            """
            UPDATE task_assignments AS child
            SET workspace_id = task.workspace_id
            FROM field_tasks AS task
            WHERE task.id = child.field_task_id
            """
        )
    )
    _assert_none(
        conn,
        """
        SELECT child.id
        FROM crew_memberships AS child
        LEFT JOIN partner_crews AS crew ON crew.id = child.crew_id
        WHERE child.workspace_id IS NULL OR crew.workspace_id IS NULL OR child.workspace_id <> crew.workspace_id
        LIMIT 1
        """,
        "Cannot bind crew memberships: parent Crew Workspace is missing or different.",
    )
    _assert_none(
        conn,
        """
        SELECT child.id
        FROM field_tasks AS child
        LEFT JOIN work_packages AS package ON package.id = child.work_package_id
        WHERE child.workspace_id IS NULL OR package.workspace_id IS NULL OR child.workspace_id <> package.workspace_id
        LIMIT 1
        """,
        "Cannot bind field tasks: parent WorkPackage Workspace is missing or different.",
    )
    _assert_none(
        conn,
        """
        SELECT child.id
        FROM task_assignments AS child
        LEFT JOIN field_tasks AS task ON task.id = child.field_task_id
        WHERE child.workspace_id IS NULL OR task.workspace_id IS NULL OR child.workspace_id <> task.workspace_id
        LIMIT 1
        """,
        "Cannot bind task assignments: parent FieldTask Workspace is missing or different.",
    )
    _assert_none(
        conn,
        """
        SELECT child.id
        FROM task_assignments AS child
        JOIN partner_crews AS crew ON crew.id = child.crew_id
        WHERE child.crew_id IS NOT NULL
          AND child.workspace_id <> crew.workspace_id
        LIMIT 1
        """,
        "Cannot bind task assignments: Assignment Crew and FieldTask use different Workspaces.",
    )
    for table in FIELD_NOT_NULL_TABLES:
        op.alter_column(table, "workspace_id", nullable=False)


def _backfill_delivery_children(conn) -> None:
    default_workspace = _default_workspace_sql()
    conn.execute(
        sa.text(
            f"""
            UPDATE projects
            SET workspace_id = {default_workspace}
            WHERE workspace_id IS NULL
              AND id IN (
                SELECT project_id FROM agent_missions
                UNION
                SELECT project_id FROM agent_mission_tasks
              )
            """
        )
    )
    conn.execute(
        sa.text(
            """
            UPDATE agent_missions AS child
            SET workspace_id = project.workspace_id
            FROM projects AS project
            WHERE project.id = child.project_id
            """
        )
    )
    conn.execute(
        sa.text(
            """
            UPDATE agent_mission_tasks AS child
            SET workspace_id = mission.workspace_id
            FROM agent_missions AS mission
            WHERE mission.id = child.mission_id
            """
        )
    )
    conn.execute(
        sa.text(
            """
            UPDATE agent_mission_tasks AS child
            SET workspace_id = project.workspace_id
            FROM projects AS project
            WHERE project.id = child.project_id
              AND child.workspace_id IS NULL
            """
        )
    )
    conn.execute(
        sa.text(
            f"""
            UPDATE proposal_plans
            SET workspace_id = {default_workspace}
            WHERE workspace_id IS NULL
              AND id IN (SELECT proposal_plan_id FROM bom_items)
            """
        )
    )
    conn.execute(
        sa.text(
            """
            UPDATE bom_items AS child
            SET workspace_id = plan.workspace_id
            FROM proposal_plans AS plan
            WHERE plan.id = child.proposal_plan_id
            """
        )
    )
    _assert_none(
        conn,
        """
        SELECT child.id
        FROM agent_missions AS child
        JOIN projects AS project ON project.id = child.project_id
        WHERE child.workspace_id IS NOT NULL
          AND project.workspace_id IS NOT NULL
          AND child.workspace_id <> project.workspace_id
        LIMIT 1
        """,
        "Cannot bind agent missions: Mission and Project use different Workspaces.",
    )
    _assert_none(
        conn,
        """
        SELECT child.id
        FROM agent_mission_tasks AS child
        JOIN agent_missions AS mission ON mission.id = child.mission_id
        WHERE child.workspace_id IS NOT NULL
          AND mission.workspace_id IS NOT NULL
          AND child.workspace_id <> mission.workspace_id
        LIMIT 1
        """,
        "Cannot bind agent mission tasks: Task and Mission use different Workspaces.",
    )
    _assert_none(
        conn,
        """
        SELECT child.id
        FROM agent_mission_tasks AS child
        JOIN projects AS project ON project.id = child.project_id
        WHERE child.workspace_id IS NOT NULL
          AND project.workspace_id IS NOT NULL
          AND child.workspace_id <> project.workspace_id
        LIMIT 1
        """,
        "Cannot bind agent mission tasks: Task and Project use different Workspaces.",
    )
    _assert_none(
        conn,
        """
        SELECT child.id
        FROM bom_items AS child
        JOIN proposal_plans AS plan ON plan.id = child.proposal_plan_id
        WHERE child.workspace_id IS NOT NULL
          AND plan.workspace_id IS NOT NULL
          AND child.workspace_id <> plan.workspace_id
        LIMIT 1
        """,
        "Cannot bind BOM items: BOM item and Proposal Plan use different Workspaces.",
    )


def upgrade() -> None:
    for schema, table, prefix in WORKSPACE_COLUMNS:
        _add_workspace_column(schema, table, prefix)

    conn = op.get_bind()
    _ensure_default_workspace(conn)
    _backfill_ai_children(conn)
    _backfill_marketing_children(conn)
    _backfill_field_children(conn)
    _backfill_delivery_children(conn)


def downgrade() -> None:
    for table in reversed(FIELD_NOT_NULL_TABLES):
        op.alter_column(table, "workspace_id", nullable=True)
    for schema, table, prefix in reversed(WORKSPACE_COLUMNS):
        _drop_workspace_column(schema, table, prefix)
