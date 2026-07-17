import json

import pytest

from app.services.deerflow_service import DeerFlowService, DeerFlowUnavailable


MESSAGES_3_TURNS = [
    {"role": "user", "content": "我最近会主动画海报。"},
    {"role": "assistant", "content": "哪一部分最吸引你？"},
    {"role": "user", "content": "我喜欢安排颜色和版式，还会反复修改。"},
    {"role": "assistant", "content": "你愿意怎样继续验证？"},
    {"role": "user", "content": "我想再做一张不同主题的海报。"},
]


@pytest.fixture
def enabled_service(monkeypatch):
    service = DeerFlowService()
    monkeypatch.setattr(service, "enabled", True)
    return service


def test_growth_prompts_keep_explore_and_unlock_rules_mutually_exclusive(
    enabled_service,
    monkeypatch,
):
    monkeypatch.setattr(
        "app.services.deerflow_service.settings.XIAOHAI_UNLOCK_AFTER_TURNS",
        3,
    )

    explore = enabled_service._build_system_prompt("小林", user_turns=2)
    unlock = enabled_service._build_system_prompt("小林", user_turns=3)

    assert "【当前阶段：探索期】" in explore
    assert "【当前阶段：深入引导期】" not in explore
    assert "【当前阶段：深入引导期】" in unlock
    assert "【当前阶段：探索期】" not in unlock


def test_chat_mode_direct_action_lowers_threshold(enabled_service, monkeypatch):
    monkeypatch.setattr(
        "app.services.deerflow_service.settings.XIAOHAI_UNLOCK_AFTER_TURNS",
        3,
    )

    balanced = enabled_service._build_system_prompt("小林", user_turns=2, chat_mode="balanced")
    direct_explore = enabled_service._build_system_prompt("小林", user_turns=1, chat_mode="direct_action")
    direct_unlocked = enabled_service._build_system_prompt("小林", user_turns=2, chat_mode="direct_action")
    explore_default = enabled_service._build_system_prompt("小林", user_turns=2)

    assert "【对话风格】" in balanced
    assert "【对话风格】" in direct_explore
    assert "【对话风格】" in direct_unlocked
    assert "【当前阶段：探索期】" in direct_explore
    assert "【当前阶段：深入引导期】" in direct_unlocked
    assert "【当前阶段：探索期】" in explore_default


@pytest.mark.asyncio
async def test_extract_task_with_valid_json_returns_structured_fields(enabled_service, monkeypatch):
    task_result = {
        "title": "做一张对比海报",
        "description": "选一个新主题，用两种版式各画一张草图，并记录更投入的一种。",
        "rationale": "验证兴趣更偏向配色还是版式组织。",
        "estimated_minutes": 20,
        "growth_points": 12,
        "topic_tags": ["视觉设计", "版式"],
        "completion_criteria": ["完成两张草图", "记录更投入的一种"],
        "reflection_prompt": "哪一种版式让你更愿意继续修改？",
        "safety_notes": [],
    }

    async def fake_chat(messages, student_name, **kwargs):
        return {
            "reply": json.dumps(task_result, ensure_ascii=False),
            "mode": "deerflow",
            "thread_id": "t1",
        }

    monkeypatch.setattr(enabled_service, "chat", fake_chat)

    task = await enabled_service.extract_task(MESSAGES_3_TURNS, "小林")

    assert task["title"] == "做一张对比海报"
    assert task["description"] == "选一个新主题，用两种版式各画一张草图，并记录更投入的一种。"
    assert task["estimated_minutes"] == 20
    assert task["growth_points"] == 12
    assert task["topic_tags"] == ["视觉设计", "版式"]


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "invalid_reply",
    [
        "不是 JSON",
        "no curly braces here",
        "{broken json",
    ],
)
async def test_extract_task_raises_on_invalid_json(
    enabled_service,
    monkeypatch,
    invalid_reply,
):
    async def fake_chat(messages, student_name, **kwargs):
        return {
            "reply": invalid_reply,
            "mode": "deerflow",
            "thread_id": "t1",
        }

    monkeypatch.setattr(enabled_service, "chat", fake_chat)

    with pytest.raises(DeerFlowUnavailable):
        await enabled_service.extract_task(MESSAGES_3_TURNS, "小林")


@pytest.mark.asyncio
async def test_extract_task_clamps_out_of_range_values(enabled_service, monkeypatch):
    task_data = {
        "title": "测试",
        "description": "描述",
        "estimated_minutes": 100,
        "growth_points": 0,
        "topic_tags": "not a list",
    }

    async def fake_chat(messages, student_name, **kwargs):
        return {
            "reply": json.dumps(task_data, ensure_ascii=False),
            "mode": "deerflow",
            "thread_id": "t1",
        }

    monkeypatch.setattr(enabled_service, "chat", fake_chat)

    result = await enabled_service.extract_task(MESSAGES_3_TURNS, "小林")

    assert 5 <= result["estimated_minutes"] <= 30
    assert 1 <= result["growth_points"] <= 100
    assert isinstance(result["topic_tags"], list)
    assert len(result["topic_tags"]) > 0


@pytest.mark.asyncio
async def test_extract_task_requires_thread_id_and_returns_valid_fields(enabled_service, monkeypatch):
    task_data = {
        "title": "小测试",
        "description": "完成测试",
        "estimated_minutes": 10,
        "growth_points": 5,
        "topic_tags": ["测试"],
    }

    async def fake_chat(messages, student_name, **kwargs):
        assert "thread_id" in kwargs or kwargs.get("thread_id") is None
        return {
            "reply": json.dumps(task_data, ensure_ascii=False),
            "mode": "deerflow",
            "thread_id": kwargs.get("thread_id") or "gen-thread-1",
        }

    monkeypatch.setattr(enabled_service, "chat", fake_chat)

    result = await enabled_service.extract_task(
        MESSAGES_3_TURNS,
        "小林",
        thread_id="existing-thread",
    )

    assert result["estimated_minutes"] == 10
    assert result["growth_points"] == 5
    assert isinstance(result["completion_criteria"], list)
    assert isinstance(result["reflection_prompt"], str)
