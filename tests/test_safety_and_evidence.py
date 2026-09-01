"""Security and evidence-integrity regression tests."""

import json
import sys
from types import ModuleType, SimpleNamespace

import pytest

from src.agent.llm_client import LLMClient, LLMClientError
from src.executor.db import DatabaseManager, DatabaseSafetyError
from src.report.timeline import TimelineRenderer
from src.scenarios.models import ExecutionTrace, RunResult, RunStatus


def test_live_model_client_fails_closed_without_keys(monkeypatch):
    """Production evaluation must never replace a missing model with known answers."""
    for name in (
        "GEMINI_API_KEY",
        "GOOGLE_API_KEY",
        "OPENAI_API_KEY",
        "GOOGLE_GENAI_USE_VERTEXAI",
        "GOOGLE_CLOUD_PROJECT",
    ):
        monkeypatch.delenv(name, raising=False)
    client = LLMClient()
    with pytest.raises(LLMClientError, match="No live model API key"):
        client.complete_json("Return a schedule", "Test")


def test_vertex_adc_counts_as_a_live_model_configuration(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setenv("GOOGLE_GENAI_USE_VERTEXAI", "true")
    monkeypatch.setenv("GOOGLE_CLOUD_PROJECT", "cutoverproof-test")

    assert LLMClient().is_live_model_available() is True


def _install_fake_gemini(monkeypatch, generate_content):
    """Install the smallest google.genai surface used by LLMClient."""

    google_module = ModuleType("google")
    genai_module = ModuleType("google.genai")
    types_module = ModuleType("google.genai.types")

    class FakeClient:
        def __init__(self, **_kwargs):
            self.models = SimpleNamespace(generate_content=generate_content)

    genai_module.Client = FakeClient
    genai_module.types = types_module
    types_module.HttpOptions = lambda **kwargs: kwargs
    types_module.GenerateContentConfig = lambda **kwargs: kwargs
    types_module.AutomaticFunctionCallingConfig = lambda **kwargs: kwargs
    google_module.genai = genai_module
    monkeypatch.setitem(sys.modules, "google", google_module)
    monkeypatch.setitem(sys.modules, "google.genai", genai_module)
    monkeypatch.setitem(sys.modules, "google.genai.types", types_module)


def test_live_gemini_fails_over_to_a_second_live_model(monkeypatch):
    calls = []

    def generate_content(*, model, **_kwargs):
        calls.append(model)
        if model == "gemini-primary":
            raise RuntimeError("504 DEADLINE_EXCEEDED")
        return SimpleNamespace(
            text='{"status": "ok"}',
            usage_metadata=SimpleNamespace(total_token_count=17),
        )

    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    monkeypatch.setenv("GEMINI_FALLBACK_MODEL", "gemini-fallback")
    _install_fake_gemini(monkeypatch, generate_content)
    client = LLMClient(model_name="gemini-primary")
    client.max_attempts = 1
    client.fallback_attempts = 1

    payload, tokens = client.complete_json("Return status", "Test")

    assert payload == {"status": "ok"}
    assert tokens == 17
    assert calls == ["gemini-primary", "gemini-fallback"]
    assert client.call_count == 2
    assert client.last_provider == "google"
    assert client.last_model == "gemini-fallback"


def test_live_gemini_does_not_retry_bad_credentials_on_another_model(monkeypatch):
    calls = []

    def generate_content(*, model, **_kwargs):
        calls.append(model)
        raise RuntimeError("403 PERMISSION_DENIED: API key not valid")

    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    monkeypatch.setenv("GEMINI_FALLBACK_MODEL", "gemini-fallback")
    _install_fake_gemini(monkeypatch, generate_content)
    client = LLMClient(model_name="gemini-primary")

    with pytest.raises(LLMClientError, match="PERMISSION_DENIED"):
        client.complete_json("Return status", "Test")

    assert calls == ["gemini-primary"]


def test_database_manager_rejects_non_sandbox_target():
    with pytest.raises(DatabaseSafetyError, match="Refusing destructive sandbox reset"):
        DatabaseManager("postgresql://admin:secret@db.example.com:5432/production")


def test_database_manager_allows_only_exact_configured_cloud_sandbox(monkeypatch):
    socket_path = "/cloudsql/demo-project:europe-west1:cutoverproof"
    monkeypatch.setenv("CUTOVERPROOF_ALLOWED_SANDBOX_HOST", socket_path)
    manager = DatabaseManager(
        "postgresql://cutover:secret@/cutoverproof_sandbox"
        f"?host={socket_path}"
    )
    assert socket_path in manager._safe_target()

    with pytest.raises(DatabaseSafetyError, match="Refusing destructive sandbox reset"):
        DatabaseManager(
            "postgresql://cutover:secret@/cutoverproof_sandbox"
            "?host=/cloudsql/demo-project:europe-west1:production"
        )


def test_timeline_uses_verified_trace_and_has_no_external_runtime_dependency(tmp_path):
    passing = ExecutionTrace(
        schedule_id="pass",
        hypothesis="passing candidate",
        operations_attempted=[],
        has_violation=False,
        status=RunStatus.NO_COUNTEREXAMPLE_WITHIN_BUDGET,
    )
    failing = ExecutionTrace(
        schedule_id="fail",
        hypothesis="winning candidate",
        operations_attempted=[],
        has_violation=True,
        first_violating_boundary="inv",
        failing_evidence_rows=[{"id": 42}],
        status=RunStatus.VERIFIED_COUNTEREXAMPLE,
    )
    result = RunResult(
        run_id="timeline-test",
        scenario_id="scenario",
        scenario_name="Scenario",
        approach_id="test",
        seed=42,
        max_budget=2,
        candidates_attempted=2,
        status=RunStatus.VERIFIED_COUNTEREXAMPLE,
        verified_counterexample_found=True,
        traces=[passing, failing],
        model_calls=2,
        model_tokens=1234,
        model_provider="google",
        model_name="gemini-test",
    )

    output = TimelineRenderer(output_dir=tmp_path).render_timeline_html(result)
    rendered = output.read_text(encoding="utf-8")
    assert "winning candidate" in rendered
    assert "passing candidate" not in rendered
    assert "cdn.tailwindcss.com" not in rendered
    assert "gemini-test" in rendered
    assert "2 calls / 1,234 tokens" in rendered
    assert "Cost not calculated" in rendered
    assert "$0.0000" not in rendered
