"""Tests for reproducibility, 3-run same-seed stability, and secret sanitization."""

import pytest
from src.scenarios.loader import ScenarioLoader
from src.executor.db import DatabaseManager
from src.executor.executor import DeterministicExecutor
from src.scenarios.models import RunStatus
from src.evidence.sanitizer import SecretSanitizer
from src.evidence.serialization import to_json_safe
from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID


@pytest.fixture
def loader():
    return ScenarioLoader()


@pytest.fixture
def db_manager():
    return DatabaseManager()


def test_u1_three_run_same_seed_stability(loader, db_manager):
    """Test AC-001/AC-007: U1 produces stable verified failure across 3 consecutive runs."""
    scenario = loader.load_scenario("u1_status_trigger_race")
    executor = DeterministicExecutor(scenario, db_manager)

    outcomes = []
    for run_idx in range(3):
        trace = executor.execute_schedule(
            candidate=scenario.known_failing_schedule,
            hypothesis=f"Stability run #{run_idx + 1}",
        )
        outcomes.append((trace.status, trace.has_violation, len(trace.failing_evidence_rows)))

    assert len(outcomes) == 3
    for status, has_viol, ev_len in outcomes:
        assert status == RunStatus.VERIFIED_COUNTEREXAMPLE
        assert has_viol is True
        assert ev_len >= 1


def test_s1_three_run_same_seed_stability(loader, db_manager):
    """Test AC-003/AC-007: S1 produces stable pass across 3 consecutive runs."""
    scenario = loader.load_scenario("s1_compat_first_safe")
    executor = DeterministicExecutor(scenario, db_manager)

    outcomes = []
    sched = ["expand_schema", "backfill_orders", "payment_event_paid", "new_app_read_status"]
    for run_idx in range(3):
        trace = executor.execute_schedule(
            candidate=sched,
            hypothesis=f"S1 stability run #{run_idx + 1}",
        )
        outcomes.append((trace.status, trace.has_violation, len(trace.failing_evidence_rows)))

    assert len(outcomes) == 3
    for status, has_viol, ev_len in outcomes:
        assert status == RunStatus.NO_COUNTEREXAMPLE_WITHIN_BUDGET
        assert has_viol is False
        assert ev_len == 0


def test_secret_sanitizer_redaction():
    """Test that secret sanitizer scrubs API keys and passwords."""
    sanitizer = SecretSanitizer()
    fake_openai_key = "sk-" + "abcdef12345678901234567890"
    fake_google_key = "AI" + "zaSyD123456789012345678901234567890"
    fake_prompt = f"Run with key {fake_openai_key} and {fake_google_key}"
    sanitized = sanitizer.sanitize_str(fake_prompt)
    assert "sk-" not in sanitized
    assert "AIza" not in sanitized
    assert "[REDACTED]" in sanitized


def test_database_evidence_values_are_json_safe():
    """Binary and PostgreSQL-native values remain usable in prompts and artifacts."""
    converted = to_json_safe(
        {
            "text_bytes": b"paid",
            "binary": b"\xff\x00",
            "amount": Decimal("149.99"),
            "recorded_at": datetime(2026, 9, 1, 12, 0, tzinfo=timezone.utc),
            "run_uuid": UUID("12345678-1234-5678-1234-567812345678"),
            "tuple_value": (1, memoryview(b"status")),
        }
    )

    import json

    encoded = json.dumps(converted)
    assert converted["text_bytes"] == "paid"
    assert converted["binary"] == {"encoding": "base64", "data": "/wA="}
    assert converted["amount"] == "149.99"
    assert "2026-09-01T12:00:00+00:00" in encoded
    assert converted["tuple_value"] == [1, "status"]
