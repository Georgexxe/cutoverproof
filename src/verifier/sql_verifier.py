"""Independent deterministic SQL invariant verifier."""

from typing import List, Optional
from src.scenarios.models import Invariant, InvariantResult
from src.executor.db import DatabaseManager


class SQLVerifier:
    """Evaluates SQL invariant assertions independently from LLM reasoning."""

    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager

    def verify_invariant(self, invariant: Invariant) -> InvariantResult:
        """Runs a single SQL invariant. Zero rows returned means PASS. 1+ rows means FAIL."""
        try:
            rows = self.db_manager.query_rows(invariant.sql)
            # Invariant convention: query returns violating rows
            passed = (len(rows) == 0)
            return InvariantResult(
                invariant_id=invariant.id,
                passed=passed,
                violating_rows=rows,
                row_count=len(rows),
                sql_query=invariant.sql,
                error_message=None,
            )
        except Exception as e:
            # SQL execution error in the invariant itself is a VERIFIER_ERROR
            return InvariantResult(
                invariant_id=invariant.id,
                passed=False,
                violating_rows=[],
                row_count=0,
                sql_query=invariant.sql,
                error_message=f"Verifier execution error: {e}",
            )

    def verify_all(self, invariants: List[Invariant]) -> List[InvariantResult]:
        """Runs all declared invariants in order."""
        results = []
        for inv in invariants:
            results.append(self.verify_invariant(inv))
        return results
