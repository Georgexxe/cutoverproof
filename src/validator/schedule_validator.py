"""Deterministic schedule validator."""

from typing import List, Set, Union
from src.scenarios.models import (
    Scenario,
    ScenarioView,
    CandidateSchedule,
    ScheduleValidationResult,
)


class ScheduleValidator:
    """Validates candidate schedules against scenario constraints and declared operations."""

    def __init__(self, scenario: Union[Scenario, ScenarioView]):
        self.scenario = scenario
        self.declared_operation_ids: Set[str] = set(scenario.operations.keys())
        self.max_length: int = scenario.max_schedule_length

    def validate(self, candidate: Union[CandidateSchedule, List[str]]) -> ScheduleValidationResult:
        """Validates a candidate schedule or raw list of operation IDs."""
        if isinstance(candidate, CandidateSchedule):
            ops = candidate.operations
        elif isinstance(candidate, list):
            ops = candidate
        else:
            return ScheduleValidationResult(
                is_valid=False,
                canonical_schedule=[],
                error_message=f"Expected CandidateSchedule or List[str], got {type(candidate).__name__}",
                rejected_operations=[],
            )

        if not ops:
            return ScheduleValidationResult(
                is_valid=False,
                canonical_schedule=[],
                error_message="Schedule is empty. At least one operation is required.",
                rejected_operations=[],
            )

        if len(ops) > self.max_length:
            return ScheduleValidationResult(
                is_valid=False,
                canonical_schedule=[],
                error_message=f"Schedule length {len(ops)} exceeds maximum allowed length of {self.max_length}.",
                rejected_operations=[],
            )

        rejected = []
        canonical = []
        for op in ops:
            clean_op = str(op).strip()
            if clean_op not in self.declared_operation_ids:
                rejected.append(clean_op)
            else:
                canonical.append(clean_op)

        if rejected:
            return ScheduleValidationResult(
                is_valid=False,
                canonical_schedule=[],
                error_message=f"Undeclared operation(s) in schedule: {', '.join(rejected)}. Allowed: {', '.join(sorted(self.declared_operation_ids))}",
                rejected_operations=rejected,
            )

        return ScheduleValidationResult(
            is_valid=True,
            canonical_schedule=canonical,
            error_message=None,
            rejected_operations=[],
        )
