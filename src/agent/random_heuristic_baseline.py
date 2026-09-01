"""Heuristic and Seeded Random Baseline Approach (A2)."""

import random
import time
from typing import List, Optional
from src.scenarios.models import ScenarioView, RunResult, RunStatus
from src.agent.base import BaseApproach
from src.agent.tools import ToolGateway


class RandomHeuristicBaseline(BaseApproach):
    """Generates candidate schedules using phase-boundary heuristics and seeded random exploration."""

    def __init__(self):
        super().__init__(name="Heuristic/Random Explorer", approach_id="A2_random_heuristic")

    def generate_candidate_schedules(self, scenario_view: ScenarioView, max_count: int, seed: int) -> List[List[str]]:
        """Generates valid candidate schedules based on phase ordering and operation combinations."""
        rng = random.Random(seed)
        ops = list(scenario_view.operations.keys())
        max_len = scenario_view.max_schedule_length

        schedules: List[List[str]] = []

        # Heuristic 1: Natural sequential phase order
        phase_map = {op.id: op.phase for op in scenario_view.operations.values()}
        sorted_by_phase = sorted(ops, key=lambda x: phase_map.get(x, ""))
        if sorted_by_phase and len(sorted_by_phase) <= max_len:
            schedules.append(sorted_by_phase)

        # Heuristic 2: Reverse phase exploration (test out-of-order execution)
        if len(sorted_by_phase) > 2:
            rev_sched = list(reversed(sorted_by_phase))[:max_len]
            if rev_sched not in schedules:
                schedules.append(rev_sched)

        # Heuristic 3: Seeded random permutations of length 3 to max_len
        attempts = 0
        while len(schedules) < max_count and attempts < 100:
            attempts += 1
            length = rng.randint(min(3, len(ops)), min(max_len, len(ops)))
            sample = rng.sample(ops, length)
            if sample not in schedules:
                schedules.append(sample)

        return schedules[:max_count]

    def run(
        self,
        scenario_view: ScenarioView,
        budget: int = 8,
        seed: int = 42,
        tool_gateway: Optional[ToolGateway] = None,
    ) -> RunResult:
        """Executes candidate schedules through tool gateway until counterexample found or budget exhausted."""
        if tool_gateway is None:
            raise ValueError("ToolGateway is required to run RandomHeuristicBaseline.")

        start_time = time.perf_counter()
        tool_gateway.inspect_scenario()

        candidates = self.generate_candidate_schedules(scenario_view, budget, seed)
        verified_found = False
        first_counterexample_idx = None
        winning_schedule = None

        for idx, sched in enumerate(candidates):
            if tool_gateway.remaining_budget <= 0:
                break

            result = tool_gateway.propose_or_run_schedule(
                operations=sched,
                hypothesis=f"Heuristic/Random schedule candidate #{idx + 1} (seed {seed})",
                reason="Testing combinatorial operation interleaving without model guidance",
            )

            if result.get("has_violation"):
                verified_found = True
                first_counterexample_idx = idx + 1
                winning_schedule = sched
                break

        wall_clock = time.perf_counter() - start_time
        status = RunStatus.VERIFIED_COUNTEREXAMPLE if verified_found else RunStatus.NO_COUNTEREXAMPLE_WITHIN_BUDGET

        return RunResult(
            run_id=f"run_a2_{scenario_view.id}_{seed}",
            scenario_id=scenario_view.id,
            scenario_name=scenario_view.name,
            approach_id=self.approach_id,
            seed=seed,
            max_budget=budget,
            candidates_attempted=len(tool_gateway.executed_traces),
            status=status,
            verified_counterexample_found=verified_found,
            first_counterexample_index=first_counterexample_idx,
            winning_schedule=winning_schedule,
            traces=tool_gateway.executed_traces,
            trajectories=tool_gateway.trajectories,
            wall_clock_seconds=wall_clock,
            model_calls=0,
            model_tokens=0,
            approximate_cost_usd=0.0,
            reasoning_backend="deterministic_heuristic",
        )
