import json

import httpx
import pytest

from app.services.deerflow_service import DeerFlowService, DeerFlowUnavailable


def _service():
    service = DeerFlowService()
    service.enabled = True
    return service


def test_build_system_prompt_respects_chat_modes_and_thresholds(monkeypatch):
    service = _service()
    monkeypatch.setattr(
        "app.services.deerflow_service.settings.XIAOHAI_UNLOCK_AFTER_TURNS",
        3,
    )

    explore = service._build_system_prompt("小林", user_turns=2)
    unlocked = service._build_system_prompt("小林", user_turns=3)

    assert "小林" in explore
    assert "【对话风格】" not in explore
    assert "探索" in explore
    assert "unlock" not in explore.lower() or "解锁" in explore or "行动建议" in unlocked


@pytest.mark.asyncio
async def test_chat_returns_deerflow_mode_with_thread_id(monkeypatch):
    service = _service()
    test_reply = "你好，我是小海。"
    test_thread = "thread-abc123"

    async def fake_stream_chat(*args, **kwargs):
        yield {"type": "meta", "thread_id": test_thread}
        yield {"type": "text", "content": test_reply}
        yield {"type": "done", "reply": test_reply, "thread_id": test_thread}

    monkeypatch.setattr(service, "stream_chat", fake_stream_chat)

    result = await service.chat(
        [{"role": "user", "content": "你好"}],
        "小林",
    )

    assert result["reply"] == test_reply
    assert result["mode"] == "deerflow"
    assert result["thread_id"] == test_thread


@pytest.mark.asyncio
async def test_chat_raises_when_stream_returns_error_without_content(monkeypatch):
    service = _service()

    async def fake_stream_chat(*args, **kwargs):
        yield {"type": "error", "message": "连接失败"}

    monkeypatch.setattr(service, "stream_chat", fake_stream_chat)

    with pytest.raises(DeerFlowUnavailable):
        await service.chat([{"role": "user", "content": "你好"}], "小林")


@pytest.mark.asyncio
async def test_check_enabled_raises_when_disabled():
    service = DeerFlowService()
    service.enabled = False

    with pytest.raises(DeerFlowUnavailable):
        service._check_enabled()


@pytest.mark.asyncio
async def test_extract_task_requires_min_turns(monkeypatch):
    service = _service()
    monkeypatch.setattr(
        "app.services.deerflow_service.settings.XIAOHAI_UNLOCK_AFTER_TURNS",
        3,
    )

    with pytest.raises(DeerFlowUnavailable):
        await service.extract_task(
            [{"role": "user", "content": "一轮对话"}],
            "小林",
        )


@pytest.mark.asyncio
async def test_extract_task_parses_valid_json(monkeypatch):
    service = _service()
    task_json = {
        "title": "测试任务",
        "description": "这是一个测试任务",
        "rationale": "测试理由",
        "estimated_minutes": 15,
        "growth_points": 10,
        "topic_tags": ["测试"],
        "completion_criteria": ["完成测试"],
        "reflection_prompt": "有什么收获？",
        "safety_notes": [],
    }

    async def fake_chat(messages, student_name, **kwargs):
        return {
            "reply": "```json\n" + json.dumps(task_json, ensure_ascii=False) + "\n```",
            "mode": "deerflow",
            "thread_id": "t1",
        }

    monkeypatch.setattr(service, "chat", fake_chat)

    result = await service.extract_task(
        [
            {"role": "user", "content": "第一轮"},
            {"role": "assistant", "content": "回复1"},
            {"role": "user", "content": "第二轮"},
            {"role": "assistant", "content": "回复2"},
            {"role": "user", "content": "第三轮"},
        ],
        "小林",
        unlock_after_turns=3,
    )

    assert result["title"] == "测试任务"
    assert result["description"] == "这是一个测试任务"
    assert result["estimated_minutes"] == 15
    assert result["growth_points"] == 10
    assert result["topic_tags"] == ["测试"]


@pytest.mark.asyncio
async def test_extract_task_clamps_invalid_values(monkeypatch):
    service = _service()
    task_json = {
        "title": "测试任务",
        "description": "描述",
        "estimated_minutes": 100,
        "growth_points": 0,
        "topic_tags": "不是数组",
    }

    async def fake_chat(messages, student_name, **kwargs):
        return {
            "reply": json.dumps(task_json, ensure_ascii=False),
            "mode": "deerflow",
            "thread_id": "t1",
        }

    monkeypatch.setattr(service, "chat", fake_chat)

    result = await service.extract_task(
        [{"role": "user", "content": f"轮{i}"} for i in range(3)],
        "小林",
        unlock_after_turns=3,
    )

    assert 5 <= result["estimated_minutes"] <= 30
    assert 1 <= result["growth_points"] <= 100
    assert isinstance(result["topic_tags"], list)
    assert len(result["topic_tags"]) > 0


@pytest.mark.asyncio
async def test_get_status_returns_offline_when_disabled():
    service = DeerFlowService()
    service.enabled = False

    status = await service.get_status()
    assert status["online"] is False


def test_clamp_int():
    assert DeerFlowService._clamp_int(15, 5, 30, 10) == 15
    assert DeerFlowService._clamp_int(0, 5, 30, 10) == 5
    assert DeerFlowService._clamp_int(100, 5, 30, 10) == 30
    assert DeerFlowService._clamp_int("not int", 5, 30, 10) == 10


def test_ensure_str_list():
    assert DeerFlowService._ensure_str_list(["a", "b"], []) == ["a", "b"]
    assert DeerFlowService._ensure_str_list([1, 2.5, "c"], []) == ["1", "2.5", "c"]
    assert DeerFlowService._ensure_str_list("not a list", ["default"]) == ["default"]
    assert DeerFlowService._ensure_str_list([], ["fallback"]) == ["fallback"]
