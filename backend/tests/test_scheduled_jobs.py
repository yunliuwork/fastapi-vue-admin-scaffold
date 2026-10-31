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


def test_scheduled_job_status_switch(client):
    headers = login(client)
    job = client.get("/api/v1/scheduled-jobs", headers=headers).json()["data"]["items"][0]

    disabled = client.patch(
        f"/api/v1/scheduled-jobs/{job['id']}/status",
        headers=headers,
        json={"enabled": False},
    )
    assert disabled.status_code == 200
    assert disabled.json()["data"]["enabled"] is False

    manual = client.post(f"/api/v1/scheduled-jobs/{job['id']}/run", headers=headers)
    assert manual.status_code == 200, manual.text
    assert manual.json()["data"]["trigger_mode"] == "manual"
    assert manual.json()["data"]["status"] == "success"

    enabled = client.patch(
        f"/api/v1/scheduled-jobs/{job['id']}/status",
        headers=headers,
        json={"enabled": True},
    )
    assert enabled.status_code == 200
    assert enabled.json()["data"]["enabled"] is True


def test_scheduled_job_log_cleanup(client):
    headers = login(client)
    job = client.get("/api/v1/scheduled-jobs", headers=headers).json()["data"]["items"][0]
    client.post(f"/api/v1/scheduled-jobs/{job['id']}/run", headers=headers)
    client.post(f"/api/v1/scheduled-jobs/{job['id']}/run", headers=headers)

    stats = client.get("/api/v1/scheduled-jobs/logs/stats", headers=headers)
    assert stats.status_code == 200
    assert stats.json()["data"]["total"] >= 2
    assert stats.json()["data"]["older_than_7d"] == 0

    # 把最新一条日志改成 10 天前，验证按天清理
    from datetime import timedelta

    from sqlalchemy import select

    from app.db import session as db_session
    from app.models.scheduled_job import ScheduledJobLog
    from app.models.user import utcnow

    db = db_session.session_factory()
    row = db.scalars(select(ScheduledJobLog).order_by(ScheduledJobLog.id.desc())).first()
    row.started_at = utcnow() - timedelta(days=10)
    db.commit()
    db.close()

    stats = client.get("/api/v1/scheduled-jobs/logs/stats", headers=headers).json()["data"]
    assert stats["older_than_7d"] == 1
    assert stats["older_than_30d"] == 0

    cleaned = client.post("/api/v1/scheduled-jobs/logs/cleanup", headers=headers, json={"days": 7})
    assert cleaned.status_code == 200
    assert cleaned.json()["data"]["deleted"] == 1
    stats = client.get("/api/v1/scheduled-jobs/logs/stats", headers=headers).json()["data"]
    assert stats["older_than_7d"] == 0
    assert stats["total"] == 1

    cleared = client.post("/api/v1/scheduled-jobs/logs/cleanup", headers=headers, json={})
    assert cleared.status_code == 200
    assert cleared.json()["data"]["deleted"] == 1
    assert client.get("/api/v1/scheduled-jobs/logs/stats", headers=headers).json()["data"]["total"] == 0


def test_scheduled_job_requires_permission(client):
    from tests.helpers import create_role, find_menu

    admin = login(client)
    user_menu = find_menu(client.get("/api/v1/menus", headers=admin).json()["data"], "system:user:list")
    role = create_role(client, admin, name="只读", code="reader2", menu_ids=[user_menu["id"]])
    role_id = role["id"]
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
