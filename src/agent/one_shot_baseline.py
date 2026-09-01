"""One-Shot LLM Baseline Approach (A1)."""

import json
import time
from typing import List, Optional
from src.scenarios.models import ScenarioView, RunResult, RunStatus
from src.agent.base import BaseApproach
from src.agent.tools import ToolGateway
from src.agent.llm_client import LLMClient, LLMClientError


PROMPT_VERSION = "one-shot-v2-live-only"


class OneShotLLMBaseline(BaseApproach):
    """Proposes candidate schedules in a single prompt without iterative execution feedback."""

    def __init__(self, llm_client: Optional[LLMClient] = None):
        super().__init__(name="One-Shot LLM Baseline", approach_id="A1_one_shot_llm")
        self.llm_client = llm_client or LLMClient()

    def _build_prompt(self, scenario_view: ScenarioView, budget: int) -> str:
        ops_desc = "\n".join(
            [f"- {op.id} ({op.phase}, {op.actor}): {op.description}" for op in scenario_view.operations.values()]
        )
        invs_desc = "\n".join(
            [f"- {inv.id}: {inv.name} - {inv.description}" for inv in scenario_view.invariants]
        )

        return f"""
Scenario: {scenario_view.name}
Description: {scenario_view.description}
Budget: Propose up to {budget} candidate schedules of ordered operations.

Declared Operations:
{ops_desc}

Business Invariants to Test:
{invs_desc}

You must respond in JSON format with:
{{
  "reasoning": "<analysis of potential migration failure modes>",
  "candidate_schedules": [
    ["op1", "op2", ...],
    ["op1", "op3", ...]
  ]
}}
"""

    def run(
        self,
        scenario_view: ScenarioView,
        budget: int = 8,
        seed: int = 42,
        tool_gateway: Optional[ToolGateway] = None,
    ) -> RunResult:
        """Runs the one-shot baseline approach."""
        if tool_gateway is None:
            raise ValueError("ToolGateway is required to run OneShotLLMBaseline.")

        start_time = time.perf_counter()
        initial_calls = self.llm_client.call_count
        initial_tokens = self.llm_client.token_count
        initial_cost = self.llm_client.estimated_cost_usd
        tool_gateway.inspect_scenario()

        system_instruction = (
            "You are a database migration safety evaluator. "
            "Examine the migration scenario and propose candidate temporal execution schedules to uncover race conditions. "
            "This is a one-shot evaluation: propose your full list of candidate schedules at once."
        )

        prompt = self._build_prompt(scenario_view, budget)
        try:
            response_json, _ = self.llm_client.complete_json(prompt, system_instruction=system_instruction)
        except LLMClientError as exc:
            return RunResult(
                run_id=f"run_a1_{scenario_view.id}_{seed}",
                scenario_id=scenario_view.id,
                scenario_name=scenario_view.name,
                approach_id=self.approach_id,
                seed=seed,
                max_budget=budget,
                candidates_attempted=0,
                status=RunStatus.AGENT_ERROR,
                trajectories=tool_gateway.trajectories,
                wall_clock_seconds=time.perf_counter() - start_time,
                model_calls=self.llm_client.call_count - initial_calls,
                model_tokens=self.llm_client.token_count - initial_tokens,
                approximate_cost_usd=self.llm_client.estimated_cost_usd - initial_cost,
                reasoning_backend="live_model",
                model_provider=self.llm_client.last_provider,
                model_name=self.llm_client.last_model or self.llm_client.model_name,
                prompt_version=PROMPT_VERSION,
                error_message=str(exc),
            )

        candidate_schedules = response_json.get("candidate_schedules", [])
        if not isinstance(candidate_schedules, list):
            candidate_schedules = []
        verified_found = False
        first_counterexample_idx = None
        winning_schedule = None

        for idx, sched in enumerate(candidate_schedules[:budget]):
            if tool_gateway.remaining_budget <= 0:
                break
            if not isinstance(sched, list) or not all(isinstance(op, str) for op in sched):
                continue

            result = tool_gateway.propose_or_run_schedule(
                operations=sched,
                hypothesis=f"One-shot candidate schedule #{idx + 1}",
                reason="Proposing pre-computed one-shot candidate without execution feedback",
            )

            if result.get("has_violation"):
                verified_found = True
                first_counterexample_idx = len(tool_gateway.executed_traces)
                winning_schedule = sched
                break

        wall_clock = time.perf_counter() - start_time
        status = RunStatus.VERIFIED_COUNTEREXAMPLE if verified_found else RunStatus.NO_COUNTEREXAMPLE_WITHIN_BUDGET

        return RunResult(
            run_id=f"run_a1_{scenario_view.id}_{seed}",
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
            model_calls=self.llm_client.call_count - initial_calls,
            model_tokens=self.llm_client.token_count - initial_tokens,
            approximate_cost_usd=self.llm_client.estimated_cost_usd - initial_cost,
            reasoning_backend="live_model",
            model_provider=self.llm_client.last_provider,
            model_name=self.llm_client.last_model or self.llm_client.model_name,
            prompt_version=PROMPT_VERSION,
        )
