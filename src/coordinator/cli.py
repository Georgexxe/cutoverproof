"""CutoverProof Command Line Interface and Evaluation Coordinator."""

import argparse
import json
import shutil
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional
from rich.console import Console
from rich.table import Table

from src.scenarios.loader import ScenarioLoader
from src.scenarios.models import EvaluatorLabel, RunResult, RunStatus
from src.executor.db import DatabaseManager
from src.executor.executor import DeterministicExecutor
from src.agent.tools import ToolGateway
from src.agent.random_heuristic_baseline import RandomHeuristicBaseline
from src.agent.one_shot_baseline import OneShotLLMBaseline
from src.agent.specialised_agent import SpecialisedAgent
from src.agent.llm_client import LLMClient
from src.repair.approval import HumanApprovalGate
from src.repair.replay import RepairReplayer
from src.evidence.recorder import EvidenceRecorder
from src.report.timeline import TimelineRenderer

console = Console()


def run_single(
    scenario_id: str,
    approach_name: str,
    budget: int = 8,
    seed: int = 42,
    approve_repair: bool = False,
    render_timeline: bool = True,
    model_name: Optional[str] = None,
    request_repair: bool = True,
    connection_url: Optional[str] = None,
    progress_callback: Optional[Callable[[int, str], None]] = None,
) -> RunResult:
    """Executes a single scenario with the specified approach."""
    def report(progress: int, stage: str) -> None:
        if progress_callback:
            progress_callback(progress, stage)

    report(12, "Validating the migration pack")
    loader = ScenarioLoader()
    scenario = loader.load_scenario(scenario_id)
    agent_view = loader.load_agent_view(scenario_id)
    db_manager = DatabaseManager(connection_url)
    executor = DeterministicExecutor(scenario, db_manager)
    recorder = EvidenceRecorder()
    report(22, "Preparing a clean PostgreSQL sandbox")

    # Build only the requested approach and bind the recorded run seed to model generation.
    normalized = {
        "specialised_agent": "a3",
        "a3": "a3",
        "one_shot_llm": "a1",
        "a1": "a1",
        "random_heuristic": "a2",
        "a2": "a2",
    }.get(approach_name.lower())
    if normalized == "a3":
        approach = SpecialisedAgent(
            LLMClient(model_name=model_name, generation_seed=seed),
            propose_repairs=request_repair,
        )
    elif normalized == "a1":
        approach = OneShotLLMBaseline(LLMClient(model_name=model_name, generation_seed=seed))
    elif normalized == "a2":
        approach = RandomHeuristicBaseline()
    else:
        raise ValueError(
            "Unknown approach: "
            f"{approach_name}. Allowed: specialised_agent, one_shot_llm, random_heuristic"
        )

    tool_gateway = ToolGateway(
        scenario=scenario,
        agent_view=agent_view,
        executor=executor,
        budget=budget,
        agent_id=approach.approach_id,
        progress_callback=progress_callback,
    )

    console.print(f"[bold cyan]Running CutoverProof[/bold cyan] | Scenario: [yellow]{scenario_id}[/yellow] | Approach: [magenta]{approach.name}[/magenta] (Budget: {budget}, Seed: {seed})")

    report(28, "Planning candidate operation orderings")
    result = approach.run(
        scenario_view=agent_view,
        budget=budget,
        seed=seed,
        tool_gateway=tool_gateway,
    )
    result.evaluator_label = scenario.evaluator_label
    report(82, "Building the migration decision")

    # Repair replay requires an explicit CLI approval flag. Benchmarks never approve.
    if result.verified_counterexample_found and result.repair_proposal:
        if approve_repair:
            console.print(
                f"[bold green]Approval Gate:[/bold green] Explicit CLI approval for repair: "
                f"'{result.repair_proposal.repair_name}'"
            )
            HumanApprovalGate.approve_proposal(result.repair_proposal, approver_name="CLI Human Approver")
            tool_gateway.record_human_approval(result.repair_proposal)
            result.trajectories = tool_gateway.trajectories

            console.print(f"[cyan]Replaying exact failing schedule against repaired sandbox...[/cyan]")
            replayer = RepairReplayer(scenario, db_manager)
            replayed_trace = replayer.replay_repair(
                # Never fall back to evaluator-only ground truth in a product run.
                # This branch is reachable only after a verified model-found schedule.
                failing_schedule=result.winning_schedule,
                repair_proposal=result.repair_proposal,
            )
            result.repair_replay_trace = replayed_trace
            console.print(f"[bold green]Repair Replay Outcome:[/bold green] {replayed_trace.status.value}")

            # Preserve the benchmark run and the approved replay as separate evidence.
            result.run_id = f"{result.run_id}_approved_repair"

    console.print(
        f"[bold]Verdict:[/bold] {result.status.value} | "
        f"candidates={result.candidates_attempted}/{result.max_budget} | "
        f"model={result.model_name or 'none'}"
    )

    # Persist evidence
    report(88, "Saving replayable evidence")
    run_file = recorder.save_run_result(result)
    console.print(f"[green]Saved run artifact:[/green] {run_file}")

    # Render visual timeline
    if render_timeline:
        report(95, "Rendering the detailed execution timeline")
        renderer = TimelineRenderer()
        timeline_path = renderer.render_timeline_html(result)
        console.print(f"[bold yellow]Visual Timeline generated:[/bold yellow] {timeline_path}")

    report(99, "Opening the verified result")
    return result


def run_benchmark(
    scenarios: Optional[List[str]] = None,
    budget: int = 8,
    seed: int = 42,
    model_name: Optional[str] = None,
    resume: bool = False,
) -> Dict[str, Any]:
    """Runs the equal-budget benchmark matrix across all scenarios and approaches."""
    loader = ScenarioLoader()
    all_scenario_ids = scenarios or loader.list_scenario_ids()
    approaches = [
        ("A2_random_heuristic", "random_heuristic"),
        ("A1_one_shot_llm", "one_shot_llm"),
        ("A3_specialised_agent", "specialised_agent"),
    ]

    console.print(f"\n[bold green]====================================================[/bold green]")
    console.print(f"[bold green] CutoverProof Frontier Benchmark Matrix (Budget: {budget}) [/bold green]")
    console.print(f"[bold green]====================================================[/bold green]\n")

    results_matrix: List[RunResult] = []
    artifacts_root = Path(__file__).resolve().parents[2] / "artifacts"
    invalid_statuses = {
        RunStatus.AGENT_ERROR,
        RunStatus.INFRASTRUCTURE_ERROR,
        RunStatus.VERIFIER_ERROR,
        RunStatus.EXECUTION_ERROR,
        RunStatus.INVALID_SCENARIO,
    }
    run_prefix = {
        "A2_random_heuristic": "a2",
        "A1_one_shot_llm": "a1",
        "A3_specialised_agent": "a3",
    }
    effective_model = model_name or LLMClient().model_name

    for scen_id in all_scenario_ids:
        for app_id, app_key in approaches:
            expected_run_id = f"run_{run_prefix[app_id]}_{scen_id}_{seed}"
            existing_file = artifacts_root / "runs" / f"{expected_run_id}.json"
            if resume and existing_file.exists():
                try:
                    existing = RunResult.model_validate_json(existing_file.read_text(encoding="utf-8"))
                    model_matches = (
                        app_id == "A2_random_heuristic" or existing.model_name == effective_model
                    )
                    if (
                        existing.status not in invalid_statuses
                        and existing.max_budget == budget
                        and existing.seed == seed
                        and existing.approach_id == app_id
                        and model_matches
                    ):
                        console.print(
                            f"[dim]Resume: using valid existing artifact {expected_run_id}[/dim]"
                        )
                        results_matrix.append(existing)
                        continue
                except (ValueError, OSError):
                    pass

                # Preserve every invalid or stale result before replacement.
                archive_dir = artifacts_root / "invalidated"
                archive_dir.mkdir(parents=True, exist_ok=True)
                stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
                shutil.copy2(existing_file, archive_dir / f"{expected_run_id}_{stamp}.json")
                trajectory_file = artifacts_root / "trajectories" / f"{expected_run_id}_trajectory.json"
                if trajectory_file.exists():
                    shutil.copy2(
                        trajectory_file,
                        archive_dir / f"{expected_run_id}_{stamp}_trajectory.json",
                    )
                console.print(
                    f"[yellow]Resume: archived and rerunning invalid/stale artifact {expected_run_id}[/yellow]"
                )

            res = run_single(
                scenario_id=scen_id,
                approach_name=app_key,
                budget=budget,
                seed=seed,
                approve_repair=False,
                render_timeline=True,
                model_name=model_name,
                request_repair=False,
            )
            results_matrix.append(res)

    # Compute aggregate metrics
    scenario_labels = {scenario_id: loader.load_scenario(scenario_id).evaluator_label for scenario_id in all_scenario_ids}
    unsafe_total = sum(1 for label in scenario_labels.values() if label == EvaluatorLabel.UNSAFE)
    safe_total = sum(1 for label in scenario_labels.values() if label == EvaluatorLabel.SAFE)

    summary_by_approach: Dict[str, Any] = {}
    for app_id, _ in approaches:
        app_runs = [r for r in results_matrix if r.approach_id == app_id]
        valid_runs = [r for r in app_runs if r.status not in invalid_statuses]
        valid_unsafe_runs = [r for r in valid_runs if r.evaluator_label == EvaluatorLabel.UNSAFE]
        valid_safe_runs = [r for r in valid_runs if r.evaluator_label == EvaluatorLabel.SAFE]
        unsafe_detected = sum(1 for r in valid_unsafe_runs if r.verified_counterexample_found)
        safe_violations = sum(1 for r in valid_safe_runs if r.verified_counterexample_found)
        total_time = sum(r.wall_clock_seconds for r in app_runs)
        total_calls = sum(r.model_calls for r in app_runs)
        total_tokens = sum(r.model_tokens for r in app_runs)
        total_cost = sum(r.approximate_cost_usd for r in app_runs)
        invalid_runs = sum(1 for r in app_runs if r.status in invalid_statuses)
        
        # Detected-only efficiency is supplemented by a miss-penalized metric;
        # otherwise an approach that finds one easy case can appear best.
        attempts_list = [r.first_counterexample_index for r in app_runs if r.first_counterexample_index is not None]
        avg_attempts = (sum(attempts_list) / len(attempts_list)) if attempts_list else 0.0
        unsafe_efforts = [
            (r.first_counterexample_index if r.first_counterexample_index is not None else r.max_budget + 1)
            for r in valid_unsafe_runs
        ]
        mean_unsafe_effort = (
            sum(unsafe_efforts) / len(unsafe_efforts) if unsafe_efforts else None
        )

        summary_by_approach[app_id] = {
            "unsafe_detection_recall": (
                f"{unsafe_detected}/{unsafe_total}"
                if len(valid_unsafe_runs) == unsafe_total
                else f"INVALID ({len(valid_unsafe_runs)}/{unsafe_total} valid runs)"
            ),
            "safe_false_rejection_rate": (
                f"{safe_violations}/{safe_total}"
                if len(valid_safe_runs) == safe_total
                else f"INVALID ({len(valid_safe_runs)}/{safe_total} valid runs)"
            ),
            "avg_candidates_to_counterexample": round(avg_attempts, 2),
            "mean_unsafe_search_effort_misses_as_budget_plus_one": (
                round(mean_unsafe_effort, 2) if mean_unsafe_effort is not None else None
            ),
            "total_wall_clock_seconds": round(total_time, 2),
            "total_model_calls": total_calls,
            "total_model_tokens": total_tokens,
            "total_estimated_cost_usd": round(total_cost, 4) if total_calls == 0 else None,
            "invalid_runs": invalid_runs,
        }

    # Print Rich Table
    table = Table(title="Benchmark Evaluation Summary")
    table.add_column("Approach", style="cyan", no_wrap=True)
    table.add_column("Unsafe Recall", style="green")
    table.add_column("Safe False Alarms", style="red")
    table.add_column("Mean Unsafe Effort*", style="yellow")
    table.add_column("Wall Clock (s)", style="magenta")
    table.add_column("Model Calls", style="blue")
    table.add_column("Invalid Runs", style="red")

    for app_id, data in summary_by_approach.items():
        table.add_row(
            app_id,
            str(data["unsafe_detection_recall"]),
            str(data["safe_false_rejection_rate"]),
            str(data["mean_unsafe_search_effort_misses_as_budget_plus_one"]),
            str(data["total_wall_clock_seconds"]),
            str(data["total_model_calls"]),
            str(data["invalid_runs"]),
        )

    console.print("\n")
    console.print(table)
    console.print("[dim]* Verified find = candidate index; valid miss = budget + 1.[/dim]")

    recorder = EvidenceRecorder()
    eval_summary = {
        "budget": budget,
        "seed": seed,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "requested_model": model_name or "environment/default",
        "scenarios_evaluated": all_scenario_ids,
        "metrics_summary": summary_by_approach,
        "individual_runs": [r.run_id for r in results_matrix],
    }
    eval_file = recorder.save_evaluation_summary(eval_summary)
    console.print(f"\n[bold green]Benchmark evaluation saved to:[/bold green] {eval_file}\n")

    return eval_summary


def main():
    parser = argparse.ArgumentParser(description="CutoverProof: Temporal Migration Safety Testing CLI")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # Command: run
    run_parser = subparsers.add_parser("run", help="Run a single scenario test")
    run_parser.add_argument("--scenario", "-s", default="u1_status_trigger_race", help="Scenario ID")
    run_parser.add_argument("--approach", "-a", default="specialised_agent", help="Approach (specialised_agent, one_shot_llm, random_heuristic)")
    run_parser.add_argument("--budget", "-b", type=int, default=8, help="Max candidate schedule budget")
    run_parser.add_argument("--seed", type=int, default=42, help="Random seed")
    run_parser.add_argument("--model", help="Live model identifier (defaults to MODEL_NAME or gemini-3.6-flash)")
    run_parser.add_argument(
        "--approve-repair",
        action="store_true",
        help="Explicitly approve the proposed sandbox repair and replay it",
    )

    # Command: evaluate
    eval_parser = subparsers.add_parser("evaluate", help="Run full benchmark across scenarios and approaches")
    eval_parser.add_argument("--budget", "-b", type=int, default=8, help="Equal budget per scenario/approach")
    eval_parser.add_argument("--seed", type=int, default=42, help="Random seed")
    eval_parser.add_argument("--model", help="Live model identifier used by both model approaches")
    eval_parser.add_argument(
        "--resume",
        action="store_true",
        help="Reuse matching valid run artifacts and rerun only invalid or stale cells",
    )

    # Command: test-db
    subparsers.add_parser("test-db", help="Verify PostgreSQL sandbox connectivity and clean reset")

    args = parser.parse_args()

    if args.command == "run":
        run_single(
            scenario_id=args.scenario,
            approach_name=args.approach,
            budget=args.budget,
            seed=args.seed,
            approve_repair=args.approve_repair,
            model_name=args.model,
        )
    elif args.command == "evaluate":
        run_benchmark(
            budget=args.budget,
            seed=args.seed,
            model_name=args.model,
            resume=args.resume,
        )
    elif args.command == "test-db":
        db = DatabaseManager()
        console.print("[cyan]Testing PostgreSQL sandbox connectivity...[/cyan]")
        db.reset_sandbox()
        console.print("[bold green]PostgreSQL Sandbox reset and connection verified successfully![/bold green]")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
