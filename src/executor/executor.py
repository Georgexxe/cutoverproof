"""Deterministic schedule executor for CutoverProof."""

import time
import uuid
from typing import List, Optional, Union
from src.scenarios.models import (
    Scenario,
    ScenarioView,
    CandidateSchedule,
    ExecutionTrace,
    StepOutcome,
    RunStatus,
)
from src.executor.db import DatabaseManager
from src.validator.schedule_validator import ScheduleValidator
from src.verifier.sql_verifier import SQLVerifier


class DeterministicExecutor:
    """Executes validated candidate schedules against disposable PostgreSQL sandbox."""

    def __init__(self, scenario: Scenario, db_manager: Optional[DatabaseManager] = None):
        self.scenario = scenario
        self.db_manager = db_manager or DatabaseManager()
        self.validator = ScheduleValidator(scenario)
        self.verifier = SQLVerifier(self.db_manager)

    def execute_schedule(
        self,
        candidate: Union[CandidateSchedule, List[str]],
        hypothesis: str = "Deterministic schedule execution",
        custom_schema_sql: Optional[str] = None,
        custom_seed_sql: Optional[str] = None,
    ) -> ExecutionTrace:
        """Executes a schedule in fresh database sandbox, evaluating invariants at completion."""
        start_time = time.perf_counter()
        schedule_id = f"sched_{uuid.uuid4().hex[:8]}"

        # 1. Validate schedule
        val_result = self.validator.validate(candidate)
        if not val_result.is_valid:
            return ExecutionTrace(
                schedule_id=schedule_id,
                hypothesis=hypothesis,
                operations_attempted=candidate.operations if isinstance(candidate, CandidateSchedule) else candidate,
                step_outcomes=[],
                invariant_results=[],
                has_violation=False,
                first_violating_boundary=None,
                failing_evidence_rows=[],
                total_duration_ms=0.0,
                status=RunStatus.INVALID_SCHEDULE,
            )

        ops = val_result.canonical_schedule

        # 2. Reset sandbox
        schema_sql = custom_schema_sql if custom_schema_sql is not None else self.scenario.schema_sql
        seed_sql = custom_seed_sql if custom_seed_sql is not None else self.scenario.seed_sql

        try:
            self.db_manager.reset_sandbox(schema_sql=schema_sql, seed_sql=seed_sql)
        except Exception as e:
            return ExecutionTrace(
                schedule_id=schedule_id,
                hypothesis=hypothesis,
                operations_attempted=ops,
                step_outcomes=[],
                invariant_results=[],
                has_violation=False,
                first_violating_boundary=None,
                failing_evidence_rows=[],
                total_duration_ms=(time.perf_counter() - start_time) * 1000.0,
                status=RunStatus.INFRASTRUCTURE_ERROR,
            )

        # 3. Execute declared operations sequentially
        step_outcomes: List[StepOutcome] = []
        for idx, op_id in enumerate(ops):
            op_def = self.scenario.operations[op_id]
            try:
                rows_aff, dur_ms = self.db_manager.execute_sql(op_def.sql)
                step_outcomes.append(
                    StepOutcome(
                        step_index=idx + 1,
                        operation_id=op_id,
                        phase=op_def.phase,
                        actor=op_def.actor,
                        sql_executed=op_def.sql,
                        rows_affected=rows_aff,
                        duration_ms=dur_ms,
                        status="success",
                        error_message=None,
                    )
                )
            except Exception as e:
                step_outcomes.append(
                    StepOutcome(
                        step_index=idx + 1,
                        operation_id=op_id,
                        phase=op_def.phase,
                        actor=op_def.actor,
                        sql_executed=op_def.sql,
                        rows_affected=0,
                        duration_ms=0.0,
                        status="failed",
                        error_message=str(e),
                    )
                )
                return ExecutionTrace(
                    schedule_id=schedule_id,
                    hypothesis=hypothesis,
                    operations_attempted=ops,
                    step_outcomes=step_outcomes,
                    invariant_results=[],
                    has_violation=False,
                    first_violating_boundary=None,
                    failing_evidence_rows=[],
                    total_duration_ms=(time.perf_counter() - start_time) * 1000.0,
                    status=RunStatus.EXECUTION_ERROR,
                )

        # 4. Verify invariants
        inv_results = self.verifier.verify_all(self.scenario.invariants)

        # Check for verifier error
        for r in inv_results:
            if r.error_message:
                return ExecutionTrace(
                    schedule_id=schedule_id,
                    hypothesis=hypothesis,
                    operations_attempted=ops,
                    step_outcomes=step_outcomes,
                    invariant_results=inv_results,
                    has_violation=False,
                    first_violating_boundary=None,
                    failing_evidence_rows=[],
                    total_duration_ms=(time.perf_counter() - start_time) * 1000.0,
                    status=RunStatus.VERIFIER_ERROR,
                )

        # Check for invariant violation (counterexample)
        has_violation = False
        first_violating_boundary = None
        failing_evidence_rows = []

        for r in inv_results:
            if not r.passed:
                has_violation = True
                first_violating_boundary = r.invariant_id
                failing_evidence_rows.extend(r.violating_rows)
                break

        total_duration_ms = (time.perf_counter() - start_time) * 1000.0
        status = RunStatus.VERIFIED_COUNTEREXAMPLE if has_violation else RunStatus.NO_COUNTEREXAMPLE_WITHIN_BUDGET

        return ExecutionTrace(
            schedule_id=schedule_id,
            hypothesis=hypothesis,
            operations_attempted=ops,
            step_outcomes=step_outcomes,
            invariant_results=inv_results,
            has_violation=has_violation,
            first_violating_boundary=first_violating_boundary,
            failing_evidence_rows=failing_evidence_rows,
            total_duration_ms=total_duration_ms,
            status=status,
        )
