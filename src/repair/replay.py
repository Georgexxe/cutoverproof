"""Deterministic repair replay engine."""

from typing import List, Optional
from src.scenarios.models import Scenario, RepairProposal, ExecutionTrace, RunStatus
from src.executor.db import DatabaseManager
from src.executor.executor import DeterministicExecutor
from src.repair.approval import HumanApprovalGate, ApprovalError


class RepairReplayer:
    """Replays the exact failing schedule against a fresh sandbox with the approved repair applied."""

    def __init__(self, scenario: Scenario, db_manager: Optional[DatabaseManager] = None):
        self.scenario = scenario
        self.db_manager = db_manager or DatabaseManager()

    def replay_repair(
        self,
        failing_schedule: List[str],
        repair_proposal: RepairProposal,
    ) -> ExecutionTrace:
        """Applies approved repair to fresh sandbox and executes identical failing schedule."""
        # 1. Enforce human approval
        HumanApprovalGate.assert_approved(repair_proposal)

        # 2. Construct repaired schema SQL by combining original schema + repair SQL
        repaired_schema_sql = f"{self.scenario.schema_sql}\n\n-- REPAIR APPLIED:\n{self.scenario.repair_sql}"

        # 3. Create executor for repaired run
        executor = DeterministicExecutor(self.scenario, self.db_manager)

        # 4. Execute identical schedule on repaired sandbox
        replayed_trace = executor.execute_schedule(
            candidate=failing_schedule,
            hypothesis=f"Replaying schedule after approved repair '{repair_proposal.repair_name}'",
            custom_schema_sql=repaired_schema_sql,
        )

        # If previously failing schedule now passes all invariants, status is REPAIR_REPLAY_PASSED
        if not replayed_trace.has_violation and replayed_trace.status == RunStatus.NO_COUNTEREXAMPLE_WITHIN_BUDGET:
            replayed_trace.status = RunStatus.REPAIR_REPLAY_PASSED
        elif replayed_trace.has_violation:
            replayed_trace.status = RunStatus.REPAIR_REPLAY_FAILED

        return replayed_trace
