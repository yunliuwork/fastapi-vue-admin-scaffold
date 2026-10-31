def test_login_success(client):
    response = client.post("/api/v1/auth/login", json={"username": "admin", "password": "admin123"})

    assert response.status_code == 200
    body = response.json()
    assert body["code"] == 0
    assert body["data"]["token_type"] == "bearer"
    assert body["data"]["access_token"]
    assert body["data"]["refresh_token"]


def test_login_wrong_password(client):
    response = client.post("/api/v1/auth/login", json={"username": "admin", "password": "wrong-password"})

    assert response.status_code == 401
    assert response.json() == {"code": 401, "message": "用户名或密码错误", "data": None}


def test_login_missing_password_uses_envelope(client):
    response = client.post("/api/v1/auth/login", json={"username": "admin"})

    assert response.status_code == 422
    body = response.json()
    assert body["code"] == 422
    assert body["data"] is None
    assert body["message"]


def test_me_requires_access_token(client):
    response = client.get("/api/v1/auth/me")

    assert response.status_code == 401
    assert response.json()["message"] == "未登录或登录已过期"


def test_me_returns_seed_admin(client):
    headers = login_headers(client)
    response = client.get("/api/v1/auth/me", headers=headers)

    assert response.status_code == 200
    profile = response.json()["data"]
    assert profile["username"] == "admin"
    assert profile["nickname"] == "超级管理员"
    assert profile["is_superuser"] is True
    assert profile["roles"][0]["code"] == "super_admin"


def test_refresh_issues_new_access_token(client):
    login_response = client.post("/api/v1/auth/login", json={"username": "admin", "password": "admin123"})
    refresh_token = login_response.json()["data"]["refresh_token"]

    response = client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})

    assert response.status_code == 200
    access_token = response.json()["data"]["access_token"]
    me = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {access_token}"})
    assert me.status_code == 200
    assert me.json()["data"]["username"] == "admin"


def test_refresh_token_cannot_call_api(client):
    login_response = client.post("/api/v1/auth/login", json={"username": "admin", "password": "admin123"})
    refresh_token = login_response.json()["data"]["refresh_token"]

    response = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {refresh_token}"})

    assert response.status_code == 401
    assert response.json()["message"] == "未登录或登录已过期"


def test_logout_invalidates_existing_tokens(client):
    login_response = client.post("/api/v1/auth/login", json={"username": "admin", "password": "admin123"})
    tokens = login_response.json()["data"]
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}

    logout = client.post("/api/v1/auth/logout", headers=headers)

    assert logout.status_code == 200
    me = client.get("/api/v1/auth/me", headers=headers)
    refreshed = client.post("/api/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    assert me.status_code == 401
    assert refreshed.status_code == 401


def test_change_password_replaces_the_session(client):
    headers = login_headers(client)
    wrong = client.put(
        "/api/v1/auth/password",
        headers=headers,
        json={"old_password": "nope", "new_password": "admin456"},
    )
    assert wrong.status_code == 400
    assert wrong.json()["message"] == "原密码不正确"

    changed = client.put(
        "/api/v1/auth/password",
        headers=headers,
        json={"old_password": "admin123", "new_password": "admin456"},
    )
    assert changed.status_code == 200
    next_headers = {"Authorization": f"Bearer {changed.json()['data']['access_token']}"}
    assert client.get("/api/v1/auth/me", headers=headers).status_code == 401
    assert client.get("/api/v1/auth/me", headers=next_headers).status_code == 200
    assert client.post("/api/v1/auth/login", json={"username": "admin", "password": "admin456"}).status_code == 200


def test_login_locks_after_repeated_failures(client):
    for _ in range(5):
        failed = client.post("/api/v1/auth/login", json={"username": "admin", "password": "wrong-password"})
        assert failed.status_code == 401

    locked = client.post("/api/v1/auth/login", json={"username": "admin", "password": "admin123"})

    assert locked.status_code == 429
    assert locked.json()["message"] == "尝试次数过多，请稍后再试"


def test_disabled_user_cannot_login(client):
    headers = login_headers(client)
    created = client.post(
        "/api/v1/users",
        headers=headers,
        json={"username": "frozen", "password": "secret12", "nickname": "冻结", "role_ids": []},
    )
    user_id = created.json()["data"]["id"]
    disabled = client.patch(f"/api/v1/users/{user_id}/status", headers=headers, json={"status": "disabled"})
    assert disabled.status_code == 200

    response = client.post("/api/v1/auth/login", json={"username": "frozen", "password": "secret12"})

    assert response.status_code == 403
    assert response.json()["message"] == "账号已停用"


def login_headers(client) -> dict[str, str]:
    response = client.post("/api/v1/auth/login", json={"username": "admin", "password": "admin123"})
    token = response.json()["data"]["access_token"]
    return {"Authorization": f"Bearer {token}"}
