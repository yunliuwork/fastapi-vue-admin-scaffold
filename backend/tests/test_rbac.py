from tests.helpers import find_menu


def test_user_without_permission_is_forbidden(client):
    admin = login(client)
    user_menu = find_menu(menu_tree(client, admin), "system:user:list")
    assert user_menu is not None
    role = client.post(
        "/api/v1/roles",
        headers=admin,
        json={"name": "只读", "code": "reader", "remark": "", "status": "active", "menu_ids": [user_menu["id"]]},
    )
    assert role.status_code == 200
    role_id = role.json()["data"]["id"]
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
    role = client.post(
        "/api/v1/roles",
        headers=admin,
        json={"name": "用户页", "code": "user_page", "remark": "", "status": "active", "menu_ids": [user_menu["id"]]},
    )
    role_id = role.json()["data"]["id"]
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
