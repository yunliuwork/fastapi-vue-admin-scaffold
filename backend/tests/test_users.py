def test_admin_can_create_and_list_users(client):
    headers = login(client)
    created = client.post(
        "/api/v1/users",
        headers=headers,
        json={"username": "editor", "password": "secret12", "nickname": "编辑", "role_ids": []},
    )

    assert created.status_code == 200
    assert created.json()["data"]["username"] == "editor"

    listed = client.get("/api/v1/users", headers=headers, params={"username": "edit", "page": 1, "page_size": 10})

    assert listed.status_code == 200
    body = listed.json()["data"]
    assert body["total"] == 1
    assert body["items"][0]["nickname"] == "编辑"
    assert "password" not in body["items"][0]
    assert "password_hash" not in body["items"][0]


def test_duplicate_username_is_rejected(client):
    headers = login(client)
    payload = {"username": "editor", "password": "secret12", "nickname": "编辑", "role_ids": []}
    assert client.post("/api/v1/users", headers=headers, json=payload).status_code == 200

    response = client.post("/api/v1/users", headers=headers, json=payload)

    assert response.status_code == 409
    assert response.json()["message"] == "用户名已存在"


def test_update_disable_and_reset_password(client):
    headers = login(client)
    created = client.post(
        "/api/v1/users",
        headers=headers,
        json={"username": "editor", "password": "secret12", "nickname": "编辑", "role_ids": []},
    )
    user_id = created.json()["data"]["id"]

    updated = client.put(
        f"/api/v1/users/{user_id}",
        headers=headers,
        json={"nickname": "内容编辑", "status": "active", "role_ids": []},
    )
    assert updated.status_code == 200
    assert updated.json()["data"]["nickname"] == "内容编辑"

    reset = client.post(
        f"/api/v1/users/{user_id}/reset-password",
        headers=headers,
        json={"password": "changed1"},
    )
    assert reset.status_code == 200

    old_login = client.post("/api/v1/auth/login", json={"username": "editor", "password": "secret12"})
    assert old_login.status_code == 401
    new_login = client.post("/api/v1/auth/login", json={"username": "editor", "password": "changed1"})
    assert new_login.status_code == 200

    disabled = client.patch(f"/api/v1/users/{user_id}/status", headers=headers, json={"status": "disabled"})
    assert disabled.status_code == 200
    assert disabled.json()["data"]["status"] == "disabled"


def test_cannot_disable_superuser(client):
    headers = login(client)
    profile = client.get("/api/v1/auth/me", headers=headers).json()["data"]

    response = client.patch(
        f"/api/v1/users/{profile['id']}/status",
        headers=headers,
        json={"status": "disabled"},
    )

    assert response.status_code == 400
    assert response.json()["message"] == "不能停用超级管理员"


def test_operator_cannot_change_superuser(client):
    from tests.helpers import create_role, find_menu

    admin = login(client)
    tree = client.get("/api/v1/menus", headers=admin).json()["data"]
    reset_menu = find_menu(tree, "system:user:reset-password")
    update_menu = find_menu(tree, "system:user:update")
    assert reset_menu is not None and update_menu is not None
    role = create_role(
        client,
        admin,
        name="账号维护",
        code="account_ops",
        menu_ids=[reset_menu["id"], update_menu["id"]],
    )
    role_id = role["id"]
    client.post(
        "/api/v1/users",
        headers=admin,
        json={"username": "clerk", "password": "secret12", "nickname": "维护", "role_ids": [role_id]},
    )
    clerk = client.post("/api/v1/auth/login", json={"username": "clerk", "password": "secret12"})
    clerk_headers = {"Authorization": f"Bearer {clerk.json()['data']['access_token']}"}
    admin_id = client.get("/api/v1/auth/me", headers=admin).json()["data"]["id"]

    reset = client.post(
        f"/api/v1/users/{admin_id}/reset-password",
        headers=clerk_headers,
        json={"password": "changed1"},
    )
    updated = client.put(
        f"/api/v1/users/{admin_id}",
        headers=clerk_headers,
        json={"nickname": "被改", "status": "active", "role_ids": []},
    )

    assert reset.status_code == 403
    assert reset.json()["message"] == "不能修改超级管理员"
    assert updated.status_code == 403
    assert client.post("/api/v1/auth/login", json={"username": "admin", "password": "admin123"}).status_code == 200


def login(client) -> dict[str, str]:
    response = client.post("/api/v1/auth/login", json={"username": "admin", "password": "admin123"})
    token = response.json()["data"]["access_token"]
    return {"Authorization": f"Bearer {token}"}
