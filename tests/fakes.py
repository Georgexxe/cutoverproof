"""Test-only model doubles. They are never used by production evaluation."""

from typing import Any, Dict, List, Tuple


class ScriptedLLMClient:
    """Returns an explicit response sequence so unit tests never call model APIs."""

    def __init__(self, responses: List[Dict[str, Any]]):
        self.responses = list(responses)
        self.call_count = 0
        self.token_count = 0
        self.estimated_cost_usd = 0.0
        self.last_provider = "test"
        self.last_model = "scripted-test-double"
        self.last_error = None
        self.model_name = "scripted-test-double"

    def complete_json(self, prompt: str, system_instruction: str = "") -> Tuple[Dict[str, Any], int]:
        self.call_count += 1
        if not self.responses:
            raise AssertionError("ScriptedLLMClient received more calls than expected")
        return self.responses.pop(0), 0

