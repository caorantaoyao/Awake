import importlib
import importlib.util

import pytest
from sqlalchemy import create_engine, text

from app.models.models import GradeEnum as ModelGradeEnum
from app.models.models import Student
from app.services import auth_service


TEST_PASSWORD = "StrongPass123!"
LEGACY_PASSWORD = "LegacyPass123!"


class TestHealthCheck:
    def test_health_endpoint(self, client):
        response = client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data


class TestRegisterAPI:
    def test_register_success(self, client, db_session):
        response = client.post("/api/register", json={
            "name": "张三",
            "email": "zhangsan@example.com",
            "grade": "高一",
            "password": TEST_PASSWORD
        })
        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        assert "student" in data["data"]
        assert data["data"]["student"]["name"] == "张三"
        assert data["data"]["student"]["email"] == "zhangsan@example.com"
        assert data["data"]["student"]["grade"] == "高一"
        assert "password" not in data["data"]["student"]
        assert "password_hash" not in data["data"]["student"]

        student = db_session.query(Student).filter(Student.email == "zhangsan@example.com").one()
        assert student.password_hash
        assert student.password_hash != TEST_PASSWORD
        assert auth_service.verify_password(TEST_PASSWORD, student.password_hash)

    def test_register_duplicate_email(self, client):
        client.post("/api/register", json={
            "name": "张三",
            "email": "zhangsan@example.com",
            "grade": "高一",
            "password": TEST_PASSWORD
        })
        response = client.post("/api/register", json={
            "name": "张三",
            "email": "zhangsan@example.com",
            "grade": "高二",
            "password": TEST_PASSWORD
        })
        assert response.status_code == 400
        assert "已注册" in response.json()["detail"]

    def test_register_missing_password(self, client):
        response = client.post("/api/register", json={
            "name": "张三",
            "email": "missing-password@example.com",
            "grade": "高一"
        })
        assert response.status_code == 422

    def test_register_missing_fields(self, client):
        response = client.post("/api/register", json={
            "name": "张三"
        })
        assert response.status_code == 422

    def test_register_invalid_email(self, client):
        response = client.post("/api/register", json={
            "name": "张三",
            "email": "invalid-email",
            "grade": "高一",
            "password": TEST_PASSWORD
        })
        assert response.status_code == 422

    def test_register_invalid_grade(self, client):
        response = client.post("/api/register", json={
            "name": "张三",
            "email": "test@example.com",
            "grade": "初一",
            "password": TEST_PASSWORD
        })
        assert response.status_code == 422

    def test_register_all_grades(self, client):
        grades = ["高一", "高二", "高三"]
        for i, grade in enumerate(grades):
            response = client.post("/api/register", json={
                "name": f"学生{i}",
                "email": f"student{i}@example.com",
                "grade": grade,
                "password": TEST_PASSWORD
            })
            assert response.status_code == 201
            assert response.json()["data"]["student"]["grade"] == grade


class TestAuthAPI:
    def _register_student(self, client, email="login@example.com", password=TEST_PASSWORD):
        return client.post("/api/register", json={
            "name": "登录学生",
            "email": email,
            "grade": "高一",
            "password": password
        })

    def test_login_success_returns_token_and_student(self, client):
        self._register_student(client)

        response = client.post("/api/login", json={
            "email": "login@example.com",
            "password": TEST_PASSWORD
        })

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["token_type"] == "bearer"
        assert isinstance(data["data"]["access_token"], str)
        assert len(data["data"]["access_token"]) > 0
        assert data["data"]["student"]["email"] == "login@example.com"
        assert data["data"]["student"]["name"] == "登录学生"
        assert "password" not in data["data"]["student"]
        assert "password_hash" not in data["data"]["student"]

    def test_login_unknown_email_returns_404(self, client):
        response = client.post("/api/login", json={
            "email": "missing@example.com",
            "password": TEST_PASSWORD
        })

        assert response.status_code == 404
        assert "未注册" in response.json()["detail"]

    def test_login_wrong_password_returns_401(self, client):
        self._register_student(client)

        response = client.post("/api/login", json={
            "email": "login@example.com",
            "password": "WrongPass123!"
        })

        assert response.status_code == 401
        assert "密码错误" in response.json()["detail"]

    def test_auth_me_returns_current_student_with_valid_token(self, client):
        self._register_student(client)
        login_response = client.post("/api/login", json={
            "email": "login@example.com",
            "password": TEST_PASSWORD
        })
        token = login_response.json()["data"]["access_token"]

        response = client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "login@example.com"
        assert data["name"] == "登录学生"

    def test_auth_me_without_token_returns_401(self, client):
        response = client.get("/api/auth/me")

        assert response.status_code == 401

    def test_migrated_legacy_user_can_login(self, client, db_session):
        student = Student(
            name="老用户",
            email="legacy@example.com",
            grade=ModelGradeEnum.GRADE_10
        )
        db_session.add(student)
        db_session.commit()

        migration_spec = importlib.util.find_spec("app.core.migrations")
        assert migration_spec is not None
        migrations = importlib.import_module("app.core.migrations")
        migrations.migrate_password_hashes(db_session.get_bind(), legacy_password=LEGACY_PASSWORD)
        db_session.expire_all()

        migrated = db_session.query(Student).filter(Student.email == "legacy@example.com").one()
        first_hash = migrated.password_hash
        assert first_hash
        assert auth_service.verify_password(LEGACY_PASSWORD, first_hash)

        migrations.migrate_password_hashes(db_session.get_bind(), legacy_password="OtherPass123!")
        db_session.expire_all()
        migrated_again = db_session.query(Student).filter(Student.email == "legacy@example.com").one()
        assert migrated_again.password_hash == first_hash

        response = client.post("/api/login", json={
            "email": "legacy@example.com",
            "password": LEGACY_PASSWORD
        })

        assert response.status_code == 200
        assert response.json()["data"]["student"]["email"] == "legacy@example.com"


class TestTaskAPI:
    def _register_student(self, client, email="test@example.com"):
        return client.post("/api/register", json={
            "name": "测试学生",
            "email": email,
            "grade": "高一",
            "password": TEST_PASSWORD
        })

    def test_create_task_success(self, client):
        self._register_student(client)
        response = client.post("/api/tasks", json={
            "student_email": "test@example.com",
            "description": "观看一个AI科普视频"
        })
        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        assert data["data"]["task"]["description"] == "观看一个AI科普视频"
        assert data["data"]["task"]["status"] == "进行中"

    def test_create_task_nonexistent_student(self, client):
        response = client.post("/api/tasks", json={
            "student_email": "nonexistent@example.com",
            "description": "测试任务"
        })
        assert response.status_code == 404

    def test_get_task(self, client):
        self._register_student(client)
        create_resp = client.post("/api/tasks", json={
            "student_email": "test@example.com",
            "description": "测试任务"
        })
        task_id = create_resp.json()["data"]["task"]["id"]

        response = client.get(f"/api/tasks/{task_id}")
        assert response.status_code == 200
        assert response.json()["description"] == "测试任务"

    def test_get_nonexistent_task(self, client):
        response = client.get("/api/tasks/99999")
        assert response.status_code == 404


class TestTaskCompleteAPI:
    def _setup_student_and_task(self, client):
        client.post("/api/register", json={
            "name": "测试学生",
            "email": "test@example.com",
            "grade": "高一",
            "password": TEST_PASSWORD
        })
        task_resp = client.post("/api/tasks", json={
            "student_email": "test@example.com",
            "description": "完成测试任务"
        })
        return task_resp.json()["data"]["task"]["id"]

    def test_complete_task_success(self, client):
        task_id = self._setup_student_and_task(client)
        response = client.post("/api/task-complete", json={
            "task_id": task_id,
            "feedback": "任务完成，感觉很有收获！"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["task"]["status"] == "已完成"
        assert data["data"]["task"]["feedback"] == "任务完成，感觉很有收获！"
        assert data["data"]["task"]["completed_at"] is not None

    def test_complete_task_without_feedback(self, client):
        task_id = self._setup_student_and_task(client)
        response = client.post("/api/task-complete", json={
            "task_id": task_id
        })
        assert response.status_code == 200
        assert response.json()["data"]["task"]["status"] == "已完成"

    def test_complete_nonexistent_task(self, client):
        response = client.post("/api/task-complete", json={
            "task_id": 99999
        })
        assert response.status_code == 404

    def test_complete_task_idempotent(self, client):
        task_id = self._setup_student_and_task(client)
        client.post("/api/task-complete", json={"task_id": task_id})
        response = client.post("/api/task-complete", json={"task_id": task_id})
        assert response.status_code == 200
        assert "无需重复打卡" in response.json()["message"]


class TestStudentAPI:
    def test_get_student(self, client):
        client.post("/api/register", json={
            "name": "李四",
            "email": "lisi@example.com",
            "grade": "高二",
            "password": TEST_PASSWORD
        })
        response = client.get("/api/students/lisi@example.com")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "李四"
        assert data["email"] == "lisi@example.com"
        assert data["grade"] == "高二"
        assert "tasks" in data

    def test_get_nonexistent_student(self, client):
        response = client.get("/api/students/nonexistent@example.com")
        assert response.status_code == 404

    def test_student_with_tasks(self, client):
        client.post("/api/register", json={
            "name": "王五",
            "email": "wangwu@example.com",
            "grade": "高三",
            "password": TEST_PASSWORD
        })
        client.post("/api/tasks", json={
            "student_email": "wangwu@example.com",
            "description": "任务1"
        })
        client.post("/api/tasks", json={
            "student_email": "wangwu@example.com",
            "description": "任务2"
        })
        response = client.get("/api/students/wangwu@example.com")
        assert response.status_code == 200
        assert len(response.json()["tasks"]) == 2


class TestChatAPI:
    def test_chat_returns_mock_reply(self, client):
        response = client.post("/api/chat", json={
            "messages": [
                {"role": "user", "content": "我最近有点迷茫，不知道该做什么。"}
            ],
            "student_name": "小明"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["mode"] == "mock"
        assert isinstance(data["reply"], str)
        assert len(data["reply"]) > 0
        # 只有 1 轮 user 消息，尚未达到可提炼任务的阈值
        assert data["can_extract_task"] is False

    def test_chat_can_extract_after_three_turns(self, client):
        response = client.post("/api/chat", json={
            "messages": [
                {"role": "user", "content": "我最近对画画挺感兴趣的。"},
                {"role": "assistant", "content": "那件事带给你什么感受呢？"},
                {"role": "user", "content": "画画的时候我感觉很平静很专注。"},
                {"role": "assistant", "content": "如果时间由你支配，你最想做什么？"},
                {"role": "user", "content": "我想多学一点插画的技法。"}
            ],
            "student_name": "小明"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["mode"] == "mock"
        assert isinstance(data["reply"], str)
        assert len(data["reply"]) > 0
        # 3 条 user 消息，达到可提炼任务的阈值
        assert data["can_extract_task"] is True

    def test_chat_empty_messages(self, client):
        response = client.post("/api/chat", json={
            "messages": []
        })
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["mode"] == "mock"
        assert isinstance(data["reply"], str)
        assert len(data["reply"]) > 0
        assert data["can_extract_task"] is False


class TestExtractTaskAPI:
    def _register_student(self, client, email="chat_student@example.com"):
        return client.post("/api/register", json={
            "name": "对话学生",
            "email": email,
            "grade": "高一",
            "password": TEST_PASSWORD
        })

    def test_extract_task_success(self, client):
        email = "chat_student@example.com"
        self._register_student(client, email)
        response = client.post("/api/chat/extract-task", json={
            "student_email": email,
            "messages": [
                {"role": "user", "content": "我最近对画画挺感兴趣的。"},
                {"role": "assistant", "content": "那件事带给你什么感受呢？"},
                {"role": "user", "content": "画画的时候我感觉很平静，很想多学一点。"}
            ]
        })
        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        task = data["data"]["task"]
        assert isinstance(task["description"], str)
        assert len(task["description"]) > 0
        assert task["status"] == "进行中"
        assert "id" in task

    def test_extract_task_student_not_found(self, client):
        response = client.post("/api/chat/extract-task", json={
            "student_email": "nonexistent@example.com",
            "messages": [
                {"role": "user", "content": "随便聊聊。"}
            ]
        })
        assert response.status_code == 404


class TestPasswordHashing:
    def test_password_hash_round_trip(self):
        assert hasattr(auth_service, "hash_password")
        assert hasattr(auth_service, "verify_password")

        password_hash = auth_service.hash_password(TEST_PASSWORD)

        assert password_hash
        assert password_hash != TEST_PASSWORD
        assert auth_service.verify_password(TEST_PASSWORD, password_hash)
        assert not auth_service.verify_password("WrongPass123!", password_hash)
        assert not auth_service.verify_password(TEST_PASSWORD, "invalid-hash")


class TestPasswordMigration:
    def test_migration_adds_password_hash_column_and_is_idempotent(self, tmp_path):
        db_path = tmp_path / "legacy.db"
        engine = create_engine(
            f"sqlite:///{db_path}",
            connect_args={"check_same_thread": False}
        )
        with engine.begin() as connection:
            connection.execute(text("""
                CREATE TABLE students (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name VARCHAR(100) NOT NULL,
                    email VARCHAR(255) NOT NULL UNIQUE,
                    grade VARCHAR(16) NOT NULL,
                    registered_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    operation_log DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """))
            connection.execute(
                text("INSERT INTO students (name, email, grade) VALUES (:name, :email, :grade)"),
                {"name": "老库用户", "email": "legacy-db@example.com", "grade": "GRADE_10"}
            )

        migration_spec = importlib.util.find_spec("app.core.migrations")
        assert migration_spec is not None
        migrations = importlib.import_module("app.core.migrations")
        migrations.migrate_password_hashes(engine, legacy_password=LEGACY_PASSWORD)

        with engine.begin() as connection:
            columns = [row[1] for row in connection.execute(text("PRAGMA table_info(students)"))]
            assert "password_hash" in columns
            first_hash = connection.execute(
                text("SELECT password_hash FROM students WHERE email = :email"),
                {"email": "legacy-db@example.com"}
            ).scalar_one()
            assert first_hash
            assert auth_service.verify_password(LEGACY_PASSWORD, first_hash)

        migrations.migrate_password_hashes(engine, legacy_password="OtherPass123!")

        with engine.begin() as connection:
            second_hash = connection.execute(
                text("SELECT password_hash FROM students WHERE email = :email"),
                {"email": "legacy-db@example.com"}
            ).scalar_one()
            assert second_hash == first_hash
