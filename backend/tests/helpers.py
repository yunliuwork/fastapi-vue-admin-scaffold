def find_menu(nodes: list[dict], permission: str) -> dict | None:
    for node in nodes:
        if node.get("permission") == permission:
            return node
        found = find_menu(node.get("children") or [], permission)
        if found is not None:
            return found
    return None
