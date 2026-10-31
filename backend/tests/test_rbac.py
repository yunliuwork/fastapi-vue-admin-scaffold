from tests.helpers import create_role, find_menu


def test_user_without_permission_is_forbidden(client):
    admin = login(client)
    user_menu = find_menu(menu_tree(client, admin), "system:user:list")
    assert user_menu is not None
    role = create_role(client, admin, name="只读", code="reader", menu_ids=[user_menu["id"]])
    role_id = role["id"]
    created = client.post(
        "/api/v1/users",
        headers=admin,
        json={"username": "reader", "password": "secret12", "nickname": "只读", "role_ids": [role_id]},
    )
    assert created.status_code == 200
    reader = login(client, "reader", "secret12")

    allowed = client.get("/api/v1/users", headers=reader)
    denied = client.post(
        "/api/v1/users",
        headers=reader,
        json={"username": "other", "password": "secret12", "nickname": "其他", "role_ids": []},
    )

    assert allowed.status_code == 200
    assert denied.status_code == 403
    assert denied.json()["message"] == "没有权限"


def test_menu_tree_includes_ancestor_of_assigned_page(client):
    admin = login(client)
    user_menu = find_menu(menu_tree(client, admin), "system:user:list")
    role = create_role(client, admin, name="用户页", code="user_page", menu_ids=[user_menu["id"]])
    role_id = role["id"]
    client.post(
        "/api/v1/users",
        headers=admin,
        json={"username": "pageuser", "password": "secret12", "nickname": "页面", "role_ids": [role_id]},
    )
    headers = login(client, "pageuser", "secret12")

    response = client.get("/api/v1/auth/menus", headers=headers)

    assert response.status_code == 200
    data = response.json()["data"]
    names = [node["name"] for node in data["menus"]]
    assert "系统管理" in names
    system_node = next(node for node in data["menus"] if node["name"] == "系统管理")
    child_names = [node["name"] for node in system_node["children"]]
    assert child_names == ["用户管理"]
    assert "system:user:list" in data["permissions"]
    assert "system:user:create" not in data["permissions"]
    assert "system:role:list" not in data["permissions"]


def test_role_status_switch_and_menu_assignment(client):
    admin = login(client)
    user_menu = find_menu(menu_tree(client, admin), "system:user:list")
    assert user_menu is not None

    role = client.post(
        "/api/v1/roles",
        headers=admin,
        json={"name": "临时角色", "code": "temp_role", "remark": ""},
    )
    assert role.status_code == 200
    data = role.json()["data"]
    assert data["status"] == "active"
    assert data["menu_ids"] == []
    role_id = data["id"]

    assigned = client.put(
        f"/api/v1/roles/{role_id}/menus",
        headers=admin,
        json={"menu_ids": [user_menu["id"]]},
    )
    assert assigned.status_code == 200
    assert assigned.json()["data"]["menu_ids"] == [user_menu["id"]]

    disabled = client.patch(
        f"/api/v1/roles/{role_id}/status",
        headers=admin,
        json={"status": "disabled"},
    )
    assert disabled.status_code == 200
    assert disabled.json()["data"]["status"] == "disabled"

    client.post(
        "/api/v1/users",
        headers=admin,
        json={"username": "tempuser", "password": "secret12", "nickname": "临时", "role_ids": [role_id]},
    )
    temp_headers = login(client, "tempuser", "secret12")
    assert client.get("/api/v1/users", headers=temp_headers).status_code == 403

    roles = client.get("/api/v1/roles", headers=admin).json()["data"]["items"]
    super_role = next(item for item in roles if item["code"] == "super_admin")
    blocked = client.patch(
        f"/api/v1/roles/{super_role['id']}/status",
        headers=admin,
        json={"status": "disabled"},
    )
    assert blocked.status_code == 400
    assert blocked.json()["message"] == "不能停用超级管理员角色"


def test_delete_role_with_menus_and_bound_user(client):
    admin = login(client)
    user_menu = find_menu(menu_tree(client, admin), "system:user:list")
    role = create_role(client, admin, name="待删除", code="to_delete", menu_ids=[user_menu["id"]])
    created_user = client.post(
        "/api/v1/users",
        headers=admin,
        json={"username": "deltest", "password": "secret12", "nickname": "删除测试", "role_ids": [role["id"]]},
    )
    assert created_user.status_code == 200

    removed = client.delete(f"/api/v1/roles/{role['id']}", headers=admin)
    assert removed.status_code == 200, removed.text

    roles = client.get("/api/v1/roles", headers=admin).json()["data"]["items"]
    assert all(item["code"] != "to_delete" for item in roles)
    users = client.get("/api/v1/users?page=1&page_size=10", headers=admin).json()["data"]["items"]
    still_there = next(item for item in users if item["username"] == "deltest")
    assert still_there["roles"] == []


def test_delete_menu_with_children_is_rejected(client):
    admin = login(client)
    parent = client.post(
        "/api/v1/menus",
        headers=admin,
        json={
            "parent_id": None,
            "name": "临时目录",
            "menu_type": "directory",
            "path": "/temp",
            "component": "",
            "permission": "",
            "icon": "",
            "sort": 50,
            "visible": True,
            "status": "active",
        },
    )
    parent_id = parent.json()["data"]["id"]
    child = client.post(
        "/api/v1/menus",
        headers=admin,
        json={
            "parent_id": parent_id,
            "name": "临时页面",
            "menu_type": "menu",
            "path": "/temp/page",
            "component": "temp/index",
            "permission": "temp:page:list",
            "icon": "",
            "sort": 0,
            "visible": True,
            "status": "active",
        },
    )
    assert child.status_code == 200

    blocked = client.delete(f"/api/v1/menus/{parent_id}", headers=admin)
    assert blocked.status_code == 400
    assert blocked.json()["message"] == "请先删除子菜单"

    assert client.delete(f"/api/v1/menus/{child.json()['data']['id']}", headers=admin).status_code == 200
    assert client.delete(f"/api/v1/menus/{parent_id}", headers=admin).status_code == 200


def login(client, username: str = "admin", password: str = "admin123") -> dict[str, str]:
    response = client.post("/api/v1/auth/login", json={"username": username, "password": password})
    assert response.status_code == 200, response.text
    token = response.json()["data"]["access_token"]
    return {"Authorization": f"Bearer {token}"}


def menu_tree(client, headers: dict[str, str]) -> list[dict]:
    response = client.get("/api/v1/menus", headers=headers)
    assert response.status_code == 200, response.text
    return response.json()["data"]
