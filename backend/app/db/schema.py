from sqlalchemy import inspect, text

# System tables are stored with a ``sys_`` prefix. The mapping below also lets
# databases created before the prefix existed be upgraded in place, keeping data.
TABLE_RENAMES: dict[str, str] = {
    "users": "sys_users",
    "roles": "sys_roles",
    "menus": "sys_menus",
    "user_roles": "sys_user_roles",
    "role_menus": "sys_role_menus",
    "operation_logs": "sys_operation_logs",
    "scheduled_jobs": "sys_scheduled_jobs",
    "scheduled_job_logs": "sys_scheduled_job_logs",
}

# (old index, new index, prefixed table, columns, unique)
INDEX_RENAMES: list[tuple[str, str, str, tuple[str, ...], bool]] = [
    ("ix_users_username", "ix_sys_users_username", "sys_users", ("username",), True),
    ("ix_roles_code", "ix_sys_roles_code", "sys_roles", ("code",), True),
    ("ix_menus_parent_id", "ix_sys_menus_parent_id", "sys_menus", ("parent_id",), False),
    (
        "ix_operation_logs_user_id",
        "ix_sys_operation_logs_user_id",
        "sys_operation_logs",
        ("user_id",),
        False,
    ),
    (
        "ix_operation_logs_username",
        "ix_sys_operation_logs_username",
        "sys_operation_logs",
        ("username",),
        False,
    ),
    (
        "ix_operation_logs_created_at",
        "ix_sys_operation_logs_created_at",
        "sys_operation_logs",
        ("created_at",),
        False,
    ),
    (
        "ix_scheduled_jobs_job_key",
        "ix_sys_scheduled_jobs_job_key",
        "sys_scheduled_jobs",
        ("job_key",),
        True,
    ),
    (
        "ix_scheduled_job_logs_job_id",
        "ix_sys_scheduled_job_logs_job_id",
        "sys_scheduled_job_logs",
        ("job_id",),
        False,
    ),
    (
        "ix_scheduled_job_logs_started_at",
        "ix_sys_scheduled_job_logs_started_at",
        "sys_scheduled_job_logs",
        ("started_at",),
        False,
    ),
]


def ensure_table_prefixes(engine) -> None:
    """Rename legacy unprefixed system tables (and their indexes) to ``sys_*``.

    Idempotent: tables already renamed (or databases created from the current
    metadata) are left untouched. On SQLite the rename keeps rows and updates
    foreign keys; on PostgreSQL the same happens through ``ALTER TABLE``.
    """

    inspector = inspect(engine)
    existing = set(inspector.get_table_names())
    renames = [
        (old, new)
        for old, new in TABLE_RENAMES.items()
        if old in existing and new not in existing
    ]
    if renames:
        with engine.begin() as connection:
            for old, new in renames:
                connection.execute(text(f'ALTER TABLE "{old}" RENAME TO "{new}"'))
    _rename_indexes(engine)


def _rename_indexes(engine) -> None:
    inspector = inspect(engine)
    pending: list[tuple[str, str, str, tuple[str, ...], bool]] = []
    for old, new, table, columns, unique in INDEX_RENAMES:
        if not inspector.has_table(table):
            continue
        names = {index["name"] for index in inspector.get_indexes(table)}
        if old in names and new not in names:
            pending.append((old, new, table, columns, unique))
    if not pending:
        return
    dialect = engine.dialect.name
    with engine.begin() as connection:
        for old, new, table, columns, unique in pending:
            if dialect == "postgresql":
                connection.execute(text(f'ALTER INDEX "{old}" RENAME TO "{new}"'))
            else:
                connection.execute(text(f'DROP INDEX "{old}"'))
                unique_sql = "UNIQUE " if unique else ""
                column_sql = ", ".join(f'"{column}"' for column in columns)
                connection.execute(
                    text(f'CREATE {unique_sql}INDEX "{new}" ON "{table}" ({column_sql})')
                )


def ensure_user_columns(engine) -> None:
    inspector = inspect(engine)
    if not inspector.has_table("sys_users"):
        return
    names = {column["name"] for column in inspector.get_columns("sys_users")}
    statements: list[str] = []
    if "token_version" not in names:
        statements.append("ALTER TABLE sys_users ADD COLUMN token_version INTEGER NOT NULL DEFAULT 0")
    if "failed_login_count" not in names:
        statements.append("ALTER TABLE sys_users ADD COLUMN failed_login_count INTEGER NOT NULL DEFAULT 0")
    locked_type = "INTEGER" if engine.dialect.name == "sqlite" else "BIGINT"
    if "locked_until" not in names:
        statements.append(f"ALTER TABLE sys_users ADD COLUMN locked_until {locked_type}")
    if "totp_secret" not in names:
        statements.append("ALTER TABLE sys_users ADD COLUMN totp_secret VARCHAR(64)")
    if "totp_required" not in names:
        bool_type = "BOOLEAN" if engine.dialect.name != "sqlite" else "INTEGER"
        default = "FALSE" if engine.dialect.name != "sqlite" else "0"
        statements.append(
            f"ALTER TABLE sys_users ADD COLUMN totp_required {bool_type} NOT NULL DEFAULT {default}"
        )
    if "totp_enabled" not in names:
        bool_type = "BOOLEAN" if engine.dialect.name != "sqlite" else "INTEGER"
        default = "FALSE" if engine.dialect.name != "sqlite" else "0"
        statements.append(
            f"ALTER TABLE sys_users ADD COLUMN totp_enabled {bool_type} NOT NULL DEFAULT {default}"
        )
    if not statements:
        return
    with engine.begin() as connection:
        for statement in statements:
            connection.execute(text(statement))


def ensure_operation_log_columns(engine) -> None:
    inspector = inspect(engine)
    if not inspector.has_table("sys_operation_logs"):
        return
    names = {column["name"] for column in inspector.get_columns("sys_operation_logs")}
    statements: list[str] = []
    if "params" not in names:
        statements.append("ALTER TABLE sys_operation_logs ADD COLUMN params TEXT NOT NULL DEFAULT ''")
    if "response_body" not in names:
        statements.append(
            "ALTER TABLE sys_operation_logs ADD COLUMN response_body TEXT NOT NULL DEFAULT ''"
        )
    if "status_code" not in names:
        statements.append("ALTER TABLE sys_operation_logs ADD COLUMN status_code INTEGER")
    if not statements:
        return
    with engine.begin() as connection:
        for statement in statements:
            connection.execute(text(statement))
