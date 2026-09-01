"""Tests for human approval gate and exact-schedule repair replay (FR-011, FR-012, FR-013, AC-005, AC-006)."""

import pytest
from src.scenarios.loader import ScenarioLoader
from src.executor.db import DatabaseManager
from src.scenarios.models import RepairProposal, RunStatus
from src.repair.approval import HumanApprovalGate, ApprovalError
from src.repair.replay import RepairReplayer


@pytest.fixture
def scenario():
    loader = ScenarioLoader()
    return loader.load_scenario("u1_status_trigger_race")


@pytest.fixture
def db_manager():
    return DatabaseManager()


def test_unapproved_repair_raises_error(scenario, db_manager):
    """Test AC-005: Replay is strictly blocked without recorded human approval."""
    replayer = RepairReplayer(scenario, db_manager)
    unapproved_proposal = RepairProposal(
        proposal_id="prop_unapproved",
        repair_id="repair_compat_trigger_before_backfill",
        repair_name="Compatibility Trigger Fix",
        explanation="Test explanation",
        requires_human_approval=True,
        approved_by_human=False,
    )

    with pytest.raises(ApprovalError) as exc_info:
        replayer.replay_repair(
            failing_schedule=scenario.known_failing_schedule,
            repair_proposal=unapproved_proposal,
        )
    assert "Human approval required" in str(exc_info.value)


def test_approved_repair_replays_and_passes(scenario, db_manager):
    """Test AC-006: Approved repair is replayed with exact schedule and passes."""
    replayer = RepairReplayer(scenario, db_manager)
    proposal = RepairProposal(
        proposal_id="prop_approved",
        repair_id="repair_compat_trigger_before_backfill",
        repair_name="Compatibility Trigger Fix",
        explanation="Test explanation",
        requires_human_approval=True,
        approved_by_human=False,
    )

    # Human approves
    HumanApprovalGate.approve_proposal(proposal, approver_name="Lead Migration Engineer")
    assert proposal.approved_by_human is True
    assert proposal.approved_by == "Lead Migration Engineer"
    assert proposal.approval_timestamp is not None

    # Replay on fresh sandbox
    replayed_trace = replayer.replay_repair(
        failing_schedule=scenario.known_failing_schedule,
        repair_proposal=proposal,
    )

    assert replayed_trace.status == RunStatus.REPAIR_REPLAY_PASSED
    assert replayed_trace.has_violation is False
    assert len(replayed_trace.failing_evidence_rows) == 0
