"""Tests for Task Manager API, configuration, and business logic."""

from datetime import date, timedelta

from fastapi.testclient import TestClient

from task_manager.config import Settings


def test_default_settings() -> None:
    """Verify default configuration settings."""
    settings = Settings()
    assert settings.environment in {"development", "test", "production"}
    assert settings.log_level in {"DEBUG", "INFO", "WARNING", "ERROR"}


def test_health_endpoint(client: TestClient) -> None:
    """Test GET /health endpoint returns 200 and ok status."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "environment" in data


def test_user_and_task_lifecycle(client: TestClient) -> None:
    """Test creating user, creating tasks, assigning, filtering, overdue, and stats."""
    # 1. Create a user
    user_resp = client.post(
        "/users",
        json={"username": "oleksandr", "email": "oleksandr@example.com"},
    )
    assert user_resp.status_code == 201
    user_id = user_resp.json()["id"]

    # 2. Create an overdue task (yesterday)
    yesterday = (date.today() - timedelta(days=1)).isoformat()
    task1_resp = client.post(
        "/tasks",
        json={
            "title": "Fix Docker pipeline",
            "description": "Configure multi-stage build",
            "priority": "high",
            "status": "todo",
            "due_date": yesterday,
        },
    )
    assert task1_resp.status_code == 201
    task1_id = task1_resp.json()["id"]

    # 3. Create a second task assigned to user
    tomorrow = (date.today() + timedelta(days=1)).isoformat()
    task2_resp = client.post(
        "/tasks",
        json={
            "title": "Write documentation",
            "description": "Update README.md for release",
            "priority": "medium",
            "status": "in_progress",
            "due_date": tomorrow,
            "user_id": user_id,
        },
    )
    assert task2_resp.status_code == 201
    task2_id = task2_resp.json()["id"]

    # 4. Assign task 1 to user
    assign_resp = client.patch(
        f"/tasks/{task1_id}/assign", json={"user_id": user_id}
    )
    assert assign_resp.status_code == 200
    assert assign_resp.json()["user_id"] == user_id

    # 5. Check user tasks (/users/{id}/tasks)
    user_tasks_resp = client.get(f"/users/{user_id}/tasks")
    assert user_tasks_resp.status_code == 200
    assert len(user_tasks_resp.json()) == 2

    # 6. Check overdue tasks (/tasks/overdue)
    overdue_resp = client.get("/tasks/overdue")
    assert overdue_resp.status_code == 200
    overdue_list = overdue_resp.json()
    assert len(overdue_list) == 1
    assert overdue_list[0]["id"] == task1_id

    # 7. Complete task 2 (/tasks/{id}/status)
    status_resp = client.patch(
        f"/tasks/{task2_id}/status", json={"status": "completed"}
    )
    assert status_resp.status_code == 200
    assert status_resp.json()["status"] == "completed"

    # 8. Filter completed vs incomplete & search
    completed_tasks = client.get("/tasks?completed=true").json()
    assert len(completed_tasks) == 1
    incomplete_tasks = client.get("/tasks?completed=false").json()
    assert len(incomplete_tasks) == 1

    search_tasks = client.get("/tasks?search=Docker").json()
    assert len(search_tasks) == 1
    assert search_tasks[0]["id"] == task1_id

    # 9. Verify statistics (/statistics)
    stats_resp = client.get("/statistics")
    assert stats_resp.status_code == 200
    stats = stats_resp.json()
    assert stats["total"] == 2
    assert stats["completed"] == 1
    assert stats["incomplete"] == 1
    assert stats["overdue"] == 1
    assert stats["by_priority"]["high"] == 1
    assert stats["by_priority"]["medium"] == 1
