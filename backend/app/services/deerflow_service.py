import json
import logging
import uuid
from typing import List, Optional, Dict, Any

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)


class DeerFlowService:
    """本地 DeerFlow 2.0 对话引擎的 HTTP 适配层。

    DeerFlow 2.0 是基于 LangGraph 的 super-agent harness，其对话入口是
    LangGraph 平台风格的 `POST /api/runs/wait`（阻塞直到完成），而非 OpenAI
    兼容的 `/v1/chat/completions`。本适配层将前端多轮消息封装成一次无状态
    run（每次请求用全新 thread，携带完整历史），注入「小海」苏格拉底 system
    prompt，并从返回的 channel_values.messages 中取最后一条 AI 回复。

    当 DeerFlow 未启用或不可达时，自动降级到内置 mock 逻辑，保证前端闭环始终
    可用，绝不向上抛异常。
    """

    _RESPONSE_TYPES = {"exploration", "growth_update", "clarification", "safety_redirect"}
    _EXPLORATION_STAGES = {"discovering", "testing", "reflecting"}
    _CONFIDENCE_LEVELS = {"low", "medium", "high"}
    _SAFETY_STATUSES = {"ok", "needs_support", "urgent"}
    _SENSITIVE_PROFILE_TERMS = (
        "人格",
        "内向",
        "外向",
        "抑郁",
        "焦虑",
        "心理",
        "精神",
        "疾病",
        "残障",
        "自闭",
        "多动",
        "神经",
        "智力",
        "成瘾",
        "家庭收入",
        "社会阶层",
        "宗教",
        "政治",
        "性取向",
        "性别认同",
        "犯罪",
    )

    def __init__(self):
        self.enabled = settings.DEERFLOW_ENABLED
        self.base_url = settings.DEERFLOW_BASE_URL.rstrip("/")
        self.assistant_id = settings.DEERFLOW_ASSISTANT_ID
        self.api_key = settings.DEERFLOW_API_KEY

    def _build_system_prompt(self, student_name: Optional[str], user_turns: int = 0) -> str:
        prompt = settings.XIAOHAI_PERSONA_PROMPT
        if student_name:
            prompt = f"{prompt}\n\n学生的名字是 {student_name}。"
        # 探索期与解锁期规则互斥二选一，避免两段规则在同一 prompt 内冲突
        if user_turns >= settings.XIAOHAI_UNLOCK_AFTER_TURNS:
            prompt = f"{prompt}{settings.XIAOHAI_UNLOCK_PROMPT}"
        else:
            prompt = f"{prompt}{settings.XIAOHAI_EXPLORE_PROMPT}"
        return f"{prompt}{settings.XIAOHAI_GROWTH_SKILL_PROMPT}"

    async def _run_deerflow(self, full_messages: List[Dict]) -> str:
        """向 DeerFlow 发起一次无状态 run 并返回最后一条 AI 回复文本。

        任何网络/协议异常都会向上抛出，由调用方负责降级。
        """
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        url = f"{self.base_url}/api/runs/wait"
        body = {
            "assistant_id": self.assistant_id,
            "input": {"messages": full_messages},
            "config": {"configurable": {"thread_id": str(uuid.uuid4())}},
        }

        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.post(url, json=body, headers=headers)
            resp.raise_for_status()
            data = resp.json()

        reply = self._extract_last_ai_text(data)
        if not reply:
            raise ValueError("DeerFlow 返回中未找到有效的 AI 回复")
        return reply

    @staticmethod
    def _content_to_text(content: Any) -> str:
        """把 LangChain 消息的 content（str 或 content-block 列表）压平成纯文本。"""
        if isinstance(content, str):
            return content.strip()
        if isinstance(content, list):
            parts = []
            for block in content:
                if isinstance(block, str):
                    parts.append(block)
                elif isinstance(block, dict) and block.get("type") == "text":
                    parts.append(str(block.get("text", "")))
            return "".join(parts).strip()
        return ""

    def _extract_last_ai_text(self, data: Dict) -> str:
        """从 `/api/runs/wait` 返回的 channel_values 中取最后一条有文本的 AI 消息。

        序列化后的 LangChain 消息用 `type` 区分角色：human/ai/system/tool；
        AI 回复对应 type == "ai"。工具调用产生的空文本 AI 消息将被跳过。
        """
        messages = data.get("messages")
        if not isinstance(messages, list):
            return ""

        for msg in reversed(messages):
            if not isinstance(msg, dict):
                continue
            role = msg.get("type") or msg.get("role")
            if role not in ("ai", "assistant"):
                continue
            text = self._content_to_text(msg.get("content"))
            if text:
                return text
        return ""

    def _validate_candidates(self, value: Any) -> List[Dict]:
        if not isinstance(value, list):
            raise ValueError("画像候选必须是数组")
        candidates = []
        for candidate in value:
            if not isinstance(candidate, dict):
                raise ValueError("画像候选项必须是对象")
            label = candidate.get("label")
            evidence = candidate.get("evidence")
            confidence = candidate.get("confidence")
            if not isinstance(label, str) or not label.strip():
                raise ValueError("画像标签无效")
            if (
                not isinstance(evidence, list)
                or not evidence
                or not all(isinstance(item, str) and item.strip() for item in evidence)
            ):
                raise ValueError("画像证据无效")
            if confidence not in self._CONFIDENCE_LEVELS:
                raise ValueError("画像置信度无效")
            if any(term in label for term in self._SENSITIVE_PROFILE_TERMS):
                continue
            candidates.append({
                "label": label.strip(),
                "evidence": [item.strip() for item in evidence],
                "confidence": confidence,
            })
        return candidates

    def _validate_profile_candidate(self, value: Any) -> Dict:
        if not isinstance(value, dict):
            raise ValueError("缺少画像候选")
        stage = value.get("exploration_stage")
        if stage not in self._EXPLORATION_STAGES:
            raise ValueError("探索阶段无效")
        summary = value.get("summary")
        uncertainties = value.get("uncertainties")
        if not isinstance(summary, str):
            raise ValueError("画像摘要无效")
        if (
            not isinstance(uncertainties, list)
            or not all(isinstance(item, str) for item in uncertainties)
        ):
            raise ValueError("画像不确定项无效")
        return {
            "interest_candidates": self._validate_candidates(
                value.get("interest_candidates")
            ),
            "ability_candidates": self._validate_candidates(
                value.get("ability_candidates")
            ),
            "exploration_stage": stage,
            "summary": summary.strip(),
            "uncertainties": [item.strip() for item in uncertainties if item.strip()],
        }

    @staticmethod
    def _required_text(value: Any, field_name: str) -> str:
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{field_name}无效")
        return value.strip()

    @classmethod
    def _validate_micro_action(cls, value: Any) -> Dict:
        if not isinstance(value, dict):
            raise ValueError("缺少微行动")
        title = cls._required_text(value.get("title"), "任务标题")
        description = cls._required_text(value.get("description"), "任务描述")
        rationale = cls._required_text(value.get("rationale"), "任务理由")
        estimated_minutes = value.get("estimated_minutes")
        growth_points = value.get("growth_points")
        topic_tags = value.get("topic_tags")
        completion_criteria = value.get("completion_criteria")
        reflection_prompt = cls._required_text(
            value.get("reflection_prompt"),
            "任务反思问题",
        )
        safety_notes = value.get("safety_notes")
        if (
            isinstance(estimated_minutes, bool)
            or not isinstance(estimated_minutes, int)
            or not 5 <= estimated_minutes <= 30
        ):
            raise ValueError("任务预计时长无效")
        if (
            isinstance(growth_points, bool)
            or not isinstance(growth_points, int)
            or not 1 <= growth_points <= 100
        ):
            raise ValueError("任务成长值无效")
        if (
            not isinstance(topic_tags, list)
            or not topic_tags
            or not all(isinstance(tag, str) and tag.strip() for tag in topic_tags)
        ):
            raise ValueError("任务主题标签无效")
        if (
            not isinstance(completion_criteria, list)
            or not completion_criteria
            or not all(
                isinstance(item, str) and item.strip()
                for item in completion_criteria
            )
        ):
            raise ValueError("任务完成标准无效")
        if (
            not isinstance(safety_notes, list)
            or not all(isinstance(item, str) for item in safety_notes)
        ):
            raise ValueError("任务安全说明无效")
        return {
            "title": title,
            "description": description,
            "rationale": rationale,
            "estimated_minutes": estimated_minutes,
            "growth_points": growth_points,
            "topic_tags": [tag.strip() for tag in topic_tags],
            "completion_criteria": [
                item.strip() for item in completion_criteria
            ],
            "reflection_prompt": reflection_prompt,
            "safety_notes": [
                item.strip() for item in safety_notes if item.strip()
            ],
        }

    def _parse_growth_result(self, text: str) -> Dict:
        result = json.loads(text)
        if not isinstance(result, dict):
            raise ValueError("成长结果必须是对象")
        if result.get("contract_version") != "awaken.student-growth.v1":
            raise ValueError("成长结果契约版本无效")
        if result.get("response_type") not in self._RESPONSE_TYPES:
            raise ValueError("成长响应类型无效")
        assistant_message = result.get("assistant_message")
        if not isinstance(assistant_message, str) or not assistant_message.strip():
            raise ValueError("成长回复无效")
        safety = result.get("safety")
        if (
            not isinstance(safety, dict)
            or safety.get("status") not in self._SAFETY_STATUSES
        ):
            raise ValueError("成长结果安全状态无效")
        return {
            "assistant_message": assistant_message.strip(),
            "profile_candidate": self._validate_profile_candidate(
                result.get("profile_candidate")
            ),
            "micro_action": (
                None
                if result.get("micro_action") is None
                else self._validate_micro_action(result.get("micro_action"))
            ),
        }

    async def analyze_growth(
        self,
        messages: List[Dict],
        student_name: Optional[str] = None,
    ) -> Dict:
        """返回经过校验的成长回复、画像候选和可选微行动。"""
        user_turns = sum(1 for message in messages if message.get("role") == "user")
        if self.enabled:
            try:
                full_messages = [
                    {
                        "role": "system",
                        "content": self._build_system_prompt(student_name, user_turns),
                    }
                ]
                full_messages.extend(messages)
                growth_result = self._parse_growth_result(
                    await self._run_deerflow(full_messages)
                )
                if user_turns < settings.XIAOHAI_UNLOCK_AFTER_TURNS:
                    growth_result["micro_action"] = None
                growth_result["reply"] = growth_result.pop("assistant_message")
                growth_result["mode"] = "deerflow"
                return growth_result
            except Exception as e:
                logger.warning(f"DeerFlow 成长分析失败，降级到 mock: {e}")

        return self._mock_growth_result(messages, student_name)

    async def chat(
        self,
        messages: List[Dict],
        student_name: Optional[str] = None,
    ) -> Dict:
        """多轮苏格拉底对话，兼容原有 reply/mode 返回字段。"""
        result = await self.analyze_growth(messages, student_name)
        return {
            "reply": result["reply"],
            "mode": result["mode"],
            "profile_candidate": result["profile_candidate"],
        }

    def _mock_growth_result(
        self,
        messages: List[Dict],
        student_name: Optional[str],
    ) -> Dict:
        user_turns = sum(1 for message in messages if message.get("role") == "user")
        return {
            "reply": self._mock_socratic_reply(messages, student_name),
            "mode": "mock",
            "profile_candidate": self._mock_profile_candidate(messages),
            "micro_action": (
                self._mock_extract_task(messages, student_name)
                if user_turns >= settings.XIAOHAI_UNLOCK_AFTER_TURNS
                else None
            ),
        }

    def _mock_socratic_reply(self, messages: List[Dict], student_name: Optional[str]) -> str:
        """内置的 mock 苏格拉底引导逻辑，按用户轮次推进提问。"""
        user_turns = sum(1 for m in messages if m.get("role") == "user")
        # 索引从 0 开始：第 1 轮用户消息 -> index 0
        index = max(user_turns - 1, 0)

        greeting = f"你好，{student_name}！" if student_name else "你好呀！"

        scripts = [
            f"{greeting}我是小海，很高兴认识你。先不聊什么大道理，"
            "我想先听听你——最近有没有哪件事，让你觉得有点好奇，或者有点烦心的？",
            "谢谢你愿意跟我说这些。那件事发生的时候，你心里最强烈的感受是什么呢？",
            "我好像有点明白你的状态了。换个角度想想：如果有一天时间完全由你自己支配，"
            "没有作业也没有人催你，你最想做点什么？",
            "听起来这里面藏着你在乎的东西。这些你提到的事情里，有哪一件是你愿意多花点时间去了解的？",
            "我能感受到你其实很清楚自己被什么吸引。我们不用一下子想清楚整个未来——"
            "可以先把它变成一个今天就能完成的小行动，你愿意试试吗？",
        ]

        safe_index = min(index, len(scripts) - 1)
        return scripts[safe_index]

    async def extract_task(
        self,
        messages: List[Dict],
        student_name: Optional[str] = None,
    ) -> Dict:
        """返回校验后的结构化微行动，失败时使用确定性本地结果。"""
        result = await self.analyze_growth(messages, student_name)
        return result["micro_action"] or self._mock_extract_task(
            messages,
            student_name,
        )

    @staticmethod
    def _user_text(messages: List[Dict]) -> str:
        return " ".join(
            str(m.get("content", ""))
            for m in messages
            if m.get("role") == "user"
        )

    def _mock_profile_candidate(self, messages: List[Dict]) -> Dict:
        text = self._user_text(messages)
        interest_candidates = []
        ability_candidates = []
        keyword_profiles = [
            (("画", "设计", "美术", "手绘", "海报"), "视觉设计"),
            (("游戏", "编程", "代码", "电脑"), "数字创作"),
            (("写", "文字", "故事", "作文"), "文字表达"),
            (("音乐", "唱", "乐器", "歌"), "音乐表达"),
            (("运动", "球", "跑", "健身"), "运动探索"),
        ]
        for keywords, label in keyword_profiles:
            if any(keyword in text for keyword in keywords):
                interest_candidates.append({
                    "label": label,
                    "evidence": ["学生在当前对话中主动提及相关经历或尝试意愿"],
                    "confidence": "low",
                })
                break
        if any(keyword in text for keyword in ("修改", "反复", "调整", "改进")):
            ability_candidates.append({
                "label": "迭代修改",
                "evidence": ["学生提到会修改或调整自己的产出"],
                "confidence": "low",
            })
        user_turns = sum(1 for m in messages if m.get("role") == "user")
        return {
            "interest_candidates": interest_candidates,
            "ability_candidates": ability_candidates,
            "exploration_stage": "testing" if user_turns >= 3 else "discovering",
            "summary": (
                f"目前可能对{interest_candidates[0]['label']}有兴趣，仍需通过行动继续验证。"
                if interest_candidates
                else "当前证据还不足以形成明确兴趣候选，可以继续从具体经历探索。"
            ),
            "uncertainties": ["本地降级结果仅依据当前对话中的关键词"],
        }

    def _mock_extract_task(self, messages: List[Dict], student_name: Optional[str]) -> Dict:
        """内置的确定性微任务生成逻辑，按对话关键词选择结构化结果。"""
        text = self._user_text(messages)

        keyword_tasks = {
            ("画", "设计", "美术", "手绘", "海报"): {
                "title": "做一次视觉创作练习",
                "description": "花 10 分钟临摹一张你喜欢的插画或海报，并写下你最想学会的一个技法。",
                "rationale": "用一个小产出验证你对视觉创作的持续投入感。",
                "estimated_minutes": 10,
                "growth_points": 10,
                "topic_tags": ["视觉设计"],
                "completion_criteria": ["完成一张临摹", "写下一个想学会的技法"],
                "reflection_prompt": "哪一步最让你投入，哪一步最困难？",
                "safety_notes": [],
            },
            ("游戏", "编程", "代码", "电脑"): {
                "title": "了解一个游戏开发案例",
                "description": "花 15 分钟了解一个游戏开发案例，并记下一个你想弄懂的问题。",
                "rationale": "用具体案例验证你更关注创意还是技术实现。",
                "estimated_minutes": 15,
                "growth_points": 10,
                "topic_tags": ["数字创作"],
                "completion_criteria": ["了解一个开发案例", "记下一个问题"],
                "reflection_prompt": "案例中哪一部分最让你想继续了解？",
                "safety_notes": [],
            },
            ("写", "文字", "故事", "作文"): {
                "title": "完成一段短写作",
                "description": "花 15 分钟写下一段 200 字的小故事或随笔，主题是你今天聊到的那件事。",
                "rationale": "用短写作验证你对文字表达的投入感。",
                "estimated_minutes": 15,
                "growth_points": 10,
                "topic_tags": ["文字表达"],
                "completion_criteria": ["完成约 200 字的文字"],
                "reflection_prompt": "写作过程中哪一部分最吸引你？",
                "safety_notes": [],
            },
            ("音乐", "唱", "乐器", "歌"): {
                "title": "拆解一首喜欢的音乐",
                "description": "花 10 分钟了解一首喜欢的音乐的创作背景，并写下最打动你的一处。",
                "rationale": "通过具体观察验证你对音乐表达的兴趣。",
                "estimated_minutes": 10,
                "growth_points": 10,
                "topic_tags": ["音乐表达"],
                "completion_criteria": ["了解创作背景", "写下最打动的一处"],
                "reflection_prompt": "最打动你的部分来自旋律、歌词还是表达方式？",
                "safety_notes": [],
            },
            ("运动", "球", "跑", "健身"): {
                "title": "完成一次短运动观察",
                "description": "今天花 15 分钟做一次你喜欢的运动，并记录运动后身体和心情的变化。",
                "rationale": "通过一次短实践观察你对这项运动的真实感受。",
                "estimated_minutes": 15,
                "growth_points": 10,
                "topic_tags": ["运动探索"],
                "completion_criteria": ["安全完成 15 分钟运动", "记录身体和心情变化"],
                "reflection_prompt": "运动后，你还愿意在什么条件下再试一次？",
                "safety_notes": ["选择适合自身状态的运动强度"],
            },
        }

        for keywords, task in keyword_tasks.items():
            if any(k in text for k in keywords):
                return task

        return {
            "title": "整理一个兴趣问题",
            "description": "花 10 分钟整理一个今天聊到的兴趣方向，并写下最想继续验证的一个问题。",
            "rationale": "先明确待验证的问题，避免在证据不足时仓促下结论。",
            "estimated_minutes": 10,
            "growth_points": 10,
            "topic_tags": ["兴趣探索"],
            "completion_criteria": ["写下一个具体兴趣方向", "写下一个待验证问题"],
            "reflection_prompt": "这个问题为什么值得你继续验证？",
            "safety_notes": [],
        }


deerflow_service = DeerFlowService()
