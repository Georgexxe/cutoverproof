"""Tests for baselines and equal-budget comparison (FR-009, AC-004)."""

import pytest
from src.scenarios.loader import ScenarioLoader
from src.executor.db import DatabaseManager
from src.executor.executor import DeterministicExecutor
from src.agent.tools import ToolGateway
from src.agent.random_heuristic_baseline import RandomHeuristicBaseline
from src.agent.one_shot_baseline import OneShotLLMBaseline
from src.agent.specialised_agent import SpecialisedAgent
from src.scenarios.models import RunStatus
from tests.fakes import ScriptedLLMClient


@pytest.fixture
def loader():
    return ScenarioLoader()


@pytest.fixture
def db_manager():
    return DatabaseManager()


def test_random_baseline_obeys_budget(loader, db_manager):
    """Test that RandomHeuristicBaseline respects the exact budget limit."""
    scenario = loader.load_scenario("u1_status_trigger_race")
    agent_view = loader.load_agent_view("u1_status_trigger_race")
    executor = DeterministicExecutor(scenario, db_manager)
    budget = 4

    tool_gateway = ToolGateway(
        scenario=scenario,
        agent_view=agent_view,
        executor=executor,
        budget=budget,
    )

    baseline = RandomHeuristicBaseline()
    result = baseline.run(agent_view, budget=budget, seed=42, tool_gateway=tool_gateway)

    assert result.candidates_attempted <= budget
    assert len(result.traces) <= budget
    assert tool_gateway.remaining_budget >= 0


def test_one_shot_baseline_obeys_budget(loader, db_manager):
    """Test that OneShotLLMBaseline respects candidate budget."""
    scenario = loader.load_scenario("u1_status_trigger_race")
    agent_view = loader.load_agent_view("u1_status_trigger_race")
    executor = DeterministicExecutor(scenario, db_manager)
    budget = 4

    tool_gateway = ToolGateway(
        scenario=scenario,
        agent_view=agent_view,
        executor=executor,
        budget=budget,
    )

    fake_model = ScriptedLLMClient(
        responses=[
            {
                "candidate_schedules": [
                    ["expand_schema", "backfill_orders", "new_app_read_status"],
                    ["expand_schema", "backfill_orders", "legacy_payment_event_paid", "new_app_read_status"],
                ]
            }
        ]
    )
    baseline = OneShotLLMBaseline(llm_client=fake_model)
    result = baseline.run(agent_view, budget=budget, seed=42, tool_gateway=tool_gateway)

    assert result.candidates_attempted <= budget


def test_specialised_agent_finds_u1_and_proposes_repair(loader, db_manager):
    """Test that SpecialisedAgent detects U1 and creates repair proposal."""
    scenario = loader.load_scenario("u1_status_trigger_race")
    agent_view = loader.load_agent_view("u1_status_trigger_race")
    executor = DeterministicExecutor(scenario, db_manager)

    tool_gateway = ToolGateway(
        scenario=scenario,
        agent_view=agent_view,
        executor=executor,
        budget=8,
    )

    fake_model = ScriptedLLMClient(
        responses=[
            {
                "action": "propose_schedule",
                "hypothesis": "Backfill followed by a legacy payment write can stale status_id.",
                "operations": [
                    "expand_schema",
                    "backfill_orders",
                    "legacy_payment_event_paid",
                    "new_app_read_status",
                ],
                "reason": "Exercise the compatibility gap.",
            },
            {
                "action": "propose_repair",
                "repair_id": "repair_compat_trigger_before_backfill",
                "explanation": "Activate compatibility before backfill.",
            },
        ]
    )
    agent = SpecialisedAgent(llm_client=fake_model)
    result = agent.run(agent_view, budget=8, seed=42, tool_gateway=tool_gateway)

    assert result.verified_counterexample_found is True
    assert result.status == RunStatus.VERIFIED_COUNTEREXAMPLE
    assert result.repair_proposal is not None


def test_specialised_agent_recovers_from_premature_repair_action(loader, db_manager):
    scenario = loader.load_scenario("u1_status_trigger_race")
    view = loader.load_agent_view("u1_status_trigger_race")
    llm = ScriptedLLMClient(
        [
            {"action": "propose_repair", "repair_id": "too_early"},
            {
                "action": "propose_schedule",
                "hypothesis": "backfill then legacy write",
                "operations": ["expand_schema", "backfill_orders", "legacy_payment_event_paid"],
                "reason": "test stale normalized value",
            },
            {
                "repair_id": "repair_compat_trigger_before_backfill",
                "explanation": "cover legacy writes before and during backfill",
            },
        ]
    )
    agent = SpecialisedAgent(llm)
    gateway = ToolGateway(
        scenario=scenario,
        agent_view=view,
        executor=DeterministicExecutor(scenario, db_manager),
        budget=4,
        agent_id=agent.approach_id,
    )

    result = agent.run(view, budget=4, seed=42, tool_gateway=gateway)

    assert result.status == RunStatus.VERIFIED_COUNTEREXAMPLE
    assert result.candidates_attempted == 1
    assert result.model_calls == 3
    assert result.repair_proposal.repair_id == "repair_compat_trigger_before_backfill"
    assert result.model_provider == "test"
    assert result.reasoning_backend == "live_model"
