import logging
from typing import Any, Dict, List, Optional
from urllib.parse import quote

import httpx

from app.core.config import settings
from app.schemas.schemas import (
    DeerFlowStatusResponse,
    ModelItem,
    ModelListResponse,
    SkillItem,
    SkillListResponse,
    SkillToggleResponse,
)

logger = logging.getLogger(__name__)


class DeerFlowControlService:
    """DeerFlow gateway 控制接口代理。

    控制台只需要读取 gateway 状态、skills、models，以及切换单个 skill。
    这里统一处理鉴权头、上游结构漂移和不可达降级，保证 FastAPI 路由拿到的是
    可序列化的响应模型，而不是向上抛出的网络异常。
    """

    def __init__(
        self,
        enabled: Optional[bool] = None,
        base_url: Optional[str] = None,
        assistant_id: Optional[str] = None,
        api_key: Optional[str] = None,
        timeout: Optional[float] = None,
    ):
        self.enabled = settings.DEERFLOW_ENABLED if enabled is None else enabled
        self.base_url = (base_url or settings.DEERFLOW_BASE_URL).rstrip("/")
        self.assistant_id = assistant_id or settings.DEERFLOW_ASSISTANT_ID
        self.api_key = settings.DEERFLOW_API_KEY if api_key is None else api_key
        self.timeout = settings.DEERFLOW_CONTROL_TIMEOUT_SECONDS if timeout is None else timeout

    def _headers(self) -> Dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    async def _request_json(
        self,
        method: str,
        path: str,
        body: Optional[Dict[str, Any]] = None,
    ) -> Any:
        url = f"{self.base_url}{path}"
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.request(
                method,
                url,
                json=body,
                headers=self._headers(),
            )
            response.raise_for_status()
            if not response.content:
                return {}
            return response.json()

    def _disabled_error(self) -> str:
        return "DeerFlow 未启用"

    @staticmethod
    def _error_message(exc: Exception) -> str:
        if isinstance(exc, httpx.HTTPStatusError):
            return f"DeerFlow 返回 HTTP {exc.response.status_code}"
        return "DeerFlow 不可达"

    @staticmethod
    def _raw_payload(data: Any) -> Dict[str, Any]:
        return data if isinstance(data, dict) else {"data": data}

    @staticmethod
    def _coerce_bool(value: Any) -> Optional[bool]:
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            lowered = value.strip().lower()
            if lowered in {"true", "1", "yes", "on", "enabled"}:
                return True
            if lowered in {"false", "0", "no", "off", "disabled"}:
                return False
        return None

    def _extract_collection(self, data: Any, keys: List[str]) -> List[Any]:
        if isinstance(data, list):
            return data
        if not isinstance(data, dict):
            return []

        for key in keys:
            value = data.get(key)
            if isinstance(value, list):
                return value
            if isinstance(value, dict):
                nested = self._extract_collection(value, keys)
                if nested:
                    return nested

        mapped_items = []
        for key, value in data.items():
            if isinstance(value, dict):
                mapped_items.append({"name": key, **value})
            elif isinstance(value, (str, bool)):
                mapped_items.append({"name": key, "value": value})
        return mapped_items

    def _normalize_skill(self, item: Any, fallback_name: Optional[str] = None) -> Optional[SkillItem]:
        if isinstance(item, str):
            return SkillItem(name=item, raw={"value": item})
        if not isinstance(item, dict):
            return None

        name = (
            item.get("name")
            or item.get("id")
            or item.get("key")
            or item.get("skill")
            or fallback_name
        )
        if not name:
            return None

        enabled = self._coerce_bool(item.get("enabled"))
        if enabled is None:
            disabled = self._coerce_bool(item.get("disabled"))
            enabled = not disabled if disabled is not None else None

        description = item.get("description") or item.get("desc") or item.get("label")
        return SkillItem(
            name=str(name),
            description=str(description) if description is not None else None,
            enabled=enabled,
            raw=item,
        )

    def _normalize_skills(self, data: Any) -> List[SkillItem]:
        items = self._extract_collection(data, ["skills", "data", "items", "tools"])
        skills = []
        for index, item in enumerate(items):
            fallback_name = f"skill_{index + 1}"
            skill = self._normalize_skill(item, fallback_name=fallback_name)
            if skill:
                skills.append(skill)
        return skills

    def _normalize_model(self, item: Any, fallback_id: Optional[str] = None) -> Optional[ModelItem]:
        if isinstance(item, str):
            return ModelItem(id=item, name=item, raw={"value": item})
        if not isinstance(item, dict):
            return None

        model_id = (
            item.get("id")
            or item.get("model")
            or item.get("name")
            or item.get("key")
            or fallback_id
        )
        if not model_id:
            return None

        name = item.get("name") or item.get("label") or model_id
        provider = item.get("provider") or item.get("type") or item.get("source")
        return ModelItem(
            id=str(model_id),
            name=str(name) if name is not None else None,
            provider=str(provider) if provider is not None else None,
            raw=item,
        )

    def _normalize_models(self, data: Any) -> List[ModelItem]:
        items = self._extract_collection(
            data,
            ["models", "data", "items", "available_models", "model_list"],
        )
        models = []
        for index, item in enumerate(items):
            fallback_id = f"model_{index + 1}"
            model = self._normalize_model(item, fallback_id=fallback_id)
            if model:
                models.append(model)
        return models

    def _extract_current_model(self, data: Any, models: List[ModelItem]) -> Optional[str]:
        if isinstance(data, dict):
            for key in ("current_model", "default_model", "selected_model", "model"):
                value = data.get(key)
                if isinstance(value, str) and value:
                    return value
                if isinstance(value, dict):
                    model = self._normalize_model(value)
                    if model:
                        return model.id
        if models:
            return models[0].id
        return None

    def _status_fallback(self, error: str) -> DeerFlowStatusResponse:
        return DeerFlowStatusResponse(
            online=False,
            assistant_id=self.assistant_id,
            model=None,
            error=error,
        )

    def _skill_list_fallback(self, error: str) -> SkillListResponse:
        return SkillListResponse(online=False, skills=[], error=error)

    def _model_list_fallback(self, error: str) -> ModelListResponse:
        return ModelListResponse(online=False, models=[], error=error)

    def _skill_toggle_fallback(self, name: str, error: str) -> SkillToggleResponse:
        return SkillToggleResponse(
            online=False,
            skill=SkillItem(name=name, enabled=None),
            error=error,
        )

    async def get_status(self) -> DeerFlowStatusResponse:
        if not self.enabled:
            return self._status_fallback(self._disabled_error())

        try:
            data = await self._request_json("GET", "/api/models")
            models = self._normalize_models(data)
            return DeerFlowStatusResponse(
                online=True,
                assistant_id=self.assistant_id,
                model=self._extract_current_model(data, models),
                raw=self._raw_payload(data),
            )
        except Exception as exc:
            logger.warning("DeerFlow status 查询失败，返回离线降级: %s", exc)
            return self._status_fallback(self._error_message(exc))

    async def list_skills(self) -> SkillListResponse:
        if not self.enabled:
            return self._skill_list_fallback(self._disabled_error())

        try:
            data = await self._request_json("GET", "/api/skills")
            return SkillListResponse(
                online=True,
                skills=self._normalize_skills(data),
                raw=self._raw_payload(data),
            )
        except Exception as exc:
            logger.warning("DeerFlow skills 查询失败，返回离线降级: %s", exc)
            return self._skill_list_fallback(self._error_message(exc))

    async def set_skill_enabled(self, name: str, enabled: bool) -> SkillToggleResponse:
        if not self.enabled:
            return self._skill_toggle_fallback(name, self._disabled_error())

        try:
            encoded_name = quote(name, safe="")
            data = await self._request_json(
                "PUT",
                f"/api/skills/{encoded_name}",
                body={"enabled": enabled},
            )
            skill = self._normalize_skill(data, fallback_name=name)
            if skill is None:
                skill = SkillItem(name=name, enabled=enabled, raw=self._raw_payload(data))
            elif skill.enabled is None:
                skill.enabled = enabled
            return SkillToggleResponse(
                online=True,
                skill=skill,
                raw=self._raw_payload(data),
            )
        except Exception as exc:
            logger.warning("DeerFlow skill 开关失败，返回离线降级: %s", exc)
            return self._skill_toggle_fallback(name, self._error_message(exc))

    async def list_models(self) -> ModelListResponse:
        if not self.enabled:
            return self._model_list_fallback(self._disabled_error())

        try:
            data = await self._request_json("GET", "/api/models")
            return ModelListResponse(
                online=True,
                models=self._normalize_models(data),
                raw=self._raw_payload(data),
            )
        except Exception as exc:
            logger.warning("DeerFlow models 查询失败，返回离线降级: %s", exc)
            return self._model_list_fallback(self._error_message(exc))


deerflow_control_service = DeerFlowControlService()
