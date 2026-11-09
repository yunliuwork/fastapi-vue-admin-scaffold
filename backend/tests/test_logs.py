def test_creating_a_user_is_written_to_the_operation_log(client):
    headers = login(client)
    created = client.post(
        "/api/v1/users",
        headers=headers,
        json={"username": "editor", "password": "secret12", "nickname": "编辑", "role_ids": []},
    )
    assert created.status_code == 200

    listed = client.get("/api/v1/operation-logs", headers=headers, params={"action": "新增用户"})

    assert listed.status_code == 200
    body = listed.json()["data"]
    assert body["total"] >= 1
    row = body["items"][0]
    assert row["username"] == "admin"
    assert row["action"] == "新增用户"
    assert row["target"] == "editor"
    assert row["ip"]
    assert row["status_code"] == 200
    assert "editor" in row["params"]
    assert "secret12" not in row["params"]
    assert "editor" in row["response"]
    assert isinstance(row["created_at"], int)
    assert len(str(row["created_at"])) == 13


def test_operation_log_can_be_filtered_by_operator(client):
    headers = login(client)
    matched = client.get("/api/v1/operation-logs", headers=headers, params={"username": "admin"})
    empty = client.get("/api/v1/operation-logs", headers=headers, params={"username": "nobody"})

    assert matched.status_code == 200
    assert matched.json()["data"]["total"] >= 1
    assert matched.json()["data"]["items"][0]["action"] == "登录"
    assert empty.json()["data"]["total"] == 0


def test_failed_login_keeps_status_and_hides_the_password(client):
    failed = client.post("/api/v1/auth/login", json={"username": "admin", "password": "wrong-pass"})
    assert failed.status_code == 401
    headers = login(client)

    listed = client.get("/api/v1/operation-logs", headers=headers, params={"action": "登录", "outcome": "failure"})

    assert listed.status_code == 200
    row = listed.json()["data"]["items"][0]
    assert row["username"] == "admin"
    assert row["status_code"] == 401
    assert "wrong-pass" not in row["params"]
    assert "***" in row["params"]
    assert "用户名或密码错误" in row["response"]
    token = headers["Authorization"].split(" ", 1)[1]
    success = client.get("/api/v1/operation-logs", headers=headers, params={"action": "登录", "outcome": "success"})
    assert token not in success.json()["data"]["items"][0]["response"]


def test_operation_log_requires_permission(client):
    from tests.helpers import create_role, find_menu

    admin = login(client)
    user_menu = find_menu(client.get("/api/v1/menus", headers=admin).json()["data"], "system:user:list")
    role = create_role(client, admin, name="只读", code="reader", menu_ids=[user_menu["id"]])
    role_id = role["id"]
    client.post(
        "/api/v1/users",
        headers=admin,
        json={"username": "reader", "password": "secret12", "nickname": "只读", "role_ids": [role_id]},
    )
    reader = login(client, "reader", "secret12")

    response = client.get("/api/v1/operation-logs", headers=reader)

    assert response.status_code == 403
    assert response.json()["message"] == "没有权限"


def login(client, username: str = "admin", password: str = "admin123") -> dict[str, str]:
    response = client.post("/api/v1/auth/login", json={"username": username, "password": password})
    assert response.status_code == 200, response.text
    token = response.json()["data"]["access_token"]
    return {"Authorization": f"Bearer {token}"}
