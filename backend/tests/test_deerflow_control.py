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


def test_deerflow_control_endpoints_return_offline_fallback(client):
    status_response = client.get("/api/deerflow/status")
    assert status_response.status_code == 200
    status_data = status_response.json()
    assert status_data["online"] is False
    assert status_data["assistant_id"] == "lead_agent"
    assert status_data["model"] is None

    skills_response = client.get("/api/deerflow/skills")
    assert skills_response.status_code == 200
    skills_data = skills_response.json()
    assert skills_data["online"] is False
    assert skills_data["skills"] == []

    models_response = client.get("/api/deerflow/models")
    assert models_response.status_code == 200
    models_data = models_response.json()
    assert models_data["online"] is False
    assert models_data["models"] == []

    toggle_response = client.put("/api/deerflow/skills/search", json={"enabled": True})
    assert toggle_response.status_code == 200
    toggle_data = toggle_response.json()
    assert toggle_data["online"] is False
    assert toggle_data["skill"]["name"] == "search"
    assert toggle_data["skill"]["enabled"] is None
