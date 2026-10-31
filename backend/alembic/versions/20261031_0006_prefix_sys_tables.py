"""prefix system tables with sys_

Renames the scaffold's system tables in place so existing rows are preserved.
Idempotent: if the tables were already renamed by application startup, only
the revision is recorded.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20261031_0006"
down_revision: str | None = "20261031_0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

TABLE_RENAMES: list[tuple[str, str]] = [
    ("users", "sys_users"),
    ("roles", "sys_roles"),
    ("menus", "sys_menus"),
    ("user_roles", "sys_user_roles"),
    ("role_menus", "sys_role_menus"),
    ("operation_logs", "sys_operation_logs"),
    ("scheduled_jobs", "sys_scheduled_jobs"),
    ("scheduled_job_logs", "sys_scheduled_job_logs"),
]

# (unprefixed index, prefixed index, unprefixed table, prefixed table, columns, unique)
INDEX_RENAMES: list[tuple[str, str, str, str, tuple[str, ...], bool]] = [
    ("ix_users_username", "ix_sys_users_username", "users", "sys_users", ("username",), True),
    ("ix_roles_code", "ix_sys_roles_code", "roles", "sys_roles", ("code",), True),
    ("ix_menus_parent_id", "ix_sys_menus_parent_id", "menus", "sys_menus", ("parent_id",), False),
    (
        "ix_operation_logs_user_id",
        "ix_sys_operation_logs_user_id",
        "operation_logs",
        "sys_operation_logs",
        ("user_id",),
        False,
    ),
    (
        "ix_operation_logs_username",
        "ix_sys_operation_logs_username",
        "operation_logs",
        "sys_operation_logs",
        ("username",),
        False,
    ),
    (
        "ix_operation_logs_created_at",
        "ix_sys_operation_logs_created_at",
        "operation_logs",
        "sys_operation_logs",
        ("created_at",),
        False,
    ),
    (
        "ix_scheduled_jobs_job_key",
        "ix_sys_scheduled_jobs_job_key",
        "scheduled_jobs",
        "sys_scheduled_jobs",
        ("job_key",),
        True,
    ),
    (
        "ix_scheduled_job_logs_job_id",
        "ix_sys_scheduled_job_logs_job_id",
        "scheduled_job_logs",
        "sys_scheduled_job_logs",
        ("job_id",),
        False,
    ),
    (
        "ix_scheduled_job_logs_started_at",
        "ix_sys_scheduled_job_logs_started_at",
        "scheduled_job_logs",
        "sys_scheduled_job_logs",
        ("started_at",),
        False,
    ),
]


def _rename_tables(*, upgrade: bool) -> None:
    existing = set(sa.inspect(op.get_bind()).get_table_names())
    pairs = TABLE_RENAMES if upgrade else [(new, old) for old, new in TABLE_RENAMES]
    for source, target in pairs:
        if source in existing and target not in existing:
            op.rename_table(source, target)


def _rename_indexes(*, upgrade: bool) -> None:
    bind = op.get_bind()
    dialect = bind.dialect.name
    for old_idx, new_idx, old_table, new_table, columns, unique in INDEX_RENAMES:
        source_table = new_table if upgrade else old_table
        source_idx, target_idx = (old_idx, new_idx) if upgrade else (new_idx, old_idx)
        inspector = sa.inspect(bind)
        if not inspector.has_table(source_table):
            continue
        names = {index["name"] for index in inspector.get_indexes(source_table)}
        if source_idx not in names or target_idx in names:
            continue
        if dialect == "postgresql":
            op.execute(f'ALTER INDEX "{source_idx}" RENAME TO "{target_idx}"')
        else:
            op.execute(f'DROP INDEX "{source_idx}"')
            unique_sql = "UNIQUE " if unique else ""
            column_sql = ", ".join(f'"{column}"' for column in columns)
            op.execute(
                f'CREATE {unique_sql}INDEX "{target_idx}" ON "{source_table}" ({column_sql})'
            )


def upgrade() -> None:
    _rename_tables(upgrade=True)
    _rename_indexes(upgrade=True)


def downgrade() -> None:
    _rename_tables(upgrade=False)
    _rename_indexes(upgrade=False)
