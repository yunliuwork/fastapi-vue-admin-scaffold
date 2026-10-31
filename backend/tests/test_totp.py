import pyotp

from app.core.config import Settings
from app.main import create_app


def test_login_without_totp_when_user_not_required(client):
    response = client.post("/api/v1/auth/login", json={"username": "admin", "password": "admin123"})
    assert response.status_code == 200
    assert response.json()["data"]["login_step"] == "complete"


def test_totp_login_flow(tmp_path):
    database = (tmp_path / "totp.db").as_posix()
    settings = Settings(
        database_url=f"sqlite:///{database}",
        jwt_secret="test-secret-key-with-extra-length-32bxx",
        seed_on_startup=True,
        auto_create_tables=True,
    )
    app = create_app(settings)
    from fastapi.testclient import TestClient

    with TestClient(app) as client:
        headers = _login_headers(client)
        me = client.get("/api/v1/auth/me", headers=headers).json()["data"]
        role_ids = [role["id"] for role in me["roles"]]
        updated = client.put(
            f"/api/v1/users/{me['id']}",
            headers=headers,
            json={
                "nickname": me["nickname"],
                "status": "active",
                "role_ids": role_ids,
                "totp_required": True,
            },
        )
        assert updated.status_code == 200

        bind_step = client.post("/api/v1/auth/login", json={"username": "admin", "password": "admin123"})
        assert bind_step.status_code == 200
        bind_body = bind_step.json()["data"]
        assert bind_body["login_step"] == "totp_bind"
        assert bind_body["otpauth_url"]
        secret = bind_body["secret"]
        pre_auth = bind_body["pre_auth_token"]

        bound = client.post(
            "/api/v1/auth/login/totp-bind",
            json={"pre_auth_token": pre_auth, "totp_code": pyotp.TOTP(secret).now()},
        )
        assert bound.status_code == 200
        assert bound.json()["data"]["access_token"]

        verify_step = client.post("/api/v1/auth/login", json={"username": "admin", "password": "admin123"})
        assert verify_step.json()["data"]["login_step"] == "totp_verify"
        pre_auth = verify_step.json()["data"]["pre_auth_token"]

        missing = client.post(
            "/api/v1/auth/login/totp-verify",
            json={"pre_auth_token": pre_auth, "totp_code": "000000"},
        )
        assert missing.status_code == 401

        ok = client.post(
            "/api/v1/auth/login/totp-verify",
            json={"pre_auth_token": pre_auth, "totp_code": pyotp.TOTP(secret).now()},
        )
        assert ok.status_code == 200
        assert ok.json()["data"]["login_step"] == "complete"


def _login_headers(client) -> dict[str, str]:
    response = client.post("/api/v1/auth/login", json={"username": "admin", "password": "admin123"})
    token = response.json()["data"]["access_token"]
    return {"Authorization": f"Bearer {token}"}
