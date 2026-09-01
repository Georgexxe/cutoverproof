"""Evidence recorder saving structured JSON runs, trajectories, and evaluation summaries."""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional
from src.scenarios.models import RunResult
from src.evidence.sanitizer import SecretSanitizer


class EvidenceRecorder:
    """Persists sanitized run artifacts and trajectories to the artifacts directory."""

    def __init__(self, artifacts_dir: Optional[Path] = None):
        if artifacts_dir is None:
            base_dir = Path(__file__).resolve().parent.parent.parent
            self.artifacts_dir = base_dir / "artifacts"
        else:
            self.artifacts_dir = Path(artifacts_dir)

        self.runs_dir = self.artifacts_dir / "runs"
        self.trajectories_dir = self.artifacts_dir / "trajectories"
        self.evaluation_dir = self.artifacts_dir / "evaluation"
        self.timelines_dir = self.artifacts_dir / "timelines"

        self.runs_dir.mkdir(parents=True, exist_ok=True)
        self.trajectories_dir.mkdir(parents=True, exist_ok=True)
        self.evaluation_dir.mkdir(parents=True, exist_ok=True)
        self.timelines_dir.mkdir(parents=True, exist_ok=True)

        self.sanitizer = SecretSanitizer()

    def save_run_result(self, result: RunResult) -> Path:
        """Saves a RunResult and its trajectory to JSON files."""
        run_dict = self.sanitizer.sanitize_obj(result.model_dump())
        run_file = self.runs_dir / f"{result.run_id}.json"
        with open(run_file, "w", encoding="utf-8") as f:
            json.dump(run_dict, f, indent=2)

        # Save trajectory separately
        if result.trajectories:
            traj_data = [self.sanitizer.sanitize_obj(t.model_dump()) for t in result.trajectories]
            traj_file = self.trajectories_dir / f"{result.run_id}_trajectory.json"
            with open(traj_file, "w", encoding="utf-8") as f:
                json.dump(traj_data, f, indent=2)

        return run_file

    def save_evaluation_summary(self, summary: Dict[str, Any], filename: str = "benchmark_results.json") -> Path:
        """Saves aggregate benchmark evaluation metrics to JSON."""
        clean_summary = self.sanitizer.sanitize_obj(summary)
        eval_file = self.evaluation_dir / filename
        with open(eval_file, "w", encoding="utf-8") as f:
            json.dump(clean_summary, f, indent=2)
        return eval_file
