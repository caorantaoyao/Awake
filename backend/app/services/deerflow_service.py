import uuid
import logging
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
        return prompt

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

    async def chat(self, messages: List[Dict], student_name: Optional[str] = None) -> Dict:
        """多轮苏格拉底对话。

        入参 messages 为 [{"role": "user"/"assistant"/"system", "content": ...}]，
        不含 system prompt（由本方法注入）。返回 {"reply": str, "mode": "deerflow"/"mock"}。
        """
        if self.enabled:
            try:
                user_turns = sum(1 for m in messages if m.get("role") == "user")
                full_messages = [
                    {"role": "system", "content": self._build_system_prompt(student_name, user_turns)}
                ]
                full_messages.extend(messages)
                reply = await self._run_deerflow(full_messages)
                return {"reply": reply, "mode": "deerflow"}
            except Exception as e:
                logger.warning(f"DeerFlow chat 调用失败，降级到 mock: {e}")
                return {"reply": self._mock_socratic_reply(messages, student_name), "mode": "mock"}

        return {"reply": self._mock_socratic_reply(messages, student_name), "mode": "mock"}

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

    async def extract_task(self, messages: List[Dict], student_name: Optional[str] = None) -> str:
        """从对话历史提炼一条符合 SMART 原则的微行动任务描述字符串（不写库）。"""
        if self.enabled:
            try:
                system_prompt = (
                    self._build_system_prompt(student_name)
                    + "\n\n现在请仅输出一条今天就能完成的微行动任务描述，不超过 40 字，不要解释，不要加引号或前缀。"
                )
                full_messages = [{"role": "system", "content": system_prompt}]
                full_messages.extend(messages)
                full_messages.append({
                    "role": "user",
                    "content": "请根据以上对话，为我生成一个今天就能完成的微行动任务。",
                })
                task = await self._run_deerflow(full_messages)
                return task.strip()
            except Exception as e:
                logger.warning(f"DeerFlow extract_task 调用失败，降级到 mock: {e}")
                return self._mock_extract_task(messages, student_name)

        return self._mock_extract_task(messages, student_name)

    def _mock_extract_task(self, messages: List[Dict], student_name: Optional[str]) -> str:
        """内置的 mock 微任务生成逻辑，按对话关键词做简单选择。"""
        text = " ".join(
            m.get("content", "") for m in messages if m.get("role") == "user"
        )

        keyword_tasks = {
            ("画", "设计", "美术", "手绘"): "花 10 分钟临摹一张你喜欢的插画或海报，并写下你最想学会的一个技法。",
            ("写", "文字", "故事", "作文"): "花 15 分钟写下一段 200 字的小故事或随笔，主题是你今天聊到的那件事。",
            ("游戏", "编程", "代码", "电脑"): "花 15 分钟在 B 站看一个游戏是如何被开发出来的科普视频，并记下一个你想弄懂的问题。",
            ("音乐", "唱", "乐器", "歌"): "花 10 分钟听一首你喜欢的音乐并查一下它的创作背景，写下打动你的一句歌词。",
            ("运动", "球", "跑", "健身"): "今天花 15 分钟做一次你喜欢的运动，并记录运动后你身体和心情的变化。",
        }

        for keywords, task in keyword_tasks.items():
            if any(k in text for k in keywords):
                return task

        return "花 10 分钟在 B 站搜索一个你今天聊到的、感兴趣的方向，看一个科普视频，并记下你最有感触的一点。"


deerflow_service = DeerFlowService()
