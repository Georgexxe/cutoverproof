"""Tests for deterministic execution core: U1 failure reproduction and S1 safe control."""

import pytest
from src.scenarios.loader import ScenarioLoader
from src.executor.db import DatabaseManager
from src.executor.executor import DeterministicExecutor
from src.scenarios.models import RunStatus


@pytest.fixture
def loader():
    return ScenarioLoader()


@pytest.fixture
def db_manager():
    return DatabaseManager()


def test_u1_known_failing_schedule_produces_counterexample(loader, db_manager):
    """Test Checkpoint 1: U1 trigger/backfill race produces verified counterexample."""
    scenario = loader.load_scenario("u1_status_trigger_race")
    executor = DeterministicExecutor(scenario, db_manager)

    # Execute known failing schedule
    trace = executor.execute_schedule(
        candidate=scenario.known_failing_schedule,
        hypothesis="Payment trigger fires after backfill, leaving status_id stale as pending while status is paid",
    )

    assert trace.has_violation is True
    assert trace.status == RunStatus.VERIFIED_COUNTEREXAMPLE
    assert trace.first_violating_boundary == "status_consistency_invariant"
    assert len(trace.failing_evidence_rows) >= 1

    # Check evidence row details for order 42
    evidence = trace.failing_evidence_rows[0]
    assert evidence["id"] == 42
    assert evidence["legacy_status"] == "paid"
    assert evidence["status_id"] == 1
    assert evidence["lookup_status"] == "pending"


def test_s1_safe_control_does_not_produce_false_alarm(loader, db_manager):
    """Test Checkpoint 1: S1 safe control passes without false counterexamples."""
    scenario = loader.load_scenario("s1_compat_first_safe")
    executor = DeterministicExecutor(scenario, db_manager)

    # Try several schedules covering different operation orderings
    test_schedules = [
        ["expand_schema", "backfill_orders", "payment_event_paid", "new_app_read_status"],
        ["expand_schema", "payment_event_paid", "backfill_orders", "new_app_read_status"],
        ["expand_schema", "legacy_order_update_shipped", "backfill_orders", "new_app_read_status"],
        ["expand_schema", "backfill_orders", "legacy_order_update_shipped", "new_app_read_status"],
    ]

    for sched in test_schedules:
        trace = executor.execute_schedule(
            candidate=sched,
            hypothesis="Testing ordering on safe control with active sync trigger",
        )
        assert trace.has_violation is False, f"False alarm on schedule: {sched}"
        assert trace.status == RunStatus.NO_COUNTEREXAMPLE_WITHIN_BUDGET
        assert len(trace.failing_evidence_rows) == 0


def test_u1_safe_ordering_does_not_fail(loader, db_manager):
    """If payment happens before expand/backfill, no race occurs."""
    scenario = loader.load_scenario("u1_status_trigger_race")
    executor = DeterministicExecutor(scenario, db_manager)

    safe_sched = [
        "legacy_payment_event_paid",
        "expand_schema",
        "backfill_orders",
        "new_app_read_status",
    ]
    trace = executor.execute_schedule(
        candidate=safe_sched,
        hypothesis="Payment occurs before backfill, so backfill correctly converts 'paid' to status_id=2",
    )
    assert trace.has_violation is False
    assert trace.status == RunStatus.NO_COUNTEREXAMPLE_WITHIN_BUDGET
