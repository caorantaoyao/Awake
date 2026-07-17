import httpx
import pytest

from app.services.deerflow_control import DeerFlowControlService
from app.services import deerflow_control


class FailingAsyncClient:
    def __init__(self, *args, **kwargs):
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, traceback):
        return False

    async def request(self, *args, **kwargs):
        raise httpx.ConnectError("gateway unavailable")


def _unreachable_service():
    return DeerFlowControlService(
        enabled=True,
        base_url="http://deerflow.local",
        assistant_id="lead_agent",
        api_key="test-token",
        timeout=0.01,
    )


def test_deerflow_control_timeout_defaults_to_config(monkeypatch):
    monkeypatch.setattr(
        deerflow_control.settings,
        "DEERFLOW_CONTROL_TIMEOUT_SECONDS",
        42.0,
    )

    service = DeerFlowControlService(
        enabled=True,
        base_url="http://deerflow.local",
        assistant_id="lead_agent",
        api_key="test-token",
    )

    assert service.timeout == 42.0


@pytest.mark.asyncio
async def test_status_falls_back_when_deerflow_unreachable(monkeypatch):
    monkeypatch.setattr("app.services.deerflow_control.httpx.AsyncClient", FailingAsyncClient)

    result = await _unreachable_service().get_status()

    assert result.online is False
    assert result.assistant_id == "lead_agent"
    assert result.model is None
    assert result.error


@pytest.mark.asyncio
async def test_skills_fall_back_when_deerflow_unreachable(monkeypatch):
    monkeypatch.setattr("app.services.deerflow_control.httpx.AsyncClient", FailingAsyncClient)

    result = await _unreachable_service().list_skills()

    assert result.online is False
    assert result.skills == []
    assert result.error


@pytest.mark.asyncio
async def test_models_fall_back_when_deerflow_unreachable(monkeypatch):
    monkeypatch.setattr("app.services.deerflow_control.httpx.AsyncClient", FailingAsyncClient)

    result = await _unreachable_service().list_models()

    assert result.online is False
    assert result.models == []
    assert result.error


@pytest.mark.asyncio
async def test_skill_toggle_falls_back_when_deerflow_unreachable(monkeypatch):
    monkeypatch.setattr("app.services.deerflow_control.httpx.AsyncClient", FailingAsyncClient)

    result = await _unreachable_service().set_skill_enabled("search", True)

    assert result.online is False
    assert result.skill.name == "search"
    assert result.skill.enabled is None
    assert result.error


@pytest.mark.parametrize(
    ("method", "path", "json"),
    [
        ("put", "/api/deerflow/skills/search", {"enabled": True}),
    ],
)
def test_deerflow_control_write_endpoints_require_authentication(
    client,
    method,
    path,
    json,
):
    response = client.request(method, path, json=json)

    assert response.status_code == 401


@pytest.mark.parametrize(
    ("method", "path"),
    [
        ("get", "/api/deerflow/status"),
        ("get", "/api/deerflow/skills"),
        ("get", "/api/deerflow/models"),
    ],
)
def test_deerflow_read_endpoints_do_not_require_authentication(
    client,
    method,
    path,
):
    response = client.request(method, path)

    assert response.status_code != 401
