import json


def test_scheduled_jobs_are_listed_and_can_run(client):
    headers = login(client)
    listed = client.get("/api/v1/scheduled-jobs", headers=headers)
    assert listed.status_code == 200
    items = listed.json()["data"]["items"]
    assert len(items) >= 1
    job = next(item for item in items if item["job_key"] == "clear_expired_login_locks")
    assert job["trigger_label"]

    run = client.post(f"/api/v1/scheduled-jobs/{job['id']}/run", headers=headers)
    assert run.status_code == 200
    assert run.json()["data"]["status"] == "success"

    logs = client.get(f"/api/v1/scheduled-jobs/{job['id']}/logs", headers=headers)
    assert logs.status_code == 200
    assert logs.json()["data"]["total"] >= 1


def test_scheduled_job_update_syncs_trigger(client):
    headers = login(client)
    job = client.get("/api/v1/scheduled-jobs", headers=headers).json()["data"]["items"][0]
    updated = client.put(
        f"/api/v1/scheduled-jobs/{job['id']}",
        headers=headers,
        json={
            "name": job["name"],
            "trigger_type": "interval",
            "trigger_config": json.dumps({"hours": 2}),
            "params": job["params"],
            "enabled": True,
            "remark": job["remark"],
        },
    )
    assert updated.status_code == 200
    assert "每 2 小时" in updated.json()["data"]["trigger_label"]


def test_scheduled_job_requires_permission(client):
    from tests.helpers import find_menu

    admin = login(client)
    user_menu = find_menu(client.get("/api/v1/menus", headers=admin).json()["data"], "system:user:list")
    role = client.post(
        "/api/v1/roles",
        headers=admin,
        json={"name": "只读", "code": "reader2", "remark": "", "status": "active", "menu_ids": [user_menu["id"]]},
    )
    role_id = role.json()["data"]["id"]
    client.post(
        "/api/v1/users",
        headers=admin,
        json={"username": "reader2", "password": "secret12", "nickname": "只读", "role_ids": [role_id]},
    )
    reader = login(client, "reader2", "secret12")
    response = client.get("/api/v1/scheduled-jobs", headers=reader)
    assert response.status_code == 403


def login(client, username: str = "admin", password: str = "admin123") -> dict[str, str]:
    response = client.post("/api/v1/auth/login", json={"username": username, "password": password})
    assert response.status_code == 200, response.text
    token = response.json()["data"]["access_token"]
    return {"Authorization": f"Bearer {token}"}
