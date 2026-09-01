"""Data models for CutoverProof scenarios, schedules, traces, and results."""

from __future__ import annotations
from enum import Enum
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field


class EvaluatorLabel(str, Enum):
    UNSAFE = "unsafe"
    SAFE = "safe"
    UNKNOWN = "unknown"


class RunStatus(str, Enum):
    VERIFIED_COUNTEREXAMPLE = "verified_counterexample_found"
    NO_COUNTEREXAMPLE_WITHIN_BUDGET = "no_counterexample_found_within_budget"
    INVALID_SCENARIO = "invalid_scenario"
    INVALID_SCHEDULE = "invalid_schedule"
    INFRASTRUCTURE_ERROR = "infrastructure_error"
    EXECUTION_ERROR = "execution_error"
    VERIFIER_ERROR = "verifier_error"
    AGENT_ERROR = "agent_error"
    REPAIR_REPLAY_PASSED = "repair_replay_passed"
    REPAIR_REPLAY_FAILED = "repair_replay_failed"
    HUMAN_APPROVAL_DECLINED = "human_approval_declined"


class Phase(BaseModel):
    id: str
    name: str
    description: str


class Operation(BaseModel):
    id: str
    phase: str
    actor: str
    description: str
    sql: str


class Invariant(BaseModel):
    id: str
    name: str
    description: str
    sql: str


class RepairOption(BaseModel):
    id: str
    name: str
    description: str
    patch_type: str


class Scenario(BaseModel):
    """Full scenario loaded from disk (includes evaluator label)."""
    id: str
    name: str
    description: str
    evaluator_label: EvaluatorLabel
    max_candidates: int = 8
    max_schedule_length: int = 6
    schema_file: str
    seed_file: str
    expand_file: str
    invariants_file: str
    repair_file: str
    phases: List[Phase]
    operations: Dict[str, Operation]
    invariants: List[Invariant]
    known_failing_schedule: List[str] = Field(default_factory=list)
    permitted_repairs: List[RepairOption] = Field(default_factory=list)

    # Loaded SQL contents
    schema_sql: str = ""
    seed_sql: str = ""
    expand_sql: str = ""
    invariants_sql: str = ""
    repair_sql: str = ""


class ScenarioView(BaseModel):
    """Agent-visible scenario view (evaluator label and known schedule strictly hidden)."""
    id: str
    name: str
    description: str
    max_candidates: int
    max_schedule_length: int
    phases: List[Phase]
    operations: Dict[str, Operation]
    invariants: List[Invariant]
    permitted_repairs: List[RepairOption]


class CandidateSchedule(BaseModel):
    """A proposed candidate schedule of ordered declared operations."""
    schedule_id: Optional[str] = None
    hypothesis: str
    operations: List[str]
    target_invariant_id: Optional[str] = None
    reason_for_ordering: Optional[str] = None


class ScheduleValidationResult(BaseModel):
    is_valid: bool
    canonical_schedule: List[str] = Field(default_factory=list)
    error_message: Optional[str] = None
    rejected_operations: List[str] = Field(default_factory=list)


class StepOutcome(BaseModel):
    step_index: int
    operation_id: str
    phase: str
    actor: str
    sql_executed: str
    rows_affected: int = 0
    duration_ms: float = 0.0
    status: str = "success"
    error_message: Optional[str] = None


class EvidenceRow(BaseModel):
    columns: Dict[str, Any]


class InvariantResult(BaseModel):
    invariant_id: str
    passed: bool
    violating_rows: List[Dict[str, Any]] = Field(default_factory=list)
    row_count: int = 0
    sql_query: str = ""
    error_message: Optional[str] = None


class ExecutionTrace(BaseModel):
    schedule_id: str
    hypothesis: str
    operations_attempted: List[str]
    step_outcomes: List[StepOutcome] = Field(default_factory=list)
    invariant_results: List[InvariantResult] = Field(default_factory=list)
    has_violation: bool = False
    first_violating_boundary: Optional[str] = None
    failing_evidence_rows: List[Dict[str, Any]] = Field(default_factory=list)
    total_duration_ms: float = 0.0
    status: RunStatus = RunStatus.NO_COUNTEREXAMPLE_WITHIN_BUDGET


class RepairProposal(BaseModel):
    proposal_id: str
    repair_id: str
    repair_name: str
    explanation: str
    requires_human_approval: bool = True
    approved_by_human: bool = False
    approved_by: Optional[str] = None
    approval_timestamp: Optional[str] = None


class TrajectoryStep(BaseModel):
    step_index: int
    timestamp: str
    agent_id: str
    action_type: str  # "tool_call", "observation", "hypothesis", "repair_proposal", "human_approval"
    tool_name: Optional[str] = None
    tool_input: Optional[Dict[str, Any]] = None
    tool_output: Optional[Dict[str, Any]] = None
    observation_summary: Optional[str] = None
    remaining_budget: int = 0


class RunResult(BaseModel):
    run_id: str
    scenario_id: str
    scenario_name: str
    approach_id: str
    seed: int
    max_budget: int
    candidates_attempted: int = 0
    status: RunStatus
    verified_counterexample_found: bool = False
    first_counterexample_index: Optional[int] = None
    winning_schedule: Optional[List[str]] = None
    traces: List[ExecutionTrace] = Field(default_factory=list)
    repair_proposal: Optional[RepairProposal] = None
    repair_replay_trace: Optional[ExecutionTrace] = None
    trajectories: List[TrajectoryStep] = Field(default_factory=list)
    wall_clock_seconds: float = 0.0
    model_calls: int = 0
    model_tokens: int = 0
    approximate_cost_usd: float = 0.0
    reasoning_backend: str = "none"
    model_provider: Optional[str] = None
    model_name: Optional[str] = None
    prompt_version: Optional[str] = None
    error_message: Optional[str] = None
    evaluator_label: Optional[EvaluatorLabel] = None
