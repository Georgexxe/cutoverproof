"""Scenario loader and validator."""

import json
import re
from pathlib import Path
from typing import Dict, List, Optional
from src.scenarios.models import (
    Scenario,
    ScenarioView,
    Phase,
    Operation,
    Invariant,
    RepairOption,
    EvaluatorLabel,
)


class ScenarioLoaderError(Exception):
    """Raised when a scenario definition is invalid or missing required fields."""
    pass


class ScenarioLoader:
    """Loads and validates scenarios from the scenarios directory."""

    def __init__(self, scenarios_dir: Optional[Path] = None):
        if scenarios_dir is None:
            base_dir = Path(__file__).resolve().parent.parent.parent
            self.scenario_roots = [
                base_dir / "scenarios",
                base_dir / "artifacts" / "imported_scenarios",
            ]
        else:
            self.scenario_roots = [Path(scenarios_dir)]

    def list_scenario_ids(self) -> List[str]:
        """Returns all available scenario IDs."""
        scenario_ids = set()
        for root in self.scenario_roots:
            if not root.exists():
                continue
            for item in root.iterdir():
                if item.is_dir() and (item / "scenario.json").exists():
                    scenario_ids.add(item.name)
        return sorted(scenario_ids)

    def load_scenario(self, scenario_id: str) -> Scenario:
        """Loads full scenario including evaluator metadata and SQL contents."""
        if not re.fullmatch(r"[a-z0-9][a-z0-9_-]{0,79}", scenario_id):
            raise ScenarioLoaderError(f"Invalid scenario identifier: {scenario_id!r}")

        scenario_dir = None
        for candidate_root in self.scenario_roots:
            root = candidate_root.resolve()
            candidate = (root / scenario_id).resolve()
            try:
                candidate.relative_to(root)
            except ValueError as exc:
                raise ScenarioLoaderError("Scenario path escapes the configured scenario directory.") from exc
            if (candidate / "scenario.json").exists():
                scenario_dir = candidate
                break
        if scenario_dir is None:
            roots = ", ".join(str(root) for root in self.scenario_roots)
            raise ScenarioLoaderError(f"Scenario configuration not found in: {roots}")
        scenario_file = scenario_dir / "scenario.json"

        try:
            with open(scenario_file, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            raise ScenarioLoaderError(f"Malformed scenario JSON in {scenario_file}: {e}")

        # Validate mandatory fields (FR-001, FR-002)
        required_fields = ["id", "name", "description", "evaluator_label", "phases", "operations", "invariants"]
        for field in required_fields:
            if field not in data or not data[field]:
                raise ScenarioLoaderError(f"Scenario '{scenario_id}' missing required field: '{field}'")
        if data["id"] != scenario_id:
            raise ScenarioLoaderError(
                f"Scenario directory '{scenario_id}' does not match declared id '{data['id']}'."
            )

        # Load SQL files
        def read_sql(file_key: str, default_name: str, required: bool = False) -> str:
            fname = data.get(file_key, default_name)
            fpath = (scenario_dir / fname).resolve()
            try:
                fpath.relative_to(scenario_dir)
            except ValueError as exc:
                raise ScenarioLoaderError(f"SQL path for '{file_key}' escapes the scenario directory.") from exc
            if fpath.exists():
                return fpath.read_text(encoding="utf-8")
            if required:
                raise ScenarioLoaderError(f"Required SQL file not found: {fpath}")
            return ""

        schema_sql = read_sql("schema_file", "schema.sql", required=True)
        seed_sql = read_sql("seed_file", "seed.sql", required=True)
        expand_sql = read_sql("expand_file", "expand.sql")
        invariants_sql = read_sql("invariants_file", "invariants.sql")
        repair_sql = read_sql("repair_file", "repair.sql")

        # Construct phases
        phases = [Phase(**p) for p in data["phases"]]
        phase_ids = {phase.id for phase in phases}
        if len(phase_ids) != len(phases):
            raise ScenarioLoaderError(f"Scenario '{scenario_id}' contains duplicate phase identifiers.")

        # Construct operations
        operations: Dict[str, Operation] = {}
        for op_id, op_data in data["operations"].items():
            operation = Operation(**op_data)
            if operation.id != op_id:
                raise ScenarioLoaderError(
                    f"Operation key '{op_id}' does not match declared id '{operation.id}'."
                )
            if operation.phase not in phase_ids:
                raise ScenarioLoaderError(
                    f"Operation '{op_id}' refers to undeclared phase '{operation.phase}'."
                )
            if not operation.sql.strip():
                raise ScenarioLoaderError(f"Operation '{op_id}' has empty SQL.")
            operations[op_id] = operation

        # Construct invariants
        invariants = [Invariant(**inv) for inv in data["invariants"]]
        if any(not invariant.sql.strip() for invariant in invariants):
            raise ScenarioLoaderError(f"Scenario '{scenario_id}' contains an invariant with empty SQL.")

        # Construct repairs
        repairs = [RepairOption(**r) for r in data.get("permitted_repairs", [])]

        scenario = Scenario(
            id=data["id"],
            name=data["name"],
            description=data["description"],
            evaluator_label=EvaluatorLabel(data["evaluator_label"]),
            max_candidates=data.get("max_candidates", 8),
            max_schedule_length=data.get("max_schedule_length", 6),
            schema_file=data.get("schema_file", "schema.sql"),
            seed_file=data.get("seed_file", "seed.sql"),
            expand_file=data.get("expand_file", "expand.sql"),
            invariants_file=data.get("invariants_file", "invariants.sql"),
            repair_file=data.get("repair_file", "repair.sql"),
            phases=phases,
            operations=operations,
            invariants=invariants,
            known_failing_schedule=data.get("known_failing_schedule", []),
            permitted_repairs=repairs,
            schema_sql=schema_sql,
            seed_sql=seed_sql,
            expand_sql=expand_sql,
            invariants_sql=invariants_sql,
            repair_sql=repair_sql,
        )
        return scenario

    def load_agent_view(self, scenario_id: str) -> ScenarioView:
        """Loads scenario view for agents with evaluator label and known schedule strictly hidden."""
        scenario = self.load_scenario(scenario_id)
        return ScenarioView(
            id=scenario.id,
            name=scenario.name,
            description=scenario.description,
            max_candidates=scenario.max_candidates,
            max_schedule_length=scenario.max_schedule_length,
            phases=scenario.phases,
            operations=scenario.operations,
            invariants=scenario.invariants,
            permitted_repairs=scenario.permitted_repairs,
        )
