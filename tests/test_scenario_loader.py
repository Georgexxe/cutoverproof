"""Tests for scenario loading and validation (FR-001, FR-002)."""

import pytest
from src.scenarios.loader import ScenarioLoader, ScenarioLoaderError
from src.scenarios.models import EvaluatorLabel


@pytest.fixture
def loader():
    return ScenarioLoader()


def test_load_all_valid_scenarios(loader):
    """Test loading checked-in scenarios plus any valid customer imports."""
    scenario_ids = loader.list_scenario_ids()
    assert {
        "u1_status_trigger_race",
        "u2_legacy_update_after_backfill",
        "u3_cutover_before_backfill",
        "s1_compat_first_safe",
        "s2_compat_read_safe",
    }.issubset(set(scenario_ids))

    for s_id in scenario_ids:
        scenario = loader.load_scenario(s_id)
        assert scenario.id == s_id
        assert len(scenario.phases) >= 3
        assert len(scenario.operations) >= 3
        assert len(scenario.invariants) >= 1
        assert scenario.schema_sql.strip() != ""


def test_agent_view_hides_evaluator_label_and_known_schedule(loader):
    """Test that agent view strictly withholds evaluator labels and answers."""
    agent_view = loader.load_agent_view("u1_status_trigger_race")
    assert agent_view.id == "u1_status_trigger_race"
    assert not hasattr(agent_view, "evaluator_label")
    assert not hasattr(agent_view, "known_failing_schedule")


def test_reject_nonexistent_scenario(loader):
    """Test error handling when scenario does not exist."""
    with pytest.raises(ScenarioLoaderError):
        loader.load_scenario("non_existent_scenario_999")


def test_reject_scenario_path_traversal(loader):
    """Scenario IDs cannot escape the checked-in scenarios directory."""
    with pytest.raises(ScenarioLoaderError):
        loader.load_scenario("../u1_status_trigger_race")
