"""Product API regressions that do not call a model or mutate PostgreSQL."""

import os
import importlib
from pathlib import Path

from fastapi.testclient import TestClient

os.environ["CUTOVERPROOF_DEMO_PASSWORD"] = "test-demo-password"

from src.api.app import app
from src.api.service import serialize_run
from src.scenarios.models import RunResult, RunStatus

api_app_module = importlib.import_module("src.api.app")


client = TestClient(app)
login_response = client.post(
    "/api/auth/login",
    json={"email": "engineer@cutoverproof.dev", "password": "test-demo-password"},
)
assert login_response.status_code == 200
csrf_headers = {"X-CSRF-Token": login_response.json()["csrf_token"]}


def test_private_api_requires_a_demo_session() -> None:
    anonymous = TestClient(app)
    assert anonymous.get("/api/scenarios").status_code == 401


def test_health_exposes_the_honest_execution_boundary() -> None:
    response = client.get("/api/health")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert "checked-in synthetic scenarios" in payload["execution_boundary"]
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["x-frame-options"] == "DENY"
    assert "tools=(self)" in response.headers["permissions-policy"]
    assert response.headers["origin-agent-cluster"] == "?1"


def test_mutating_api_requires_the_session_csrf_token() -> None:
    rejected = client.post(
        "/api/webmcp/review-drafts",
        json={
            "scenario_id": "u1_status_trigger_race",
            "objective": "Review the compatibility window before release.",
            "risk_focus": ["stale_writes"],
            "idempotency_key": "csrf-test-review",
        },
    )
    assert rejected.status_code == 403


def test_demo_login_is_rate_limited_without_user_enumeration() -> None:
    api_app_module.app.state.login_failures = {}
    attacker = TestClient(app)
    try:
        for _ in range(api_app_module.LOGIN_MAX_FAILURES):
            rejected = attacker.post(
                "/api/auth/login",
                json={"email": "nobody@example.com", "password": "incorrect-password"},
            )
            assert rejected.status_code == 401
            assert rejected.json()["detail"] == "Email or password is incorrect."
        limited = attacker.post(
            "/api/auth/login",
            json={"email": "engineer@cutoverproof.dev", "password": "test-demo-password"},
        )
        assert limited.status_code == 429
        assert limited.headers["retry-after"] == str(api_app_module.LOGIN_WINDOW_SECONDS)
    finally:
        api_app_module.app.state.login_failures = {}


def test_scenarios_hide_evaluator_answers_and_raw_sql() -> None:
    response = client.get("/api/scenarios")
    assert response.status_code == 200
    payload = response.json()
    assert {
        "u1_status_trigger_race",
        "u2_legacy_update_after_backfill",
        "u3_cutover_before_backfill",
        "s1_compat_first_safe",
        "s2_compat_read_safe",
    }.issubset({scenario["id"] for scenario in payload})
    assert all("evaluator_label" not in scenario for scenario in payload)
    assert all("known_failing_schedule" not in scenario for scenario in payload)
    assert all("sql" not in scenario for scenario in payload)


def test_product_run_prioritizes_decision_and_links_to_evidence() -> None:
    response = client.get("/api/runs/run_a3_u1_status_trigger_race_42")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "blocked"
    assert payload["status_label"] == "DO NOT CUT OVER"
    assert payload["candidates_attempted"] == 1
    assert payload["repair"]["approved"] is False
    assert payload["evidence_url"].endswith("run_a3_u1_status_trigger_race_42")
    assert "evaluator_label" not in payload
    assert "sql_executed" not in response.text


def test_model_timeout_is_not_mislabeled_as_a_migration_failure() -> None:
    payload = serialize_run(
        RunResult(
            run_id="run_a3_u1_timeout_test_42",
            scenario_id="u1_status_trigger_race",
            scenario_name="Status Normalization Trigger/Backfill Race",
            approach_id="A3_specialised_agent",
            seed=42,
            max_budget=4,
            status=RunStatus.AGENT_ERROR,
            error_message="Gemini request failed: 504 DEADLINE_EXCEEDED",
        )
    )
    assert payload["status"] == "failed"
    assert payload["status_label"] == "ASSESSMENT INTERRUPTED"
    assert "Gemini could not return" in payload["finding"]
    assert payload["candidates_attempted"] == 0


def test_importing_the_same_valid_pack_is_idempotent(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(api_app_module, "IMPORTED_SCENARIOS", tmp_path)
    template = client.get("/api/scenario-packs/template").json()

    first = client.post("/api/scenario-packs", json=template, headers=csrf_headers)
    second = client.post("/api/scenario-packs", json=template, headers=csrf_headers)

    assert first.status_code == 201
    assert first.json()["reused"] is False
    assert second.status_code == 201
    assert second.json()["reused"] is True

    changed = {**template, "name": "A different pack using the same id"}
    conflict = client.post("/api/scenario-packs", json=changed, headers=csrf_headers)
    assert conflict.status_code == 409


def test_video_demo_packs_are_distinct_valid_uploads(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(api_app_module, "IMPORTED_SCENARIOS", tmp_path)
    template = client.get("/api/scenario-packs/template").json()
    demo_directory = Path(__file__).parents[1] / "examples" / "video-demo-packs"
    pack_paths = sorted(demo_directory.glob("*.json"))

    assert len(pack_paths) == 3

    imported_ids: set[str] = set()
    repairable_pack = None
    for path in pack_paths:
        response = client.post(
            "/api/scenario-packs",
            content=path.read_bytes(),
            headers={"content-type": "application/json", **csrf_headers},
        )
        assert response.status_code == 201, response.text
        imported_ids.add(response.json()["id"])
        if path.name.startswith("01-"):
            repairable_pack = tmp_path / response.json()["id"]

    assert len(imported_ids) == len(pack_paths)
    assert template["id"] not in imported_ids
    assert repairable_pack is not None
    assert (repairable_pack / "repair.sql").exists()
    stored = (repairable_pack / "scenario.json").read_text(encoding="utf-8")
    assert "repair_compat_trigger_before_backfill" in stored


def test_benchmark_endpoint_preserves_the_same_model_comparison() -> None:
    response = client.get("/api/benchmarks")
    assert response.status_code == 200
    metrics = response.json()["metrics_summary"]
    assert metrics["A1_one_shot_llm"]["unsafe_detection_recall"] == "2/3"
    assert metrics["A3_specialised_agent"]["unsafe_detection_recall"] == "3/3"


def test_invalid_run_paths_and_payloads_are_rejected() -> None:
    invalid_run = client.get("/api/runs/..%2F..%2F.env")
    assert invalid_run.status_code in {400, 404}
    malformed = client.post(
        "/api/runs",
        json={"scenario_id": "../../outside", "approach": "specialised_agent", "budget": 99},
        headers=csrf_headers,
    )
    assert malformed.status_code == 422


def test_openapi_documents_human_approval_endpoint() -> None:
    response = client.get("/openapi.json")
    assert response.status_code == 200
    paths = response.json()["paths"]
    assert "/api/runs/{run_id}/approve-repair" in paths
    assert "/api/webmcp/review-drafts" in paths


def test_webmcp_contract_hides_sql_and_evaluator_answers() -> None:
    response = client.get("/api/webmcp/contracts/u1_status_trigger_race")
    assert response.status_code == 200
    payload = response.json()
    assert payload["authority"]["human"].startswith("Must start")
    assert payload["invariants"]
    assert all("sql" not in operation for operation in payload["declared_operations"])
    assert all("sql" not in invariant for invariant in payload["invariants"])
    assert "evaluator_label" not in response.text
    assert "known_failing_schedule" not in response.text


def test_webmcp_review_draft_is_idempotent_and_does_not_execute() -> None:
    payload = {
        "scenario_id": "u1_status_trigger_race",
        "objective": "Check stale writes before the status cutover reaches production.",
        "risk_focus": ["stale_writes", "compatibility_window"],
        "idempotency_key": "release-status-v42",
    }
    first = client.post("/api/webmcp/review-drafts", json=payload, headers=csrf_headers)
    second = client.post("/api/webmcp/review-drafts", json=payload, headers=csrf_headers)
    assert first.status_code == 201
    assert second.status_code == 201
    assert first.json()["id"] == second.json()["id"]
    assert first.json()["execution_started"] is False
    assert first.json()["status"] == "awaiting_human_review"
