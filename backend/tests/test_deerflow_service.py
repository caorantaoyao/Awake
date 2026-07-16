import json

import httpx
import pytest

from app.services.deerflow_service import DeerFlowService


def _service():
    service = DeerFlowService()
    service.enabled = True
    return service


def _growth_payload():
    return {
        "contract_version": "awaken.student-growth.v1",
        "response_type": "growth_update",
        "assistant_message": "你可以先用一个小实验验证自己是否享受知识表达。",
        "next_question": None,
        "profile_candidate": {
            "interest_candidates": [
                {
                    "label": "知识表达",
                    "evidence": ["学生提到主动给同学讲解数学题"],
                    "confidence": "medium",
                }
            ],
            "ability_candidates": [
                {
                    "label": "拆解问题",
                    "evidence": ["学生描述了分步骤讲题的过程"],
                    "confidence": "low",
                }
            ],
            "exploration_stage": "testing",
            "summary": "目前可能喜欢把知识讲清楚，仍需要更多尝试验证。",
            "uncertainties": ["尚未确认是否愿意持续投入"],
        },
        "micro_action": {
            "title": "做一次知识讲解试验",
            "description": "选一道数学题，写出三步讲解并录一段两分钟内的口头说明。",
            "rationale": "用小产出验证对知识表达的投入感。",
            "estimated_minutes": 15,
            "growth_points": 10,
            "topic_tags": ["知识表达", "数学"],
            "completion_criteria": ["写出三步讲解", "完成两分钟内的说明"],
            "reflection_prompt": "哪一步最投入，哪一步最困难？",
            "safety_notes": [],
        },
        "resource_suggestions": [],
        "safety": {
            "status": "ok",
            "reason": None,
            "suggested_support": None,
        },
    }


def test_build_system_prompt_keeps_phase_rules_mutually_exclusive_and_adds_growth_contract():
    service = _service()

    exploration = service._build_system_prompt("小林", user_turns=2)
    unlocked = service._build_system_prompt("小林", user_turns=3)

    assert "【当前阶段：探索期】" in exploration
    assert "【当前阶段：深入引导期】" not in exploration
    assert "【当前阶段：深入引导期】" in unlocked
    assert "【当前阶段：探索期】" not in unlocked
    assert "awaken.student-growth.v1" in exploration
    assert "awaken.student-growth.v1" in unlocked


@pytest.mark.asyncio
async def test_analyze_growth_parses_structured_profile_and_task(monkeypatch):
    service = _service()
    payload = _growth_payload()

    async def fake_run(full_messages):
        return json.dumps(payload, ensure_ascii=False)

    monkeypatch.setattr(service, "_run_deerflow", fake_run)

    result = await service.analyze_growth(
        [
            {"role": "user", "content": "我喜欢给同学讲数学题。"},
            {"role": "user", "content": "我会先拆成几个步骤。"},
            {"role": "user", "content": "我愿意今天试着录一段讲解。"},
        ],
        "小林",
    )

    assert result["mode"] == "deerflow"
    assert result["profile_candidate"] == payload["profile_candidate"]
    assert result["micro_action"]["description"] == payload["micro_action"]["description"]
    assert result["micro_action"]["estimated_minutes"] == 15
    assert result["micro_action"]["growth_points"] == 10
    assert result["micro_action"]["topic_tags"] == ["知识表达", "数学"]


@pytest.mark.asyncio
async def test_analyze_growth_removes_sensitive_personality_and_mental_health_candidates(
    monkeypatch,
):
    service = _service()
    payload = _growth_payload()
    payload["profile_candidate"]["interest_candidates"].append(
        {
            "label": "抑郁倾向",
            "evidence": ["学生说最近有点累"],
            "confidence": "low",
        }
    )
    payload["profile_candidate"]["ability_candidates"].append(
        {
            "label": "内向型人格",
            "evidence": ["学生说更喜欢独处"],
            "confidence": "low",
        }
    )

    async def fake_run(full_messages):
        return json.dumps(payload, ensure_ascii=False)

    monkeypatch.setattr(service, "_run_deerflow", fake_run)

    result = await service.analyze_growth(
        [{"role": "user", "content": "我喜欢给同学讲数学题。"}],
        "小林",
    )

    labels = {
        candidate["label"]
        for key in ("interest_candidates", "ability_candidates")
        for candidate in result["profile_candidate"][key]
    }
    assert labels == {"知识表达", "拆解问题"}


@pytest.mark.asyncio
async def test_analyze_growth_drops_micro_action_before_unlock_threshold(monkeypatch):
    service = _service()

    async def fake_run(full_messages):
        return json.dumps(_growth_payload(), ensure_ascii=False)

    monkeypatch.setattr(service, "_run_deerflow", fake_run)

    result = await service.analyze_growth(
        [{"role": "user", "content": "我喜欢给同学讲数学题。"}],
        "小林",
    )

    assert result["mode"] == "deerflow"
    assert result["micro_action"] is None


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "invalid_reply",
    [
        pytest.param("不是 JSON", id="非法-json"),
        pytest.param(
            json.dumps(
                {
                    **_growth_payload(),
                    "micro_action": {
                        **_growth_payload()["micro_action"],
                        "estimated_minutes": 45,
                    },
                },
                ensure_ascii=False,
            ),
            id="任务时长越界",
        ),
        pytest.param(
            json.dumps(
                {
                    **_growth_payload(),
                    "micro_action": {
                        **_growth_payload()["micro_action"],
                        "growth_points": 0,
                        "topic_tags": [],
                    },
                },
                ensure_ascii=False,
            ),
            id="成长值与标签非法",
        ),
    ],
)
async def test_analyze_growth_falls_back_to_valid_deterministic_result_on_invalid_output(
    monkeypatch,
    invalid_reply,
):
    service = _service()

    async def fake_run(full_messages):
        return invalid_reply

    monkeypatch.setattr(service, "_run_deerflow", fake_run)
    messages = [
        {"role": "user", "content": "我想试试编程。"},
        {"role": "user", "content": "我喜欢把想法做成能运行的东西。"},
        {"role": "user", "content": "我愿意今天写一个小程序。"},
    ]

    result = await service.analyze_growth(messages, "小林")

    assert result["mode"] == "mock"
    assert result["profile_candidate"]["interest_candidates"][0]["label"] == "数字创作"
    assert 5 <= result["micro_action"]["estimated_minutes"] <= 30
    assert result["micro_action"]["growth_points"] > 0
    assert result["micro_action"]["topic_tags"] == ["数字创作"]


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "error",
    [
        pytest.param(httpx.ReadTimeout("timed out"), id="超时"),
        pytest.param(httpx.ConnectError("unreachable"), id="不可达"),
    ],
)
async def test_analyze_growth_falls_back_without_raising_when_deerflow_fails(
    monkeypatch,
    error,
):
    service = _service()

    async def failing_run(full_messages):
        raise error

    monkeypatch.setattr(service, "_run_deerflow", failing_run)
    messages = [
        {"role": "user", "content": "我喜欢画画。"},
        {"role": "user", "content": "我会留意海报的配色。"},
        {"role": "user", "content": "我想做一次小尝试。"},
    ]

    first = await service.analyze_growth(messages, "小林")
    second = await service.analyze_growth(messages, "小林")

    assert first == second
    assert first["mode"] == "mock"
    assert first["profile_candidate"]["interest_candidates"][0]["label"] == "视觉设计"
    assert first["micro_action"]["description"]
    assert 5 <= first["micro_action"]["estimated_minutes"] <= 30


@pytest.mark.asyncio
async def test_chat_and_extract_task_return_structured_growth_contracts(monkeypatch):
    service = _service()
    payload = _growth_payload()

    async def fake_run(full_messages):
        return json.dumps(payload, ensure_ascii=False)

    monkeypatch.setattr(service, "_run_deerflow", fake_run)
    messages = [
        {"role": "user", "content": "我喜欢给同学讲数学题。"},
        {"role": "user", "content": "我会先拆成几个步骤。"},
        {"role": "user", "content": "我愿意今天试着录一段讲解。"},
    ]

    chat_result = await service.chat(messages, "小林")
    task = await service.extract_task(messages, "小林")

    assert chat_result["reply"] == payload["assistant_message"]
    assert chat_result["mode"] == "deerflow"
    assert task == payload["micro_action"]
