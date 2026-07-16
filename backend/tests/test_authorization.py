import pytest

from app.models.models import Task, TaskStatusEnum


TEST_PASSWORD = "StrongPass123!"


def register_and_login(client, *, name: str, email: str) -> dict:
    register_response = client.post("/api/register", json={
        "name": name,
        "email": email,
        "grade": "高一",
        "password": TEST_PASSWORD,
    })
    assert register_response.status_code == 201

    login_response = client.post("/api/login", json={
        "email": email,
        "password": TEST_PASSWORD,
    })
    assert login_response.status_code == 200
    token = login_response.json()["data"]["access_token"]
    student = login_response.json()["data"]["student"]
    return {
        "student": student,
        "headers": {"Authorization": f"Bearer {token}"},
    }


@pytest.mark.parametrize(
    ("method", "path", "json"),
    [
        ("post", "/api/tasks", {
            "student_email": "anyone@example.com",
            "description": "不应创建的任务",
        }),
        ("post", "/api/task-complete", {"task_id": 1}),
        ("get", "/api/students/anyone@example.com", None),
        ("get", "/api/tasks/1", None),
        ("post", "/api/chat", {
            "messages": [{"role": "user", "content": "你好"}],
            "student_name": "伪造姓名",
        }),
        ("post", "/api/chat/extract-task", {
            "student_email": "anyone@example.com",
            "messages": [{"role": "user", "content": "生成任务"}],
        }),
        ("get", "/api/deerflow/status", None),
        ("get", "/api/deerflow/skills", None),
        ("put", "/api/deerflow/skills/search", {"enabled": True}),
        ("get", "/api/deerflow/models", None),
    ],
)
def test_student_business_endpoints_require_token(client, method, path, json):
    response = client.request(method, path, json=json)

    assert response.status_code == 401


def test_student_business_endpoint_rejects_invalid_token(client):
    response = client.post(
        "/api/chat",
        headers={"Authorization": "Bearer invalid-token"},
        json={"messages": [{"role": "user", "content": "你好"}]},
    )

    assert response.status_code == 401


def test_student_cannot_read_or_complete_another_students_task(client, db_session):
    owner = register_and_login(client, name="任务所有者", email="owner@example.com")
    attacker = register_and_login(client, name="越权学生", email="attacker@example.com")
    create_response = client.post(
        "/api/tasks",
        headers=owner["headers"],
        json={
            "student_email": "owner@example.com",
            "description": "所有者的任务",
        },
    )
    assert create_response.status_code == 201
    task_id = create_response.json()["data"]["task"]["id"]

    read_response = client.get(f"/api/tasks/{task_id}", headers=attacker["headers"])
    complete_response = client.post(
        "/api/task-complete",
        headers=attacker["headers"],
        json={"task_id": task_id, "feedback": "伪造完成"},
    )

    assert read_response.status_code == 404
    assert complete_response.status_code == 404
    db_session.expire_all()
    task = db_session.query(Task).filter(Task.id == task_id).one()
    assert task.status == TaskStatusEnum.IN_PROGRESS
    assert task.feedback is None


def test_student_cannot_read_another_student_by_email(client):
    owner = register_and_login(client, name="当前学生", email="current@example.com")
    register_and_login(client, name="其他学生", email="other@example.com")

    response = client.get(
        "/api/students/other@example.com",
        headers=owner["headers"],
    )

    assert response.status_code == 404


def test_task_creation_ignores_forged_identity_fields(client):
    current = register_and_login(client, name="当前学生", email="current@example.com")
    other = register_and_login(client, name="其他学生", email="other@example.com")

    response = client.post(
        "/api/tasks",
        headers=current["headers"],
        json={
            "student_email": "other@example.com",
            "student_id": other["student"]["id"],
            "description": "应属于当前学生",
        },
    )

    assert response.status_code == 201
    assert response.json()["data"]["task"]["student_id"] == current["student"]["id"]
    assert response.json()["data"]["task"]["student_id"] != other["student"]["id"]


def test_chat_ignores_forged_student_name(client, monkeypatch):
    current = register_and_login(client, name="真实姓名", email="current@example.com")
    called_with = {}

    async def fake_chat(messages, student_name):
        called_with["student_name"] = student_name
        return {"reply": "测试回复", "mode": "mock"}

    monkeypatch.setattr("app.api.routes.deerflow_service.chat", fake_chat)

    response = client.post(
        "/api/chat",
        headers=current["headers"],
        json={
            "messages": [{"role": "user", "content": "你好"}],
            "student_name": "伪造姓名",
        },
    )

    assert response.status_code == 200
    assert called_with["student_name"] == "真实姓名"


def test_extract_task_ignores_forged_identity_fields(client, monkeypatch):
    current = register_and_login(client, name="当前学生", email="current@example.com")
    other = register_and_login(client, name="其他学生", email="other@example.com")

    async def fake_extract_task(messages, student_name):
        assert student_name == "当前学生"
        return {
            "description": "属于当前学生的任务",
            "estimated_minutes": 10,
            "growth_points": 10,
            "topic_tags": ["身份边界"],
        }

    monkeypatch.setattr(
        "app.api.routes.deerflow_service.extract_task",
        fake_extract_task,
    )

    response = client.post(
        "/api/chat/extract-task",
        headers=current["headers"],
        json={
            "student_email": "other@example.com",
            "student_id": other["student"]["id"],
            "messages": [{"role": "user", "content": "生成任务"}],
        },
    )

    assert response.status_code == 201
    assert response.json()["data"]["task"]["student_id"] == current["student"]["id"]
    assert response.json()["data"]["task"]["student_id"] != other["student"]["id"]


@pytest.mark.parametrize(
    ("method", "path", "json"),
    [
        ("get", "/api/deerflow/status", None),
        ("get", "/api/deerflow/skills", None),
        ("put", "/api/deerflow/skills/search", {"enabled": True}),
        ("get", "/api/deerflow/models", None),
    ],
)
def test_student_cannot_access_deerflow_control_endpoints(
    client,
    method,
    path,
    json,
):
    current = register_and_login(client, name="普通学生", email="student@example.com")

    response = client.request(method, path, headers=current["headers"], json=json)

    assert response.status_code == 403
