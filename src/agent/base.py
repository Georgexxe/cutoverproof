"""Abstract base class for CutoverProof approaches."""

from abc import ABC, abstractmethod
from typing import Any, List, Optional
from src.scenarios.models import ScenarioView, RunResult


class BaseApproach(ABC):
    """Base interface for all test approaches (Specialised Agent, One-Shot LLM, Heuristic/Random)."""

    def __init__(self, name: str, approach_id: str):
        self.name = name
        self.approach_id = approach_id

    @abstractmethod
    def run(
        self,
        scenario_view: ScenarioView,
        budget: int = 8,
        seed: int = 42,
        tool_gateway: Optional[Any] = None,
    ) -> RunResult:
        """Runs the approach against the scenario view within the fixed budget."""
        pass
