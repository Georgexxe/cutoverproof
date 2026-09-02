"""Read models and safe workflow operations used by the web API."""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from src.coordinator.cli import run_single
from src.evidence.recorder import EvidenceRecorder
from src.executor.db import DatabaseManager
from src.repair.approval import HumanApprovalGate
from src.repair.replay import RepairReplayer
from src.report.timeline import TimelineRenderer
from src.scenarios.loader import ScenarioLoader
from src.scenarios.models import RunResult, RunStatus, TrajectoryStep


PROJECT_ROOT = Path(__file__).resolve().parents[2]
ARTIFACTS_ROOT = PROJECT_ROOT / "artifacts"
RUNS_ROOT = ARTIFACTS_ROOT / "runs"
TIMELINES_ROOT = ARTIFACTS_ROOT / "timelines"
RUN_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{0,159}$")


class ProductServiceError(RuntimeError):
    """An expected product workflow failure with safe user-facing text."""


def _safe_run_id(run_id: str) -> str:
    if not RUN_ID_PATTERN.fullmatch(run_id):
        raise ProductServiceError("Invalid run identifier")
    return run_id


def _load_run_result(run_id: str) -> RunResult:
    safe_id = _safe_run_id(run_id)
    run_path = RUNS_ROOT / f"{safe_id}.json"
    if not run_path.exists():
        raise ProductServiceError("Assessment run not found")
    try:
        return RunResult.model_validate_json(run_path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise ProductServiceError("Assessment evidence could not be read") from exc


def _load_reviewable_run(run_id: str) -> RunResult:
    """Recover the real pre-approval checkpoint for a benchmark-overwritten demo run.

    Benchmark runs intentionally suppress repair proposals and reuse the base run ID.
    The separately preserved approved artifact contains the earlier real proposal and
    replay. For the customer review flow we reconstruct only that pre-approval state;
    no schedule, hypothesis, or repair content is invented.
    """

    original = _load_run_result(run_id)
    if original.repair_proposal:
        return original
    approved_path = RUNS_ROOT / f"{_safe_run_id(run_id)}_approved_repair.json"
    if not approved_path.exists():
        return original
    try:
        approved = RunResult.model_validate_json(approved_path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return original
    if not approved.repair_proposal:
        return original

    checkpoint = approved.model_copy(deep=True)
    checkpoint.run_id = original.run_id
    checkpoint.repair_replay_trace = None
    checkpoint.repair_proposal.approved_by_human = False
    checkpoint.repair_proposal.approved_by = None
    checkpoint.repair_proposal.approval_timestamp = None
    checkpoint.trajectories = [
        step for step in checkpoint.trajectories if step.action_type != "human_approval"
    ]
    return checkpoint


def _plain_finding(result: RunResult) -> str:
    if result.status == RunStatus.AGENT_ERROR:
        return (
            "Gemini could not return a migration plan after automatic retries. "
            "No migration verdict was produced."
        )
    if result.status == RunStatus.INFRASTRUCTURE_ERROR:
        return (
            "The disposable PostgreSQL sandbox was unavailable. "
            "No migration verdict was produced."
        )
    if result.status in {
        RunStatus.INVALID_SCENARIO,
        RunStatus.INVALID_SCHEDULE,
        RunStatus.EXECUTION_ERROR,
        RunStatus.VERIFIER_ERROR,
    }:
        return (
            "The migration pack could not complete a verified candidate execution. "
            "Review its declared SQL and invariant, then run it again."
        )
    if not result.verified_counterexample_found or not result.traces:
        return "No executed counterexample was found within the configured search budget."

    trace = next((item for item in result.traces if item.has_violation), result.traces[0])
    row = trace.failing_evidence_rows[0] if trace.failing_evidence_rows else {}
    if "legacy_status" in row and "lookup_status" in row:
        return (
            "A legacy write can leave the new status reference out of sync during "
            f"backfill ({row['legacy_status']} versus {row['lookup_status']})."
        )
    invariant = trace.first_violating_boundary or "declared invariant"
    return f"The executed schedule produced a reproducible violation of {invariant}."


def _phase_progress(result: RunResult) -> list[dict[str, Any]]:
    loader = ScenarioLoader()
    scenario = loader.load_agent_view(result.scenario_id)
    operation_phases = {
        operation_id: operation.phase for operation_id, operation in scenario.operations.items()
    }
    completed_phases: set[str] = set()
    failed_operation: str | None = None
    if result.winning_schedule:
        for operation_id in result.winning_schedule:
            phase_id = operation_phases.get(operation_id)
            if phase_id:
                completed_phases.add(phase_id)
        if result.verified_counterexample_found:
            failed_operation = result.winning_schedule[-1]

    visible_phases = [phase for phase in scenario.phases if phase.id != "seed"]
    product_phase_names = {
        "expand": "Expand",
        "backfill": "Backfill",
        "compat": "Compatibility",
        "cutover": "Cutover",
        "contract": "Contract",
    }
    return [
        {
            "id": phase.id,
            "name": product_phase_names.get(phase.id, phase.name.replace(" Phase", "")),
            "description": phase.description,
            "state": "complete" if phase.id in completed_phases else "pending",
            "failed_operation": failed_operation
            if failed_operation and operation_phases.get(failed_operation) == phase.id
            else None,
        }
        for phase in visible_phases
    ]


def serialize_run(result: RunResult) -> dict[str, Any]:
    """Return product-safe evidence without evaluator labels or raw SQL."""

    loader = ScenarioLoader()
    scenario = loader.load_agent_view(result.scenario_id)
    trace = next((item for item in result.traces if item.has_violation), None)
    repair = result.repair_proposal
    replay = result.repair_replay_trace
    operation_catalog = scenario.operations

    steps: list[dict[str, Any]] = []
    if trace:
        for step in trace.step_outcomes:
            operation = operation_catalog.get(step.operation_id)
            steps.append(
                {
                    "index": step.step_index,
                    "id": step.operation_id,
                    "actor": step.actor,
                    "phase": step.phase,
                    "description": operation.description if operation else step.operation_id,
                    "duration_ms": round(step.duration_ms, 1),
                    "status": step.status,
                }
            )

    failed_statuses = {
        RunStatus.INVALID_SCENARIO,
        RunStatus.INVALID_SCHEDULE,
        RunStatus.INFRASTRUCTURE_ERROR,
        RunStatus.EXECUTION_ERROR,
        RunStatus.VERIFIER_ERROR,
        RunStatus.AGENT_ERROR,
    }
    status = "failed" if result.status in failed_statuses else ("blocked" if result.verified_counterexample_found else "inconclusive")
    if replay:
        status = "repair_verified" if not replay.has_violation else "repair_failed"

    return {
        "run_id": result.run_id,
        "scenario_id": result.scenario_id,
        "title": result.scenario_name.replace(" Trigger/Backfill Race", " rollout"),
        "scenario_name": result.scenario_name,
        "scenario_description": scenario.description,
        "status": status,
        "status_label": {
            "blocked": "DO NOT CUT OVER",
            "inconclusive": "NO COUNTEREXAMPLE FOUND",
            "failed": "ASSESSMENT INTERRUPTED",
            "repair_verified": "REPAIR VERIFIED IN SANDBOX",
            "repair_failed": "REPAIR REPLAY FAILED",
        }[status],
        "finding": _plain_finding(result),
        "error_message": result.error_message,
        "boundary": trace.first_violating_boundary if trace else None,
        "evidence_rows": trace.failing_evidence_rows if trace else [],
        "steps": steps,
        "phases": _phase_progress(result),
        "winning_schedule": result.winning_schedule or [],
        "candidates_attempted": result.candidates_attempted,
        "max_budget": result.max_budget,
        "wall_clock_seconds": round(result.wall_clock_seconds, 2),
        "approach_id": result.approach_id,
        "model_provider": result.model_provider,
        "model_name": result.model_name,
        "model_calls": result.model_calls,
        "model_tokens": result.model_tokens,
        "repair": (
            {
                "id": repair.repair_id,
                "name": repair.repair_name.replace(" & Dual-Write Trigger", ""),
                "description": next(
                    (
                        option.description
                        for option in scenario.permitted_repairs
                        if option.id == repair.repair_id
                    ),
                    repair.explanation,
                ),
                "explanation": repair.explanation,
                "approved": repair.approved_by_human,
                "approved_by": repair.approved_by,
                "approval_timestamp": repair.approval_timestamp,
            }
            if repair
            else None
        ),
        "replay": (
            {
                "passed": not replay.has_violation,
                "status": replay.status.value,
                "duration_ms": round(replay.total_duration_ms, 1),
            }
            if replay
            else None
        ),
        "evidence_url": f"/api/evidence/{result.run_id}",
    }


def list_scenarios() -> list[dict[str, Any]]:
    loader = ScenarioLoader()
    scenarios: list[dict[str, Any]] = []
    for scenario_id in loader.list_scenario_ids():
        scenario = loader.load_agent_view(scenario_id)
        scenarios.append(
            {
                "id": scenario.id,
                "name": scenario.name,
                "description": scenario.description,
                "max_candidates": scenario.max_candidates,
                "max_schedule_length": scenario.max_schedule_length,
                "phase_count": len(scenario.phases),
                "operation_count": len(scenario.operations),
                "invariant_count": len(scenario.invariants),
            }
        )
    return sorted(
        scenarios,
        key=lambda item: (item["id"] != "u1_status_trigger_race", item["name"]),
    )


def inspect_change_contract(scenario_id: str) -> dict[str, Any]:
    """Return the agent-visible contract without evaluator answers or raw SQL."""

    scenario = ScenarioLoader().load_agent_view(scenario_id)
    return {
        "id": scenario.id,
        "name": scenario.name,
        "objective": scenario.description,
        "phase_order": [
            {
                "id": phase.id,
                "name": phase.name.replace(" Phase", ""),
                "guardrail": phase.description,
            }
            for phase in scenario.phases
            if phase.id != "seed"
        ],
        "declared_operations": [
            {
                "id": operation.id,
                "actor": operation.actor,
                "phase": operation.phase,
                "intent": operation.description,
            }
            for operation in scenario.operations.values()
        ],
        "invariants": [
            {
                "id": invariant.id,
                "name": invariant.name,
                "meaning": invariant.description,
            }
            for invariant in scenario.invariants
        ],
        "allowed_repairs": [
            {
                "id": repair.id,
                "name": repair.name,
                "meaning": repair.description,
                "requires_human_approval": True,
            }
            for repair in scenario.permitted_repairs
        ],
        "candidate_budget": scenario.max_candidates,
        "max_schedule_length": scenario.max_schedule_length,
        "authority": {
            "agent": "May inspect this contract and prepare a review draft.",
            "verifier": "Executes declared operations in PostgreSQL and decides invariant outcomes.",
            "human": "Must start the sandbox assessment and approve any repair replay.",
        },
        "claims_boundary": (
            "A passing bounded search means only that no counterexample was found within "
            "the tested candidate budget; it is not proof that the migration is safe."
        ),
    }


def list_runs() -> list[dict[str, Any]]:
    summaries: list[dict[str, Any]] = []
    for path in sorted(RUNS_ROOT.glob("*.json"), key=lambda item: item.stat().st_mtime, reverse=True):
        try:
            result = RunResult.model_validate_json(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        # Customer history contains product assessments only. Baseline and heuristic
        # runs remain available in the separate evaluation artifact/API for judges.
        if result.approach_id != "A3_specialised_agent":
            continue
        serialized = serialize_run(result)
        summaries.append(
            {
                key: serialized[key]
                for key in (
                    "run_id",
                    "scenario_id",
                    "scenario_name",
                    "title",
                    "status",
                    "status_label",
                    "candidates_attempted",
                    "max_budget",
                    "approach_id",
                    "wall_clock_seconds",
                    "model_name",
                )
            }
        )
    return summaries


def get_run(run_id: str) -> dict[str, Any]:
    return serialize_run(_load_reviewable_run(run_id))


def execute_run(
    payload: dict[str, Any],
    connection_url: str | None = None,
    progress_callback: Callable[[int, str], None] | None = None,
) -> dict[str, Any]:
    result = run_single(
        scenario_id=payload["scenario_id"],
        approach_name=payload["approach"],
        budget=payload["budget"],
        seed=payload["seed"],
        approve_repair=False,
        render_timeline=True,
        model_name=payload.get("model_name"),
        request_repair=payload.get("request_repair", True),
        connection_url=connection_url,
        progress_callback=progress_callback,
    )
    return serialize_run(result)


def approve_and_replay(run_id: str, reviewer_name: str, connection_url: str | None = None) -> dict[str, Any]:
    original = _load_reviewable_run(run_id)
    if not original.verified_counterexample_found or not original.winning_schedule:
        raise ProductServiceError("Only a verified counterexample can be repaired and replayed")
    if not original.repair_proposal:
        raise ProductServiceError("This run does not contain an allow-listed repair proposal")
    if original.repair_replay_trace or original.repair_proposal.approved_by_human:
        raise ProductServiceError("This run has already been approved and replayed")

    result = original.model_copy(deep=True)
    HumanApprovalGate.approve_proposal(result.repair_proposal, approver_name=reviewer_name)
    result.trajectories.append(
        TrajectoryStep(
            step_index=len(result.trajectories) + 1,
            timestamp=datetime.now(timezone.utc).isoformat(),
            agent_id="human_reviewer",
            action_type="human_approval",
            tool_name="approve_bounded_repair",
            tool_input={"repair_id": result.repair_proposal.repair_id},
            tool_output={"approved": True, "reviewer": reviewer_name},
            observation_summary="Named human approved an allow-listed sandbox repair replay.",
            remaining_budget=0,
        )
    )

    scenario = ScenarioLoader().load_scenario(result.scenario_id)
    replay = RepairReplayer(scenario, DatabaseManager(connection_url)).replay_repair(
        failing_schedule=result.winning_schedule,
        repair_proposal=result.repair_proposal,
    )
    result.repair_replay_trace = replay
    result.run_id = f"{original.run_id}_approved_repair"

    EvidenceRecorder().save_run_result(result)
    TimelineRenderer().render_timeline_html(result)
    return serialize_run(result)


def benchmark_summary() -> dict[str, Any]:
    path = ARTIFACTS_ROOT / "evaluation" / "benchmark_results.json"
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ProductServiceError("Benchmark evidence is unavailable") from exc


def evidence_path(run_id: str) -> Path:
    safe_id = _safe_run_id(run_id)
    path = (TIMELINES_ROOT / f"{safe_id}_timeline.html").resolve()
    try:
        path.relative_to(TIMELINES_ROOT.resolve())
    except ValueError as exc:
        raise ProductServiceError("Invalid evidence path") from exc
    if not path.exists():
        raise ProductServiceError("Technical evidence was not found")
    return path
