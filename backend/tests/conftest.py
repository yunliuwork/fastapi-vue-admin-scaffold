import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import create_app


@pytest.fixture
def client(tmp_path):
    database = (tmp_path / "test.db").as_posix()
    settings = Settings(
        database_url=f"sqlite:///{database}",
        jwt_secret="test-secret-key-with-extra-length-32bxx",
        seed_on_startup=True,
        auto_create_tables=True,
        cors_origins="http://localhost:5173",
    )
    app = create_app(settings)
    with TestClient(app) as test_client:
        yield test_client
