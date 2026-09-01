"""Specialised Iterative Planning Agent Approach (A3)."""

import json
import time
from typing import Any, Dict, List, Optional
from src.scenarios.models import ScenarioView, RunResult, RunStatus, RepairProposal
from src.agent.base import BaseApproach
from src.agent.tools import ToolGateway
from src.agent.llm_client import LLMClient, LLMClientError


PROMPT_VERSION = "specialised-v2-live-only"


class SpecialisedAgent(BaseApproach):
    """Adaptive testing agent that inspects migration phase graph, proposes hypotheses, and iterates on feedback."""

    def __init__(self, llm_client: Optional[LLMClient] = None, propose_repairs: bool = True):
        super().__init__(name="Specialised Iterative Agent", approach_id="A3_specialised_agent")
        self.llm_client = llm_client or LLMClient()
        self.propose_repairs = propose_repairs

    def run(
        self,
        scenario_view: ScenarioView,
        budget: int = 8,
        seed: int = 42,
        tool_gateway: Optional[ToolGateway] = None,
    ) -> RunResult:
        """Executes the iterative observe-hypothesise-act-verify agent loop."""
        if tool_gateway is None:
            raise ValueError("ToolGateway is required to run SpecialisedAgent.")

        start_time = time.perf_counter()
        initial_calls = self.llm_client.call_count
        initial_tokens = self.llm_client.token_count
        initial_cost = self.llm_client.estimated_cost_usd

        # 1. Observe: Inspect scenario
        scenario_info = tool_gateway.inspect_scenario()

        system_instruction = (
            "You are CutoverProof Specialised Agent. "
            "Your objective: find the smallest sequence of concurrent writes, backfills, retries, and cutover operations "
            "that causes an online PostgreSQL migration to violate a business invariant. "
            "You receive deterministic execution traces and SQL assertion results after each candidate schedule. "
            "Use only declared operation IDs. When a counterexample is verified, explain the causal mechanism and propose a permitted repair."
        )

        history: List[Dict[str, Any]] = []
        verified_found = False
        first_counterexample_idx = None
        winning_schedule = None
        repair_proposal = None
        agent_error: Optional[str] = None
        planning_attempts = 0
        max_planning_attempts = max(budget * 2, 1)
        seen_schedules = set()

        while (
            tool_gateway.remaining_budget > 0
            and not verified_found
            and planning_attempts < max_planning_attempts
        ):
            # Build iterative prompt with accumulated feedback
            prompt = f"""
Scenario: {scenario_view.name}
Description: {scenario_view.description}
Remaining Candidate Budget: {tool_gateway.remaining_budget}

Declared Operations:
{json.dumps(scenario_info['operations'], indent=2)}

Business Invariants:
{json.dumps(scenario_info['invariants'], indent=2)}

Permitted Repairs:
{json.dumps(scenario_info['permitted_repairs'], indent=2)}

Execution History & Observations:
{json.dumps(history, indent=2)}

Respond in JSON by proposing exactly one new schedule:
{{
  "action": "propose_schedule",
  "hypothesis": "<concrete hypothesis about an unsafe interleaving>",
  "operations": ["op1", "op2", ...],
  "reason": "<why this schedule tests an unverified interaction>"
}}

Do not propose a repair during search. Do not repeat an operations list already
present in Execution History. A passing schedule disproves only that exact
ordering, so change a meaningful temporal boundary on the next attempt.
"""
            try:
                response_json, _ = self.llm_client.complete_json(prompt, system_instruction=system_instruction)
                planning_attempts += 1
            except LLMClientError as exc:
                agent_error = str(exc)
                break
            action = response_json.get("action", "propose_schedule")

            if action == "propose_schedule":
                ops = response_json.get("operations", [])
                if not isinstance(ops, list) or not all(isinstance(op, str) for op in ops):
                    history.append({
                        "model_output_rejected": "operations must be a list of declared operation IDs",
                    })
                    continue
                schedule_key = tuple(ops)
                reason = response_json.get("reason", "Exploring temporal gap")
                if schedule_key in seen_schedules:
                    # A duplicate is a valid but wasteful experiment. Count it
                    # against the same candidate budget instead of granting the
                    # agent free retries or invalidating the entire run.
                    reason = (
                        f"{reason} "
                        "[duplicate schedule; counted against candidate budget]"
                    )
                seen_schedules.add(schedule_key)
                hyp = response_json.get("hypothesis", "Iterative hypothesis")

                # Act & Verify: Execute schedule via tool gateway
                result = tool_gateway.propose_or_run_schedule(
                    operations=ops,
                    hypothesis=hyp,
                    reason=reason,
                )

                history.append({
                    "attempt": len(tool_gateway.executed_traces),
                    "schedule_id": result.get("schedule_id"),
                    "operations": ops,
                    "hypothesis": hyp,
                    "has_violation": result.get("has_violation"),
                    "status": result.get("status"),
                    "violating_rows": result.get("violating_evidence_rows"),
                })

                if result.get("has_violation"):
                    verified_found = True
                    first_counterexample_idx = len(tool_gateway.executed_traces)
                    winning_schedule = ops

                    # Diagnose and propose repair if permitted repairs exist
                    if self.propose_repairs and scenario_view.permitted_repairs:
                        rep_prompt = f"""
A deterministic PostgreSQL verifier confirmed a business-invariant violation.
Failing schedule: {json.dumps(ops)}
Invariant: {result.get('first_violating_boundary')}
Evidence rows: {json.dumps(result.get('violating_evidence_rows', []))}
Permitted repairs: {json.dumps([r.model_dump() for r in scenario_view.permitted_repairs], indent=2)}

Return JSON only:
{{
  "repair_id": "<one permitted repair ID>",
  "explanation": "<causal diagnosis tied to the schedule and why the repair prevents it>"
}}
"""
                        try:
                            rep_response, _ = self.llm_client.complete_json(
                                rep_prompt, system_instruction=system_instruction
                            )
                            repair_id = rep_response.get("repair_id") or scenario_view.permitted_repairs[0].id
                            explanation = rep_response.get("explanation") or (
                                "Legacy write occurred after backfill before compatibility coverage."
                            )
                            repair_result = tool_gateway.propose_repair(
                                repair_id=repair_id,
                                explanation=explanation,
                            )
                            repair_proposal = tool_gateway.pending_repair
                            if repair_result.get("status") != "success":
                                agent_error = (
                                    "Counterexample verified, but model selected an undeclared repair: "
                                    f"{repair_id}"
                                )
                        except LLMClientError as exc:
                            # Preserve the verified counterexample even when optional repair reasoning fails.
                            agent_error = f"Counterexample verified, but repair proposal failed: {exc}"
                    break
            else:
                history.append({
                    "model_output_rejected": (
                        f"unsupported action '{action}'; only propose_schedule is allowed during search"
                    )
                })
                continue

        if (
            not verified_found
            and not agent_error
            and planning_attempts >= max_planning_attempts
            and tool_gateway.remaining_budget > 0
        ):
            agent_error = (
                "Planning-attempt limit exhausted after repeated malformed, unsupported, "
                "or duplicate model outputs."
            )

        wall_clock = time.perf_counter() - start_time
        if verified_found:
            status = RunStatus.VERIFIED_COUNTEREXAMPLE
        elif agent_error:
            status = RunStatus.AGENT_ERROR
        else:
            status = RunStatus.NO_COUNTEREXAMPLE_WITHIN_BUDGET
        model_calls = self.llm_client.call_count - initial_calls
        model_tokens = self.llm_client.token_count - initial_tokens
        approx_cost = self.llm_client.estimated_cost_usd - initial_cost

        return RunResult(
            run_id=f"run_a3_{scenario_view.id}_{seed}",
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
            repair_proposal=repair_proposal,
            trajectories=tool_gateway.trajectories,
            wall_clock_seconds=wall_clock,
            model_calls=model_calls,
            model_tokens=model_tokens,
            approximate_cost_usd=approx_cost,
            reasoning_backend="live_model",
            model_provider=self.llm_client.last_provider,
            model_name=self.llm_client.last_model or self.llm_client.model_name,
            prompt_version=PROMPT_VERSION,
            error_message=agent_error,
        )
