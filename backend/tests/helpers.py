def find_menu(nodes: list[dict], permission: str) -> dict | None:
    for node in nodes:
        if node.get("permission") == permission:
            return node
        found = find_menu(node.get("children") or [], permission)
        if found is not None:
            return found
    return None


def create_role(client, headers: dict[str, str], *, name: str, code: str, menu_ids: list[int], remark: str = "") -> dict:
    """建角色（只写名称/编码/备注），再单独分配菜单，与页面上的两步操作一致。"""
    role = client.post(
        "/api/v1/roles",
        headers=headers,
        json={"name": name, "code": code, "remark": remark},
    )
    assert role.status_code == 200, role.text
    created = role.json()["data"]
    if not menu_ids:
        return created
    assigned = client.put(
        f"/api/v1/roles/{created['id']}/menus",
        headers=headers,
        json={"menu_ids": menu_ids},
    )
    assert assigned.status_code == 200, assigned.text
    return assigned.json()["data"]
