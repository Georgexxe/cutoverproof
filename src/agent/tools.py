"""Tool Gateway enforcing strict Agent/Deterministic boundaries."""

import time
import uuid
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional
from src.scenarios.models import (
    Scenario,
    ScenarioView,
    CandidateSchedule,
    ExecutionTrace,
    RepairProposal,
    TrajectoryStep,
    RunStatus,
)
from src.executor.executor import DeterministicExecutor


class ToolGateway:
    """Controlled tool gateway between planning agents and deterministic execution."""

    def __init__(
        self,
        scenario: Scenario,
        agent_view: ScenarioView,
        executor: DeterministicExecutor,
        budget: int = 8,
        agent_id: str = "specialised_agent",
        progress_callback: Optional[Callable[[int, str], None]] = None,
    ):
        self.scenario = scenario
        self.agent_view = agent_view
        self.executor = executor
        self.max_budget = budget
        self.remaining_budget = budget
        self.agent_id = agent_id
        self.trajectories: List[TrajectoryStep] = []
        self.executed_traces: List[ExecutionTrace] = []
        self.pending_repair: Optional[RepairProposal] = None
        self.counterexample_trace: Optional[ExecutionTrace] = None
        self.step_counter = 0
        self.progress_callback = progress_callback

    def _report_progress(self, progress: int, stage: str) -> None:
        if self.progress_callback:
            self.progress_callback(progress, stage)

    def _record_trajectory(
        self,
        action_type: str,
        tool_name: Optional[str] = None,
        tool_input: Optional[Dict[str, Any]] = None,
        tool_output: Optional[Dict[str, Any]] = None,
        observation_summary: Optional[str] = None,
    ) -> None:
        self.step_counter += 1
        now_str = datetime.now(timezone.utc).isoformat()
        self.trajectories.append(
            TrajectoryStep(
                step_index=self.step_counter,
                timestamp=now_str,
                agent_id=self.agent_id,
                action_type=action_type,
                tool_name=tool_name,
                tool_input=tool_input,
                tool_output=tool_output,
                observation_summary=observation_summary,
                remaining_budget=self.remaining_budget,
            )
        )

    def inspect_scenario(self) -> Dict[str, Any]:
        """Tool: inspect_scenario -> returns agent-visible scenario view and remaining budget."""
        self._report_progress(30, "Inspecting phases, operations, and invariants")
        tool_input = {}
        output = {
            "scenario_id": self.agent_view.id,
            "scenario_name": self.agent_view.name,
            "description": self.agent_view.description,
            "remaining_budget": self.remaining_budget,
            "max_schedule_length": self.agent_view.max_schedule_length,
            "phases": [p.model_dump() for p in self.agent_view.phases],
            "operations": {
                op_id: {
                    "id": op.id,
                    "phase": op.phase,
                    "actor": op.actor,
                    "description": op.description,
                }
                for op_id, op in self.agent_view.operations.items()
            },
            "invariants": [
                {
                    "id": inv.id,
                    "name": inv.name,
                    "description": inv.description,
                }
                for inv in self.agent_view.invariants
            ],
            "permitted_repairs": [r.model_dump() for r in self.agent_view.permitted_repairs],
        }
        self._record_trajectory(
            action_type="tool_call",
            tool_name="inspect_scenario",
            tool_input=tool_input,
            tool_output=output,
            observation_summary=f"Inspected scenario '{self.agent_view.id}'. Remaining budget: {self.remaining_budget}.",
        )
        return output

    def propose_or_run_schedule(
        self,
        operations: List[str],
        hypothesis: str = "Agent candidate schedule",
        reason: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Tool: propose_or_run_schedule -> validates, resets sandbox, executes schedule, verifies invariants."""
        tool_input = {
            "operations": operations,
            "hypothesis": hypothesis,
            "reason": reason,
        }

        if self.remaining_budget <= 0:
            output = {
                "status": "error",
                "error": "Experiment budget exhausted. No further candidate executions allowed.",
                "remaining_budget": 0,
            }
            self._record_trajectory(
                action_type="tool_call",
                tool_name="propose_or_run_schedule",
                tool_input=tool_input,
                tool_output=output,
                observation_summary="Execution rejected: experiment budget exhausted.",
            )
            return output

        # Deduct 1 candidate execution from budget
        self.remaining_budget -= 1
        candidate_number = self.max_budget - self.remaining_budget
        start_progress = min(72, 42 + (candidate_number - 1) * 8)
        self._report_progress(
            start_progress,
            f"Executing candidate {candidate_number} of {self.max_budget} in PostgreSQL",
        )

        candidate = CandidateSchedule(
            schedule_id=f"cand_{len(self.executed_traces) + 1}",
            hypothesis=hypothesis,
            operations=operations,
            reason_for_ordering=reason,
        )

        trace = self.executor.execute_schedule(candidate, hypothesis=hypothesis)
        self.executed_traces.append(trace)
        self._report_progress(
            min(80, start_progress + 10),
            "Checking the declared SQL invariant",
        )

        if trace.has_violation and not self.counterexample_trace:
            self.counterexample_trace = trace

        output = {
            "schedule_id": trace.schedule_id,
            "status": trace.status.value,
            "has_violation": trace.has_violation,
            "first_violating_boundary": trace.first_violating_boundary,
            "violating_evidence_rows": trace.failing_evidence_rows,
            "operations_executed": [
                {
                    "step": s.step_index,
                    "op": s.operation_id,
                    "phase": s.phase,
                    "actor": s.actor,
                    "status": s.status,
                }
                for s in trace.step_outcomes
            ],
            "invariants_checked": [
                {
                    "invariant_id": r.invariant_id,
                    "passed": r.passed,
                    "violating_rows_count": r.row_count,
                }
                for r in trace.invariant_results
            ],
            "remaining_budget": self.remaining_budget,
        }

        obs_summary = (
            f"Executed schedule '{trace.schedule_id}'. "
            f"Violation found: {trace.has_violation}. "
            f"Status: {trace.status.value}. Remaining budget: {self.remaining_budget}."
        )

        self._record_trajectory(
            action_type="tool_call",
            tool_name="propose_or_run_schedule",
            tool_input=tool_input,
            tool_output=output,
            observation_summary=obs_summary,
        )

        return output

    def inspect_trace(self, schedule_id: str) -> Dict[str, Any]:
        """Tool: inspect_trace -> retrieves detailed trace for a previously executed schedule."""
        tool_input = {"schedule_id": schedule_id}
        for trace in self.executed_traces:
            if trace.schedule_id == schedule_id:
                output = trace.model_dump()
                self._record_trajectory(
                    action_type="tool_call",
                    tool_name="inspect_trace",
                    tool_input=tool_input,
                    tool_output=output,
                    observation_summary=f"Inspected full trace for schedule '{schedule_id}'.",
                )
                return output

        output = {"error": f"Schedule ID '{schedule_id}' not found in execution history."}
        self._record_trajectory(
            action_type="tool_call",
            tool_name="inspect_trace",
            tool_input=tool_input,
            tool_output=output,
            observation_summary=f"Schedule ID '{schedule_id}' not found.",
        )
        return output

    def propose_repair(self, repair_id: str, explanation: str) -> Dict[str, Any]:
        """Tool: propose_repair -> proposes one bounded repair from permitted repair list."""
        tool_input = {"repair_id": repair_id, "explanation": explanation}

        # Check if repair_id is in permitted repairs
        matched_repair = None
        for r in self.agent_view.permitted_repairs:
            if r.id == repair_id:
                matched_repair = r
                break

        if not matched_repair:
            allowed = [r.id for r in self.agent_view.permitted_repairs]
            output = {
                "status": "error",
                "error": f"Repair '{repair_id}' is not in permitted repairs list: {allowed}",
            }
            self._record_trajectory(
                action_type="tool_call",
                tool_name="propose_repair",
                tool_input=tool_input,
                tool_output=output,
                observation_summary=f"Repair proposal '{repair_id}' rejected (undeclared repair).",
            )
            return output

        proposal = RepairProposal(
            proposal_id=f"prop_{uuid.uuid4().hex[:6]}",
            repair_id=matched_repair.id,
            repair_name=matched_repair.name,
            explanation=explanation,
            requires_human_approval=True,
            approved_by_human=False,
            approval_timestamp=None,
        )
        self.pending_repair = proposal

        output = {
            "status": "success",
            "proposal_id": proposal.proposal_id,
            "repair_id": proposal.repair_id,
            "repair_name": proposal.repair_name,
            "message": "Repair proposed successfully. Awaiting explicit human approval before replay.",
            "requires_human_approval": True,
        }

        self._record_trajectory(
            action_type="repair_proposal",
            tool_name="propose_repair",
            tool_input=tool_input,
            tool_output=output,
            observation_summary=f"Proposed repair '{proposal.repair_name}'. Human approval required.",
        )
        return output

    def record_human_approval(self, proposal: RepairProposal) -> None:
        """Records an approval performed outside the agent boundary."""
        self._record_trajectory(
            action_type="human_approval",
            tool_name=None,
            tool_input={
                "proposal_id": proposal.proposal_id,
                "repair_id": proposal.repair_id,
            },
            tool_output={
                "approved_by_human": proposal.approved_by_human,
                "approved_by": proposal.approved_by,
                "approval_timestamp": proposal.approval_timestamp,
            },
            observation_summary=f"Human approval recorded for repair '{proposal.repair_id}'.",
        )
