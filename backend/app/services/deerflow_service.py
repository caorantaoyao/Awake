import json
import logging
import uuid
from typing import Any, AsyncGenerator, Dict, List, Optional

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)


class DeerFlowUnavailable(Exception):
    """DeerFlow 引擎不可达时抛出。"""
    def __init__(self, detail: str = "DeerFlow 对话引擎未启动或不可达"):
        self.detail = detail
        super().__init__(detail)


class DeerFlowService:
    """DeerFlow 2.0 对话引擎适配层。

    职责：
    - SSE 流式对话：stream_chat() async generator，yield 结构化事件
    - Thread 生命周期：create / delete / get_messages
    - 运行时参数透传：model_name / thinking_enabled / is_plan_mode
    - 能力查询：list_models / list_skills / set_skill_enabled / get_status
    - 微行动提取：extract_task() 独立 JSON 请求
    - DeerFlow 不可达时抛出 DeerFlowUnavailable，不做 mock 伪装
    """

    def __init__(self):
        self.enabled = settings.DEERFLOW_ENABLED
        self.base_url = settings.DEERFLOW_BASE_URL.rstrip("/")
        self.assistant_id = settings.DEERFLOW_ASSISTANT_ID
        self.api_key = settings.DEERFLOW_API_KEY
        self.timeout = 120.0
        self.stream_timeout = 300.0

    def _check_enabled(self) -> None:
        if not self.enabled:
            raise DeerFlowUnavailable("DeerFlow 未启用（设置 DEERFLOW_ENABLED=true）")

    def _headers(self, extra: Optional[Dict[str, str]] = None) -> Dict[str, str]:
        h = {"Content-Type": "application/json"}
        if self.api_key:
            h["Authorization"] = f"Bearer {self.api_key}"
        if extra:
            h.update(extra)
        return h

    def _build_system_prompt(
        self,
        student_name: Optional[str],
        user_turns: int = 0,
        unlock_after_turns: Optional[int] = None,
        chat_mode: Optional[str] = None,
        student_profile: Optional[Dict[str, Any]] = None,
    ) -> str:
        prompt = settings.XIAOHAI_PERSONA_PROMPT
        if student_name:
            prompt = f"{prompt}\n\n学生的名字是 {student_name}。"

        if student_profile:
            profile_lines = []
            interests = student_profile.get("interest_tags") or []
            abilities = student_profile.get("ability_tags") or []
            confusion = student_profile.get("confusion")
            exploration_stage = student_profile.get("exploration_stage")
            if interests:
                profile_lines.append(f"学生感兴趣的方向：{', '.join(interests)}。")
            if confusion:
                profile_lines.append(f"学生目前最想搞清楚的是：{confusion}。")
            if abilities:
                style_map = {
                    "视觉学习": "偏好看视频/图解等视觉方式学习",
                    "阅读学习": "偏好通过阅读文章和书籍学习",
                    "实践学习": "偏好动手做项目、边做边学",
                    "交流学习": "偏好通过与人聊天讨论来学习",
                }
                style_desc = ", ".join(style_map.get(a, a) for a in abilities if a in style_map)
                if style_desc:
                    profile_lines.append(f"学生的学习偏好：{style_desc}。")
            if exploration_stage and exploration_stage != "探索中":
                profile_lines.append(f"当前探索阶段：{exploration_stage}。")
            if profile_lines:
                prompt = f"{prompt}\n\n【学生画像】\n" + "\n".join(profile_lines)
                prompt = (
                    f"{prompt}\n请在对话中自然地引用这些信息——"
                    "比如当学生提到相关方向时表现出你知道他/她的兴趣，"
                    "在推荐行动时优先匹配他/她的学习偏好，但不要生硬地罗列标签。"
                )

        threshold = unlock_after_turns or settings.XIAOHAI_UNLOCK_AFTER_TURNS
        mode = chat_mode or "explore_first"
        if mode == "direct_action":
            prompt = f"{prompt}\n\n【对话风格】学生偏好直接给出方向和建议，不需要过多追问。"
            threshold = max(1, threshold - 1)
        elif mode == "balanced":
            prompt = f"{prompt}\n\n【对话风格】保持探索与行动之间的平衡，适时追问也适时给出建议。"
        if user_turns >= threshold:
            prompt = f"{prompt}{settings.XIAOHAI_UNLOCK_PROMPT}"
        else:
            prompt = f"{prompt}{settings.XIAOHAI_EXPLORE_PROMPT}"
        return prompt

    def _build_run_body(
        self,
        messages: List[Dict],
        student_name: Optional[str] = None,
        thread_id: Optional[str] = None,
        user_turns: int = 0,
        unlock_after_turns: Optional[int] = None,
        chat_mode: Optional[str] = None,
        model_name: Optional[str] = None,
        thinking_enabled: bool = False,
        is_plan_mode: bool = False,
        student_profile: Optional[Dict[str, Any]] = None,
        file_ids: Optional[List[str]] = None,
    ) -> Dict:
        system_prompt = self._build_system_prompt(
            student_name, user_turns, unlock_after_turns, chat_mode, student_profile,
        )
        full_messages = [{"role": "system", "content": system_prompt}]
        full_messages.extend(messages)

        config: Dict[str, Any] = {"configurable": {}}
        if thread_id:
            config["configurable"]["thread_id"] = thread_id
        if file_ids:
            config["configurable"]["file_ids"] = file_ids

        context: Dict[str, Any] = {}
        if model_name:
            context["model_name"] = model_name
        if thinking_enabled:
            context["thinking_enabled"] = True
        if is_plan_mode:
            context["is_plan_mode"] = True

        body: Dict[str, Any] = {
            "assistant_id": self.assistant_id,
            "input": {"messages": full_messages},
            "config": config,
            "stream_mode": ["messages-tuple"],
        }
        if context:
            body["context"] = context
        return body

    async def create_thread(self) -> str:
        self._check_enabled()
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.post(
                    f"{self.base_url}/api/threads",
                    json={},
                    headers=self._headers(),
                )
                resp.raise_for_status()
                data = resp.json()
                tid = data.get("thread_id")
                if not tid:
                    raise DeerFlowUnavailable("DeerFlow 创建 thread 未返回 thread_id")
                return str(tid)
        except httpx.HTTPError as e:
            logger.warning(f"DeerFlow create_thread HTTP 失败: {e}")
            raise DeerFlowUnavailable(f"DeerFlow 创建 thread 失败: {e}") from e
        except Exception as e:
            logger.warning(f"DeerFlow create_thread 失败: {e}")
            raise DeerFlowUnavailable(str(e)) from e

    async def delete_thread(self, thread_id: str) -> None:
        self._check_enabled()
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.request(
                    "DELETE",
                    f"{self.base_url}/api/threads/{thread_id}",
                    headers=self._headers(),
                )
                resp.raise_for_status()
        except httpx.HTTPError as e:
            logger.warning(f"DeerFlow delete_thread 失败: {e}")
            raise DeerFlowUnavailable(f"删除 thread 失败: {e}") from e

    async def get_thread_messages(
        self, thread_id: str, limit: int = 100
    ) -> List[Dict]:
        self._check_enabled()
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.post(
                    f"{self.base_url}/api/threads/{thread_id}/history",
                    json={"limit": limit},
                    headers=self._headers(),
                )
                resp.raise_for_status()
                data = resp.json()
                messages: List[Dict] = []
                if isinstance(data, list):
                    seen_user: set = set()
                    for entry in data:
                        if not isinstance(entry, dict):
                            continue
                        for msg in entry.get("values", {}).get("messages", []):
                            role = msg.get("type") or msg.get("role")
                            if role in ("human", "user"):
                                role = "user"
                            elif role in ("ai", "assistant"):
                                role = "assistant"
                            else:
                                continue
                            content = msg.get("content", "")
                            if isinstance(content, list):
                                content = "".join(
                                    b.get("text", "")
                                    for b in content
                                    if isinstance(b, dict) and b.get("type") == "text"
                                )
                            if isinstance(content, str) and content.strip():
                                stripped = content.strip()
                                if stripped.startswith("<memory>") or stripped.startswith("<system-"):
                                    continue
                                if stripped.startswith("<") and "</" in stripped[:200]:
                                    continue
                                key = (role, stripped[:80])
                                if role == "user":
                                    if key in seen_user:
                                        continue
                                    seen_user.add(key)
                                messages.append({"role": role, "content": stripped})
                return messages
        except httpx.HTTPError as e:
            logger.warning(f"DeerFlow get_thread_messages 失败: {e}")
            raise DeerFlowUnavailable(f"获取 thread 消息失败: {e}") from e

    async def stream_chat(
        self,
        messages: List[Dict],
        student_name: Optional[str] = None,
        thread_id: Optional[str] = None,
        unlock_after_turns: Optional[int] = None,
        chat_mode: Optional[str] = None,
        model_name: Optional[str] = None,
        thinking_enabled: bool = False,
        is_plan_mode: bool = False,
        student_profile: Optional[Dict[str, Any]] = None,
        file_ids: Optional[List[str]] = None,
    ) -> AsyncGenerator[Dict, None]:
        """SSE 流式对话。

        yield 事件类型：
        - {"type": "meta", "thread_id": str}
        - {"type": "text", "content": str}
        - {"type": "tool", "name": str, "input": dict}
        - {"type": "thinking", "content": str}
        - {"type": "plan", "steps": list}
        - {"type": "artifact", "artifact": dict}
        - {"type": "done", "reply": str, "thread_id": str}
        - {"type": "error", "message": str}
        """
        self._check_enabled()
        user_turns = sum(1 for m in messages if m.get("role") == "user")
        effective_thread_id = thread_id
        body = self._build_run_body(
            messages, student_name, effective_thread_id,
            user_turns, unlock_after_turns, chat_mode,
            model_name, thinking_enabled, is_plan_mode,
            student_profile=student_profile,
            file_ids=file_ids,
        )

        try:
            async with httpx.AsyncClient(timeout=self.stream_timeout) as client:
                if effective_thread_id:
                    url = f"{self.base_url}/api/threads/{effective_thread_id}/runs/stream"
                else:
                    url = f"{self.base_url}/api/runs/stream"
                async with client.stream(
                    "POST", url, json=body, headers=self._headers()
                ) as resp:
                    resp.raise_for_status()

                    content_location = resp.headers.get("content-location", "")
                    if not effective_thread_id and "/threads/" in content_location:
                        parts = content_location.split("/threads/")[-1].split("/")
                        if parts:
                            effective_thread_id = parts[0]

                    yield {"type": "meta", "thread_id": effective_thread_id or ""}

                    full_reply_parts: List[str] = []
                    full_thinking_parts: List[str] = []
                    current_tool_names: Dict[int, str] = {}
                    artifacts: List[Dict] = []
                    plan_steps: List[Dict] = []
                    async for raw_line in resp.aiter_lines():
                        if not raw_line or raw_line.startswith("event:"):
                            continue
                        if not raw_line.startswith("data:"):
                            continue
                        data_str = raw_line[5:].strip()
                        if not data_str or data_str == "[DONE]":
                            continue
                        try:
                            event = json.loads(data_str)
                        except json.JSONDecodeError:
                            continue

                        if not isinstance(event, list):
                            continue

                        for msg in event:
                            if not isinstance(msg, dict):
                                continue
                            msg_type = msg.get("type")
                            content = msg.get("content", "")
                            tool_call_chunks = msg.get("tool_call_chunks") or []
                            additional_kwargs = msg.get("additional_kwargs") or {}

                            if msg_type == "AIMessageChunk":
                                chunk_text = ""
                                chunk_thinking = ""
                                if isinstance(content, str):
                                    chunk_text = content
                                elif isinstance(content, list):
                                    for block in content:
                                        if not isinstance(block, dict):
                                            continue
                                        block_type = block.get("type", "")
                                        if block_type == "text":
                                            chunk_text += block.get("text", "")
                                        elif block_type == "thinking" or block_type == "reasoning":
                                            chunk_thinking += block.get("thinking", "") or block.get("text", "")

                                if chunk_thinking:
                                    full_thinking_parts.append(chunk_thinking)
                                    yield {"type": "thinking", "content": chunk_thinking}

                                if chunk_text:
                                    full_reply_parts.append(chunk_text)
                                    yield {"type": "text", "content": chunk_text}

                                for tcc in tool_call_chunks:
                                    if not isinstance(tcc, dict):
                                        continue
                                    idx = tcc.get("index", 0)
                                    name = tcc.get("name")
                                    args = tcc.get("args", "")
                                    if name:
                                        current_tool_names[idx] = name
                                    if args and idx in current_tool_names:
                                        try:
                                            parsed_args = json.loads(args) if args.strip().startswith("{") else args
                                        except json.JSONDecodeError:
                                            parsed_args = args
                                        tool_name = current_tool_names[idx]
                                        yield {
                                            "type": "tool",
                                            "name": tool_name,
                                            "input": parsed_args,
                                        }
                                        if tool_name in ("write_report", "create_artifact", "generate_plan") and isinstance(parsed_args, dict):
                                            if "steps" in parsed_args and isinstance(parsed_args["steps"], list):
                                                plan_steps = parsed_args["steps"]
                                                yield {"type": "plan", "steps": plan_steps}
                                            if "artifact_path" in parsed_args or "filename" in parsed_args:
                                                artifact_url = self.build_artifact_url(
                                                    effective_thread_id or "",
                                                    parsed_args.get("artifact_path") or parsed_args.get("filename", "")
                                                )
                                                artifact_info = {
                                                    "name": parsed_args.get("title") or parsed_args.get("filename", "产出物"),
                                                    "path": parsed_args.get("artifact_path") or parsed_args.get("filename", ""),
                                                    "url": artifact_url,
                                                    "type": parsed_args.get("type", "document"),
                                                }
                                                artifacts.append(artifact_info)
                                                yield {"type": "artifact", "artifact": artifact_info}

                            artifact_data = additional_kwargs.get("artifact") or msg.get("artifact")
                            if artifact_data and isinstance(artifact_data, dict):
                                artifact_path = artifact_data.get("path") or artifact_data.get("artifact_path", "")
                                artifact_url = self.build_artifact_url(effective_thread_id or "", artifact_path)
                                artifact_info = {
                                    "name": artifact_data.get("name") or artifact_data.get("title", "产出物"),
                                    "path": artifact_path,
                                    "url": artifact_url,
                                    "type": artifact_data.get("type", "document"),
                                }
                                if not any(a["path"] == artifact_path for a in artifacts):
                                    artifacts.append(artifact_info)
                                    yield {"type": "artifact", "artifact": artifact_info}

                    yield {
                        "type": "done",
                        "reply": "".join(full_reply_parts).strip(),
                        "thinking": "".join(full_thinking_parts).strip(),
                        "artifacts": artifacts,
                        "plan_steps": plan_steps,
                        "thread_id": effective_thread_id or "",
                    }

        except httpx.HTTPStatusError as e:
            logger.warning(f"DeerFlow stream_chat HTTP {e.response.status_code}")
            yield {"type": "error", "message": f"DeerFlow 返回错误 (HTTP {e.response.status_code})"}
        except (httpx.ConnectError, httpx.ConnectTimeout) as e:
            logger.warning(f"DeerFlow stream_chat 连接失败: {e}")
            yield {"type": "error", "message": "无法连接到 DeerFlow 引擎，请确认服务已启动"}
        except Exception as e:
            logger.warning(f"DeerFlow stream_chat 失败: {e}")
            yield {"type": "error", "message": f"对话流出错: {e}"}

    async def chat(
        self,
        messages: List[Dict],
        student_name: Optional[str] = None,
        thread_id: Optional[str] = None,
        unlock_after_turns: Optional[int] = None,
        chat_mode: Optional[str] = None,
        model_name: Optional[str] = None,
        thinking_enabled: bool = False,
        is_plan_mode: bool = False,
        student_profile: Optional[Dict[str, Any]] = None,
    ) -> Dict:
        """一次性收集完整回复（非流式）。"""
        full_parts: List[str] = []
        final_tid = thread_id
        error_msg: Optional[str] = None
        async for ev in self.stream_chat(
            messages, student_name, thread_id,
            unlock_after_turns, chat_mode,
            model_name, thinking_enabled, is_plan_mode,
            student_profile=student_profile,
        ):
            if ev["type"] == "text":
                full_parts.append(ev["content"])
            elif ev["type"] == "meta" and not final_tid:
                final_tid = ev.get("thread_id")
            elif ev["type"] == "done":
                final_tid = ev.get("thread_id", final_tid)
            elif ev["type"] == "error":
                error_msg = ev["message"]
        if error_msg and not full_parts:
            raise DeerFlowUnavailable(error_msg)
        return {
            "reply": "".join(full_parts).strip(),
            "mode": "deerflow",
            "thread_id": final_tid,
        }

    async def extract_task(
        self,
        messages: List[Dict],
        student_name: Optional[str] = None,
        unlock_after_turns: Optional[int] = None,
        chat_mode: Optional[str] = None,
        thread_id: Optional[str] = None,
        model_name: Optional[str] = None,
        student_profile: Optional[Dict[str, Any]] = None,
    ) -> Dict:
        """从对话中提炼结构化微行动。"""
        user_turns = sum(1 for m in messages if m.get("role") == "user")
        threshold = unlock_after_turns or settings.XIAOHAI_UNLOCK_AFTER_TURNS
        if user_turns < threshold:
            raise DeerFlowUnavailable(f"需要至少 {threshold} 轮对话才能提炼任务")

        extract_prompt = (
            "基于以上对话，生成一个今天就能完成的微行动任务。"
            "严格只输出一个 JSON 对象，不要 Markdown 围栏：\n"
            "{\n"
            '  "title": "任务标题（15字内）",\n'
            '  "description": "具体要做什么（50字内）",\n'
            '  "rationale": "为什么推荐（50字内）",\n'
            '  "estimated_minutes": 15,\n'
            '  "growth_points": 10,\n'
            '  "topic_tags": ["标签1"],\n'
            '  "completion_criteria": ["完成标准1", "完成标准2"],\n'
            '  "reflection_prompt": "完成后反思问题",\n'
            '  "safety_notes": []\n'
            "}\n"
            "estimated_minutes 为 5-30 的整数，growth_points 为 1-100 的整数。"
        )
        task_messages = list(messages) + [{"role": "user", "content": extract_prompt}]

        result = await self.chat(
            task_messages, student_name,
            thread_id=thread_id,
            unlock_after_turns=unlock_after_turns,
            chat_mode=chat_mode,
            model_name=model_name,
            student_profile=student_profile,
        )
        text = result["reply"]
        json_start = text.find("{")
        json_end = text.rfind("}")
        if json_start < 0 or json_end <= json_start:
            raise DeerFlowUnavailable("AI 未能返回有效的任务 JSON")
        data = json.loads(text[json_start:json_end + 1])
        return {
            "title": str(data.get("title", "探索兴趣"))[:80],
            "description": str(data.get("description", ""))[:500],
            "rationale": str(data.get("rationale", ""))[:300],
            "estimated_minutes": self._clamp_int(data.get("estimated_minutes", 15), 5, 30, 15),
            "growth_points": self._clamp_int(data.get("growth_points", 10), 1, 100, 10),
            "topic_tags": self._ensure_str_list(data.get("topic_tags"), ["兴趣探索"]),
            "completion_criteria": self._ensure_str_list(data.get("completion_criteria"), ["完成任务"]),
            "reflection_prompt": str(data.get("reflection_prompt", "这次尝试给你什么启发？"))[:200],
            "safety_notes": self._ensure_str_list(data.get("safety_notes"), []),
        }

    @staticmethod
    def _clamp_int(v: Any, lo: int, hi: int, default: int) -> int:
        try:
            return max(lo, min(hi, int(v)))
        except (TypeError, ValueError):
            return default

    @staticmethod
    def _ensure_str_list(v: Any, default: List[str]) -> List[str]:
        if not isinstance(v, list):
            return default
        return [str(x).strip() for x in v if isinstance(x, (str, int, float)) and str(x).strip()] or default

    async def list_models(self) -> List[Dict]:
        self._check_enabled()
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(
                    f"{self.base_url}/api/models", headers=self._headers()
                )
                resp.raise_for_status()
                return resp.json().get("models", [])
        except Exception as e:
            logger.warning(f"DeerFlow list_models 失败: {e}")
            raise DeerFlowUnavailable(f"获取模型列表失败: {e}") from e

    async def list_skills(self) -> List[Dict]:
        self._check_enabled()
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(
                    f"{self.base_url}/api/skills", headers=self._headers()
                )
                resp.raise_for_status()
                return resp.json().get("skills", [])
        except Exception as e:
            logger.warning(f"DeerFlow list_skills 失败: {e}")
            raise DeerFlowUnavailable(f"获取技能列表失败: {e}") from e

    async def set_skill_enabled(self, name: str, enabled: bool) -> None:
        self._check_enabled()
        endpoint = "enable" if enabled else "disable"
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(
                    f"{self.base_url}/api/skills/{name}/{endpoint}",
                    headers=self._headers(),
                )
                resp.raise_for_status()
        except Exception as e:
            logger.warning(f"DeerFlow set_skill_enabled 失败: {e}")
            raise DeerFlowUnavailable(f"切换技能失败: {e}") from e

    async def get_status(self) -> Dict:
        if not self.enabled:
            return {"online": False, "error": "未启用"}
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(
                    f"{self.base_url}/api/models", headers=self._headers()
                )
                resp.raise_for_status()
                models = resp.json().get("models", [])
                return {
                    "online": True,
                    "assistant_id": self.assistant_id,
                    "models_count": len(models),
                    "current_model": models[0]["name"] if models else None,
                    "models": models,
                }
        except Exception as e:
            return {"online": False, "error": str(e)}

    async def get_suggestions(self, messages: List[Dict], model_name: Optional[str] = None) -> List[str]:
        self._check_enabled()
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.post(
                    f"{self.base_url}/api/suggestions",
                    json={"messages": messages, "model": model_name},
                    headers=self._headers(),
                )
                resp.raise_for_status()
                data = resp.json()
                return [str(s) for s in data.get("suggestions", []) if isinstance(s, str)][:4]
        except Exception as e:
            logger.warning(f"DeerFlow suggestions 失败: {e}")
            return []

    async def upload_files(
        self, thread_id: str, files: List[tuple]
    ) -> List[Dict]:
        """上传文件到 DeerFlow thread。files: [(filename, content_bytes, content_type)]"""
        self._check_enabled()
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                form_files = []
                for fname, fbytes, ctype in files:
                    form_files.append(("files", (fname, fbytes, ctype)))
                resp = await client.post(
                    f"{self.base_url}/api/threads/{thread_id}/uploads",
                    files=form_files,
                    headers=self._headers({"Content-Type": None}) if self.api_key else {},
                )
                resp.raise_for_status()
                data = resp.json()
                return data.get("files", [])
        except Exception as e:
            logger.warning(f"DeerFlow upload_files 失败: {e}")
            raise DeerFlowUnavailable(f"文件上传失败: {e}") from e

    def build_artifact_url(self, thread_id: str, artifact_path: str) -> str:
        return f"{self.base_url}/api/threads/{thread_id}/artifacts/{artifact_path.lstrip('/')}"

    async def get_artifact(self, thread_id: str, artifact_path: str) -> tuple:
        """获取 artifact 文件内容，返回 (content_bytes, content_type)"""
        self._check_enabled()
        url = self.build_artifact_url(thread_id, artifact_path)
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.get(url, headers=self._headers())
                resp.raise_for_status()
                content_type = resp.headers.get("content-type", "application/octet-stream")
                return resp.content, content_type
        except Exception as e:
            logger.warning(f"DeerFlow get_artifact 失败: {e}")
            raise DeerFlowUnavailable(f"获取产出物失败: {e}") from e

    async def list_artifacts(self, thread_id: str) -> List[Dict]:
        """列出 thread 下的所有 artifacts"""
        self._check_enabled()
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(
                    f"{self.base_url}/api/threads/{thread_id}/artifacts",
                    headers=self._headers(),
                )
                resp.raise_for_status()
                data = resp.json()
                artifacts = data.get("artifacts", [])
                for a in artifacts:
                    if "path" in a:
                        a["url"] = self.build_artifact_url(thread_id, a["path"])
                return artifacts
        except Exception as e:
            logger.warning(f"DeerFlow list_artifacts 失败: {e}")
            return []

    async def submit_feedback(
        self, thread_id: str, run_id: str, rating: Optional[str] = None, comment: Optional[str] = None
    ) -> Dict:
        """提交消息反馈"""
        self._check_enabled()
        body: Dict[str, Any] = {}
        if rating is not None:
            body["rating"] = rating
        if comment is not None:
            body["comment"] = comment
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.put(
                    f"{self.base_url}/api/threads/{thread_id}/runs/{run_id}/feedback",
                    json=body,
                    headers=self._headers(),
                )
                resp.raise_for_status()
                return resp.json()
        except Exception as e:
            logger.warning(f"DeerFlow submit_feedback 失败: {e}")
            raise DeerFlowUnavailable(f"提交反馈失败: {e}") from e

    async def polish_input(self, text: str) -> str:
        """润色用户输入"""
        self._check_enabled()
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.post(
                    f"{self.base_url}/api/input-polish",
                    json={"text": text},
                    headers=self._headers(),
                )
                resp.raise_for_status()
                data = resp.json()
                return data.get("polished_text") or data.get("text") or text
        except Exception as e:
            logger.warning(f"DeerFlow polish_input 失败: {e}")
            return text

    async def list_mcp_servers(self) -> List[Dict]:
        """列出 MCP 服务器"""
        self._check_enabled()
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(
                    f"{self.base_url}/api/mcp",
                    headers=self._headers(),
                )
                resp.raise_for_status()
                data = resp.json()
                return data.get("servers", [])
        except Exception as e:
            logger.warning(f"DeerFlow list_mcp_servers 失败: {e}")
            return []

    async def list_runs(self, thread_id: Optional[str] = None) -> List[Dict]:
        """列出 run 历史"""
        self._check_enabled()
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                if thread_id:
                    url = f"{self.base_url}/api/threads/{thread_id}/runs"
                else:
                    url = f"{self.base_url}/api/runs"
                resp = await client.get(url, headers=self._headers())
                resp.raise_for_status()
                data = resp.json()
                return data.get("runs", [])
        except Exception as e:
            logger.warning(f"DeerFlow list_runs 失败: {e}")
            return []

    async def list_scheduled_tasks(self) -> List[Dict]:
        """列出定时任务"""
        self._check_enabled()
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(
                    f"{self.base_url}/api/scheduled-tasks",
                    headers=self._headers(),
                )
                resp.raise_for_status()
                data = resp.json()
                return data.get("tasks", [])
        except Exception as e:
            logger.warning(f"DeerFlow list_scheduled_tasks 失败: {e}")
            return []

    async def create_scheduled_task(self, task_data: Dict) -> Dict:
        """创建定时任务"""
        self._check_enabled()
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(
                    f"{self.base_url}/api/scheduled-tasks",
                    json=task_data,
                    headers=self._headers(),
                )
                resp.raise_for_status()
                return resp.json()
        except Exception as e:
            logger.warning(f"DeerFlow create_scheduled_task 失败: {e}")
            raise DeerFlowUnavailable(f"创建定时任务失败: {e}") from e


deerflow_service = DeerFlowService()
