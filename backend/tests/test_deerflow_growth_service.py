import json

import httpx
import pytest

from app.services.deerflow_service import DeerFlowService


MESSAGES = [
    {"role": "user", "content": "我最近会主动画海报。"},
    {"role": "assistant", "content": "哪一部分最吸引你？"},
    {"role": "user", "content": "我喜欢安排颜色和版式，还会反复修改。"},
    {"role": "assistant", "content": "你愿意怎样继续验证？"},
    {"role": "user", "content": "我想再做一张不同主题的海报。"},
]


def growth_result():
    return {
        "contract_version": "awaken.student-growth.v1",
        "response_type": "growth_update",
        "assistant_message": "你可能对视觉表达和版式调整有持续兴趣，可以用一次小实验继续验证。",
        "next_question": None,
        "profile_candidate": {
            "interest_candidates": [
                {
                    "label": "视觉设计",
                    "evidence": ["主动画海报并反复调整颜色和版式"],
                    "confidence": "medium",
                }
            ],
            "ability_candidates": [
                {
                    "label": "迭代修改",
                    "evidence": ["会反复修改海报"],
                    "confidence": "low",
                }
            ],
            "exploration_stage": "testing",
            "summary": "目前可能对视觉表达和迭代修改有兴趣，仍需通过不同主题继续验证。",
            "uncertainties": ["证据主要来自一次海报制作经历"],
        },
        "micro_action": {
            "title": "做一张对比海报",
            "description": "选一个新主题，用两种版式各画一张草图，并记录更投入的一种。",
            "rationale": "验证兴趣更偏向配色还是版式组织。",
            "estimated_minutes": 20,
            "growth_points": 12,
            "topic_tags": ["视觉设计", "版式"],
            "completion_criteria": ["完成两张草图", "记录更投入的一种"],
            "reflection_prompt": "哪一种版式让你更愿意继续修改？",
            "safety_notes": [],
        },
        "resource_suggestions": [],
        "safety": {
            "status": "ok",
            "reason": None,
            "suggested_support": None,
        },
    }


@pytest.fixture
def enabled_service(monkeypatch):
    service = DeerFlowService()
    monkeypatch.setattr(service, "enabled", True)
    return service


@pytest.mark.asyncio
async def test_chat_extracts_valid_profile_candidate(enabled_service, monkeypatch):
    async def fake_run(_messages):
        return json.dumps(growth_result(), ensure_ascii=False)

    monkeypatch.setattr(enabled_service, "_run_deerflow", fake_run)

    result = await enabled_service.chat(MESSAGES, "小林")

    assert result["mode"] == "deerflow"
    assert result["reply"] == growth_result()["assistant_message"]
    assert result["profile_candidate"] == growth_result()["profile_candidate"]


@pytest.mark.asyncio
async def test_extract_task_returns_validated_structured_fields(enabled_service, monkeypatch):
    async def fake_run(_messages):
        return json.dumps(growth_result(), ensure_ascii=False)

    monkeypatch.setattr(enabled_service, "_run_deerflow", fake_run)

    task = await enabled_service.extract_task(MESSAGES, "小林")

    assert task == growth_result()["micro_action"]


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "mutate",
    [
        lambda result: "不是 JSON",
        lambda result: json.dumps(
            {**result, "micro_action": {**result["micro_action"], "estimated_minutes": 31}},
            ensure_ascii=False,
        ),
        lambda result: json.dumps(
            {**result, "micro_action": {**result["micro_action"], "growth_points": 0}},
            ensure_ascii=False,
        ),
        lambda result: json.dumps(
            {**result, "micro_action": {**result["micro_action"], "topic_tags": ["视觉设计", 1]}},
            ensure_ascii=False,
        ),
    ],
)
async def test_extract_task_invalid_output_uses_deterministic_fallback(
    enabled_service,
    monkeypatch,
    mutate,
):
    async def fake_run(_messages):
        return mutate(growth_result())

    monkeypatch.setattr(enabled_service, "_run_deerflow", fake_run)

    first = await enabled_service.extract_task(MESSAGES, "小林")
    second = await enabled_service.extract_task(MESSAGES, "小林")

    assert first == second
    assert first["description"] == (
        "花 10 分钟临摹一张你喜欢的插画或海报，并写下你最想学会的一个技法。"
    )
    assert first["estimated_minutes"] == 10
    assert first["growth_points"] == 10
    assert first["topic_tags"] == ["视觉设计"]


@pytest.mark.asyncio
async def test_network_errors_never_escape_and_use_deterministic_mock(enabled_service, monkeypatch):
    async def fail_run(_messages):
        request = httpx.Request("POST", "http://deerflow.test/api/runs/wait")
        raise httpx.ReadTimeout("timed out", request=request)

    monkeypatch.setattr(enabled_service, "_run_deerflow", fail_run)

    first_chat = await enabled_service.chat(MESSAGES, "小林")
    second_chat = await enabled_service.chat(MESSAGES, "小林")
    first_task = await enabled_service.extract_task(MESSAGES, "小林")
    second_task = await enabled_service.extract_task(MESSAGES, "小林")

    assert first_chat == second_chat
    assert first_chat["mode"] == "mock"
    assert first_chat["profile_candidate"]["interest_candidates"][0]["label"] == "视觉设计"
    assert first_task == second_task
    assert first_task["estimated_minutes"] == 10
    assert first_task["growth_points"] > 0


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
    assert "awaken.student-growth.v1" in explore
    assert "estimated_minutes" in unlock
