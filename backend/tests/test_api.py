import pytest


class TestHealthCheck:
    def test_health_endpoint(self, client):
        response = client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data


class TestRegisterAPI:
    def test_register_success(self, client):
        response = client.post("/api/register", json={
            "name": "张三",
            "email": "zhangsan@example.com",
            "grade": "高一"
        })
        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        assert "student" in data["data"]
        assert data["data"]["student"]["name"] == "张三"
        assert data["data"]["student"]["email"] == "zhangsan@example.com"
        assert data["data"]["student"]["grade"] == "高一"

    def test_register_duplicate_email(self, client):
        client.post("/api/register", json={
            "name": "张三",
            "email": "zhangsan@example.com",
            "grade": "高一"
        })
        response = client.post("/api/register", json={
            "name": "张三",
            "email": "zhangsan@example.com",
            "grade": "高二"
        })
        assert response.status_code == 400
        assert "已注册" in response.json()["detail"]

    def test_register_missing_fields(self, client):
        response = client.post("/api/register", json={
            "name": "张三"
        })
        assert response.status_code == 422

    def test_register_invalid_email(self, client):
        response = client.post("/api/register", json={
            "name": "张三",
            "email": "invalid-email",
            "grade": "高一"
        })
        assert response.status_code == 422

    def test_register_invalid_grade(self, client):
        response = client.post("/api/register", json={
            "name": "张三",
            "email": "test@example.com",
            "grade": "初一"
        })
        assert response.status_code == 422

    def test_register_all_grades(self, client):
        grades = ["高一", "高二", "高三"]
        for i, grade in enumerate(grades):
            response = client.post("/api/register", json={
                "name": f"学生{i}",
                "email": f"student{i}@example.com",
                "grade": grade
            })
            assert response.status_code == 201
            assert response.json()["data"]["student"]["grade"] == grade


class TestTaskAPI:
    def _register_student(self, client, email="test@example.com"):
        return client.post("/api/register", json={
            "name": "测试学生",
            "email": email,
            "grade": "高一"
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
            "grade": "高一"
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
            "grade": "高二"
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
            "grade": "高三"
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
            "grade": "高一"
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
