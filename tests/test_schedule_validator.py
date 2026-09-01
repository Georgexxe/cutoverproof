"""Tests for schedule validator (FR-003, FR-004)."""

import pytest
from src.scenarios.loader import ScenarioLoader
from src.validator.schedule_validator import ScheduleValidator
from src.scenarios.models import CandidateSchedule


@pytest.fixture
def scenario():
    loader = ScenarioLoader()
    return loader.load_scenario("u1_status_trigger_race")


def test_valid_schedule(scenario):
    validator = ScheduleValidator(scenario)
    result = validator.validate(["expand_schema", "backfill_orders", "new_app_read_status"])
    assert result.is_valid is True
    assert result.error_message is None
    assert len(result.canonical_schedule) == 3


def test_reject_empty_schedule(scenario):
    validator = ScheduleValidator(scenario)
    result = validator.validate([])
    assert result.is_valid is False
    assert "empty" in result.error_message.lower()


def test_reject_undeclared_operations(scenario):
    validator = ScheduleValidator(scenario)
    result = validator.validate(["expand_schema", "drop_all_tables_fake", "backfill_orders"])
    assert result.is_valid is False
    assert "undeclared" in result.error_message.lower()
    assert "drop_all_tables_fake" in result.rejected_operations


def test_reject_schedule_exceeding_max_length(scenario):
    validator = ScheduleValidator(scenario)
    long_sched = ["expand_schema"] * 10
    result = validator.validate(long_sched)
    assert result.is_valid is False
    assert "exceeds maximum allowed length" in result.error_message.lower()
