from fastapi.testclient import TestClient
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.security import hash_password
from app.db.base import Base
from app.db.schema import TABLE_RENAMES, ensure_table_prefixes
from app.main import create_app
from app.models import (  # noqa: F401
    Menu,
    OperationLog,
    Role,
    ScheduledJob,
    ScheduledJobLog,
    User,
)


def test_ensure_table_prefixes_preserves_rows_and_renames_indexes(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'legacy.db'}")
    with engine.begin() as connection:
        connection.execute(
            text("CREATE TABLE users (id INTEGER PRIMARY KEY, username VARCHAR(64) NOT NULL)")
        )
        connection.execute(text("CREATE UNIQUE INDEX ix_users_username ON users (username)"))
        connection.execute(text("CREATE TABLE roles (id INTEGER PRIMARY KEY, code VARCHAR(64) NOT NULL)"))
        connection.execute(
            text(
                "CREATE TABLE user_roles ("
                "user_id INTEGER NOT NULL, role_id INTEGER NOT NULL, "
                "PRIMARY KEY (user_id, role_id), "
                "FOREIGN KEY(user_id) REFERENCES users (id), "
                "FOREIGN KEY(role_id) REFERENCES roles (id))"
            )
        )
        connection.execute(text("INSERT INTO users (id, username) VALUES (1, 'legacy')"))

    ensure_table_prefixes(engine)
    ensure_table_prefixes(engine)

    inspector = inspect(engine)
    tables = set(inspector.get_table_names())
    assert {"sys_users", "sys_roles", "sys_user_roles"} <= tables
    assert not {"users", "roles", "user_roles"} & tables

    with engine.connect() as connection:
        assert connection.execute(text("SELECT username FROM sys_users")).scalar_one() == "legacy"
        foreign_tables = {
            row[2] for row in connection.execute(text("PRAGMA foreign_key_list(sys_user_roles)"))
        }
    assert foreign_tables == {"sys_users", "sys_roles"}

    index_names = {index["name"] for index in inspector.get_indexes("sys_users")}
    assert "ix_sys_users_username" in index_names
    assert "ix_users_username" not in index_names


def test_startup_renames_legacy_tables_and_keeps_logins_working(tmp_path):
    database = tmp_path / "legacy-app.db"
    engine = create_engine(f"sqlite:///{database}")
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        db.add(
            User(
                username="legacy",
                password_hash=hash_password("legacy-pass"),
                nickname="Legacy",
                status="active",
                is_superuser=True,
            )
        )
        db.commit()
    with engine.begin() as connection:
        for old, new in TABLE_RENAMES.items():
            connection.execute(text(f'ALTER TABLE "{new}" RENAME TO "{old}"'))
    engine.dispose()

    settings = Settings(
        database_url=f"sqlite:///{database}",
        jwt_secret="test-secret-key-with-extra-length-32bxx",
        seed_on_startup=True,
        auto_create_tables=True,
        cors_origins="http://localhost:5174",
    )
    with TestClient(create_app(settings)) as client:
        response = client.post(
            "/api/v1/auth/login",
            json={"username": "legacy", "password": "legacy-pass"},
        )
    assert response.status_code == 200, response.text
    assert response.json()["data"]["login_step"] == "complete"

    tables = set(inspect(create_engine(f"sqlite:///{database}")).get_table_names())
    assert "sys_users" in tables
    assert "users" not in tables
